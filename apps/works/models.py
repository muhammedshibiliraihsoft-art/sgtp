from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from backend.core.models import BaseModel
from apps.catalog.models import GarmentFamily
from apps.works.constants import WorkPriority, WorkStatus


class WorkOrder(BaseModel):
    """One Shop-owned garment order with immutable source snapshots by reference."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="work_orders"
    )
    sequence = models.PositiveIntegerField()
    work_number = models.CharField(max_length=24)
    client = models.ForeignKey(
        "clients.Client", on_delete=models.PROTECT, related_name="work_orders"
    )
    related_person = models.ForeignKey(
        "clients.RelatedPerson",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="work_orders",
    )
    design_version = models.ForeignKey(
        "catalog.DesignVersion", on_delete=models.PROTECT, related_name="work_orders"
    )
    design_price_amount = models.DecimalField(
        max_digits=18, decimal_places=4, null=True, blank=True
    )
    design_price_currency = models.CharField(max_length=3, null=True, blank=True)
    measurement_set = models.ForeignKey(
        "catalog.MeasurementSet", on_delete=models.PROTECT, related_name="work_orders"
    )
    material = models.ForeignKey(
        "catalog.Material",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="work_orders",
    )
    assigned_membership = models.ForeignKey(
        "tenants.TenantMember",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="assigned_work_orders",
    )
    status = models.CharField(
        max_length=16, choices=WorkStatus.choices, default=WorkStatus.REQUEST
    )
    priority = models.CharField(
        max_length=16, choices=WorkPriority.choices, default=WorkPriority.NORMAL
    )
    due_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("tenant", "sequence"), name="work_shop_sequence_uniq"
            ),
            models.UniqueConstraint(
                fields=("tenant", "work_number"), name="work_shop_number_uniq"
            ),
            models.CheckConstraint(
                condition=Q(sequence__gte=1), name="work_sequence_positive"
            ),
            models.CheckConstraint(
                condition=Q(status__in=WorkStatus.values), name="work_status_valid"
            ),
            models.CheckConstraint(
                condition=Q(priority__in=WorkPriority.values),
                name="work_priority_valid",
            ),
            models.CheckConstraint(
                condition=(
                    Q(design_price_amount__isnull=True, design_price_currency__isnull=True)
                    | Q(design_price_amount__isnull=False, design_price_currency__isnull=False)
                ),
                name="work_design_price_snapshot_pair",
            ),
            models.CheckConstraint(
                condition=Q(design_price_amount__isnull=True) | Q(design_price_amount__gte=0),
                name="work_design_price_snapshot_nonnegative",
            ),
        ]
        indexes = [
            models.Index(
                fields=("tenant", "status", "due_date"), name="work_shop_status_due_idx"
            ),
            models.Index(
                fields=("tenant", "priority", "created_at"),
                name="work_shop_priority_idx",
            ),
        ]

    def clean(self):
        super().clean()
        if not all(
            (
                self.tenant_id,
                self.client_id,
                self.design_version_id,
                self.measurement_set_id,
            )
        ):
            return
        if self.client.tenant_id != self.tenant_id or (
            self._state.adding and self.client.deleted is not None
        ):
            raise ValidationError({"client": "Client must be active in this Shop."})
        if self.related_person_id and (
            self.related_person.tenant_id != self.tenant_id
            or self.related_person.primary_client_id != self.client_id
            or (self._state.adding and self.related_person.deleted is not None)
        ):
            raise ValidationError(
                {
                    "related_person": "Related Person must belong to this Client and Shop."
                }
            )
        version = self.design_version
        design = version.design
        family = (
            GarmentFamily.all_objects.only("status", "deleted").get(
                pk=design.family_id
            )
            if self._state.adding
            else None
        )
        if (
            (self._state.adding and version.deleted is not None)
            or version.status != "PUBLISHED"
            or (self._state.adding and design.deleted is not None)
            or (self._state.adding and design.status != "ACTIVE")
            or (
                self._state.adding
                and (
                    family.deleted is not None
                    or family.status != GarmentFamily.Status.ACTIVE
                )
            )
            or design.tenant_id not in (None, self.tenant_id)
        ):
            raise ValidationError(
                {
                    "design_version": (
                        "An active family and design with an available published version are required."
                    )
                }
            )
        measurement = self.measurement_set
        profile = measurement.profile
        if (
            (self._state.adding and measurement.deleted is not None)
            or (self._state.adding and profile.deleted is not None)
            or profile.tenant_id != self.tenant_id
        ):
            raise ValidationError(
                {
                    "measurement_set": "An active measurement version in this Shop is required."
                }
            )
        if self._state.adding and not measurement.is_active:
            raise ValidationError(
                {"measurement_set": "An active measurement version is required."}
            )
        if (
            profile.client_id != (None if self.related_person_id else self.client_id)
            or profile.related_person_id != self.related_person_id
        ):
            raise ValidationError(
                {"measurement_set": "Measurement owner must match the Work wearer."}
            )
        if (
            design.family_id != profile.family_id
        ):
            raise ValidationError(
                {"design_version": "Design garment must match the measurement garment."}
            )
        if self.material_id and (
            (self._state.adding and self.material.deleted is not None)
            or self.material.tenant_id != self.tenant_id
            or (self._state.adding and self.material.status != "ACTIVE")
        ):
            raise ValidationError({"material": "Material must be active in this Shop."})
        if self.assigned_membership_id and (
            self.assigned_membership.deleted is not None
            or not self.assigned_membership.is_active
            or self.assigned_membership.tenant_id != self.tenant_id
            or not self.assigned_membership.user.is_active
        ):
            raise ValidationError(
                {"assigned_membership": "Assigned member must be active in this Shop."}
            )

    def save(self, *args, **kwargs):
        if not self._state.adding:
            previous = type(self).objects.filter(pk=self.pk).values(
                "design_price_amount", "design_price_currency"
            ).first()
            if previous and (
                previous["design_price_amount"] != self.design_price_amount
                or previous["design_price_currency"] != self.design_price_currency
            ):
                raise ValidationError("The Work Design price snapshot is immutable.")
        self.full_clean()
        return super().save(*args, **kwargs)


class WorkEvent(models.Model):
    """Append-only, internal audit record for a Work lifecycle mutation."""

    class Action(models.TextChoices):
        CREATED = "CREATED", "Created"
        UPDATED = "UPDATED", "Updated"
        ASSIGNED = "ASSIGNED", "Assigned"
        STAGE_TRANSITIONED = "STAGE_TRANSITIONED", "Stage transitioned"
        SOFT_DELETED = "SOFT_DELETED", "Soft deleted"

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="work_events"
    )
    work = models.ForeignKey(
        WorkOrder, on_delete=models.DO_NOTHING, related_name="events"
    )
    actor_id = models.UUIDField()
    action = models.CharField(max_length=24, choices=Action.choices)
    before_state = models.JSONField(default=dict)
    after_state = models.JSONField(default=dict)
    changed_fields = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
        indexes = [
            models.Index(
                fields=("tenant", "work", "created_at"), name="work_event_scope_time_idx"
            )
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Work audit events are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Work audit events are append-only.")
