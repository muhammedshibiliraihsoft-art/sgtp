import pytest
from django.test import TestCase, TransactionTestCase
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from ..models import Supplier

class SupplierSingletonTest(TestCase):
    def test_create_supplier_fails(self):
        """Test creating a second supplier fails since migration creates first"""
        with self.assertRaises(ValidationError):
            Supplier.objects.create(name="Second Supplier")
            
    def test_can_update_supplier(self):
        """Test that updating an existing supplier works"""
        supplier = Supplier.objects.get(singleton_lock=True)
        supplier.name = "Updated Supplier"
        supplier.save()
        
        supplier.refresh_from_db()
        self.assertEqual(supplier.name, "Updated Supplier")
        
    def test_bulk_create_fails(self):
        """Test bulk_create cannot bypass singleton constraint"""
        # Delete the existing one safely through DB to test bulk create properly, 
        # or just try to bulk create a second one.
        with self.assertRaises(IntegrityError):
            Supplier.objects.bulk_create([
                Supplier(name="Bulk 1"),
                Supplier(name="Bulk 2")
            ])
            
    def test_soft_delete_blocked(self):
        """Test that attempting to delete the Main Supplier raises ValidationError"""
        supplier = Supplier.objects.get(singleton_lock=True)
        with self.assertRaises(ValidationError) as ctx:
            supplier.delete()
        self.assertIn("cannot be deleted", str(ctx.exception))
        
    def test_restore_blocked(self):
        """Test that restore is practically not applicable since delete is blocked"""
        supplier = Supplier.objects.get(singleton_lock=True)
        # Verify it is active and not deleted
        self.assertIsNone(supplier.deleted)
        self.assertTrue(supplier.is_active)
        
    def test_invalid_singleton_lock(self):
        """Test that you cannot save a supplier with singleton_lock=False"""
        supplier = Supplier.objects.get(singleton_lock=True)
        # Even if we bypass clean, the DB check constraint will block it if we try to insert a new one
        # But we can't easily change editable=False field. Let's test clean method
        supplier.singleton_lock = False
        with self.assertRaises(IntegrityError):
            # bypassing clean by using update
            Supplier.objects.filter(pk=supplier.pk).update(singleton_lock=False)

import threading

class SupplierConcurrencyTest(TransactionTestCase):
    def test_concurrent_creation(self):
        """Test that concurrent creation attempts safely hit IntegrityError"""
        # Migration already created one, let's delete it natively to test creation race
        Supplier.objects.all()._raw_delete(Supplier.objects.all().db)
        
        exceptions = []
        def create_supplier():
            from django.db import connection
            try:
                Supplier.objects.create(name="Concurrent Supplier")
            except Exception as e:
                exceptions.append(e)
            finally:
                connection.close()

        threads = [threading.Thread(target=create_supplier) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # One should succeed, 4 should fail with IntegrityError or ValidationError
        self.assertEqual(Supplier.objects.count(), 1)
        self.assertEqual(len(exceptions), 4)
        
        # Verify that all exceptions are validation/integrity errors, not generic 500s
        for e in exceptions:
            self.assertTrue(isinstance(e, (ValidationError, IntegrityError)))
