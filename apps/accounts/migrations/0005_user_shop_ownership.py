from django.db import migrations, models
import django.db.models.deletion


def preflight_and_backfill_shop_ownership(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    db = schema_editor.connection.alias

    # Include soft-removed history: ownership must survive the membership lifecycle.
    shops_by_user = {}
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("SELECT user_id, tenant_id FROM tenants_tenantmember")
        historical_memberships = cursor.fetchall()
    for user_id, shop_id in historical_memberships:
        shops_by_user.setdefault(user_id, set()).add(shop_id)

    multi_shop = []
    unowned = []
    assignments = []
    for user_id, is_superuser in (
        User.objects.using(db).values_list("pk", "is_superuser").iterator()
    ):
        if is_superuser:
            continue
        shop_ids = shops_by_user.get(user_id, set())
        if len(shop_ids) > 1:
            multi_shop.append(str(user_id))
        elif not shop_ids:
            unowned.append(str(user_id))
        else:
            assignments.append((user_id, next(iter(shop_ids))))

    if multi_shop or unowned:
        details = []
        if multi_shop:
            details.append(
                "ordinary Users associated with multiple Shops: "
                + ", ".join(multi_shop)
            )
        if unowned:
            details.append(
                "ordinary Users with no determinable Shop: " + ", ".join(unowned)
            )
        raise RuntimeError(
            "T3-04B User Shop ownership migration stopped; resolve actual ownership "
            "without merging accounts or fabricating Shop assignments. "
            + "; ".join(details)
        )

    for user_id, shop_id in assignments:
        User.objects.using(db).filter(pk=user_id).update(owning_shop_id=shop_id)


OWNERSHIP_SQL = r"""
CREATE OR REPLACE FUNCTION sgtp_check_user_shop_ownership() RETURNS trigger AS $$
DECLARE current_owner uuid;
DECLARE current_superuser boolean;
BEGIN
    SELECT owning_shop_id, is_superuser
      INTO current_owner, current_superuser
      FROM accounts_user WHERE id = NEW.id;
    IF NOT FOUND THEN RETURN NULL; END IF;
    IF current_superuser AND current_owner IS NOT NULL THEN
        RAISE EXCEPTION 'Main Supplier account cannot have ordinary Shop ownership';
    ELSIF NOT current_superuser AND current_owner IS NULL THEN
        RAISE EXCEPTION 'Ordinary User must have an owning Shop';
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER sgtp_user_shop_ownership_required
AFTER INSERT OR UPDATE ON accounts_user
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION sgtp_check_user_shop_ownership();

CREATE OR REPLACE FUNCTION sgtp_user_shop_ownership_immutable() RETURNS trigger AS $$
BEGIN
    IF OLD.owning_shop_id IS NOT NULL
       AND OLD.owning_shop_id IS DISTINCT FROM NEW.owning_shop_id THEN
        RAISE EXCEPTION 'User Shop ownership is immutable';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sgtp_user_shop_ownership_immutable
BEFORE UPDATE OF owning_shop_id ON accounts_user
FOR EACH ROW EXECUTE FUNCTION sgtp_user_shop_ownership_immutable();

CREATE OR REPLACE FUNCTION sgtp_check_membership_user_shop() RETURNS trigger AS $$
DECLARE owner_id uuid;
DECLARE supplier_account boolean;
BEGIN
    SELECT owning_shop_id, is_superuser
      INTO owner_id, supplier_account
      FROM accounts_user WHERE id = NEW.user_id;
    IF NOT FOUND THEN RETURN NULL; END IF;
    IF NOT supplier_account AND owner_id IS DISTINCT FROM NEW.tenant_id THEN
        RAISE EXCEPTION 'Membership Shop must match immutable User Shop ownership';
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE CONSTRAINT TRIGGER sgtp_membership_user_shop_match
AFTER INSERT OR UPDATE ON tenants_tenantmember
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION sgtp_check_membership_user_shop();
"""


REVERSE_OWNERSHIP_SQL = r"""
DROP TRIGGER IF EXISTS sgtp_membership_user_shop_match ON tenants_tenantmember;
DROP FUNCTION IF EXISTS sgtp_check_membership_user_shop();
DROP TRIGGER IF EXISTS sgtp_user_shop_ownership_immutable ON accounts_user;
DROP FUNCTION IF EXISTS sgtp_user_shop_ownership_immutable();
DROP TRIGGER IF EXISTS sgtp_user_shop_ownership_required ON accounts_user;
DROP FUNCTION IF EXISTS sgtp_check_user_shop_ownership();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_t304a_global_identity"),
        ("tenants", "0008_tenant_default_currency_tenant_default_locale_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="owning_shop",
            field=models.ForeignKey(
                blank=True,
                editable=False,
                help_text="Immutable owning Shop for ordinary accounts; null for Main Supplier accounts.",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="owned_users",
                to="tenants.tenant",
            ),
        ),
        migrations.RunPython(
            preflight_and_backfill_shop_ownership, migrations.RunPython.noop
        ),
        migrations.RunSQL(OWNERSHIP_SQL, REVERSE_OWNERSHIP_SQL),
    ]
