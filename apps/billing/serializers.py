from collections.abc import Mapping

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.billing.models import CreditNote, FinancialPurgeRequest, Invoice, InvoiceLineItem, InvoicePayment, InvoiceRefund
from apps.catalog.models import LOCALES


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if isinstance(data, Mapping):
            unknown = set(data) - set(self.fields)
            if unknown:
                raise serializers.ValidationError(
                    {key: "Unknown field." for key in unknown}
                )
        return super().to_internal_value(data)


class InvoiceLineInputSerializer(StrictSerializer):
    description = serializers.CharField(max_length=240, trim_whitespace=True)
    quantity = serializers.DecimalField(
        max_digits=12, decimal_places=3, required=False, default=1
    )
    unit_price = serializers.DecimalField(max_digits=18, decimal_places=4)

    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than zero.")
        return value

    def validate_description(self, value):
        if not value:
            raise serializers.ValidationError("Description must not be blank.")
        return value


class InvoiceCreateSerializer(StrictSerializer):
    mode = serializers.ChoiceField(choices=("AUTO", "MANUAL"))
    lines = InvoiceLineInputSerializer(many=True, required=False, allow_empty=True)
    discount_type = serializers.ChoiceField(choices=Invoice.DiscountType.choices, required=False, default=Invoice.DiscountType.NONE)
    discount_value = serializers.DecimalField(max_digits=18, decimal_places=6, required=False, default=0)
    tax_rate = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True, default=None)


class InvoicePaymentInputSerializer(StrictSerializer):
    amount = serializers.DecimalField(max_digits=18, decimal_places=4)


class InvoiceLineSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceLineItem
        fields = (
            "id",
            "source",
            "description",
            "quantity",
            "unit_price",
            "line_total",
            "discount_amount",
            "tax_amount",
        )
        read_only_fields = fields


class InvoiceRefundSerializer(serializers.ModelSerializer):
    payment_id = serializers.UUIDField(read_only=True)
    credit_note_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = InvoiceRefund
        fields = ("id", "payment_id", "credit_note_id", "amount", "refunded_at", "recorded_by_id")
        read_only_fields = fields


class InvoicePaymentSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    amount = serializers.DecimalField(max_digits=18, decimal_places=4, read_only=True)
    received_at = serializers.DateTimeField(read_only=True)
    recorded_by_id = serializers.UUIDField(read_only=True)
    refunds = serializers.SerializerMethodField()

    @extend_schema_field(InvoiceRefundSerializer(many=True))
    def get_refunds(self, obj):
        return InvoiceRefundSerializer(obj.refunds.all(), many=True).data


class InvoiceAdjustmentsSerializer(StrictSerializer):
    discount_type = serializers.ChoiceField(choices=Invoice.DiscountType.choices)
    discount_value = serializers.DecimalField(max_digits=18, decimal_places=6, required=False, default=0)
    tax_rate = serializers.DecimalField(max_digits=9, decimal_places=6, required=False, allow_null=True, default=None)


class VoidInvoiceSerializer(StrictSerializer):
    reason = serializers.CharField(max_length=500, trim_whitespace=True)


class CreditNoteCreateSerializer(StrictSerializer):
    amount = serializers.DecimalField(max_digits=20, decimal_places=4)
    reason = serializers.CharField(max_length=500, trim_whitespace=True)


class InvoiceRefundInputSerializer(StrictSerializer):
    payment_id = serializers.UUIDField()
    amount = serializers.DecimalField(max_digits=18, decimal_places=4)


class FinancialDocumentRequestSerializer(StrictSerializer):
    locale = serializers.ChoiceField(choices=LOCALES, required=False)


class FinancialDocumentSerializer(serializers.Serializer):
    id = serializers.UUIDField(read_only=True)
    kind = serializers.CharField(read_only=True)
    locale = serializers.CharField(read_only=True)
    sha256 = serializers.CharField(read_only=True)
    generated_at = serializers.DateTimeField(read_only=True)


class InvoicePurgeRequestSerializer(StrictSerializer):
    reason = serializers.CharField(min_length=1, max_length=500, trim_whitespace=True)
    confirm_invoice_number = serializers.CharField(min_length=1, max_length=32, trim_whitespace=True)


class FinancialPurgeRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialPurgeRequest
        fields = ("id", "invoice_id", "invoice_number", "status", "attempt_count", "failure_code", "completed_at")
        read_only_fields = fields


class CreditNoteSerializer(serializers.ModelSerializer):
    invoice_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = CreditNote
        fields = ("id", "invoice_id", "credit_number", "status", "reason", "amount", "issued_at", "issued_by_id", "created_at")
        read_only_fields = fields


class InvoiceSerializer(serializers.ModelSerializer):
    work_id = serializers.UUIDField(read_only=True)
    client_id = serializers.UUIDField(read_only=True)
    related_person_id = serializers.UUIDField(read_only=True, allow_null=True)
    subtotal = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)
    amount_paid = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)
    balance = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)
    discount_total = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)
    tax_total = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)
    total_amount = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)
    amount_refunded = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)
    credited_total = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)
    refund_due = serializers.DecimalField(max_digits=20, decimal_places=4, read_only=True)
    items = InvoiceLineSerializer(many=True, read_only=True)
    payments = InvoicePaymentSerializer(many=True, read_only=True)
    credit_notes = CreditNoteSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = (
            "id",
            "work_id",
            "client_id",
            "related_person_id",
            "currency",
            "status",
            "invoice_number",
            "subtotal",
            "discount_type",
            "discount_value",
            "discount_total",
            "tax_rate",
            "tax_total",
            "total_amount",
            "amount_paid",
            "amount_refunded",
            "credited_total",
            "balance",
            "refund_due",
            "items",
            "payments",
            "credit_notes",
            "issued_at",
            "issued_by_id",
            "voided_at",
            "voided_by_id",
            "void_reason",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields
