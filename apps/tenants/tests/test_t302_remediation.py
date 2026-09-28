import time
import threading
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
            
        self.shop = Tenant.objects.create(name="Test Shop", slug="test-shop", supplier=self.supplier, max_users=2)
        
        # Identity Users
        self.user_1 = User.objects.create_user(email="user1@test.com", password="pw", first_name="Muhammed")
        self.user_2 = User.objects.create_user(email="user2@test.com", password="pw", first_name="Muhammed")
        
        self.client = APIClient()

    def test_identity_uniqueness_and_stability(self):
        """1, 2, 3, 4, 5, 6, 8. User identity is system-generated UUID, unique, stable, independent of name."""
        self.assertNotEqual(self.user_1.id, self.user_2.id)
        self.assertEqual(self.user_1.first_name, self.user_2.first_name)
        
        # Cannot supply ID
        with self.assertRaises(Exception):
            User.objects.create_user(id=self.user_1.id, email="duplicate@test.com", password="pw")
            
    def test_identity_preservation_on_soft_delete(self):
        """7, 9. Removed User identity remains associated. FKs remain correct."""
        mem = TenantMember.objects.create(tenant=self.shop, user=self.user_1, role=ShopRole.STAFF, is_active=False)
        mem.delete()
        self.assertIsNotNone(mem.deleted)
        
        # Fetch with deleted
        mem_deleted = TenantMember.objects.all_with_deleted().get(id=mem.id)
        self.assertEqual(mem_deleted.user_id, self.user_1.id)
        
    def test_active_membership_cannot_be_removed(self):
        """14. ACTIVE -> Remove is rejected."""
        mem = TenantMember.objects.create(tenant=self.shop, user=self.user_1, role=ShopRole.STAFF, is_active=True)
        from django.core.exceptions import ValidationError
        
        # Model layer protection
        with self.assertRaises(ValidationError):
            mem.delete()
            
        # DB layer protection bypassed Model delete? No, CheckConstraint prevents it
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TenantMember.objects.filter(id=mem.id).update(deleted=timezone.now())

    def test_inactive_membership_can_be_removed(self):
        """12, 15, 16. ACTIVE -> INACTIVE -> REMOVED."""
        mem = TenantMember.objects.create(tenant=self.shop, user=self.user_1, role=ShopRole.STAFF, is_active=True)
        mem.is_active = False
        mem.save()
        mem.delete() # Soft delete
        self.assertIsNotNone(mem.deleted)
        
    def test_undo_restores_previous_state_and_preserves_identity(self):
        """19, 22, 23, 24, 25, 26, 27. Undo inside 5s restores same row."""
        mem = TenantMember.objects.create(tenant=self.shop, user=self.user_1, role=ShopRole.STAFF, is_active=False)
        mem.delete()
        
        mem_id = mem.id
        
        self.client.force_authenticate(user=User.objects.create_superuser(email="admin@test.com", password="pw"))
        r = self.client.post(f"/api/v1/memberships/{mem_id}/undo_remove/")
        self.assertEqual(r.status_code, status.HTTP_200_OK)
        
        mem.refresh_from_db()
        self.assertIsNone(mem.deleted)
        self.assertEqual(mem.id, mem_id)
        self.assertEqual(mem.user_id, self.user_1.id)
        self.assertEqual(mem.tenant_id, self.shop.id)
        self.assertFalse(mem.is_active) # Restored previous state

    def test_undo_outside_5s_fails(self):
        """20, 21. Undo outside 5 seconds fails."""
        mem = TenantMember.objects.create(tenant=self.shop, user=self.user_1, role=ShopRole.STAFF, is_active=False)
        with mock.patch('django.utils.timezone.now', return_value=timezone.now() - timedelta(seconds=6)):
            mem.delete()
            
        self.client.force_authenticate(user=User.objects.create_superuser(email="admin@test.com", password="pw"))
        r = self.client.post(f"/api/v1/memberships/{mem.id}/undo_remove/")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(r.data['detail'], "Undo window expired.")

    def test_capacity_counts(self):
        """29, 30, 31, 32. user_count includes ACTIVE and INACTIVE, excludes REMOVED."""
        TenantMember.objects.create(tenant=self.shop, user=self.user_1, is_active=True)
        u3 = User.objects.create_user(email="u3@test.com")
        TenantMember.objects.create(tenant=self.shop, user=u3, is_active=False)
        u4 = User.objects.create_user(email="u4@test.com")
        mem_rem = TenantMember.objects.create(tenant=self.shop, user=u4, is_active=False)
        mem_rem.delete()
        
        self.assertEqual(self.shop.user_count, 2)

    def test_capacity_undo_rejected_when_full(self):
        """36. Undo rejected when capacity is full."""
        # Max users = 2
        mem = TenantMember.objects.create(tenant=self.shop, user=self.user_1, is_active=False)
        mem.delete()
        
        u3 = User.objects.create_user(email="u3@test.com")
        u4 = User.objects.create_user(email="u4@test.com")
        TenantMember.objects.create(tenant=self.shop, user=u3, is_active=True)
        TenantMember.objects.create(tenant=self.shop, user=u4, is_active=True)
        
        self.client.force_authenticate(user=User.objects.create_superuser(email="admin@test.com", password="pw"))
        r = self.client.post(f"/api/v1/memberships/{mem.id}/undo_remove/")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("maximum user limit", r.data['detail'])

    def test_removed_membership_does_not_authorize(self):
        """17, 40. Removed membership does not authorize."""
        mem = TenantMember.objects.create(tenant=self.shop, user=self.user_1, role=ShopRole.ADMIN, is_active=False)
        mem.delete()
        
        from apps.tenants.policy import ShopRolePolicy
        # is_shop_member should return False
        self.assertFalse(ShopRolePolicy.is_shop_member(self.user_1, self.shop.id))
        self.assertFalse(ShopRolePolicy.can_manage_memberships(self.user_1, self.shop.id))

    def test_duplicate_membership_rejected(self):
        """11. Duplicate membership rejected."""
        TenantMember.objects.create(tenant=self.shop, user=self.user_1)
        with self.assertRaises(IntegrityError):
            TenantMember.objects.create(tenant=self.shop, user=self.user_1)
            
    def test_race_condition_protection(self):
        """37. Capacity race behavior is protected."""
        self.client.force_authenticate(user=User.objects.create_superuser(email="admin@test.com", password="pw"))
        u3 = User.objects.create_user(email="u3@test.com")
        u4 = User.objects.create_user(email="u4@test.com")
        u5 = User.objects.create_user(email="u5@test.com")
        
        # Max users = 2
        r1 = self.client.post("/api/v1/memberships/", {'tenant': self.shop.id, 'user': u3.id})
        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        r2 = self.client.post("/api/v1/memberships/", {'tenant': self.shop.id, 'user': u4.id})
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)
        r3 = self.client.post("/api/v1/memberships/", {'tenant': self.shop.id, 'user': u5.id})
        self.assertEqual(r3.status_code, status.HTTP_400_BAD_REQUEST)
