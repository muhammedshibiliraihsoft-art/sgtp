"""Deterministic, localized PDF rendering for immutable billing records."""

from decimal import Decimal
from functools import partial
from html import escape
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfgen.canvas import Canvas
import arabic_reshaper
from bidi.algorithm import get_display

from apps.catalog.measurement_pdf import (
    INK,
    LINE,
    MUTED,
    PALE,
    SCRIPT_FONTS,
    _register_script_fonts,
    _script_for_text,
)
from apps.common.pdf_layout import PDF_EXPORT_PAGE_SIZE


LABELS = {
    "en": {
        "invoice": "Invoice", "receipt": "Payment receipt", "credit_note": "Credit note",
        "shop": "Shop", "client": "Client", "work": "Work", "number": "Number",
        "date": "Date", "description": "Description", "quantity": "Qty", "unit_price": "Unit price",
        "line_total": "Line total", "subtotal": "Subtotal", "discount": "Discount",
        "tax": "Tax", "total": "Total", "paid": "Paid", "balance": "Balance",
        "amount_received": "Amount received", "reason": "Reason", "void": "VOID",
    },
    "ar-KW": {
        "invoice": "فاتورة", "receipt": "إيصال دفع", "credit_note": "إشعار دائن",
        "shop": "المتجر", "client": "العميل", "work": "الطلب", "number": "الرقم",
        "date": "التاريخ", "description": "الوصف", "quantity": "الكمية", "unit_price": "سعر الوحدة",
        "line_total": "الإجمالي", "subtotal": "المجموع الفرعي", "discount": "الخصم",
        "tax": "الضريبة", "total": "الإجمالي النهائي", "paid": "المدفوع", "balance": "الرصيد",
        "amount_received": "المبلغ المستلم", "reason": "السبب", "void": "ملغاة",
    },
    "bn": {
        "invoice": "চালান", "receipt": "পেমেন্ট রসিদ", "credit_note": "ক্রেডিট নোট",
        "shop": "দোকান", "client": "গ্রাহক", "work": "কাজ", "number": "নম্বর",
        "date": "তারিখ", "description": "বিবরণ", "quantity": "পরিমাণ", "unit_price": "একক মূল্য",
        "line_total": "লাইন মোট", "subtotal": "উপমোট", "discount": "ছাড়",
        "tax": "কর", "total": "মোট", "paid": "পরিশোধিত", "balance": "বকেয়া",
        "amount_received": "গৃহীত অর্থ", "reason": "কারণ", "void": "বাতিল",
    },
    "ur": {
        "invoice": "انوائس", "receipt": "ادائیگی کی رسید", "credit_note": "کریڈٹ نوٹ",
        "shop": "دکان", "client": "گاہک", "work": "کام", "number": "نمبر",
        "date": "تاریخ", "description": "تفصیل", "quantity": "مقدار", "unit_price": "فی یونٹ قیمت",
        "line_total": "لائن کا کل", "subtotal": "ذیلی کل", "discount": "رعایت",
        "tax": "ٹیکس", "total": "کل", "paid": "ادا شدہ", "balance": "بقایا",
        "amount_received": "وصول شدہ رقم", "reason": "وجہ", "void": "منسوخ",
    },
}

ACCENT = colors.HexColor("#176b74")
FINANCIAL_PDF_LAYOUT_VERSION = 2


def _money(value, currency):
    return f"{Decimal(value):f} {currency}"


