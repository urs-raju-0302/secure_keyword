from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Set secrets before app imports settings
os.environ["JWT_SECRET"] = "test-jwt-secret-key-at-least-32-chars-long!!"
os.environ["MASTER_KEY"] = "test-master-key-at-least-32-characters-long!!"
os.environ["DATABASE_URL"] = "sqlite+pysqlite://"
os.environ["STORAGE_PROVIDER"] = "local"
os.environ["LOCAL_STORAGE_PATH"] = "./data/test_storage"
os.environ["ENVIRONMENT"] = "test"
os.environ["CORS_ORIGINS"] = "http://test"
os.environ["SEED_ADMIN_PASSWORD"] = "AdminPass123!"
os.environ["SEED_USER_PASSWORD"] = "UserPass1234!"

from app.config.settings import get_settings

get_settings.cache_clear()

from app.db import Base, get_db
from app.main import create_app
from app.models import User, UserRole
from app.security.password import hash_password
from app.services.key_management_service import KeyManagementService
from app.storage import get_storage_provider


@pytest.fixture()
def engine():
    eng = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture()
def db(engine) -> Generator[Session, None, None]:
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    settings = get_settings()
    kms = KeyManagementService(session, settings)
    kms.ensure_bootstrap_keys()
    session.commit()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(engine, tmp_path) -> Generator[TestClient, None, None]:
    os.environ["LOCAL_STORAGE_PATH"] = str(tmp_path / "storage")
    get_storage_provider.cache_clear()
    get_settings.cache_clear()

    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        session = TestingSession()
        try:
            # ensure keys
            KeyManagementService(session, get_settings()).ensure_bootstrap_keys()
            session.commit()
            yield session
        finally:
            session.close()

    app = create_app()
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    get_storage_provider.cache_clear()


@pytest.fixture()
def user_tokens(client: TestClient) -> dict:
    email = "alice@example.com"
    password = "SecurePass12"
    r = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code == 201
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return r.json()


@pytest.fixture()
def other_user_tokens(client: TestClient) -> dict:
    email = "bob@example.com"
    password = "SecurePass34"
    client.post("/api/v1/auth/register", json={"email": email, "password": password})
    r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return r.json()


@pytest.fixture()
def admin_tokens(client: TestClient, engine) -> dict:
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSession()
    admin = User(
        email="admin@example.com",
        password_hash=hash_password("AdminPass123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    session.add(admin)
    session.commit()
    session.close()
    r = client.post("/api/v1/auth/login", json={"email": "admin@example.com", "password": "AdminPass123!"})
    assert r.status_code == 200
    return r.json()


def auth_header(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}
