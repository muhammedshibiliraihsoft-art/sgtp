"""Private, non-persistent Measurement / Design worksheet PDF rendering."""

from html import escape
from io import BytesIO
from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    LongTable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


INK = colors.HexColor("#17243a")
MUTED = colors.HexColor("#64748b")
ACCENT = colors.HexColor("#176b74")
PALE = colors.HexColor("#eef6f6")
LINE = colors.HexColor("#d9e2ec")
FONT_DIR = Path(__file__).with_name("fonts")
SCRIPT_FONTS = {
    "arabic": "SGTPNotoArabic",
    "bengali": "SGTPNotoBengali",
    "malayalam": "SGTPNotoMalayalam",
}


def _register_script_fonts():
    font_files = {
        "arabic": "NotoSansArabic.ttf",
        "bengali": "NotoSansBengali.ttf",
        "malayalam": "NotoSansMalayalam.ttf",
    }
    registered = set(pdfmetrics.getRegisteredFontNames())
    for script, font_name in SCRIPT_FONTS.items():
        if font_name not in registered:
            pdfmetrics.registerFont(
                TTFont(font_name, str(FONT_DIR / font_files[script]), shapable=True)
            )


def _script_for_text(value):
    for character in value:
        codepoint = ord(character)
        if (
            0x0600 <= codepoint <= 0x06FF
            or 0x0750 <= codepoint <= 0x077F
            or 0x08A0 <= codepoint <= 0x08FF
            or 0xFB50 <= codepoint <= 0xFDFF
            or 0xFE70 <= codepoint <= 0xFEFF
        ):
            return "arabic"
        if 0x0980 <= codepoint <= 0x09FF:
            return "bengali"
        if 0x0D00 <= codepoint <= 0x0D7F:
            return "malayalam"
    return None


def _localized_name(instance, locale, related_name="translations", field="name"):
    if instance is None:
        return ""
    translations = getattr(instance, related_name, None)
    if translations is None:
        return str(instance)
    return (
        translations.filter(locale=locale).values_list(field, flat=True).first()
        or translations.filter(locale="en").values_list(field, flat=True).first()
        or str(instance)
    )


