"""Request-local resolution of explicitly selected Shop context."""

from dataclasses import dataclass
from typing import Optional

from django.core.exceptions import ValidationError
from rest_framework.exceptions import APIException, NotAuthenticated

from apps.tenants.models import Tenant, TenantMember
from apps.tenants.policy import ShopRolePolicy


class ShopContextUnavailable(APIException):
    """Uniform, non-disclosing response for any Shop context denial."""

    status_code = 404
    default_code = "shop_context_unavailable"
    default_detail = {
        "code": default_code,
        "detail": "Shop not found.",
    }


@dataclass(frozen=True)
class ShopRequestContext:
    """The trusted Shop and actor-specific authorization for one request."""

    shop: Tenant
    actor_user_id: object
    membership: Optional[TenantMember]
    is_main_supplier: bool

    @property
    def role(self) -> Optional[str]:
        if self.membership is None:
            return None
        return self.membership.role


def resolve_shop_context(user, shop_id) -> ShopRequestContext:
    """Resolve an active Shop and authorize this User for that explicit Shop."""
    if not user or not getattr(user, "is_authenticated", False):
        raise NotAuthenticated()
    if not getattr(user, "is_active", False):
        raise NotAuthenticated()

    try:
        # The default SafeDelete manager intentionally excludes deleted Shops.
        shop = Tenant.objects.get(pk=shop_id, is_active=True)
    except (Tenant.DoesNotExist, ValueError, ValidationError):
        raise ShopContextUnavailable() from None

    if ShopRolePolicy.is_main_supplier_admin(user):
        return ShopRequestContext(
            shop=shop,
            actor_user_id=user.pk,
            membership=None,
            is_main_supplier=True,
        )

    membership = ShopRolePolicy.get_active_membership(user, shop.pk)
    if membership is None:
        raise ShopContextUnavailable()

    return ShopRequestContext(
        shop=shop,
        actor_user_id=user.pk,
        membership=membership,
        is_main_supplier=False,
    )
