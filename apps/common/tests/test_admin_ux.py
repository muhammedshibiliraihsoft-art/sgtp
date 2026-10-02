from django.contrib import admin
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.accounts.admin import UserAdmin
from apps.accounts.models import User
from apps.accounts.tests.factories import create_test_user
from apps.catalog.admin import CatalogRecordAdmin
from apps.catalog.models import DesignVersion, GarmentFamily, StyleOptionImage
from apps.clients.admin import ClientAdmin
from apps.clients.models import Client
from apps.common.admin import MainSupplierReadOnlyAdmin, status_badge
from apps.tenants.admin import TenantAdmin
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember


class DjangoAdminUXTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.supplier, _ = Supplier.objects.get_or_create(
            singleton_lock=True, defaults={"name": "Main Supplier"}
        )
        cls.shop = Tenant.objects.create(
            supplier=cls.supplier,
            name="Admin UX Shop",
            slug="admin-ux-shop",
            max_users=10,
        )
        cls.main = User.objects.create_superuser(
            email="admin-ux-main@example.test",
            password="Strong-Password-993!",
            first_name="Main",
            phone="+96551112222",
        )
        cls.staff = create_test_user(
            owning_shop=cls.shop,
            email="admin-ux-staff@example.test",
            password="Strong-Password-994!",
            first_name="Staff",
            phone="+96551112223",
        )
        cls.membership = TenantMember.objects.create(
            tenant=cls.shop, user=cls.staff, role=ShopRole.STAFF
        )
        cls.client_record = Client.objects.create(
            tenant=cls.shop, name="Private Client", email="client@example.test"
        )

    def setUp(self):
        self.factory = RequestFactory()
        self.admin_request = self.factory.get("/admin/")
        self.admin_request.user = self.main
        self.staff_request = self.factory.get("/admin/")
        self.staff_request.user = self.staff

    def test_admin_branding_uses_internal_names(self):
        self.assertEqual(admin.site.site_header, "BiRKy Administration")
        self.assertEqual(admin.site.site_title, "BiRKy Admin")
        self.assertEqual(admin.site.index_title, "Internal Management")

    def test_main_supplier_can_access_internal_model_surfaces(self):
        for model in (User, Tenant, TenantMember, Client, GarmentFamily):
            model_admin = admin.site._registry[model]
            self.assertTrue(model_admin.has_module_permission(self.admin_request))
            self.assertTrue(model_admin.has_view_permission(self.admin_request))

    def test_shop_staff_cannot_access_user_admin_directly(self):
        model_admin = admin.site._registry[User]
        self.assertFalse(model_admin.has_module_permission(self.staff_request))
        self.assertFalse(model_admin.has_view_permission(self.staff_request))
        self.assertFalse(model_admin.has_change_permission(self.staff_request))

    def test_shop_staff_cannot_access_client_admin_directly(self):
        model_admin = admin.site._registry[Client]
        self.assertFalse(model_admin.has_module_permission(self.staff_request))
        self.assertFalse(model_admin.has_view_permission(self.staff_request))

    def test_user_creation_and_deletion_remain_disabled(self):
        model_admin = admin.site._registry[User]
        self.assertFalse(model_admin.has_add_permission(self.admin_request))
        self.assertFalse(model_admin.has_delete_permission(self.admin_request))

    def test_user_password_change_route_remains_removed(self):
        model_admin = UserAdmin(User, AdminSite())
        self.assertFalse(
            any(
                (url.name or "").endswith("_user_password_change")
                for url in model_admin.get_urls()
            )
        )

    def test_shop_create_delete_remain_disabled(self):
        model_admin = admin.site._registry[Tenant]
        self.assertFalse(model_admin.has_add_permission(self.admin_request))
        self.assertFalse(
            model_admin.has_delete_permission(self.admin_request, self.shop)
        )

    def test_shop_owner_remains_readonly_in_admin(self):
        model_admin = admin.site._registry[Tenant]
        self.assertIn(
            "supplier", model_admin.get_readonly_fields(self.admin_request, self.shop)
        )

    def test_shop_membership_lifecycle_remains_readonly(self):
        model_admin = admin.site._registry[TenantMember]
        self.assertFalse(model_admin.has_add_permission(self.admin_request))
        self.assertFalse(
            model_admin.has_change_permission(self.admin_request, self.membership)
        )
        self.assertFalse(
            model_admin.has_delete_permission(self.admin_request, self.membership)
        )

    def test_shop_counts_are_annotated_in_one_queryset(self):
        model_admin = TenantAdmin(Tenant, admin.site)
        with self.assertNumQueries(1):
            shop = model_admin.get_queryset(self.admin_request).get(pk=self.shop.pk)
            self.assertEqual(shop._admin_user_count, 1)

    def test_catalog_records_are_readonly_for_main_supplier(self):
        model_admin = admin.site._registry[GarmentFamily]
        self.assertIsInstance(model_admin, MainSupplierReadOnlyAdmin)
        self.assertFalse(model_admin.has_add_permission(self.admin_request))
        self.assertFalse(model_admin.has_change_permission(self.admin_request))
        self.assertFalse(model_admin.has_delete_permission(self.admin_request))

    def test_published_design_version_fields_are_readonly(self):
        model_admin = CatalogRecordAdmin(DesignVersion, admin.site)
        names = {field.name for field in DesignVersion._meta.concrete_fields}
        self.assertTrue(
            names.issubset(set(model_admin.get_readonly_fields(self.admin_request)))
        )

    def test_private_image_upload_fields_are_excluded_from_admin_forms(self):
        model_admin = CatalogRecordAdmin(StyleOptionImage, admin.site)
        self.assertIn("image", model_admin.get_exclude(self.admin_request))
        self.assertNotIn("image", model_admin.get_readonly_fields(self.admin_request))
        self.assertNotIn("image", model_admin.get_list_display(self.admin_request))

    def test_client_detail_and_list_queries_remain_shop_linked(self):
        model_admin = ClientAdmin(Client, admin.site)
        row = model_admin.get_queryset(self.admin_request).get(pk=self.client_record.pk)
        self.assertEqual(row.tenant_id, self.shop.pk)
        self.assertEqual(row.email, "client@example.test")

    def test_admin_index_is_available_to_main_supplier_and_groups_sections(self):
        self.client.force_login(self.main)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "BiRKy Administration")
        self.assertContains(response, "Business")
        self.assertContains(response, "Garments &amp; Designs")
        self.assertContains(response, "Measurements")
        self.assertContains(response, "Users &amp; Access")

    def test_admin_index_denies_shop_staff(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("admin:index"))
        self.assertEqual(response.status_code, 302)

    def test_status_badge_escapes_untrusted_labels(self):
        rendered = str(status_badge("unsafe", "<img src=x>"))
        self.assertIn("admin-status-badge--neutral", rendered)
        self.assertIn("&lt;img src=x&gt;", rendered)
        self.assertNotIn("<img", rendered)

    def test_django_groups_are_not_a_separate_admin_surface(self):
        from django.contrib.auth.models import Group

        self.assertNotIn(Group, admin.site._registry)
