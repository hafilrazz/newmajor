import base64
from flask import Blueprint, jsonify, request
from bson import ObjectId

from backend.mongo.client import get_mongo
from backend.mongo.repositories import PatientRepository
from backend.services.report_generator import generate_ai_report_text
from backend.services.pdf_generator import generate_pdf_base64
from backend.services.email_sender import send_email_smtp_detailed

bp = Blueprint("reports", __name__)

def _repo() -> PatientRepository:
    _, db = get_mongo()
    return PatientRepository(db)

@bp.post("/generate")
def generate_report():
    data = request.get_json(silent=True) or {}
    patient_id = str(data.get("patient_id", "")).strip()
    if not patient_id:
        return jsonify({"error": "patient_id is required"}), 400

    clinician_notes = str(data.get("clinician_notes", "")).strip()
    prediction = data.get("prediction") or {}

    predicted_stage = prediction.get("predicted_stage", "Unknown")
    confidence = float(prediction.get("confidence_score", 0.0))
    risk = int(prediction.get("risk_score", 0))

    report_text = generate_ai_report_text(
        predicted_stage=predicted_stage,
        confidence_score=confidence,
        risk_score=risk,
        clinician_notes=clinician_notes,
    )
    pdf_b64 = generate_pdf_base64(report_text=report_text, patient_id=patient_id, predicted_stage=predicted_stage)

    repo = _repo()
    report_id = repo.save_report(
        patient_id=patient_id,
        prediction_id=prediction.get("prediction_id"),
        report_text=report_text,
        pdf_base64=pdf_b64,
        clinician_notes=clinician_notes,
    )

    return jsonify({"report_id": report_id, "report_text": report_text, "pdf_base64": pdf_b64})

@bp.post("/email")
def email_report():
    data = request.get_json(silent=True) or {}
    report_id = str(data.get("report_id", "")).strip()
    recipient_email = str(data.get("recipient_email", "")).strip()

    if not report_id or not recipient_email:
        return jsonify({"error": "report_id and recipient_email are required"}), 400

    # Find report
    repo = _repo()
    reports_col = repo.reports

    # Reports are stored with Mongo _id (ObjectId). UI sends it as string.
    report = None
    try:
        report = reports_col.find_one({"_id": ObjectId(report_id)})
    except Exception:
        report = None

    if not report:
        # Fallback: some schemas may store a separate string field
        report = reports_col.find_one({"report_id": report_id})

    if not report:
        return jsonify({"error": "report not found"}), 404

    pdf_b64 = report.get("pdf_base64", "")
    report_text = report.get("report_text", "")

    result = send_email_smtp_detailed(
        to_email=recipient_email,
        subject="Alzheimer’s MRI AI Report",
        body_text=report_text,
        attachments=[{"filename": f"alzheimer_report_{report_id}.pdf", "base64": pdf_b64}],
    )

    if result.get("status") == "email_failed":
        return jsonify(result), 502

    return jsonify(result)
