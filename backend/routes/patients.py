from flask import Blueprint, jsonify, request
from backend.mongo.client import get_mongo
from backend.mongo.repositories import PatientRepository

bp = Blueprint("patients", __name__)

def _repo() -> PatientRepository:
    client, db = get_mongo()
    return PatientRepository(db)

@bp.post("/register")
def register_patient():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    age = data.get("age")
    gender = (data.get("gender") or "").strip()
    email = (data.get("email") or "").strip()

    if not name:
        return jsonify({"error": "name is required"}), 400
    if age is None:
        return jsonify({"error": "age is required"}), 400
    if not email:
        return jsonify({"error": "email is required"}), 400
    if "@" not in email or "." not in email.split("@")[-1]:
        return jsonify({"error": "email must be a valid address"}), 400

    repo = _repo()
    patient = repo.create_patient(name=name, age=int(age), gender=gender, email=email)
    return jsonify({"patient": patient}), 201

@bp.get("/<patient_id>/history")
def patient_history(patient_id: str):
    repo = _repo()
    history = repo.get_prediction_history(patient_id)
    return jsonify({"patient_id": patient_id, "history": history})
