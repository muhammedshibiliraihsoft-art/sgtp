from unittest.mock import patch

from django.utils import timezone
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.billing.models import (
    CreditNote,
    FinanceMutation,
    FinancialAuditEvent,
    FinancialDocument,
    FinancialPurgeRequest,
    Invoice,
    InvoiceLineItem,
    InvoicePayment,
    InvoiceRefund,
    ShopFinancialSequence,
)
from apps.catalog.models import Design, DesignVersion, GarmentFamily, GarmentVariant, MeasurementProfile, MeasurementSet
from apps.clients.models import Client
from apps.tenants.models import Supplier, Tenant, TenantMember, ShopRole
from apps.works.models import WorkOrder


class InvoiceBundlePurgeTests(APITestCase):
    def setUp(self):
        supplier, _ = Supplier.objects.get_or_create(singleton_lock=True)
        self.shop = Tenant.objects.create(supplier=supplier, name="Purge Shop", slug="purge-shop", max_users=20)
        self.admin = User.objects.create_superuser(
            email="purge-main@example.test", password="Test-password-293!", first_name="Purge Admin",
            phone="+96550000111",
        )
        self.staff = User.objects.create_user(
            email="purge-staff@example.test", password="Test-password-293!", first_name="Purge Staff",
            phone="+96550000112", owning_shop=self.shop,
        )
        TenantMember.objects.create(tenant=self.shop, user=self.staff, role=ShopRole.STAFF)
        client = Client.objects.create(tenant=self.shop, name="Purge Client")
        family = GarmentFamily.objects.get(code="mens-shirt")
        variant = GarmentVariant.objects.get(family=family, is_default=True)
        design = Design.objects.create(tenant=self.shop, family=family, variant=variant)
        version = DesignVersion.objects.create(design=design, number=1, status=DesignVersion.Status.PUBLISHED)
        profile = MeasurementProfile.objects.create(tenant=self.shop, client=client, family=family, variant=variant)
        measurements = MeasurementSet.objects.create(profile=profile, version=1)
        self.work = WorkOrder.objects.create(
            tenant=self.shop, sequence=1, work_number="ORD-000001", client=client,
            design_version=version, measurement_set=measurements,
        )
        self.invoice = Invoice.objects.create(
            tenant=self.shop, work=self.work, client=client, currency="USD", status=Invoice.Status.ISSUED,
            invoice_number="INV-000001", issued_at=timezone.now(), issued_by=self.admin,
            created_by=self.admin, updated_by=self.admin,
        )
        self.line = InvoiceLineItem.objects.create(
            invoice=self.invoice, source=InvoiceLineItem.Source.MANUAL, description="Stitching",
            quantity="1", unit_price="20", line_total="20",
        )
        self.payment = InvoicePayment.objects.create(
            invoice=self.invoice, amount="10", received_at=timezone.now(), recorded_by=self.admin,
        )
        self.credit = CreditNote.objects.create(
            tenant=self.shop, invoice=self.invoice, credit_number="CN-000001", status=CreditNote.Status.ISSUED,
            reason="Correction", amount="5", issued_at=timezone.now(), issued_by=self.admin,
        )
        self.refund = InvoiceRefund.objects.create(
            payment=self.payment, credit_note=self.credit, amount="2", refunded_at=timezone.now(), recorded_by=self.admin,
        )
        self.documents = [
            FinancialDocument.objects.create(
                tenant=self.shop, kind=FinancialDocument.Kind.INVOICE, invoice=self.invoice,
                locale="en", file="financial-documents/invoice.pdf", sha256="a" * 64,
                generated_by=self.admin, generated_at=timezone.now(),
            ),
            FinancialDocument.objects.create(
                tenant=self.shop, kind=FinancialDocument.Kind.RECEIPT, payment=self.payment,
                locale="en", file="financial-documents/receipt.pdf", sha256="b" * 64,
                generated_by=self.admin, generated_at=timezone.now(),
            ),
            FinancialDocument.objects.create(
                tenant=self.shop, kind=FinancialDocument.Kind.CREDIT_NOTE, credit_note=self.credit,
                locale="en", file="financial-documents/credit.pdf", sha256="c" * 64,
                generated_by=self.admin, generated_at=timezone.now(),
            ),
        ]
        self.old_audit = FinancialAuditEvent.objects.create(
            tenant=self.shop, actor=self.admin, action="INVOICE_ISSUED", object_type="Invoice",
            object_id=self.invoice.pk, before={}, after={"total": "20"},
        )
        self.old_mutation = FinanceMutation.objects.create(
            tenant=self.shop, actor=self.admin, key="original-issue", operation="invoice.issue",
            request_hash="d" * 64, resource_type="Invoice", resource_id=self.invoice.pk,
            response_snapshot={"invoice_number": "INV-000001", "total_amount": "20"}, response_status=200,
        )
        self.invoice_sequence = ShopFinancialSequence.objects.create(tenant=self.shop, kind="INVOICE", last_number=4)
        self.credit_sequence = ShopFinancialSequence.objects.create(tenant=self.shop, kind="CREDIT_NOTE", last_number=2)
        self.url = f"/api/v1/shops/{self.shop.pk}/invoices/{self.invoice.pk}/purge/"
        self.payload = {"reason": "Duplicate created in error", "confirm_invoice_number": "INV-000001"}

    def test_main_admin_can_review_and_purge_after_storage_retry_preserving_audit_and_sequences(self):
        self.client.force_authenticate(self.admin)
        invoices_url = f"/api/v1/shops/{self.shop.pk}/billing/invoices/"
        self.assertEqual(self.client.get(invoices_url).status_code, 200)
        storage = FinancialDocument._meta.get_field("file").storage
        with patch.object(storage, "delete", side_effect=OSError("test storage unavailable")):
            failed = self.client.post(self.url, self.payload, format="json", HTTP_IDEMPOTENCY_KEY="purge-1")
        self.assertEqual(failed.status_code, 202, failed.data)
        self.assertEqual(failed.data["status"], FinancialPurgeRequest.Status.FAILED)
        self.assertTrue(Invoice.objects.filter(pk=self.invoice.pk).exists())
        self.assertTrue(InvoicePayment.objects.filter(pk=self.payment.pk).exists())
        self.assertEqual(FinancialDocument.objects.filter(pk__in=[row.pk for row in self.documents]).count(), 3)
        conflicting_retry = self.client.post(
            self.url,
            {"reason": "Different reason", "confirm_invoice_number": "INV-000001"},
            format="json",
            HTTP_IDEMPOTENCY_KEY="purge-1",
        )
        self.assertEqual(conflicting_retry.status_code, 409)

        with patch.object(storage, "delete", return_value=None) as delete_file:
            completed = self.client.post(self.url, self.payload, format="json", HTTP_IDEMPOTENCY_KEY="purge-2")
        self.assertEqual(completed.status_code, 200, completed.data)
        self.assertEqual(completed.data["status"], FinancialPurgeRequest.Status.COMPLETED)
        self.assertEqual(delete_file.call_count, 3)
        self.assertFalse(Invoice.objects.filter(pk=self.invoice.pk).exists())
        self.assertFalse(InvoiceLineItem.objects.filter(pk=self.line.pk).exists())
        self.assertFalse(InvoicePayment.objects.filter(pk=self.payment.pk).exists())
        self.assertFalse(CreditNote.objects.filter(pk=self.credit.pk).exists())
        self.assertFalse(InvoiceRefund.objects.filter(pk=self.refund.pk).exists())
        self.assertFalse(FinancialDocument.objects.filter(pk__in=[row.pk for row in self.documents]).exists())
        self.assertTrue(FinanceMutation.objects.filter(pk=self.old_mutation.pk).exists())
        self.assertTrue(FinancialAuditEvent.objects.filter(pk=self.old_audit.pk).exists())
        self.assertTrue(FinancialAuditEvent.objects.filter(tenant=self.shop, action="INVOICE_BUNDLE_PURGED", object_id=self.invoice.pk).exists())
        self.invoice_sequence.refresh_from_db()
        self.credit_sequence.refresh_from_db()
        self.assertEqual(self.invoice_sequence.last_number, 4)
        self.assertEqual(self.credit_sequence.last_number, 2)

        replay = self.client.post(self.url, self.payload, format="json", HTTP_IDEMPOTENCY_KEY="purge-3")
        self.assertEqual(replay.status_code, 200, replay.data)
        self.assertEqual(replay.data["id"], completed.data["id"])

    def test_non_main_supplier_user_cannot_purge_or_read_for_purge(self):
        self.client.force_authenticate(self.staff)
        invoices_url = f"/api/v1/shops/{self.shop.pk}/works/{self.work.pk}/invoices/"
        self.assertEqual(self.client.get(invoices_url).status_code, 403)
        response = self.client.post(self.url, self.payload, format="json", HTTP_IDEMPOTENCY_KEY="purge-staff")
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Invoice.objects.filter(pk=self.invoice.pk).exists())
        self.assertFalse(FinancialPurgeRequest.objects.filter(tenant=self.shop).exists())

    def test_purge_requires_matching_invoice_number_and_reason(self):
        self.client.force_authenticate(self.admin)
        wrong = self.client.post(
            self.url, {"reason": "Duplicate", "confirm_invoice_number": "INV-000002"},
            format="json", HTTP_IDEMPOTENCY_KEY="purge-wrong-number",
        )
        self.assertEqual(wrong.status_code, 400)
        self.assertTrue(Invoice.objects.filter(pk=self.invoice.pk).exists())
        missing_reason = self.client.post(
            self.url, {"confirm_invoice_number": "INV-000001"},
            format="json", HTTP_IDEMPOTENCY_KEY="purge-no-reason",
        )
        self.assertEqual(missing_reason.status_code, 400)
