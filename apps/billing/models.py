from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from backend.core.models import TimeStampedUUIDModel
from apps.catalog.models import LOCALES
from apps.catalog.storage import PrivateReferenceStorage


class Invoice(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ISSUED = "ISSUED", "Issued"
        VOID = "VOID", "Void"

    class DiscountType(models.TextChoices):
        NONE = "NONE", "None"
        FIXED = "FIXED", "Fixed amount"
        PERCENT = "PERCENT", "Percentage"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="invoices")
    work = models.ForeignKey("works.WorkOrder", on_delete=models.PROTECT, related_name="invoices")
    client = models.ForeignKey("clients.Client", on_delete=models.PROTECT, related_name="invoices")
    related_person = models.ForeignKey(
        "clients.RelatedPerson", null=True, blank=True, on_delete=models.PROTECT, related_name="invoices"
    )
    currency = models.CharField(max_length=3)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.DRAFT)
    invoice_number = models.CharField(max_length=32, null=True, blank=True)
    discount_type = models.CharField(max_length=8, choices=DiscountType.choices, default=DiscountType.NONE)
    discount_value = models.DecimalField(max_digits=18, decimal_places=6, default=Decimal("0"))
    tax_rate = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    issued_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.PROTECT, related_name="issued_invoices"
    )
    voided_at = models.DateTimeField(null=True, blank=True)
    voided_by = models.ForeignKey(
        "accounts.User", null=True, blank=True, on_delete=models.PROTECT, related_name="voided_invoices"
    )
    void_reason = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=("tenant", "status", "created_at"), name="bill_shop_status_created_idx"),
            models.Index(fields=("tenant", "work", "created_at"), name="bill_shop_work_created_idx"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(status__in=("DRAFT", "ISSUED", "VOID")), name="bill_invoice_status_valid"),
            models.CheckConstraint(
                condition=(
                    Q(status="DRAFT", issued_at__isnull=True, issued_by__isnull=True, invoice_number__isnull=True,
                      voided_at__isnull=True, voided_by__isnull=True, void_reason="")
                    | Q(status="ISSUED", issued_at__isnull=False, issued_by__isnull=False, invoice_number__isnull=False,
                       voided_at__isnull=True, voided_by__isnull=True, void_reason="")
                    | Q(status="VOID", issued_at__isnull=False, issued_by__isnull=False, invoice_number__isnull=False,
                       voided_at__isnull=False, voided_by__isnull=False)
                ),
                name="bill_invoice_issue_pair",
            ),
            models.CheckConstraint(condition=Q(discount_value__gte=0), name="bill_discount_nonnegative"),
            models.CheckConstraint(condition=Q(tax_rate__isnull=True) | Q(tax_rate__gte=0), name="bill_tax_nonnegative"),
            models.UniqueConstraint(fields=("tenant", "invoice_number"), condition=Q(invoice_number__isnull=False), name="bill_shop_invoice_number_uniq"),
        ]

    def _calculated_amounts(self):
        from apps.billing.calculations import calculate_invoice_lines

        return calculate_invoice_lines(self, list(self.items.all()))

    @property
    def subtotal(self):
        return sum((item.line_total for item in self.items.all()), Decimal("0"))

    @property
    def discount_total(self):
        if self.status == self.Status.DRAFT:
            return sum((row["discount_amount"] for row in self._calculated_amounts()), Decimal("0"))
        return sum((item.discount_amount for item in self.items.all()), Decimal("0"))

    @property
    def tax_total(self):
        if self.status == self.Status.DRAFT:
            return sum((row["tax_amount"] for row in self._calculated_amounts()), Decimal("0"))
        return sum((item.tax_amount for item in self.items.all()), Decimal("0"))

    @property
    def total_amount(self):
        return self.subtotal - self.discount_total + self.tax_total

    @property
    def amount_paid(self):
        return sum((payment.amount for payment in self.payments.all()), Decimal("0"))

    @property
    def amount_refunded(self):
        return sum(
            (refund.amount for payment in self.payments.all() for refund in payment.refunds.all()),
            Decimal("0"),
        )

    @property
    def credited_total(self):
        return sum(
            (note.amount for note in self.credit_notes.all() if note.status == CreditNote.Status.ISSUED),
            Decimal("0"),
        )

    @property
    def balance(self):
        if self.status == self.Status.VOID:
            return Decimal("0")
        return self.total_amount - self.credited_total - self.amount_paid + self.amount_refunded

    @property
    def refund_due(self):
        return max(-self.balance, Decimal("0"))

    def save(self, *args, **kwargs):
        if not self._state.adding:
            original = type(self).objects.get(pk=self.pk)
            update_fields = set(kwargs.get("update_fields") or ())
            changed = {
                field.name
                for field in self._meta.concrete_fields
                if field.name != "updated_at" and getattr(original, field.attname) != getattr(self, field.attname)
            }
            if original.status == self.Status.ISSUED:
                permitted = {"status", "voided_at", "voided_by", "void_reason", "updated_by", "updated_at"}
                if self.status != self.Status.VOID or changed - permitted or (update_fields and update_fields - permitted):
                    raise ValidationError("Issued invoices are immutable except for a permitted void.")
            elif original.status == self.Status.VOID and (changed or (update_fields - {"updated_at"})):
                raise ValidationError("Voided invoices are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status != self.Status.DRAFT or self.payments.exists() or self.credit_notes.exists():
            raise ValidationError("Only a Draft invoice without financial records can be deleted.")
        return super().delete(*args, **kwargs)


class InvoiceLineItem(TimeStampedUUIDModel):
    class Source(models.TextChoices):
        DESIGN_SNAPSHOT = "DESIGN_SNAPSHOT", "Design price snapshot"
        MANUAL = "MANUAL", "Manual"

    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="items")
    source = models.CharField(max_length=20, choices=Source.choices)
    description = models.CharField(max_length=240)
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("1"))
    unit_price = models.DecimalField(max_digits=18, decimal_places=4)
    line_total = models.DecimalField(max_digits=20, decimal_places=4)
    discount_amount = models.DecimalField(max_digits=20, decimal_places=4, default=Decimal("0"))
    tax_amount = models.DecimalField(max_digits=20, decimal_places=4, default=Decimal("0"))

    class Meta:
        ordering = ("created_at", "id")
        constraints = [
            models.CheckConstraint(condition=Q(quantity__gt=0), name="bill_line_quantity_positive"),
            models.CheckConstraint(condition=Q(unit_price__gte=0), name="bill_line_unit_price_nonnegative"),
            models.CheckConstraint(condition=Q(line_total__gte=0), name="bill_line_total_nonnegative"),
            models.CheckConstraint(condition=Q(discount_amount__gte=0), name="bill_line_discount_nonnegative"),
            models.CheckConstraint(condition=Q(tax_amount__gte=0), name="bill_line_tax_nonnegative"),
            models.CheckConstraint(condition=Q(source__in=("DESIGN_SNAPSHOT", "MANUAL")), name="bill_line_source_valid"),
        ]

    def save(self, *args, **kwargs):
        if self.invoice_id and not self._state.adding and Invoice.objects.filter(pk=self.invoice_id).exclude(status=Invoice.Status.DRAFT).exists():
            raise ValidationError("Issued invoice lines are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if Invoice.objects.filter(pk=self.invoice_id).exclude(status=Invoice.Status.DRAFT).exists():
            raise ValidationError("Issued invoice lines are immutable.")
        return super().delete(*args, **kwargs)


class InvoicePayment(TimeStampedUUIDModel):
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=18, decimal_places=4)
    received_at = models.DateTimeField()
    recorded_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="recorded_invoice_payments")

    class Meta:
        ordering = ("received_at", "id")
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name="bill_payment_amount_positive")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Invoice payments are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Invoice payments are append-only.")


