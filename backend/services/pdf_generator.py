import base64
import io
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# -----------------------------------------------------------------------------
# Brand palette (mirrors backend/static/css/volt.css)
# -----------------------------------------------------------------------------
PRIMARY = colors.HexColor("#31316a")
INDIGO = colors.HexColor("#6366f1")
TEAL = colors.HexColor("#0d9488")
INK = colors.HexColor("#1f2937")
MUTED = colors.HexColor("#6b7280")
FAINT = colors.HexColor("#9ca3af")
BORDER = colors.HexColor("#e5e7eb")
SOFT = colors.HexColor("#eef1fb")
CARD_BG = colors.HexColor("#f8fafc")
SUCCESS = colors.HexColor("#10b981")
WARNING = colors.HexColor("#f0b429")
DANGER = colors.HexColor("#ef4444")

PAGE_TITLE = "Alzheimer's MRI AI Diagnostic Report"
BRAND_NAME = "NeuroLens"
BRAND_SUB = "AI-assisted neuroimaging"


def _risk_meta(risk_score: int):
    """Return (label, color) for a 0-100 risk score."""
    if risk_score < 30:
        return "Low", SUCCESS
    if risk_score < 60:
        return "Moderate", WARNING
    return "High", DANGER


def _draw_page_furniture(canvas, doc):
    """Header band + footer painted on every page."""
    canvas.saveState()
    w, h = A4

    # --- Header band ---
    band_h = 26 * mm
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, h - band_h, w, band_h, stroke=0, fill=1)
    canvas.setFillColor(INDIGO)
    canvas.rect(0, h - band_h - 2.2, w, 2.2, stroke=0, fill=1)

    # Brand mark
    mark_x, mark_y, mark_s = 18 * mm, h - band_h + 6.5 * mm, 13 * mm
    canvas.setFillColor(INDIGO)
    canvas.roundRect(mark_x, mark_y, mark_s, mark_s, 3, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 15)
    canvas.drawCentredString(mark_x + mark_s / 2, mark_y + 3.5 * mm, "N")

    # Brand text
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 14)
    canvas.drawString(mark_x + mark_s + 5 * mm, h - band_h + 15 * mm, BRAND_NAME)
    canvas.setFillColor(colors.HexColor("#c7cbf5"))
    canvas.setFont("Helvetica", 8)
    canvas.drawString(mark_x + mark_s + 5 * mm, h - band_h + 10 * mm, BRAND_SUB)

    # Right-aligned document label
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 9)
    canvas.drawRightString(w - 18 * mm, h - band_h + 15 * mm, "DIAGNOSTIC REPORT")
    canvas.setFillColor(colors.HexColor("#c7cbf5"))
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(w - 18 * mm, h - band_h + 10 * mm, "Confidential · Clinical use")

    # --- Footer ---
    canvas.setStrokeColor(BORDER)
    canvas.setLineWidth(0.6)
    canvas.line(18 * mm, 15 * mm, w - 18 * mm, 15 * mm)
    canvas.setFillColor(FAINT)
    canvas.setFont("Helvetica", 7.5)
    canvas.drawString(
        18 * mm,
        10.5 * mm,
        "Confidential — for authorized clinical personnel only. AI-assisted; not a standalone diagnosis.",
    )
    canvas.drawRightString(w - 18 * mm, 10.5 * mm, f"Page {doc.page}")
    canvas.restoreState()


def _styles():
    ss = getSampleStyleSheet()

    ss.add(
        ParagraphStyle(
            "DocTitle",
            parent=ss["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=2,
        )
    )
    ss.add(
        ParagraphStyle(
            "DocSubtitle",
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=MUTED,
            spaceAfter=0,
        )
    )
    ss.add(
        ParagraphStyle(
            "Section",
            fontName="Helvetica-Bold",
            fontSize=11.5,
            leading=14,
            textColor=PRIMARY,
            spaceBefore=6,
            spaceAfter=8,
        )
    )
    ss.add(
        ParagraphStyle(
            "Body",
            parent=ss["BodyText"],
            fontName="Helvetica",
            fontSize=9.8,
            leading=15,
            textColor=INK,
            alignment=TA_JUSTIFY,
            spaceAfter=6,
        )
    )
    ss.add(
        ParagraphStyle(
            "ReportBullet",
            fontName="Helvetica",
            fontSize=9.8,
            leading=15,
            textColor=INK,
        )
    )
    ss.add(
        ParagraphStyle(
            "CellLabel",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED,
        )
    )
    ss.add(
        ParagraphStyle(
            "CellValue",
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=13,
            textColor=INK,
        )
    )
    ss.add(
        ParagraphStyle(
            "MetricLabel",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=MUTED,
            alignment=TA_CENTER,
        )
    )
    ss.add(
        ParagraphStyle(
            "MetricValue",
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=PRIMARY,
            alignment=TA_CENTER,
        )
    )
    ss.add(
        ParagraphStyle(
            "Disclaimer",
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=12,
            textColor=MUTED,
        )
    )
    ss.add(
        ParagraphStyle(
            "Caption",
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=11,
            textColor=MUTED,
            alignment=TA_CENTER,
        )
    )
    return ss


def _detail_table(rows, ss):
    """Two-column key/value details table."""
    data = []
    for label, value in rows:
        data.append(
            [
                Paragraph(label.upper(), ss["CellLabel"]),
                Paragraph(str(value), ss["CellValue"]),
            ]
        )
    tbl = Table(data, colWidths=[45 * mm, 128 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), CARD_BG),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, BORDER),
                ("BOX", (0, 0), (-1, -1), 0.6, BORDER),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return tbl


