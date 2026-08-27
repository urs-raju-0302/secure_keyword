"""Idempotent seed of demo users. Passwords printed only in development logs once."""

from __future__ import annotations

import logging
import os
import secrets

from sqlalchemy import select

from app.config import get_settings
from app.db import SessionLocal
from app.models import User, UserRole
from app.security.password import hash_password
from app.services.key_management_service import KeyManagementService

logger = logging.getLogger("secure_keyword.seed")


def seed() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        kms = KeyManagementService(db, settings)
        kms.ensure_bootstrap_keys()

        admin = db.scalar(select(User).where(User.email == "admin@example.com"))
        if not admin:
            admin_pw = os.environ.get("SEED_ADMIN_PASSWORD") or secrets.token_urlsafe(12)
            admin = User(
                email="admin@example.com",
                password_hash=hash_password(admin_pw),
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            if settings.environment == "development":
                logger.info("Seeded admin@example.com password=%s", admin_pw)

        user = db.scalar(select(User).where(User.email == "user@example.com"))
        if not user:
            user_pw = os.environ.get("SEED_USER_PASSWORD") or secrets.token_urlsafe(12)
            user = User(
                email="user@example.com",
                password_hash=hash_password(user_pw),
                role=UserRole.USER,
                is_active=True,
            )
            db.add(user)
            if settings.environment == "development":
                logger.info("Seeded user@example.com password=%s", user_pw)

        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed()