class ShopFinancialSequence(TimeStampedUUIDModel):
    class Kind(models.TextChoices):
        INVOICE = "INVOICE", "Invoice"
        CREDIT_NOTE = "CREDIT_NOTE", "Credit note"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="financial_sequences")
    kind = models.CharField(max_length=12, choices=Kind.choices)
    last_number = models.PositiveBigIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("tenant", "kind"), name="bill_shop_sequence_kind_uniq"),
            models.CheckConstraint(condition=Q(kind__in=("INVOICE", "CREDIT_NOTE")), name="bill_sequence_kind_valid"),
        ]


class CreditNote(TimeStampedUUIDModel):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        ISSUED = "ISSUED", "Issued"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="credit_notes")
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="credit_notes")
    credit_number = models.CharField(max_length=32, null=True, blank=True)
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.DRAFT)
    reason = models.CharField(max_length=500)
    amount = models.DecimalField(max_digits=20, decimal_places=4)
    issued_at = models.DateTimeField(null=True, blank=True)
    issued_by = models.ForeignKey("accounts.User", null=True, blank=True, on_delete=models.PROTECT, related_name="issued_credit_notes")

    class Meta:
        ordering = ("created_at", "id")
        constraints = [
            models.CheckConstraint(condition=Q(status__in=("DRAFT", "ISSUED")), name="bill_credit_status_valid"),
            models.CheckConstraint(condition=Q(amount__gt=0), name="bill_credit_amount_positive"),
            models.CheckConstraint(
                condition=(Q(status="DRAFT", issued_at__isnull=True, issued_by__isnull=True, credit_number__isnull=True)
                           | Q(status="ISSUED", issued_at__isnull=False, issued_by__isnull=False, credit_number__isnull=False)),
                name="bill_credit_issue_pair",
            ),
            models.UniqueConstraint(fields=("tenant", "credit_number"), condition=Q(credit_number__isnull=False), name="bill_shop_credit_number_uniq"),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding and type(self).objects.filter(pk=self.pk, status=self.Status.ISSUED).exists():
            raise ValidationError("Issued credit notes are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.status != self.Status.DRAFT or self.refunds.exists():
            raise ValidationError("Only a Draft credit note without refund records can be deleted.")
        return super().delete(*args, **kwargs)


class InvoiceRefund(TimeStampedUUIDModel):
    payment = models.ForeignKey(InvoicePayment, on_delete=models.PROTECT, related_name="refunds")
    credit_note = models.ForeignKey(CreditNote, on_delete=models.PROTECT, related_name="refunds")
    amount = models.DecimalField(max_digits=18, decimal_places=4)
    refunded_at = models.DateTimeField()
    recorded_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="recorded_invoice_refunds")

    class Meta:
        ordering = ("refunded_at", "id")
        constraints = [models.CheckConstraint(condition=Q(amount__gt=0), name="bill_refund_amount_positive")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Refund records are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Refund records are append-only.")


class FinanceMutation(TimeStampedUUIDModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="finance_mutations")
    actor = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="finance_mutations")
    key = models.CharField(max_length=128)
    operation = models.CharField(max_length=32)
    request_hash = models.CharField(max_length=64)
    resource_type = models.CharField(max_length=32)
    resource_id = models.UUIDField()
    response_snapshot = models.JSONField(null=True, blank=True)
    response_status = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=("tenant", "actor", "key"), name="bill_idem_shop_actor_key_uniq")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Financial idempotency records are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Financial idempotency records are immutable.")


