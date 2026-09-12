from flask import Blueprint, jsonify, request
from PIL import Image

from backend.services.predictor import ModelUnavailableError, predict_stage_and_scores
from backend.services.explainability import explain_prediction
from backend.services.mri_validator import validate_mri_image

bp = Blueprint("prediction", __name__)

def _do_predict():
    """
    Expected multipart/form-data:
    - patient_id (optional but recommended for saving history later)
    - clinical_notes (optional)
    - mri_file (required): image file
    """
    try:
        if "mri_file" not in request.files:
            return jsonify({"error": "mri_file is required"}), 400

        mri_file = request.files["mri_file"]
        patient_id = request.form.get("patient_id", "").strip()
        patient_email = request.form.get("patient_email", "").strip()
        clinical_notes = request.form.get("clinical_notes", "").strip()

        try:
            # Ensure stream is at start (some clients re-read; multipart may leave offset).
            try:
                mri_file.stream.seek(0)
            except Exception:
                pass
            img = Image.open(mri_file.stream).convert("RGB")
        except Exception as e:
            return jsonify({"error": f"Invalid image: {str(e)}"}), 400

        validation = validate_mri_image(img)
        if not validation.accepted:
            return jsonify(
                {
                    "error": "Upload rejected: this image does not appear to be a compatible brain MRI scan.",
                    "code": "invalid_mri_image",
                    "reasons": validation.reasons,
                }
            ), 422

        try:
            pred = predict_stage_and_scores(img)
        except ModelUnavailableError as error:
            return jsonify({"error": str(error), "code": "model_unavailable"}), 503
        except Exception as error:
            # Surface a short reason so the UI tip is actionable without log diving.
            return jsonify(
                {
                    "error": f"The trained model could not complete prediction: {error}",
                    "code": "inference_failed",
                }
            ), 500

        explanation = None
        try:
            xai = explain_prediction(
                img,
                target_index=pred.get("predicted_index"),
                stage_name=pred.get("predicted_stage") or "",
            )
            gradcam_b64 = xai.get("gradcam_image_base64", "") or ""
            explanation = xai.get("explanation")
        except Exception:
            gradcam_b64 = ""
        gradcam_error = "" if gradcam_b64 else "Grad-CAM++ generation returned no image."

        if patient_id and not patient_email:
            try:
                from backend.mongo.client import get_mongo
                from backend.mongo.repositories import PatientRepository

                _, db = get_mongo()
                repo = PatientRepository(db)
                patient_email = repo.get_patient_email(patient_id) or ""
            except Exception:
                pass

        prediction_id = None
        if patient_id:
            # Save prediction to MongoDB history
            try:
                from backend.mongo.client import get_mongo
                from backend.mongo.repositories import PatientRepository

                _, db = get_mongo()
                repo = PatientRepository(db)
                # Keep one decimal for risk; storage field is numeric.
                risk_for_db = float(pred["risk_score"])
                prediction_id = repo.upsert_prediction_history(
                    patient_id=patient_id,
                    patient_email=patient_email,
                    predicted_stage=pred["predicted_stage"],
                    confidence_score=float(pred["confidence_score"]),
                    risk_score=int(round(risk_for_db)),
                    gradcam_image_base64=gradcam_b64,
                    clinical_notes=clinical_notes,
                )
            except Exception:
                # If DB fails, still return prediction response to avoid client connection abort
                prediction_id = None

        response = {
            "patient_id": patient_id or None,
            "patient_email": patient_email or None,
            "prediction_id": prediction_id,
            "predicted_stage": pred.get("predicted_stage"),
            "confidence_score": pred.get("confidence_score"),
            "risk_score": pred.get("risk_score"),
            "raw_probs": pred.get("raw_probs") or [],
            "class_names": [
                "Mild Impairment",
                "Moderate Impairment",
                "No Impairment",
                "Very Mild Impairment",
            ],
            "gradcam_image_base64": gradcam_b64,
            "explanation": explanation,
            "meta": {
                "input_format": getattr(mri_file, "mimetype", None),
                "clinical_notes_present": bool(clinical_notes),
                "model_inference": True,
                "gradcam_available": bool(gradcam_b64),
                "gradcam_error": gradcam_error,
                "mri_validation": "passed",
                "history_saved": bool(prediction_id),
            },
        }
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500

