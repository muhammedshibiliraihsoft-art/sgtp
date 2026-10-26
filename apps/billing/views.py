from decimal import Decimal
from django.http import FileResponse

from django.db.models import DecimalField, F, OuterRef, Subquery, Sum, Value
from django.db.models.functions import Coalesce
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema

from apps.accounts.permissions import PasswordChangeGate
from apps.accounts.preferences import resolve_locale
from apps.billing.models import CreditNote, FinancialDocument, FinancialPurgeRequest, Invoice, InvoiceLineItem, InvoicePayment, InvoiceRefund
from apps.billing.idempotency import mutation_response
from apps.billing.serializers import (
    CreditNoteCreateSerializer,
    CreditNoteSerializer,
    InvoiceAdjustmentsSerializer,
    InvoiceCreateSerializer,
    InvoiceLineInputSerializer,
    InvoiceLineSerializer,
    InvoicePaymentInputSerializer,
    InvoicePaymentSerializer,
    FinancialDocumentRequestSerializer,
    FinancialDocumentSerializer,
    InvoiceRefundInputSerializer,
    InvoiceRefundSerializer,
    InvoiceSerializer,
    InvoicePurgeRequestSerializer,
    FinancialPurgeRequestSerializer,
    VoidInvoiceSerializer,
)
from apps.billing.services import (
    add_invoice_line,
    create_credit_note,
    create_invoice,
    delete_invoice_line,
    delete_draft_invoice,
    delete_draft_credit_note,
    issue_invoice,
    issue_credit_note,
    record_invoice_payment,
    record_invoice_refund,
    generate_credit_note_document,
    generate_invoice_document,
    generate_payment_receipt,
    set_invoice_adjustments,
    update_invoice_line,
    void_invoice,
    purge_invoice_bundle,
)
from apps.tenants.context_views import ShopContextMixin
from apps.tenants.financial_access import IsShopFinancialUser
from apps.tenants.financial_access import has_financial_access
from apps.tenants.policy import ShopRolePolicy
from apps.works.models import WorkOrder


def _write_options(request):
    key = request.headers.get("Idempotency-Key", "").strip()
    if not key:
        from rest_framework.exceptions import ValidationError

        raise ValidationError({"Idempotency-Key": "This header is required for financial writes."})
    if len(key) > 128:
        from rest_framework.exceptions import ValidationError

        raise ValidationError({"Idempotency-Key": "The key must not exceed 128 characters."})
    return {"idempotency_key": key, "request_id": request.headers.get("X-Request-ID", "")[:128]}


def _document_locale(request, validated_data):
    return validated_data.get("locale") or resolve_locale(
        request.user.preferred_locale,
        authorized_shop_locale=request.shop_context.shop.default_locale,
    )


class BillingPagination(PageNumberPagination):
    page_size = 20


class BillingBase(ShopContextMixin, APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate, IsShopFinancialUser)

    def invoices(self):
        return Invoice.objects.filter(
            tenant=self.request.shop_context.shop
        ).select_related("work", "client", "related_person", "issued_by").prefetch_related(
            "items", "payments", "credit_notes", "payments__refunds"
        )


class IsFinancialHistoryReaderOrShopFinancialUser(IsShopFinancialUser):
    """Allow Main Supplier Admins to inspect the selected Shop's invoices for purge review."""

    def has_permission(self, request, view):
        if request.method == "GET" and ShopRolePolicy.is_main_supplier_admin(request.user):
            return True
        context = getattr(request, "shop_context", None)
        return bool(context and has_financial_access(context.membership))


class IsMainSupplierAdmin(IsAuthenticated):
    message = "Main Supplier Admin access required."

    def has_permission(self, request, view):
        return ShopRolePolicy.is_main_supplier_admin(request.user)