def build_measurement_worksheet_pdf(
    *, shop, profile, measurement_set, locale="en", design=None, design_version=None
):
    """Build a private A4 worksheet from already-authorized ORM objects."""
    output = BytesIO()
    document = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title=f"Measurement Worksheet - Version {measurement_set.version}",
        author="SGTP",
        pageCompression=1,
    )

    styles = {
        "title": ParagraphStyle(
            "WorksheetTitle",
            fontName="Helvetica-Bold",
            fontSize=19,
            leading=23,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=3 * mm,
        ),
        "subtitle": ParagraphStyle(
            "WorksheetSubtitle",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=MUTED,
            spaceAfter=5 * mm,
        ),
        "section": ParagraphStyle(
            "WorksheetSection",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=INK,
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
        ),
        "body": ParagraphStyle(
            "WorksheetBody",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=INK,
        ),
        "muted": ParagraphStyle(
            "WorksheetMuted",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED,
        ),
        "table_header": ParagraphStyle(
            "WorksheetTableHeader",
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=11,
            textColor=colors.white,
        ),
        "demo_title": ParagraphStyle(
            "WorksheetDemoTitle",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=ACCENT,
        ),
        "center": ParagraphStyle(
            "WorksheetCenter",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED,
            alignment=TA_CENTER,
        ),
    }

    _register_script_fonts()

    def paragraph(value, style="body"):
        cleaned = " ".join(str(value or "").split())
        script = _script_for_text(cleaned)
        paragraph_style = styles[style]
        if script:
            font_name = SCRIPT_FONTS[script]
            paragraph_style = ParagraphStyle(
                f"{paragraph_style.name}_{font_name}",
                parent=paragraph_style,
                fontName=font_name,
                alignment=TA_RIGHT if script == "arabic" else TA_LEFT,
            )
            if script == "arabic":
                cleaned = get_display(arabic_reshaper.reshape(cleaned))
        return Paragraph(escape(cleaned), paragraph_style)

    wearer = profile.client or profile.related_person
    primary_client = (
        profile.client if profile.client_id else profile.related_person.primary_client
    )
    family_name = _localized_name(profile.family, locale)
    variant_name = _localized_name(profile.variant, locale)

    story = [
        paragraph("Measurement / Design Worksheet", "title"),
        paragraph(
            "PRIVATE WORKSHEET · NOT AN INVOICE · Measurement values retain their recorded units.",
            "subtitle",
        ),
    ]

    identity_rows = []
    if shop is not None:
        identity_rows.append((paragraph("Shop", "muted"), paragraph(shop.name)))
    identity_rows.extend(
        [
            (paragraph("Primary Client", "muted"), paragraph(primary_client.name)),
            (paragraph("Measured Person", "muted"), paragraph(wearer.name)),
            (paragraph("Garment Family", "muted"), paragraph(family_name)),
            (paragraph("Variant", "muted"), paragraph(variant_name or "—")),
            (
                paragraph("Measurement Version", "muted"),
                paragraph(str(measurement_set.version)),
            ),
        ]
    )
    identity = Table(identity_rows, colWidths=[43 * mm, 132 * mm], hAlign="LEFT")
    identity.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
                ("LINEBELOW", (0, 0), (-1, -1), 0.35, LINE),
            ]
        )
    )
    story.extend([identity, paragraph("Measurements", "section")])

    measurement_rows = [
        [
            paragraph("Measurement", "table_header"),
            paragraph("Value", "table_header"),
            paragraph("Unit", "table_header"),
        ]
    ]
    for value in measurement_set.values.all():
        label = _localized_name(value, locale, "label_translations", "name")
        measurement_rows.append(
            [
                paragraph(label or value.label_snapshot),
                paragraph(value.value),
                paragraph(value.unit),
            ]
        )
    if len(measurement_rows) == 1:
        measurement_rows.append(
            [paragraph("No values recorded"), paragraph("—"), paragraph("—")]
        )
    measurement_table = LongTable(
        measurement_rows,
        colWidths=[100 * mm, 39 * mm, 36 * mm],
        repeatRows=1,
        hAlign="LEFT",
    )
    measurement_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ]
        )
    )
    story.append(measurement_table)

    if design is not None:
        story.append(paragraph("Design", "section"))
        design_name = (
            _localized_name(design_version, locale, "translations", "name")
            or "Saved design"
        )
        design_rows = [
            [paragraph("Name", "muted"), paragraph(design_name)],
            [
                paragraph("Design Version", "muted"),
                paragraph(str(design_version.number) if design_version else "—"),
            ],
        ]
        if design_version is not None:
            for selection in design_version.selections.all():
                selection_name = (
                    _localized_name(selection, locale, "translations", "name")
                    or selection.selected_name_en
                )
                design_rows.append(
                    [
                        paragraph(selection.option_group.code, "muted"),
                        paragraph(selection_name),
                    ]
                )
        design_table = Table(design_rows, colWidths=[43 * mm, 132 * mm], hAlign="LEFT")
        design_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
                    ("TOPPADDING", (0, 0), (-1, -1), 2 * mm),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
                    ("LINEBELOW", (0, 0), (-1, -1), 0.35, LINE),
                ]
            )
        )
        story.append(design_table)
    else:
        story.extend(
            [paragraph("Design", "section"), paragraph("No design selected.", "muted")]
        )

    story.extend(
        [
            Spacer(1, 6 * mm),
            KeepTogether(
                [
                    paragraph("Bill / Estimate — DEMO ONLY", "demo_title"),
                    paragraph(
                        "Presentation placeholder only. No invoice, amount, tax, payment, balance, or billing record is generated or stored.",
                        "muted",
                    ),
                ]
            ),
        ]
    )

    def draw_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(LINE)
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, 13 * mm, A4[0] - doc.rightMargin, 13 * mm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawRightString(A4[0] - doc.rightMargin, 8 * mm, f"Page {doc.page}")
        canvas.restoreState()

    document.build(story, onFirstPage=draw_footer, onLaterPages=draw_footer)
    return output.getvalue()
