from typing import Optional


def generate_ai_report_text(
    predicted_stage: str,
    confidence_score: float,
    risk_score: int,
    clinician_notes: str = "",
) -> str:
    """
    Generate structured AI report text.
    """

    confidence_pct = round(
        confidence_score * 100,
        1,
    )

    # Risk interpretation
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

    report = f"""
AI ANALYSIS SUMMARY

Predicted Stage
{predicted_stage}

Confidence Score
{confidence_pct}%

Estimated Risk Level
{risk_label} ({risk_score}/100)


INTERPRETATION

This assessment was generated from MRI-derived image features.

The predicted stage indicates the model's estimated classification based on observed imaging patterns.

Confidence score represents model certainty for this prediction.

Risk score estimates relative progression likelihood and should be interpreted alongside clinical evaluation.


CLINICAL NOTES

{notes}


RECOMMENDED NEXT STEPS

• Correlate with neurological examination

• Consider cognitive assessment if clinically indicated

• Compare with prior imaging studies

• Schedule specialist review when appropriate


DISCLAIMER

This report is AI-assisted and intended to support clinical decision-making.
It is not a standalone medical diagnosis.
"""

    return report.strip()