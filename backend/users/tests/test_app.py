import os
import jwt
import pytest
from http.cookies import SimpleCookie
from datetime import datetime, timedelta, timezone

from users.app import app as flask_app, validate_email, validate_password
from users.model import db, User


def https_post(client, url, **kwargs):
    env = kwargs.pop("environ_overrides", {})
    env.update({"wsgi.url_scheme": "https"})
    return client.post(url, environ_overrides=env, **kwargs)


# ------------------------
# Unit tests
# ------------------------

@pytest.mark.unit
@pytest.mark.parametrize("email,ok", [
    ("a@b.co", True),
    ("user+tag@domain.io", True),
    ("  spaced@out.com ", True),
    ("no-at", False),
    ("bad@domain", False),
    (None, False),
    (123, False),
])
def test_validate_email(email, ok):
    assert validate_email(email) is ok


@pytest.mark.unit
@pytest.mark.parametrize("pw,ok", [
    ("123456", True),
    ("abcdef", True),
    ("short", False),
    (None, False),
    (123456, False),
])
def test_validate_password(pw, ok):
    assert validate_password(pw) is ok


@pytest.mark.unit
def test_user_json_and_repr_contract():
    u = User(username="bob", email="b@example.com", password_hash="hash")
    u.user_id = 7
    u.created_at = datetime(2024, 1, 2, 12, 0, 0)
    j = u.json()
    assert j == {
        "user_id": 7,
        "username": "bob",
        "email": "b@example.com",
        "created_at": "2024-01-02",
    }
    assert "<User 7 - bob>" in repr(u)


@pytest.mark.unit
def test_register_exception_path(client, monkeypatch):
    # force commit to fail -> 500 path
    def boom():
        raise RuntimeError("boom")
    monkeypatch.setattr(db.session, "commit", boom, raising=True)
    r = client.post("/register", json={"username": "x", "email": "x@x.com", "password": "abcdef"})
    assert r.status_code == 500
    assert "An error occurred" in r.get_json()["message"]


@pytest.mark.unit
def test_login_exception_path(client, monkeypatch, seed_user):
    # ensure route reaches password check
    u = seed_user
    def boom(*_, **__): raise RuntimeError("boom")
    # Patch where the app actually uses it
    monkeypatch.setattr("users.app.check_password_hash", boom, raising=True)

    r = client.post("/login", json={"email": u["email"], "password": u["password"]})
    assert r.status_code == 500
    assert "An error occurred" in r.get_json()["message"]


# ------------------------
# Integration tests
# ------------------------

@pytest.mark.integration
def test_register_success(client):
    payload = {"username": "newguy", "email": "new@example.com", "password": "secret123"}
    r = client.post("/register", json=payload)
    assert r.status_code == 201
    body = r.get_json()
    assert body["code"] == 201
    assert body["data"]["username"] == "newguy"
    assert body["data"]["email"] == "new@example.com"
    with flask_app.app_context():
        u = User.query.filter_by(email="new@example.com").first()
        assert u is not None
        assert u.password_hash != payload["password"]  # hashed


@pytest.mark.integration
def test_register_validation_and_conflict(client, seed_user):
    # missing required
    r = client.post("/register", json={"email": "only@email.com"})
    assert r.status_code == 400

    r = client.post("/register", json={"email": "only@email.com", "password": "abcdef"})
    assert r.status_code == 400

    r = client.post("/register", json={"email": "only@email.com", "password": "abcdef"})
    assert r.status_code == 400

    # bad email
    r = client.post("/register", json={"username": "x", "email": "bad", "password": "abcdef"})
    assert r.status_code == 400
    assert "Invalid email" in r.get_json()["message"]

    # short password
    r = client.post("/register", json={"username": "x", "email": "ok@ok.com", "password": "123"})
    assert r.status_code == 400
    assert "at least 6" in r.get_json()["message"]

    # duplicate email
    r = client.post("/register", json={"username": "dup", "email": "alice@example.com", "password": "abcdef"})
    assert r.status_code == 409


@pytest.mark.integration
def test_login_success_sets_tokens(client, seed_user):
    u = seed_user

    r = client.post("/login", json={"email": u["email"], "password": u["password"]})
    assert r.status_code == 200
    body = r.get_json()
    assert body["code"] == 200
    assert "access_token" in body

    # ---- decode & validate ACCESS token ----
    secret = os.environ["JWT_SECRET_KEY"]
    access = body["access_token"]
    access_claims = jwt.decode(
        access,
        secret,
        algorithms=["HS256"],
        options={"require": ["sub", "iat", "exp", "type"]},
    )
    assert access_claims["type"] == "access"
    assert access_claims["sub"] == str(u["user_id"])
    assert access_claims.get("name") == u["username"]

    now = datetime.now(timezone.utc).timestamp()
    assert access_claims["iat"] <= now < access_claims["exp"]
    assert (access_claims["exp"] - access_claims["iat"]) >= 60  # at least 1 min

    # ---- grab refresh token from Set-Cookie and decode ----
    set_cookie = r.headers.get("Set-Cookie", "")
    assert "refresh_token=" in set_cookie
    assert "Path=/refresh-token" in set_cookie

    jar = SimpleCookie()
    jar.load(set_cookie)
    refresh = jar["refresh_token"].value

    refresh_claims = jwt.decode(
        refresh,
        secret,
        algorithms=["HS256"],
        options={"require": ["sub", "iat", "exp", "type"]},
    )
    assert refresh_claims["type"] == "refresh"
    assert refresh_claims["sub"] == str(u["user_id"])
    assert refresh_claims.get("name") == u["username"]
    assert refresh_claims["exp"] > access_claims["exp"]


