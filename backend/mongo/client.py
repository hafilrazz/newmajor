from typing import Tuple

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from backend.config import get_settings

_client: MongoClient | None = None
_using_fallback: bool = False


def is_using_fallback() -> bool:
    """True when real MongoDB is unreachable and in-memory storage is active."""
    return _using_fallback


def get_mongo() -> Tuple[object, object]:
    """
    Returns (client, db).

    Uses a real MongoDB connection when available. If MongoDB is down or not
    installed, falls back to an in-memory mongomock database so local demos
    still work (data is lost when the process exits).
    """
    global _client, _using_fallback
    settings = get_settings()

    if _client is None:
        try:
            candidate = MongoClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=2000,
                connectTimeoutMS=2000,
                socketTimeoutMS=10000,
            )
            # Fail fast if the server is not reachable.
            candidate.admin.command("ping")
            _client = candidate
            _using_fallback = False
        except (PyMongoError, Exception):
            import mongomock

            _client = mongomock.MongoClient()
            _using_fallback = True

    db = _client[settings.MONGODB_DB]
    return _client, db