def _metric_cards(predicted_stage, confidence_pct, risk_score, risk_label, risk_color, ss):
    """Three summary cards: stage, confidence, risk."""
    stage_cell = [
        Paragraph("PREDICTED STAGE", ss["MetricLabel"]),
        Spacer(1, 4),
        Paragraph(predicted_stage, ss["MetricValue"]),
    ]
    conf_cell = [
        Paragraph("MODEL CONFIDENCE", ss["MetricLabel"]),
        Spacer(1, 4),
        Paragraph(f"{confidence_pct}%", ss["MetricValue"]),
    ]
    risk_value_style = ParagraphStyle(
        "RiskValue", parent=ss["MetricValue"], textColor=risk_color
    )
    risk_cell = [
        Paragraph("ESTIMATED RISK", ss["MetricLabel"]),
        Spacer(1, 4),
        Paragraph(f"{risk_label}", risk_value_style),
        Paragraph(f"{risk_score}/100", ss["MetricLabel"]),
    ]

    tbl = Table(
        [[stage_cell, conf_cell, risk_cell]],
        colWidths=[57.6 * mm, 57.6 * mm, 57.6 * mm],
    )
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ("BOX", (0, 0), (0, -1), 0.6, BORDER),
                ("BOX", (1, 0), (1, -1), 0.6, BORDER),
                ("BOX", (2, 0), (2, -1), 0.6, BORDER),
                ("LINEABOVE", (0, 0), (-1, 0), 2.2, INDIGO),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return tbl


def _gradcam_flowable(gradcam_b64, ss):
    """
    Decode a base64 Grad-CAM image and return a framed, captioned flowable.
    Returns None if the image is missing or cannot be decoded.
    """
    if not gradcam_b64:
        return None

    raw = gradcam_b64.strip()
    # Tolerate data URIs like "data:image/png;base64,...."
    if raw.startswith("data:") and "," in raw:
        raw = raw.split(",", 1)[1]

    try:
        img_bytes = base64.b64decode(raw)
        reader = ImageReader(io.BytesIO(img_bytes))
        iw, ih = reader.getSize()
        if not iw or not ih:
            return None
    except Exception:
        return None

    # Scale to fit a sensible display width while preserving aspect ratio.
    display_w = 78 * mm
    display_h = display_w * (ih / iw)
    max_h = 78 * mm
    if display_h > max_h:
        display_h = max_h
        display_w = display_h * (iw / ih)

    img = Image(io.BytesIO(img_bytes), width=display_w, height=display_h)
    img.hAlign = "CENTER"

    inner = Table([[img]], colWidths=[display_w])
    inner.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.8, BORDER),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#0b1220")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )

    return KeepTogether(
        [
            Paragraph("Grad-CAM Visualization", ss["Section"]),
            Paragraph(
                "Heat-map overlay highlighting the MRI regions that most "
                "influenced the model's prediction. Warmer areas indicate "
                "higher activation.",
                ss["Body"],
            ),
            Spacer(1, 4),
            inner,
            Spacer(1, 4),
            Paragraph(
                "Figure 1 — Model attention overlay (Grad-CAM).", ss["Caption"]
            ),
        ]
    )


def _disclaimer_box(text, ss):
    tbl = Table([[Paragraph(text, ss["Disclaimer"])]], colWidths=[173 * mm])
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff8e6")),
                ("BOX", (0, 0), (-1, -1), 0.6, WARNING),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return tbl


