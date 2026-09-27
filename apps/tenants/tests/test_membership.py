import pytest
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model

from apps.tenants.models import Tenant, Supplier, TenantMember, ShopRole

User = get_user_model()

class TenantMembershipTest(TestCase):
    def setUp(self):
        self.supplier = Supplier.objects.get(singleton_lock=True)
        self.tenant = Tenant.objects.create(
            name="Test Shop", 
            slug="test-shop", 
            supplier=self.supplier
        )
        self.user = User.objects.create_user(
            email="member@test.com", 
            password="testpass"
        )

    def test_create_membership(self):
        """Test creating a valid shop membership"""
        membership = TenantMember.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=ShopRole.STAFF
        )
        self.assertEqual(membership.tenant, self.tenant)
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.role, ShopRole.STAFF)
        self.assertTrue(membership.is_active)

    def test_duplicate_membership_prevented(self):
        """Test that a user cannot have multiple memberships in the same Shop"""
        TenantMember.objects.create(
            tenant=self.tenant,
            user=self.user,
            role=ShopRole.STAFF
        )
        with self.assertRaises(IntegrityError):
            TenantMember.objects.create(
                tenant=self.tenant,
                user=self.user,
                role=ShopRole.ADMIN
            )

    def test_cannot_add_inactive_user(self):
        """Test that inactive users cannot be added to a shop"""
        inactive_user = User.objects.create_user(
            email="inactive@test.com", 
            password="testpass",
            is_active=False
        )
        membership = TenantMember(
            tenant=self.tenant,
            user=inactive_user,
            role=ShopRole.STAFF
        )
        with self.assertRaises(ValidationError) as ctx:
            membership.full_clean()
        self.assertIn("Cannot add an inactive user", str(ctx.exception))

    def test_cannot_add_to_inactive_shop(self):
        """Test that users cannot be added to an inactive shop"""
        inactive_shop = Tenant.objects.create(
            name="Inactive Shop",
            slug="inactive-shop",
            supplier=self.supplier,
            is_active=False
        )
        membership = TenantMember(
            tenant=inactive_shop,
            user=self.user,
            role=ShopRole.STAFF
        )
        with self.assertRaises(ValidationError) as ctx:
            membership.full_clean()
        self.assertIn("Cannot add members to an inactive Shop", str(ctx.exception))

    def test_external_supplier_boundary(self):
        """
        Test the boundary that External Suppliers are not users.
        An external supplier record (when implemented) is a distinct business model.
        The TenantMember requires a User instance, preventing mixing the two concepts.
        """
        class MockExternalSupplier:
            pk = 999
            is_active = True
            
        with self.assertRaises(ValueError):
            # Django ORM will raise ValueError because MockExternalSupplier is not a User instance
            TenantMember(
                tenant=self.tenant,
                user=MockExternalSupplier(),
                role=ShopRole.STAFF
            )

    def test_shop_role_policy_main_supplier_authority(self):
        """Test that a superuser has cross-shop authority without explicit membership"""
        from apps.tenants.policy import ShopRolePolicy
        admin_user = User.objects.create_superuser(
            email="main_admin@test.com", password="testpass"
        )
        self.assertTrue(ShopRolePolicy.is_main_supplier_admin(admin_user))
        self.assertTrue(ShopRolePolicy.is_shop_member(admin_user, self.tenant.id))

    def test_shop_role_policy_regular_member(self):
        """Test that a regular user requires explicit active membership"""
        from apps.tenants.policy import ShopRolePolicy
        self.assertFalse(ShopRolePolicy.is_main_supplier_admin(self.user))
        self.assertFalse(ShopRolePolicy.is_shop_member(self.user, self.tenant.id))
        
        # Add active membership
        TenantMember.objects.create(
            tenant=self.tenant, user=self.user, role=ShopRole.VIEWER
        )
        self.assertTrue(ShopRolePolicy.is_shop_member(self.user, self.tenant.id))
