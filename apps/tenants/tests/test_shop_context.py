from django.urls import reverse
from types import SimpleNamespace
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import User
from apps.tenants.context import resolve_shop_context
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember
from core.permissions import IsTenantMember


class ShopContextAPITests(APITestCase):
    def setUp(self):
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.shop_a = self.make_shop("Shop A", "shop-a")
        self.shop_b = self.make_shop("Shop B", "shop-b")
        self.user = self.make_user("member@example.test")

    def make_shop(self, name, slug, *, active=True):
        return Tenant.objects.create(
            supplier=self.supplier,
            name=name,
            slug=slug,
            max_users=20,
            is_active=active,
        )

    @staticmethod
    def make_user(email, *, superuser=False, password_change=False):
        return User.objects.create_user(
            email=email,
            password="Safe-Test-Password-293!",
            is_superuser=superuser,
            is_staff=superuser,
            must_change_password=password_change,
        )

    def authenticate(self, user, *, auth_version=None):
        token = AccessToken.for_user(user)
        token["auth_version"] = (
            user.auth_version if auth_version is None else auth_version
        )
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    @staticmethod
    def context_url(shop_id):
        return reverse("v1:shop_context", kwargs={"shop_id": shop_id})

    def request_context(self, user, shop_id, *, path_shop_id=None, **headers):
        self.authenticate(user)
        url = self.context_url(path_shop_id or shop_id)
        return self.client.get(url, **headers)

    def test_anonymous_and_invalid_or_revoked_access_tokens_keep_401(self):
        url = self.context_url(self.shop_a.pk)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.credentials(HTTP_AUTHORIZATION="Bearer not-a-token")
        self.assertEqual(self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED)

        self.authenticate(self.user, auth_version=self.user.auth_version - 1)
        self.assertEqual(self.client.get(url).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_password_change_gate_denies_before_shop_resolution(self):
        gated_user = self.make_user("first-login@example.test", password_change=True)
        self.authenticate(gated_user)

        existing = self.client.get(self.context_url(self.shop_a.pk))
        nonexistent = self.client.get(
            self.context_url("00000000-0000-0000-0000-000000000001")
        )

        self.assertEqual(existing.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(existing.status_code, nonexistent.status_code)

    def test_active_membership_all_roles_can_enter_context(self):
        for index, role in enumerate(ShopRole.values):
            with self.subTest(role=role):
                user = self.make_user(f"role-{index}@example.test")
                TenantMember.objects.create(
                    tenant=self.shop_a, user=user, role=role, is_active=True
                )
                response = self.request_context(user, self.shop_a.pk)

                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.data["shop_id"], str(self.shop_a.pk))
                self.assertEqual(response.data["role"], role)
                self.assertFalse(response.data["is_main_supplier"])

    def test_foreign_nonexistent_inactive_and_deleted_shops_are_identical_404(self):
        TenantMember.objects.create(
            tenant=self.shop_a,
            user=self.user,
            role=ShopRole.STAFF,
            is_active=True,
        )
        TenantMember.objects.create(
            tenant=self.shop_b,
            user=self.make_user("other-member@example.test"),
            role=ShopRole.STAFF,
            is_active=True,
        )
        inactive_shop = self.make_shop("Inactive", "inactive", active=False)
        deleted_shop = self.make_shop("Deleted", "deleted")
        deleted_shop.delete()
        missing_shop_id = "00000000-0000-0000-0000-000000000001"

        denied_ids = [
            self.shop_b.pk,
            inactive_shop.pk,
            deleted_shop.pk,
            missing_shop_id,
        ]
        responses = [self.request_context(self.user, shop_id) for shop_id in denied_ids]

        self.assertTrue(
            all(r.status_code == status.HTTP_404_NOT_FOUND for r in responses)
        )
        self.assertTrue(all(r.data == responses[0].data for r in responses))
        self.assertEqual(
            responses[0].data,
            {
                "errors": {
                    "code": "shop_context_unavailable",
                    "detail": "Shop not found.",
                }
            },
        )

    def test_inactive_and_removed_memberships_are_denied_with_same_404(self):
        inactive = TenantMember.objects.create(
            tenant=self.shop_a,
            user=self.user,
            role=ShopRole.STAFF,
            is_active=False,
        )
        inactive_response = self.request_context(self.user, self.shop_a.pk)

        inactive.delete()
        removed_response = self.request_context(self.user, self.shop_a.pk)
        missing_response = self.request_context(
            self.user, "00000000-0000-0000-0000-000000000001"
        )

        self.assertEqual(inactive_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(removed_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(inactive_response.data, removed_response.data)
        self.assertEqual(removed_response.data, missing_response.data)

    def test_reactivated_membership_can_enter_again(self):
        membership = TenantMember.objects.create(
            tenant=self.shop_a,
            user=self.user,
            role=ShopRole.ADMIN,
            is_active=False,
        )
        membership.delete()
        membership.undelete()
        self.assertEqual(
            self.request_context(self.user, self.shop_a.pk).status_code,
            status.HTTP_404_NOT_FOUND,
        )

        membership.is_active = True
        membership.save(update_fields=["is_active"])
        self.assertEqual(
            self.request_context(self.user, self.shop_a.pk).status_code,
            status.HTTP_200_OK,
        )

    def test_is_tenant_member_requires_the_authenticated_users_resolved_context(self):
        membership = TenantMember.objects.create(
            tenant=self.shop_a,
            user=self.user,
            role=ShopRole.STAFF,
            is_active=True,
        )
        context = resolve_shop_context(self.user, self.shop_a.pk)
        permission = IsTenantMember()

        request = SimpleNamespace(
            user=self.user,
            shop_context=context,
            tenant_id=self.shop_a.pk,
        )
        self.assertTrue(permission.has_permission(request, None))

        request.tenant_id = self.shop_b.pk
        self.assertFalse(permission.has_permission(request, None))

        main_admin = self.make_user("main-without-context@example.test", superuser=True)
        no_context = SimpleNamespace(user=main_admin)
        self.assertFalse(permission.has_permission(no_context, None))

        self.assertEqual(membership.tenant_id, context.shop.pk)

    def test_main_supplier_must_explicitly_select_each_active_shop(self):
        main_admin = self.make_user("main@example.test", superuser=True)

        first = self.request_context(main_admin, self.shop_a.pk)
        second = self.request_context(main_admin, self.shop_b.pk)

        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertEqual(first.data["shop_id"], str(self.shop_a.pk))
        self.assertEqual(second.data["shop_id"], str(self.shop_b.pk))
        self.assertIsNone(first.data["role"])
        self.assertTrue(first.data["is_main_supplier"])

        inactive_shop = self.make_shop("Inactive", "inactive-main", active=False)
        denied = self.request_context(main_admin, inactive_shop.pk)
        self.assertEqual(denied.status_code, status.HTTP_404_NOT_FOUND)

    def test_incidental_main_supplier_membership_does_not_define_context_role(self):
        main_admin = self.make_user("main-member@example.test", superuser=True)
        TenantMember.objects.create(
            tenant=self.shop_a,
            user=main_admin,
            role=ShopRole.VIEWER,
            is_active=False,
        )

        response = self.request_context(main_admin, self.shop_a.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_main_supplier"])
        self.assertIsNone(response.data["role"])

    def test_each_request_resolves_url_shop_without_global_context_leak(self):
        TenantMember.objects.create(
            tenant=self.shop_a, user=self.user, role=ShopRole.ADMIN
        )
        second_user = self.make_user("second@example.test")
        TenantMember.objects.create(
            tenant=self.shop_b, user=second_user, role=ShopRole.VIEWER
        )

        first = self.request_context(self.user, self.shop_a.pk)
        second = self.request_context(second_user, self.shop_b.pk)

        self.assertEqual(first.data["shop_id"], str(self.shop_a.pk))
        self.assertEqual(second.data["shop_id"], str(self.shop_b.pk))
        self.assertEqual(first.data["role"], ShopRole.ADMIN)
        self.assertEqual(second.data["role"], ShopRole.VIEWER)

    def test_user_with_multiple_shop_roles_gets_role_for_selected_path(self):
        TenantMember.objects.create(
            tenant=self.shop_a, user=self.user, role=ShopRole.ADMIN
        )
        TenantMember.objects.create(
            tenant=self.shop_b, user=self.user, role=ShopRole.VIEWER
        )

        first = self.request_context(self.user, self.shop_a.pk)
        second = self.request_context(self.user, self.shop_b.pk)

        self.assertEqual(first.data["role"], ShopRole.ADMIN)
        self.assertEqual(second.data["role"], ShopRole.VIEWER)

    def test_query_and_header_shop_selectors_cannot_override_url(self):
        TenantMember.objects.create(
            tenant=self.shop_a, user=self.user, role=ShopRole.STAFF
        )
        self.authenticate(self.user)
        response = self.client.get(
            f"{self.context_url(self.shop_a.pk)}?shop_id={self.shop_b.pk}",
            HTTP_X_SHOP_ID=str(self.shop_b.pk),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["shop_id"], str(self.shop_a.pk))

    def test_malformed_uuid_does_not_match_shop_context_route(self):
        self.authenticate(self.user)
        response = self.client.get("/api/v1/shops/not-a-uuid/context/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_shop_defaults_are_not_returned_by_context_contract(self):
        self.shop_a.default_locale = "ar-KW"
        self.shop_a.default_timezone = "Asia/Kuwait"
        self.shop_a.default_currency = "KWD"
        self.shop_a.save(
            update_fields=[
                "default_locale",
                "default_timezone",
                "default_currency",
            ]
        )
        TenantMember.objects.create(
            tenant=self.shop_a, user=self.user, role=ShopRole.STAFF
        )

        response = self.request_context(self.user, self.shop_a.pk)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(response.data), {"shop_id", "role", "is_main_supplier"})

    def test_resolver_requires_authenticated_active_user(self):
        from django.contrib.auth.models import AnonymousUser
        from rest_framework.exceptions import NotAuthenticated

        with self.assertRaises(NotAuthenticated):
            resolve_shop_context(AnonymousUser(), self.shop_a.pk)
