import pytest
from flask import request

import display_orders.app as app_module
from display_orders.app import app as flask_app


# --- helpers ---------------------------------------------------------------

class DummyResp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}
    def json(self):
        return self._payload

def install_bypass_auth(monkeypatch, sub="1", name="alice"):
    """
    Replace the Flask view function for 'get_my_orders'
    """
    if not hasattr(app_module.get_my_orders, "__wrapped__"):
        raise RuntimeError("jwt_required decorator does not expose __wrapped__; "
                           "functools.wraps is needed in your decorator for this test strategy.")

    def fake_view():
        request.user = {"sub": sub, "name": name}
        # call the undecorated view
        return app_module.get_my_orders.__wrapped__()

    # Swap the view function Flask will call for this endpoint
    app_module.app.view_functions["get_my_orders"] = fake_view


# ------------------------
# Unit tests (no client)
# ------------------------

@pytest.mark.unit
@pytest.mark.parametrize(
    "qs, expected_suffix",
    [
        ("", ""),
        ("?page=2", "?page=2"),
        ("?limit=5", "?limit=5"),
        ("?page=3&limit=10", "?page=3&limit=10"),
    ],
    ids=["no_qs", "page_only", "limit_only", "both"],
)
def test_builds_orders_url_unit(monkeypatch, qs, expected_suffix):
    """Call the view directly in a request context; assert it calls Orders with the right URL."""
    # stub Orders call
    called = {}

    def fake_get(url):
        called["url"] = url
        return DummyResp(200, {
            "code": 200,
            "data": [],
            "pagination": {"page": 1, "limit": 10, "total": 0, "has_more": False},
        })

    monkeypatch.setattr(app_module.requests, "get", fake_get, raising=True)

    # call the undecorated function inside a request context
    with flask_app.test_request_context(f"/myorders{qs}"):
        request.user = {"sub": "1", "name": "alice"}  # bypass auth manually
        resp, status = app_module.get_my_orders.__wrapped__()  # <-- no decorator
        assert status == 200
        assert called["url"] == f"{app_module.ORDERS_URL}/1{expected_suffix}"


# ------------------------
# Integration tests (client)
# ------------------------

@pytest.mark.integration
def test_myorders_happy_path_passthrough(client, monkeypatch):
    """GET /myorders returns whatever Orders returns (200), with the same body."""
    install_bypass_auth(monkeypatch)

    payload = {
        "code": 200,
        "data": [{"order_id": 1, "title": "Budget Cooking"}],
        "pagination": {"page": 1, "limit": 10, "total": 1, "has_more": False},
    }

    def fake_get(url):
        # Ensure URL built correctly without pagination
        assert url == f"{app_module.ORDERS_URL}/1"
        return DummyResp(200, payload)

    monkeypatch.setattr(app_module.requests, "get", fake_get, raising=True)

    r = client.get("/myorders")
    assert r.status_code == 200
    assert r.get_json() == payload


@pytest.mark.integration
def test_myorders_with_pagination_variants(client, monkeypatch):
    """page only, limit only, both — query string must be forwarded correctly."""
    install_bypass_auth(monkeypatch)

    seen = []

    def fake_get(url):
        seen.append(url)
        return DummyResp(200, {
            "code": 200, "data": [],
            "pagination": {"page": 1, "limit": 10, "total": 0, "has_more": False},
        })

    monkeypatch.setattr(app_module.requests, "get", fake_get, raising=True)

    r1 = client.get("/myorders?page=2")
    assert r1.status_code == 200
    r2 = client.get("/myorders?limit=5")
    assert r2.status_code == 200
    r3 = client.get("/myorders?page=3&limit=7")
    assert r3.status_code == 200

    assert f"{app_module.ORDERS_URL}/1?page=2" in seen
    assert f"{app_module.ORDERS_URL}/1?limit=5" in seen
    assert f"{app_module.ORDERS_URL}/1?page=3&limit=7" in seen


@pytest.mark.integration
def test_myorders_forwards_non_200_from_orders(client, monkeypatch):
    """If Orders returns non-200 (e.g., 404/500), forward status + body."""
    install_bypass_auth(monkeypatch)

    def fake_get(url):
        return DummyResp(404, {"code": 404, "message": "not found"})

    monkeypatch.setattr(app_module.requests, "get", fake_get, raising=True)

    r = client.get("/myorders")
    assert r.status_code == 404
    assert r.get_json() == {"code": 404, "message": "not found"}


@pytest.mark.integration
def test_myorders_exception_path(client, monkeypatch):
    """If requests.get raises, we hit our 500 branch."""
    install_bypass_auth(monkeypatch)

    def boom(*_, **__):
        raise RuntimeError("boom")

    monkeypatch.setattr(app_module.requests, "get", boom, raising=True)

    r = client.get("/myorders")
    assert r.status_code == 500
    assert "An error occurred" in r.get_json()["message"]


# ------------------------
# Tiny E2E (single-service flow)
# ------------------------

@pytest.mark.e2e
def test_end_to_end_like_flow_with_pagination(client, monkeypatch):
    """
    Simulate the whole flow:
      - inject user
      - /myorders called with page+limit
      - service builds URL and returns Orders' payload untouched
    """
    install_bypass_auth(monkeypatch)

    expected = {
        "code": 200,
        "data": [
            {"order_id": 10, "title": "Deep Space"},
            {"order_id": 11, "title": "Premium Atlas"},
        ],
        "pagination": {"page": 2, "limit": 2, "total": 5, "has_more": True},
    }

    def fake_get(url):
        assert url == f"{app_module.ORDERS_URL}/1?page=2&limit=2"
        return DummyResp(200, expected)

    monkeypatch.setattr(app_module.requests, "get", fake_get, raising=True)

    r = client.get("/myorders?page=2&limit=2")
    assert r.status_code == 200
    assert r.get_json() == expected