@bp.post("/predict")
def predict():
    return _do_predict()

# Backwards-compatible route: POST /api/predictions
@bp.post("")
def predict_root():
    return _do_predict()


@bp.post("/mri")
def predict_mri():
    return _do_predict()


@bp.post("/ct")
def predict_ct():
    """Run CT Stacking Ensemble prediction over brain CT scan."""
    try:
        from backend.services.ct_predictor import predict_ct_stage_and_scores

        file = request.files.get("ct_file") or request.files.get("mri_file")
        if not file:
            return jsonify({"error": "ct_file is required"}), 400

        patient_id = (request.form.get("patient_id") or "").strip()
        patient_email = (request.form.get("patient_email") or "").strip()
        clinical_notes = (request.form.get("clinical_notes") or "").strip()

        try:
            file.stream.seek(0)
            img = Image.open(file.stream).convert("RGB")
        except Exception as err:
            return jsonify({"error": f"Invalid image: {err}"}), 400

        res = predict_ct_stage_and_scores(img)

        if patient_id and not patient_email:
            try:
                from backend.mongo.client import get_mongo
                from backend.mongo.repositories import PatientRepository
                _, db = get_mongo()
                patient_email = PatientRepository(db).get_patient_email(patient_id) or ""
            except Exception:
                pass

        prediction_id = None
        if patient_id:
            try:
                from backend.mongo.client import get_mongo
                from backend.mongo.repositories import PatientRepository
                _, db = get_mongo()
                prediction_id = PatientRepository(db).upsert_prediction_history(
                    patient_id=patient_id,
                    patient_email=patient_email,
                    predicted_stage=res["predicted_stage"],
                    confidence_score=float(res["confidence_score"]),
                    risk_score=int(round(float(res["risk_score"]))),
                    gradcam_image_base64=res.get("gradcam_image_base64", ""),
                    clinical_notes=clinical_notes,
                    modality="ct",
                    extra_data={"base_models": res.get("base_models")},
                )
            except Exception:
                prediction_id = None

        res["patient_id"] = patient_id or None
        res["patient_email"] = patient_email or None
        res["prediction_id"] = prediction_id
        res["modality"] = "ct"
        return jsonify(res)
    except Exception as err:
        return jsonify({"error": f"CT Prediction failed: {str(err)}"}), 500


@bp.post("/clinical")
def predict_clinical():
    """Run Clinical Stacking Ensemble prediction (Random Forest + XGBoost) over clinical features."""
    try:
        from backend.services.clinical_predictor import predict_clinical_alzheimer

        data = request.get_json(silent=True) or request.form.to_dict() or {}
        patient_id = str(data.get("patient_id") or "").strip()
        patient_email = str(data.get("patient_email") or "").strip()
        clinical_notes = str(data.get("clinical_notes") or "").strip()

        features = data.get("features") if isinstance(data.get("features"), dict) else data

        res = predict_clinical_alzheimer(features)

        if patient_id and not patient_email:
            try:
                from backend.mongo.client import get_mongo
                from backend.mongo.repositories import PatientRepository
                _, db = get_mongo()
                patient_email = PatientRepository(db).get_patient_email(patient_id) or ""
            except Exception:
                pass

        prediction_id = None
        if patient_id:
            try:
                from backend.mongo.client import get_mongo
                from backend.mongo.repositories import PatientRepository
                _, db = get_mongo()
                prediction_id = PatientRepository(db).upsert_prediction_history(
                    patient_id=patient_id,
                    patient_email=patient_email,
                    predicted_stage=res["predicted_stage"],
                    confidence_score=float(res["confidence_score"]),
                    risk_score=int(round(float(res["risk_score"]))),
                    gradcam_image_base64="",
                    clinical_notes=clinical_notes,
                    modality="clinical",
                    extra_data={
                        "risk_tier": res.get("risk_tier"),
                        "base_models": res.get("base_models"),
                        "risk_factors": res.get("risk_factors"),
                    },
                )
            except Exception:
                prediction_id = None

        res["patient_id"] = patient_id or None
        res["patient_email"] = patient_email or None
        res["prediction_id"] = prediction_id
        res["modality"] = "clinical"
        return jsonify(res)
    except Exception as err:
        return jsonify({"error": f"Clinical Prediction failed: {str(err)}"}), 500
