"""Synthetic-data stages used by verify_phase5_backup_restore.ps1."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from decimal import Decimal
from pathlib import Path
import re
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django  # noqa: E402

django.setup()

import psycopg  # noqa: E402
from django.conf import settings  # noqa: E402
from django.core.files.base import ContentFile  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.db import connections  # noqa: E402
from django.test.utils import override_settings  # noqa: E402
from django.utils import timezone  # noqa: E402

from apps.accounts.models import User  # noqa: E402
from apps.billing.models import (  # noqa: E402
    CreditNote,
    FinancialDocument,
    Invoice,
    InvoiceLineItem,
    InvoicePayment,
    InvoiceRefund,
    ShopFinancialSequence,
)
from apps.billing.pdf import (  # noqa: E402
    FINANCIAL_PDF_LAYOUT_VERSION,
    invoice_pdf,
)
from apps.catalog.measurement_models import MeasurementProfile, MeasurementSet  # noqa: E402
from apps.catalog.models import Design, DesignVersion, GarmentFamily  # noqa: E402
from apps.catalog.storage import PrivateReferenceStorage  # noqa: E402
from apps.clients.models import Client  # noqa: E402
from apps.tenants.models import ShopRole, Supplier, Tenant, TenantMember  # noqa: E402
from apps.works.models import WorkOrder  # noqa: E402


DATABASE_NAME_PATTERN = re.compile(r"^sgtp_p5_restore_(source|target)_[0-9a-f]{12}$")


def _expected_database(stage: str, suffix: str) -> str:
    kind = "source" if stage == "seed" else "target"
    return f"sgtp_p5_restore_{kind}_{suffix}"


def _validate_temp_media_path(media_root: Path, stage: str, suffix: str) -> None:
    expected_leaf = "source-private-media" if stage == "seed" else "restored-private-media"
    resolved = media_root.resolve()
    expected_run_root = (
        ROOT / ".test-private-assets" / f"sgtp-phase5-restore-{suffix}"
    ).resolve()
    if (
        not resolved.is_absolute()
        or resolved.name != expected_leaf
        or resolved.parent != expected_run_root
    ):
        raise SystemExit("Refusing a media path outside this run's exact temporary directory.")


def _preflight(suffix: str) -> None:
    database = settings.DATABASES["default"]
    if database["ENGINE"] != "django.db.backends.postgresql":
        raise SystemExit("This verification requires PostgreSQL.")
    if database["HOST"] not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Refusing a non-local database host.")

    names = [
        f"sgtp_p5_restore_source_{suffix}",
        f"sgtp_p5_restore_target_{suffix}",
    ]
    if not all(DATABASE_NAME_PATTERN.fullmatch(name) for name in names):
        raise SystemExit("Generated database names did not match the disposable-only guard.")
    if database["NAME"] in names:
        raise SystemExit("Refusing to use the configured application database as a disposable target.")

    with psycopg.connect(
        dbname="postgres",
        user=database["USER"],
        password=database["PASSWORD"],
        host=database["HOST"],
        port=database["PORT"],
        autocommit=True,
    ) as admin:
        role = admin.execute(
            "SELECT rolcreatedb FROM pg_roles WHERE rolname = current_user"
        ).fetchone()
        if not role or not role[0]:
            raise SystemExit("Configured local role cannot create disposable databases.")
        server_started_at_us = admin.execute(
            "SELECT (extract(epoch FROM pg_postmaster_start_time()) * 1000000)::bigint"
        ).fetchone()[0]
        existing = admin.execute(
            "SELECT datname FROM pg_database WHERE datname = ANY(%s)", (names,)
        ).fetchall()
        if existing:
            raise SystemExit("One or more exact disposable database names already exist; stopping.")

    print(
        json.dumps(
            {
                "configured_application_database_not_used": database["NAME"],
                "host": database["HOST"],
                "port": database["PORT"],
                "user": database["USER"],
                "server_started_at_us": str(server_started_at_us),
                "disposable_databases": names,
                "preexisting": False,
            }
        )
    )


def _seed_synthetic_financial_data(suffix: str, media_root: Path) -> None:
    source_name = _expected_database("seed", suffix)
    if settings.DATABASES["default"]["NAME"] != source_name:
        raise SystemExit("Seed stage refuses to run unless DB_NAME is the exact disposable source name.")
    _validate_temp_media_path(media_root, "seed", suffix)

    call_command("migrate", interactive=False, verbosity=0)
    supplier = Supplier.objects.get(singleton_lock=True)
    shop = Tenant.objects.create(
        supplier=supplier,
        name="Phase 5 Restore Fixture",
        slug=f"p5-restore-{suffix}",
        max_users=3,
        default_currency="USD",
        default_timezone="UTC",
    )
    actor = User.objects.create_user(
        email=f"phase5-restore-{suffix}@example.test",
        password="synthetic-only-not-a-real-credential",
        first_name="Phase 5 Restore",
        phone="+96550001998",
        owning_shop=shop,
    )
    TenantMember.objects.create(tenant=shop, user=actor, role=ShopRole.ADMIN)
    client = Client.objects.create(tenant=shop, name="Synthetic Restore Client")
    family = GarmentFamily.objects.get(code="mens-shirt")
    design = Design.objects.create(tenant=shop, family=family)
    now = timezone.now()
    design_version = DesignVersion.objects.create(
        design=design,
        number=1,
        status=DesignVersion.Status.PUBLISHED,
        published_at=now,
        published_by=actor,
    )
    profile = MeasurementProfile.objects.create(
        tenant=shop, client=client, family=family
    )
    measurement = MeasurementSet.objects.create(
        profile=profile, version=1, design_version=design_version
    )
    work = WorkOrder.objects.create(
        tenant=shop,
        sequence=1,
        work_number=f"P5-{suffix}",
        client=client,
        design_version=design_version,
        design_price_amount="20.0000",
        design_price_currency="USD",
        measurement_set=measurement,
        created_by=actor,
        updated_by=actor,
    )
    invoice = Invoice.objects.create(
        tenant=shop,
        work=work,
        client=client,
        currency="USD",
        status=Invoice.Status.ISSUED,
        invoice_number="INV-000001",
        discount_type=Invoice.DiscountType.FIXED,
        discount_value="1.00",
        tax_rate="10.00",
        issued_at=now,
        issued_by=actor,
        created_by=actor,
        updated_by=actor,
    )
    InvoiceLineItem.objects.create(
        invoice=invoice,
        source=InvoiceLineItem.Source.MANUAL,
        description="Synthetic garment",
        quantity="1.000",
        unit_price="20.0000",
        line_total="20.0000",
        discount_amount="1.0000",
        tax_amount="1.9000",
        created_by=actor,
        updated_by=actor,
    )
    payment = InvoicePayment.objects.create(
        invoice=invoice,
        amount="10.0000",
        received_at=now,
        recorded_by=actor,
        created_by=actor,
        updated_by=actor,
    )
    credit_note = CreditNote.objects.create(
        tenant=shop,
        invoice=invoice,
        credit_number="CN-000001",
        status=CreditNote.Status.ISSUED,
        reason="Synthetic restore adjustment",
        amount="2.0000",
        issued_at=now,
        issued_by=actor,
        created_by=actor,
        updated_by=actor,
    )
    ShopFinancialSequence.objects.create(
        tenant=shop,
        kind=ShopFinancialSequence.Kind.INVOICE,
        last_number=1,
        created_by=actor,
        updated_by=actor,
    )
    ShopFinancialSequence.objects.create(
        tenant=shop,
        kind=ShopFinancialSequence.Kind.CREDIT_NOTE,
        last_number=1,
        created_by=actor,
        updated_by=actor,
    )
    InvoiceRefund.objects.create(
        payment=payment,
        credit_note=credit_note,
        amount="1.0000",
        refunded_at=now,
        recorded_by=actor,
        created_by=actor,
        updated_by=actor,
    )

    media_root.mkdir(parents=True, exist_ok=False)
    file_field = FinancialDocument._meta.get_field("file")
    with override_settings(PRIVATE_MEDIA_ROOT=str(media_root), R2_ENABLED=False):
        storage = PrivateReferenceStorage()
        content = invoice_pdf(invoice, locale="en")
        document = FinancialDocument(
            tenant=shop,
            kind=FinancialDocument.Kind.INVOICE,
            invoice=invoice,
            locale="en",
            layout_version=FINANCIAL_PDF_LAYOUT_VERSION,
            sha256=hashlib.sha256(content).hexdigest(),
            generated_by=actor,
            generated_at=now,
            created_by=actor,
            updated_by=actor,
        )
        with patch.object(file_field, "storage", storage):
            document.file.save(
                f"invoice-INV-000001-en-layout-{FINANCIAL_PDF_LAYOUT_VERSION}.pdf",
                ContentFile(content),
                save=False,
            )
            document.save()

    connections.close_all()
    print(
        json.dumps(
            {
                "shop_id": str(shop.pk),
                "work_id": str(work.pk),
                "document_id": str(document.pk),
            }
        )
    )


def _verify_restored_financial_data(
    suffix: str, shop_id: str, document_id: str, media_root: Path
) -> None:
    target_name = _expected_database("verify", suffix)
    if settings.DATABASES["default"]["NAME"] != target_name:
        raise SystemExit("Verify stage refuses to run unless DB_NAME is the exact disposable target name.")
    _validate_temp_media_path(media_root, "verify", suffix)
    connections.close_all()

    invoice = Invoice.objects.get(tenant_id=shop_id, invoice_number="INV-000001")
    assert Invoice.objects.filter(tenant_id=shop_id).count() == 1
    assert InvoiceLineItem.objects.filter(invoice=invoice).count() == 1
    assert InvoicePayment.objects.filter(invoice=invoice).count() == 1
    assert CreditNote.objects.filter(tenant_id=shop_id, invoice=invoice).count() == 1
    assert InvoiceRefund.objects.filter(credit_note__invoice=invoice).count() == 1
    assert invoice.work.tenant_id == invoice.tenant_id == invoice.client.tenant_id
    assert invoice.subtotal == Decimal("20.0000")
    assert invoice.discount_total == Decimal("1.0000")
    assert invoice.tax_total == Decimal("1.9000")
    assert invoice.total_amount == Decimal("20.9000")
    assert invoice.amount_paid == Decimal("10.0000")
    assert invoice.credited_total == Decimal("2.0000")
    assert invoice.amount_refunded == Decimal("1.0000")
    assert invoice.balance == Decimal("9.9000")
    document = FinancialDocument.objects.get(
        pk=document_id, tenant_id=shop_id, invoice=invoice
    )
    assert document.layout_version == FINANCIAL_PDF_LAYOUT_VERSION
    assert document.file.name.endswith(
        f"invoice-INV-000001-en-layout-{FINANCIAL_PDF_LAYOUT_VERSION}.pdf"
    )
    with override_settings(PRIVATE_MEDIA_ROOT=str(media_root), R2_ENABLED=False):
        storage = PrivateReferenceStorage()
        assert storage.exists(document.file.name)
        with storage.open(document.file.name, "rb") as restored_pdf:
            content = restored_pdf.read()
    assert content.startswith(b"%PDF-")
    assert hashlib.sha256(content).hexdigest() == document.sha256
    connections.close_all()
    print(
        json.dumps(
            {
                "status": "pass",
                "invoice_number": invoice.invoice_number,
                "layout_version": document.layout_version,
            }
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("preflight", "seed", "verify"), required=True)
    parser.add_argument("--suffix", required=True)
    parser.add_argument("--media-root", type=Path)
    parser.add_argument("--shop-id")
    parser.add_argument("--document-id")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{12}", args.suffix):
        raise SystemExit("--suffix must be exactly 12 lowercase hexadecimal characters.")

    if args.stage == "preflight":
        _preflight(args.suffix)
    elif args.stage == "seed":
        if args.media_root is None:
            raise SystemExit("--media-root is required for seed stage.")
        _seed_synthetic_financial_data(args.suffix, args.media_root)
    else:
        if args.media_root is None or not args.shop_id or not args.document_id:
            raise SystemExit("--media-root, --shop-id, and --document-id are required for verify stage.")
        _verify_restored_financial_data(
            args.suffix, args.shop_id, args.document_id, args.media_root
        )


if __name__ == "__main__":
    main()