def generate_pdf_base64(
    report_text: str,
    patient_id: str,
    predicted_stage: str,
    confidence_score: Optional[float] = None,
    risk_score: Optional[int] = None,
    clinician_notes: str = "",
    patient_name: str = "",
    patient_age: Optional[int] = None,
    patient_gender: str = "",
    report_id: str = "",
    gradcam_base64: str = "",
) -> str:
    """
    Render a professional, branded clinical PDF and return it base64-encoded.

    Structured fields (confidence_score, risk_score, clinician_notes, patient
    details, gradcam_base64) are optional; when omitted the report still
    renders cleanly.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=34 * mm,
        bottomMargin=22 * mm,
        title=PAGE_TITLE,
        author=BRAND_NAME,
    )
    ss = _styles()
    story = []

    generated_on = datetime.now().strftime("%d %B %Y · %I:%M %p")

    # --- Title block ---
    story.append(Paragraph(PAGE_TITLE, ss["DocTitle"]))
    story.append(
        Paragraph(
            "Automated neuroimaging analysis with clinician review",
            ss["DocSubtitle"],
        )
    )
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER))
    story.append(Spacer(1, 14))

    # --- Patient & examination details ---
    story.append(Paragraph("Patient &amp; Examination", ss["Section"]))
    detail_rows = [
        ("Patient name", patient_name or "—"),
    ]
    demo = []
    if patient_age is not None:
        demo.append(f"{patient_age} yrs")
    if patient_gender:
        demo.append(str(patient_gender).capitalize())
    if demo:
        detail_rows.append(("Demographics", " · ".join(demo)))
    detail_rows += [
        ("Patient ID", patient_id or "—"),
        ("Report ID", report_id or "—"),
        ("Generated on", generated_on),
    ]
    story.append(_detail_table(detail_rows, ss))
    story.append(Spacer(1, 16))

    # --- AI analysis summary (metric cards) ---
    story.append(Paragraph("AI Analysis Summary", ss["Section"]))
    confidence_pct = round((confidence_score or 0.0) * 100, 1)
    risk_val = int(risk_score or 0)
    risk_label, risk_color = _risk_meta(risk_val)
    story.append(
        _metric_cards(
            predicted_stage or "Unavailable",
            confidence_pct,
            risk_val,
            risk_label,
            risk_color,
            ss,
        )
    )
    story.append(Spacer(1, 16))

    # --- Grad-CAM visualization (optional) ---
    gradcam = _gradcam_flowable(gradcam_base64, ss)
    if gradcam is not None:
        story.append(gradcam)
        story.append(Spacer(1, 16))

    # --- Interpretation ---
    interpretation = KeepTogether(
        [
            Paragraph("Interpretation", ss["Section"]),
            Paragraph(
                "This assessment was generated from MRI-derived image features. "
                "The predicted stage reflects the model's estimated classification "
                "based on observed imaging patterns, and the confidence score "
                "represents model certainty for this prediction. The risk score "
                "estimates relative progression likelihood and should be interpreted "
                "alongside a full clinical evaluation.",
                ss["Body"],
            ),
        ]
    )
    story.append(interpretation)
    story.append(Spacer(1, 8))

    # --- Clinical notes ---
    notes = (clinician_notes or "").strip() or "No clinician notes provided."
    story.append(
        KeepTogether(
            [
                Paragraph("Clinical Notes", ss["Section"]),
                Paragraph(notes.replace("\n", "<br/>"), ss["Body"]),
            ]
        )
    )
    story.append(Spacer(1, 8))

    # --- Recommended next steps ---
    steps = [
        "Correlate findings with a neurological examination.",
        "Consider cognitive assessment if clinically indicated.",
        "Compare with prior imaging studies where available.",
        "Schedule specialist review when appropriate.",
    ]
    story.append(
        KeepTogether(
            [
                Paragraph("Recommended Next Steps", ss["Section"]),
                ListFlowable(
                    [ListItem(Paragraph(s, ss["ReportBullet"]), leftIndent=6) for s in steps],
                    bulletType="bullet",
                    bulletColor=INDIGO,
                    bulletFontSize=7,
                    leftIndent=14,
                    spaceBefore=1,
                ),
            ]
        )
    )
    story.append(Spacer(1, 16))

    # --- Disclaimer ---
    story.append(
        _disclaimer_box(
            "<b>Disclaimer.</b> This report is generated using AI-assisted analysis "
            "and is intended to support clinical decision-making. It is not a "
            "standalone medical diagnosis and must be reviewed by a qualified clinician.",
            ss,
        )
    )

    doc.build(story, onFirstPage=_draw_page_furniture, onLaterPages=_draw_page_furniture)

    pdf_bytes = buf.getvalue()
    buf.close()
    return base64.b64encode(pdf_bytes).decode("utf-8")
