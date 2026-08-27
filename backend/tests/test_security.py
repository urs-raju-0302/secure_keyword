from io import BytesIO
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from app.models import Document
from app.storage import get_storage_provider
from tests.conftest import auth_header


def test_sql_injection_search_safe(client, user_tokens):
    headers = auth_header(user_tokens)
    payload = "' OR 1=1;--"
    r = client.post("/api/v1/search", headers=headers, json={"keyword": payload})
    assert r.status_code == 200
    assert r.json()["result_count"] == 0


def test_path_traversal_filename(client, user_tokens):
    headers = auth_header(user_tokens)
    files = {"file": ("../../etc/passwd.txt", BytesIO(b"traversal security test"), "text/plain")}
    r = client.post("/api/v1/documents", headers=headers, files=files)
    assert r.status_code == 201
    assert ".." not in r.json()["original_filename"]


def test_tampered_ciphertext_download_fails(client, user_tokens, engine):
    headers = auth_header(user_tokens)
    files = {"file": ("t.txt", BytesIO(b"integrity security"), "text/plain")}
    r = client.post("/api/v1/documents", headers=headers, files=files)
    doc_id = r.json()["id"]

    TestingSession = sessionmaker(bind=engine)
    session = TestingSession()
    doc = session.scalar(select(Document).where(Document.id == UUID(doc_id)))
    assert doc is not None
    storage = get_storage_provider()
    raw = bytearray(storage.get_object(doc.storage_key))
    raw[0] ^= 0xFF
    storage.put_object(doc.storage_key, bytes(raw))
    session.close()

    r = client.get(f"/api/v1/documents/{doc_id}/download", headers=headers)
    assert r.status_code == 500
    assert r.content != b"integrity security"


def test_search_key_rotation(client, admin_tokens, user_tokens):
    headers = auth_header(user_tokens)
    files = {"file": ("rot.txt", BytesIO(b"rotation security keyword"), "text/plain")}
    r = client.post("/api/v1/documents", headers=headers, files=files)
    assert r.status_code == 201

    r = client.post("/api/v1/search", headers=headers, json={"keyword": "security"})
    assert r.json()["result_count"] >= 1

    admin_h = auth_header(admin_tokens)
    r = client.post("/api/v1/keys/rotate/search", headers=admin_h)
    assert r.status_code == 200
    assert r.json()["documents_reindexed"] >= 1

    r = client.post("/api/v1/search", headers=headers, json={"keyword": "security"})
    assert r.status_code == 200
    assert r.json()["result_count"] >= 1


def test_admin_endpoint_requires_admin(client, user_tokens, admin_tokens):
    r = client.post("/api/v1/keys/reindex", headers=auth_header(user_tokens))
    assert r.status_code == 403
    r = client.post("/api/v1/keys/reindex", headers=auth_header(admin_tokens))
    assert r.status_code == 200
