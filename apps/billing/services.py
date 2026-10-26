import hashlib
import json
import logging
from decimal import Decimal

from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework.exceptions import APIException, NotFound, ValidationError

from apps.billing.calculations import calculate_invoice_lines
from apps.billing.idempotency import MutationReplay
from apps.billing.models import (
    CreditNote,
    FinanceMutation,
    FinancialAuditEvent,
    FinancialDocument,
    FinancialPurgeIdempotency,
    FinancialPurgeRequest,
    Invoice,
    InvoiceLineItem,
    InvoicePayment,
    InvoiceRefund,
    ShopFinancialSequence,
)
from apps.catalog.models import DesignVersionTranslation
from apps.catalog.models import LOCALES
from apps.billing.pdf import (
    FINANCIAL_PDF_LAYOUT_VERSION,
    credit_note_pdf,
    invoice_pdf,
    receipt_pdf,
)
from apps.tenants.currency import normalize_currency, validate_money_amount
from apps.tenants.financial_access import require_financial_access
from apps.tenants.models import Tenant
from apps.tenants.policy import ShopRolePolicy
from apps.works.models import WorkOrder


logger = logging.getLogger(__name__)


class IdempotencyConflict(APIException):
    status_code = 409
    default_detail = "This idempotency key was already used for a different request."
    default_code = "idempotency_conflict"


