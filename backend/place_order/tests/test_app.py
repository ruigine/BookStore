import json
import pytest
from flask import request

import place_order.app as app_module
from place_order.app import app as flask_app

# ------------------------
# Helpers
# ------------------------

class DummyResp:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self._payload = payload or {}
    def json(self):
        return self._payload

class DummyRMQ:
    def __init__(self):
        self.published = []
    def publish(self, obj):
        self.published.append(obj)

def install_bypass_auth(monkeypatch, sub="1", name="alice"):
    """
    Replace each Flask view function with a shim that injects request.user
    and calls the undecorated function (.__wrapped__), forwarding route kwargs.
    """
    for endpoint in ("place_order", "check_order_status", "get_my_pending_book_order"):
        view = getattr(app_module, endpoint)
        if not hasattr(view, "__wrapped__"):
            raise RuntimeError(f"{endpoint} missing __wrapped__; ensure your jwt_required uses @wraps")

        def make_fake(view_func):
            def _fake(**view_args):
                request.user = {"sub": sub, "name": name}
                return view_func.__wrapped__(**view_args)  # forward order_id/book_id
            _fake.__name__ = view_func.__name__
            return _fake

        monkeypatch.setitem(app_module.app.view_functions, endpoint, make_fake(view))


# ========================
# Integration tests
# ========================

class TestPlaceOrder:

    @pytest.mark.integration
    def test_success_publishes_and_returns_201(self, monkeypatch):
        # Stub Orders POST to return created order
        seen = {}
        order_out = {
            "order_id": 10,
            "book_id": 111,
            "user_id": 1,
            "price": 9.99,
            "quantity": 2,
            "status": "pending",
            "title": "Budget Cooking",
            "authors": "Chef A",
            "url": "/img/cook.png",
        }
        def fake_post(url, json=None):
            seen["url"] = url
            seen["json"] = json
            return DummyResp(201, {"data": order_out})
        monkeypatch.setattr(app_module.requests, "post", fake_post, raising=True)

        # Stub RabbitMQClient to record publish
        rmq = DummyRMQ()
        monkeypatch.setattr(app_module, "RabbitMQClient", lambda: rmq, raising=True)

        payload = {
            "book_id": 111, "price": 9.99, "quantity": 2,
            "title": "Budget Cooking", "authors": "Chef A", "url": "/img/cook.png",
        }

        with flask_app.test_request_context(
            "/placeorder", method="POST",
            data=json.dumps(payload), content_type="application/json"
        ):
            request.user = {"sub": "1", "name": "alice"}  # bypass auth
            resp, status = app_module.place_order.__wrapped__()  # call undecorated

        # Assertions
        assert status == 201
        body = resp.get_json()
        assert body["code"] == 201 and body["data"] == order_out
        assert seen["url"] == f"{app_module.ORDERS_URL}"
        assert int(seen["json"]["user_id"]) == 1
        assert seen["json"]["status"] == "pending"
        assert rmq.published == [order_out]
        assert len(rmq.published) == 1

    @pytest.mark.integration
    def test_orders_non_201_is_forwarded_and_no_publish(self, monkeypatch):
        # Orders rejects creation
        def fake_post(url, json=None):
            return DummyResp(500, {"code": 500, "message": "An error occurred"})
        monkeypatch.setattr(app_module.requests, "post", fake_post, raising=True)

        rmq = DummyRMQ()
        monkeypatch.setattr(app_module, "RabbitMQClient", lambda: rmq, raising=True)

        payload = {"book_id": 1, "price": 1.23, "quantity": 1, "title": "X", "authors": "Y", "url": "/u"}
        with flask_app.test_request_context(
            "/placeorder", method="POST",
            data=json.dumps(payload), content_type="application/json"
        ):
            request.user = {"sub": "9", "name": "bob"}
            resp, status = app_module.place_order.__wrapped__()

        assert status == 500
        assert resp.get_json() == {"code": 500, "message": "An error occurred"}
        assert rmq.published == []

    @pytest.mark.integration
    def test_exception_path_returns_500_and_no_publish(self, monkeypatch):
        def boom(*_, **__):
            raise RuntimeError("network down")
        monkeypatch.setattr(app_module.requests, "post", boom, raising=True)
        rmq = DummyRMQ()
        monkeypatch.setattr(app_module, "RabbitMQClient", lambda: rmq, raising=True)

        payload = {"book_id": 1, "price": 1.0, "quantity": 1, "title": "X", "authors": "Y", "url": "/u"}
        with flask_app.test_request_context(
            "/placeorder", method="POST",
            data=json.dumps(payload), content_type="application/json"
        ):
            request.user = {"sub": "1"}
            resp, status = app_module.place_order.__wrapped__()

        assert status == 500
        assert "An error occurred" in resp.get_json()["message"]
        assert rmq.published == []

    @pytest.mark.integration
    def test_requires_auth(self, client):
        # No bypass; should be blocked by auth decorator
        r = client.post("/placeorder", json={})
        assert r.status_code == 401

    # ---- Input validation edge cases ----

    @pytest.mark.integration
    @pytest.mark.parametrize("payload", [
        {"price": 9.99, "quantity": 1, "title": "T", "authors": "A", "url": "/u"},        # missing book_id
        {"book_id": 1, "quantity": 1, "title": "T", "authors": "A", "url": "/u"},         # missing price
        {"book_id": 1, "price": 9.99, "title": "T", "authors": "A", "url": "/u"},         # missing quantity
        {"book_id": 1, "price": 9.99, "quantity": 1, "authors": "A", "url": "/u"},        # missing title
    ])
    def test_input_validation_missing_fields(self, client, monkeypatch, payload):
        install_bypass_auth(monkeypatch, sub="1")
        r = client.post("/placeorder", json=payload)
        assert r.status_code == 500

    @pytest.mark.integration
    @pytest.mark.parametrize("payload", [
        {"book_id": "not-a-number", "price": 9.99, "quantity": 1, "title": "T", "authors": "A", "url": "/u"},
        {"book_id": 1, "price": "abc", "quantity": 1, "title": "T", "authors": "A", "url": "/u"},
        {"book_id": 1, "price": 9.99, "quantity": -1, "title": "T", "authors": "A", "url": "/u"},
    ])
    def test_input_validation_invalid_types(self, client, monkeypatch, payload):
        install_bypass_auth(monkeypatch, sub="1")
        r = client.post("/placeorder", json=payload)
        assert r.status_code == 500


