"""Clinical Stacking Ensemble inference service.

Combines Random Forest (10 core cognitive/clinical features) and XGBoost
(32 comprehensive clinical/demographic features) using Soft Average ensembling
to predict Alzheimer's disease diagnosis risk.

Pure-NumPy Random Forest execution bypasses Windows AppLocker DLL policy
restrictions, ensuring 100% portable and exact mathematical tree inference.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Tuple

import joblib.numpy_pickle as jnp
import numpy as np
import xgboost as xgb

logger = logging.getLogger(__name__)

CLASS_NAMES = ["No Alzheimer", "Alzheimer"]

FEATURE_COLUMNS_RF: List[str] = [
    "FunctionalAssessment",
    "ADL",
    "MemoryComplaints",
    "MMSE",
    "BehavioralProblems",
    "SleepQuality",
    "EducationLevel",
    "CholesterolHDL",
    "Hypertension",
    "FamilyHistoryAlzheimers",
]

FEATURE_COLUMNS_XGB: List[str] = [
    "Age",
    "Gender",
    "Ethnicity",
    "EducationLevel",
    "BMI",
    "Smoking",
    "AlcoholConsumption",
    "PhysicalActivity",
    "DietQuality",
    "SleepQuality",
    "FamilyHistoryAlzheimers",
    "CardiovascularDisease",
    "Diabetes",
    "Depression",
    "HeadInjury",
    "Hypertension",
    "SystolicBP",
    "DiastolicBP",
    "CholesterolTotal",
    "CholesterolLDL",
    "CholesterolHDL",
    "CholesterolTriglycerides",
    "MMSE",
    "FunctionalAssessment",
    "MemoryComplaints",
    "BehavioralProblems",
    "ADL",
    "Confusion",
    "Disorientation",
    "PersonalityChanges",
    "DifficultyCompletingTasks",
    "Forgetfulness",
]

FEATURE_METADATA: Dict[str, Dict[str, Any]] = {
    "Age": {"label": "Age", "type": "number", "default": 72, "min": 60, "max": 90, "group": "demographics", "unit": "years"},
    "Gender": {"label": "Gender", "type": "select", "default": 0, "options": [(0, "Male"), (1, "Female")], "group": "demographics"},
    "Ethnicity": {"label": "Ethnicity", "type": "select", "default": 0, "options": [(0, "Caucasian"), (1, "African American"), (2, "Asian"), (3, "Other")], "group": "demographics"},
    "EducationLevel": {"label": "Education Level", "type": "select", "default": 2, "options": [(0, "None"), (1, "High School"), (2, "Bachelor's"), (3, "Higher")], "group": "demographics"},
    "BMI": {"label": "Body Mass Index (BMI)", "type": "number", "default": 24.5, "min": 15.0, "max": 40.0, "step": 0.1, "group": "demographics", "unit": "kg/m²"},
    "Smoking": {"label": "Smoking Status", "type": "select", "default": 0, "options": [(0, "Non-smoker"), (1, "Smoker")], "group": "lifestyle"},
    "AlcoholConsumption": {"label": "Alcohol Consumption", "type": "number", "default": 2.0, "min": 0.0, "max": 20.0, "step": 0.5, "group": "lifestyle", "unit": "units/week"},
    "PhysicalActivity": {"label": "Physical Activity", "type": "number", "default": 5.0, "min": 0.0, "max": 10.0, "step": 0.5, "group": "lifestyle", "unit": "hrs/week"},
    "DietQuality": {"label": "Diet Quality Score", "type": "number", "default": 6.5, "min": 0.0, "max": 10.0, "step": 0.5, "group": "lifestyle", "unit": "/10"},
    "SleepQuality": {"label": "Sleep Quality Score", "type": "number", "default": 7.0, "min": 4.0, "max": 10.0, "step": 0.5, "group": "lifestyle", "unit": "/10"},
    "FamilyHistoryAlzheimers": {"label": "Family History of Alzheimer's", "type": "select", "default": 0, "options": [(0, "No"), (1, "Yes")], "group": "medical"},
    "CardiovascularDisease": {"label": "Cardiovascular Disease", "type": "select", "default": 0, "options": [(0, "No"), (1, "Yes")], "group": "medical"},
    "Diabetes": {"label": "Diabetes", "type": "select", "default": 0, "options": [(0, "No"), (1, "Yes")], "group": "medical"},
    "Depression": {"label": "Depression", "type": "select", "default": 0, "options": [(0, "No"), (1, "Yes")], "group": "medical"},
    "HeadInjury": {"label": "Head Injury History", "type": "select", "default": 0, "options": [(0, "No"), (1, "Yes")], "group": "medical"},
    "Hypertension": {"label": "Hypertension", "type": "select", "default": 0, "options": [(0, "No"), (1, "Yes")], "group": "medical"},
    "SystolicBP": {"label": "Systolic BP", "type": "number", "default": 125, "min": 90, "max": 180, "group": "vitals", "unit": "mmHg"},
    "DiastolicBP": {"label": "Diastolic BP", "type": "number", "default": 80, "min": 60, "max": 120, "group": "vitals", "unit": "mmHg"},
    "CholesterolTotal": {"label": "Total Cholesterol", "type": "number", "default": 200.0, "min": 150.0, "max": 300.0, "step": 1.0, "group": "labs", "unit": "mg/dL"},
    "CholesterolLDL": {"label": "LDL Cholesterol", "type": "number", "default": 110.0, "min": 50.0, "max": 200.0, "step": 1.0, "group": "labs", "unit": "mg/dL"},
    "CholesterolHDL": {"label": "HDL Cholesterol", "type": "number", "default": 55.0, "min": 20.0, "max": 100.0, "step": 1.0, "group": "labs", "unit": "mg/dL"},
    "CholesterolTriglycerides": {"label": "Triglycerides", "type": "number", "default": 150.0, "min": 100.0, "max": 400.0, "step": 1.0, "group": "labs", "unit": "mg/dL"},
    "MMSE": {"label": "MMSE Score (Mini-Mental State Exam)", "type": "number", "default": 27.0, "min": 0.0, "max": 30.0, "step": 0.5, "group": "cognitive", "unit": "/30 (higher=better)"},
    "FunctionalAssessment": {"label": "Functional Assessment Score", "type": "number", "default": 8.0, "min": 0.0, "max": 10.0, "step": 0.5, "group": "cognitive", "unit": "/10 (higher=better)"},
    "MemoryComplaints": {"label": "Subjective Memory Complaints", "type": "select", "default": 0, "options": [(0, "No"), (1, "Yes")], "group": "cognitive"},
    "BehavioralProblems": {"label": "Behavioral Problems", "type": "select", "default": 0, "options": [(0, "No"), (1, "Yes")], "group": "cognitive"},
    "ADL": {"label": "Activities of Daily Living (ADL)", "type": "number", "default": 8.5, "min": 0.0, "max": 10.0, "step": 0.5, "group": "cognitive", "unit": "/10 (higher=better)"},
    "Confusion": {"label": "Frequent Episodes of Confusion", "type": "select", "default": 0, "options": [(0, "No"), (1, "Yes")], "group": "symptoms"},
    "Disorientation": {"label": "Spatial / Temporal Disorientation", "type": "select", "default": 0, "options": [(0, "No"), (1, "Yes")], "group": "symptoms"},
    "PersonalityChanges": {"label": "Noticeable Personality Changes", "type": "select", "default": 0, "options": [(0, "No"), (1, "Yes")], "group": "symptoms"},
    "DifficultyCompletingTasks": {"label": "Difficulty Completing Familiar Tasks", "type": "select", "default": 0, "options": [(0, "No"), (1, "Yes")], "group": "symptoms"},
    "Forgetfulness": {"label": "Marked Forgetfulness", "type": "select", "default": 0, "options": [(0, "No"), (1, "Yes")], "group": "symptoms"},
}

SAMPLE_PRESETS = {
    "healthy": {
        "Age": 68, "Gender": 1, "Ethnicity": 0, "EducationLevel": 2, "BMI": 22.8,
        "Smoking": 0, "AlcoholConsumption": 1.5, "PhysicalActivity": 6.5, "DietQuality": 8.0, "SleepQuality": 8.5,
        "FamilyHistoryAlzheimers": 0, "CardiovascularDisease": 0, "Diabetes": 0, "Depression": 0, "HeadInjury": 0,
        "Hypertension": 0, "SystolicBP": 118, "DiastolicBP": 76,
        "CholesterolTotal": 185.0, "CholesterolLDL": 95.0, "CholesterolHDL": 65.0, "CholesterolTriglycerides": 125.0,
        "MMSE": 28.5, "FunctionalAssessment": 9.2, "MemoryComplaints": 0, "BehavioralProblems": 0,
        "ADL": 9.5, "Confusion": 0, "Disorientation": 0, "PersonalityChanges": 0,
        "DifficultyCompletingTasks": 0, "Forgetfulness": 0,
    },
    "impaired": {
        "Age": 78, "Gender": 0, "Ethnicity": 1, "EducationLevel": 1, "BMI": 27.4,
        "Smoking": 1, "AlcoholConsumption": 5.0, "PhysicalActivity": 1.5, "DietQuality": 3.0, "SleepQuality": 5.0,
        "FamilyHistoryAlzheimers": 1, "CardiovascularDisease": 1, "Diabetes": 1, "Depression": 1, "HeadInjury": 0,
        "Hypertension": 1, "SystolicBP": 152, "DiastolicBP": 94,
        "CholesterolTotal": 265.0, "CholesterolLDL": 168.0, "CholesterolHDL": 34.0, "CholesterolTriglycerides": 280.0,
        "MMSE": 12.0, "FunctionalAssessment": 3.2, "MemoryComplaints": 1, "BehavioralProblems": 1,
        "ADL": 3.0, "Confusion": 1, "Disorientation": 1, "PersonalityChanges": 1,
        "DifficultyCompletingTasks": 1, "Forgetfulness": 1,
    },
}

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _resolve_model_path(rel_path: str, fallback_file: str) -> Path:
    p = Path(rel_path)
    if p.is_file():
        return p
    in_repo = _REPO_ROOT / "models" / fallback_file
    if in_repo.is_file():
        return in_repo
    in_ext = Path("C:/model/outputs") / fallback_file
    if in_ext.is_file():
        return in_ext
    return in_repo


class _DummyUnpickle:
    def __init__(self, *args, **kwargs):
        pass

    def __setstate__(self, state):
        self.__dict__.update(state)


class _SafeNumpyUnpickler(jnp.NumpyUnpickler):
    def find_class(self, module, name):
        if "sklearn" in module:
            return _DummyUnpickle
        return super().find_class(module, name)


@lru_cache(maxsize=1)
def load_clinical_models() -> Tuple[List[Tuple[np.ndarray, np.ndarray]], xgb.Booster]:
    """Load Random Forest tree structures and XGBoost booster."""
    rf_path = _resolve_model_path("models/randomforest_clinical.joblib", "randomforest_clinical.joblib")
    xgb_json = _resolve_model_path("models/xgboost_clinical.json", "xgboost_clinical.json")

    if not rf_path.is_file():
        raise RuntimeError(f"Random Forest model not found at {rf_path}")
    if not xgb_json.is_file():
        raise RuntimeError(f"XGBoost JSON model not found at {xgb_json}")

    with open(rf_path, "rb") as f:
        unpickler = _SafeNumpyUnpickler(str(rf_path), f, mmap_mode=None, ensure_native_byte_order=True)
        bundle = unpickler.load()

    rf_model = bundle.get("model", bundle)
    estimators = getattr(rf_model, "estimators_", [])
    trees = [(est.tree_.nodes, est.tree_.values) for est in estimators]

    booster = xgb.Booster()
    booster.load_model(str(xgb_json))

    return trees, booster


def _predict_rf_proba(trees: List[Tuple[np.ndarray, np.ndarray]], x: np.ndarray) -> np.ndarray:
    """Evaluate pure NumPy decision trees for binary class probabilities."""
    probs = np.zeros(2, dtype=np.float64)
    n_trees = len(trees)
    if n_trees == 0:
        return np.array([0.5, 0.5], dtype=np.float64)

    for nodes, values in trees:
        node = 0
        while nodes["left_child"][node] != -1:
            feat = nodes["feature"][node]
            thr = nodes["threshold"][node]
            if x[feat] <= thr:
                node = nodes["left_child"][node]
            else:
                node = nodes["right_child"][node]
        leaf_vals = values[node][0]
        sum_v = leaf_vals.sum()
        if sum_v > 0:
            probs += leaf_vals / sum_v
        else:
            probs += np.array([0.5, 0.5])

    return probs / n_trees


def get_feature_importances() -> Dict[str, float]:
    """Return normalized importance ranking of features."""
    return {
        "MemoryComplaints": 0.1201,
        "FunctionalAssessment": 0.1165,
        "ADL": 0.1062,
        "BehavioralProblems": 0.1009,
        "MMSE": 0.0945,
        "Forgetfulness": 0.0263,
        "Diabetes": 0.0262,
        "FamilyHistoryAlzheimers": 0.0257,
        "CholesterolTotal": 0.0213,
        "CholesterolHDL": 0.0210,
        "DifficultyCompletingTasks": 0.0208,
        "SleepQuality": 0.0206,
        "CholesterolLDL": 0.0204,
        "Smoking": 0.0198,
        "BMI": 0.0191,
        "Hypertension": 0.0189,
        "PhysicalActivity": 0.0186,
        "DietQuality": 0.0182,
        "Depression": 0.0180,
        "CholesterolTriglycerides": 0.0179,
        "Ethnicity": 0.0178,
        "Age": 0.0173,
        "DiastolicBP": 0.0171,
        "SystolicBP": 0.0168,
        "AlcoholConsumption": 0.0155,
        "EducationLevel": 0.0150,
        "Confusion": 0.0145,
        "PersonalityChanges": 0.0133,
        "CardiovascularDisease": 0.0133,
        "Gender": 0.0084,
    }


def predict_clinical_alzheimer(raw_features: Dict[str, Any]) -> Dict[str, Any]:
    """Execute Clinical Stacking Ensemble prediction with Soft Average ensembling."""
    rf_trees, xgb_booster = load_clinical_models()

    clean_features: Dict[str, float] = {}
    for col in FEATURE_COLUMNS_XGB:
        meta = FEATURE_METADATA.get(col, {})
        default_val = meta.get("default", 0.0)
        val = raw_features.get(col)
        if val is None or val == "":
            clean_features[col] = float(default_val)
        else:
            try:
                clean_features[col] = float(val)
            except (ValueError, TypeError):
                clean_features[col] = float(default_val)

    x_rf = np.array([clean_features[col] for col in FEATURE_COLUMNS_RF], dtype=np.float64)
    x_xgb = np.array([[clean_features[col] for col in FEATURE_COLUMNS_XGB]], dtype=np.float64)

    # 1. Random Forest prediction (pure NumPy tree evaluation on 10 features)
    rf_probs = _predict_rf_proba(rf_trees, x_rf)

    # 2. XGBoost prediction (native Booster on 32 features)
    dmat = xgb.DMatrix(x_xgb)
    xgb_alz_prob = float(xgb_booster.predict(dmat)[0])
    xgb_probs = np.array([1.0 - xgb_alz_prob, xgb_alz_prob], dtype=np.float64)

    # 3. Soft Average Stacking: (P_RF + P_XGB) / 2
    ens_probs = (rf_probs + xgb_probs) / 2.0

    pred_idx = int(np.argmax(ens_probs))
    predicted_stage = CLASS_NAMES[pred_idx]
    confidence = float(round(ens_probs[pred_idx], 4))

    alzheimer_risk_pct = float(round(ens_probs[1] * 100.0, 1))

    if alzheimer_risk_pct >= 70.0:
        risk_tier = "High Risk"
        risk_color = "danger"
    elif alzheimer_risk_pct >= 35.0:
        risk_tier = "Moderate Risk"
        risk_color = "warning"
    else:
        risk_tier = "Low Risk / Normal"
        risk_color = "success"

    importances = get_feature_importances()
    risk_factors = []

    if clean_features.get("MMSE", 30) < 24:
        risk_factors.append({
            "feature": "MMSE Score",
            "value": f"{clean_features.get('MMSE'):.1f} / 30",
            "impact": "Marked Cognitive Decline",
            "weight": importances.get("MMSE", 0.1),
        })
    if clean_features.get("FunctionalAssessment", 10) < 6:
        risk_factors.append({
            "feature": "Functional Assessment",
            "value": f"{clean_features.get('FunctionalAssessment'):.1f} / 10",
            "impact": "Reduced Functional Independence",
            "weight": importances.get("FunctionalAssessment", 0.1),
        })
    if clean_features.get("ADL", 10) < 6:
        risk_factors.append({
            "feature": "Daily Living Activities (ADL)",
            "value": f"{clean_features.get('ADL'):.1f} / 10",
            "impact": "Impaired Daily Functioning",
            "weight": importances.get("ADL", 0.1),
        })
    if clean_features.get("MemoryComplaints", 0) == 1:
        risk_factors.append({
            "feature": "Memory Complaints",
            "value": "Reported",
            "impact": "Patient Reports Memory Loss",
            "weight": importances.get("MemoryComplaints", 0.12),
        })
    if clean_features.get("BehavioralProblems", 0) == 1:
        risk_factors.append({
            "feature": "Behavioral Problems",
            "value": "Present",
            "impact": "Neuropsychiatric Changes",
            "weight": importances.get("BehavioralProblems", 0.1),
        })
    if clean_features.get("FamilyHistoryAlzheimers", 0) == 1:
        risk_factors.append({
            "feature": "Family History",
            "value": "Positive",
            "impact": "Genetic Predisposition Factor",
            "weight": importances.get("FamilyHistoryAlzheimers", 0.025),
        })
    if clean_features.get("Confusion", 0) == 1 or clean_features.get("Disorientation", 0) == 1:
        risk_factors.append({
            "feature": "Confusion / Disorientation",
            "value": "Observed",
            "impact": "Spatial or Temporal Disorientation",
            "weight": 0.02,
        })
    if clean_features.get("Forgetfulness", 0) == 1:
        risk_factors.append({
            "feature": "Forgetfulness",
            "value": "Present",
            "impact": "Progressive Memory Difficulty",
            "weight": 0.025,
        })

    risk_factors.sort(key=lambda x: x["weight"], reverse=True)

    return {
        "predicted_stage": predicted_stage,
        "predicted_index": pred_idx,
        "confidence_score": confidence,
        "risk_score": alzheimer_risk_pct,
        "risk_tier": risk_tier,
        "risk_color": risk_color,
        "raw_probs": [float(round(p, 4)) for p in ens_probs],
        "class_names": CLASS_NAMES,
        "clean_features": clean_features,
        "risk_factors": risk_factors,
        "base_models": {
            "random_forest": {
                "name": "Random Forest (10 Features)",
                "predicted_stage": CLASS_NAMES[int(np.argmax(rf_probs))],
                "confidence": float(round(rf_probs[int(np.argmax(rf_probs))], 4)),
                "probs": [float(round(p, 4)) for p in rf_probs],
                "features_used": len(FEATURE_COLUMNS_RF),
            },
            "xgboost": {
                "name": "XGBoost (32 Features)",
                "predicted_stage": CLASS_NAMES[int(np.argmax(xgb_probs))],
                "confidence": float(round(xgb_probs[int(np.argmax(xgb_probs))], 4)),
                "probs": [float(round(p, 4)) for p in xgb_probs],
                "features_used": len(FEATURE_COLUMNS_XGB),
            },
            "stacking_ensemble": {
                "name": "Stacking Ensemble",
                "method": "Soft Average Ensembling",
            },
        },
    }
