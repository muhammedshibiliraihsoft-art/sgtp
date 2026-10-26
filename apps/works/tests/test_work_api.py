from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from io import BytesIO
import hashlib
from threading import Barrier
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.base import ContentFile
from django.test import SimpleTestCase, override_settings
from django.db import close_old_connections, connection
from django.test import TransactionTestCase, skipUnlessDBFeature
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import User
from apps.catalog.models import (
    Design,
    DesignVersion,
    GarmentFamily,
    GarmentVariant,
    MeasurementProfile,
    MeasurementSet,
    ShopDesignPrice,
)
from apps.catalog.storage import PrivateReferenceStorage
from apps.catalog.serializers import DesignSerializer
from apps.clients.models import Client, RelatedPerson
from apps.billing.models import (
    CreditNote,
    FinanceMutation,
    FinancialAuditEvent,
    FinancialDocument,
    Invoice,
    InvoicePayment,
    InvoiceRefund,
)
from apps.tenants.models import (
    MembershipWorkFunction,
    ShopRole,
    Supplier,
    Tenant,
    TenantMember,
)
from apps.tenants.currency import validate_money_amount
from apps.works.constants import WorkStatus
from apps.works.models import WorkEvent, WorkOrder
from apps.works.services import due_indicator


class DueIndicatorTests(SimpleTestCase):
    def test_shop_calendar_cutoffs(self):
        class Shop:
            default_timezone = "Asia/Kuwait"

        class Order:
            tenant = Shop()
            due_date = None

        now = timezone.now()
        today = timezone.localtime(
            now, __import__("zoneinfo").ZoneInfo("Asia/Kuwait")
        ).date()
        order = Order()
        self.assertIsNone(due_indicator(order, now=now))
        for offset, expected in (
            (-1, "OVERDUE"),
            (0, "DUE_TODAY"),
            (1, "DUE_SOON"),
            (2, "DUE_SOON"),
            (3, "UPCOMING"),
        ):
            order.due_date = today + timedelta(days=offset)
            self.assertEqual(due_indicator(order, now=now), expected)

    def test_shop_local_midnight_controls_due_day(self):
        class Shop:
            default_timezone = "Asia/Kuwait"

        class Order:
            tenant = Shop()
            due_date = None

        # 21:30 UTC is already 00:30 on the next calendar day in Kuwait.
        now = datetime(2026, 10, 20, 21, 30, tzinfo=UTC)
        today = date(2026, 10, 21)
        order = Order()
        cases = (
            (-1, "OVERDUE"),
            (0, "DUE_TODAY"),
            (1, "DUE_SOON"),
            (2, "DUE_SOON"),
            (3, "UPCOMING"),
        )
        for offset, expected in cases:
            with self.subTest(offset=offset):
                order.due_date = today + timedelta(days=offset)
                self.assertEqual(due_indicator(order, now=now), expected)


class CurrencyPrecisionTests(SimpleTestCase):
    def test_minor_units_are_enforced_without_rounding(self):
        self.assertEqual(validate_money_amount("10.125", "KWD"), Decimal("10.125"))
        self.assertEqual(validate_money_amount("10", "JPY"), Decimal("10"))
        for amount, currency in (("10.125", "USD"), ("10.01", "JPY"), ("1.00001", "KWD")):
            with self.subTest(amount=amount, currency=currency):
                with self.assertRaises(ValueError):
                    validate_money_amount(amount, currency)
        with self.assertRaises(ValueError):
            validate_money_amount("10", "ZZZ")


