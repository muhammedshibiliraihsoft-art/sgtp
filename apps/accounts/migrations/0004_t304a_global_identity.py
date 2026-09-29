import secrets
import re

from django.db import IntegrityError, migrations, models, transaction
from django.db.models.functions import Lower, Trim
from django.db.models.lookups import Exact


ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
CODE_CONSTRAINT = "accounts_user_user_code_key"


def preflight_and_backfill(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    TenantMember = apps.get_model("tenants", "TenantMember")
    db = schema_editor.connection.alias

    # Querying values avoids relying on database-specific whitespace trimming.
    missing_names = sum(
        not (value or "").strip()
        for value in User.objects.using(db)
        .values_list("first_name", flat=True)
        .iterator()
    )
    if missing_names:
        raise RuntimeError(
            f"T3-04A migration stopped: {missing_names} existing User row(s) have no usable first_name. "
            "Collect the real name through an approved remediation process; do not fabricate names."
        )

    canonical_emails = {}
    for pk, value in User.objects.using(db).values_list("pk", "email").iterator():
        canonical = (value or "").strip().lower()
        if canonical:
            canonical_emails.setdefault(canonical, []).append(pk)
    collisions = sum(len(ids) > 1 for ids in canonical_emails.values())
    if collisions:
        raise RuntimeError(
            f"T3-04A migration stopped: {collisions} case-insensitive email duplicate group(s) exist. "
            "Manually reconcile account ownership; accounts will not be merged."
        )

    invalid_phone_rows = sum(
        bool(value and not re.fullmatch(r"\+[1-9][0-9]{7,14}", value.strip()))
        for value in User.objects.using(db).values_list("phone", flat=True).iterator()
    )
    if invalid_phone_rows:
        raise RuntimeError(
            f"T3-04A migration stopped: {invalid_phone_rows} existing phone value(s) are not canonical E.164. "
            "Manually verify and normalize each contact; do not infer a region or fabricate a number."
        )

    missing_superuser_contacts = (
        User.objects.using(db)
        .filter(is_superuser=True)
        .filter(
            models.Q(email__isnull=True)
            | models.Q(email="")
            | models.Q(phone__isnull=True)
            | models.Q(phone="")
        )
        .count()
    )
    if missing_superuser_contacts:
        raise RuntimeError(
            f"T3-04A migration stopped: {missing_superuser_contacts} Main Supplier account(s) "
            "lack required email/phone. Collect verified contact data; do not fabricate it or disable accounts."
        )

    missing_shop_admin_contacts = (
        TenantMember.objects.using(db)
        .filter(role="ADMIN", is_active=True, deleted__isnull=True)
        .filter(
            models.Q(user__email__isnull=True)
            | models.Q(user__email="")
            | models.Q(user__phone__isnull=True)
            | models.Q(user__phone="")
        )
        .values("user_id")
        .distinct()
        .count()
    )
    if missing_shop_admin_contacts:
        raise RuntimeError(
            f"T3-04A migration stopped: {missing_shop_admin_contacts} active Shop Admin account(s) "
            "lack required email/phone. Collect verified contact data; do not fabricate it."
        )


def backfill_identity(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    db = schema_editor.connection.alias
    for user in User.objects.using(db).all().iterator():
        canonical_email = (user.email or "").strip().lower() or None
        canonical_phone = (user.phone or "").strip() or None
        if canonical_email != user.email or canonical_phone != user.phone:
            User.objects.using(db).filter(pk=user.pk).update(
                email=canonical_email, phone=canonical_phone
            )
        if user.user_code:
            continue
        for _ in range(8):
            code = "U-" + "".join(secrets.choice(ALPHABET) for _ in range(16))
            try:
                with transaction.atomic(using=db):
                    updated = (
                        User.objects.using(db)
                        .filter(pk=user.pk, user_code__isnull=True)
                        .update(user_code=code)
                    )
                if updated:
                    break
                break
            except IntegrityError as exc:
                cause = getattr(exc, "__cause__", None)
                constraint = getattr(
                    getattr(cause, "diag", None), "constraint_name", None
                )
                if constraint != CODE_CONSTRAINT:
                    raise
        else:
            raise RuntimeError(
                "T3-04A migration stopped: could not allocate a unique User ID after bounded retries."
            )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_alter_user_options_user_appearance_preference_and_more"),
        ("tenants", "0008_tenant_default_currency_tenant_default_locale_and_more"),
    ]

    operations = [
        migrations.RunPython(preflight_and_backfill, migrations.RunPython.noop),
        migrations.AddField(
            model_name="user",
            name="user_code",
            field=models.CharField(
                max_length=18, null=True, unique=True, editable=False
            ),
        ),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True),
        ),
        migrations.RunPython(backfill_identity, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="user_code",
            field=models.CharField(max_length=18, unique=True, editable=False),
        ),
        migrations.AlterField(
            model_name="user",
            name="first_name",
            field=models.CharField(max_length=30),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.UniqueConstraint(
                Lower(Trim("email")),
                condition=models.Q(email__isnull=False) & ~models.Q(email=""),
                name="unique_user_email_casefold",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                condition=models.Q(
                    user_code__regex=r"^U-[23456789ABCDEFGHJKMNPQRSTUVWXYZ]{16}$"
                ),
                name="user_code_format_valid",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                condition=~Exact(Trim("first_name"), models.Value("")),
                name="user_first_name_required",
            ),
        ),
        migrations.AddConstraint(
            model_name="user",
            constraint=models.CheckConstraint(
                condition=(
                    ~models.Q(is_superuser=True)
                    | (
                        models.Q(email__isnull=False)
                        & ~Exact(Trim("email"), models.Value(""))
                        & models.Q(phone__isnull=False)
                        & ~Exact(Trim("phone"), models.Value(""))
                    )
                ),
                name="superuser_requires_contact",
            ),
        ),
    ]
