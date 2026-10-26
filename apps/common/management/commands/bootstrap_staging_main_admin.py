"""Create one explicitly configured Main Supplier Admin in staging."""

import os

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q

from apps.accounts.identity import normalize_login_id
from apps.accounts.models import User
from apps.accounts.phone_numbers import InvalidUserPhone, normalize_user_phone
from apps.accounts.security import validate_pin


SWITCH = "STAGING_MAIN_ADMIN_BOOTSTRAP_ENABLED"
EMAIL = "STAGING_MAIN_ADMIN_EMAIL"
FIRST_NAME = "STAGING_MAIN_ADMIN_FIRST_NAME"
LOGIN_ID = "STAGING_MAIN_ADMIN_LOGIN_ID"
PHONE = "STAGING_MAIN_ADMIN_PHONE"
PIN = "STAGING_MAIN_ADMIN_PIN"


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
            key: os.environ.get(key, "").strip()
            for key in (EMAIL, FIRST_NAME, LOGIN_ID, PHONE, PIN)
        }
        config[EMAIL] = config[EMAIL].lower()
        if not all(config.values()):
            raise CommandError("Required Main Admin bootstrap values are missing.")
        try:
            validate_email(config[EMAIL])
        except ValidationError:
            raise CommandError("Main Admin email is invalid.") from None
        if len(config[FIRST_NAME]) > 30:
            raise CommandError("Main Admin first name is too long.")
        try:
            config[LOGIN_ID] = normalize_login_id(config[LOGIN_ID])
            validate_pin(config[PIN])
        except (ValueError, ValidationError) as exc:
            raise CommandError("Main Admin Login ID or PIN is invalid.") from None
        try:
            config[PHONE] = normalize_user_phone(config[PHONE])
        except InvalidUserPhone:
            raise CommandError(
                "Main Admin phone must be a valid international number."
            ) from None
        return config

    def handle(self, *args, **options):
        if not options["confirm_staging_main_admin_bootstrap"]:
            raise CommandError(
                "Pass --confirm-staging-main-admin-bootstrap to create the account."
            )
        config = self._configuration()
        try:
            with transaction.atomic():
                # Never promote or reset an existing identity. Treat identity
                # collisions as a safe no-op for startup availability.
                if (
                    User.objects.select_for_update()
                    .filter(
                        Q(email__iexact=config[EMAIL])
                        | Q(phone=config[PHONE])
                        | Q(login_id__iexact=config[LOGIN_ID])
                    )
                    .exists()
                ):
                    self.stdout.write(
                        "A User with a configured identity already exists; "
                        "no account changes were made."
                    )
                    return

                User.objects.create_superuser(
                    email=config[EMAIL],
                    password=config[PIN],
                    first_name=config[FIRST_NAME],
                    login_id=config[LOGIN_ID],
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
                "Staging Main Supplier Admin created; first login requires a PIN change."
            )
        )
