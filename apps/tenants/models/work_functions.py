from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from backend.core.models import BaseModel


class WorkFunctionCode(models.TextChoices):
    """The fixed V1 catalog; these codes describe eligibility, not authority."""

    SALES = "SALES", _("Sales")
    MEASUREMENT = "MEASUREMENT", _("Measurement")
    CUTTING = "CUTTING", _("Cutting")
    STITCHING = "STITCHING", _("Stitching")
    FINISHING = "FINISHING", _("Finishing")
    QC = "QC", _("Quality control")
    CASHIER = "CASHIER", _("Cashier")


class MembershipWorkFunction(BaseModel):
    """A historical, membership-scoped assignment from the controlled catalog."""

    membership = models.ForeignKey(
        "tenants.TenantMember",
        on_delete=models.CASCADE,
        related_name="work_functions",
    )
    function_code = models.CharField(
        max_length=16,
        choices=WorkFunctionCode.choices,
    )

    class Meta:
        ordering = ["function_code", "created_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["membership", "function_code"],
                condition=Q(deleted__isnull=True),
                name="uniq_active_membership_work_function",
            ),
            models.CheckConstraint(
                condition=Q(
                    function_code__in=[
                        code for code, _label in WorkFunctionCode.choices
                    ]
                ),
                name="valid_membership_work_function_code",
            ),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            previous = (
                type(self)
                .objects.all_with_deleted()
                .filter(pk=self.pk)
                .values("membership_id", "function_code")
                .first()
            )
            if previous and (
                previous["membership_id"] != self.membership_id
                or previous["function_code"] != self.function_code
            ):
                raise ValidationError(
                    "A Work-Function history row cannot be reassigned or rewritten."
                )
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.membership_id}: {self.function_code}"
