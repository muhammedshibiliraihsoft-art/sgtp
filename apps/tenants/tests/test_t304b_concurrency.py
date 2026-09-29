import threading
from concurrent.futures import ThreadPoolExecutor

from django.db import close_old_connections, connection
from django.test import TransactionTestCase
from rest_framework.exceptions import ValidationError

from apps.accounts.models import User
from apps.accounts.services.user_lifecycle import deactivate_global_user
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember
from apps.tenants.services.membership import (
    change_membership_role,
    create_shop_with_first_admin,
)


class T304BConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.assertEqual(
            connection.vendor, "postgresql", "These lock tests require PostgreSQL."
        )
        self.supplier, _ = Supplier.objects.get_or_create(singleton_lock=True)
        self.actor = User.objects.create_superuser(
            email="concurrency-main@example.test",
            password="pw",
            first_name="Main",
            phone="+96550999999",
        )

    def user(self, number):
        return User.objects.create_user(
            email=f"concurrency-{number}@example.test",
            password="pw",
            first_name="Tailor",
            phone=f"+96550002{number:03d}",
        )

    def shop(self, slug):
        return Tenant.objects.create(
            supplier=self.supplier, name=slug, slug=slug, max_users=10
        )

    @staticmethod
    def concurrently(*operations):
        gate = threading.Barrier(len(operations))

        def run(operation):
            close_old_connections()
            try:
                gate.wait(timeout=10)
                try:
                    operation()
                    return "ok"
                except (ValidationError, PermissionError) as exc:
                    return type(exc).__name__
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=len(operations)) as pool:
            return list(pool.map(run, operations))

    def test_two_simultaneous_promotions_never_create_third_admin(self):
        shop = self.shop("race-promote")
        first = self.user(1)
        candidates = [self.user(2), self.user(3)]
        TenantMember.objects.create(tenant=shop, user=first, role=ShopRole.ADMIN)
        memberships = [
            TenantMember.objects.create(tenant=shop, user=user, role=ShopRole.STAFF)
            for user in candidates
        ]

        results = self.concurrently(
            *[
                lambda membership=membership: change_membership_role(
                    self.actor, membership.pk, ShopRole.ADMIN
                )
                for membership in memberships
            ]
        )

        self.assertCountEqual(results, ["ok", "ValidationError"])
        self.assertEqual(
            TenantMember.objects.filter(
                tenant=shop,
                role=ShopRole.ADMIN,
                is_active=True,
                deleted__isnull=True,
                user__is_active=True,
            ).count(),
            2,
        )

    def test_demote_and_global_deactivate_cannot_remove_both_admins(self):
        shop = self.shop("race-remove-admins")
        demote_user, deactivate_user = self.user(4), self.user(5)
        demote_membership = TenantMember.objects.create(
            tenant=shop, user=demote_user, role=ShopRole.ADMIN
        )
        TenantMember.objects.create(
            tenant=shop, user=deactivate_user, role=ShopRole.ADMIN
        )

        results = self.concurrently(
            lambda: change_membership_role(
                self.actor, demote_membership.pk, ShopRole.STAFF
            ),
            lambda: deactivate_global_user(self.actor, deactivate_user),
        )

        self.assertCountEqual(results, ["ok", "ValidationError"])
        self.assertEqual(
            TenantMember.objects.filter(
                tenant=shop,
                role=ShopRole.ADMIN,
                is_active=True,
                deleted__isnull=True,
                user__is_active=True,
            ).count(),
            1,
        )

    def test_first_admin_creation_races_global_user_deactivation_safely(self):
        first_admin = self.user(6)

        def create_shop():
            create_shop_with_first_admin(
                self.actor,
                {
                    "name": "race-first-admin",
                    "slug": "race-first-admin",
                    "max_users": 2,
                },
                first_admin.pk,
            )

        self.concurrently(
            lambda: deactivate_global_user(self.actor, first_admin), create_shop
        )

        first_admin.refresh_from_db()
        shop = Tenant.objects.filter(slug="race-first-admin").first()
        if shop:
            self.assertTrue(first_admin.is_active)
            self.assertEqual(
                TenantMember.objects.filter(
                    tenant=shop,
                    user=first_admin,
                    role=ShopRole.ADMIN,
                    is_active=True,
                    deleted__isnull=True,
                ).count(),
                1,
            )
        else:
            self.assertFalse(first_admin.is_active)
