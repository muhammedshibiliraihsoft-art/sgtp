from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from backend.core.models import BaseModel
from safedelete.queryset import SafeDeleteQueryset
from safedelete.managers import SafeDeleteManager


class ShopRole(models.TextChoices):
    """
    Approved roles within a Shop / Tenant workspace.
    External Suppliers are NOT users and do not receive these roles.
    Main Supplier Admins implicitly have cross-shop authority and do not strictly need a ShopRole.
    """

    ADMIN = "ADMIN", _("Shop Admin")
    STAFF = "STAFF", _("Shop Staff")
    VIEWER = "VIEWER", _("Shop Viewer")


class TenantMemberQuerySet(SafeDeleteQueryset):
    def update(self, *args, **kwargs):
        if "deleted" in kwargs:
            if self.filter(is_active=True).exists():
                raise ValidationError(
                    "Cannot bulk remove active memberships. Deactivate them first."
                )
        return super().update(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.filter(is_active=True).exists():
            raise ValidationError(
                "Cannot bulk remove active memberships. Deactivate them first."
            )
        return super().delete(*args, **kwargs)


class TenantMemberManager(SafeDeleteManager):
    _queryset_class = TenantMemberQuerySet


class TenantMember(BaseModel):
    """
    Membership linking a User to a Shop (Tenant).
    """

    objects = TenantMemberManager()

    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="memberships",
        help_text="The Shop this user is a member of.",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_memberships",
        help_text="The user holding membership in the Shop.",
    )
    role = models.CharField(
        max_length=20,
        choices=ShopRole.choices,
        default=ShopRole.STAFF,
        help_text="The user's role within this Shop.",
    )
    is_active = models.BooleanField(
        default=True, help_text="Whether this membership is currently active."
    )

    class Meta:
        verbose_name = "Shop Membership"
        verbose_name_plural = "Shop Memberships"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "user"],
                name="unique_tenant_user_membership",
                condition=models.Q(deleted__isnull=True),
            )
        ]

    def __str__(self):
        return f"{self.user.full_name} - {self.tenant.name} ({self.get_role_display()})"

    def clean(self):
        super().clean()
        # Activity is required when assigning a new membership. Existing links
        # remain manageable by the Main Supplier after a User/Shop is disabled;
        # reactivation is separately rejected in save() and the domain service.
        if self._state.adding:
            if self.user and not self.user.is_active:
                raise ValidationError(
                    {"user": "Cannot add an inactive user to a Shop."}
                )
            if self.tenant and not self.tenant.is_active:
                raise ValidationError(
                    {"tenant": "Cannot add members to an inactive Shop."}
                )
        if (
            self.user_id
            and self.tenant_id
            and not self.user.is_superuser
            and self.user.owning_shop_id is not None
            and self.user.owning_shop_id != self.tenant_id
        ):
            raise ValidationError(
                {"user": "Membership Shop must match the User's owning Shop."}
            )

    def save(self, *args, **kwargs):
        if not self._state.adding and self.is_active:
            previous_active = (
                type(self)
                .objects.all_with_deleted()
                .filter(pk=self.pk)
                .values_list("is_active", flat=True)
                .first()
            )
            if previous_active is False:
                if self.user and not self.user.is_active:
                    raise ValidationError(
                        {"user": "Cannot reactivate membership for an inactive user."}
                    )
                if self.tenant and not self.tenant.is_active:
                    raise ValidationError(
                        {"tenant": "Cannot reactivate membership in an inactive Shop."}
                    )
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, force_policy=None, **kwargs):
        if self.is_active:
            raise ValidationError(
                "Cannot remove an active membership. Deactivate it first."
            )
        return super().delete(force_policy=force_policy, **kwargs)