def _request_hash(operation, payload):
    canonical = json.dumps(
        {"operation": operation, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_idempotency_key(key):
    if not key:
        raise ValidationError({"Idempotency-Key": "This header is required for financial writes."})
    key = str(key)
    if len(key) > 128:
        raise ValidationError({"Idempotency-Key": "The key must not exceed 128 characters."})
    return key


def _existing_mutation(*, shop, actor, key, operation, payload):
    key = _normalize_idempotency_key(key)
    record = FinanceMutation.objects.select_for_update().filter(
        tenant=shop, actor=actor, key=key
    ).first()
    if record is None:
        return None
    digest = _request_hash(operation, payload)
    if record.operation != operation or record.request_hash != digest:
        raise IdempotencyConflict()
    if record.resource_type == "DELETED":
        return MutationReplay(None, record.response_status or 204)
    if record.response_snapshot is not None and record.response_status is not None:
        return MutationReplay(record.response_snapshot, record.response_status)
    models = {
        "Invoice": Invoice,
        "InvoiceLineItem": InvoiceLineItem,
        "InvoicePayment": InvoicePayment,
        "CreditNote": CreditNote,
        "InvoiceRefund": InvoiceRefund,
    }
    from apps.catalog.models import ShopDesignPrice

    models["ShopDesignPrice"] = ShopDesignPrice
    model = models.get(record.resource_type)
    if model is None:
        raise ValidationError("Stored idempotency result has an unsupported resource type.")
    try:
        resource = model.objects.get(pk=record.resource_id)
    except model.DoesNotExist:
        raise ValidationError("The original idempotent result is no longer available.") from None
    # Rows written before response snapshots were introduced retain the original
    # resource lookup behavior; no financial mutation history is rewritten.
    return resource


def _finish_mutation(*, shop, actor, key, operation, payload, resource):
    key = _normalize_idempotency_key(key)
    response_status = {
        "invoice.create": 201,
        "invoice.line.add": 201,
        "invoice.payment": 201,
        "credit_note.create": 201,
        "invoice.refund": 201,
        "invoice.line.delete": 204,
        "invoice.delete_draft": 204,
        "credit_note.delete_draft": 204,
    }.get(operation, 200)
    response_snapshot = None
    if resource is not None:
        from apps.billing.serializers import (
            CreditNoteSerializer,
            InvoiceLineSerializer,
            InvoicePaymentSerializer,
            InvoiceRefundSerializer,
            InvoiceSerializer,
        )
        from apps.catalog.serializers import ShopDesignPriceSerializer

        serializers = {
            "Invoice": InvoiceSerializer,
            "InvoiceLineItem": InvoiceLineSerializer,
            "InvoicePayment": InvoicePaymentSerializer,
            "CreditNote": CreditNoteSerializer,
            "InvoiceRefund": InvoiceRefundSerializer,
            "ShopDesignPrice": ShopDesignPriceSerializer,
        }
        serializer_class = serializers.get(type(resource).__name__)
        if serializer_class is None:
            raise ValidationError("Cannot store an idempotent response for this resource.")
        response_snapshot = json.loads(
            json.dumps(serializer_class(resource).data, cls=DjangoJSONEncoder)
        )
    FinanceMutation.objects.create(
        tenant=shop,
        actor=actor,
        key=key,
        operation=operation,
        request_hash=_request_hash(operation, payload),
        resource_type="DELETED" if resource is None else type(resource).__name__,
        resource_id=resource.pk if resource is not None else shop.pk,
        response_snapshot=response_snapshot,
        response_status=response_status,
        created_by=actor,
        updated_by=actor,
    )


def _audit(*, shop, actor, action, resource, before=None, after=None, request_id=""):
    FinancialAuditEvent.objects.create(
        tenant=shop,
        actor=actor,
        action=action,
        object_type=type(resource).__name__,
        object_id=resource.pk,
        request_id=(request_id or "")[:128],
        before=before or {},
        after=after or {},
        created_by=actor,
        updated_by=actor,
    )


def _currency_for_work(*, shop, work):
    existing = list(
        Invoice.objects.filter(tenant=shop, work=work)
        .values_list("currency", flat=True)
        .order_by("currency")
        .distinct()[:2]
    )
    if len(existing) > 1:
        raise ValidationError("Work has invoices in conflicting currencies.")
    if work.design_price_currency:
        if existing and existing[0] != work.design_price_currency:
            raise ValidationError("Work's Design price and existing invoice currencies differ.")
        return work.design_price_currency
    if existing:
        return existing[0]
    try:
        return normalize_currency(shop.default_currency)
    except ValueError:
        raise ValidationError(
            {"currency": "Set a valid Shop default currency before creating an invoice."}
        ) from None


def _create_line(*, invoice, actor, source, description, quantity, unit_price):
    if not description or not description.strip():
        raise ValidationError({"description": "Description must not be blank."})
    if quantity <= 0:
        raise ValidationError({"quantity": "Quantity must be greater than zero."})
    try:
        unit_price = validate_money_amount(unit_price, invoice.currency)
        line_total = validate_money_amount(quantity * unit_price, invoice.currency)
    except ValueError as error:
        raise ValidationError({"unit_price": str(error)}) from error
    return InvoiceLineItem.objects.create(
        invoice=invoice,
        source=source,
        description=description.strip(),
        quantity=quantity,
        unit_price=unit_price,
        line_total=line_total,
        created_by=actor,
        updated_by=actor,
    )


def _locked_shop_context(context, actor):
    shop = Tenant.objects.select_for_update().get(pk=context.shop.pk, is_active=True)
    require_financial_access(context=context, actor=actor, lock=True)
    return shop


def _locked_invoice(*, context, actor, invoice_id):
    shop = _locked_shop_context(context, actor)
    try:
        invoice = Invoice.objects.select_for_update().get(pk=invoice_id, tenant=shop)
    except (Invoice.DoesNotExist, ValueError, TypeError):
        raise NotFound() from None
    if FinancialPurgeRequest.objects.filter(
        tenant=shop,
        invoice_id=invoice.pk,
        status__in=(FinancialPurgeRequest.Status.PENDING, FinancialPurgeRequest.Status.FAILED),
    ).exists():
        raise ValidationError({"invoice": "A Super Admin purge is pending. Retry or complete that purge first."})
    return shop, invoice


def purge_invoice_bundle(*, context, actor, invoice_id, reason, confirm_invoice_number, idempotency_key, request_id=""):
    """Manually purge one invoice and all linked financial records.

    Private files are removed before database rows. A persisted request blocks
    subsequent invoice mutations while storage cleanup is pending; retrying is
    safe because storage deletion is idempotent for absent objects.
    """
    if not ShopRolePolicy.is_main_supplier_admin(actor):
        from rest_framework.exceptions import PermissionDenied

        raise PermissionDenied("Main Supplier Admin access required.")
    key = _normalize_idempotency_key(idempotency_key)
    reason = (reason or "").strip()
    if not reason or len(reason) > 500:
        raise ValidationError({"reason": "Provide a reason of 1 to 500 characters."})
    invoice_number = (confirm_invoice_number or "").strip()
    if not invoice_number:
        raise ValidationError({"confirm_invoice_number": "Enter the exact invoice number to confirm."})

    digest = _request_hash(
        "invoice.purge",
        {"invoice_id": str(invoice_id), "invoice_number": invoice_number, "reason": reason},
    )
    with transaction.atomic():
        shop = Tenant.objects.select_for_update().filter(pk=context.shop.pk, is_active=True).first()
        if shop is None:
            raise NotFound()
        key_record = FinancialPurgeIdempotency.objects.select_for_update().filter(
            tenant=shop, actor=actor, key=key
        ).select_related("purge_request").first()
        if key_record:
            if key_record.request_hash != digest:
                raise IdempotencyConflict()
            request = key_record.purge_request
            if request.status == FinancialPurgeRequest.Status.COMPLETED:
                return request
        # Invoice UUID remains addressable through the purge tombstone after the
        # source rows are removed, making retries and repeated requests idempotent.
        try:
            invoice = Invoice.objects.select_for_update().filter(tenant=shop, pk=invoice_id).first()
        except (ValueError, TypeError):
            invoice = None
        if invoice is None:
            if key_record:
                raise NotFound()
            request = FinancialPurgeRequest.objects.select_for_update().filter(
                tenant=shop, invoice_id=invoice_id,
                status=FinancialPurgeRequest.Status.COMPLETED, request_hash=digest,
            ).first()
            if request is None:
                raise NotFound()
            FinancialPurgeIdempotency.objects.create(
                tenant=shop, actor=actor, key=key, request_hash=digest, purge_request=request,
                created_by=actor, updated_by=actor,
            )
            return request
        if invoice.status == Invoice.Status.DRAFT:
            raise ValidationError({"invoice": "Draft invoices must use the existing draft-delete action."})
        if invoice.invoice_number != invoice_number:
            raise ValidationError({"confirm_invoice_number": "The invoice number does not match."})

        request = key_record.purge_request if key_record else FinancialPurgeRequest.objects.select_for_update().filter(
            tenant=shop, invoice_id=invoice.pk
        ).first()
        if request:
            if request.request_hash != digest:
                raise IdempotencyConflict()
            if request.status == FinancialPurgeRequest.Status.COMPLETED:
                if not key_record:
                    FinancialPurgeIdempotency.objects.create(
                        tenant=shop, actor=actor, key=key, request_hash=digest, purge_request=request,
                        created_by=actor, updated_by=actor,
                    )
                return request
            request.status = FinancialPurgeRequest.Status.PENDING
            request.failure_code = ""
            request.save(update_fields=("status", "failure_code", "updated_at"))
        else:
            request = FinancialPurgeRequest.objects.create(
                tenant=shop,
                invoice_id=invoice.pk,
                invoice_number=invoice.invoice_number,
                requested_by=actor,
                reason=reason,
                request_hash=digest,
                status=FinancialPurgeRequest.Status.PENDING,
                created_by=actor,
                updated_by=actor,
            )
        if not key_record:
            FinancialPurgeIdempotency.objects.create(
                tenant=shop, actor=actor, key=key, request_hash=digest, purge_request=request,
                created_by=actor, updated_by=actor,
            )
        document_filter = Q(invoice_id=invoice.pk) | Q(payment__invoice_id=invoice.pk) | Q(credit_note__invoice_id=invoice.pk)
        document_names = list(
            FinancialDocument.objects.filter(tenant=shop).filter(document_filter)
            .exclude(file="").values_list("file", flat=True)
        )
        request.attempt_count += 1
        request.save(update_fields=("attempt_count", "updated_at"))

    # No DB rows are removed unless every linked private object deletion returns
    # successfully. If one fails, retry will re-check the full immutable set.
    try:
        for name in document_names:
            FinancialDocument._meta.get_field("file").storage.delete(name)
    except Exception:
        logger.warning("Private financial purge storage operation failed", exc_info=True)
        FinancialPurgeRequest.objects.filter(
            pk=request.pk, status=FinancialPurgeRequest.Status.PENDING
        ).update(status=FinancialPurgeRequest.Status.FAILED, failure_code="PRIVATE_FILE_DELETE_FAILED")
        request.refresh_from_db()
        return request

    with transaction.atomic():
        shop = Tenant.objects.select_for_update().get(pk=shop.pk)
        request = FinancialPurgeRequest.objects.select_for_update().get(pk=request.pk, tenant=shop)
        if request.status == FinancialPurgeRequest.Status.COMPLETED:
            return request
        invoice = Invoice.objects.select_for_update().filter(pk=invoice_id, tenant=shop).first()
        if invoice is None:
            # A prior attempt may have committed deletion immediately before a
            # process interruption. The tombstone makes that outcome explicit.
            request.status = FinancialPurgeRequest.Status.COMPLETED
            request.failure_code = ""
            request.completed_at = timezone.now()
            request.save(update_fields=("status", "failure_code", "completed_at", "updated_at"))
            return request
        payment_ids = list(InvoicePayment.objects.filter(invoice=invoice).values_list("pk", flat=True))
        credit_note_ids = list(CreditNote.objects.filter(invoice=invoice).values_list("pk", flat=True))
        counts = {
            "documents": FinancialDocument.objects.filter(tenant=shop).filter(document_filter).count(),
            "refunds": InvoiceRefund.objects.filter(
                Q(payment__invoice=invoice) | Q(credit_note__invoice=invoice)
            ).count(),
            "credit_notes": len(credit_note_ids),
            "payments": len(payment_ids),
            "items": InvoiceLineItem.objects.filter(invoice=invoice).count(),
        }
        FinancialDocument.objects.filter(tenant=shop).filter(document_filter).delete()
        InvoiceRefund.objects.filter(
            Q(payment__invoice=invoice) | Q(credit_note__invoice=invoice)
        ).delete()
        CreditNote.objects.filter(pk__in=credit_note_ids, tenant=shop).delete()
        InvoicePayment.objects.filter(pk__in=payment_ids).delete()
        InvoiceLineItem.objects.filter(invoice=invoice).delete()
        purged_invoice_id = invoice.pk
        purged_status = invoice.status
        # QuerySet.delete intentionally bypasses the ordinary model guard: the
        # elevated, audited bundle-purge service owns this exceptional path.
        Invoice.objects.filter(pk=invoice.pk, tenant=shop).delete()
        FinancialAuditEvent.objects.create(
            tenant=shop,
            actor=actor,
            action="INVOICE_BUNDLE_PURGED",
            object_type="Invoice",
            object_id=purged_invoice_id,
            request_id=(request_id or "")[:128],
            before={"status": purged_status, "invoice_number": request.invoice_number},
            after={"reason": request.reason, "records_removed": counts},
            created_by=actor,
            updated_by=actor,
        )
        request.status = FinancialPurgeRequest.Status.COMPLETED
        request.failure_code = ""
        request.completed_at = timezone.now()
        request.save(update_fields=("status", "failure_code", "completed_at", "updated_at"))
    return request


def _apply_idempotency_result(*, shop, actor, key, operation, payload):
    result = _existing_mutation(
        shop=shop, actor=actor, key=key, operation=operation, payload=payload
    )
    return result


@transaction.atomic
def create_invoice(*, context, actor, work_id, mode, lines, idempotency_key, request_id="", discount_type=Invoice.DiscountType.NONE, discount_value=Decimal("0"), tax_rate=None):
    shop = _locked_shop_context(context, actor)
    payload = {"work_id": str(work_id), "mode": mode, "lines": lines, "discount_type": discount_type, "discount_value": discount_value, "tax_rate": tax_rate}
    previous = _apply_idempotency_result(
        shop=shop, actor=actor, key=idempotency_key, operation="invoice.create", payload=payload
    )
    if previous is not None:
        return previous
    try:
        work = WorkOrder.objects.select_for_update().get(pk=work_id, tenant=shop)
    except (WorkOrder.DoesNotExist, ValueError, TypeError):
        raise NotFound() from None
    try:
        currency = normalize_currency(_currency_for_work(shop=shop, work=work))
    except ValueError as error:
        raise ValidationError({"currency": "Work has no valid billing currency."}) from error
    try:
        discount_value = Decimal(discount_value or "0")
        tax_rate = None if tax_rate in (None, "") else Decimal(tax_rate)
        if not discount_value.is_finite() or discount_value < 0 or (tax_rate is not None and (not tax_rate.is_finite() or tax_rate < 0)):
            raise ValueError("Discount and tax values must be finite and non-negative.")
        if discount_type == Invoice.DiscountType.FIXED:
            discount_value = validate_money_amount(discount_value, currency)
        elif discount_type == Invoice.DiscountType.PERCENT and discount_value > 100:
            raise ValueError("Percentage discount cannot exceed 100%.")
        elif discount_type == Invoice.DiscountType.NONE:
            discount_value = Decimal("0")
    except (ValueError, TypeError) as error:
        raise ValidationError({"discount_value": str(error)}) from error
    invoice = Invoice.objects.create(
        tenant=shop, work=work, client=work.client, related_person=work.related_person,
        currency=currency, discount_type=discount_type, discount_value=discount_value,
        tax_rate=tax_rate, created_by=actor, updated_by=actor,
    )
    if mode == "AUTO":
        if work.design_price_amount is None or work.design_price_currency is None:
            raise ValidationError(
                {"mode": "This Work has no Design price snapshot; use manual invoice mode."}
            )
        translation = DesignVersionTranslation.objects.filter(
            version=work.design_version, locale="en"
        ).first()
        _create_line(
            invoice=invoice, actor=actor, source=InvoiceLineItem.Source.DESIGN_SNAPSHOT,
            description=translation.name if translation else "Design", quantity=Decimal("1"),
            unit_price=work.design_price_amount,
        )
    for line in lines:
        _create_line(
            invoice=invoice, actor=actor, source=InvoiceLineItem.Source.MANUAL,
            description=line["description"], quantity=line.get("quantity", Decimal("1")),
            unit_price=line["unit_price"],
        )
    try:
        calculate_invoice_lines(invoice, list(invoice.items.all()))
    except ValueError as error:
        raise ValidationError({"discount_value": str(error)}) from error
    _audit(shop=shop, actor=actor, action="INVOICE_CREATED", resource=invoice,
           after={"status": invoice.status, "currency": invoice.currency, "mode": mode}, request_id=request_id)
    _finish_mutation(shop=shop, actor=actor, key=idempotency_key, operation="invoice.create", payload=payload, resource=invoice)
    return invoice


@transaction.atomic
def add_invoice_line(*, context, actor, invoice_id, values, idempotency_key, request_id=""):
    shop, invoice = _locked_invoice(context=context, actor=actor, invoice_id=invoice_id)
    payload = {"invoice_id": str(invoice.pk), "values": values}
    previous = _apply_idempotency_result(shop=shop, actor=actor, key=idempotency_key, operation="invoice.line.add", payload=payload)
    if previous is not None:
        return previous
    if invoice.status != Invoice.Status.DRAFT:
        raise ValidationError("Only Draft invoices can be changed.")
    item = _create_line(invoice=invoice, actor=actor, source=InvoiceLineItem.Source.MANUAL,
                        description=values["description"], quantity=values.get("quantity", Decimal("1")),
                        unit_price=values["unit_price"])
    _audit(shop=shop, actor=actor, action="INVOICE_LINE_ADDED", resource=invoice,
           after={"line_id": str(item.pk), "description": item.description}, request_id=request_id)
    _finish_mutation(shop=shop, actor=actor, key=idempotency_key, operation="invoice.line.add", payload=payload, resource=item)
    return item


@transaction.atomic
def update_invoice_line(*, context, actor, invoice_id, item_id, values, idempotency_key, request_id=""):
    shop, invoice = _locked_invoice(context=context, actor=actor, invoice_id=invoice_id)
    payload = {"invoice_id": str(invoice.pk), "item_id": str(item_id), "values": values}
    previous = _apply_idempotency_result(shop=shop, actor=actor, key=idempotency_key, operation="invoice.line.update", payload=payload)
    if previous is not None:
        return previous
    if invoice.status != Invoice.Status.DRAFT:
        raise ValidationError("Only Draft invoices can be changed.")
    try:
        item = InvoiceLineItem.objects.select_for_update().get(pk=item_id, invoice=invoice, source=InvoiceLineItem.Source.MANUAL)
    except (InvoiceLineItem.DoesNotExist, ValueError, TypeError):
        raise NotFound() from None
    before = {"description": item.description, "quantity": str(item.quantity), "unit_price": str(item.unit_price)}
    description = values.get("description", item.description)
    quantity = values.get("quantity", item.quantity)
    unit_price = values.get("unit_price", item.unit_price)
    if not description.strip() or quantity <= 0:
        raise ValidationError("Description and quantity must be valid.")
    try:
        unit_price = validate_money_amount(unit_price, invoice.currency)
        line_total = validate_money_amount(quantity * unit_price, invoice.currency)
    except ValueError as error:
        raise ValidationError({"unit_price": str(error)}) from error
    item.description, item.quantity, item.unit_price, item.line_total, item.updated_by = description.strip(), quantity, unit_price, line_total, actor
    item.save(update_fields=("description", "quantity", "unit_price", "line_total", "updated_by", "updated_at"))
    _audit(shop=shop, actor=actor, action="INVOICE_LINE_UPDATED", resource=invoice, before=before,
           after={"line_id": str(item.pk), "description": item.description, "quantity": str(item.quantity), "unit_price": str(item.unit_price)}, request_id=request_id)
    _finish_mutation(shop=shop, actor=actor, key=idempotency_key, operation="invoice.line.update", payload=payload, resource=item)
    return item


@transaction.atomic
def delete_invoice_line(*, context, actor, invoice_id, item_id, idempotency_key, request_id=""):
    shop, invoice = _locked_invoice(context=context, actor=actor, invoice_id=invoice_id)
    payload = {"invoice_id": str(invoice.pk), "item_id": str(item_id)}
    previous = _apply_idempotency_result(shop=shop, actor=actor, key=idempotency_key, operation="invoice.line.delete", payload=payload)
    if previous is not None:
        return
    if invoice.status != Invoice.Status.DRAFT:
        raise ValidationError("Only Draft invoices can be changed.")
    try:
        item = InvoiceLineItem.objects.select_for_update().get(pk=item_id, invoice=invoice)
    except (InvoiceLineItem.DoesNotExist, ValueError, TypeError):
        raise NotFound() from None
    if item.source != InvoiceLineItem.Source.MANUAL:
        raise ValidationError("Design snapshot lines cannot be removed from this invoice.")
    before = {"line_id": str(item.pk), "description": item.description, "line_total": str(item.line_total)}
    item.delete()
    _audit(shop=shop, actor=actor, action="INVOICE_LINE_DELETED", resource=invoice, before=before, request_id=request_id)
    _finish_mutation(shop=shop, actor=actor, key=idempotency_key, operation="invoice.line.delete", payload=payload, resource=None)


@transaction.atomic
def set_invoice_adjustments(*, context, actor, invoice_id, discount_type, discount_value, tax_rate, idempotency_key, request_id=""):
    shop, invoice = _locked_invoice(context=context, actor=actor, invoice_id=invoice_id)
    payload = {"invoice_id": str(invoice.pk), "discount_type": discount_type, "discount_value": discount_value, "tax_rate": tax_rate}
    previous = _apply_idempotency_result(shop=shop, actor=actor, key=idempotency_key, operation="invoice.adjustments", payload=payload)
    if previous is not None:
        return previous
    if invoice.status != Invoice.Status.DRAFT:
        raise ValidationError("Only Draft invoices can be changed.")
    if discount_type not in Invoice.DiscountType.values:
        raise ValidationError({"discount_type": "Choose NONE, FIXED, or PERCENT."})
    try:
        discount_value = Decimal(discount_value or "0")
        tax_rate = None if tax_rate in (None, "") else Decimal(tax_rate)
    except Exception as error:
        raise ValidationError("Discount and tax values must be valid decimals.") from error
    if not discount_value.is_finite() or discount_value < 0 or (tax_rate is not None and (not tax_rate.is_finite() or tax_rate < 0)):
        raise ValidationError("Discount and tax values must be finite and non-negative.")
    if discount_type == Invoice.DiscountType.FIXED:
        try:
            discount_value = validate_money_amount(discount_value, invoice.currency)
        except ValueError as error:
            raise ValidationError({"discount_value": str(error)}) from error
    elif discount_type == Invoice.DiscountType.NONE:
        discount_value = Decimal("0")
    if discount_type == Invoice.DiscountType.PERCENT and discount_value > 100:
        raise ValidationError({"discount_value": "Percentage discount cannot exceed 100%."})
    before = {"discount_type": invoice.discount_type, "discount_value": str(invoice.discount_value), "tax_rate": str(invoice.tax_rate) if invoice.tax_rate is not None else None}
    invoice.discount_type, invoice.discount_value, invoice.tax_rate, invoice.updated_by = discount_type, discount_value, tax_rate, actor
    try:
        amounts = calculate_invoice_lines(invoice, list(invoice.items.all()))
    except ValueError as error:
        raise ValidationError({"discount_value": str(error)}) from error
    invoice.save(update_fields=("discount_type", "discount_value", "tax_rate", "updated_by", "updated_at"))
    _audit(shop=shop, actor=actor, action="INVOICE_ADJUSTMENTS_UPDATED", resource=invoice, before=before,
           after={"discount_type": discount_type, "discount_value": str(discount_value), "tax_rate": str(tax_rate) if tax_rate is not None else None}, request_id=request_id)
    _finish_mutation(shop=shop, actor=actor, key=idempotency_key, operation="invoice.adjustments", payload=payload, resource=invoice)
    return invoice


def _next_number(*, shop, kind, actor):
    sequence, _ = ShopFinancialSequence.objects.get_or_create(tenant=shop, kind=kind, defaults={"last_number": 0})
    sequence = ShopFinancialSequence.objects.select_for_update().get(pk=sequence.pk)
    sequence.last_number += 1
    sequence.updated_by = actor
    sequence.save(update_fields=("last_number", "updated_at", "updated_by"))
    prefix = "INV" if kind == ShopFinancialSequence.Kind.INVOICE else "CN"
    return f"{prefix}-{sequence.last_number:06d}"


@transaction.atomic
def issue_invoice(*, context, actor, invoice_id, idempotency_key, request_id=""):
    shop, invoice = _locked_invoice(context=context, actor=actor, invoice_id=invoice_id)
    payload = {"invoice_id": str(invoice.pk)}
    previous = _apply_idempotency_result(shop=shop, actor=actor, key=idempotency_key, operation="invoice.issue", payload=payload)
    if previous is not None:
        return previous
    if invoice.status != Invoice.Status.DRAFT:
        raise ValidationError("Only Draft invoices can be issued.")
    items = list(invoice.items.select_for_update().all())
    if not items:
        raise ValidationError({"items": "Add at least one line before issuing."})
    try:
        amounts = calculate_invoice_lines(invoice, items)
    except ValueError as error:
        raise ValidationError({"discount_value": str(error)}) from error
    for row in amounts:
        item = row["item"]
        item.discount_amount, item.tax_amount = row["discount_amount"], row["tax_amount"]
        item.save(update_fields=("discount_amount", "tax_amount", "updated_at"))
    invoice.invoice_number = _next_number(shop=shop, kind=ShopFinancialSequence.Kind.INVOICE, actor=actor)
    invoice.status, invoice.issued_at, invoice.issued_by, invoice.updated_by = Invoice.Status.ISSUED, timezone.now(), actor, actor
    invoice.save(update_fields=("invoice_number", "status", "issued_at", "issued_by", "updated_by", "updated_at"))
    _audit(shop=shop, actor=actor, action="INVOICE_ISSUED", resource=invoice,
           after={"invoice_number": invoice.invoice_number, "total": str(invoice.total_amount)}, request_id=request_id)
    _finish_mutation(shop=shop, actor=actor, key=idempotency_key, operation="invoice.issue", payload=payload, resource=invoice)
    return invoice


@transaction.atomic
def delete_draft_invoice(*, context, actor, invoice_id, idempotency_key, request_id=""):
    shop, invoice = _locked_invoice(context=context, actor=actor, invoice_id=invoice_id)
    payload = {"invoice_id": str(invoice.pk)}
    previous = _apply_idempotency_result(shop=shop, actor=actor, key=idempotency_key, operation="invoice.delete_draft", payload=payload)
    if previous is not None:
        return
    if invoice.status != Invoice.Status.DRAFT or invoice.payments.exists() or invoice.credit_notes.exists():
        raise ValidationError("Only a Draft invoice without financial records can be deleted.")
    _audit(shop=shop, actor=actor, action="DRAFT_INVOICE_DELETED", resource=invoice,
           before={"invoice_id": str(invoice.pk), "status": invoice.status}, request_id=request_id)
    invoice.items.all().delete()
    invoice.delete()
    _finish_mutation(shop=shop, actor=actor, key=idempotency_key, operation="invoice.delete_draft", payload=payload, resource=None)


@transaction.atomic
def void_invoice(*, context, actor, invoice_id, reason, idempotency_key, request_id=""):
    shop, invoice = _locked_invoice(context=context, actor=actor, invoice_id=invoice_id)
    payload = {"invoice_id": str(invoice.pk), "reason": reason}
    previous = _apply_idempotency_result(shop=shop, actor=actor, key=idempotency_key, operation="invoice.void", payload=payload)
    if previous is not None:
        return previous
    if invoice.status != Invoice.Status.ISSUED:
        raise ValidationError("Only an Issued invoice can be voided.")
    if invoice.payments.exists() or invoice.credit_notes.filter(status=CreditNote.Status.ISSUED).exists():
        raise ValidationError("An invoice with payment or credit history must be corrected using a credit note.")
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError({"reason": "A reason is required to void an invoice."})
    before = {"status": invoice.status, "invoice_number": invoice.invoice_number}
    invoice.status, invoice.void_reason, invoice.voided_at, invoice.voided_by, invoice.updated_by = Invoice.Status.VOID, reason[:500], timezone.now(), actor, actor
    invoice.save(update_fields=("status", "void_reason", "voided_at", "voided_by", "updated_by", "updated_at"))
    _audit(shop=shop, actor=actor, action="INVOICE_VOIDED", resource=invoice, before=before,
           after={"status": invoice.status, "reason": invoice.void_reason}, request_id=request_id)
    _finish_mutation(shop=shop, actor=actor, key=idempotency_key, operation="invoice.void", payload=payload, resource=invoice)
    return invoice


@transaction.atomic
def record_invoice_payment(*, context, actor, invoice_id, amount, idempotency_key, request_id=""):
    shop, invoice = _locked_invoice(context=context, actor=actor, invoice_id=invoice_id)
    payload = {"invoice_id": str(invoice.pk), "amount": amount}
    previous = _apply_idempotency_result(shop=shop, actor=actor, key=idempotency_key, operation="invoice.payment", payload=payload)
    if previous is not None:
        return previous
    if invoice.status != Invoice.Status.ISSUED:
        raise ValidationError("Payment can be recorded only for an Issued invoice.")
    try:
        amount = validate_money_amount(amount, invoice.currency, allow_zero=False)
    except ValueError as error:
        raise ValidationError({"amount": str(error)}) from error
    if amount > max(invoice.balance, Decimal("0")):
        raise ValidationError({"amount": "Payment cannot exceed this invoice's outstanding balance."})
    payment = InvoicePayment.objects.create(invoice=invoice, amount=amount, received_at=timezone.now(), recorded_by=actor, created_by=actor, updated_by=actor)
    _audit(shop=shop, actor=actor, action="INVOICE_PAYMENT_RECORDED", resource=payment,
           after={"invoice_id": str(invoice.pk), "amount": str(amount), "currency": invoice.currency}, request_id=request_id)
    _finish_mutation(shop=shop, actor=actor, key=idempotency_key, operation="invoice.payment", payload=payload, resource=payment)
    return payment


@transaction.atomic
def create_credit_note(*, context, actor, invoice_id, amount, reason, idempotency_key, request_id=""):
    shop, invoice = _locked_invoice(context=context, actor=actor, invoice_id=invoice_id)
    payload = {"invoice_id": str(invoice.pk), "amount": amount, "reason": reason}
    previous = _apply_idempotency_result(shop=shop, actor=actor, key=idempotency_key, operation="credit_note.create", payload=payload)
    if previous is not None:
        return previous
    if invoice.status != Invoice.Status.ISSUED:
        raise ValidationError("Credit notes can be created only for an Issued invoice.")
    if not invoice.payments.exists():
        raise ValidationError("An unpaid Issued invoice should be voided instead of credited.")
    try:
        amount = validate_money_amount(amount, invoice.currency, allow_zero=False)
    except ValueError as error:
        raise ValidationError({"amount": str(error)}) from error
    reason = (reason or "").strip()
    if not reason:
        raise ValidationError({"reason": "A reason is required."})
    remaining = invoice.total_amount - invoice.credited_total
    if amount > remaining:
        raise ValidationError({"amount": "Credit notes cannot exceed the remaining invoice total."})
    note = CreditNote.objects.create(tenant=shop, invoice=invoice, reason=reason[:500], amount=amount, created_by=actor, updated_by=actor)
    _audit(shop=shop, actor=actor, action="CREDIT_NOTE_CREATED", resource=note,
           after={"invoice_id": str(invoice.pk), "amount": str(amount), "currency": invoice.currency}, request_id=request_id)
    _finish_mutation(shop=shop, actor=actor, key=idempotency_key, operation="credit_note.create", payload=payload, resource=note)
    return note


@transaction.atomic
def issue_credit_note(*, context, actor, credit_note_id, idempotency_key, request_id=""):
    shop = _locked_shop_context(context, actor)
    try:
        note = CreditNote.objects.select_for_update().select_related("invoice").get(pk=credit_note_id, tenant=shop)
    except (CreditNote.DoesNotExist, ValueError, TypeError):
        raise NotFound() from None
    payload = {"credit_note_id": str(note.pk)}
    previous = _apply_idempotency_result(shop=shop, actor=actor, key=idempotency_key, operation="credit_note.issue", payload=payload)
    if previous is not None:
        return previous
    invoice = Invoice.objects.select_for_update().get(pk=note.invoice_id, tenant=shop)
    if note.status != CreditNote.Status.DRAFT or invoice.status != Invoice.Status.ISSUED:
        raise ValidationError("Only a Draft credit note for an Issued invoice can be issued.")
    if note.amount > invoice.total_amount - invoice.credited_total:
        raise ValidationError({"amount": "Credit notes cannot exceed the remaining invoice total."})
    note.credit_number = _next_number(shop=shop, kind=ShopFinancialSequence.Kind.CREDIT_NOTE, actor=actor)
    note.status, note.issued_at, note.issued_by, note.updated_by = CreditNote.Status.ISSUED, timezone.now(), actor, actor
    note.save(update_fields=("credit_number", "status", "issued_at", "issued_by", "updated_by", "updated_at"))
    _audit(shop=shop, actor=actor, action="CREDIT_NOTE_ISSUED", resource=note,
           after={"credit_number": note.credit_number, "amount": str(note.amount)}, request_id=request_id)
    _finish_mutation(shop=shop, actor=actor, key=idempotency_key, operation="credit_note.issue", payload=payload, resource=note)
    return note


@transaction.atomic
def delete_draft_credit_note(*, context, actor, credit_note_id, idempotency_key, request_id=""):
    shop = _locked_shop_context(context, actor)
    try:
        note = CreditNote.objects.select_for_update().get(pk=credit_note_id, tenant=shop)
    except (CreditNote.DoesNotExist, ValueError, TypeError):
        raise NotFound() from None
    payload = {"credit_note_id": str(note.pk)}
    previous = _apply_idempotency_result(shop=shop, actor=actor, key=idempotency_key, operation="credit_note.delete_draft", payload=payload)
    if previous is not None:
        return
    if note.status != CreditNote.Status.DRAFT or note.refunds.exists():
        raise ValidationError("Only a Draft credit note without refund records can be deleted.")
    _audit(shop=shop, actor=actor, action="DRAFT_CREDIT_NOTE_DELETED", resource=note,
           before={"credit_note_id": str(note.pk), "amount": str(note.amount)}, request_id=request_id)
    note.delete()
    _finish_mutation(shop=shop, actor=actor, key=idempotency_key, operation="credit_note.delete_draft", payload=payload, resource=None)


@transaction.atomic
def record_invoice_refund(*, context, actor, credit_note_id, payment_id, amount, idempotency_key, request_id=""):
    shop = _locked_shop_context(context, actor)
    try:
        note = CreditNote.objects.select_for_update().select_related("invoice").get(pk=credit_note_id, tenant=shop)
        payment = InvoicePayment.objects.select_for_update().select_related("invoice").get(pk=payment_id, invoice=note.invoice)
    except (CreditNote.DoesNotExist, InvoicePayment.DoesNotExist, ValueError, TypeError):
        raise NotFound() from None
    payload = {"credit_note_id": str(note.pk), "payment_id": str(payment.pk), "amount": amount}
    previous = _apply_idempotency_result(shop=shop, actor=actor, key=idempotency_key, operation="invoice.refund", payload=payload)
    if previous is not None:
        return previous
    if note.status != CreditNote.Status.ISSUED:
        raise ValidationError("Refunds can be recorded only against an Issued credit note.")
    try:
        amount = validate_money_amount(amount, note.invoice.currency, allow_zero=False)
    except ValueError as error:
        raise ValidationError({"amount": str(error)}) from error
    payment_refunded = InvoiceRefund.objects.filter(payment=payment).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    note_refunded = InvoiceRefund.objects.filter(credit_note=note).aggregate(total=Sum("amount"))["total"] or Decimal("0")
    if amount > payment.amount - payment_refunded:
        raise ValidationError({"amount": "Refund cannot exceed the remaining amount of this payment."})
    if amount > note.amount - note_refunded:
        raise ValidationError({"amount": "Refund cannot exceed the remaining amount of this credit note."})
    refund = InvoiceRefund.objects.create(payment=payment, credit_note=note, amount=amount, refunded_at=timezone.now(), recorded_by=actor, created_by=actor, updated_by=actor)
    _audit(shop=shop, actor=actor, action="INVOICE_REFUND_RECORDED", resource=refund,
           after={"invoice_id": str(payment.invoice_id), "credit_note_id": str(note.pk), "payment_id": str(payment.pk), "amount": str(amount), "currency": note.invoice.currency}, request_id=request_id)
    _finish_mutation(shop=shop, actor=actor, key=idempotency_key, operation="invoice.refund", payload=payload, resource=refund)
    return refund


def _store_financial_document(
    *, shop, actor, kind, locale, source, content, layout_version
):
    if locale not in LOCALES:
        raise ValidationError({"locale": "Choose a supported document language."})
    owner_field = {"INVOICE": "invoice", "RECEIPT": "payment", "CREDIT_NOTE": "credit_note"}[kind]
    existing = FinancialDocument.objects.filter(
        tenant=shop,
        kind=kind,
        locale=locale,
        layout_version=layout_version,
        **{f"{owner_field}_id": source.pk},
    ).first()
    if existing:
        return existing
    if not content.startswith(b"%PDF-") or len(content) > 8 * 1024 * 1024:
        raise ValidationError("Generated PDF is invalid or exceeds the private document size limit.")
    document = FinancialDocument(
        tenant=shop, kind=kind, locale=locale, layout_version=layout_version,
        generated_by=actor,
        generated_at=timezone.now(), sha256=hashlib.sha256(content).hexdigest(),
        **{owner_field: source}, created_by=actor, updated_by=actor,
    )
    if kind == "INVOICE":
        reference = source.invoice_number or str(source.pk)
    elif kind == "CREDIT_NOTE":
        reference = source.credit_number or str(source.pk)
    else:
        reference = str(source.pk)
    document.file.save(
        f"{kind.lower()}-{reference}-{locale}-layout-{layout_version}.pdf",
        ContentFile(content),
        save=False,
    )
    stored_name = document.file.name
    try:
        document.save()
    except Exception:
        try:
            document.file.storage.delete(stored_name)
        except Exception:
            logger.exception("Failed to remove orphaned private financial document object")
        raise
    _audit(
        shop=shop, actor=actor, action="FINANCIAL_DOCUMENT_GENERATED", resource=document,
        after={
            "kind": kind,
            "locale": locale,
            "layout_version": layout_version,
            "sha256": document.sha256,
        },
    )
    return document


def _validate_document_locale(locale):
    if locale not in LOCALES:
        raise ValidationError({"locale": "Choose a supported document language."})


@transaction.atomic
def generate_invoice_document(*, context, actor, invoice_id, locale):
    _validate_document_locale(locale)
    shop, invoice = _locked_invoice(context=context, actor=actor, invoice_id=invoice_id)
    if invoice.status not in (Invoice.Status.ISSUED, Invoice.Status.VOID):
        raise ValidationError("Only an Issued or Voided invoice can be exported.")
    existing = FinancialDocument.objects.filter(
        tenant=shop,
        kind=FinancialDocument.Kind.INVOICE,
        invoice=invoice,
        locale=locale,
        layout_version=FINANCIAL_PDF_LAYOUT_VERSION,
    ).first()
    if existing:
        return existing
    return _store_financial_document(
        shop=shop, actor=actor, kind=FinancialDocument.Kind.INVOICE, locale=locale,
        source=invoice,
        content=invoice_pdf(invoice, locale=locale),
        layout_version=FINANCIAL_PDF_LAYOUT_VERSION,
    )


@transaction.atomic
def generate_payment_receipt(*, context, actor, invoice_id, payment_id, locale):
    _validate_document_locale(locale)
    shop, invoice = _locked_invoice(context=context, actor=actor, invoice_id=invoice_id)
    try:
        payment = InvoicePayment.objects.select_for_update().get(pk=payment_id, invoice=invoice)
    except (InvoicePayment.DoesNotExist, ValueError, TypeError):
        raise NotFound() from None
    existing = FinancialDocument.objects.filter(
        tenant=shop,
        kind=FinancialDocument.Kind.RECEIPT,
        payment=payment,
        locale=locale,
        layout_version=FINANCIAL_PDF_LAYOUT_VERSION,
    ).first()
    if existing:
        return existing
    return _store_financial_document(
        shop=shop, actor=actor, kind=FinancialDocument.Kind.RECEIPT, locale=locale,
        source=payment,
        content=receipt_pdf(payment, locale=locale),
        layout_version=FINANCIAL_PDF_LAYOUT_VERSION,
    )


@transaction.atomic
def generate_credit_note_document(*, context, actor, credit_note_id, locale):
    _validate_document_locale(locale)
    shop = _locked_shop_context(context, actor)
    try:
        note = CreditNote.objects.select_for_update().select_related(
            "invoice__tenant", "invoice__client", "invoice__work"
        ).get(pk=credit_note_id, tenant=shop)
    except (CreditNote.DoesNotExist, ValueError, TypeError):
        raise NotFound() from None
    if FinancialPurgeRequest.objects.filter(
        tenant=shop,
        invoice_id=note.invoice_id,
        status__in=(FinancialPurgeRequest.Status.PENDING, FinancialPurgeRequest.Status.FAILED),
    ).exists():
        raise ValidationError({"invoice": "A Super Admin purge is pending. Retry or complete that purge first."})
    if note.status != CreditNote.Status.ISSUED:
        raise ValidationError("Only an Issued credit note can be exported.")
    existing = FinancialDocument.objects.filter(
        tenant=shop,
        kind=FinancialDocument.Kind.CREDIT_NOTE,
        credit_note=note,
        locale=locale,
        layout_version=FINANCIAL_PDF_LAYOUT_VERSION,
    ).first()
    if existing:
        return existing
    return _store_financial_document(
        shop=shop, actor=actor, kind=FinancialDocument.Kind.CREDIT_NOTE, locale=locale,
        source=note,
        content=credit_note_pdf(note, locale=locale),
        layout_version=FINANCIAL_PDF_LAYOUT_VERSION,
    )
