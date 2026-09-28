import pytest
from django.test import TransactionTestCase
from django.db.migrations.executor import MigrationExecutor
from django.db import connection

class TestTenantMigration(TransactionTestCase):
    # Tests the 0001 -> 0002 migration
    app = 'tenants'
    migrate_from = [('tenants', '0001_initial')]
    migrate_to = [('tenants', '0002_supplier_and_tenant_supplier')]

    def setUp(self):
        super().setUp()
        old_state = self.migrate(self.migrate_from)
        Tenant = old_state.apps.get_model('tenants', 'Tenant')
        
        # Create an existing tenant with no supplier (as it was in 0001)
        # We need a user to satisfy created_by, but wait, created_by can be null
        self.tenant = Tenant.objects.create(max_users=10, name="Legacy Tenant", slug="legacy")
        
        # Apply the migration
        self.migrate(self.migrate_to)

    def migrate(self, target):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()  # reload.
        executor.migrate(target)
        return executor.loader.project_state(target)

    def test_migration_assigns_supplier(self):
        """Test that the migration assigns the Main Supplier to existing Tenants"""
        from apps.tenants.models import Tenant, Supplier
        
        # Verify exactly one supplier exists
        self.assertEqual(Supplier.objects.count(), 1)
        supplier = Supplier.objects.get()
        
        # Verify the legacy tenant survived and was assigned to the supplier
        tenant = Tenant.objects.get(slug="legacy")
        self.assertEqual(tenant.name, "Legacy Tenant")
        self.assertEqual(tenant.supplier, supplier)
