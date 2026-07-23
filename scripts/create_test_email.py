"""
Create a disposable Ethereal test SMTP account and print .env lines.

Usage (from alzheimers-app/):
  python scripts/create_test_email.py
"""
from __future__ import annotations

import json
import sys

import requests


def main() -> int:
    r = requests.post(
        "https://api.nodemailer.com/user",
        json={"requestor": "alzheimers-app", "version": "1.0.0"},
        timeout=30,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "success":
        print(json.dumps(data, indent=2), file=sys.stderr)
        return 1

    user = data["user"]
    password = data["pass"]
    host = data["smtp"]["host"]
    port = data["smtp"]["port"]

    print("# Paste into alzheimers-app/.env")
    print(f"EMAIL_SMTP_HOST={host}")
    print(f"EMAIL_SMTP_PORT={port}")
    print(f"EMAIL_SMTP_USER={user}")
    print(f"EMAIL_SMTP_PASSWORD={password}")
    print(f"EMAIL_FROM={user}")
    print("EMAIL_SMTP_STARTTLS=1")
    print("EMAIL_SMTP_SSL=0")
    print()
    print(f"# View sent mail: {data.get('web', 'https://ethereal.email')}")
    print(f"# Login with user={user} pass={password}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
