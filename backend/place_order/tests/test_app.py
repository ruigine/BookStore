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


# ------------------------
# Unit tests
# ------------------------

@pytest.mark.unit
def test_place_order_success_publishes_and_returns_201(monkeypatch):
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
    # ensure user_id came from request.user and status is 'pending'
    assert seen["json"]["user_id"] == "1" or seen["json"]["user_id"] == 1
    assert seen["json"]["status"] == "pending"
    # publish called with the created order
    assert rmq.published == [order_out]


@pytest.mark.unit
def test_place_order_orders_non_201_is_forwarded_and_no_publish(monkeypatch):
    # Orders rejects creation
    def fake_post(url, json=None):
        return DummyResp(400, {"code": 400, "message": "bad payload"})
    monkeypatch.setattr(app_module.requests, "post", fake_post, raising=True)

    # RMQ should not be called
    rmq = DummyRMQ()
    monkeypatch.setattr(app_module, "RabbitMQClient", lambda: rmq, raising=True)

    payload = {"book_id": 1, "price": 1.23, "quantity": 1, "title": "X", "authors": "Y", "url": "/u"}
    with flask_app.test_request_context(
        "/placeorder", method="POST",
        data=json.dumps(payload), content_type="application/json"
    ):
        request.user = {"sub": "9", "name": "bob"}
        resp, status = app_module.place_order.__wrapped__()

    assert status == 400
    assert resp.get_json() == {"code": 400, "message": "bad payload"}
    assert rmq.published == []


@pytest.mark.unit
def test_place_order_exception_path(monkeypatch):
    def boom(*_, **__):
        raise RuntimeError("network down")
    monkeypatch.setattr(app_module.requests, "post", boom, raising=True)
    monkeypatch.setattr(app_module, "RabbitMQClient", DummyRMQ, raising=True)

    payload = {"book_id": 1, "price": 1.0, "quantity": 1, "title": "X", "authors": "Y", "url": "/u"}
    with flask_app.test_request_context(
        "/placeorder", method="POST",
        data=json.dumps(payload), content_type="application/json"
    ):
        request.user = {"sub": "1"}
        resp, status = app_module.place_order.__wrapped__()

    assert status == 500
    assert "An error occurred" in resp.get_json()["message"]


@pytest.mark.unit
def test_check_order_status_happy_path(monkeypatch):
    # Orders returns an order for this user
    def fake_get(url):
        assert url.endswith("/orders/22")
        return DummyResp(200, {"data": {"order_id": 22, "status": "paid", "user_id": 1}})
    monkeypatch.setattr(app_module.requests, "get", fake_get, raising=True)

    with flask_app.test_request_context("/checkorder/22"):
        request.user = {"sub": "1"}
        resp, status = app_module.check_order_status.__wrapped__(order_id=22)
    assert status == 200
    assert resp.get_json() == {"code": 200, "data": {"order_id": 22, "status": "paid"}}


@pytest.mark.unit
def test_check_order_status_forbidden_wrong_user(monkeypatch):
    def fake_get(url):
        return DummyResp(200, {"data": {"order_id": 7, "status": "pending", "user_id": 999}})
    monkeypatch.setattr(app_module.requests, "get", fake_get, raising=True)

    with flask_app.test_request_context("/checkorder/7"):
        request.user = {"sub": "1"}
        resp, status = app_module.check_order_status.__wrapped__(order_id=7)
    assert status == 403
    j = resp.get_json()
    assert j["code"] == 403 and "forbidden" in j["message"].lower()


@pytest.mark.unit
def test_check_order_status_forwards_non_200_and_exception(monkeypatch):
    # Forward non-200
    def r404(_url): return DummyResp(404, {"code": 404, "message": "not found"})
    monkeypatch.setattr(app_module.requests, "get", r404, raising=True)
    with flask_app.test_request_context("/checkorder/1"):
        request.user = {"sub": "1"}
        resp, status = app_module.check_order_status.__wrapped__(order_id=1)
    assert status == 404 and resp.get_json()["code"] == 404

    # Exception → 500
    def boom(*_, **__): raise RuntimeError("boom")
    monkeypatch.setattr(app_module.requests, "get", boom, raising=True)
    with flask_app.test_request_context("/checkorder/1"):
        request.user = {"sub": "1"}
        resp, status = app_module.check_order_status.__wrapped__(order_id=1)
    assert status == 500 and "An error occurred" in resp.get_json()["message"]


