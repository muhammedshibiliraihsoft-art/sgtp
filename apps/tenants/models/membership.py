from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from backend.core.models import BaseModel

class ShopRole(models.TextChoices):
    """
    Approved roles within a Shop / Tenant workspace.
    External Suppliers are NOT users and do not receive these roles.
    Main Supplier Admins implicitly have cross-shop authority and do not strictly need a ShopRole.
    """
    ADMIN = 'ADMIN', _('Shop Admin')
    STAFF = 'STAFF', _('Shop Staff')
    VIEWER = 'VIEWER', _('Shop Viewer')

class TenantMember(BaseModel):
    """
    Membership linking a User to a Shop (Tenant).
    """
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='memberships',
        help_text="The Shop this user is a member of."
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tenant_memberships',
        help_text="The user holding membership in the Shop."
    )
    role = models.CharField(
        max_length=20,
        choices=ShopRole.choices,
        default=ShopRole.STAFF,
        help_text="The user's role within this Shop."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this membership is currently active."
    )

    class Meta:
        verbose_name = 'Shop Membership'
        verbose_name_plural = 'Shop Memberships'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'user'],
                name='unique_tenant_user_membership',
                condition=models.Q(deleted__isnull=True)
            ),
            models.CheckConstraint(
                check=models.Q(is_active=False) | models.Q(deleted__isnull=True),
                name='active_membership_cannot_be_deleted'
            )
        ]

    def __str__(self):
        return f"{self.user.email} - {self.tenant.name} ({self.get_role_display()})"

    def clean(self):
        super().clean()
        if self.user and not self.user.is_active:
            raise ValidationError({'user': "Cannot add an inactive user to a Shop."})
        if self.tenant and not self.tenant.is_active:
            raise ValidationError({'tenant': "Cannot add members to an inactive Shop."})

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, force_policy=None, **kwargs):
        if self.is_active:
            raise ValidationError("Cannot remove an active membership. Deactivate it first.")
        return super().delete(force_policy=force_policy, **kwargs)
