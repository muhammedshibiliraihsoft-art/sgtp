from django.core.exceptions import ValidationError as DjangoValidationError
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient
from unittest.mock import MagicMock

from apps.accounts.models import User
from apps.accounts.tests.factories import create_test_user
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember
from apps.tenants.services.membership import create_membership
from importlib import import_module

preflight_and_backfill_shop_ownership = import_module(
    "apps.accounts.migrations.0005_user_shop_ownership"
).preflight_and_backfill_shop_ownership


class ShopScopedAccountTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.supplier, _ = Supplier.objects.get_or_create(singleton_lock=True)
        self.main = User.objects.create_superuser(
            email="scope-main@example.test",
            password="Main-Password-912!",
            first_name="Main",
            phone="+96550100001",
        )
        self.shop_a = self.make_shop("scope-shop-a")
        self.shop_b = self.make_shop("scope-shop-b")
        self.admin_a = self.make_member(
            self.shop_a, "scope-admin-a@example.test", ShopRole.ADMIN
        )
        self.admin_b = self.make_member(
            self.shop_b, "scope-admin-b@example.test", ShopRole.ADMIN
        )

    def make_shop(self, slug, *, max_users=10):
        return Tenant.objects.create(
            supplier=self.supplier, name=slug, slug=slug, max_users=max_users
        )

    def make_member(self, shop, email, role):
        user = create_test_user(
            owning_shop=shop,
            email=email,
            password="Member-Password-913!",
            first_name="Staff",
            phone=f"+965501{User.objects.count() + 2:05d}",
        )
        TenantMember.objects.create(tenant=shop, user=user, role=role)
        return user

    def test_shop_admin_creates_only_staff_or_viewer_in_url_shop(self):
        self.client.force_authenticate(self.admin_a)
        for role in (ShopRole.STAFF, ShopRole.VIEWER):
            email = f"{role.lower()}-created@example.test"
            response = self.client.post(
                f"/api/v1/shops/{self.shop_a.pk}/users/",
                {"email": email, "first_name": "New", "login_id": f"{role.lower()}_created" if role == ShopRole.STAFF else None, "role": role},
                format="json",
            )
            self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(response["Cache-Control"], "no-store")
            user = User.objects.get(email=email)
            self.assertEqual(user.owning_shop_id, self.shop_a.pk)
            if role == ShopRole.STAFF:
                self.assertTrue(user.must_change_password)
                self.assertTrue(user.check_password(response.data["initial_password"]))
                self.assertNotEqual(user.password, response.data["initial_password"])
            else:
                self.assertIsNone(user.login_id)
                self.assertFalse(user.login_enabled)
                self.assertFalse(user.has_usable_password())
                self.assertNotIn("initial_password", response.data)
            self.assertEqual(
                TenantMember.objects.get(user=user).role,
                role,
            )

        denied = self.client.post(
            f"/api/v1/shops/{self.shop_a.pk}/users/",
            {
                "first_name": "No",
                "role": ShopRole.ADMIN,
                "login_id": "unauthorized_admin",
                "email": "new-admin@example.test",
                "phone": "+96550100030",
            },
            format="json",
        )
        self.assertEqual(denied.status_code, 403)

    def test_shop_admin_cannot_spoof_or_create_in_foreign_shop(self):
        self.client.force_authenticate(self.admin_a)
        spoof = self.client.post(
            f"/api/v1/shops/{self.shop_a.pk}/users/",
            {
                "first_name": "Spoof",
                "role": ShopRole.STAFF,
                "shop": str(self.shop_b.pk),
            },
            format="json",
        )
        foreign = self.client.post(
            f"/api/v1/shops/{self.shop_b.pk}/users/",
            {"first_name": "Foreign", "role": ShopRole.STAFF},
            format="json",
        )
        self.assertEqual(spoof.status_code, 400)
        self.assertEqual(foreign.status_code, 404)
        self.assertFalse(
            User.objects.filter(first_name__in=["Spoof", "Foreign"]).exists()
        )

    def test_main_supplier_creates_selected_shop_roles(self):
        self.client.force_authenticate(self.main)
        for index, role in enumerate(ShopRole.values):
            login_id = f"role{index}" if role != ShopRole.VIEWER else None
            response = self.client.post(
                "/api/v1/auth/users/",
                {
                    "shop": str(self.shop_a.pk),
                    "role": role,
                    "first_name": f"Role{index}",
                    "login_id": login_id,
                    "email": f"role{index}@example.test",
                    "phone": f"+965501000{index + 40:02d}",
                },
                format="json",
            )
            if role == ShopRole.ADMIN:
                # The fixture already supplies one effective ADMIN.
                self.assertEqual(response.status_code, 201, response.data)
            else:
                self.assertEqual(response.status_code, 201, response.data)
            self.assertEqual(
                User.objects.get(email=f"role{index}@example.test").owning_shop_id,
                self.shop_a.pk,
            )

    def test_account_creation_requires_shop_and_rolls_back_on_capacity_failure(self):
        self.client.force_authenticate(self.main)
        missing = self.client.post(
            "/api/v1/auth/users/",
            {"first_name": "Orphan", "role": ShopRole.STAFF},
            format="json",
        )
        self.assertEqual(missing.status_code, 400)

        full_shop = self.make_shop("scope-full-shop", max_users=0)
        before = User.objects.count()
        full = self.client.post(
            "/api/v1/auth/users/",
            {
                "shop": str(full_shop.pk),
                "role": ShopRole.STAFF,
                "first_name": "No Slot",
                "email": "no-slot@example.test",
            },
            format="json",
        )
        self.assertEqual(full.status_code, 400)
        self.assertEqual(User.objects.count(), before)

    def test_same_person_can_have_independent_accounts_in_distinct_shops(self):
        a = self.make_member(self.shop_a, "same-a@example.test", ShopRole.STAFF)
        b = self.make_member(self.shop_b, "same-b@example.test", ShopRole.STAFF)
        a.first_name = b.first_name = "Same Person"
        a.save(update_fields=["first_name"])
        b.save(update_fields=["first_name"])
        self.assertNotEqual(a.pk, b.pk)
        self.assertNotEqual(a.user_code, b.user_code)
        self.assertNotEqual(a.password, b.password)

    def test_ownership_is_immutable_and_foreign_membership_is_rejected(self):
        member = self.make_member(self.shop_a, "owned-a@example.test", ShopRole.STAFF)
        member.owning_shop = self.shop_b
        with self.assertRaises(DjangoValidationError):
            member.save(update_fields=["owning_shop"])

        for state in ("active", "inactive", "removed"):
            with self.subTest(state=state):
                candidate = self.make_member(
                    self.shop_a, f"{state}@example.test", ShopRole.STAFF
                )
                membership = TenantMember.objects.get(user=candidate)
                if state in ("inactive", "removed"):
                    membership.is_active = False
                    membership.save(update_fields=["is_active"])
                if state == "removed":
                    membership.delete()
                with self.assertRaises(ValidationError) as error:
                    create_membership(
                        self.main, self.shop_b.pk, candidate.pk, ShopRole.STAFF
                    )
                self.assertIn("not owned", str(error.exception).lower())

    def test_shop_admin_resets_only_current_same_shop_staff(self):
        target = self.make_member(
            self.shop_a, "reset-staff@example.test", ShopRole.STAFF
        )
        self.client.force_authenticate(self.admin_a)
        allowed = self.client.post(
            f"/api/v1/auth/users/{target.pk}/reset-credentials/", {}, format="json"
        )
        self.assertEqual(allowed.status_code, 200, allowed.data)
        self.assertEqual(allowed["Cache-Control"], "no-store")
        target.refresh_from_db()
        self.assertTrue(target.must_change_password)
        self.assertTrue(target.check_password(allowed.data["temporary_password"]))

        viewer = self.make_member(self.shop_a, "reset-viewer@example.test", ShopRole.VIEWER)
        denied_viewer = self.client.post(
            f"/api/v1/auth/users/{viewer.pk}/reset-credentials/", {}, format="json"
        )
        self.assertEqual(denied_viewer.status_code, 404)

        for candidate in (
            self.admin_a,
            self.make_member(self.shop_b, "foreign-reset@example.test", ShopRole.STAFF),
        ):
            denied = self.client.post(
                f"/api/v1/auth/users/{candidate.pk}/reset-credentials/",
                {},
                format="json",
            )
            self.assertEqual(denied.status_code, 404)

        removed = self.make_member(
            self.shop_a, "removed-reset@example.test", ShopRole.STAFF
        )
        removed_membership = TenantMember.objects.get(user=removed)
        removed_membership.is_active = False
        removed_membership.save(update_fields=["is_active"])
        removed_membership.delete()
        denied_removed = self.client.post(
            f"/api/v1/auth/users/{removed.pk}/reset-credentials/", {}, format="json"
        )
        self.assertEqual(denied_removed.status_code, 404)

    def test_migration_preflight_rejects_multi_shop_history_with_user_id(self):
        user = self.make_member(
            self.shop_a, "migration-multi@example.test", ShopRole.STAFF
        )
        apps = MagicMock()
        apps.get_model.return_value = User
        schema_editor = MagicMock()
        schema_editor.connection.alias = "default"
        cursor = schema_editor.connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [
            (user.pk, self.shop_a.pk),
            (user.pk, self.shop_b.pk),
        ]

        with self.assertRaisesRegex(RuntimeError, str(user.pk)):
            preflight_and_backfill_shop_ownership(apps, schema_editor)

    def test_migration_preflight_rejects_unowned_account_without_fabrication(self):
        user = self.make_member(
            self.shop_a, "migration-unowned@example.test", ShopRole.STAFF
        )
        apps = MagicMock()
        apps.get_model.return_value = User
        schema_editor = MagicMock()
        schema_editor.connection.alias = "default"
        schema_editor.connection.cursor.return_value.__enter__.return_value.fetchall.return_value = (
            []
        )

        with self.assertRaisesRegex(RuntimeError, str(user.pk)):
            preflight_and_backfill_shop_ownership(apps, schema_editor)
