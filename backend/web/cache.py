"""Filesystem cache for large UI payloads (images) — avoids cookie session limits."""

from __future__ import annotations

import secrets
from pathlib import Path
from typing import Any, Dict, Optional

from flask import session

_REPO = Path(__file__).resolve().parent.parent.parent
_CACHE_ROOT = _REPO / "data" / "ui_cache"


def _ensure_id() -> str:
    cid = session.get("cache_id")
    if not cid:
        cid = secrets.token_hex(16)
        session["cache_id"] = cid
    return cid


def _dir() -> Path:
    path = _CACHE_ROOT / _ensure_id()
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_text(name: str, data: str) -> None:
    (_dir() / name).write_text(data or "", encoding="utf-8")


def load_text(name: str) -> str:
    path = _CACHE_ROOT / session.get("cache_id", "") / name
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def save_prediction(payload: Dict[str, Any]) -> None:
    """Persist prediction without giant base64 blobs in the cookie session."""
    slim = dict(payload or {})
    grad = slim.pop("gradcam_image_base64", "") or ""
    save_text("gradcam.b64", grad)
    # Keep a lightweight copy in session
    session["last_prediction"] = slim
    session["has_gradcam"] = bool(grad)


def load_prediction() -> Optional[Dict[str, Any]]:
    pred = session.get("last_prediction")
    if not pred:
        return None
    out = dict(pred)
    out["gradcam_image_base64"] = load_text("gradcam.b64")
    return out


def save_mri_image(b64: str) -> None:
    save_text("mri.b64", b64 or "")


def load_mri_image() -> str:
    return load_text("mri.b64")


def save_report(report_id: str, report_text: str, pdf_b64: str) -> None:
    session["last_report_id"] = report_id
    session["last_report_text"] = report_text
    # PDF can also be large
    save_text("report.pdf.b64", pdf_b64 or "")


def load_report_pdf() -> str:
    return load_text("report.pdf.b64")
