from decimal import Decimal

from django.test import SimpleTestCase

from apps.billing.calculations import calculate_invoice_lines
from apps.billing.models import Invoice, InvoiceLineItem


class InvoiceCalculationTests(SimpleTestCase):
    def _invoice(self, currency="USD", discount_type=Invoice.DiscountType.NONE, discount_value="0", tax_rate=None):
        invoice = Invoice(
            currency=currency,
            discount_type=discount_type,
            discount_value=Decimal(discount_value),
            tax_rate=Decimal(tax_rate) if tax_rate is not None else None,
        )
        return invoice

    @staticmethod
    def _line(total):
        return InvoiceLineItem(line_total=Decimal(total))

    def test_fixed_discount_is_allocated_proportionally_then_taxed_per_line(self):
        invoice = self._invoice(
            discount_type=Invoice.DiscountType.FIXED,
            discount_value="3.00",
            tax_rate="10.00",
        )
        result = calculate_invoice_lines(invoice, [self._line("10.00"), self._line("20.00")])
        self.assertEqual([row["discount_amount"] for row in result], [Decimal("1.00"), Decimal("2.00")])
        self.assertEqual([row["tax_amount"] for row in result], [Decimal("0.90"), Decimal("1.80")])

    def test_tax_rounds_half_up_to_currency_minor_unit(self):
        invoice = self._invoice(tax_rate="10")
        result = calculate_invoice_lines(invoice, [self._line("0.05")])
        self.assertEqual(result[0]["tax_amount"], Decimal("0.01"))

    def test_fixed_discount_cannot_exceed_subtotal(self):
        invoice = self._invoice(discount_type=Invoice.DiscountType.FIXED, discount_value="10.01")
        with self.assertRaisesRegex(ValueError, "cannot exceed"):
            calculate_invoice_lines(invoice, [self._line("10.00")])
