from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.clients.models import Client, RelatedPerson
from apps.tenants.models import (
    MembershipWorkFunction,
    ShopRole,
    Supplier,
    Tenant,
    TenantMember,
    WorkFunctionCode,
)


class ClientApiTests(APITestCase):
    def setUp(self):
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.shop_a = self.make_shop("Client Shop A", "client-shop-a")
        self.shop_b = self.make_shop("Client Shop B", "client-shop-b")
        self.admin = self.make_user("client-admin", self.shop_a)
        self.staff = self.make_user("client-staff", self.shop_a)
        self.viewer = self.make_user("client-viewer", self.shop_a)
        self.member(self.admin, self.shop_a, ShopRole.ADMIN)
        self.member(self.staff, self.shop_a, ShopRole.STAFF)
        self.viewer_membership = self.member(self.viewer, self.shop_a, ShopRole.VIEWER)
        self.main = User.objects.create_superuser(
            email="client-main@example.test",
            password="Safe-Test-Password-293!",
            first_name="Main",
            phone="+96550001001",
        )

    def make_shop(self, name, slug):
        return Tenant.objects.create(
            supplier=self.supplier, name=name, slug=slug, max_users=20
        )

    @staticmethod
    def make_user(name, shop):
        return User.objects.create_user(
            email=f"{name}@example.test",
            password="Safe-Test-Password-293!",
            first_name=name,
            owning_shop=shop,
        )

    @staticmethod
    def member(user, shop, role, *, active=True):
        return TenantMember.objects.create(
            user=user, tenant=shop, role=role, is_active=active
        )

    @staticmethod
    def clients_url(shop):
        return f"/api/v1/shops/{shop.pk}/clients/"

    @staticmethod
    def related_url(shop, client_id):
        return f"/api/v1/shops/{shop.pk}/clients/{client_id}/related-persons/"

    def authenticate(self, user):
        self.client.force_authenticate(user)

    def create_client(self, *, name="Ada Tailor", **extra):
        return Client.objects.create(tenant=self.shop_a, name=name, **extra)

    def test_admin_staff_viewer_and_main_supplier_permissions(self):
        self.authenticate(self.admin)
        created = self.client.post(
            self.clients_url(self.shop_a), {"name": "Admin Client"}, format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        client_id = created.data["id"]
        deleted = self.client.delete(f"{self.clients_url(self.shop_a)}{client_id}/")
        self.assertEqual(deleted.status_code, status.HTTP_204_NO_CONTENT)

        self.authenticate(self.staff)
        created = self.client.post(
            self.clients_url(self.shop_a), {"name": "Staff Client"}, format="json"
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        updated = self.client.patch(
            f"{self.clients_url(self.shop_a)}{created.data['id']}/",
            {"name": "Updated Staff Client"},
            format="json",
        )
        self.assertEqual(updated.status_code, status.HTTP_200_OK)
        denied_delete = self.client.delete(
            f"{self.clients_url(self.shop_a)}{created.data['id']}/"
        )
        self.assertEqual(denied_delete.status_code, status.HTTP_403_FORBIDDEN)

        self.authenticate(self.viewer)
        self.assertEqual(
            self.client.get(self.clients_url(self.shop_a)).status_code,
            status.HTTP_200_OK,
        )
        denied_create = self.client.post(
            self.clients_url(self.shop_a), {"name": "Viewer Client"}, format="json"
        )
        self.assertEqual(denied_create.status_code, status.HTTP_403_FORBIDDEN)

        self.authenticate(self.main)
        supplier_create = self.client.post(
            self.clients_url(self.shop_b), {"name": "Main Client"}, format="json"
        )
        self.assertEqual(supplier_create.status_code, status.HTTP_201_CREATED)

    def test_cross_shop_client_uuid_and_search_are_non_disclosing(self):
        foreign = Client.objects.create(tenant=self.shop_b, name="Private Person")
        self.authenticate(self.admin)
        list_response = self.client.get(
            self.clients_url(self.shop_a), {"search": "Private"}
        )
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(list_response.data["count"], 0)
        detail = self.client.get(f"{self.clients_url(self.shop_a)}{foreign.pk}/")
        self.assertEqual(detail.status_code, status.HTTP_404_NOT_FOUND)
        update = self.client.patch(
            f"{self.clients_url(self.shop_a)}{foreign.pk}/",
            {"name": "Stolen"},
            format="json",
        )
        self.assertEqual(update.status_code, status.HTTP_404_NOT_FOUND)
        delete = self.client.delete(f"{self.clients_url(self.shop_a)}{foreign.pk}/")
        self.assertEqual(delete.status_code, status.HTTP_404_NOT_FOUND)

    def test_unicode_phone_uuid_search_and_pagination(self):
        client = self.create_client(
            name="مريم Bánā",
            phone="+٩٦٥ ٥٠٠٠-١٢٣٤",
            email="Mariam@Example.test",
        )
        self.authenticate(self.admin)
        for search in ("مريم", "+96550001234", str(client.pk)):
            response = self.client.get(
                self.clients_url(self.shop_a), {"search": search}
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.data["count"], 1)
            self.assertEqual(response.data["results"][0]["id"], str(client.pk))
        self.assertEqual(client.phone_normalized, "+96550001234")
        for index in range(20):
            self.create_client(name=f"Page Client {index:02d}")
        page_two = self.client.get(self.clients_url(self.shop_a), {"page": 2})
        self.assertEqual(page_two.data["count"], 21)
        self.assertEqual(len(page_two.data["results"]), 1)

    def test_duplicate_phone_and_email_warn_but_allow_and_never_merge(self):
        self.authenticate(self.admin)
        first = self.client.post(
            self.clients_url(self.shop_a),
            {"name": "First", "phone": "+965 5000 1234", "email": "X@EXAMPLE.TEST"},
            format="json",
        )
        second = self.client.post(
            self.clients_url(self.shop_a),
            {"name": "Second", "phone": "+96550001234", "email": "x@example.test"},
            format="json",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            {warning["field"] for warning in second.data["warnings"]},
            {"phone", "email"},
        )
        self.assertEqual(Client.objects.filter(tenant=self.shop_a).count(), 2)
        self.assertEqual(second.data["warnings"][0]["code"], "possible_duplicate")

    def test_related_person_duplicates_warn_and_are_allowed(self):
        parent = self.create_client(name="Primary")
        self.authenticate(self.admin)
        url = self.related_url(self.shop_a, parent.pk)
        first = self.client.post(
            url,
            {"name": "Relative One", "phone": "٠٠٩٦٥٥٥٥٥", "email": "rel@example.test"},
            format="json",
        )
        second = self.client.post(
            url,
            {"name": "Relative Two", "phone": "009655555", "email": "REL@example.test"},
            format="json",
        )
        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            {warning["field"] for warning in second.data["warnings"]},
            {"phone", "email"},
        )
        self.assertEqual(RelatedPerson.objects.filter(primary_client=parent).count(), 2)

    def test_duplicate_warning_on_contact_update_is_shop_local(self):
        foreign = Client.objects.create(
            tenant=self.shop_b, name="Other Shop", phone="+96555551234"
        )
        first = self.create_client(name="First", phone="+96555551234")
        second = self.create_client(name="Second")
        self.authenticate(self.admin)
        response = self.client.patch(
            f"{self.clients_url(self.shop_a)}{second.pk}/",
            {"phone": "+965 5555 1234"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["warnings"][0]["matches"][0]["id"], str(first.pk)
        )
        self.assertNotEqual(
            response.data["warnings"][0]["matches"][0]["id"], str(foreign.pk)
        )

    def test_related_person_uses_primary_client_and_cannot_cross_shop(self):
        parent = self.create_client(name="Primary")
        foreign_parent = Client.objects.create(tenant=self.shop_b, name="Foreign")
        self.authenticate(self.staff)
        result = self.client.post(
            self.related_url(self.shop_a, parent.pk),
            {"name": "Family Member", "phone": "٥٠٠٠"},
            format="json",
        )
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        person = RelatedPerson.objects.get(pk=result.data["id"])
        self.assertEqual(person.tenant_id, self.shop_a.pk)
        self.assertEqual(person.primary_client_id, parent.pk)
        self.assertEqual(person.primary_client_id, parent.pk)  # future billing owner
        denied = self.client.post(
            self.related_url(self.shop_a, foreign_parent.pk),
            {"name": "Cross Shop"},
            format="json",
        )
        self.assertEqual(denied.status_code, status.HTTP_404_NOT_FOUND)

        with self.assertRaises(ValidationError):
            RelatedPerson.objects.create(
                tenant=self.shop_a,
                primary_client=foreign_parent,
                name="Direct cross-shop attempt",
            )

    def test_related_person_crud_and_foreign_object_non_disclosure(self):
        parent = self.create_client(name="Primary")
        foreign_parent = Client.objects.create(tenant=self.shop_b, name="Other")
        foreign_person = RelatedPerson.objects.create(
            tenant=self.shop_b, primary_client=foreign_parent, name="Hidden"
        )
        self.authenticate(self.admin)
        created = self.client.post(
            self.related_url(self.shop_a, parent.pk),
            {"name": "Relative"},
            format="json",
        )
        self.assertEqual(created.status_code, status.HTTP_201_CREATED)
        detail_url = f"{self.related_url(self.shop_a, parent.pk)}{created.data['id']}/"
        self.assertEqual(
            self.client.patch(
                detail_url, {"name": "Updated"}, format="json"
            ).status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            self.client.get(
                f"{self.related_url(self.shop_a, parent.pk)}{foreign_person.pk}/"
            ).status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.delete(detail_url).status_code,
            status.HTTP_204_NO_CONTENT,
        )

    def test_soft_deleted_records_are_hidden_and_delete_preserves_row(self):
        record = self.create_client(name="Soft Delete")
        self.authenticate(self.admin)
        response = self.client.delete(f"{self.clients_url(self.shop_a)}{record.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Client.objects.filter(pk=record.pk).exists())
        self.assertTrue(
            Client.all_objects.filter(pk=record.pk, deleted__isnull=False).exists()
        )

    def test_primary_client_soft_delete_preserves_and_hides_related_history(self):
        parent = self.create_client(name="Primary History")
        related = RelatedPerson.objects.create(
            tenant=self.shop_a, primary_client=parent, name="Related History"
        )
        self.authenticate(self.admin)
        response = self.client.delete(f"{self.clients_url(self.shop_a)}{parent.pk}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(RelatedPerson.objects.filter(pk=related.pk).exists())
        self.assertTrue(
            RelatedPerson.all_objects.filter(
                pk=related.pk, deleted__isnull=False
            ).exists()
        )

    def test_inactive_membership_has_no_operational_client_access(self):
        self.member(
            self.make_user("inactive", self.shop_a),
            self.shop_a,
            ShopRole.STAFF,
            active=False,
        )
        inactive = User.objects.get(email="inactive@example.test")
        self.authenticate(inactive)
        response = self.client.get(self.clients_url(self.shop_a))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        removed_user = self.make_user("removed", self.shop_a)
        removed_membership = self.member(
            removed_user, self.shop_a, ShopRole.STAFF, active=False
        )
        removed_membership.delete()
        self.authenticate(removed_user)
        removed_response = self.client.get(self.clients_url(self.shop_a))
        self.assertEqual(removed_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_work_function_does_not_grant_viewer_write_access(self):
        MembershipWorkFunction.objects.create(
            membership=self.viewer_membership,
            function_code=WorkFunctionCode.SALES,
        )
        self.authenticate(self.viewer)
        response = self.client.post(
            self.clients_url(self.shop_a), {"name": "Function Viewer"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_no_client_code_tags_or_work_number_search_contract(self):
        record = self.create_client(name="No Work Code")
        self.authenticate(self.admin)
        response = self.client.get(
            self.clients_url(self.shop_a), {"search": "WORK-2042"}
        )
        self.assertEqual(response.data["count"], 0)
        self.assertNotIn(
            "client_code",
            response.data["results"][0] if response.data["results"] else {},
        )
        self.assertFalse(hasattr(record, "tags"))
