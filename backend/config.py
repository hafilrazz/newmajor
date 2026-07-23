import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"

@dataclass(frozen=True)
class Settings:
    MONGODB_URI: str
    MONGODB_DB: str

    FLASK_PORT: int
    FLASK_DEBUG: bool
    FLASK_USE_RELOADER: bool
    CORS_ORIGINS: str

    MODEL_PATH: str

    EMAIL_SMTP_HOST: str
    EMAIL_SMTP_PORT: int
    EMAIL_SMTP_USER: str
    EMAIL_SMTP_PASSWORD: str
    EMAIL_FROM: str
    EMAIL_SMTP_STARTTLS: bool
    EMAIL_SMTP_SSL: bool


def _get_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def get_settings() -> Settings:
    # Re-load .env on each read so a backend restart is not required after editing .env
    # (also overrides stale Windows USER/Machine EMAIL_* variables).
    if _ENV_PATH.exists():
        load_dotenv(_ENV_PATH, override=True)

    return Settings(
        MONGODB_URI=os.getenv("MONGODB_URI", "mongodb://localhost:27017"),
        MONGODB_DB=os.getenv("MONGODB_DB", "alzheimers"),

        FLASK_PORT=int(os.getenv("FLASK_PORT", "5000")),
        FLASK_DEBUG=_get_bool("FLASK_DEBUG", True),
        # PyTorch lazy-imports touch site-packages files; Flask's watchdog reloader
        # treats that as a code change and restarts mid-request (ConnectionReset 10054).
        FLASK_USE_RELOADER=_get_bool("FLASK_USE_RELOADER", False),
        CORS_ORIGINS=os.getenv("CORS_ORIGINS", "http://localhost:8501"),

        MODEL_PATH=os.getenv("MODEL_PATH", "./models/model.pth"),

        EMAIL_SMTP_HOST=os.getenv("EMAIL_SMTP_HOST", ""),
        EMAIL_SMTP_PORT=int(os.getenv("EMAIL_SMTP_PORT", "1025")),
        EMAIL_SMTP_USER=os.getenv("EMAIL_SMTP_USER", ""),
        EMAIL_SMTP_PASSWORD=os.getenv("EMAIL_SMTP_PASSWORD", ""),
        EMAIL_FROM=os.getenv("EMAIL_FROM", ""),
        EMAIL_SMTP_STARTTLS=_get_bool(
            "EMAIL_SMTP_STARTTLS",
            default=os.getenv("EMAIL_SMTP_PORT", "1025") == "587",
        ),
        EMAIL_SMTP_SSL=_get_bool(
            "EMAIL_SMTP_SSL",
            default=os.getenv("EMAIL_SMTP_PORT", "1025") == "465",
        ),
    )
