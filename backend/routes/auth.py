from flask import Blueprint, jsonify, request

from backend.mongo.client import get_mongo
from backend.mongo.user_repository import UserRepository

bp = Blueprint("auth", __name__)


def _repo() -> UserRepository:
    _, db = get_mongo()
    return UserRepository(db)


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    try:
        user = _repo().create_user(
            full_name=str(data.get("full_name") or ""),
            email=str(data.get("email") or ""),
            username=str(data.get("username") or ""),
            password=str(data.get("password") or ""),
        )
    except ValueError as error:
        return jsonify({"error": str(error)}), 400
    except Exception:
        return jsonify({"error": "Could not register user. Please try again."}), 500

    return jsonify({"user": user, "message": "Registration successful."}), 201


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username") or "").strip()
    password = str(data.get("password") or "")

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 400

    try:
        user = _repo().authenticate(username=username, password=password)
    except Exception:
        return jsonify({"error": "Could not sign in. Please try again."}), 500

    if not user:
        return jsonify({"error": "Invalid username or password."}), 401

    return jsonify({"user": user, "message": "Login successful."})
