from django.db import transaction
from django.db.models import Q
from rest_framework.exceptions import ValidationError

from apps.catalog.models import Design, ShopDesignPrice
from apps.tenants.currency import normalize_currency, validate_money_amount
from apps.tenants.financial_access import require_financial_access
from apps.tenants.models import Tenant
from apps.billing.services import (
    _apply_idempotency_result,
    _audit,
    _finish_mutation,
)


@transaction.atomic
def set_shop_design_price(*, context, actor, design_id, amount, reject_change=False, idempotency_key, request_id=""):
    shop = Tenant.objects.select_for_update().get(pk=context.shop.pk, is_active=True)
    require_financial_access(context=context, actor=actor, lock=True)
    try:
        currency = normalize_currency(shop.default_currency)
    except ValueError as error:
        raise ValidationError(
            {"currency": "Set a valid Shop default currency before entering prices."}
        ) from error
    try:
        amount = validate_money_amount(amount, currency)
    except ValueError as error:
        raise ValidationError({"amount": str(error)}) from error
    payload = {"design_id": str(design_id), "amount": amount, "currency": currency}
    previous = _apply_idempotency_result(
        shop=shop, actor=actor, key=idempotency_key, operation="design_price.set", payload=payload
    )
    if previous is not None:
        return previous
    try:
        design = Design.objects.select_for_update().get(
            Q(tenant__isnull=True) | Q(tenant=shop),
            pk=design_id,
            status=Design.Status.ACTIVE,
        )
    except (Design.DoesNotExist, ValueError, TypeError):
        from rest_framework.exceptions import NotFound

        raise NotFound() from None
    price = (
        ShopDesignPrice.objects.select_for_update()
        .filter(tenant=shop, design=design)
        .first()
    )
    if price is not None:
        before = {"amount": str(price.amount), "currency": price.currency}
        if reject_change:
            if price.amount != amount or price.currency != currency:
                raise ValidationError(
                    {"price": "A retry cannot change an existing Design price."}
                )
            return price
        price.amount = amount
        price.currency = currency
        price.updated_by = actor
        price.save(update_fields=("amount", "currency", "updated_by", "updated_at"))
        _audit(shop=shop, actor=actor, action="DESIGN_PRICE_SET", resource=price, before=before,
               after={"amount": str(price.amount), "currency": price.currency}, request_id=request_id)
        _finish_mutation(shop=shop, actor=actor, key=idempotency_key, operation="design_price.set", payload=payload, resource=price)
        return price
    price = ShopDesignPrice.objects.create(
        tenant=shop,
        design=design,
        amount=amount,
        currency=currency,
        created_by=actor,
        updated_by=actor,
    )
    _audit(shop=shop, actor=actor, action="DESIGN_PRICE_SET", resource=price,
           after={"amount": str(price.amount), "currency": price.currency}, request_id=request_id)
    _finish_mutation(shop=shop, actor=actor, key=idempotency_key, operation="design_price.set", payload=payload, resource=price)
    return price
