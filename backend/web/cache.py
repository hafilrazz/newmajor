"""Filesystem cache for large UI payloads (images) — avoids cookie session limits.

Provides strict namespace isolation by modality ('mri', 'ct', 'clinical')
so that MRI, CT, and Clinical predictions never overwrite or alter each other.
"""

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


def save_prediction(payload: Dict[str, Any], modality: str = "mri") -> None:
    """Persist prediction without giant base64 blobs in the cookie session, isolated by modality."""
    mod = (modality or "mri").lower().strip()
    slim = dict(payload or {})
    grad = slim.pop("gradcam_image_base64", "") or ""

    save_text(f"gradcam_{mod}.b64", grad)
    session[f"last_prediction_{mod}"] = slim
    session[f"has_gradcam_{mod}"] = bool(grad)

    # Backwards-compatibility for existing MRI code that reads session['last_prediction']
    if mod == "mri":
        save_text("gradcam.b64", grad)
        session["last_prediction"] = slim
        session["has_gradcam"] = bool(grad)


def load_prediction(modality: str = "mri") -> Optional[Dict[str, Any]]:
    """Load cached prediction payload for a specific modality."""
    mod = (modality or "mri").lower().strip()
    pred = session.get(f"last_prediction_{mod}")
    if not pred and mod == "mri":
        pred = session.get("last_prediction")

    if not pred:
        return None

    out = dict(pred)
    grad = load_text(f"gradcam_{mod}.b64")
    if not grad and mod == "mri":
        grad = load_text("gradcam.b64")
    out["gradcam_image_base64"] = grad
    return out


def save_scan_image(b64: str, modality: str = "mri") -> None:
    """Save raw uploaded scan image base64 for side-by-side display."""
    mod = (modality or "mri").lower().strip()
    save_text(f"{mod}_image.b64", b64 or "")
    if mod == "mri":
        save_text("mri.b64", b64 or "")


def load_scan_image(modality: str = "mri") -> str:
    """Load raw uploaded scan image base64."""
    mod = (modality or "mri").lower().strip()
    img = load_text(f"{mod}_image.b64")
    if not img and mod == "mri":
        img = load_text("mri.b64")
    return img


def save_mri_image(b64: str) -> None:
    save_scan_image(b64, modality="mri")


def load_mri_image() -> str:
    return load_scan_image(modality="mri")


def save_ct_image(b64: str) -> None:
    save_scan_image(b64, modality="ct")


def load_ct_image() -> str:
    return load_scan_image(modality="ct")


def save_report(report_id: str, report_text: str, pdf_b64: str) -> None:
    session["last_report_id"] = report_id
    session["last_report_text"] = report_text
    save_text("report.pdf.b64", pdf_b64 or "")


def load_report_pdf() -> str:
    return load_text("report.pdf.b64")