class WorkInvoiceListCreateView(BillingBase):
    @extend_schema(responses=InvoiceSerializer(many=True), operation_id="work_invoice_list")
    def get(self, request, shop_id, work_id):
        work = get_object_or_404(
            WorkOrder.objects.filter(tenant=request.shop_context.shop), pk=work_id
        )
        invoices = self.invoices().filter(work=work).order_by("created_at", "id")
        page = BillingPagination()
        rows = page.paginate_queryset(invoices, request, view=self)
        return page.get_paginated_response(InvoiceSerializer(rows, many=True).data)

    @extend_schema(request=InvoiceCreateSerializer, responses={201: InvoiceSerializer})
    def post(self, request, shop_id, work_id):
        data = InvoiceCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        invoice = create_invoice(
            context=request.shop_context,
            actor=request.user,
            work_id=work_id,
            mode=data.validated_data["mode"],
            lines=data.validated_data.get("lines", []),
            discount_type=data.validated_data["discount_type"],
            discount_value=data.validated_data["discount_value"],
            tax_rate=data.validated_data["tax_rate"],
            **_write_options(request),
        )
        if not hasattr(invoice, "pk"):
            return mutation_response(invoice, InvoiceSerializer, status.HTTP_201_CREATED)
        invoice = self.invoices().get(pk=invoice.pk)
        return mutation_response(invoice, InvoiceSerializer, status.HTTP_201_CREATED)


class InvoiceDetailView(BillingBase):
    @extend_schema(responses=InvoiceSerializer, operation_id="invoice_retrieve")
    def get(self, request, shop_id, invoice_id):
        invoice = get_object_or_404(self.invoices(), pk=invoice_id)
        return Response(InvoiceSerializer(invoice).data)

    @extend_schema(responses={status.HTTP_204_NO_CONTENT: None}, operation_id="invoice_draft_delete")
    def delete(self, request, shop_id, invoice_id):
        result = delete_draft_invoice(context=request.shop_context, actor=request.user, invoice_id=invoice_id, **_write_options(request))
        return mutation_response(result, None, status.HTTP_204_NO_CONTENT)


class InvoicePurgeView(ShopContextMixin, APIView):
    permission_classes = (IsAuthenticated, PasswordChangeGate)

    def get_permissions(self):
        return [permission() for permission in (IsAuthenticated, PasswordChangeGate, IsMainSupplierAdmin)]

    @extend_schema(request=InvoicePurgeRequestSerializer, responses={200: FinancialPurgeRequestSerializer, 202: FinancialPurgeRequestSerializer})
    def post(self, request, shop_id, invoice_id):
        data = InvoicePurgeRequestSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        operation = purge_invoice_bundle(
            context=request.shop_context,
            actor=request.user,
            invoice_id=invoice_id,
            reason=data.validated_data["reason"],
            confirm_invoice_number=data.validated_data["confirm_invoice_number"],
            **_write_options(request),
        )
        response_status = status.HTTP_200_OK if operation.status == "COMPLETED" else status.HTTP_202_ACCEPTED
        return Response(FinancialPurgeRequestSerializer(operation).data, status=response_status)


class InvoiceLineListCreateView(BillingBase):
    @extend_schema(request=InvoiceLineInputSerializer, responses={201: InvoiceLineSerializer})
    def post(self, request, shop_id, invoice_id):
        data = InvoiceLineInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        item = add_invoice_line(
            context=request.shop_context,
            actor=request.user,
            invoice_id=invoice_id,
            values=data.validated_data,
            **_write_options(request),
        )
        return mutation_response(item, InvoiceLineSerializer, status.HTTP_201_CREATED)


