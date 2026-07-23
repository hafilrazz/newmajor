import os
import sys
from typing import Dict

from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# Ensure `backend/*` imports work when starting from repo root.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

_env_path = os.path.join(_REPO_ROOT, ".env")
if os.path.exists(_env_path):
    load_dotenv(_env_path, override=True)
else:
    load_dotenv(override=True)


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static",
    )

    # Session cookies for the professional web UI
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "neurolens-dev-secret-change-me")
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    # Allow larger session payloads (prediction / Grad-CAM previews)
    app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024

    cors_origins = os.getenv(
        "CORS_ORIGINS", "http://localhost:5000,http://localhost:8501"
    )
    CORS(app, resources={r"/api/*": {"origins": cors_origins}})

    # JSON API (unchanged capability surface)
    from backend.routes.prediction import bp as prediction_bp
    from backend.routes.patients import bp as patients_bp
    from backend.routes.reports import bp as reports_bp
    from backend.routes.analytics import bp as analytics_bp
    from backend.routes.auth import bp as auth_bp
    from backend.web.routes import bp as web_bp

    app.register_blueprint(prediction_bp, url_prefix="/api/predictions")
    app.register_blueprint(patients_bp, url_prefix="/api/patients")
    app.register_blueprint(reports_bp, url_prefix="/api/reports")
    app.register_blueprint(analytics_bp, url_prefix="/api/analytics")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(web_bp)

    @app.get("/health")
    def health():
        from backend.mongo.client import get_mongo, is_using_fallback

        db_status = "ok"
        try:
            get_mongo()
            if is_using_fallback():
                db_status = "fallback_memory"
        except Exception:
            db_status = "error"

        return {
            "status": "ok",
            "database": db_status,
            "ui": "flask",
        }

    @app.get("/api/debug/env-email")
    def debug_env_email():
        def present(name: str) -> Dict[str, object]:
            val = os.getenv(name, "")
            return {"present": bool(val), "length": len(val)}

        from backend.config import get_settings
        from backend.services import email_sender

        settings = get_settings()
        host = settings.EMAIL_SMTP_HOST or ""
        user = settings.EMAIL_SMTP_USER or ""

        return {
            "email_sender_version": getattr(
                email_sender, "EMAIL_SENDER_VERSION", "unknown"
            ),
            "env_path": _env_path,
            "env_path_exists": os.path.exists(_env_path),
            "EMAIL_SMTP_HOST": {**present("EMAIL_SMTP_HOST"), "value": host},
            "EMAIL_SMTP_PORT": {
                "present": True,
                "value": str(settings.EMAIL_SMTP_PORT),
            },
            "EMAIL_SMTP_USER": {**present("EMAIL_SMTP_USER"), "value": user},
            "EMAIL_SMTP_PASSWORD": present("EMAIL_SMTP_PASSWORD"),
            "EMAIL_FROM": {**present("EMAIL_FROM"), "value": settings.EMAIL_FROM},
            "using_gmail": "gmail.com" in host.lower(),
            "using_ethereal": "ethereal.email" in host.lower(),
        }

    return app


if __name__ == "__main__":
    from backend.config import get_settings

    settings = get_settings()
    app = create_app()
    print(
        f"NeuroLens Flask UI + API on http://127.0.0.1:{settings.FLASK_PORT}"
    )
    print(
        f"Email SMTP: {settings.EMAIL_SMTP_HOST}:{settings.EMAIL_SMTP_PORT} as {settings.EMAIL_SMTP_USER}"
    )
    app.run(
        host="0.0.0.0",
        port=settings.FLASK_PORT,
        debug=settings.FLASK_DEBUG,
        use_reloader=settings.FLASK_USE_RELOADER,
    )
