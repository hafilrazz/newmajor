"""User accounts stored in MongoDB (with local file backup for offline/fallback mode)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from bson import ObjectId
from werkzeug.security import check_password_hash, generate_password_hash

# Survives process restarts when Mongo is unavailable (mongomock fallback).
_USERS_FILE = Path(
    os.getenv(
        "USERS_DATA_PATH",
        str(Path(__file__).resolve().parent.parent.parent / "data" / "users.json"),
    )
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _json_safe(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, ObjectId):
        return str(value)
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            return str(value)
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


class UserRepository:
    def __init__(self, db):
        self.db = db
        self.users = db["users"]
        self._hydrate_from_file_if_empty()
        self._ensure_indexes()

    def _ensure_indexes(self) -> None:
        try:
            self.users.create_index("username", unique=True)
            self.users.create_index("email", unique=True)
        except Exception:
            # mongomock / older backends may not support indexes the same way
            pass

    def _hydrate_from_file_if_empty(self) -> None:
        """Load durable users into the active DB if the collection is empty."""
        try:
            if self.users.count_documents({}) > 0:
                return
        except Exception:
            return

        if not _USERS_FILE.exists():
            return

        try:
            payload = json.loads(_USERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return

        if not isinstance(payload, list):
            return

        for item in payload:
            if not isinstance(item, dict):
                continue
            doc = dict(item)
            raw_id = doc.pop("_id", None) or doc.pop("user_id", None)
            if raw_id:
                try:
                    doc["_id"] = ObjectId(str(raw_id))
                except Exception:
                    doc["_id"] = str(raw_id)
            # Avoid unique collisions if partially loaded
            username = (doc.get("username") or "").strip().lower()
            if not username:
                continue
            if self.users.find_one({"username": username}):
                continue
            doc["username"] = username
            self.users.insert_one(doc)

    def _persist_to_file(self) -> None:
        """Mirror all users to disk so accounts survive backend restarts."""
        try:
            _USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
            docs = []
            for item in self.users.find({}):
                docs.append(_json_safe(item))
            _USERS_FILE.write_text(
                json.dumps(docs, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except Exception:
            # File persistence is best-effort; Mongo remains source of truth when available.
            pass

    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        username = (username or "").strip().lower()
        if not username:
            return None
        return self.users.find_one({"username": username})

    def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        email = (email or "").strip().lower()
        if not email:
            return None
        return self.users.find_one({"email": email})

    def create_user(
        self,
        *,
        full_name: str,
        email: str,
        username: str,
        password: str,
    ) -> Dict[str, Any]:
        username_norm = (username or "").strip().lower()
        email_norm = (email or "").strip().lower()
        full_name = (full_name or "").strip()

        if not full_name:
            raise ValueError("Full name is required.")
        if not email_norm or "@" not in email_norm:
            raise ValueError("A valid email is required.")
        if not username_norm:
            raise ValueError("Username is required.")
        if len(password or "") < 4:
            raise ValueError("Password must be at least 4 characters.")

        if self.find_by_username(username_norm):
            raise ValueError("That username is already registered. Please sign in.")
        if self.find_by_email(email_norm):
            raise ValueError("That email is already registered. Please sign in.")

        doc = {
            "full_name": full_name,
            "email": email_norm,
            "username": username_norm,
            "password_hash": generate_password_hash(password),
            "role": "user",
            "created_at": _utcnow(),
        }
        res = self.users.insert_one(doc)
        self._persist_to_file()

        return {
            "user_id": str(res.inserted_id),
            "full_name": full_name,
            "email": email_norm,
            "username": username_norm,
            "role": "user",
        }

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        user = self.find_by_username(username)
        if not user:
            return None
        if not check_password_hash(user.get("password_hash") or "", password or ""):
            return None
        return {
            "user_id": str(user.get("_id")),
            "full_name": user.get("full_name") or "",
            "email": user.get("email") or "",
            "username": user.get("username") or "",
            "role": user.get("role") or "user",
        }