def _build_pdf(*, title, locale, shop_name, client_name, work_number, number, date, rows, totals):
    labels = LABELS[locale]
    _register_script_fonts()
    output = BytesIO()
    doc = SimpleDocTemplate(
        output, pagesize=PDF_EXPORT_PAGE_SIZE, rightMargin=8 * mm, leftMargin=8 * mm,
        topMargin=9 * mm, bottomMargin=10 * mm, title=title, author="SGTP", pageCompression=1,
    )

    def p(
        text,
        *,
        bold=False,
        muted=False,
        header=False,
        title_style=False,
        align_right=False,
    ):
        text = " ".join(str(text or "").split())
        script = _script_for_text(text)
        if script == "arabic":
            text = get_display(arabic_reshaper.reshape(text))
        style = ParagraphStyle(
            f"Financial{script or 'Latin'}{bold}{muted}{header}{title_style}{align_right}",
            fontName=(SCRIPT_FONTS[script] if script else ("Helvetica-Bold" if bold or header else "Helvetica")),
            fontSize=14 if title_style else (7.5 if header else 8.5),
            leading=16 if title_style else (9 if header else 10),
            textColor=colors.white if header else (MUTED if muted else INK),
            alignment=TA_RIGHT if script == "arabic" or align_right else TA_LEFT,
        )
        return Paragraph(escape(text), style)

    story = [p(title, bold=True, title_style=True), Spacer(1, 2 * mm)]
    info_rows = [
        [p(labels["shop"], muted=True), p(shop_name)],
        [p(labels["client"], muted=True), p(client_name)],
        [p(labels["work"], muted=True), p(work_number)],
        [p(labels["number"], muted=True), p(number)],
        [p(labels["date"], muted=True), p(date)],
    ]
    content_width = doc.width
    info = Table(
        info_rows,
        colWidths=(content_width * 0.28, content_width * 0.72),
        hAlign="LEFT",
    )
    info.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEBELOW", (0, 0), (-1, -1), 0.35, LINE),
        ("LEFTPADDING", (0, 0), (-1, -1), 1.2 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1.2 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 1 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1 * mm),
    ]))
    story.extend([info, Spacer(1, 3 * mm)])

    table_rows = [[
        p(labels["description"], header=True),
        p(labels["quantity"], header=True, align_right=True),
        p(labels["unit_price"], header=True, align_right=True),
        p(labels["line_total"], header=True, align_right=True),
    ]]
    table_rows.extend(
        [
            p(row[0]),
            p(row[1], align_right=True),
            p(row[2], align_right=True),
            p(row[3], align_right=True),
        ]
        for row in rows
    )
    if len(table_rows) == 1:
        table_rows.append([p("—"), p("—"), p("—"), p("—")])
    line_table = Table(
        table_rows,
        colWidths=(
            content_width * 0.39,
            content_width * 0.11,
            content_width * 0.24,
            content_width * 0.26,
        ),
        repeatRows=1,
        hAlign="LEFT",
    )
    line_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), (colors.white, PALE)),
        ("GRID", (0, 0), (-1, -1), 0.35, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 1 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 1 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 1 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1 * mm),
    ]))
    story.extend([line_table, Spacer(1, 3 * mm)])

    total_rows = [
        [p(labels[key], muted=True), p(value, bold=(key == "total"), align_right=True)]
        for key, value in totals
    ]
    totals_table = Table(
        total_rows,
        colWidths=(content_width * 0.30, content_width * 0.34),
        hAlign="RIGHT",
    )
    totals_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("LINEABOVE", (0, -1), (-1, -1), 0.8, ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 1 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1 * mm),
    ]))
    story.append(totals_table)
    doc.build(story, canvasmaker=partial(Canvas, invariant=1))
    return output.getvalue()


def invoice_pdf(invoice, *, locale):
    labels = LABELS[locale]
    lines = list(invoice.items.all())
    rows = [
        (item.description, item.quantity, _money(item.unit_price, invoice.currency), _money(item.line_total, invoice.currency))
        for item in lines
    ]
    totals = [
        ("subtotal", _money(invoice.subtotal, invoice.currency)),
        ("discount", _money(invoice.discount_total, invoice.currency)),
        ("tax", _money(invoice.tax_total, invoice.currency)),
        ("total", _money(invoice.total_amount, invoice.currency)),
        ("paid", _money(invoice.amount_paid, invoice.currency)),
        ("balance", _money(invoice.balance, invoice.currency)),
    ]
    title = f"{labels['invoice']} {invoice.invoice_number or ''}".strip()
    if invoice.status == "VOID":
        title += f" — {labels['void']}"
    return _build_pdf(
        title=title, locale=locale, shop_name=invoice.tenant.name,
        client_name=invoice.client.name, work_number=invoice.work.work_number,
        number=invoice.invoice_number or "Draft", date=(invoice.issued_at or invoice.created_at).date().isoformat(),
        rows=rows, totals=totals,
    )


def receipt_pdf(payment, *, locale):
    labels = LABELS[locale]
    invoice = payment.invoice
    return _build_pdf(
        title=labels["receipt"], locale=locale, shop_name=invoice.tenant.name,
        client_name=invoice.client.name, work_number=invoice.work.work_number,
        number=f"{invoice.invoice_number or 'Invoice'} / {payment.pk}",
        date=payment.received_at.date().isoformat(), rows=[],
        totals=[("amount_received", _money(payment.amount, invoice.currency))],
    )


def credit_note_pdf(note, *, locale):
    labels = LABELS[locale]
    invoice = note.invoice
    return _build_pdf(
        title=f"{labels['credit_note']} {note.credit_number or ''}".strip(), locale=locale,
        shop_name=invoice.tenant.name, client_name=invoice.client.name,
        work_number=invoice.work.work_number, number=note.credit_number or "Draft",
        date=(note.issued_at or note.created_at).date().isoformat(), rows=[
            (note.reason, "1", _money(note.amount, invoice.currency), _money(note.amount, invoice.currency))
        ], totals=[("total", _money(note.amount, invoice.currency))],
    )
