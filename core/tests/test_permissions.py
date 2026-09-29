from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.db import connection, models
from django.test import TestCase
from rest_framework import generics, serializers, status
from rest_framework.exceptions import NotFound
from rest_framework.filters import OrderingFilter
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.common.views import TenantScopedMixin
from apps.tenants.context_views import ShopContextMixin
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember
from backend.core.models import BaseModelWithTenant
from core.permissions import DenyAll, IsOwner, IsTenantMember

User = get_user_model()


class DummyTestModel(BaseModelWithTenant):
    """Temporary test-only Shop-owned model; it has no production migration."""

    owner_id = models.UUIDField()

    class Meta:
        app_label = "core"
        ordering = ["created_at"]


class DummyTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DummyTestModel
        fields = "__all__"


class DummyTestView(ShopContextMixin, TenantScopedMixin, generics.RetrieveAPIView):
    queryset = DummyTestModel.objects.all()
    serializer_class = DummyTestSerializer
    permission_classes = [IsTenantMember, IsOwner]


class DummyTestListView(ShopContextMixin, TenantScopedMixin, generics.ListAPIView):
    queryset = DummyTestModel.objects.all()
    serializer_class = DummyTestSerializer
    permission_classes = [IsTenantMember]
    filter_backends = [OrderingFilter]
    ordering_fields = ["created_at"]
    ordering = ["created_at"]


class DummyTestCreateView(ShopContextMixin, TenantScopedMixin, generics.CreateAPIView):
    queryset = DummyTestModel.objects.all()
    serializer_class = DummyTestSerializer
    permission_classes = [IsTenantMember]


class DummyTestUpdateView(ShopContextMixin, TenantScopedMixin, generics.UpdateAPIView):
    queryset = DummyTestModel.objects.all()
    serializer_class = DummyTestSerializer
    permission_classes = [IsTenantMember]


class PermissionsAndScopingTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(DummyTestModel)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(DummyTestModel)
        super().tearDownClass()

    def setUp(self):
        self.factory = APIRequestFactory()
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.shop_a = self.make_shop("Shop A", "proof-shop-a")
        self.shop_b = self.make_shop("Shop B", "proof-shop-b")
        self.user1 = User.objects.create_user(email="user1@test.com", password="pw", first_name='Test')
        self.user2 = User.objects.create_user(email="user2@test.com", password="pw", first_name='Test')
        self.main_supplier = User.objects.create_superuser(
            email="main@test.com", password="pw",
            first_name='Main', phone='+96550000000',
        )
        self.member(self.user1, self.shop_a, ShopRole.ADMIN)
        self.member(self.user1, self.shop_b, ShopRole.VIEWER)
        self.member(self.user2, self.shop_a, ShopRole.STAFF)
        self.obj_a = DummyTestModel.objects.create(
            tenant=self.shop_a, owner_id=self.user1.pk
        )
        self.obj_b = DummyTestModel.objects.create(
            tenant=self.shop_b, owner_id=self.user2.pk
        )

    def make_shop(self, name, slug):
        return Tenant.objects.create(
            supplier=self.supplier,
            name=name,
            slug=slug,
            max_users=20,
            is_active=True,
        )

    @staticmethod
    def member(user, shop, role):
        return TenantMember.objects.create(tenant=shop, user=user, role=role)

    def request(self, user, shop, method="get", path=None, payload=None):
        path = path or f"/api/v1/shops/{shop.pk}/objects/"
        request = getattr(self.factory, method)(path, payload or {}, format="json")
        force_authenticate(request, user=user)
        return request

    def test_missing_object_returns_404(self):
        request = self.request(
            self.user1, self.shop_a, path=f"/shops/{self.shop_a.pk}/objects/"
        )
        response = DummyTestView.as_view()(
            request, shop_id=self.shop_a.pk, pk="missing"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_foreign_object_uuid_returns_404_for_multishop_user(self):
        request = self.request(self.user1, self.shop_a)
        response = DummyTestView.as_view()(
            request, shop_id=self.shop_a.pk, pk=self.obj_b.pk
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_in_scope_object_but_failed_action_permission_returns_403(self):
        request = self.request(self.user2, self.shop_a)
        response = DummyTestView.as_view()(
            request, shop_id=self.shop_a.pk, pk=self.obj_a.pk
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_in_scope_and_authorized_object_returns_200(self):
        request = self.request(self.user1, self.shop_a)
        response = DummyTestView.as_view()(
            request, shop_id=self.shop_a.pk, pk=self.obj_a.pk
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_lists_and_counts_contain_only_selected_shop_even_for_main_supplier(self):
        DummyTestModel.objects.all().delete()
        for _ in range(3):
            DummyTestModel.objects.create(tenant=self.shop_a, owner_id=self.user1.pk)
        for _ in range(7):
            DummyTestModel.objects.create(tenant=self.shop_b, owner_id=self.user2.pk)

        for user in (self.user1, self.main_supplier):
            request = self.request(
                user,
                self.shop_a,
                path=f"/api/v1/shops/{self.shop_a.pk}/objects/?ordering=-created_at",
            )
            response = DummyTestListView.as_view()(request, shop_id=self.shop_a.pk)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["count"], 3)
            self.assertTrue(
                all(
                    str(row["tenant"]) == str(self.shop_a.pk)
                    for row in response.data["results"]
                )
            )

        request = self.request(
            self.user1,
            self.shop_a,
            path=f"/api/v1/shops/{self.shop_a.pk}/objects/?tenant_id={self.shop_b.pk}",
        )
        response = DummyTestListView.as_view()(request, shop_id=self.shop_a.pk)
        self.assertEqual(response.data["count"], 3)

    def test_create_ownership_is_forced_from_authorized_context(self):
        request = self.request(
            self.user1,
            self.shop_a,
            method="post",
            payload={"tenant": str(self.shop_b.pk), "owner_id": str(self.user1.pk)},
        )
        response = DummyTestCreateView.as_view()(request, shop_id=self.shop_a.pk)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(str(response.data["tenant"]), str(self.shop_a.pk))

    def test_update_cannot_reparent_to_another_shop(self):
        request = self.request(
            self.user1,
            self.shop_a,
            method="patch",
            payload={"tenant": str(self.shop_b.pk)},
        )
        response = DummyTestUpdateView.as_view()(
            request, shop_id=self.shop_a.pk, pk=self.obj_a.pk
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.obj_a.refresh_from_db()
        self.assertEqual(self.obj_a.tenant_id, self.shop_a.pk)

    def test_missing_context_fails_as_configuration_error_not_unscoped_query(self):
        view = DummyTestView()
        view.request = SimpleNamespace(user=self.user1)
        view.kwargs = {"shop_id": self.shop_a.pk}
        with self.assertRaises(ImproperlyConfigured):
            view.get_queryset()

        view.request = SimpleNamespace(
            user=self.user1,
            shop_context=SimpleNamespace(shop=self.shop_a, actor_user_id=self.user1.pk),
            tenant_id=self.shop_a.pk,
        )
        view.kwargs = {}
        with self.assertRaises(ImproperlyConfigured):
            view.get_queryset()

    def test_context_url_or_compatibility_alias_mismatch_returns_404(self):
        request = self.request(self.user1, self.shop_a)
        request = DummyTestView().initialize_request(request)
        request.shop_context = SimpleNamespace(
            shop=self.shop_a, actor_user_id=self.user1.pk
        )
        request.tenant_id = self.shop_a.pk
        view = DummyTestView()
        view.request = request
        view.kwargs = {"shop_id": self.shop_b.pk}
        with self.assertRaises(NotFound):
            view.get_queryset()

        view.kwargs = {"shop_id": self.shop_a.pk}
        request.tenant_id = self.shop_b.pk
        with self.assertRaises(NotFound):
            view.get_queryset()

        request.tenant_id = self.shop_a.pk
        request.shop_context = SimpleNamespace(
            shop=self.shop_a, actor_user_id=self.user2.pk
        )
        with self.assertRaises(NotFound):
            view.get_queryset()

    def test_soft_deleted_rows_are_not_returned(self):
        deleted = DummyTestModel.objects.create(
            tenant=self.shop_a, owner_id=self.user1.pk
        )
        deleted.delete()
        request = self.request(self.user1, self.shop_a)
        response = DummyTestView.as_view()(
            request, shop_id=self.shop_a.pk, pk=deleted.pk
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_object_permission_binds_membership_and_main_supplier_to_selected_shop(
        self,
    ):
        request = self.request(self.user1, self.shop_a)
        request = DummyTestView().initialize_request(request)
        from apps.tenants.context import resolve_shop_context

        request.shop_context = resolve_shop_context(self.user1, self.shop_a.pk)
        request.tenant_id = self.shop_a.pk
        permission = IsTenantMember()
        self.assertFalse(permission.has_object_permission(request, None, self.obj_b))
        self.assertTrue(permission.has_object_permission(request, None, self.obj_a))

        main_request = self.request(self.main_supplier, self.shop_a)
        main_request = DummyTestView().initialize_request(main_request)
        main_request.shop_context = resolve_shop_context(
            self.main_supplier, self.shop_a.pk
        )
        main_request.tenant_id = self.shop_a.pk
        self.assertTrue(
            permission.has_object_permission(main_request, None, self.obj_a)
        )
        self.assertFalse(
            permission.has_object_permission(main_request, None, self.obj_b)
        )

    def test_missing_context_denies_object_permission(self):
        request = self.request(self.user1, self.shop_a)
        request = DummyTestView().initialize_request(request)
        self.assertFalse(
            IsTenantMember().has_object_permission(request, None, self.obj_a)
        )

    def test_denyall_permission(self):
        request = self.request(self.user1, self.shop_a)
        request = DummyTestView().initialize_request(request)
        permission = DenyAll()
        self.assertFalse(permission.has_permission(request, None))
        self.assertFalse(permission.has_object_permission(request, None, self.obj_a))