class FinancialAuditEvent(TimeStampedUUIDModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="financial_audit_events")
    actor = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="financial_audit_events")
    action = models.CharField(max_length=40)
    object_type = models.CharField(max_length=32)
    object_id = models.UUIDField()
    request_id = models.CharField(max_length=128, blank=True)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)

    class Meta:
        ordering = ("created_at", "id")
        indexes = [models.Index(fields=("tenant", "created_at"), name="bill_audit_shop_created_idx")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Financial audit events are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Financial audit events are append-only.")


class FinancialDocument(TimeStampedUUIDModel):
    class Kind(models.TextChoices):
        INVOICE = "INVOICE", "Invoice"
        RECEIPT = "RECEIPT", "Receipt"
        CREDIT_NOTE = "CREDIT_NOTE", "Credit note"

    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.PROTECT, related_name="financial_documents")
    kind = models.CharField(max_length=16, choices=Kind.choices)
    invoice = models.ForeignKey(Invoice, null=True, blank=True, on_delete=models.PROTECT, related_name="documents")
    payment = models.ForeignKey(InvoicePayment, null=True, blank=True, on_delete=models.PROTECT, related_name="documents")
    credit_note = models.ForeignKey(CreditNote, null=True, blank=True, on_delete=models.PROTECT, related_name="documents")
    locale = models.CharField(max_length=5, choices=[(locale, locale) for locale in LOCALES])
    layout_version = models.PositiveSmallIntegerField(default=1, editable=False)
    file = models.FileField(storage=PrivateReferenceStorage(), upload_to="financial-documents/")
    sha256 = models.CharField(max_length=64)
    generated_by = models.ForeignKey("accounts.User", on_delete=models.PROTECT, related_name="financial_documents")
    generated_at = models.DateTimeField()

    class Meta:
        ordering = ("-generated_at", "-id")
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(kind="INVOICE", invoice__isnull=False, payment__isnull=True, credit_note__isnull=True)
                    | Q(kind="RECEIPT", invoice__isnull=True, payment__isnull=False, credit_note__isnull=True)
                    | Q(kind="CREDIT_NOTE", invoice__isnull=True, payment__isnull=True, credit_note__isnull=False)
                ),
                name="bill_document_kind_owner_valid",
            ),
            models.UniqueConstraint(
                fields=("invoice", "locale", "layout_version"),
                condition=Q(kind="INVOICE"),
                name="bill_doc_inv_layout_uniq",
            ),
            models.UniqueConstraint(
                fields=("payment", "locale", "layout_version"),
                condition=Q(kind="RECEIPT"),
                name="bill_doc_pay_layout_uniq",
            ),
            models.UniqueConstraint(
                fields=("credit_note", "locale", "layout_version"),
                condition=Q(kind="CREDIT_NOTE"),
                name="bill_doc_cn_layout_uniq",
            ),
        ]
        indexes = [models.Index(fields=("tenant", "generated_at"), name="bill_doc_shop_created_idx")]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Financial document metadata is immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Financial document history is retained.")


