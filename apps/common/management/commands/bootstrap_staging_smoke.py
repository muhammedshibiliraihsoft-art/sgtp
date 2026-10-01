"""Create the deterministic synthetic fixture used by T3-05A staging checks."""

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
    WorkFunctionCode,
)
from apps.tenants.services.membership import (
    create_shop_with_first_admin,
    get_effective_admins,
)
from apps.tenants.services.work_functions import set_membership_work_functions


MAIN_EMAIL = "sgtp-smoke-main@staging.invalid"
SHOP_FIXTURES = (
    {
        "key": "SHOP_A",
        "email": "sgtp-smoke-shop-a-admin@staging.invalid",
        "phone": "+12025550101",
        "first_name": "Synthetic Shop A Admin",
        "slug": "sgtp-smoke-shop-a",
        "name": "SGTP Synthetic Smoke Shop A",
        "function_code": WorkFunctionCode.CUTTING,
    },
    {
        "key": "SHOP_B",
        "email": "sgtp-smoke-shop-b-admin@staging.invalid",
        "phone": "+12025550102",
        "first_name": "Synthetic Shop B Admin",
        "slug": "sgtp-smoke-shop-b",
        "name": "SGTP Synthetic Smoke Shop B",
        "function_code": WorkFunctionCode.STITCHING,
    },
)
PASSWORD_VARIABLES = {
    "main": "STAGING_SMOKE_MAIN_PASSWORD",
    "shop_a": "STAGING_SMOKE_SHOP_A_ADMIN_PASSWORD",
    "shop_b": "STAGING_SMOKE_SHOP_B_ADMIN_PASSWORD",
}


class Command(BaseCommand):
    help = "Create the guarded synthetic SGTP staging smoke-test fixture."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm-staging-bootstrap",
            action="store_true",
            help="Required explicit acknowledgement before creating staging data.",
        )

    @staticmethod
    def _configuration():
        if getattr(settings, "ENVIRONMENT", None) != "staging":
            raise CommandError(
                "Bootstrap is available only in the staging environment."
            )
        if Command._configured_database_name() != "sgtp_staging":
            raise CommandError("Refusing bootstrap: database name is not sgtp_staging.")
        if (
            os.environ.get("STAGING_SMOKE_BOOTSTRAP_ENABLED", "").strip().lower()
            != "true"
        ):
            raise CommandError("Staging smoke bootstrap is not explicitly enabled.")

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
    def _configured_database_name():
        return settings.DATABASES["default"].get("NAME")

    @staticmethod
    def _existing_fixture(passwords, supplier):
        emails = [MAIN_EMAIL, *(fixture["email"] for fixture in SHOP_FIXTURES)]
        shops = {
            shop.slug: shop
            for shop in Tenant.objects.all_with_deleted()
            .select_for_update()
            .filter(slug__in=[fixture["slug"] for fixture in SHOP_FIXTURES])
        }
        users = {
            user.email: user
            for user in User.objects.select_for_update().filter(email__in=emails)
        }
        if not shops and not users:
            return None

        if len(shops) != len(SHOP_FIXTURES) or len(users) != len(emails):
            raise CommandError(
                "A partial synthetic fixture already exists; inspect/reset staging deliberately."
            )

        main_user = users[MAIN_EMAIL]
        if (
            not main_user.is_active
            or not main_user.is_superuser
            or main_user.owning_shop_id is not None
            or main_user.first_name != "Synthetic Main Supplier Admin"
            or main_user.phone != "+12025550100"
            or not main_user.check_password(passwords["main"])
        ):
            raise CommandError(
                "The existing synthetic Main Supplier identity is inconsistent."
            )

        for fixture in SHOP_FIXTURES:
            shop = shops[fixture["slug"]]
            user = users[fixture["email"]]
            membership = (
                TenantMember.objects.all_with_deleted()
                .select_for_update()
                .filter(user=user, tenant=shop, deleted__isnull=True)
                .first()
            )
            if (
                shop.deleted is not None
                or not shop.is_active
                or shop.name != fixture["name"]
                or shop.supplier_id != supplier.pk
                or shop.max_users < shop.user_count
                or shop.contact_email != fixture["email"]
                or shop.contact_phone != fixture["phone"]
                or not user.is_active
                or user.is_superuser
                or user.owning_shop_id != shop.pk
                or user.first_name != fixture["first_name"]
                or user.phone != fixture["phone"]
                or user.must_change_password
                or not user.check_password(passwords[fixture["key"].lower()])
                or membership is None
                or membership.role != ShopRole.ADMIN
                or not membership.is_active
                or membership.deleted is not None
                or not 1 <= get_effective_admins(shop.pk).count() <= 2
                or not MembershipWorkFunction.objects.filter(
                    membership=membership,
                    function_code=fixture["function_code"],
                    deleted__isnull=True,
                ).exists()
            ):
                raise CommandError(
                    "The existing synthetic Shop fixture is inconsistent."
                )
        return shops

    def handle(self, *args, **options):
        if not options["confirm_staging_bootstrap"]:
            raise CommandError(
                "Pass --confirm-staging-bootstrap to create the staging fixture."
            )
        passwords = self._configuration()

        try:
            with transaction.atomic():
                supplier = Supplier.objects.select_for_update().get(singleton_lock=True)
                if not supplier.is_active:
                    raise CommandError("The Main Supplier entity is inactive.")

                existing = self._existing_fixture(passwords, supplier)
                if existing is not None:
                    self.stdout.write(
                        "Synthetic Main Supplier, Shop A, Shop B, memberships, "
                        "and Work Functions already exist and are valid; no changes made."
                    )
                    return

                main_user = User.objects.create_superuser(
                    email=MAIN_EMAIL,
                    password=passwords["main"],
                    first_name="Synthetic Main Supplier Admin",
                    phone="+12025550100",
                )

                shops = {}
                for fixture in SHOP_FIXTURES:
                    shop, admin, _temporary_password = create_shop_with_first_admin(
                        actor=main_user,
                        shop_data={
                            "name": fixture["name"],
                            "slug": fixture["slug"],
                            "max_users": 5,
                            "contact_email": fixture["email"],
                            "contact_phone": fixture["phone"],
                        },
                        first_admin_data={
                            "email": fixture["email"],
                            "phone": fixture["phone"],
                            "first_name": fixture["first_name"],
                        },
                    )
                    set_password_and_revoke_sessions(
                        admin,
                        passwords[fixture["key"].lower()],
                        must_change=False,
                    )
                    membership = TenantMember.objects.get(
                        tenant=shop, user=admin, role=ShopRole.ADMIN
                    )
                    set_membership_work_functions(
                        actor=admin,
                        shop_id=shop.pk,
                        membership_id=membership.pk,
                        function_codes=[fixture["function_code"]],
                    )
                    shops[fixture["key"]] = shop
        except CommandError:
            raise
        except Exception as exc:
            # Avoid propagating exception text that could accidentally contain inputs.
            raise CommandError(
                "Staging smoke bootstrap failed safely "
                f"({type(exc).__name__}); credential values were not reported."
            ) from None

        self.stdout.write(
            self.style.SUCCESS(
                "Synthetic Main Supplier created; Shop A and Shop B created; "
                "ADMIN memberships and isolated Work Functions are valid; "
                "staging smoke bootstrap complete."
            )
        )
