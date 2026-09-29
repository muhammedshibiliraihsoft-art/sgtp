"""Small test-only factories that model durable ordinary-User ownership."""

import uuid

from apps.accounts.models import User
from apps.tenants.models import Supplier, Tenant


def create_test_user(*, owning_shop=None, **fields):
    if owning_shop is None:
        supplier, _ = Supplier.objects.get_or_create(singleton_lock=True)
        owning_shop = Tenant.objects.create(
            supplier=supplier,
            name="Isolated test account Shop",
            slug=f"test-user-{uuid.uuid4().hex[:12]}",
            max_users=100,
        )
        # These accounts are unrelated to Shop API visibility tests.
        owning_shop.delete()
    return User.objects.create_user(owning_shop=owning_shop, **fields)
