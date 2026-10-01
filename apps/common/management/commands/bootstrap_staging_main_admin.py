"""Create one explicitly configured Main Supplier Admin in staging."""

import os

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q

from apps.accounts.models import User
from apps.accounts.phone_numbers import InvalidUserPhone, normalize_user_phone


SWITCH = "STAGING_MAIN_ADMIN_BOOTSTRAP_ENABLED"
EMAIL = "STAGING_MAIN_ADMIN_EMAIL"
FIRST_NAME = "STAGING_MAIN_ADMIN_FIRST_NAME"
PHONE = "STAGING_MAIN_ADMIN_PHONE"
PASSWORD = "STAGING_MAIN_ADMIN_PASSWORD"


class Command(BaseCommand):
    help = "Create one guarded Main Supplier Admin in the staging database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm-staging-main-admin-bootstrap",
            action="store_true",
            help="Required acknowledgement before creating a staging admin.",
        )

    @staticmethod
    def _configured_database_name():
        return settings.DATABASES["default"].get("NAME")

    @staticmethod
    def _configuration():
        if getattr(settings, "ENVIRONMENT", None) != "staging":
            raise CommandError("Main Admin bootstrap is available only in staging.")
        if Command._configured_database_name() != "sgtp_staging":
            raise CommandError("Refusing bootstrap: database is not sgtp_staging.")
        if os.environ.get("DJANGO_ENV", "").strip().lower() != "staging":
            raise CommandError("Refusing bootstrap: DJANGO_ENV is not staging.")
        if os.environ.get(SWITCH, "").strip().lower() != "true":
            raise CommandError("Main Admin bootstrap is not explicitly enabled.")

        config = {
            key: os.environ.get(key, "").strip() for key in (EMAIL, FIRST_NAME, PHONE)
        }
        config[EMAIL] = config[EMAIL].lower()
        password = os.environ.get(PASSWORD, "")
        if not all(config.values()) or not password:
            raise CommandError("Required Main Admin bootstrap values are missing.")
        try:
            validate_email(config[EMAIL])
        except ValidationError:
            raise CommandError("Main Admin email is invalid.") from None
        if len(config[FIRST_NAME]) > 30:
            raise CommandError("Main Admin first name is too long.")
        try:
            config[PHONE] = normalize_user_phone(config[PHONE])
        except InvalidUserPhone:
            raise CommandError(
                "Main Admin phone must be a valid international number."
            ) from None
        if len(password) < 40:
            raise CommandError("Bootstrap password must be at least 40 characters.")
        config[PASSWORD] = password
        return config

    def handle(self, *args, **options):
        if not options["confirm_staging_main_admin_bootstrap"]:
            raise CommandError(
                "Pass --confirm-staging-main-admin-bootstrap to create the account."
            )
        config = self._configuration()
        try:
            with transaction.atomic():
                # Never promote or reset an existing identity. Treat either
                # contact collision as a safe no-op for startup availability.
                if (
                    User.objects.select_for_update()
                    .filter(Q(email__iexact=config[EMAIL]) | Q(phone=config[PHONE]))
                    .exists()
                ):
                    self.stdout.write(
                        "A User with the configured email or phone already exists; "
                        "no account changes were made."
                    )
                    return

                candidate = User(
                    email=config[EMAIL],
                    phone=config[PHONE],
                    first_name=config[FIRST_NAME],
                    is_active=True,
                    is_staff=True,
                    is_superuser=True,
                    must_change_password=True,
                )
                try:
                    validate_password(config[PASSWORD], user=candidate)
                except ValidationError:
                    raise CommandError(
                        "Bootstrap password does not meet policy."
                    ) from None

                User.objects.create_superuser(
                    email=config[EMAIL],
                    password=config[PASSWORD],
                    first_name=config[FIRST_NAME],
                    phone=config[PHONE],
                    must_change_password=True,
                )
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(
                "Main Admin bootstrap failed safely "
                f"({type(exc).__name__}); input values were not reported."
            ) from None

        self.stdout.write(
            self.style.SUCCESS(
                "Staging Main Supplier Admin created; first login requires a password change."
            )
        )
