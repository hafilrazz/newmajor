from typing import Optional


def generate_ai_report_text(
    predicted_stage: str,
    confidence_score: float,
    risk_score: int,
    clinician_notes: str = "",
    patient_name: str = "",
    patient_age: Optional[int] = None,
    patient_gender: str = "",
    patient_id: str = "",
) -> str:
    """
    Generate a structured, professional AI report in plain text format.

    Enriched with patient demographics when available; gracefully handles
    missing optional fields.
    """

    confidence_pct = round(confidence_score * 100, 1)

    # Risk interpretation with severity marker
    if risk_score < 30:
        risk_label = "Low"
    elif risk_score < 60:
        risk_label = "Moderate"
    else:
        risk_label = "High"

    notes = (
        clinician_notes.strip()
        if clinician_notes.strip()
        else "No clinician notes provided."
    )

    # Build demographics line
    demo_parts = []
    if patient_age is not None:
        demo_parts.append(f"{patient_age} years")
    if patient_gender:
        demo_parts.append(str(patient_gender).capitalize())
    demographics = " · ".join(demo_parts) if demo_parts else "—"

    rule = "=" * 75
    thin = "-" * 75

    report = f"""{rule}
  ALZHEIMER'S MRI AI DIAGNOSTIC REPORT
  NeuroLens · AI-assisted neuroimaging
{rule}

PATIENT & EXAMINATION
{thin}
  Patient name    : {patient_name or "—"}
  Demographics    : {demographics}
  Patient ID      : {patient_id or "—"}

AI ANALYSIS SUMMARY
{thin}
  Predicted stage : {predicted_stage}
  Model confidence: {confidence_pct}%
  Estimated risk  : {risk_label} ({risk_score}/100)

INTERPRETATION
{thin}
This assessment was generated from MRI-derived image features. The predicted
stage reflects the model's estimated classification based on observed imaging
patterns, and the confidence score represents model certainty for this
prediction.

The risk score estimates relative progression likelihood and should be
interpreted alongside a full clinical evaluation.

CLINICAL NOTES
{thin}
{notes}

RECOMMENDED NEXT STEPS
{thin}
  1. Correlate findings with a neurological examination
  2. Consider cognitive assessment if clinically indicated
  3. Compare with prior imaging studies where available
  4. Schedule specialist review when appropriate

{rule}
DISCLAIMER
{thin}
This report is generated using AI-assisted analysis and is intended to support
clinical decision-making. It is not a standalone medical diagnosis and must be
reviewed by a qualified clinician.
{rule}"""

    return report.strip()