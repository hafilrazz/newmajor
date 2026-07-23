import base64
import os
import tempfile
from typing import Any, Dict, List, Optional

import yagmail

from backend.config import get_settings

# Bump when changing email logic (shown on /api/debug/env-email).
EMAIL_SENDER_VERSION = "2"


def _normalize_smtp_password(password: str) -> str:
    return password.replace(" ", "").strip()


def _gmail_auth_hint(exc: Exception) -> Optional[str]:
    msg = str(exc).lower()
    if "535" in msg or "badcredentials" in msg.replace(" ", "") or "username and password not accepted" in msg:
        return (
            "Gmail rejected the login. Use a 16-character App Password (not your normal Gmail password): "
            "https://myaccount.google.com/apppasswords — or switch to local test SMTP (Mailpit) in .env."
        )
    return None


def _build_yagmail_client(settings) -> yagmail.SMTP:
    host = (settings.EMAIL_SMTP_HOST or "").strip()
    if not host:
        raise ValueError("EMAIL_SMTP_HOST is not set")

    port = int(settings.EMAIL_SMTP_PORT)
    password = _normalize_smtp_password(settings.EMAIL_SMTP_PASSWORD)
    user = (settings.EMAIL_SMTP_USER or "").strip()

    # yagmail defaults host to smtp.gmail.com — always pass user first, host explicitly.
    return yagmail.SMTP(
        user,
        password,
        host=host,
        port=port,
        smtp_starttls=settings.EMAIL_SMTP_STARTTLS,
        smtp_ssl=settings.EMAIL_SMTP_SSL,
    )


def send_email_smtp(
    to_email: str,
    subject: str,
    body_text: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    Send email via yagmail.

    Local test (Mailpit): docker compose up -d mailpit
      → view mail at http://localhost:8025
    """
    settings = get_settings()

    if not settings.EMAIL_SMTP_HOST or not settings.EMAIL_FROM:
        return "stub_email_not_configured"

    temp_paths: List[str] = []
    try:
        for att in attachments or []:
            filename = att.get("filename", "attachment.pdf")
            b64 = att.get("base64", "")
            if not b64:
                continue

            raw = base64.b64decode(b64)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[-1] or ".pdf")
            tmp.write(raw)
            tmp.flush()
            tmp.close()
            temp_paths.append(tmp.name)

        yag = _build_yagmail_client(settings)
        yag.send(
            to=to_email,
            subject=subject,
            contents=body_text or "",
            attachments=temp_paths if temp_paths else None,
        )

        return "email_sent"
    except Exception as e:
        return f"email_failed: {e}"
    finally:
        for p in temp_paths:
            try:
                os.remove(p)
            except Exception:
                pass


def send_email_smtp_detailed(
    to_email: str,
    subject: str,
    body_text: str,
    attachments: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    status = send_email_smtp(to_email, subject, body_text, attachments)
    if status == "email_sent":
        settings = get_settings()
        out: Dict[str, Any] = {"status": status}
        host = (settings.EMAIL_SMTP_HOST or "").lower()
        if settings.EMAIL_SMTP_PORT == 1025:
            out["test_inbox_url"] = "http://localhost:8025"
        elif "ethereal.email" in host:
            out["test_inbox_url"] = "https://ethereal.email"
        return out

    if status.startswith("email_failed:"):
        err_text = status[len("email_failed:") :].strip()
        out = {"status": "email_failed", "error": err_text}
        hint = _gmail_auth_hint(Exception(err_text))
        if hint:
            out["hint"] = hint
        return out

    return {"status": status}