@pytest.mark.unit
def test_get_my_pending_book_order_passthrough_and_exception(monkeypatch):
    # Pass-through success
    def ok(url):
        assert "/orders/user/1/book/999" in url
        return DummyResp(200, {"code": 200, "hasPending": True})
    monkeypatch.setattr(app_module.requests, "get", ok, raising=True)
    with flask_app.test_request_context("/pendingorder/999"):
        request.user = {"sub": "1"}
        resp, status = app_module.get_my_pending_book_order.__wrapped__(book_id=999)
    assert status == 200 and resp.get_json() == {"code": 200, "hasPending": True}

    # Exception
    def boom(*_, **__): raise RuntimeError("down")
    monkeypatch.setattr(app_module.requests, "get", boom, raising=True)
    with flask_app.test_request_context("/pendingorder/999"):
        request.user = {"sub": "1"}
        resp, status = app_module.get_my_pending_book_order.__wrapped__(book_id=999)
    assert status == 500 and "An error occurred" in resp.get_json()["message"]


# ------------------------
# Integration tests
# ------------------------

@pytest.mark.integration
def test_place_order_integration_happy_path(client, monkeypatch):
    install_bypass_auth(monkeypatch, sub="1")

    seen = {}
    order_out = {"order_id": 55, "book_id": 5, "user_id": 1, "price": 12.34,
                 "quantity": 1, "status": "pending", "title": "T", "authors": "A", "url": "/u"}
    def fake_post(url, json=None):
        seen["url"], seen["json"] = url, json
        return DummyResp(201, {"data": order_out})
    monkeypatch.setattr(app_module.requests, "post", fake_post, raising=True)

    rmq = DummyRMQ()
    monkeypatch.setattr(app_module, "RabbitMQClient", lambda: rmq, raising=True)

    payload = {"book_id": 5, "price": 12.34, "quantity": 1, "title": "T", "authors": "A", "url": "/u"}
    r = client.post("/placeorder", json=payload)
    assert r.status_code == 201
    assert r.get_json()["data"] == order_out
    assert rmq.published == [order_out]
    assert seen["json"]["user_id"] in ("1", 1)


@pytest.mark.integration
def test_check_order_status_integration_paths(client, monkeypatch):
    install_bypass_auth(monkeypatch, sub="1")

    # happy
    def ok(url): return DummyResp(200, {"data": {"order_id": 9, "status": "paid", "user_id": 1}})
    monkeypatch.setattr(app_module.requests, "get", ok, raising=True)
    r = client.get("/checkorder/9")
    assert r.status_code == 200 and r.get_json()["data"]["status"] == "paid"

    # forbidden
    def wrong(url): return DummyResp(200, {"data": {"order_id": 9, "status": "paid", "user_id": 999}})
    monkeypatch.setattr(app_module.requests, "get", wrong, raising=True)
    r2 = client.get("/checkorder/9")
    assert r2.status_code == 403

    # passthrough 404
    def nf(url): return DummyResp(404, {"code": 404, "message": "not found"})
    monkeypatch.setattr(app_module.requests, "get", nf, raising=True)
    r3 = client.get("/checkorder/12345")
    assert r3.status_code == 404 and r3.get_json()["code"] == 404


@pytest.mark.integration
def test_pendingorder_integration(client, monkeypatch):
    install_bypass_auth(monkeypatch, sub="7")
    def ok(url):
        assert url.endswith("/orders/user/7/book/222")
        return DummyResp(200, {"code": 200, "hasPending": False})
    monkeypatch.setattr(app_module.requests, "get", ok, raising=True)
    r = client.get("/pendingorder/222")
    assert r.status_code == 200 and r.get_json()["hasPending"] is False


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