class TestCheckOrder:

    @pytest.mark.integration
    def test_happy_path(self, monkeypatch):
        # Orders returns an order for this user
        def fake_get(url):
            assert url.endswith("/orders/22")
            return DummyResp(200, {"data": {"order_id": 22, "status": "completed", "user_id": 1}})
        monkeypatch.setattr(app_module.requests, "get", fake_get, raising=True)

        with flask_app.test_request_context("/checkorder/22"):
            request.user = {"sub": "1"}
            resp, status = app_module.check_order_status.__wrapped__(order_id=22)
        assert status == 200
        assert resp.get_json() == {"code": 200, "data": {"order_id": 22, "status": "completed"}}

    @pytest.mark.integration
    def test_forbidden_wrong_user(self, monkeypatch):
        def fake_get(url):
            return DummyResp(200, {"data": {"order_id": 7, "status": "pending", "user_id": 999}})
        monkeypatch.setattr(app_module.requests, "get", fake_get, raising=True)

        with flask_app.test_request_context("/checkorder/7"):
            request.user = {"sub": "1"}
            resp, status = app_module.check_order_status.__wrapped__(order_id=7)
        assert status == 403
        j = resp.get_json()
        assert j["code"] == 403 and "forbidden" in j["message"].lower()

    @pytest.mark.integration
    def test_forwards_non_200(self, monkeypatch):
        def r404(_url): return DummyResp(404, {"code": 404, "message": "not found"})
        monkeypatch.setattr(app_module.requests, "get", r404, raising=True)
        with flask_app.test_request_context("/checkorder/1"):
            request.user = {"sub": "1"}
            resp, status = app_module.check_order_status.__wrapped__(order_id=1)
        assert status == 404 and resp.get_json()["code"] == 404

    @pytest.mark.integration
    def test_exception_returns_500(self, monkeypatch):
        def boom(*_, **__): raise RuntimeError("boom")
        monkeypatch.setattr(app_module.requests, "get", boom, raising=True)
        with flask_app.test_request_context("/checkorder/1"):
            request.user = {"sub": "1"}
            resp, status = app_module.check_order_status.__wrapped__(order_id=1)
        assert status == 500 and "An error occurred" in resp.get_json()["message"]

    @pytest.mark.integration
    def test_requires_auth(self, client):
        r = client.get("/checkorder/1")
        assert r.status_code == 401


