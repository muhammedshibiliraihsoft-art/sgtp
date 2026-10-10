from django.contrib.auth import get_user_model
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from apps.accounts.tests.factories import create_test_user
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember


class AccountLoginEligibilityMigrationTests(TransactionTestCase):
    def test_0007_reverses_with_deferred_shop_ownership_trigger(self):
        if connection.vendor != "postgresql":
            self.skipTest("This migration regression is specific to PostgreSQL.")

        supplier = Supplier.objects.get(singleton_lock=True)
        shop = Tenant.objects.create(
            supplier=supplier,
            name="Eligibility Migration Shop",
            slug="eligibility-migration-shop",
            max_users=5,
        )
        viewer = create_test_user(
            owning_shop=shop,
            email="eligibility-migration-viewer@example.test",
            password="migration-test-only-password",
            first_name="Migration",
            last_name="Viewer",
            phone="+96550000771",
            login_id="migration_viewer",
        )
        membership = TenantMember.objects.create(
            tenant=shop,
            user=viewer,
            role=ShopRole.VIEWER,
        )
        get_user_model().objects.filter(pk=viewer.pk).update(login_enabled=False)
        original_password_hash = viewer.password

        executor = MigrationExecutor(connection)
        latest_targets = executor.loader.graph.leaf_nodes()
        reverse_targets = [
            node for node in latest_targets if node[0] != "accounts"
        ] + [("accounts", "0006_authattemptbucket_shopadminpinresetrequest_and_more")]

        try:
            executor.migrate(reverse_targets)

            historical_apps = MigrationExecutor(connection).loader.project_state(
                reverse_targets
            ).apps
            HistoricalUser = historical_apps.get_model("accounts", "User")
            HistoricalMember = historical_apps.get_model("tenants", "TenantMember")
            migrated_viewer = HistoricalUser.objects.get(pk=viewer.pk)

            self.assertEqual(migrated_viewer.password, original_password_hash)
            self.assertTrue(HistoricalMember.objects.filter(pk=membership.pk).exists())
            with connection.cursor() as cursor:
                columns = {
                    column.name
                    for column in connection.introspection.get_table_description(
                        cursor, "accounts_user"
                    )
                }
            self.assertNotIn("login_enabled", columns)
        finally:
            MigrationExecutor(connection).migrate(latest_targets)

        viewer.refresh_from_db()
        self.assertFalse(viewer.login_enabled)
