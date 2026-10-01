"""Rotate passwords for the already-existing deterministic staging fixture."""

import os

from django.conf import settings
from django.core.management import BaseCommand, CommandError
from django.db import transaction

from apps.accounts.models import User
from apps.accounts.security import set_password_and_revoke_sessions
from apps.tenants.models import (
    MembershipWorkFunction,
    ShopRole,
    Supplier,
    Tenant,
    TenantMember,
)
from apps.tenants.services.membership import get_effective_admins

from .bootstrap_staging_smoke import MAIN_EMAIL, PASSWORD_VARIABLES, SHOP_FIXTURES


ROTATION_SWITCH = "STAGING_SMOKE_ROTATE_CREDENTIALS_ENABLED"


class Command(BaseCommand):
    help = "Rotate credentials for the existing synthetic SGTP staging fixture."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm-staging-credential-rotation",
            action="store_true",
            help="Required explicit acknowledgement before rotating staging credentials.",
        )

    @staticmethod
    def _configured_database_name():
        return settings.DATABASES["default"].get("NAME")

    @staticmethod
    def _configuration():
        if getattr(settings, "ENVIRONMENT", None) != "staging":
            raise CommandError("Credential rotation is available only in staging.")
        if Command._configured_database_name() != "sgtp_staging":
            raise CommandError(
                "Refusing credential rotation: database name is not sgtp_staging."
            )
        if os.environ.get(ROTATION_SWITCH, "").strip().lower() != "true":
            raise CommandError("Staging smoke credential rotation is not enabled.")

        missing = [
            variable
            for variable in PASSWORD_VARIABLES.values()
            if not os.environ.get(variable)
        ]
        if missing:
            raise CommandError(
                "Required staging smoke credential secrets are missing: "
                + ", ".join(missing)
            )
        weak = [
            variable
            for variable in PASSWORD_VARIABLES.values()
            if len(os.environ[variable]) < 40
        ]
        if weak:
            raise CommandError(
                "Staging smoke credential secrets must be at least 40 characters: "
                + ", ".join(weak)
            )
        return {
            role: os.environ[variable] for role, variable in PASSWORD_VARIABLES.items()
        }

    @staticmethod
    def _existing_fixture(supplier):
        expected_slugs = {fixture["slug"] for fixture in SHOP_FIXTURES}
        expected_emails = {MAIN_EMAIL, *(fixture["email"] for fixture in SHOP_FIXTURES)}

        shops = list(
            Tenant.objects.all_with_deleted()
            .select_for_update()
            .filter(slug__startswith="sgtp-smoke-")
            .order_by("slug", "pk")
        )
        users = list(
            User.objects.select_for_update()
            .filter(email__startswith="sgtp-smoke-")
            .order_by("email", "pk")
        )
        if not shops and not users:
            raise CommandError("The existing synthetic staging fixture is missing.")
        if {shop.slug for shop in shops} != expected_slugs:
            raise CommandError(
                "The existing synthetic Shop fixture is missing, partial, or has unexpected duplicates."
            )
        if {user.email for user in users} != expected_emails:
            raise CommandError(
                "The existing synthetic User fixture is missing, partial, or has unexpected identities."
            )

        shop_by_slug = {shop.slug: shop for shop in shops}
        user_by_email = {user.email: user for user in users}
        main_user = user_by_email[MAIN_EMAIL]
        if (
            not main_user.is_active
            or not main_user.is_staff
            or not main_user.is_superuser
            or main_user.owning_shop_id is not None
            or main_user.first_name != "Synthetic Main Supplier Admin"
            or main_user.phone != "+12025550100"
            or main_user.must_change_password
        ):
            raise CommandError(
                "The existing synthetic Main Supplier identity is inconsistent."
            )

        fixture_users = {"main": main_user}
        for fixture in SHOP_FIXTURES:
            shop = shop_by_slug[fixture["slug"]]
            user = user_by_email[fixture["email"]]
            memberships = list(
                TenantMember.objects.all_with_deleted()
                .select_for_update()
                .filter(tenant=shop)
                .order_by("user_id", "pk")
            )
            if (
                shop.deleted is not None
                or not shop.is_active
                or shop.name != fixture["name"]
                or shop.supplier_id != supplier.pk
                or shop.max_users != 5
                or shop.contact_email != fixture["email"]
                or shop.contact_phone != fixture["phone"]
                or shop.user_count != 1
                or not user.is_active
                or user.is_staff
                or user.is_superuser
                or user.owning_shop_id != shop.pk
                or user.email != fixture["email"]
                or user.first_name != fixture["first_name"]
                or user.phone != fixture["phone"]
                or user.must_change_password
                or len(memberships) != 1
            ):
                raise CommandError(
                    f"The existing synthetic {fixture['key']} Shop/User fixture is inconsistent."
                )

            membership = memberships[0]
            if (
                membership.user_id != user.pk
                or membership.role != ShopRole.ADMIN
                or not membership.is_active
                or membership.deleted is not None
                or not 1 <= get_effective_admins(shop.pk).count() <= 2
            ):
                raise CommandError(
                    f"The existing synthetic {fixture['key']} ADMIN membership is inconsistent."
                )

            functions = list(
                MembershipWorkFunction.objects.all_with_deleted()
                .select_for_update()
                .filter(membership=membership)
                .order_by("function_code", "pk")
            )
            if (
                len(functions) != 1
                or functions[0].deleted is not None
                or functions[0].function_code != fixture["function_code"]
            ):
                raise CommandError(
                    f"The existing synthetic {fixture['key']} Work Function is inconsistent."
                )
            fixture_users[fixture["key"].lower()] = user

        return fixture_users

    def handle(self, *args, **options):
        if not options["confirm_staging_credential_rotation"]:
            raise CommandError(
                "Pass --confirm-staging-credential-rotation to rotate staging credentials."
            )
        passwords = self._configuration()

        try:
            with transaction.atomic():
                suppliers = list(Supplier.objects.select_for_update().order_by("pk"))
                if len(suppliers) != 1 or not suppliers[0].is_active:
                    raise CommandError(
                        "The active single Main Supplier fixture is unavailable or inconsistent."
                    )
                roles = ("main", "shop_a", "shop_b")
                users_by_role = self._existing_fixture(suppliers[0])
                users = [users_by_role[role] for role in roles]
                already_current = [
                    user.check_password(passwords[role])
                    for user, role in zip(users, roles, strict=True)
                ]
                if all(already_current):
                    self.stdout.write(
                        "Synthetic staging credentials are already current; no changes made."
                    )
                    return
                if any(already_current):
                    raise CommandError(
                        "Only part of the synthetic staging credential set is current; no changes made."
                    )

                for user, role in zip(users, roles, strict=True):
                    set_password_and_revoke_sessions(
                        user, passwords[role], must_change=False
                    )
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(
                "Staging smoke credential rotation failed safely "
                f"({type(exc).__name__}); credential values were not reported."
            ) from None

        self.stdout.write(
            self.style.SUCCESS(
                "Credentials rotated for the existing synthetic staging identities; "
                "fixture data was unchanged."
            )
        )