@pytest.mark.integration
def test_login_missing_or_invalid(client, seed_user):
    u = seed_user
    # missing fields
    r = client.post("/login", json={"email": u["email"]})
    assert r.status_code == 400

    r = client.post("/login", json={"password": u["password"]})
    assert r.status_code == 400

    # wrong password
    r = client.post("/login", json={"email": u["email"], "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.integration
def test_refresh_token_success_after_login(client, seed_user):
    u = seed_user

    # 1) Login -> capture initial refresh cookie + decode its exp
    r = client.post("/login", json={"email": u["email"], "password": u["password"]})
    assert r.status_code == 200
    login_cookie = r.headers.get("Set-Cookie", "")

    jar = SimpleCookie(); jar.load(login_cookie)
    old_refresh = jar["refresh_token"].value

    secret = os.environ["JWT_SECRET_KEY"]
    old_claims = jwt.decode(
        old_refresh,
        secret,
        algorithms=["HS256"],
        options={"require": ["sub", "iat", "exp", "type"]},
    )

    # 2) Refresh over HTTPS so the Secure cookie is sent
    r2 = https_post(client, "/refresh-token")
    assert r2.status_code == 200
    body = r2.get_json()
    assert body["code"] == 200
    assert "access_token" in body

    # Decode & validate NEW ACCESS token
    access_claims = jwt.decode(
        body["access_token"],
        secret,
        algorithms=["HS256"],
        options={"require": ["sub", "iat", "exp", "type"]},
    )
    assert access_claims["type"] == "access"
    assert access_claims["sub"] == str(u["user_id"])
    now = datetime.now(timezone.utc).timestamp()
    assert access_claims["iat"] <= now < access_claims["exp"]
    assert (access_claims["exp"] - access_claims["iat"]) >= 60  # at least 1 min

    # 3) Compare refresh cookie exp (expects rotation with same exp)
    refresh_cookie2 = r2.headers.get("Set-Cookie", "")
    assert "refresh_token=" in refresh_cookie2 
    jar2 = SimpleCookie(); jar2.load(refresh_cookie2)
    new_refresh = jar2["refresh_token"].value

    new_claims = jwt.decode(
        new_refresh,
        secret,
        algorithms=["HS256"],
        options={"require": ["sub", "iat", "exp", "type"]},
    )
    assert new_claims["type"] == "refresh"
    assert new_claims["sub"] == str(u["user_id"])
    assert new_claims["exp"] == old_claims["exp"]  # same expiry after refresh


@pytest.mark.integration
def test_refresh_missing_invalid_wrong_type_and_expired(client, seed_user):
    secret = os.environ["JWT_SECRET_KEY"]

    # A) missing cookie
    r = https_post(client, "/refresh-token")
    assert r.status_code == 401
    assert "Missing refresh token" in r.get_json()["message"]

    u = seed_user

    # B) invalid token string (2-arg set_cookie)
    client.set_cookie("refresh_token", "not-a-jwt", path="/refresh-token", secure=True)
    r = https_post(client, "/refresh-token")
    assert r.status_code == 401

    # C) wrong token type (access instead of refresh)
    access = jwt.encode({
        "sub": str(u["user_id"]), "name": u["username"],
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(minutes=15),
        "type": "access"
    }, secret, algorithm="HS256")
    client.set_cookie("refresh_token", access, path="/refresh-token", secure=True)
    r = https_post(client, "/refresh-token")
    assert r.status_code == 400
    assert "Invalid token type" in r.get_json()["message"]

    # D) expired refresh token
    expired = jwt.encode({
        "sub": str(u["user_id"]), "name": u["username"],
        "iat": datetime.now(timezone.utc) - timedelta(days=1),
        "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        "type": "refresh"
    }, secret, algorithm="HS256")
    client.set_cookie("refresh_token", expired, path="/refresh-token", secure=True)
    r = https_post(client, "/refresh-token")
    assert r.status_code == 401
    assert "expired" in r.get_json()["message"].lower()

    # E) refresh token for a non-existent user -> 401
    wrong_refresh = jwt.encode({
        "sub": "999",  # user id that doesn't exist
        "name": "invaliduser",
        "iat": datetime.now(timezone.utc),
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "refresh"
    }, secret, algorithm="HS256")

    client.set_cookie("refresh_token", wrong_refresh, path="/refresh-token", secure=True)

    r = https_post(client, "/refresh-token")
    assert r.status_code == 401
    assert "invalid refresh token user" in r.get_json()["message"].lower()


@pytest.mark.integration
def test_logout_clears_refresh_cookie(client):
    r = client.post("/logout")
    assert r.status_code == 200
    assert "refresh_token=;" in r.headers.get("Set-Cookie", "")


# ------------------------
# Simple E2E flow
# ------------------------

@pytest.mark.e2e
def test_register_login_refresh_logout_flow(client):
    # register
    r = client.post("/register", json={"username": "zoe", "email": "zoe@example.com", "password": "secret123"})
    assert r.status_code == 201

    # login
    r = client.post("/login", json={"email": "zoe@example.com", "password": "secret123"})
    assert r.status_code == 200
    assert "access_token" in r.get_json()
    assert "refresh_token=" in r.headers.get("Set-Cookie", "")

    # refresh (HTTPS to send Secure cookie)
    r = https_post(client, "/refresh-token")
    assert r.status_code == 200
    assert "access_token" in r.get_json()

    # logout clears cookie
    r = client.post("/logout")
    assert r.status_code == 200
    assert "refresh_token=;" in r.headers.get("Set-Cookie", "")
