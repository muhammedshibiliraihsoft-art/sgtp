from django.conf import settings
from django.core.management import BaseCommand, CommandError, call_command


class Command(BaseCommand):
    help = "Flush synthetic staging data while preserving the migrated schema."

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm-staging-reset",
            action="store_true",
            help="Required explicit acknowledgement before removing staging data.",
        )

    def handle(self, *args, **options):
        if getattr(settings, "ENVIRONMENT", None) != "staging":
            raise CommandError(
                "This command is available only with DJANGO_ENV=staging."
            )

        database_name = settings.DATABASES["default"]["NAME"]
        if database_name != "sgtp_staging":
            raise CommandError(
                "Refusing reset: database is not the named staging database."
            )

        if not options["confirm_staging_reset"]:
            raise CommandError("Pass --confirm-staging-reset to remove staging data.")

        call_command(
            "flush",
            interactive=False,
            database="default",
            verbosity=options["verbosity"],
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Staging data reset; schema and migrations were retained."
            )
        )
