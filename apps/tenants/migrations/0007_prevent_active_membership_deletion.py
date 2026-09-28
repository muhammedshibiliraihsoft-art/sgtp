from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('tenants', '0006_alter_tenant_max_users'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE OR REPLACE FUNCTION prevent_active_membership_deletion()
            RETURNS TRIGGER AS $$
            BEGIN
                -- If we are setting deleted to non-null and it was previously null
                IF NEW.deleted IS NOT NULL AND OLD.deleted IS NULL THEN
                    -- Check the PREVIOUS state of is_active
                    IF OLD.is_active = TRUE THEN
                        RAISE EXCEPTION 'Cannot remove an active membership. Deactivate it first.';
                    END IF;
                END IF;
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER prevent_active_membership_deletion_trigger
            BEFORE UPDATE ON tenants_tenantmember
            FOR EACH ROW EXECUTE FUNCTION prevent_active_membership_deletion();
            """,
            reverse_sql="""
            DROP TRIGGER IF EXISTS prevent_active_membership_deletion_trigger ON tenants_tenantmember;
            DROP FUNCTION IF EXISTS prevent_active_membership_deletion();
            """
        )
    ]
