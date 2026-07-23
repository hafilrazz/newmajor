import base64
import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


def generate_pdf_base64(
    report_text: str,
    patient_id: str,
    predicted_stage: str,
) -> str:

    buf = io.BytesIO()

    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=50,
        rightMargin=50,
        topMargin=60,
        bottomMargin=50,
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    title_style.alignment = TA_CENTER

    heading = styles["Heading2"]
    normal = styles["BodyText"]

    elements = []

    # -----------------------------
    # HEADER
    # -----------------------------
    elements.append(
        Paragraph(
            "Alzheimer’s MRI AI Diagnostic Report",
            title_style,
        )
    )

    elements.append(Spacer(1, 20))

    # -----------------------------
    # PATIENT DETAILS TABLE
    # -----------------------------
    patient_info = [
        ["Patient ID", patient_id],
        ["Predicted Stage", predicted_stage],
        [
            "Generated On",
            datetime.now().strftime(
                "%d %B %Y, %I:%M %p"
            ),
        ],
    ]

    table = Table(
        patient_info,
        colWidths=[160, 300],
    )

    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E8EEF7")),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("PADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    elements.append(table)

    elements.append(Spacer(1, 30))

    # -----------------------------
    # REPORT SECTION
    # -----------------------------
    elements.append(
        Paragraph(
            "AI Findings & Interpretation",
            heading,
        )
    )

    elements.append(Spacer(1, 10))

    paragraphs = report_text.split("\n")

    for p in paragraphs:
        if p.strip():
            elements.append(
                Paragraph(
                    p,
                    normal,
                )
            )
            elements.append(
                Spacer(
                    1,
                    8,
                )
            )

    elements.append(Spacer(1, 20))

    # -----------------------------
    # RECOMMENDATIONS
    # -----------------------------
    elements.append(
        Paragraph(
            "Clinical Recommendation",
            heading,
        )
    )

    recommendation = """
    • Review MRI findings with a specialist.<br/>
    • Correlate with cognitive assessment.<br/>
    • Schedule follow-up evaluation if necessary.
    """

    elements.append(
        Paragraph(
            recommendation,
            normal,
        )
    )

    elements.append(Spacer(1, 25))

    # -----------------------------
    # DISCLAIMER
    # -----------------------------
    disclaimer = """
    <font size=9 color="grey">
    This report is generated automatically using AI-assisted analysis.
    It is intended to support clinical evaluation and should not
    replace professional medical diagnosis.
    </font>
    """

    elements.append(
        Paragraph(
            disclaimer,
            normal,
        )
    )

    # Build PDF
    doc.build(elements)

    pdf_bytes = buf.getvalue()
    buf.close()

    return base64.b64encode(
        pdf_bytes
    ).decode("utf-8")