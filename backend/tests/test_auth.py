from tests.conftest import auth_header


def test_register_login_me(client):
    r = client.post(
        "/api/v1/auth/register",
        json={"email": "carol@example.com", "password": "SecurePass99"},
    )
    assert r.status_code == 201
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": "wrong-password"},
    )
    assert r.status_code == 401
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": "SecurePass99"},
    )
    assert r.status_code == 200
    tokens = r.json()
    r = client.get("/api/v1/auth/me", headers=auth_header(tokens))
    assert r.status_code == 200
    assert r.json()["email"] == "carol@example.com"


def test_refresh_rotation(client, user_tokens):
    old_refresh = user_tokens["refresh_token"]
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 200
    new = r.json()
    # Old refresh should be revoked
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert r.status_code == 401
    r = client.post("/api/v1/auth/refresh", json={"refresh_token": new["refresh_token"]})
    assert r.status_code == 200


def test_invalid_jwt(client):
    r = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"})
    assert r.status_code == 401