class TestPendingOrder:

    @pytest.mark.integration
    def test_passthrough_success(self, monkeypatch):
        def ok(url):
            assert "/orders/user/1/book/999" in url
            return DummyResp(200, {"code": 200, "hasPending": True})
        monkeypatch.setattr(app_module.requests, "get", ok, raising=True)
        with flask_app.test_request_context("/pendingorder/999"):
            request.user = {"sub": "1"}
            resp, status = app_module.get_my_pending_book_order.__wrapped__(book_id=999)
        assert status == 200 and resp.get_json() == {"code": 200, "hasPending": True}

    @pytest.mark.integration
    def test_exception_returns_500(self, monkeypatch):
        def boom(*_, **__): raise RuntimeError("down")
        monkeypatch.setattr(app_module.requests, "get", boom, raising=True)
        with flask_app.test_request_context("/pendingorder/999"):
            request.user = {"sub": "1"}
            resp, status = app_module.get_my_pending_book_order.__wrapped__(book_id=999)
        assert status == 500 and "An error occurred" in resp.get_json()["message"]

    @pytest.mark.integration
    def test_requires_auth(self, client):
        r = client.get("/pendingorder/1")
        assert r.status_code == 401


# ------------------------
# Simple E2E Flow
# ------------------------

@pytest.mark.e2e
def test_place_and_check_flow(client, monkeypatch):
    install_bypass_auth(monkeypatch, sub="42")

    # in-memory "orders" store for the fake Orders service
    store = {}
    next_id = {"v": 1000}

    def fake_post(url, json=None):
        oid = next_id["v"]; next_id["v"] += 1
        record = {
            "order_id": oid,
            "book_id": json["book_id"],
            "user_id": int(json["user_id"]),
            "price": json["price"],
            "quantity": json["quantity"],
            "status": "pending",
            "title": json["title"],
            "authors": json["authors"],
            "url": json["url"],
        }
        store[oid] = record
        return DummyResp(201, {"data": record})

    def fake_get(url):
        # url ends with /orders/<id>
        oid = int(url.rsplit("/", 1)[-1])
        rec = store.get(oid)
        if rec is None:
            return DummyResp(404, {"code": 404, "message": "not found"})
        return DummyResp(200, {"data": rec})

    monkeypatch.setattr(app_module.requests, "post", fake_post, raising=True)
    monkeypatch.setattr(app_module.requests, "get", fake_get, raising=True)

    rmq = DummyRMQ()
    monkeypatch.setattr(app_module, "RabbitMQClient", lambda: rmq, raising=True)

    # place order
    payload = {"book_id": 999, "price": 19.99, "quantity": 3, "title": "Atlas", "authors": "C. B", "url": "/img/a"}
    r = client.post("/placeorder", json=payload)
    assert r.status_code == 201
    placed = r.get_json()["data"]
    assert rmq.published == [placed]

    # check order (same user 42)
    oid = placed["order_id"]
    r2 = client.get(f"/checkorder/{oid}")
    assert r2.status_code == 200
    assert r2.get_json()["data"] == {"order_id": oid, "status": "pending"}
