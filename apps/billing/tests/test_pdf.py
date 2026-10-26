from unittest import TestCase
from io import BytesIO

from pypdf import PdfReader
from reportlab.lib.pagesizes import A5

from apps.billing.pdf import LABELS, _build_pdf


class FinancialPdfTests(TestCase):
    def test_invoice_layout_renders_each_supported_locale_consistently(self):
        for locale in LABELS:
            with self.subTest(locale=locale):
                kwargs = {
                    "title": LABELS[locale]["invoice"],
                    "locale": locale,
                    "shop_name": "Shop",
                    "client_name": "Client",
                    "work_number": "WO-0001",
                    "number": "INV-000001",
                    "date": "2026-10-21",
                    "rows": [("Stitching", "1", "12.50 KWD", "12.50 KWD")],
                    "totals": [("total", "12.50 KWD")],
                }
                first = _build_pdf(**kwargs)
                second = _build_pdf(**kwargs)
                self.assertTrue(first.startswith(b"%PDF-"))
                self.assertEqual(len(first), len(second))
                for page in PdfReader(BytesIO(first)).pages:
                    self.assertAlmostEqual(float(page.mediabox.width), A5[0], delta=0.5)
                    self.assertAlmostEqual(float(page.mediabox.height), A5[1], delta=0.5)

    def test_long_invoice_wraps_and_continues_on_a5_pages(self):
        rows = [
            (
                f"Alteration {index:03d} with a longer description that wraps neatly on A5",
                "2",
                "123.45 KWD",
                "246.90 KWD",
            )
            for index in range(1, 46)
        ]
        pdf = _build_pdf(
            title="Invoice INV-000001",
            locale="en",
            shop_name="Shop",
            client_name="Client",
            work_number="WO-0001",
            number="INV-000001",
            date="2026-10-22",
            rows=rows,
            totals=[("total", "11110.50 KWD")],
        )

        reader = PdfReader(BytesIO(pdf))
        self.assertGreater(len(reader.pages), 1)
        for page in reader.pages:
            self.assertAlmostEqual(float(page.mediabox.width), A5[0], delta=0.5)
            self.assertAlmostEqual(float(page.mediabox.height), A5[1], delta=0.5)
        extracted = "\n".join(page.extract_text() or "" for page in reader.pages)
        self.assertIn("Alteration 001", extracted)
        self.assertIn("Alteration 045", extracted)
        self.assertIn("11110.50 KWD", extracted)
