#!/usr/bin/env python3
"""Generate cryptographically secure development secrets. Do not commit output."""

from __future__ import annotations

import secrets
import sys


def main() -> None:
    print("# Paste into .env (never commit):")
    print(f"JWT_SECRET={secrets.token_urlsafe(48)}")
    print(f"MASTER_KEY={secrets.token_urlsafe(48)}")
    print(f"POSTGRES_PASSWORD={secrets.token_urlsafe(24)}")
    print(f"MINIO_SECRET_KEY={secrets.token_urlsafe(24)}")
    print(
        "DATABASE_URL=postgresql+psycopg2://securekw:"
        f"<POSTGRES_PASSWORD>@postgres:5432/secure_keyword",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
