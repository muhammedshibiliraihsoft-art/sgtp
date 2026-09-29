from django.db import transaction
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from apps.tenants.models import TenantMember, ShopRole


def deactivate_global_user(actor: User, target_user: User):
    """
    Safely deactivate a global User, ensuring it does not leave any Shop without an ADMIN.
    """
    if not target_user.is_active:
        return target_user

    with transaction.atomic():
        # 1. Identify affected Shop IDs where the target user is an effective ACTIVE ADMIN
        affected_shop_ids = list(
            TenantMember.objects.filter(
                user=target_user,
                role=ShopRole.ADMIN,
                is_active=True,
                deleted__isnull=True,
                tenant__is_active=True
            ).values_list('tenant_id', flat=True).distinct()
        )

        # 2. Sort deterministically and lock affected Shop rows in order
        affected_shop_ids.sort()
        from apps.tenants.models import Tenant
        if affected_shop_ids:
            list(Tenant.objects.filter(id__in=affected_shop_ids).select_for_update().order_by('id'))

        # 3. Lock/re-read the target User
        target_user = User.objects.select_for_update().get(pk=target_user.pk)
        if not target_user.is_active:
            return target_user

        # 4. Verify every affected Shop retains >= 1 OTHER effective ACTIVE ADMIN
        if affected_shop_ids:
            # Re-read active ADMIN counts for these shops, excluding the target user
            for shop_id in affected_shop_ids:
                other_admins_count = TenantMember.objects.filter(
                    tenant_id=shop_id,
                    role=ShopRole.ADMIN,
                    is_active=True,
                    deleted__isnull=True,
                    user__is_active=True
                ).exclude(user=target_user).count()

                if other_admins_count < 1:
                    raise ValidationError(
                        "Cannot deactivate user: it would leave one or more Shops without an active ADMIN."
                    )

        # 5. Safe to deactivate
        target_user.is_active = False
        # Preserve attribution if applicable (Django abstract user doesn't have updated_by, but if it does, set it)
        # Assuming standard Django User attributes for now.
        target_user.save(update_fields=['is_active'])

        return target_user
