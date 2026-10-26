from decimal import Decimal, ROUND_HALF_UP

from apps.tenants.currency import currency_minor_unit


def calculate_invoice_lines(invoice, items):
    """Return stable discount/tax amounts without rounding the input money."""
    if not items:
        return []
    scale = currency_minor_unit(invoice.currency)
    quantum = Decimal(1).scaleb(-scale)
    subtotal = sum((item.line_total for item in items), Decimal("0"))
    discount_value = invoice.discount_value or Decimal("0")
    if invoice.discount_type == "FIXED":
        discount_total = discount_value.quantize(quantum, rounding=ROUND_HALF_UP)
        if discount_total > subtotal:
            raise ValueError("Discount cannot exceed the invoice subtotal.")
        allocations = []
        allocated = Decimal("0")
        for item in items[:-1]:
            amount = (discount_total * item.line_total / subtotal).quantize(
                quantum, rounding=ROUND_HALF_UP
            ) if subtotal else Decimal("0")
            allocations.append(amount)
            allocated += amount
        allocations.append(discount_total - allocated)
        # A rounded residual can exceed a very small final line. Keep every
        # discounted line non-negative while preserving the approved total.
        overflow = Decimal("0")
        if allocations[-1] > items[-1].line_total:
            overflow = allocations[-1] - items[-1].line_total
            allocations[-1] = items[-1].line_total
            for index in range(len(allocations) - 2, -1, -1):
                room = allocations[index]
                reduction = min(room, overflow)
                allocations[index] -= reduction
                overflow -= reduction
                if overflow == 0:
                    break
        if overflow:
            raise ValueError("Discount allocation could not be represented safely.")
    elif invoice.discount_type == "PERCENT":
        if discount_value < 0:
            raise ValueError("Discount percentage cannot be negative.")
        allocations = [
            (item.line_total * discount_value / Decimal("100")).quantize(
                quantum, rounding=ROUND_HALF_UP
            )
            for item in items
        ]
        if any(amount > item.line_total for amount, item in zip(allocations, items)):
            raise ValueError("Discount cannot exceed the invoice subtotal.")
    else:
        allocations = [Decimal("0") for _ in items]

    tax_rate = invoice.tax_rate
    rows = []
    for item, discount in zip(items, allocations):
        discounted = item.line_total - discount
        tax = Decimal("0")
        if tax_rate is not None:
            tax = (discounted * tax_rate / Decimal("100")).quantize(
                quantum, rounding=ROUND_HALF_UP
            )
        rows.append({"item": item, "discount_amount": discount, "tax_amount": tax})
    return rows
