import uuid

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class T304AIdentityMigrationTests(TransactionTestCase):
    migrate_from = [
        ("accounts", "0003_alter_user_options_user_appearance_preference_and_more"),
        ("tenants", "0008_tenant_default_currency_tenant_default_locale_and_more"),
    ]

    def migrate(self, targets):
        executor = MigrationExecutor(connection)
        executor.migrate(targets)
        return executor.loader.project_state(targets).apps

    def setUp(self):
        super().setUp()
        old_apps = self.migrate(self.migrate_from)
        User = old_apps.get_model("accounts", "User")
        Supplier = old_apps.get_model("tenants", "Supplier")
        Tenant = old_apps.get_model("tenants", "Tenant")
        TenantMember = old_apps.get_model("tenants", "TenantMember")

        self.user_id = uuid.uuid4()
        self.password_hash = "preserved-password-hash"
        self.email = "legacy@example.test"
        User.objects.create(
            id=self.user_id,
            password=self.password_hash,
            email=self.email,
            first_name="Legacy",
            last_name="Person",
            phone="+96550000123",
            auth_version=7,
        )
        supplier, _ = Supplier.objects.get_or_create(
            singleton_lock=True, defaults={"name": "Migration Supplier"}
        )
        tenant = Tenant.objects.create(
            supplier=supplier,
            name="Migration Shop",
            slug="migration-shop-t304a",
            max_users=5,
        )
        TenantMember.objects.create(
            tenant=tenant,
            user_id=self.user_id,
            role="STAFF",
            created_by_id=self.user_id,
            updated_by_id=self.user_id,
        )
        self.migrated_apps = self.migrate(
            MigrationExecutor(connection).loader.graph.leaf_nodes()
        )

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())
        super().tearDown()

    def test_backfill_preserves_identity_credentials_and_membership(self):
        User = self.migrated_apps.get_model("accounts", "User")
        TenantMember = self.migrated_apps.get_model("tenants", "TenantMember")
        user = User.objects.get(pk=self.user_id)
        membership = TenantMember.objects.get(user_id=self.user_id)

        self.assertEqual(user.pk, self.user_id)
        self.assertEqual(user.password, self.password_hash)
        self.assertEqual(user.email, self.email)
        self.assertEqual(user.phone, "+96550000123")
        self.assertEqual(user.auth_version, 7)
        self.assertRegex(user.user_code, r"^U-[23456789ABCDEFGHJKMNPQRSTUVWXYZ]{16}$")
        self.assertEqual(membership.user_id, self.user_id)
        self.assertEqual(membership.created_by_id, self.user_id)
        self.assertEqual(membership.updated_by_id, self.user_id)