class WorkApiTests(APITestCase):
    def setUp(self):
        self._mutation_seq = 0
        original_generic = self.client.generic

        def generic_with_idempotency(method, path, *args, **kwargs):
            if method.upper() not in {"GET", "HEAD", "OPTIONS"}:
                self._mutation_seq += 1
                kwargs.setdefault("HTTP_IDEMPOTENCY_KEY", f"test-finance-{self._mutation_seq}")
            return original_generic(method, path, *args, **kwargs)

        self.client.generic = generic_with_idempotency
        supplier = Supplier.objects.get(singleton_lock=True)
        self.shop = Tenant.objects.create(
            supplier=supplier, name="Work Shop", slug="work-shop", max_users=20
        )
        self.other_shop = Tenant.objects.create(
            supplier=supplier,
            name="Other Work Shop",
            slug="other-work-shop",
            max_users=20,
        )
        self.admin, self.admin_member = self.member(
            "work-admin", self.shop, ShopRole.ADMIN
        )
        self.staff, self.staff_member = self.member(
            "work-staff", self.shop, ShopRole.STAFF
        )
        self.viewer, _ = self.member("work-viewer", self.shop, ShopRole.VIEWER)
        self.foreign_admin, _ = self.member(
            "work-other-admin", self.other_shop, ShopRole.ADMIN
        )
        self.client_record = Client.objects.create(tenant=self.shop, name="Work Client")
        self.foreign_client = Client.objects.create(
            tenant=self.other_shop, name="Foreign Client"
        )
        self.family = GarmentFamily.objects.get(code="mens-shirt")
        self.variant = GarmentVariant.objects.get(family=self.family, is_default=True)
        self.design = Design.objects.create(
            tenant=self.shop, family=self.family, variant=self.variant
        )
        self.design_version = DesignVersion.objects.create(
            design=self.design, number=1, status="PUBLISHED"
        )
        self.profile = MeasurementProfile.objects.create(
            tenant=self.shop,
            client=self.client_record,
            family=self.family,
            variant=self.variant,
        )
        self.measurement_set = MeasurementSet.objects.create(
            profile=self.profile, version=1
        )

    @staticmethod
    def member(name, shop, role):
        user = User.objects.create_user(
            email=f"{name}@example.test",
            password="Safe-Test-Password-293!",
            first_name=name,
            owning_shop=shop,
        )
        membership = TenantMember.objects.create(tenant=shop, user=user, role=role)
        return user, membership

    def url(self, order=None, action="", shop=None):
        base = f"/api/v1/shops/{(shop or self.shop).pk}/works/"
        return base if order is None else f"{base}{order.pk}/{action}"

    def payload(self, **overrides):
        return {
            "client_id": str(self.client_record.pk),
            "design_version_id": str(self.design_version.pk),
            "measurement_set_id": str(self.measurement_set.pk),
            **overrides,
        }

    def create(self, user=None, **overrides):
        self.client.force_authenticate(user or self.admin)
        return self.client.post(self.url(), self.payload(**overrides), format="json")

    def advance(self, order, expected_status=None):
        return self.client.post(
            self.url(order, "advance/"),
            {"expected_status": expected_status or order.status},
            format="json",
        )

    def test_create_search_and_shop_isolation(self):
        response = self.create(priority="VERY_URGENT")
        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["work_number"], "ORD-000001")
        self.assertEqual(response.data["priority"], "VERY_URGENT")
        order = WorkOrder.objects.get(pk=response.data["id"])
        self.assertEqual(
            self.client.get(self.url() + "?search=ORD-000001").data["count"], 1
        )
        self.client.force_authenticate(self.foreign_admin)
        self.assertEqual(
            self.client.get(self.url(order, shop=self.other_shop)).status_code, 404
        )
        self.assertEqual(
            self.client.get(self.url(shop=self.other_shop)).data["count"], 0
        )
        self.client.force_authenticate(self.admin)
        self.assertEqual(
            self.create(client_id=str(self.foreign_client.pk)).status_code, 400
        )

    def test_work_captures_shop_design_price_and_keeps_the_snapshot(self):
        self.shop.default_currency = "KWD"
        self.shop.save(update_fields=["default_currency"])
        price = ShopDesignPrice.objects.create(
            tenant=self.shop,
            design=self.design,
            amount="12.500",
            currency="KWD",
            created_by=self.admin,
            updated_by=self.admin,
        )
        first = self.create()
        self.assertEqual(first.status_code, 201, first.data)
        first_order = WorkOrder.objects.get(pk=first.data["id"])
        self.assertEqual(first_order.design_price_amount, Decimal("12.500"))
        self.assertEqual(first_order.design_price_currency, "KWD")
        self.assertNotIn("design_price_amount", first.data)

        first_order.design_price_amount = Decimal("99.000")
        with self.assertRaises(DjangoValidationError):
            first_order.save(update_fields=("design_price_amount",))

        price.amount = Decimal("15.000")
        price.save(update_fields=["amount"])
        second = self.create()
        self.assertEqual(second.status_code, 201, second.data)
        first_order.refresh_from_db()
        second_order = WorkOrder.objects.get(pk=second.data["id"])
        self.assertEqual(first_order.design_price_amount, Decimal("12.500"))
        self.assertEqual(second_order.design_price_amount, Decimal("15.000"))

    def test_design_price_requires_admin_or_cashier_and_currency_precision(self):
        price_url = f"/api/v1/shops/{self.shop.pk}/design-prices/{self.design.pk}/"
        self.shop.default_currency = "KWD"
        self.shop.save(update_fields=["default_currency"])

        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.put(price_url, {"amount": "12.500"}, format="json").status_code, 403)
        MembershipWorkFunction.objects.create(
            membership=self.staff_member, function_code="CASHIER"
        )
        allowed = self.client.put(price_url, {"amount": "12.500"}, format="json")
        self.assertEqual(allowed.status_code, 200, allowed.data)
        self.assertEqual(allowed.data["currency"], "KWD")

        self.shop.default_currency = "JPY"
        with self.assertRaises(DjangoValidationError):
            self.shop.save(update_fields=["default_currency"])
        self.shop.refresh_from_db()

        yen_shop = Tenant.objects.create(
            supplier=self.shop.supplier, name="Yen Shop", slug="yen-shop",
            max_users=20, default_currency="JPY",
        )
        yen_admin, _ = self.member("yen-admin", yen_shop, ShopRole.ADMIN)
        yen_design = Design.objects.create(
            tenant=yen_shop, family=self.family, variant=self.variant
        )
        yen_price_url = f"/api/v1/shops/{yen_shop.pk}/design-prices/{yen_design.pk}/"
        self.client.force_authenticate(yen_admin)
        rejected = self.client.put(yen_price_url, {"amount": "12.50"}, format="json")
        self.assertEqual(rejected.status_code, 400, rejected.data)

        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.get(price_url).status_code, 403)
        self.client.force_authenticate(self.foreign_admin)
        self.assertEqual(
            self.client.get(
                f"/api/v1/shops/{self.other_shop.pk}/design-prices/{self.design.pk}/"
            ).status_code,
            404,
        )

    def test_design_price_entry_fails_when_shop_currency_is_missing_or_invalid(self):
        price_url = f"/api/v1/shops/{self.shop.pk}/design-prices/{self.design.pk}/"
        self.client.force_authenticate(self.admin)
        missing = self.client.put(price_url, {"amount": "10.00"}, format="json")
        self.assertEqual(missing.status_code, 400, missing.data)
        self.shop.default_currency = "ZZZ"
        self.shop.save(update_fields=["default_currency"])
        invalid = self.client.put(price_url, {"amount": "10.00"}, format="json")
        self.assertEqual(invalid.status_code, 400, invalid.data)

    def test_invoice_auto_manual_issue_partial_payment_and_work_stage_isolation(self):
        self.shop.default_currency = "KWD"
        self.shop.save(update_fields=["default_currency"])
        self.client.force_authenticate(self.admin)
        price_url = f"/api/v1/shops/{self.shop.pk}/design-prices/{self.design.pk}/"
        priced = self.client.put(price_url, {"amount": "12.500"}, format="json")
        self.assertEqual(priced.status_code, 200, priced.data)

        created_work = self.create()
        self.assertEqual(created_work.status_code, 201, created_work.data)
        work = WorkOrder.objects.get(pk=created_work.data["id"])
        invoices_url = f"/api/v1/shops/{self.shop.pk}/works/{work.pk}/invoices/"
        created_invoice = self.client.post(
            invoices_url,
            {
                "mode": "AUTO",
                "lines": [
                    {"description": "Alteration", "quantity": "2", "unit_price": "3.250"}
                ],
            },
            format="json",
        )
        self.assertEqual(created_invoice.status_code, 201, created_invoice.data)
        invoice_id = created_invoice.data["id"]
        self.assertEqual(created_invoice.data["client_id"], str(self.client_record.pk))
        self.assertEqual(created_invoice.data["currency"], "KWD")
        self.assertEqual(created_invoice.data["subtotal"], "19.0000")
        self.assertEqual(created_invoice.data["balance"], "19.0000")
        self.assertEqual(len(created_invoice.data["items"]), 2)
        self.assertEqual(created_invoice.data["items"][0]["source"], "DESIGN_SNAPSHOT")

        item_url = f"/api/v1/shops/{self.shop.pk}/invoices/{invoice_id}/items/"
        added = self.client.post(
            item_url,
            {"description": "Buttons", "quantity": "1", "unit_price": "2.000"},
            format="json",
        )
        self.assertEqual(added.status_code, 201, added.data)
        self.assertEqual(self.client.get(f"/api/v1/shops/{self.shop.pk}/invoices/{invoice_id}/").data["subtotal"], "21.0000")
        changed = self.client.patch(
            f"{item_url}{added.data['id']}/", {"unit_price": "1.000"}, format="json"
        )
        self.assertEqual(changed.status_code, 200, changed.data)
        self.assertEqual(self.client.get(f"/api/v1/shops/{self.shop.pk}/invoices/{invoice_id}/").data["subtotal"], "20.0000")
        self.assertEqual(
            self.client.delete(f"{item_url}{added.data['id']}/").status_code, 204
        )
        self.assertEqual(self.client.get(f"/api/v1/shops/{self.shop.pk}/invoices/{invoice_id}/").data["subtotal"], "19.0000")

        issue_url = f"/api/v1/shops/{self.shop.pk}/invoices/{invoice_id}/issue/"
        issued = self.client.post(issue_url, {}, format="json")
        self.assertEqual(issued.status_code, 200, issued.data)
        self.assertEqual(issued.data["status"], "ISSUED")
        self.assertEqual(issued.data["balance"], "19.0000")
        self.assertEqual(work.status, WorkStatus.REQUEST)
        issued_invoice = Invoice.objects.get(pk=invoice_id)
        issued_invoice.currency = "USD"
        with self.assertRaises(DjangoValidationError):
            issued_invoice.save(update_fields=("currency",))
        issued_line_id = created_invoice.data["items"][0]["id"]
        self.assertEqual(
            self.client.patch(
                f"{item_url}{issued_line_id}/",
                {"unit_price": "99.000"},
                format="json",
            ).status_code,
            400,
        )

        payment_url = f"/api/v1/shops/{self.shop.pk}/invoices/{invoice_id}/payments/"
        partial = self.client.post(payment_url, {"amount": "5.000"}, format="json")
        self.assertEqual(partial.status_code, 201, partial.data)
        self.assertEqual(InvoicePayment.objects.filter(invoice_id=invoice_id).count(), 1)
        detail_url = f"/api/v1/shops/{self.shop.pk}/invoices/{invoice_id}/"
        detail = self.client.get(detail_url)
        self.assertEqual(detail.data["amount_paid"], "5.0000")
        self.assertEqual(detail.data["balance"], "14.0000")
        self.assertEqual(WorkOrder.objects.get(pk=work.pk).status, WorkStatus.REQUEST)
        excessive = self.client.post(payment_url, {"amount": "14.001"}, format="json")
        self.assertEqual(excessive.status_code, 400, excessive.data)

        manual = self.client.post(
            invoices_url,
            {
                "mode": "MANUAL",
                "lines": [
                    {"description": "Extra work", "quantity": "1", "unit_price": "8.000"}
                ],
            },
            format="json",
        )
        self.assertEqual(manual.status_code, 201, manual.data)
        self.assertEqual(Invoice.objects.filter(work=work).count(), 2)
        self.assertEqual(manual.data["subtotal"], "8.0000")
        self.assertEqual(manual.data["currency"], "KWD")
        self.assertEqual(
            list(
                Invoice.objects.filter(tenant=self.shop, work=work)
                .values_list("currency", flat=True)
                .order_by("currency")
                .distinct()
            ),
            ["KWD"],
        )
        empty = self.client.post(invoices_url, {"mode": "MANUAL"}, format="json")
        self.assertEqual(empty.status_code, 201, empty.data)
        self.assertEqual(
            self.client.post(
                f"/api/v1/shops/{self.shop.pk}/invoices/{empty.data['id']}/issue/",
                {},
                format="json",
            ).status_code,
            400,
        )
        issued_manual = self.client.post(
            f"/api/v1/shops/{self.shop.pk}/invoices/{manual.data['id']}/issue/",
            {},
            format="json",
        )
        self.assertEqual(issued_manual.status_code, 200, issued_manual.data)
        outstanding = self.client.get(
            f"/api/v1/shops/{self.shop.pk}/billing/outstanding/"
        )
        self.assertEqual(outstanding.status_code, 200, outstanding.data)
        self.assertEqual(
            [item["id"] for item in outstanding.data["results"]],
            [invoice_id, manual.data["id"]],
        )

        deleted = self.client.delete(self.url(work))
        self.assertEqual(deleted.status_code, 400, deleted.data)
        self.assertTrue(WorkOrder.objects.filter(pk=work.pk).exists())

    def test_invoice_access_requires_financial_permission_and_stays_shop_scoped(self):
        self.shop.default_currency = "USD"
        self.shop.save(update_fields=["default_currency"])
        work_response = self.create()
        self.assertEqual(work_response.status_code, 201, work_response.data)
        work_id = work_response.data["id"]
        invoices_url = f"/api/v1/shops/{self.shop.pk}/works/{work_id}/invoices/"

        self.client.force_authenticate(self.staff)
        self.assertEqual(self.client.get(invoices_url).status_code, 403)
        self.assertEqual(
            self.client.post(invoices_url, {"mode": "MANUAL"}, format="json").status_code,
            403,
        )
        MembershipWorkFunction.objects.create(
            membership=self.staff_member, function_code="CASHIER"
        )
        allowed = self.client.post(invoices_url, {"mode": "MANUAL"}, format="json")
        self.assertEqual(allowed.status_code, 201, allowed.data)
        invoice_url = f"/api/v1/shops/{self.shop.pk}/invoices/{allowed.data['id']}/"
        self.client.force_authenticate(self.foreign_admin)
        self.assertEqual(
            self.client.get(
                f"/api/v1/shops/{self.other_shop.pk}/invoices/{allowed.data['id']}/"
            ).status_code,
            404,
        )
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(invoice_url).status_code, 200)

    def test_related_person_invoice_is_owned_by_primary_client(self):
        self.shop.default_currency = "USD"
        self.shop.save(update_fields=["default_currency"])
        related_person = RelatedPerson.objects.create(
            tenant=self.shop,
            primary_client=self.client_record,
            name="Work Wearer",
        )
        profile = MeasurementProfile.objects.create(
            tenant=self.shop,
            related_person=related_person,
            family=self.family,
            variant=self.variant,
        )
        measurement_set = MeasurementSet.objects.create(profile=profile, version=1)
        work_response = self.create(
            related_person_id=str(related_person.pk),
            measurement_set_id=str(measurement_set.pk),
        )
        self.assertEqual(work_response.status_code, 201, work_response.data)
        invoices_url = (
            f"/api/v1/shops/{self.shop.pk}/works/{work_response.data['id']}/invoices/"
        )
        invoice = self.client.post(
            invoices_url,
            {
                "mode": "MANUAL",
                "lines": [
                    {
                        "description": "Garment",
                        "quantity": "1",
                        "unit_price": "10.00",
                    }
                ],
            },
            format="json",
        )
        self.assertEqual(invoice.status_code, 201, invoice.data)
        self.assertEqual(invoice.data["client_id"], str(self.client_record.pk))
        self.assertEqual(invoice.data["related_person_id"], str(related_person.pk))

    def test_invoice_adjustments_numbering_credit_note_and_refund_are_immutable(self):
        self.shop.default_currency = "USD"
        self.shop.save(update_fields=["default_currency"])
        self.client.force_authenticate(self.admin)
        work = self.create()
        self.assertEqual(work.status_code, 201, work.data)
        invoices_url = f"/api/v1/shops/{self.shop.pk}/works/{work.data['id']}/invoices/"
        draft = self.client.post(
            invoices_url,
            {
                "mode": "MANUAL",
                "lines": [
                    {"description": "Top", "quantity": "1", "unit_price": "10.00"},
                    {"description": "Skirt", "quantity": "1", "unit_price": "20.00"},
                ],
                "discount_type": "FIXED",
                "discount_value": "3.00",
                "tax_rate": "10.00",
            },
            format="json",
        )
        self.assertEqual(draft.status_code, 201, draft.data)
        self.assertEqual(draft.data["subtotal"], "30.0000")
        self.assertEqual(draft.data["discount_total"], "3.0000")
        self.assertEqual(draft.data["tax_total"], "2.7000")
        self.assertEqual(draft.data["total_amount"], "29.7000")

        invoice_id = draft.data["id"]
        root = f"/api/v1/shops/{self.shop.pk}/invoices/{invoice_id}/"
        issued = self.client.post(f"{root}issue/", {}, format="json")
        self.assertEqual(issued.status_code, 200, issued.data)
        self.assertEqual(issued.data["invoice_number"], "INV-000001")
        self.assertEqual([item["discount_amount"] for item in issued.data["items"]], ["1.0000", "2.0000"])
        payment = self.client.post(f"{root}payments/", {"amount": "20.00"}, format="json")
        self.assertEqual(payment.status_code, 201, payment.data)

        file_field = FinancialDocument._meta.get_field("file")
        private_media = TemporaryDirectory(prefix="sgtp-financial-documents-")
        self.addCleanup(private_media.cleanup)
        with override_settings(PRIVATE_MEDIA_ROOT=private_media.name, R2_ENABLED=False):
            private_storage = PrivateReferenceStorage()

        def assert_private_pdf(document_id):
            document = FinancialDocument.objects.get(pk=document_id)
            self.assertEqual(document.layout_version, 2)
            self.assertTrue(private_storage.exists(document.file.name))
            with private_storage.open(document.file.name, "rb") as stored_pdf:
                content = stored_pdf.read()
            self.assertTrue(content.startswith(b"%PDF-"))
            self.assertEqual(hashlib.sha256(content).hexdigest(), document.sha256)
            with self.assertRaises(ValueError):
                private_storage.url(document.file.name)
            return document

        legacy_output = BytesIO()
        legacy_canvas = Canvas(legacy_output, pagesize=A4, invariant=1)
        legacy_canvas.drawString(20, 20, "Existing immutable A4 invoice")
        legacy_canvas.save()
        legacy_pdf = legacy_output.getvalue()

        self.admin.preferred_locale = "ur"
        self.admin.phone = "+96550000001"
        self.admin.save(update_fields=("preferred_locale", "phone"))
        with patch.object(file_field, "storage", private_storage):
            legacy_document = FinancialDocument(
                tenant=self.shop,
                kind=FinancialDocument.Kind.INVOICE,
                invoice=Invoice.objects.get(pk=invoice_id),
                locale="ar-KW",
                layout_version=1,
                sha256=hashlib.sha256(legacy_pdf).hexdigest(),
                generated_by=self.admin,
                generated_at=timezone.now(),
                created_by=self.admin,
                updated_by=self.admin,
            )
            legacy_document.file.save(
                f"invoice-{invoice_id}-ar-KW-layout-1.pdf",
                ContentFile(legacy_pdf),
                save=False,
            )
            legacy_document.save()
            legacy_path = legacy_document.file.name

            invoice_doc_url = f"{root}documents/"
            invoice_doc = self.client.post(invoice_doc_url, {"locale": "ar-KW"}, format="json")
            self.assertEqual(invoice_doc.status_code, 200, invoice_doc.data)
            self.assertNotEqual(invoice_doc.data["id"], str(legacy_document.pk))
            current_document = FinancialDocument.objects.get(pk=invoice_doc.data["id"])
            self.assertEqual(current_document.layout_version, 2)
            self.assertEqual(legacy_document.layout_version, 1)
            with private_storage.open(legacy_path, "rb") as old_file:
                self.assertEqual(old_file.read(), legacy_pdf)
            legacy_download = self.client.get(
                f"/api/v1/shops/{self.shop.pk}/financial-documents/"
                f"{legacy_document.pk}/download/"
            )
            self.assertEqual(legacy_download.status_code, 200)
            self.assertEqual(b"".join(legacy_download.streaming_content), legacy_pdf)
            invoice_doc_retry = self.client.post(invoice_doc_url, {"locale": "ar-KW"}, format="json")
            self.assertEqual(invoice_doc_retry.data["id"], invoice_doc.data["id"])
            invoice_default = self.client.post(invoice_doc_url, {}, format="json")
            self.assertEqual(invoice_default.data["locale"], "ur")
            self.assertEqual(FinancialDocument.objects.filter(invoice_id=invoice_id).count(), 3)
            invoice_pdf_response = self.client.get(
                f"/api/v1/shops/{self.shop.pk}/financial-documents/{invoice_doc.data['id']}/download/"
            )
            self.assertEqual(invoice_pdf_response.status_code, 200)
            self.assertEqual(invoice_pdf_response["Content-Type"], "application/pdf")
            self.assertIn("no-store", invoice_pdf_response["Cache-Control"])
            downloaded_pdf = b"".join(invoice_pdf_response.streaming_content)
            self.assertTrue(downloaded_pdf.startswith(b"%PDF-"))
            stored_document = assert_private_pdf(invoice_doc.data["id"])
            self.assertTrue(stored_document.file.name.endswith("-layout-2.pdf"))
            with private_storage.open(stored_document.file.name, "rb") as stored_pdf:
                self.assertEqual(stored_pdf.read(), downloaded_pdf)
            foreign_download = self.client.get(
                f"/api/v1/shops/{self.other_shop.pk}/financial-documents/{stored_document.pk}/download/"
            )
            self.assertEqual(foreign_download.status_code, 404)

            receipt = self.client.post(
                f"{root}payments/{payment.data['id']}/receipt/", {"locale": "bn"}, format="json"
            )
            self.assertEqual(receipt.status_code, 200, receipt.data)
            assert_private_pdf(receipt.data["id"])
            self.assertEqual(receipt.status_code, 200, receipt.data)

        credit = self.client.post(
            f"{root}credit-notes/", {"amount": "5.00", "reason": "Returned item"}, format="json"
        )
        self.assertEqual(credit.status_code, 201, credit.data)
        credit_id = credit.data["id"]
        issued_credit = self.client.post(
            f"/api/v1/shops/{self.shop.pk}/credit-notes/{credit_id}/issue/", {}, format="json"
        )
        self.assertEqual(issued_credit.status_code, 200, issued_credit.data)
        self.assertEqual(issued_credit.data["credit_number"], "CN-000001")
        with patch.object(file_field, "storage", private_storage):
            credit_document = self.client.post(
                f"/api/v1/shops/{self.shop.pk}/credit-notes/{credit_id}/documents/",
                {"locale": "ur"}, format="json",
            )
        self.assertEqual(credit_document.status_code, 200, credit_document.data)
        assert_private_pdf(credit_document.data["id"])
        refund = self.client.post(
            f"/api/v1/shops/{self.shop.pk}/credit-notes/{credit_id}/refunds/",
            {"payment_id": payment.data["id"], "amount": "5.00"},
            format="json",
        )
        self.assertEqual(refund.status_code, 201, refund.data)
        self.assertEqual(InvoiceRefund.objects.count(), 1)
        detail = self.client.get(root)
        self.assertEqual(detail.data["amount_refunded"], "5.0000")
        self.assertEqual(detail.data["credited_total"], "5.0000")
        self.assertEqual(detail.data["balance"], "9.7000")
        self.assertEqual(WorkOrder.objects.get(pk=work.data["id"]).status, WorkStatus.REQUEST)
        self.assertGreaterEqual(FinancialAuditEvent.objects.count(), 5)

    def test_invoice_creation_idempotency_replays_and_rejects_reused_key_with_new_body(self):
        self.shop.default_currency = "USD"
        self.shop.save(update_fields=["default_currency"])
        self.client.force_authenticate(self.admin)
        work = self.create()
        url = f"/api/v1/shops/{self.shop.pk}/works/{work.data['id']}/invoices/"
        request = {"mode": "MANUAL", "lines": [{"description": "Alteration", "unit_price": "8.00"}]}
        first = self.client.post(url, request, format="json", HTTP_IDEMPOTENCY_KEY="invoice-create-retry")
        replay = self.client.post(url, request, format="json", HTTP_IDEMPOTENCY_KEY="invoice-create-retry")
        self.assertEqual(first.status_code, 201, first.data)
        self.assertEqual(replay.status_code, 201, replay.data)
        self.assertEqual(first.data["id"], replay.data["id"])
        issue_url = f"/api/v1/shops/{self.shop.pk}/invoices/{first.data['id']}/issue/"
        issued = self.client.post(issue_url, {}, format="json", HTTP_IDEMPOTENCY_KEY="invoice-issue-after-create")
        self.assertEqual(issued.status_code, 200, issued.data)
        replay_after_later_change = self.client.post(
            url, request, format="json", HTTP_IDEMPOTENCY_KEY="invoice-create-retry"
        )
        self.assertEqual(replay_after_later_change.status_code, 201, replay_after_later_change.data)
        self.assertEqual(replay_after_later_change.data, first.data)
        self.assertEqual(Invoice.objects.get(pk=first.data["id"]).status, Invoice.Status.ISSUED)
        self.assertEqual(Invoice.objects.filter(work_id=work.data["id"]).count(), 1)
        conflict = self.client.post(
            url,
            {"mode": "MANUAL", "lines": [{"description": "Different", "unit_price": "8.00"}]},
            format="json",
            HTTP_IDEMPOTENCY_KEY="invoice-create-retry",
        )
        self.assertEqual(conflict.status_code, 409, conflict.data)
        self.assertEqual(FinanceMutation.objects.filter(key="invoice-create-retry").count(), 1)

    def test_invoice_create_replay_returns_snapshot_after_draft_is_deleted(self):
        self.shop.default_currency = "USD"
        self.shop.save(update_fields=["default_currency"])
        self.client.force_authenticate(self.admin)
        work = self.create()
        url = f"/api/v1/shops/{self.shop.pk}/works/{work.data['id']}/invoices/"
        request = {"mode": "MANUAL", "lines": [{"description": "Repair", "unit_price": "12.00"}]}
        first = self.client.post(url, request, format="json", HTTP_IDEMPOTENCY_KEY="invoice-create-deleted-replay")
        self.assertEqual(first.status_code, 201, first.data)
        deleted = self.client.delete(
            f"/api/v1/shops/{self.shop.pk}/invoices/{first.data['id']}/",
            HTTP_IDEMPOTENCY_KEY="invoice-draft-delete",
        )
        self.assertEqual(deleted.status_code, 204)
        replay = self.client.post(
            url, request, format="json", HTTP_IDEMPOTENCY_KEY="invoice-create-deleted-replay"
        )
        self.assertEqual(replay.status_code, 201, replay.data)
        self.assertEqual(replay.data, first.data)
        self.assertFalse(Invoice.objects.filter(pk=first.data["id"]).exists())

    def test_unpaid_issued_invoice_void_keeps_issued_number_reserved(self):
        self.shop.default_currency = "USD"
        self.shop.save(update_fields=["default_currency"])
        self.client.force_authenticate(self.admin)
        work = self.create()
        url = f"/api/v1/shops/{self.shop.pk}/works/{work.data['id']}/invoices/"
        first = self.client.post(url, {"mode": "MANUAL", "lines": [{"description": "Work", "unit_price": "10.00"}]}, format="json")
        first_root = f"/api/v1/shops/{self.shop.pk}/invoices/{first.data['id']}/"
        issued = self.client.post(f"{first_root}issue/", {}, format="json")
        self.assertEqual(issued.data["invoice_number"], "INV-000001")
        voided = self.client.post(f"{first_root}void/", {"reason": "Duplicate entry"}, format="json")
        self.assertEqual(voided.status_code, 200, voided.data)
        self.assertEqual(voided.data["status"], "VOID")
        second = self.client.post(url, {"mode": "MANUAL", "lines": [{"description": "New work", "unit_price": "11.00"}]}, format="json")
        second_issued = self.client.post(f"/api/v1/shops/{self.shop.pk}/invoices/{second.data['id']}/issue/", {}, format="json")
        self.assertEqual(second_issued.data["invoice_number"], "INV-000002")

    def test_due_indicator_is_serialized_on_work_list_and_detail(self):
        self.shop.default_timezone = "Asia/Kuwait"
        self.shop.save(update_fields=["default_timezone"])
        fixed_now = datetime(2026, 10, 20, 21, 30, tzinfo=UTC)
        local_today = date(2026, 10, 21)
        cases = (
            (-1, "OVERDUE"),
            (0, "DUE_TODAY"),
            (1, "DUE_SOON"),
            (2, "DUE_SOON"),
            (3, "UPCOMING"),
            (None, None),
        )
        self.client.force_authenticate(self.admin)
        expected_by_id = {}
        with patch("apps.works.services.timezone.now", return_value=fixed_now):
            for offset, expected in cases:
                due_date = (
                    (local_today + timedelta(days=offset)).isoformat()
                    if offset is not None
                    else None
                )
                created = self.create(due_date=due_date)
                self.assertEqual(created.status_code, 201, created.data)
                expected_by_id[created.data["id"]] = (due_date, expected)

            listed = self.client.get(self.url())
            self.assertEqual(listed.status_code, 200, listed.data)
            listed_by_id = {item["id"]: item for item in listed.data["results"]}
            self.assertEqual(set(listed_by_id), set(expected_by_id))

            for order_id, (due_date, expected) in expected_by_id.items():
                with self.subTest(order_id=order_id, expected=expected):
                    self.assertEqual(listed_by_id[order_id]["due_date"], due_date)
                    self.assertEqual(listed_by_id[order_id]["due_indicator"], expected)
                    detail = self.client.get(f"{self.url()}{order_id}/")
                    self.assertEqual(detail.status_code, 200, detail.data)
                    self.assertEqual(detail.data["due_date"], due_date)
                    self.assertEqual(detail.data["due_indicator"], expected)

    def test_role_function_and_assignment_transition(self):
        self.assertEqual(self.create(self.viewer).status_code, 403)
        self.assertEqual(self.create(self.staff).status_code, 403)
        MembershipWorkFunction.objects.create(
            membership=self.staff_member, function_code="SALES"
        )
        response = self.create(self.staff)
        self.assertEqual(response.status_code, 201, response.data)
        order = WorkOrder.objects.get(pk=response.data["id"])
        self.client.force_authenticate(self.admin)
        assigned = self.client.post(
            self.url(order, "assign/"),
            {"membership_id": str(self.staff_member.pk)},
            format="json",
        )
        self.assertEqual(assigned.status_code, 200, assigned.data)
        assignment_event = WorkEvent.objects.get(
            work=order, action=WorkEvent.Action.ASSIGNED
        )
        self.assertEqual(assignment_event.after_state["assigned_membership_id"], str(self.staff_member.pk))
        self.assertEqual(self.advance(order).status_code, 403)
        self.client.force_authenticate(self.staff)
        advanced = self.advance(order)
        self.assertEqual(advanced.status_code, 200, advanced.data)
        self.assertEqual(advanced.data["status"], WorkStatus.CUTTING)
        self.assertIsNone(advanced.data["assigned_membership_id"])
        self.assertEqual(self.advance(order).status_code, 409)
        MembershipWorkFunction.objects.create(
            membership=self.staff_member, function_code="CUTTING"
        )
        self.assertEqual(
            self.advance(order, WorkStatus.CUTTING).data["status"],
            WorkStatus.STITCHING,
        )

    def test_advance_requires_expected_status_and_replay_cannot_skip_a_stage(self):
        response = self.create()
        order = WorkOrder.objects.get(pk=response.data["id"])
        self.assertEqual(self.client.post(self.url(order, "advance/")).status_code, 400)

        MembershipWorkFunction.objects.create(
            membership=self.admin_member, function_code="SALES"
        )
        first = self.advance(order, WorkStatus.REQUEST)
        self.assertEqual(first.status_code, 200, first.data)
        self.assertEqual(first.data["status"], WorkStatus.CUTTING)

        replay = self.advance(order, WorkStatus.REQUEST)
        self.assertEqual(replay.status_code, 409, replay.data)
        self.assertEqual(WorkOrder.objects.get(pk=order.pk).status, WorkStatus.CUTTING)
        events = WorkEvent.objects.filter(work=order)
        self.assertEqual(events.filter(action=WorkEvent.Action.STAGE_TRANSITIONED).count(), 1)
        transition = events.get(action=WorkEvent.Action.STAGE_TRANSITIONED)
        self.assertEqual(transition.before_state["status"], WorkStatus.REQUEST)
        self.assertEqual(transition.after_state["status"], WorkStatus.CUTTING)

    def test_audit_events_record_changes_but_never_customer_notes(self):
        response = self.create(notes="private fitting note")
        self.assertEqual(response.status_code, 201, response.data)
        order = WorkOrder.objects.get(pk=response.data["id"])
        created = WorkEvent.objects.get(work=order, action=WorkEvent.Action.CREATED)
        self.assertNotIn("notes", created.after_state)
        self.assertNotIn("private fitting note", str(created.after_state))

        self.client.force_authenticate(self.admin)
        updated = self.client.patch(
            self.url(order), {"notes": "updated private note"}, format="json"
        )
        self.assertEqual(updated.status_code, 200, updated.data)
        event = WorkEvent.objects.get(work=order, action=WorkEvent.Action.UPDATED)
        self.assertEqual(event.changed_fields, ["notes"])
        self.assertNotIn("updated private note", str(event.after_state))

    def test_audit_failure_rolls_back_stage_transition(self):
        response = self.create()
        order = WorkOrder.objects.get(pk=response.data["id"])
        MembershipWorkFunction.objects.create(
            membership=self.admin_member, function_code="SALES"
        )
        with patch("apps.works.services._record_event", side_effect=RuntimeError):
            response = self.advance(order, WorkStatus.REQUEST)
        self.assertEqual(response.status_code, 500)
        self.assertEqual(WorkOrder.objects.get(pk=order.pk).status, WorkStatus.REQUEST)
        self.assertEqual(
            WorkEvent.objects.filter(
                work=order, action=WorkEvent.Action.STAGE_TRANSITIONED
            ).count(),
            0,
        )

    def test_invalid_links_and_read_only_state(self):
        self.assertEqual(
            self.create(design_version_id=str(self.measurement_set.pk)).status_code, 400
        )
        response = self.create()
        self.assertEqual(response.status_code, 201, response.data)
        order = WorkOrder.objects.get(pk=response.data["id"])
        self.client.force_authenticate(self.admin)
        self.assertEqual(
            self.client.patch(
                self.url(order), {"status": "COMPLETED"}, format="json"
            ).status_code,
            400,
        )
        self.assertEqual(WorkOrder.objects.get(pk=order.pk).status, WorkStatus.REQUEST)

    def test_unpublished_design_version_cannot_create_work(self):
        draft = DesignVersion.objects.create(
            design=self.design, number=2, status=DesignVersion.Status.DRAFT
        )

        response = self.create(design_version_id=str(draft.pk))

        self.assertEqual(response.status_code, 400, response.data)
        self.assertIn("design_version", response.data["errors"])

    def test_design_and_measurement_compatibility_is_family_based(self):
        family_design = Design.objects.create(tenant=self.shop, family=self.family)
        family_version = DesignVersion.objects.create(
            design=family_design, number=1, status="PUBLISHED"
        )
        compatible = self.create(design_version_id=str(family_version.pk))
        self.assertEqual(compatible.status_code, 201, compatible.data)

        other_family = GarmentFamily.objects.get(code="abaya")
        incompatible_design = Design.objects.create(
            tenant=self.shop, family=other_family
        )
        incompatible_version = DesignVersion.objects.create(
            design=incompatible_design, number=1, status="PUBLISHED"
        )
        incompatible = self.create(design_version_id=str(incompatible_version.pk))
        self.assertEqual(incompatible.status_code, 400, incompatible.data)

    def test_global_design_is_allowed_for_work_in_a_shop(self):
        global_design = Design.objects.create(tenant=None, family=self.family)
        global_version = DesignVersion.objects.create(
            design=global_design, number=1, status="PUBLISHED"
        )

        response = self.create(design_version_id=str(global_version.pk))

        self.assertEqual(response.status_code, 201, response.data)

    def test_archived_design_blocks_new_work_without_hiding_existing_work(self):
        existing = self.create()
        self.assertEqual(existing.status_code, 201, existing.data)
        existing_order_id = existing.data["id"]

        self.design.status = Design.Status.ARCHIVED
        self.design.save(update_fields=("status",))

        rejected = self.create()
        self.assertEqual(rejected.status_code, 400, rejected.data)
        self.assertIn("design_version", rejected.data["errors"])
        self.assertEqual(WorkOrder.objects.filter(tenant=self.shop).count(), 1)

        historical = self.client.get(self.url(WorkOrder.objects.get(pk=existing_order_id)))
        self.assertEqual(historical.status_code, 200, historical.data)
        self.assertEqual(
            historical.data["design_version_id"], str(self.design_version.pk)
        )

    def test_archived_family_blocks_new_work_without_hiding_existing_work(self):
        existing = self.create()
        self.assertEqual(existing.status_code, 201, existing.data)
        existing_order_id = existing.data["id"]

        self.family.status = GarmentFamily.Status.ARCHIVED
        self.family.save(update_fields=("status",))

        rejected = self.create()
        self.assertEqual(rejected.status_code, 400, rejected.data)
        self.assertIn("design_version", rejected.data["errors"])
        self.assertEqual(WorkOrder.objects.filter(tenant=self.shop).count(), 1)

        historical = self.client.get(self.url(WorkOrder.objects.get(pk=existing_order_id)))
        self.assertEqual(historical.status_code, 200, historical.data)
        self.assertEqual(
            historical.data["design_version_id"], str(self.design_version.pk)
        )

    def test_design_payload_exposes_parent_family_status(self):
        self.assertEqual(
            DesignSerializer(self.design).data["family_status"],
            GarmentFamily.Status.ACTIVE,
        )

    def test_cross_shop_wearer_design_and_measurement_are_rejected(self):
        foreign_person = RelatedPerson.objects.create(
            tenant=self.other_shop,
            primary_client=self.foreign_client,
            name="Foreign wearer",
        )
        foreign_design = Design.objects.create(
            tenant=self.other_shop, family=self.family, variant=self.variant
        )
        foreign_version = DesignVersion.objects.create(
            design=foreign_design, number=1, status="PUBLISHED"
        )
        foreign_profile = MeasurementProfile.objects.create(
            tenant=self.other_shop,
            client=self.foreign_client,
            family=self.family,
            variant=self.variant,
        )
        foreign_set = MeasurementSet.objects.create(profile=foreign_profile, version=1)

        wearer_response = self.create(related_person_id=str(foreign_person.pk))
        design_response = self.create(design_version_id=str(foreign_version.pk))
        measurement_response = self.create(measurement_set_id=str(foreign_set.pk))

        self.assertEqual(wearer_response.status_code, 400, wearer_response.data)
        self.assertEqual(design_response.status_code, 400, design_response.data)
        self.assertEqual(measurement_response.status_code, 400, measurement_response.data)
        self.assertFalse(WorkOrder.objects.filter(tenant=self.shop).exists())

    def test_request_only_delete_preserves_number_high_water_mark(self):
        first = self.create()
        self.assertEqual(first.status_code, 201, first.data)
        order = WorkOrder.objects.get(pk=first.data["id"])
        self.client.force_authenticate(self.viewer)
        self.assertEqual(self.client.delete(self.url(order)).status_code, 403)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.delete(self.url(order)).status_code, 204)
        self.assertTrue(
            WorkEvent.objects.filter(
                work_id=order.pk, action=WorkEvent.Action.SOFT_DELETED
            ).exists()
        )
        self.assertEqual(self.client.get(self.url(order)).status_code, 404)
        second = self.create()
        self.assertEqual(second.data["work_number"], "ORD-000002")

    def test_deleted_orders_are_admin_only_shop_scoped_and_date_filtered(self):
        first = self.create()
        self.assertEqual(first.status_code, 201, first.data)
        deleted_id = first.data["id"]
        self.assertEqual(self.client.delete(self.url(WorkOrder.objects.get(pk=deleted_id))).status_code, 204)
        self.assertEqual(self.create().status_code, 201)
        archive_url = self.url() + "deleted/"
        archived = self.client.get(archive_url)
        self.assertEqual(archived.status_code, 200, archived.data)
        self.assertEqual(archived.data["count"], 1)
        row = archived.data["results"][0]
        self.assertEqual(row["id"], deleted_id)
        self.assertEqual(row["client_name"], self.client_record.name)
        self.assertIn("deleted", row)
        deleted_day = timezone.localtime(
            WorkOrder.all_objects.get(pk=deleted_id).deleted
        ).date().isoformat()
        self.assertEqual(row["deleted_date"], deleted_day)
        self.assertEqual(
            self.client.get(
                archive_url,
                {"deleted_from": deleted_day, "deleted_to": deleted_day},
            ).data["count"],
            1,
        )
        self.assertEqual(
            self.client.get(archive_url, {"deleted_from": "2099-01-01"}).data["count"],
            0,
        )
        self.assertEqual(
            self.client.get(
                archive_url,
                {"deleted_from": "2026-10-18", "deleted_to": "2026-10-17"},
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.get(archive_url, {"deleted_from": "invalid"}).status_code,
            400,
        )
        for user in (self.staff, self.viewer):
            self.client.force_authenticate(user)
            self.assertEqual(self.client.get(archive_url).status_code, 403)
        self.client.force_authenticate(self.foreign_admin)
        self.assertEqual(self.client.get(archive_url).status_code, 404)
        self.assertEqual(
            self.client.get(self.url(shop=self.other_shop) + "deleted/").data["count"],
            0,
        )

    def test_deleted_date_filter_uses_shop_calendar_day(self):
        self.shop.default_timezone = "Asia/Kuwait"
        self.shop.save(update_fields=["default_timezone"])
        created = self.create()
        self.assertEqual(created.status_code, 201, created.data)
        order = WorkOrder.objects.get(pk=created.data["id"])
        self.assertEqual(self.client.delete(self.url(order)).status_code, 204)
        WorkOrder.all_objects.filter(pk=order.pk).update(
            deleted=datetime(2026, 10, 16, 21, 30, tzinfo=UTC)
        )
        archive_url = self.url() + "deleted/"
        on_shop_day = self.client.get(
            archive_url, {"deleted_from": "2026-10-17", "deleted_to": "2026-10-17"}
        )
        self.assertEqual(on_shop_day.data["count"], 1)
        self.assertEqual(on_shop_day.data["results"][0]["deleted_date"], "2026-10-17")
        self.assertEqual(
            self.client.get(
                archive_url,
                {"deleted_from": "2026-10-16", "deleted_to": "2026-10-16"},
            ).data["count"],
            0,
        )

    def test_all_stages_require_current_function_and_end_at_completed(self):
        response = self.create()
        self.assertEqual(response.status_code, 201, response.data)
        order = WorkOrder.objects.get(pk=response.data["id"])
        self.client.force_authenticate(self.admin)
        for code, expected in (
            ("SALES", WorkStatus.CUTTING),
            ("CUTTING", WorkStatus.STITCHING),
            ("STITCHING", WorkStatus.CHECK),
            ("CHECK", WorkStatus.FINISHING),
            ("FINISHING", WorkStatus.QC),
            ("QC", WorkStatus.COMPLETED),
        ):
            with self.subTest(code=code):
                self.assertEqual(
                    self.advance(order, order.status).status_code, 403
                )
                MembershipWorkFunction.objects.get_or_create(
                    membership=self.admin_member, function_code=code
                )
                progressed = self.advance(order, order.status)
                self.assertEqual(progressed.status_code, 200, progressed.data)
                self.assertEqual(progressed.data["status"], expected)
                order.status = expected
        self.assertEqual(self.advance(order, WorkStatus.COMPLETED).status_code, 400)
        self.assertEqual(
            self.client.patch(
                self.url(order), {"notes": "late"}, format="json"
            ).status_code,
            400,
        )

    def test_request_to_completed_preserves_source_links_and_shop_isolation(self):
        created = self.create()
        self.assertEqual(created.status_code, 201, created.data)
        order = WorkOrder.objects.get(pk=created.data["id"])

        source_ids = {
            "client_id": str(self.client_record.pk),
            "design_version_id": str(self.design_version.pk),
            "measurement_set_id": str(self.measurement_set.pk),
        }
        for field, expected in source_ids.items():
            self.assertEqual(created.data[field], expected)
        self.assertEqual(order.tenant_id, self.shop.pk)
        self.assertEqual(order.client_id, self.client_record.pk)
        self.assertEqual(order.design_version_id, self.design_version.pk)
        self.assertEqual(order.measurement_set_id, self.measurement_set.pk)

        stages = (
            ("SALES", WorkStatus.CUTTING),
            ("CUTTING", WorkStatus.STITCHING),
            ("STITCHING", WorkStatus.CHECK),
            ("CHECK", WorkStatus.FINISHING),
            ("FINISHING", WorkStatus.QC),
            ("QC", WorkStatus.COMPLETED),
        )
        for function_code, expected_status in stages:
            with self.subTest(function=function_code):
                MembershipWorkFunction.objects.get_or_create(
                    membership=self.admin_member, function_code=function_code
                )
                assigned = self.client.post(
                    self.url(order, "assign/"),
                    {"membership_id": str(self.admin_member.pk)},
                    format="json",
                )
                self.assertEqual(assigned.status_code, 200, assigned.data)

                advanced = self.advance(order, order.status)
                self.assertEqual(advanced.status_code, 200, advanced.data)
                self.assertEqual(advanced.data["status"], expected_status)
                self.assertIsNone(advanced.data["assigned_membership_id"])
                for field, expected in source_ids.items():
                    self.assertEqual(advanced.data[field], expected)
                order.status = expected_status

        order.refresh_from_db()
        self.assertEqual(order.status, WorkStatus.COMPLETED)
        self.assertIsNone(order.assigned_membership_id)
        self.assertEqual(order.tenant_id, self.shop.pk)
        self.assertEqual(order.client_id, self.client_record.pk)
        self.assertEqual(order.design_version_id, self.design_version.pk)
        self.assertEqual(order.measurement_set_id, self.measurement_set.pk)

        self.client.force_authenticate(self.foreign_admin)
        foreign_shop_list = self.client.get(self.url(shop=self.other_shop))
        self.assertEqual(foreign_shop_list.status_code, 200, foreign_shop_list.data)
        self.assertEqual(foreign_shop_list.data["count"], 0)
        self.assertEqual(
            self.client.get(self.url(order, shop=self.other_shop)).status_code, 404
        )


@skipUnlessDBFeature("has_select_for_update")
class WorkAdvanceConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    def setUp(self):
        self.assertEqual(connection.vendor, "postgresql")
        supplier, _created = Supplier.objects.get_or_create(singleton_lock=True)
        self.shop = Tenant.objects.create(
            supplier=supplier, name="Work Race Shop", slug="work-race-shop", max_users=10
        )
        self.actor = User.objects.create_user(
            email="work-race-admin@example.test",
            password="Safe-Test-Password-293!",
            first_name="Work Race Admin",
            owning_shop=self.shop,
        )
        self.membership = TenantMember.objects.create(
            tenant=self.shop, user=self.actor, role=ShopRole.ADMIN
        )
        MembershipWorkFunction.objects.create(
            membership=self.membership, function_code="SALES"
        )
        client_record = Client.objects.create(tenant=self.shop, name="Race Client")
        family = GarmentFamily.objects.create(
            tenant=self.shop, code="work-race-family"
        )
        design = Design.objects.create(tenant=self.shop, family=family)
        version = DesignVersion.objects.create(
            design=design, number=1, status="PUBLISHED"
        )
        profile = MeasurementProfile.objects.create(
            tenant=self.shop, client=client_record, family=family
        )
        measurement_set = MeasurementSet.objects.create(profile=profile, version=1)
        api = APIClient()
        api.force_authenticate(self.actor)
        created = api.post(
            f"/api/v1/shops/{self.shop.pk}/works/",
            {
                "client_id": str(client_record.pk),
                "design_version_id": str(version.pk),
                "measurement_set_id": str(measurement_set.pk),
            },
            format="json",
        )
        self.assertEqual(created.status_code, 201, created.data)
        self.work_id = created.data["id"]

    def test_simultaneous_same_stage_retries_advance_once(self):
        gate = Barrier(2)

        def advance():
            close_old_connections()
            try:
                actor = User.objects.get(pk=self.actor.pk)
                api = APIClient()
                api.force_authenticate(actor)
                gate.wait(timeout=10)
                response = api.post(
                    f"/api/v1/shops/{self.shop.pk}/works/{self.work_id}/advance/",
                    {"expected_status": WorkStatus.REQUEST},
                    format="json",
                )
                return response.status_code
            finally:
                connection.close()
                close_old_connections()

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = [future.result(timeout=30) for future in (pool.submit(advance), pool.submit(advance))]

        self.assertCountEqual(results, [200, 409])
        self.assertEqual(WorkOrder.objects.get(pk=self.work_id).status, WorkStatus.CUTTING)
        self.assertEqual(
            WorkEvent.objects.filter(
                work_id=self.work_id, action=WorkEvent.Action.STAGE_TRANSITIONED
            ).count(),
            1,
        )
