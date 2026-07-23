import os
from typing import Any, Dict, Optional

import requests


class ApiClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def health(self) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/health", timeout=10)
        r.raise_for_status()
        return r.json()

    def register_user(
        self,
        full_name: str,
        email: str,
        username: str,
        password: str,
    ) -> Dict[str, Any]:
        r = requests.post(
            f"{self.base_url}/api/auth/register",
            json={
                "full_name": full_name,
                "email": email,
                "username": username,
                "password": password,
            },
            timeout=30,
        )
        if not r.ok:
            self._raise_api_error(r, "Registration failed")
        return r.json()

    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        r = requests.post(
            f"{self.base_url}/api/auth/login",
            json={"username": username, "password": password},
            timeout=30,
        )
        if not r.ok:
            self._raise_api_error(r, "Login failed")
        return r.json()

    def register_patient(
        self, name: str, age: int, gender: str = "", email: str = ""
    ) -> Dict[str, Any]:
        r = requests.post(
            f"{self.base_url}/api/patients/register",
            json={"name": name, "age": age, "gender": gender, "email": email},
            timeout=30,
        )
        if not r.ok:
            self._raise_api_error(r, "Patient registration failed")
        return r.json()

    def get_patient_history(self, patient_id: str) -> Dict[str, Any]:
        r = requests.get(
            f"{self.base_url}/api/patients/{patient_id}/history", timeout=30
        )
        if not r.ok:
            self._raise_api_error(r, "Could not load patient history")
        return r.json()

    def predict_mri(
        self,
        mri_file_bytes: bytes,
        mri_filename: str,
        patient_id: str = "",
        patient_email: str = "",
        clinical_notes: str = "",
    ) -> Dict[str, Any]:
        lower = (mri_filename or "").lower()
        if lower.endswith(".png"):
            mime = "image/png"
        elif lower.endswith(".jpg") or lower.endswith(".jpeg"):
            mime = "image/jpeg"
        else:
            mime = "application/octet-stream"

        files = {
            "mri_file": (mri_filename or "scan.png", mri_file_bytes, mime),
        }
        data = {
            "patient_id": patient_id,
            "patient_email": patient_email,
            "clinical_notes": clinical_notes,
        }
        r = requests.post(
            f"{self.base_url}/api/predictions", files=files, data=data, timeout=180
        )
        if not r.ok:
            self._raise_api_error(r, "Prediction failed")
        return r.json()

    def generate_ai_report(
        self,
        patient_id: str,
        prediction: Dict[str, Any],
        clinician_notes: str = "",
    ) -> Dict[str, Any]:
        payload = {
            "patient_id": patient_id,
            "prediction": prediction,
            "clinician_notes": clinician_notes,
        }
        r = requests.post(
            f"{self.base_url}/api/reports/generate", json=payload, timeout=60
        )
        if not r.ok:
            self._raise_api_error(r, "Report generation failed")
        return r.json()

    def email_report(self, report_id: str, recipient_email: str) -> Dict[str, Any]:
        payload = {"report_id": report_id, "recipient_email": recipient_email}
        r = requests.post(
            f"{self.base_url}/api/reports/email", json=payload, timeout=60
        )
        data = r.json() if r.content else {}
        if r.ok:
            return data
        if isinstance(data, dict) and data.get("status"):
            return data
        self._raise_api_error(r, "Email failed")
        return data

    def stage_distribution(self) -> Dict[str, Any]:
        r = requests.get(
            f"{self.base_url}/api/analytics/stage-distribution", timeout=20
        )
        if not r.ok:
            self._raise_api_error(r, "Analytics unavailable")
        return r.json()

    def risk_trend(self) -> Dict[str, Any]:
        r = requests.get(f"{self.base_url}/api/analytics/risk-trend", timeout=20)
        if not r.ok:
            self._raise_api_error(r, "Analytics unavailable")
        return r.json()

    @staticmethod
    def _raise_api_error(response: requests.Response, fallback: str) -> None:
        try:
            response_data = response.json() if response.content else {}
        except Exception:
            response_data = {}
        if isinstance(response_data, dict) and response_data.get("error"):
            reasons = response_data.get("reasons") or []
            detail = f" {' '.join(str(r) for r in reasons)}" if reasons else ""
            raise RuntimeError(f"{response_data['error']}{detail}")
        response.raise_for_status()
        raise RuntimeError(fallback)


_default_client: Optional[ApiClient] = None


def get_api_client() -> ApiClient:
    global _default_client
    if _default_client is not None:
        return _default_client

    base_url = os.getenv("API_BASE_URL", "http://localhost:5000").rstrip("/")
    _default_client = ApiClient(base_url)
    return _default_client