class FinancialPurgeRequest(TimeStampedUUIDModel):
    """Manual, retryable purge state for one invoice bundle.

    This row deliberately has no FK to the invoice: it remains as the minimal
    tombstone/idempotency record after the invoice bundle is removed.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        FAILED = "FAILED", "Failed"
        COMPLETED = "COMPLETED", "Completed"

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="financial_purge_requests"
    )
    invoice_id = models.UUIDField()
    invoice_number = models.CharField(max_length=32)
    requested_by = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="financial_purge_requests"
    )
    reason = models.CharField(max_length=500)
    request_hash = models.CharField(max_length=64)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    attempt_count = models.PositiveIntegerField(default=0)
    failure_code = models.CharField(max_length=64, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("tenant", "invoice_id"), name="bill_purge_shop_invoice_uniq"),
        ]
        indexes = [models.Index(fields=("tenant", "status"), name="bill_purge_shop_status_idx")]


class FinancialPurgeIdempotency(TimeStampedUUIDModel):
    """Append-only mapping from an idempotency key to a purge operation."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.PROTECT, related_name="financial_purge_idempotency"
    )
    actor = models.ForeignKey(
        "accounts.User", on_delete=models.PROTECT, related_name="financial_purge_idempotency"
    )
    key = models.CharField(max_length=128)
    request_hash = models.CharField(max_length=64)
    purge_request = models.ForeignKey(
        FinancialPurgeRequest, on_delete=models.PROTECT, related_name="idempotency_records"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("tenant", "actor", "key"), name="bill_purge_shop_actor_key_uniq"),
        ]

    def save(self, *args, **kwargs):
        if not self._state.adding:
            raise ValidationError("Financial purge idempotency records are immutable.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Financial purge idempotency records are immutable.")