class InvoiceLineDetailView(BillingBase):
    serializer_class = InvoiceLineInputSerializer

    @extend_schema(request=InvoiceLineInputSerializer, responses=InvoiceLineSerializer)
    def patch(self, request, shop_id, invoice_id, item_id):
        data = InvoiceLineInputSerializer(data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        item = update_invoice_line(
            context=request.shop_context,
            actor=request.user,
            invoice_id=invoice_id,
            item_id=item_id,
            values=data.validated_data,
            **_write_options(request),
        )
        return mutation_response(item, InvoiceLineSerializer)

    def delete(self, request, shop_id, invoice_id, item_id):
        result = delete_invoice_line(
            context=request.shop_context,
            actor=request.user,
            invoice_id=invoice_id,
            item_id=item_id,
            **_write_options(request),
        )
        return mutation_response(result, None, status.HTTP_204_NO_CONTENT)


class InvoiceIssueView(BillingBase):
    @extend_schema(request=None, responses=InvoiceSerializer)
    def post(self, request, shop_id, invoice_id):
        invoice = issue_invoice(
            context=request.shop_context, actor=request.user, invoice_id=invoice_id, **_write_options(request)
        )
        if not hasattr(invoice, "pk"):
            return mutation_response(invoice, InvoiceSerializer)
        invoice = self.invoices().get(pk=invoice.pk)
        return mutation_response(invoice, InvoiceSerializer)


class InvoicePaymentListCreateView(BillingBase):
    @extend_schema(request=InvoicePaymentInputSerializer, responses={201: InvoicePaymentSerializer})
    def post(self, request, shop_id, invoice_id):
        data = InvoicePaymentInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        payment = record_invoice_payment(
            context=request.shop_context,
            actor=request.user,
            invoice_id=invoice_id,
            amount=data.validated_data["amount"],
            **_write_options(request),
        )
        return mutation_response(payment, InvoicePaymentSerializer, status.HTTP_201_CREATED)


class OutstandingInvoiceListView(BillingBase):
    @extend_schema(responses=InvoiceSerializer(many=True), operation_id="billing_outstanding_list")
    def get(self, request, shop_id):
        subtotal = (
            InvoiceLineItem.objects.filter(invoice_id=OuterRef("pk"))
            .values("invoice_id")
            .annotate(total=Sum("line_total"))
            .values("total")
        )
        line_discount = (
            InvoiceLineItem.objects.filter(invoice_id=OuterRef("pk"))
            .values("invoice_id")
            .annotate(total=Sum("discount_amount"))
            .values("total")
        )
        line_tax = (
            InvoiceLineItem.objects.filter(invoice_id=OuterRef("pk"))
            .values("invoice_id")
            .annotate(total=Sum("tax_amount"))
            .values("total")
        )
        paid = (
            InvoicePayment.objects.filter(invoice_id=OuterRef("pk"))
            .values("invoice_id")
            .annotate(total=Sum("amount"))
            .values("total")
        )
        credits = (
            CreditNote.objects.filter(invoice_id=OuterRef("pk"), status=CreditNote.Status.ISSUED)
            .values("invoice_id")
            .annotate(total=Sum("amount"))
            .values("total")
        )
        refunds = (
            InvoiceRefund.objects.filter(payment__invoice_id=OuterRef("pk"))
            .values("payment__invoice_id")
            .annotate(total=Sum("amount"))
            .values("total")
        )
        decimal_field = DecimalField(max_digits=20, decimal_places=4)
        zero = Value(Decimal("0"), output_field=decimal_field)
        invoices = (
            self.invoices()
            .filter(status=Invoice.Status.ISSUED)
            .annotate(
                subtotal_value=Coalesce(Subquery(subtotal, output_field=decimal_field), zero),
                discount_total_value=Coalesce(Subquery(line_discount, output_field=decimal_field), zero),
                tax_value=Coalesce(Subquery(line_tax, output_field=decimal_field), zero),
                paid_value=Coalesce(Subquery(paid, output_field=decimal_field), zero),
                credit_value=Coalesce(Subquery(credits, output_field=decimal_field), zero),
                refund_value=Coalesce(Subquery(refunds, output_field=decimal_field), zero),
            )
            .annotate(balance_value=F("subtotal_value") - F("discount_total_value") + F("tax_value") - F("paid_value") + F("refund_value") - F("credit_value"))
            .filter(balance_value__gt=zero)
            .order_by("created_at", "id")
        )
        page = BillingPagination()
        rows = page.paginate_queryset(invoices, request, view=self)
        return page.get_paginated_response(InvoiceSerializer(rows, many=True).data)


class InvoiceAdjustmentsView(BillingBase):
    @extend_schema(request=InvoiceAdjustmentsSerializer, responses=InvoiceSerializer)
    def patch(self, request, shop_id, invoice_id):
        data = InvoiceAdjustmentsSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        invoice = set_invoice_adjustments(context=request.shop_context, actor=request.user, invoice_id=invoice_id, **data.validated_data, **_write_options(request))
        if not hasattr(invoice, "pk"):
            return mutation_response(invoice, InvoiceSerializer)
        return mutation_response(self.invoices().get(pk=invoice.pk), InvoiceSerializer)


class InvoiceVoidView(BillingBase):
    @extend_schema(request=VoidInvoiceSerializer, responses=InvoiceSerializer)
    def post(self, request, shop_id, invoice_id):
        data = VoidInvoiceSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        invoice = void_invoice(context=request.shop_context, actor=request.user, invoice_id=invoice_id, reason=data.validated_data["reason"], **_write_options(request))
        if not hasattr(invoice, "pk"):
            return mutation_response(invoice, InvoiceSerializer)
        return mutation_response(self.invoices().get(pk=invoice.pk), InvoiceSerializer)


class InvoiceCreditNoteListCreateView(BillingBase):
    @extend_schema(responses=CreditNoteSerializer(many=True))
    def get(self, request, shop_id, invoice_id):
        invoice = get_object_or_404(self.invoices(), pk=invoice_id)
        return Response(CreditNoteSerializer(invoice.credit_notes.all(), many=True).data)

    @extend_schema(request=CreditNoteCreateSerializer, responses={201: CreditNoteSerializer})
    def post(self, request, shop_id, invoice_id):
        data = CreditNoteCreateSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        note = create_credit_note(context=request.shop_context, actor=request.user, invoice_id=invoice_id, **data.validated_data, **_write_options(request))
        return mutation_response(note, CreditNoteSerializer, status.HTTP_201_CREATED)


class CreditNoteIssueView(BillingBase):
    @extend_schema(request=None, responses=CreditNoteSerializer)
    def post(self, request, shop_id, credit_note_id):
        note = issue_credit_note(context=request.shop_context, actor=request.user, credit_note_id=credit_note_id, **_write_options(request))
        return mutation_response(note, CreditNoteSerializer)


class CreditNoteDetailView(BillingBase):
    @extend_schema(responses={status.HTTP_204_NO_CONTENT: None}, operation_id="credit_note_draft_delete")
    def delete(self, request, shop_id, credit_note_id):
        result = delete_draft_credit_note(context=request.shop_context, actor=request.user, credit_note_id=credit_note_id, **_write_options(request))
        return mutation_response(result, None, status.HTTP_204_NO_CONTENT)


class CreditNoteRefundListCreateView(BillingBase):
    @extend_schema(request=InvoiceRefundInputSerializer, responses={201: InvoiceRefundSerializer})
    def post(self, request, shop_id, credit_note_id):
        data = InvoiceRefundInputSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        refund = record_invoice_refund(context=request.shop_context, actor=request.user, credit_note_id=credit_note_id, **data.validated_data, **_write_options(request))
        return mutation_response(refund, InvoiceRefundSerializer, status.HTTP_201_CREATED)


class InvoiceDocumentCreateView(BillingBase):
    @extend_schema(request=FinancialDocumentRequestSerializer, responses=FinancialDocumentSerializer)
    def post(self, request, shop_id, invoice_id):
        data = FinancialDocumentRequestSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        document = generate_invoice_document(
            context=request.shop_context, actor=request.user, invoice_id=invoice_id,
            locale=_document_locale(request, data.validated_data),
        )
        return Response(FinancialDocumentSerializer(document).data, status=status.HTTP_200_OK)


class PaymentReceiptCreateView(BillingBase):
    @extend_schema(request=FinancialDocumentRequestSerializer, responses=FinancialDocumentSerializer)
    def post(self, request, shop_id, invoice_id, payment_id):
        data = FinancialDocumentRequestSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        document = generate_payment_receipt(
            context=request.shop_context, actor=request.user, invoice_id=invoice_id,
            payment_id=payment_id, locale=_document_locale(request, data.validated_data),
        )
        return Response(FinancialDocumentSerializer(document).data, status=status.HTTP_200_OK)


class CreditNoteDocumentCreateView(BillingBase):
    @extend_schema(request=FinancialDocumentRequestSerializer, responses=FinancialDocumentSerializer)
    def post(self, request, shop_id, credit_note_id):
        data = FinancialDocumentRequestSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        document = generate_credit_note_document(
            context=request.shop_context, actor=request.user, credit_note_id=credit_note_id,
            locale=_document_locale(request, data.validated_data),
        )
        return Response(FinancialDocumentSerializer(document).data, status=status.HTTP_200_OK)


class FinancialDocumentDownloadView(BillingBase):
    @extend_schema(responses={(status.HTTP_200_OK): OpenApiTypes.BINARY}, operation_id="financial_document_download")
    def get(self, request, shop_id, document_id):
        document = get_object_or_404(
            FinancialDocument.objects.filter(tenant=request.shop_context.shop), pk=document_id
        )
        if FinancialPurgeRequest.objects.filter(
            tenant=request.shop_context.shop,
            invoice_id__in=[document.invoice_id, document.payment.invoice_id if document.payment_id else None,
                            document.credit_note.invoice_id if document.credit_note_id else None],
            status__in=(FinancialPurgeRequest.Status.PENDING, FinancialPurgeRequest.Status.FAILED),
        ).exists():
            from rest_framework.exceptions import ValidationError

            raise ValidationError({"document": "This financial document is unavailable during a pending purge."})
        try:
            stream = document.file.open("rb")
        except (FileNotFoundError, OSError, ValueError):
            from rest_framework.exceptions import APIException

            raise APIException("The private financial document is unavailable.") from None
        response = FileResponse(
            stream, as_attachment=True,
            filename=f"{document.kind.lower()}-{document.pk}.pdf",
            content_type="application/pdf",
        )
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        return response


class BillingInvoiceListView(BillingBase):
    permission_classes = (IsAuthenticated, PasswordChangeGate, IsFinancialHistoryReaderOrShopFinancialUser)

    @extend_schema(responses=InvoiceSerializer(many=True), operation_id="billing_invoice_history")
    def get(self, request, shop_id):
        invoices = self.invoices()
        status_filter = request.query_params.get("status")
        if status_filter in Invoice.Status.values:
            invoices = invoices.filter(status=status_filter)
        elif status_filter:
            return Response({"status": ["Choose DRAFT, ISSUED, or VOID."]}, status=status.HTTP_400_BAD_REQUEST)
        start = request.query_params.get("from")
        end = request.query_params.get("to")
        if start:
            parsed_start = parse_date(start)
            if parsed_start is None:
                return Response({"from": ["Enter a valid ISO date."]}, status=status.HTTP_400_BAD_REQUEST)
            invoices = invoices.filter(issued_at__date__gte=parsed_start)
        if end:
            parsed_end = parse_date(end)
            if parsed_end is None:
                return Response({"to": ["Enter a valid ISO date."]}, status=status.HTTP_400_BAD_REQUEST)
            invoices = invoices.filter(issued_at__date__lte=parsed_end)
        work_id = request.query_params.get("work")
        if work_id:
            invoices = invoices.filter(work_id=work_id)
        page = BillingPagination()
        rows = page.paginate_queryset(invoices.order_by("-created_at", "-id"), request, view=self)
        return page.get_paginated_response(InvoiceSerializer(rows, many=True).data)
