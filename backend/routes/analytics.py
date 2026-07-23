from flask import Blueprint, jsonify
from backend.mongo.client import get_mongo

bp = Blueprint("analytics", __name__)

@bp.get("/stage-distribution")
def stage_distribution():
    _, db = get_mongo()
    predictions = db["prediction_history"]

    pipeline = [
        {"$group": {"_id": "$predicted_stage", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    rows = list(predictions.aggregate(pipeline))

    # Ensure stable ordering/keys
    dist = [{"stage": r.get("_id", "Unknown"), "count": int(r.get("count", 0))} for r in rows]
    return jsonify({"distribution": dist})

@bp.get("/risk-trend")
def risk_trend():
    # Scaffold: returns last N records with patient_id, created_at, risk_score.
    _, db = get_mongo()
    predictions = db["prediction_history"]

    cursor = predictions.find({}).sort("created_at", -1).limit(50)
    out = []
    for item in cursor:
        item["_id"] = str(item.get("_id"))
        if "created_at" in item and hasattr(item["created_at"], "isoformat"):
            item["created_at"] = item["created_at"].isoformat()
        out.append({
            "patient_id": item.get("patient_id"),
            "created_at": item.get("created_at"),
            "risk_score": item.get("risk_score"),
            "predicted_stage": item.get("predicted_stage"),
        })

    return jsonify({"trend": out})
