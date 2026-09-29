from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APITestCase

from apps.accounts.tests.factories import create_test_user
from apps.tenants.models import (
    MembershipWorkFunction,
    ShopRole,
    Supplier,
    Tenant,
    TenantMember,
    WorkFunctionCode,
)
from apps.tenants.policy import ShopRolePolicy
from apps.tenants.services.membership import (
    deactivate_membership,
    reactivate_membership,
    remove_membership,
    undo_remove_membership,
)
from apps.tenants.services.work_functions import set_membership_work_functions

User = get_user_model()
CATALOG = [code for code, _label in WorkFunctionCode.choices]


class MembershipWorkFunctionModelTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.shop = Tenant.objects.create(
            supplier=self.supplier,
            name="Functions Model Shop",
            slug="functions-model-shop",
            max_users=20,
        )
        self.user = create_test_user(
            owning_shop=self.shop,
            email="functions-model@example.test",
            first_name="Model",
        )
        self.membership = TenantMember.objects.create(
            tenant=self.shop, user=self.user, role=ShopRole.STAFF
        )

    def test_empty_single_multiple_and_complete_catalog_are_supported(self):
        self.assertEqual(self.membership.work_functions.count(), 0)
        rows = [
            MembershipWorkFunction.objects.create(
                membership=self.membership, function_code=code
            )
            for code in CATALOG
        ]
        self.assertEqual(len(rows), 7)
        self.assertEqual(
            set(self.membership.work_functions.values_list("function_code", flat=True)),
            set(CATALOG),
        )
        self.assertEqual(rows[0].membership_id, self.membership.pk)
        self.assertNotIn("user", {field.name for field in rows[0]._meta.fields})
        self.assertNotIn("tenant", {field.name for field in rows[0]._meta.fields})

    def test_database_rejects_duplicate_active_assignment(self):
        MembershipWorkFunction.objects.create(
            membership=self.membership, function_code=WorkFunctionCode.CUTTING
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MembershipWorkFunction.objects.create(
                    membership=self.membership, function_code=WorkFunctionCode.CUTTING
                )

    def test_database_rejects_code_outside_fixed_catalog(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MembershipWorkFunction.objects.create(
                    membership=self.membership, function_code="CHECK"
                )

    def test_assignment_history_row_cannot_be_reassigned_or_rewritten(self):
        row = MembershipWorkFunction.objects.create(
            membership=self.membership, function_code=WorkFunctionCode.SALES
        )
        row.function_code = WorkFunctionCode.QC
        with self.assertRaises(DjangoValidationError):
            row.save()


class MembershipWorkFunctionAPITests(APITestCase):
    def setUp(self):
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.shop_a = self.make_shop("Functions Shop A", "functions-shop-a")
        self.shop_b = self.make_shop("Functions Shop B", "functions-shop-b")
        self.admin_a, self.membership_admin_a = self.make_member(
            "functions-admin-a@example.test", self.shop_a, ShopRole.ADMIN
        )
        self.staff_a, self.membership_staff_a = self.make_member(
            "functions-staff-a@example.test", self.shop_a, ShopRole.STAFF
        )
        self.viewer_a, self.membership_viewer_a = self.make_member(
            "functions-viewer-a@example.test", self.shop_a, ShopRole.VIEWER
        )
        self.admin_b, self.membership_admin_b = self.make_member(
            "functions-admin-b@example.test", self.shop_b, ShopRole.ADMIN
        )
        self.foreign_member, self.foreign_membership = self.make_member(
            "functions-member-b@example.test", self.shop_b, ShopRole.STAFF
        )
        self.main_supplier = User.objects.create_superuser(
            email="functions-main@example.test",
            password="Safe-Test-Password-451!",
            first_name="Supplier",
            phone="+96550000881",
        )

    def make_shop(self, name, slug):
        return Tenant.objects.create(
            supplier=self.supplier, name=name, slug=slug, max_users=20
        )

    @staticmethod
    def make_member(email, shop, role):
        user = create_test_user(
            owning_shop=shop,
            email=email,
            password="Safe-Test-Password-451!",
            first_name="Function",
            phone=None,
        )
        return user, TenantMember.objects.create(tenant=shop, user=user, role=role)

    @staticmethod
    def url(shop, membership):
        return reverse(
            "v1:membership_work_functions",
            kwargs={"shop_id": shop.pk, "membership_id": membership.pk},
        )

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def test_shop_admin_can_read_and_atomically_set_any_same_shop_role(self):
        self.authenticate(self.admin_a)
        for membership in (
            self.membership_admin_a,
            self.membership_staff_a,
            self.membership_viewer_a,
        ):
            with self.subTest(role=membership.role):
                response = self.client.put(
                    self.url(self.shop_a, membership),
                    {"functions": ["STITCHING", "SALES", "QC"]},
                    format="json",
                )
                self.assertEqual(
                    response.status_code, status.HTTP_200_OK, response.data
                )
                self.assertEqual(
                    response.data["functions"], ["SALES", "STITCHING", "QC"]
                )
                self.assertEqual(response.data["shop_id"], self.shop_a.pk)
                self.assertEqual(
                    membership.role, TenantMember.objects.get(pk=membership.pk).role
                )
                self.assertEqual(
                    self.client.get(self.url(self.shop_a, membership)).data[
                        "functions"
                    ],
                    ["SALES", "STITCHING", "QC"],
                )

    def test_put_is_idempotent_and_replaces_the_whole_set_in_catalog_order(self):
        self.authenticate(self.admin_a)
        url = self.url(self.shop_a, self.membership_staff_a)
        first = self.client.put(
            url,
            {"functions": ["CUTTING", "MEASUREMENT"]},
            format="json",
        )
        second = self.client.put(
            url,
            {"functions": ["MEASUREMENT", "CUTTING"]},
            format="json",
        )
        replacement = self.client.put(url, {"functions": ["FINISHING"]}, format="json")
        self.assertEqual(first.data["functions"], ["MEASUREMENT", "CUTTING"])
        self.assertEqual(second.data["functions"], first.data["functions"])
        self.assertEqual(replacement.data["functions"], ["FINISHING"])
        self.assertEqual(
            MembershipWorkFunction.objects.filter(
                membership=self.membership_staff_a
            ).count(),
            1,
        )
        self.assertEqual(
            MembershipWorkFunction.objects.all_with_deleted()
            .filter(membership=self.membership_staff_a)
            .count(),
            3,
        )

    def test_empty_set_is_valid_and_duplicate_or_unknown_codes_are_rejected(self):
        self.authenticate(self.admin_a)
        url = self.url(self.shop_a, self.membership_staff_a)
        self.assertEqual(
            self.client.put(url, {"functions": []}, format="json").data["functions"],
            [],
        )
        duplicate = self.client.put(url, {"functions": ["QC", "QC"]}, format="json")
        unknown = self.client.put(url, {"functions": ["CHECK"]}, format="json")
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(unknown.status_code, status.HTTP_400_BAD_REQUEST)

    def test_staff_and_viewer_cannot_manage_functions_or_gain_authority_from_them(self):
        for user, membership, assigned in (
            (self.staff_a, self.membership_staff_a, ["CUTTING"]),
            (self.viewer_a, self.membership_viewer_a, ["QC", "CASHIER", "SALES"]),
        ):
            with self.subTest(role=membership.role):
                self.authenticate(self.admin_a)
                set_membership_work_functions(
                    actor=self.admin_a,
                    shop_id=self.shop_a.pk,
                    membership_id=membership.pk,
                    function_codes=assigned,
                )
                self.assertFalse(
                    ShopRolePolicy.can_manage_memberships(user, self.shop_a.pk)
                )
                self.authenticate(user)
                response = self.client.put(
                    self.url(self.shop_a, membership),
                    {"functions": ["SALES"]},
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
                membership.refresh_from_db()
                self.assertEqual(membership.role, user.tenant_memberships.get().role)
                self.assertEqual(user.owning_shop_id, self.shop_a.pk)

    def test_foreign_membership_is_indistinguishable_from_missing_membership(self):
        self.authenticate(self.admin_a)
        missing_id = "00000000-0000-0000-0000-000000000001"
        foreign = self.client.get(self.url(self.shop_a, self.foreign_membership))
        missing = self.client.get(
            reverse(
                "v1:membership_work_functions",
                kwargs={"shop_id": self.shop_a.pk, "membership_id": missing_id},
            )
        )
        foreign_shop = self.client.get(self.url(self.shop_b, self.membership_admin_b))
        self.assertEqual(foreign.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(missing.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(foreign.data, missing.data)
        self.assertEqual(foreign_shop.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(
            foreign_shop.data["errors"]["code"], "shop_context_unavailable"
        )

    def test_main_supplier_does_not_receive_shop_work_function_management_authority(
        self,
    ):
        self.authenticate(self.main_supplier)
        response = self.client.put(
            self.url(self.shop_a, self.membership_staff_a),
            {"functions": ["SALES"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            MembershipWorkFunction.objects.filter(
                membership=self.membership_staff_a
            ).exists()
        )

    def test_anonymous_request_keeps_authentication_401(self):
        response = self.client.get(self.url(self.shop_a, self.membership_staff_a))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_generic_membership_api_does_not_add_a_globally_scoped_function_field(self):
        self.authenticate(self.main_supplier)
        response = self.client.get("/api/v1/memberships/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("functions", response.data["results"][0])

    def test_function_assignment_does_not_change_viewer_role_or_membership_authority(
        self,
    ):
        self.authenticate(self.admin_a)
        response = self.client.put(
            self.url(self.shop_a, self.membership_viewer_a),
            {"functions": ["QC", "CASHIER", "SALES"]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.membership_viewer_a.refresh_from_db()
        self.viewer_a.refresh_from_db()
        self.assertEqual(self.membership_viewer_a.role, ShopRole.VIEWER)
        self.assertEqual(self.viewer_a.owning_shop_id, self.shop_a.pk)
        self.assertFalse(self.viewer_a.is_superuser)
        self.assertFalse(
            ShopRolePolicy.can_manage_memberships(self.viewer_a, self.shop_a.pk)
        )


class MembershipWorkFunctionLifecycleTests(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.shop = Tenant.objects.create(
            supplier=self.supplier,
            name="Functions Lifecycle Shop",
            slug="functions-lifecycle-shop",
            max_users=20,
        )
        self.admin = create_test_user(
            owning_shop=self.shop,
            email="functions-lifecycle-admin@example.test",
            first_name="Lifecycle",
        )
        self.admin_membership = TenantMember.objects.create(
            tenant=self.shop, user=self.admin, role=ShopRole.ADMIN
        )
        self.staff = create_test_user(
            owning_shop=self.shop,
            email="functions-lifecycle-staff@example.test",
            first_name="Lifecycle",
        )
        self.membership = TenantMember.objects.create(
            tenant=self.shop, user=self.staff, role=ShopRole.STAFF
        )
        set_membership_work_functions(
            actor=self.admin,
            shop_id=self.shop.pk,
            membership_id=self.membership.pk,
            function_codes=["MEASUREMENT", "CUTTING"],
        )

    def codes(self):
        return list(
            MembershipWorkFunction.objects.filter(membership=self.membership)
            .order_by("function_code")
            .values_list("function_code", flat=True)
        )

    def test_deactivation_and_reactivation_preserve_current_functions(self):
        deactivate_membership(actor=self.admin, membership_id=self.membership.pk)
        self.assertEqual(self.codes(), ["CUTTING", "MEASUREMENT"])
        reactivate_membership(actor=self.admin, membership_id=self.membership.pk)
        self.assertEqual(self.codes(), ["CUTTING", "MEASUREMENT"])

    def test_remove_and_valid_five_second_undo_restore_function_history(self):
        deactivate_membership(actor=self.admin, membership_id=self.membership.pk)
        remove_membership(actor=self.admin, membership_id=self.membership.pk)
        self.assertFalse(
            MembershipWorkFunction.objects.filter(membership=self.membership).exists()
        )
        historical = MembershipWorkFunction.objects.all_with_deleted().filter(
            membership=self.membership
        )
        self.assertEqual(historical.count(), 2)
        self.assertTrue(all(row.deleted is not None for row in historical))
        undo_remove_membership(actor=self.admin, membership_id=self.membership.pk)
        self.assertEqual(self.codes(), ["CUTTING", "MEASUREMENT"])

    def test_expired_undo_keeps_function_history_removed(self):
        deactivate_membership(actor=self.admin, membership_id=self.membership.pk)
        remove_membership(actor=self.admin, membership_id=self.membership.pk)
        removed = TenantMember.objects.all_with_deleted().get(pk=self.membership.pk)
        expired_at = removed.deleted + timedelta(seconds=5, microseconds=1)

        with patch(
            "apps.tenants.services.membership.timezone.now", return_value=expired_at
        ):
            with self.assertRaises(ValidationError):
                undo_remove_membership(
                    actor=self.admin, membership_id=self.membership.pk
                )

        history = MembershipWorkFunction.objects.all_with_deleted().filter(
            membership=self.membership
        )
        self.assertEqual(history.count(), 2)
        self.assertTrue(all(row.deleted is not None for row in history))


class MembershipWorkFunctionMigrationTests(TransactionTestCase):
    """The additive migration never assigns inferred functions to old members."""

    migrate_from = [
        ("tenants", "0008_tenant_default_currency_tenant_default_locale_and_more")
    ]
    migrate_to = [("tenants", "0009_membership_work_functions")]

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_existing_membership_is_preserved_with_zero_functions(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        old_state = executor.loader.project_state(self.migrate_from)
        OldSupplier = old_state.apps.get_model("tenants", "Supplier")
        OldTenant = old_state.apps.get_model("tenants", "Tenant")
        OldMembership = old_state.apps.get_model("tenants", "TenantMember")

        supplier, _created = OldSupplier.objects.get_or_create(
            singleton_lock=True,
            defaults={"name": "Main Supplier", "is_active": True},
        )
        shop = OldTenant.objects.create(
            supplier=supplier,
            name="Legacy functions migration Shop",
            slug="legacy-functions-migration-shop",
            max_users=20,
        )
        current_shop = Tenant.objects.defer(
            "default_currency", "default_locale", "default_timezone"
        ).get(pk=shop.pk)
        user = create_test_user(
            owning_shop=current_shop,
            email="legacy-functions-migration@example.test",
            first_name="Legacy",
        )
        removed = OldMembership.objects.create(
            tenant_id=shop.pk,
            user_id=user.pk,
            role=ShopRole.VIEWER,
            is_active=False,
        )
        removed_pk = removed.pk
        OldMembership.objects.filter(pk=removed_pk).update(deleted=timezone.now())
        active = OldMembership.objects.create(
            tenant_id=shop.pk,
            user_id=user.pk,
            role=ShopRole.STAFF,
            is_active=True,
        )
        memberships = [removed_pk, active.pk]
        expected = [
            (
                row.pk,
                row.user_id,
                row.tenant_id,
                row.role,
                row.is_active,
                row.deleted,
            )
            for row in OldMembership.objects.filter(pk__in=memberships).order_by("pk")
        ]

        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_to)
        migrated_memberships = TenantMember.objects.all_with_deleted().filter(
            pk__in=memberships
        )
        actual = [
            (row.pk, row.user_id, row.tenant_id, row.role, row.is_active, row.deleted)
            for row in migrated_memberships.order_by("pk")
        ]
        self.assertCountEqual(actual, expected)
        self.assertFalse(
            MembershipWorkFunction.objects.filter(
                membership_id__in=[row[0] for row in expected]
            ).exists()
        )
