"""Server-rendered professional UI routes (Flask + Jinja)."""

from __future__ import annotations

import base64
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Optional

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from PIL import Image

from backend.web import cache as ui_cache

bp = Blueprint("web", __name__)


def _year() -> int:
    return datetime.now().year


def login_required(view: Callable):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            flash("Please sign in to continue.", "info")
            return redirect(url_for("web.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


def admin_required(view: Callable):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            flash("Please sign in to continue.", "info")
            return redirect(url_for("web.login", next=request.path))
        if session.get("role") != "admin":
            flash("This area is available to administrators only.", "error")
            return redirect(url_for("web.dashboard"))
        return view(*args, **kwargs)

    return wrapped


def _ctx(**extra):
    data = {"year": _year()}
    data.update(extra)
    return data


# ── Public marketing ──────────────────────────────────────────


@bp.get("/")
def home():
    return render_template("pages/home.html", **_ctx())


@bp.get("/about")
def about():
    return render_template("pages/about.html", **_ctx())


@bp.get("/contact")
def contact():
    return render_template("pages/contact.html", **_ctx())


# ── Auth ──────────────────────────────────────────────────────


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("web.dashboard"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        mode = request.form.get("mode") or "user"

        if mode == "admin":
            if username == "admin" and password == "123456":
                theme = session.get("ui_theme", "light")
                session.clear()
                session.update(
                    {
                        "authenticated": True,
                        "role": "admin",
                        "username": "admin",
                        "full_name": "Administrator",
                        "email": "",
                        "user_id": "admin",
                        "ui_theme": theme,
                    }
                )
                flash("Welcome back, Administrator.", "success")
                return redirect(url_for("web.dashboard"))
            flash("Invalid administrator credentials.", "error")
        else:
            if not username or not password:
                flash("Enter username and password.", "error")
            else:
                try:
                    from backend.mongo.client import get_mongo
                    from backend.mongo.user_repository import UserRepository

                    _, db = get_mongo()
                    user = UserRepository(db).authenticate(username, password)
                    if not user:
                        flash("Invalid username or password.", "error")
                    else:
                        theme = session.get("ui_theme", "light")
                        session.clear()
                        session.update(
                            {
                                "authenticated": True,
                                "role": user.get("role") or "user",
                                "username": user.get("username", ""),
                                "full_name": user.get("full_name", ""),
                                "email": user.get("email", ""),
                                "user_id": user.get("user_id", ""),
                                "ui_theme": theme,
                            }
                        )
                        flash("Signed in successfully.", "success")
                        nxt = request.args.get("next") or url_for("web.dashboard")
                        return redirect(nxt)
                except Exception as err:
                    flash(f"Could not sign in: {err}", "error")

    return render_template("auth/login.html", **_ctx())


@bp.route("/register", methods=["GET", "POST"])
def register():
    if session.get("authenticated"):
        return redirect(url_for("web.dashboard"))

    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip()
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        if not full_name:
            flash("Enter your full name.", "error")
        elif not email or "@" not in email:
            flash("Enter a valid email.", "error")
        elif not username:
            flash("Enter a username.", "error")
        elif len(password) < 4:
            flash("Password must be at least 4 characters.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        else:
            try:
                from backend.mongo.client import get_mongo
                from backend.mongo.user_repository import UserRepository

                _, db = get_mongo()
                UserRepository(db).create_user(
                    full_name=full_name,
                    email=email,
                    username=username,
                    password=password,
                )
                flash("Account created. Please sign in.", "success")
                return redirect(url_for("web.login"))
            except ValueError as err:
                flash(str(err), "error")
            except Exception:
                flash("Could not register. Please try again.", "error")

    return render_template("auth/register.html", **_ctx())


@bp.get("/logout")
def logout():
    theme = session.get("ui_theme", "light")
    session.clear()
    session["ui_theme"] = theme
    flash("You have been signed out.", "info")
    return redirect(url_for("web.home"))


# ── Workspace pages ───────────────────────────────────────────


@bp.get("/app")
@login_required
def dashboard():
    dist, trend = [], []
    try:
        from backend.mongo.client import get_mongo

        _, db = get_mongo()
        predictions = db["prediction_history"]
        pipeline = [
            {"$group": {"_id": "$predicted_stage", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        rows = list(predictions.aggregate(pipeline))
        dist = [
            {"stage": r.get("_id", "Unknown"), "count": int(r.get("count", 0))}
            for r in rows
        ]
        cursor = predictions.find({}).sort("created_at", -1).limit(50)
        for item in cursor:
            created = item.get("created_at")
            if hasattr(created, "isoformat"):
                created = created.isoformat()
            trend.append(
                {
                    "patient_id": item.get("patient_id"),
                    "created_at": created,
                    "risk_score": item.get("risk_score") or 0,
                    "predicted_stage": item.get("predicted_stage"),
                }
            )
    except Exception:
        pass

    total = sum(int(r["count"]) for r in dist)
    latest_risk = trend[0]["risk_score"] if trend else 0
    max_count = max((int(r["count"]) for r in dist), default=1) or 1
    risk_vals = [int(t.get("risk_score") or 0) for t in reversed(trend[:20])]
    max_risk = max(risk_vals) if risk_vals else 1

    return render_template(
        "app/dashboard.html",
        active="dashboard",
        dist=dist,
        trend=trend,
        total=total,
        stages=len(dist),
        latest_risk=latest_risk,
        max_count=max_count,
        risk_vals=risk_vals,
        max_risk=max_risk or 1,
        last_prediction=ui_cache.load_prediction(),
        **_ctx(),
    )


@bp.route("/app/patients", methods=["GET", "POST"])
@admin_required
def patients():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        age = request.form.get("age")
        gender = (request.form.get("gender") or "").strip()
        email = (request.form.get("email") or "").strip()
        if not name:
            flash("Full name is required.", "error")
        elif not email or "@" not in email:
            flash("Please enter a valid email address.", "error")
        else:
            try:
                from backend.mongo.client import get_mongo
                from backend.mongo.repositories import PatientRepository

                _, db = get_mongo()
                patient = PatientRepository(db).create_patient(
                    name=name, age=int(age or 0), gender=gender, email=email
                )
                session["active_patient_id"] = patient.get("patient_id", "")
                session["active_patient_email"] = patient.get("email", email)
                flash(
                    f"Patient created. ID: {patient.get('patient_id')}",
                    "success",
                )
                return redirect(url_for("web.mri"))
            except Exception as err:
                flash(f"Registration failed: {err}", "error")

    return render_template(
        "app/patients.html",
        active="patients",
        **_ctx(),
    )


@bp.route("/app/mri", methods=["GET", "POST"])
@admin_required
def mri():
    if request.method == "POST":
        patient_id = (request.form.get("patient_id") or "").strip()
        patient_email = (request.form.get("patient_email") or "").strip()
        clinical_notes = (request.form.get("clinical_notes") or "").strip()
        file = request.files.get("mri_file")

        if not file or not file.filename:
            flash("Please upload an MRI image.", "error")
        elif not patient_id:
            flash("Patient ID is required.", "error")
        elif not patient_email or "@" not in patient_email:
            flash("A valid patient email is required.", "error")
        else:
            try:
                from backend.services.predictor import (
                    ModelUnavailableError,
                    predict_stage_and_scores,
                )
                from backend.services.explainability import explain_prediction
                from backend.services.mri_validator import validate_mri_image

                file.stream.seek(0)
                img = Image.open(file.stream).convert("RGB")
                validation = validate_mri_image(img)
                if not validation.accepted:
                    flash(
                        "Upload rejected: image does not appear to be a compatible brain MRI. "
                        + " ".join(validation.reasons or []),
                        "error",
                    )
                else:
                    pred = predict_stage_and_scores(img)
                    gradcam_b64 = ""
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
                        pass

                    # Keep original for side-by-side
                    file.stream.seek(0)
                    raw = file.read()
                    mri_b64 = base64.b64encode(raw).decode("utf-8")

                    prediction_id = None
                    try:
                        from backend.mongo.client import get_mongo
                        from backend.mongo.repositories import PatientRepository

                        _, db = get_mongo()
                        risk_for_db = float(pred["risk_score"])
                        prediction_id = PatientRepository(db).upsert_prediction_history(
                            patient_id=patient_id,
                            patient_email=patient_email,
                            predicted_stage=pred["predicted_stage"],
                            confidence_score=float(pred["confidence_score"]),
                            risk_score=int(round(risk_for_db)),
                            gradcam_image_base64=gradcam_b64,
                            clinical_notes=clinical_notes,
                        )
                    except Exception:
                        prediction_id = None

                    payload = {
                        "patient_id": patient_id,
                        "patient_email": patient_email,
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
                            "history_saved": bool(prediction_id),
                            "gradcam_available": bool(gradcam_b64),
                        },
                    }
                    session["active_patient_id"] = patient_id
                    session["active_patient_email"] = patient_email
                    ui_cache.save_prediction(payload)
                    ui_cache.save_mri_image(mri_b64)
                    flash("Analysis complete.", "success")
                    return redirect(url_for("web.mri"))
            except ModelUnavailableError as err:
                flash(str(err), "error")
            except Exception as err:
                flash(f"Prediction failed: {err}", "error")

    # Prefill
    patient_id = session.get("active_patient_id", "")
    patient_email = session.get("active_patient_email", "")
    result = ui_cache.load_prediction()
    class_probs = []
    if result:
        names = result.get("class_names") or []
        probs = result.get("raw_probs") or []
        class_probs = sorted(
            zip(names, probs), key=lambda x: float(x[1]), reverse=True
        )

    return render_template(
        "app/mri.html",
        active="mri",
        patient_id=patient_id,
        patient_email=patient_email,
        result=result,
        class_probs=class_probs,
        **_ctx(),
    )


@bp.get("/app/gradcam")
@admin_required
def gradcam():
    prediction = ui_cache.load_prediction() or {}
    return render_template(
        "app/gradcam.html",
        active="gradcam",
        prediction=prediction,
        gradcam=prediction.get("gradcam_image_base64") or "",
        original=ui_cache.load_mri_image(),
        **_ctx(),
    )


@bp.route("/app/assessment", methods=["GET", "POST"])
@admin_required
def assessment():
    if request.method == "POST":
        session["clinician_assessment"] = {
            "patient_id": (request.form.get("patient_id") or "").strip(),
            "symptoms": (request.form.get("symptoms") or "").strip(),
            "additional_findings": (
                request.form.get("additional_findings") or ""
            ).strip(),
            "cognitive_decline": int(request.form.get("cognitive_decline") or 5),
            "functional_impairment": int(
                request.form.get("functional_impairment") or 5
            ),
        }
        flash("Clinical assessment saved for report generation.", "success")
        return redirect(url_for("web.assessment"))

    return render_template(
        "app/assessment.html",
        active="assess",
        assessment=session.get("clinician_assessment") or {},
        patient_id=session.get("active_patient_id", ""),
        **_ctx(),
    )


@bp.route("/app/report", methods=["GET", "POST"])
@admin_required
def report():
    prediction = ui_cache.load_prediction()

    if request.method == "POST":
        action = request.form.get("action") or "generate"
        if action == "email":
            recipient = (request.form.get("recipient_email") or "").strip()
            rid = session.get("last_report_id") or ""
            if not recipient:
                flash("Recipient email is required.", "error")
            elif not rid:
                flash("Generate a report first.", "error")
            else:
                try:
                    from bson import ObjectId
                    from backend.mongo.client import get_mongo
                    from backend.mongo.repositories import PatientRepository
                    from backend.services.email_sender import send_email_smtp_detailed

                    _, db = get_mongo()
                    repo = PatientRepository(db)
                    rep = None
                    try:
                        rep = repo.reports.find_one({"_id": ObjectId(rid)})
                    except Exception:
                        rep = repo.reports.find_one({"report_id": rid})
                    if not rep:
                        flash("Report not found.", "error")
                    else:
                        result = send_email_smtp_detailed(
                            to_email=recipient,
                            subject="Alzheimer’s MRI AI Report",
                            body_text=rep.get("report_text", ""),
                            attachments=[
                                {
                                    "filename": f"alzheimer_report_{rid}.pdf",
                                    "base64": rep.get("pdf_base64", ""),
                                }
                            ],
                        )
                        if result.get("status") == "email_sent":
                            flash("Report emailed successfully.", "success")
                        else:
                            flash(
                                result.get("error")
                                or "Email could not be sent.",
                                "error",
                            )
                            if result.get("hint"):
                                flash(result["hint"], "info")
                except Exception as err:
                    flash(f"Email failed: {err}", "error")
        else:
            patient_id = (request.form.get("patient_id") or "").strip()
            notes = (request.form.get("clinician_notes") or "").strip()
            if not prediction:
                flash("Complete an MRI prediction first.", "error")
            elif not patient_id:
                flash("Patient ID is required.", "error")
            else:
                try:
                    from backend.mongo.client import get_mongo
                    from backend.mongo.repositories import PatientRepository
                    from backend.services.report_generator import generate_ai_report_text
                    from backend.services.pdf_generator import generate_pdf_base64

                    report_text = generate_ai_report_text(
                        predicted_stage=prediction.get("predicted_stage", "Unknown"),
                        confidence_score=float(
                            prediction.get("confidence_score") or 0
                        ),
                        risk_score=int(prediction.get("risk_score") or 0),
                        clinician_notes=notes,
                    )
                    pdf_b64 = generate_pdf_base64(
                        report_text=report_text,
                        patient_id=patient_id,
                        predicted_stage=prediction.get("predicted_stage", "Unknown"),
                    )
                    _, db = get_mongo()
                    report_id = PatientRepository(db).save_report(
                        patient_id=patient_id,
                        prediction_id=prediction.get("prediction_id"),
                        report_text=report_text,
                        pdf_base64=pdf_b64,
                        clinician_notes=notes,
                    )
                    ui_cache.save_report(report_id, report_text, pdf_b64)
                    flash("Report prepared successfully.", "success")
                except Exception as err:
                    flash(f"Report generation failed: {err}", "error")

        return redirect(url_for("web.report"))

    assessment = session.get("clinician_assessment") or {}
    default_notes = assessment.get("additional_findings") or ""

    return render_template(
        "app/report.html",
        active="report",
        prediction=prediction,
        report_text=session.get("last_report_text", ""),
        report_id=session.get("last_report_id", ""),
        pdf_b64=ui_cache.load_report_pdf(),
        patient_id=session.get("active_patient_id", ""),
        patient_email=session.get("active_patient_email", ""),
        default_notes=default_notes,
        **_ctx(),
    )


@bp.route("/app/history", methods=["GET", "POST"])
@admin_required
def history():
    history_rows = []
    patient_id = session.get("active_patient_id", "")
    if request.method == "POST":
        patient_id = (request.form.get("patient_id") or "").strip()
        if not patient_id:
            flash("Patient ID is required.", "error")
        else:
            try:
                from backend.mongo.client import get_mongo
                from backend.mongo.repositories import PatientRepository

                _, db = get_mongo()
                history_rows = PatientRepository(db).get_prediction_history(patient_id)
                if not history_rows:
                    flash("No assessments found for this patient.", "info")
            except Exception as err:
                flash(f"History could not be loaded: {err}", "error")

    risk_vals = [int(r.get("risk_score") or 0) for r in history_rows]
    max_risk = max(risk_vals) if risk_vals else 1

    # Sanitize for table (drop huge blobs)
    display_rows = []
    for row in history_rows:
        display_rows.append(
            {
                k: v
                for k, v in row.items()
                if k not in {"gradcam_image_base64", "pdf_base64"}
            }
        )

    return render_template(
        "app/history.html",
        active="history",
        patient_id=patient_id,
        rows=display_rows,
        risk_vals=risk_vals,
        max_risk=max_risk or 1,
        **_ctx(),
    )


@bp.get("/app/analytics")
@admin_required
def analytics():
    dist, trend = [], []
    try:
        from backend.mongo.client import get_mongo

        _, db = get_mongo()
        predictions = db["prediction_history"]
        pipeline = [
            {"$group": {"_id": "$predicted_stage", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
        ]
        dist = [
            {"stage": r.get("_id", "Unknown"), "count": int(r.get("count", 0))}
            for r in predictions.aggregate(pipeline)
        ]
        for item in predictions.find({}).sort("created_at", -1).limit(50):
            created = item.get("created_at")
            if hasattr(created, "isoformat"):
                created = created.isoformat()
            trend.append(
                {
                    "patient_id": item.get("patient_id"),
                    "created_at": created,
                    "risk_score": item.get("risk_score") or 0,
                    "predicted_stage": item.get("predicted_stage"),
                }
            )
    except Exception:
        pass

    max_count = max((int(r["count"]) for r in dist), default=1) or 1
    risk_vals = [int(t.get("risk_score") or 0) for t in reversed(trend[:24])]
    max_risk = max(risk_vals) if risk_vals else 1

    return render_template(
        "app/analytics.html",
        active="analytics",
        dist=dist,
        trend=trend,
        max_count=max_count,
        risk_vals=risk_vals,
        max_risk=max_risk or 1,
        **_ctx(),
    )


@bp.get("/app/settings")
@login_required
def settings():
    return render_template(
        "app/settings.html",
        active="settings",
        ui_theme=session.get("ui_theme", "light"),
        **_ctx(),
    )


@bp.route("/app/theme", methods=["GET", "POST"])
@login_required
def set_theme():
    """Switch light/dark mode. Supports GET links and POST forms (avoids Method Not Allowed)."""
    theme = (
        request.values.get("theme")
        or (request.get_json(silent=True) or {}).get("theme")
        or ""
    )
    theme = str(theme).strip().lower()
    if theme not in {"light", "dark"}:
        flash("Unknown theme selection.", "error")
        return redirect(request.referrer or url_for("web.settings"))

    session["ui_theme"] = theme
    flash(f"{'Dark' if theme == 'dark' else 'Light'} mode enabled.", "success")

    # Prefer returning to the page the user was on
    nxt = request.values.get("next") or request.referrer
    if nxt and nxt.startswith("/") and not nxt.startswith("//"):
        return redirect(nxt)
    if nxt and request.host_url and nxt.startswith(request.host_url):
        return redirect(nxt)
    return redirect(url_for("web.settings"))



@bp.get("/app/about")
@login_required
def about_app():
    return render_template("app/about.html", active="about", **_ctx())


@bp.get("/app/contact")
@login_required
def contact_app():
    return render_template("app/contact.html", active="contact", **_ctx())
