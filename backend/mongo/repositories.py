from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from bson import ObjectId


JsonLike = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PatientRepository:
    def __init__(self, db):
        self.db = db
        self.patients = db["patients"]
        self.predictions = db["prediction_history"]
        self.reports = db["reports"]

    @staticmethod
    def _jsonify(value: Any) -> Any:
        """
        Convert MongoDB-specific types (ObjectId, datetimes, etc.) into JSON-serializable forms.
        """
        if value is None:
            return None

        if isinstance(value, ObjectId):
            return str(value)

        # datetime-like
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except Exception:
                pass

        if isinstance(value, dict):
            return {k: PatientRepository._jsonify(v) for k, v in value.items()}

        if isinstance(value, list):
            return [PatientRepository._jsonify(v) for v in value]

        return value

    def create_patient(self, name: str, age: int, gender: str = "", email: str = "") -> Dict[str, Any]:
        doc = {
            "name": name,
            "age": age,
            "gender": gender,
            "email": email,
            "created_at": _utcnow(),
        }
        res = self.patients.insert_one(doc)
        payload = {
            "patient_id": res.inserted_id,
            "name": name,
            "age": age,
            "gender": gender,
            "email": email,
            "created_at": doc["created_at"],
        }
        return self._jsonify(payload)

    def get_patient_email(self, patient_id: str) -> Optional[str]:
        try:
            oid = ObjectId(patient_id)
        except Exception:
            return None
        doc = self.patients.find_one({"_id": oid}, {"email": 1})
        if not doc:
            return None
        return (doc.get("email") or "").strip() or None

    def get_patient(self, patient_id: str) -> Optional[Dict[str, Any]]:
        """Return a patient document (JSON-safe) or None."""
        try:
            oid = ObjectId(patient_id)
        except Exception:
            return None
        doc = self.patients.find_one({"_id": oid})
        return self._jsonify(doc) if doc else None

    def get_prediction_history(self, patient_id: str, modality: Optional[str] = None) -> List[Dict[str, Any]]:
        query: Dict[str, Any] = {"patient_id": patient_id}
        if modality:
            query["modality"] = modality.lower().strip()
        cursor = self.predictions.find(query).sort("created_at", -1)
        out: List[Dict[str, Any]] = []
        for item in cursor:
            item["_id"] = item.get("_id")
            out.append(self._jsonify(item))
        return out

    def upsert_prediction_history(
        self,
        patient_id: str,
        predicted_stage: str,
        confidence_score: float,
        risk_score: int,
        gradcam_image_base64: str,
        clinical_notes: str = "",
        patient_email: str = "",
        modality: str = "mri",
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        doc = {
            "patient_id": patient_id,
            "patient_email": patient_email,
            "modality": (modality or "mri").lower().strip(),
            "predicted_stage": predicted_stage,
            "confidence_score": confidence_score,
            "risk_score": risk_score,
            "gradcam_image_base64": gradcam_image_base64,
            "clinical_notes": clinical_notes,
            "created_at": _utcnow(),
        }
        if extra_data:
            doc["extra_data"] = self._jsonify(extra_data)
        res = self.predictions.insert_one(doc)
        return str(res.inserted_id)

    def save_report(
        self,
        patient_id: str,
        prediction_id: Optional[str],
        report_text: str,
        pdf_base64: str,
        clinician_notes: str = "",
        report_id: Optional[str] = None,
    ) -> str:
        doc = {
            "patient_id": patient_id,
            "prediction_id": prediction_id,
            "report_text": report_text,
            "pdf_base64": pdf_base64,
            "clinician_notes": clinician_notes,
            "created_at": _utcnow(),
        }
        if report_id:
            try:
                doc["_id"] = ObjectId(report_id)
            except Exception:
                pass
        res = self.reports.insert_one(doc)
        return str(res.inserted_id)

    def get_reports_for_patient(self, patient_id: str) -> List[Dict[str, Any]]:
        cursor = self.reports.find({"patient_id": patient_id}).sort("created_at", -1)
        out: List[Dict[str, Any]] = []
        for item in cursor:
            item["_id"] = item.get("_id")
            out.append(self._jsonify(item))
        return out
