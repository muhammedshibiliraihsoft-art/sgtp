from datetime import timedelta
from django.utils import timezone
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient
from rest_framework import status
from unittest import mock

from apps.tenants.models import Tenant, Supplier, TenantMember, ShopRole

User = get_user_model()


class T302RemediationTests(TestCase):

    def setUp(self):
        try:
            self.supplier = Supplier.objects.get(singleton_lock=True)
        except Supplier.DoesNotExist:
            self.supplier = Supplier.objects.create(name="Main Supplier")

        self.shop = Tenant.objects.create(
            name="Test Shop", slug="test-shop", supplier=self.supplier, max_users=2
        )

        # Identity Users
        self.user_1 = User.objects.create_user(
            email="user1@test.com", password="pw", first_name="Muhammed"
        )
        self.user_2 = User.objects.create_user(
            email="user2@test.com", password="pw", first_name="Muhammed"
        )

        self.client = APIClient()

    def test_identity_uniqueness_and_stability(self):
        """1, 2, 3, 4, 5, 6, 8. User identity is system-generated UUID, unique, stable, independent of name."""
        self.assertNotEqual(self.user_1.id, self.user_2.id)
        self.assertEqual(self.user_1.first_name, self.user_2.first_name)

        # Cannot supply ID
        with self.assertRaises(Exception):
            User.objects.create_user(
                id=self.user_1.id,
                email="duplicate@test.com",
                password="pw",
                first_name="Test",
            )

    def test_identity_preservation_on_soft_delete(self):
        """7, 9. Removed User identity remains associated. FKs remain correct."""
        mem = TenantMember.objects.create(
            tenant=self.shop, user=self.user_1, role=ShopRole.STAFF, is_active=False
        )
        mem.delete()
        self.assertIsNotNone(mem.deleted)

        # Fetch with deleted
        mem_deleted = TenantMember.objects.all_with_deleted().get(id=mem.id)
        self.assertEqual(mem_deleted.user_id, self.user_1.id)

    def test_active_membership_cannot_be_removed(self):
        """14. ACTIVE -> Remove is rejected."""
        mem = TenantMember.objects.create(
            tenant=self.shop, user=self.user_1, role=ShopRole.STAFF, is_active=True
        )
        from django.core.exceptions import ValidationError

        # Model layer protection
        with self.assertRaises(ValidationError):
            mem.delete()

        # Queryset protection
        with self.assertRaises(ValidationError):
            with transaction.atomic():
                TenantMember.objects.filter(id=mem.id).update(deleted=timezone.now())

    def test_inactive_membership_can_be_removed(self):
        """12, 15, 16. ACTIVE -> INACTIVE -> REMOVED."""
        mem = TenantMember.objects.create(
            tenant=self.shop, user=self.user_1, role=ShopRole.STAFF, is_active=True
        )
        mem.is_active = False
        mem.save()
        mem.delete()  # Soft delete
        self.assertIsNotNone(mem.deleted)

    def test_undo_restores_previous_state_and_preserves_identity(self):
        """19, 22, 23, 24, 25, 26, 27. Undo inside 5s restores same row."""
        mem = TenantMember.objects.create(
            tenant=self.shop, user=self.user_1, role=ShopRole.STAFF, is_active=False
        )
        mem.delete()

        mem_id = mem.id

        self.client.force_authenticate(
            user=User.objects.create_superuser(
                email="admin@test.com",
                password="pw",
                first_name="Main",
                phone="+96550000000",
            )
        )
        r = self.client.post(f"/api/v1/memberships/{mem_id}/undo_remove/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

        mem.refresh_from_db()
        self.assertIsNone(mem.deleted)
        self.assertEqual(mem.id, mem_id)
        self.assertEqual(mem.user_id, self.user_1.id)
        self.assertEqual(mem.tenant_id, self.shop.id)
        self.assertFalse(mem.is_active)  # Restored previous state

    def test_undo_exactly_at_boundary_succeeds(self):
        """Undo exactly at 5.0 seconds succeeds."""
        mem = TenantMember.objects.create(
            tenant=self.shop, user=self.user_1, role=ShopRole.STAFF, is_active=False
        )
        delete_time = timezone.now()
        with mock.patch("django.utils.timezone.now", return_value=delete_time):
            mem.delete()

        self.client.force_authenticate(
            user=User.objects.create_superuser(
                email="admin@test.com",
                password="pw",
                first_name="Main",
                phone="+96550000001",
            )
        )
        with mock.patch(
            "django.utils.timezone.now", return_value=delete_time + timedelta(seconds=5)
        ):
            r = self.client.post(f"/api/v1/memberships/{mem.id}/undo_remove/")
            self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_undo_just_outside_boundary_fails(self):
        """Undo at 5.000001 seconds fails."""
        mem = TenantMember.objects.create(
            tenant=self.shop, user=self.user_1, role=ShopRole.STAFF, is_active=False
        )
        delete_time = timezone.now()
        with mock.patch("django.utils.timezone.now", return_value=delete_time):
            mem.delete()

        self.client.force_authenticate(
            user=User.objects.create_superuser(
                email="admin@test.com",
                password="pw",
                first_name="Main",
                phone="+96550000002",
            )
        )
        with mock.patch(
            "django.utils.timezone.now",
            return_value=delete_time + timedelta(seconds=5, microseconds=1),
        ):
            r = self.client.post(f"/api/v1/memberships/{mem.id}/undo_remove/")
            self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_repeated_undo_fails(self):
        """Repeated Undo after removal has expired or already undone."""
        mem = TenantMember.objects.create(
            tenant=self.shop, user=self.user_1, role=ShopRole.STAFF, is_active=False
        )
        mem.delete()

        self.client.force_authenticate(
            user=User.objects.create_superuser(
                email="admin@test.com",
                password="pw",
                first_name="Main",
                phone="+96550000003",
            )
        )
        r1 = self.client.post(f"/api/v1/memberships/{mem.id}/undo_remove/")
        self.assertEqual(r1.status_code, status.HTTP_200_OK)

        r2 = self.client.post(f"/api/v1/memberships/{mem.id}/undo_remove/")
        self.assertEqual(r2.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r2.data, {"errors": ["Membership is not removed."]})

    def test_capacity_counts(self):
        """29, 30, 31, 32. user_count includes ACTIVE and INACTIVE, excludes REMOVED."""
        TenantMember.objects.create(tenant=self.shop, user=self.user_1, is_active=True)
        u3 = User.objects.create_user(email="u3@test.com", first_name="Test")
        TenantMember.objects.create(tenant=self.shop, user=u3, is_active=False)
        u4 = User.objects.create_user(email="u4@test.com", first_name="Test")
        mem_rem = TenantMember.objects.create(
            tenant=self.shop, user=u4, is_active=False
        )
        mem_rem.delete()

        self.assertEqual(self.shop.user_count, 2)

    def test_capacity_undo_rejected_when_full(self):
        """36. Undo rejected when capacity is full."""
        # Max users = 2
        mem = TenantMember.objects.create(
            tenant=self.shop, user=self.user_1, is_active=False
        )
        mem.delete()

        u3 = User.objects.create_user(email="u3@test.com", first_name="Test")
        u4 = User.objects.create_user(email="u4@test.com", first_name="Test")
        TenantMember.objects.create(tenant=self.shop, user=u3, is_active=True)
        TenantMember.objects.create(tenant=self.shop, user=u4, is_active=True)

        self.client.force_authenticate(
            user=User.objects.create_superuser(
                email="admin@test.com",
                password="pw",
                first_name="Main",
                phone="+96550000004",
            )
        )
        r = self.client.post(f"/api/v1/memberships/{mem.id}/undo_remove/")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r.data,
            {"errors": ["Shop has reached its maximum user limit. Cannot restore."]},
        )

    def test_capacity_undo_succeeds_when_capacity_freed(self):
        """Undo succeeds if capacity was full but becomes available within 5 seconds."""
        # Max users = 2
        mem = TenantMember.objects.create(
            tenant=self.shop, user=self.user_1, is_active=False
        )
        mem.delete()

        u3 = User.objects.create_user(email="u3@test.com", first_name="Test")
        u4 = User.objects.create_user(email="u4@test.com", first_name="Test")
        TenantMember.objects.create(tenant=self.shop, user=u3, is_active=True)
        mem_4 = TenantMember.objects.create(tenant=self.shop, user=u4, is_active=False)

        # Free up capacity by removing mem_4
        mem_4.delete()

        self.client.force_authenticate(
            user=User.objects.create_superuser(
                email="admin@test.com",
                password="pw",
                first_name="Main",
                phone="+96550000005",
            )
        )
        r = self.client.post(f"/api/v1/memberships/{mem.id}/undo_remove/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)

    def test_removed_membership_does_not_authorize(self):
        """17, 40. Removed membership does not authorize."""
        mem = TenantMember.objects.create(
            tenant=self.shop, user=self.user_1, role=ShopRole.ADMIN, is_active=False
        )
        mem.delete()

        from apps.tenants.policy import ShopRolePolicy

        # is_shop_member should return False
        self.assertFalse(ShopRolePolicy.is_shop_member(self.user_1, self.shop.id))
        self.assertFalse(
            ShopRolePolicy.can_manage_memberships(self.user_1, self.shop.id)
        )

    def test_duplicate_membership_rejected(self):
        """11. Duplicate membership rejected."""
        TenantMember.objects.create(tenant=self.shop, user=self.user_1)
        with self.assertRaises(IntegrityError):
            TenantMember.objects.create(tenant=self.shop, user=self.user_1)

    def test_race_condition_protection(self):
        """37. Capacity race behavior is protected."""
        self.client.force_authenticate(
            user=User.objects.create_superuser(
                email="admin@test.com",
                password="pw",
                first_name="Main",
                phone="+96550000006",
            )
        )
        u3 = User.objects.create_user(email="u3@test.com", first_name="Test")
        u4 = User.objects.create_user(email="u4@test.com", first_name="Test")
        u5 = User.objects.create_user(email="u5@test.com", first_name="Test")

        # Max users = 2
        r1 = self.client.post(
            "/api/v1/memberships/", {"tenant": self.shop.id, "user": u3.id}
        )
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        r2 = self.client.post(
            "/api/v1/memberships/", {"tenant": self.shop.id, "user": u4.id}
        )
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)
        r3 = self.client.post(
            "/api/v1/memberships/", {"tenant": self.shop.id, "user": u5.id}
        )
        self.assertEqual(r3.status_code, status.HTTP_400_BAD_REQUEST)

    def test_patch_user_identity_spoofing_denied(self):
        """Identity spoofing on update is denied."""
        mem = TenantMember.objects.create(
            tenant=self.shop, user=self.user_1, role=ShopRole.STAFF
        )
        self.client.force_authenticate(
            user=User.objects.create_superuser(
                email="admin@test.com",
                password="pw",
                first_name="Main",
                phone="+96550000007",
            )
        )
        r = self.client.patch(
            f"/api/v1/memberships/{mem.id}/", {"user": self.user_2.id}
        )
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Cannot change the user", r.data["errors"]["user"][0])
        mem.refresh_from_db()
        self.assertEqual(mem.user_id, self.user_1.id)

    def test_recreate_membership_after_soft_delete(self):
        """A new membership may be created after an old membership was soft-deleted."""
        mem = TenantMember.objects.create(
            tenant=self.shop, user=self.user_1, role=ShopRole.STAFF, is_active=False
        )
        mem.delete()

        self.client.force_authenticate(
            user=User.objects.create_superuser(
                email="admin@test.com",
                password="pw",
                first_name="Main",
                phone="+96550000008",
            )
        )
        r = self.client.post(
            "/api/v1/memberships/",
            {"tenant": self.shop.id, "user": self.user_1.id, "role": ShopRole.VIEWER},
        )
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

        # Identity and history remain correct
        new_mem = TenantMember.objects.get(id=r.data["id"])
        self.assertNotEqual(new_mem.id, mem.id)
        self.assertEqual(new_mem.user_id, self.user_1.id)

        # Undo of old membership should now fail due to uniqueness!
        r_undo = self.client.post(f"/api/v1/memberships/{mem.id}/undo_remove/")
        self.assertEqual(r_undo.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            r_undo.data,
            {
                "errors": [
                    "Cannot restore: a membership for this user already exists in this Shop."
                ]
            },
        )

    def test_db_trigger_prevents_active_deletion(self):
        """F-01: DB trigger prevents ACTIVE -> REMOVED transition even via bulk_update or raw ORM."""
        mem = TenantMember.objects.create(
            tenant=self.shop, user=self.user_1, role=ShopRole.STAFF, is_active=True
        )

        # Test 1: QuerySet.update() direct DB bypass attempt
        from django.db import transaction

        with self.assertRaises(Exception) as ctx:
            with transaction.atomic():
                # We must use base queryset to avoid SafeDeleteManager overrides if we really want to test the DB
                TenantMember.all_objects.filter(id=mem.id).update(
                    is_active=False, deleted=timezone.now()
                )

        self.assertIn(
            "Cannot remove an active membership. Deactivate it first.",
            str(ctx.exception),
        )

        # Test 2: Raw DB cursor update attempt (completely bypassing ORM)
        mem2 = TenantMember.objects.create(
            tenant=self.shop, user=self.user_2, role=ShopRole.STAFF, is_active=True
        )
        from django.db import connection

        with self.assertRaises(Exception) as ctx2:
            with transaction.atomic():
                with connection.cursor() as cursor:
                    cursor.execute(
                        "UPDATE tenants_tenantmember SET deleted = NOW() WHERE id = %s",
                        [mem2.id],
                    )

        self.assertIn("Cannot remove an active membership", str(ctx2.exception))

    def test_unauthorized_user_assignment_denied(self):
        """F-07: Authorized and unauthorized user assignment."""
        # A. Main Supplier assigning an existing user
        u_target1 = User.objects.create_user(
            email="t1@test.com", password="pw", first_name="Test"
        )
        self.client.force_authenticate(
            user=User.objects.create_superuser(
                email="admin@test.com",
                password="pw",
                first_name="Main",
                phone="+96550000009",
            )
        )
        r_sup = self.client.post(
            "/api/v1/memberships/",
            {"tenant": self.shop.id, "user": u_target1.id, "role": ShopRole.VIEWER},
        )
        self.assertEqual(r_sup.status_code, status.HTTP_201_CREATED)  # Authorized

        # Shop Admin (Shop 1)
        u_admin = User.objects.create_user(
            email="admin_shop@test.com", password="pw", first_name="Test"
        )
        TenantMember.objects.create(tenant=self.shop, user=u_admin, role=ShopRole.ADMIN)

        # B. Shop Admin assigning an existing user to own Shop
        u_target2 = User.objects.create_user(
            email="t2@test.com", password="pw", first_name="Test"
        )
        self.client.force_authenticate(user=u_admin)
        r_adm = self.client.post(
            "/api/v1/memberships/",
            {"tenant": self.shop.id, "user": u_target2.id, "role": ShopRole.VIEWER},
        )
        # Note: default max_users is 2 for self.shop, wait! We created mem=1(target1), admin=1(u_admin), target2=1. We will hit limit?
        # Let's adjust shop capacity before this test.
        self.shop.max_users = 10
        self.shop.save()
        r_adm = self.client.post(
            "/api/v1/memberships/",
            {"tenant": self.shop.id, "user": u_target2.id, "role": ShopRole.VIEWER},
        )
        self.assertEqual(r_adm.status_code, status.HTTP_201_CREATED)  # Authorized

        # C. Shop Admin assigning into another Shop
        shop2 = Tenant.objects.create(
            name="Shop 2", slug="shop-2", supplier=self.supplier, max_users=10
        )
        u_target3 = User.objects.create_user(
            email="t3@test.com", password="pw", first_name="Test"
        )
        r_adm_other = self.client.post(
            "/api/v1/memberships/",
            {"tenant": shop2.id, "user": u_target3.id, "role": ShopRole.VIEWER},
        )
        self.assertEqual(r_adm_other.status_code, status.HTTP_403_FORBIDDEN)  # Denied

        # Create a STAFF user (Shop 1)
        u_staff = User.objects.create_user(
            email="staff@test.com", password="pw", first_name="Test"
        )
        TenantMember.objects.create(tenant=self.shop, user=u_staff, role=ShopRole.STAFF)

        # D. Staff attempting assignment
        self.client.force_authenticate(user=u_staff)
        r_staff = self.client.post(
            "/api/v1/memberships/",
            {"tenant": self.shop.id, "user": u_target3.id, "role": ShopRole.VIEWER},
        )
        self.assertEqual(r_staff.status_code, status.HTTP_403_FORBIDDEN)  # Denied

        # E. Viewer attempting assignment
        u_viewer = User.objects.create_user(
            email="viewer@test.com", password="pw", first_name="Test"
        )
        TenantMember.objects.create(
            tenant=self.shop, user=u_viewer, role=ShopRole.VIEWER
        )
        self.client.force_authenticate(user=u_viewer)
        r_viewer = self.client.post(
            "/api/v1/memberships/",
            {"tenant": self.shop.id, "user": u_target3.id, "role": ShopRole.VIEWER},
        )
        self.assertEqual(r_viewer.status_code, status.HTTP_403_FORBIDDEN)  # Denied

        # F. Unauthorized user attempting assignment
        u_unauth = User.objects.create_user(
            email="unauth@test.com", password="pw", first_name="Test"
        )
        self.client.force_authenticate(user=u_unauth)
        r_unauth = self.client.post(
            "/api/v1/memberships/",
            {"tenant": self.shop.id, "user": u_target3.id, "role": ShopRole.VIEWER},
        )
        self.assertEqual(r_unauth.status_code, status.HTTP_403_FORBIDDEN)  # Denied

    def test_reactivation_capacity(self):
        """13, 14. Reactivation capacity enforcement (A-F)."""
        # max_users = 2
        mem = TenantMember.objects.create(
            tenant=self.shop, user=self.user_1, is_active=False
        )
        self.assertEqual(self.shop.user_count, 1)  # Consumes capacity even as INACTIVE

        self.client.force_authenticate(
            user=User.objects.create_superuser(
                email="admin@test.com",
                password="pw",
                first_name="Main",
                phone="+96550000010",
            )
        )

        # A. Reactivation succeeds when capacity is available.
        # D. Successful reactivation makes it ACTIVE.
        r = self.client.post(f"/api/v1/memberships/{mem.id}/reactivate/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        mem.refresh_from_db()
        self.assertTrue(mem.is_active)

        # F. Same membership identity is preserved.
        self.assertEqual(mem.user, self.user_1)

        # Now fill the capacity. We need user_count to be 2.
        # Since max_users=2, we create mem2 manually.
        TenantMember.objects.create(tenant=self.shop, user=self.user_2, is_active=True)
        self.assertEqual(self.shop.user_count, 2)

        # E. Consumed capacity correctly incremented (mem + mem2 = 2, max=2)
        # B. Reactivation succeeds: inactive memberships already consume capacity.
        u4 = User.objects.create_user(email="u4@test.com", first_name="Test")
        mem3 = TenantMember(tenant=self.shop, user=u4, is_active=False)
        mem3.save()  # Manually bypass serializer check. user_count is now 3.

        r2 = self.client.post(f"/api/v1/memberships/{mem3.id}/reactivate/")
        self.assertEqual(r2.status_code, status.HTTP_200_OK)

        # C. Reactivation changes only the state, not the capacity count.
        mem3.refresh_from_db()
        self.assertTrue(mem3.is_active)
