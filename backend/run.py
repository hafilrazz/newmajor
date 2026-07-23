"""Launch the Flask API.

Run from repo root or from this folder:

    python backend/run.py
    python run.py
"""

from __future__ import annotations

import os
import sys

# Allow `import backend...` when this file is executed as a script.
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from backend.app import create_app  # noqa: E402
from backend.config import get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()
    app = create_app()
    print(
        f"Email SMTP: {settings.EMAIL_SMTP_HOST}:{settings.EMAIL_SMTP_PORT} "
        f"as {settings.EMAIL_SMTP_USER}"
    )
    app.run(
        host="0.0.0.0",
        port=settings.FLASK_PORT,
        debug=settings.FLASK_DEBUG,
        use_reloader=settings.FLASK_USE_RELOADER,
    )


if __name__ == "__main__":
    main()
