import json
import pytest
from decimal import Decimal
from datetime import datetime
from sqlalchemy import desc

from orders.app import app as flask_app
from orders.model import db, Order

# ------------------------
# Unit tests
# ------------------------

@pytest.mark.unit
def test_order_json_includes_all_fields_and_values():
    o = Order(
        book_id=321, user_id=42, price=Decimal("12.34"),
        quantity=3, status="pending", title="Some Book",
        authors="Anon", url="/img/x.png",
    )
    o.order_id = 7
    o.order_date = datetime(2024, 3, 4, 5, 6, 7)

    j = o.json()
    assert j == {
        "order_id": 7,
        "book_id": 321,
        "user_id": 42,
        "price": Decimal("12.34"),
        "quantity": 3,
        "status": "pending",
        "title": "Some Book",
        "authors": "Anon",
        "url": "/img/x.png",
        "order_date": datetime(2024, 3, 4, 5, 6, 7),
    }


@pytest.mark.unit
def test_order_repr_contains_id_and_title():
    o = Order(
        book_id=1, user_id=1, price=Decimal("1.00"),
        quantity=1, status="paid", title="Hello", authors=None, url=None
    )
    o.order_id = 99
    assert "<Order 99 - Hello>" in repr(o)


# ------------------------
# Integration tests
# ------------------------

@pytest.mark.integration
def test_create_order_success(client):
    payload = {
        "book_id": 101,
        "user_id": 1,
        "price": 9.99,            # float is fine; we’ll compare via Decimal(str(...))
        "quantity": 2,
        "status": "pending",
        "title": "Budget Cooking",
        "authors": "Chef A",
        "url": "/img/cook.png",
    }
    r = client.post("/orders", json=payload)
    assert r.status_code == 201
    body = r.get_json()
    assert body["code"] == 201
    data = body["data"]

    # response assertions
    assert "order_id" in data
    assert data["book_id"] == payload["book_id"]
    assert data["user_id"] == payload["user_id"]
    assert float(data["price"]) == float(payload["price"])
    assert data["quantity"] == payload["quantity"]
    assert data["status"] == payload["status"]
    assert data["title"] == payload["title"]
    assert data["authors"] == payload["authors"]
    assert data["url"] == payload["url"]

    # DB assertions
    with flask_app.app_context():
        row = db.session.get(Order, data["order_id"])
        assert row is not None
        assert row.book_id == payload["book_id"]
        assert row.user_id == payload["user_id"]
        assert row.price == Decimal(str(payload["price"]))  # compare as Decimal
        assert row.quantity == payload["quantity"]
        assert row.status == payload["status"]
        assert row.title == payload["title"]
        assert row.authors == payload["authors"]
        assert row.url == payload["url"]
        assert row.order_date is not None  


@pytest.mark.integration
def test_create_order_bad_json_and_missing_fields(client):
    # A) no body / no JSON -> 500
    r = client.post("/orders")
    assert r.status_code == 500

    # B) malformed JSON -> 500
    r = client.post("/orders", data="{bad json", content_type="application/json")
    assert r.status_code == 500

    # C) missing required fields -> 500
    r = client.post("/orders", json={"title": "Only Title"})
    assert r.status_code == 500

    # D) wrong types/values -> 500 (quantity <= 0, non-numeric price)
    r = client.post("/orders", json={
        "book_id": 101,
        "user_id": 1,
        "price": "abc",     # not a number
        "quantity": 0,      # invalid (<= 0)
        "status": "pending",
        "title": "Budget Cooking",
        "authors": "Chef A",
        "url": "/img/cook.png",
    })
    assert r.status_code == 500


@pytest.mark.integration
def test_create_order_exception_path(client, monkeypatch):
    # Force db.session.commit to raise to hit the 500 branch
    def boom():
        raise RuntimeError("boom")
    monkeypatch.setattr(db.session, "commit", boom, raising=True)

    r = client.post("/orders", json={
        "book_id": 1, "user_id": 1, "price": "1.00", "quantity": 1,
        "status": "pending", "title": "X"
    })
    assert r.status_code == 500
    assert "An error occurred" in r.get_json()["message"]


@pytest.mark.integration
def test_get_order_found_and_not_found(client, seed_orders):
    # pick an existing seeded order id
    some = seed_orders[0]["order_id"]
    r = client.get(f"/orders/{some}")
    assert r.status_code == 200
    assert r.get_json()["data"]["order_id"] == some
    assert r.get_json()["data"]["title"] == seed_orders[0]["title"]

    r2 = client.get("/orders/999999")
    assert r2.status_code == 404
    assert "not found" in r2.get_json()["message"].lower()


@pytest.mark.integration
def test_get_order_by_id_exception_path(client, monkeypatch):
    import orders.app as app_module

    def boom(*_, **__):
        raise RuntimeError("boom")

    # Patch the session.get that the route calls
    monkeypatch.setattr(app_module.db.session, "get", boom, raising=True)

    r = client.get("/orders/1")
    assert r.status_code == 500
    assert "An error occurred" in r.get_json()["message"]


@pytest.mark.integration
def test_update_order_status_success_404_and_exception(client, seed_orders, monkeypatch):
    target = seed_orders[0]["order_id"]

    # success
    r = client.put(f"/orders/{target}", json={"status": "failed"})
    assert r.status_code == 200
    assert r.get_json()["data"]["status"] == "failed"
    assert r.get_json()["data"]["order_id"] == target

    # 404
    r2 = client.put("/orders/999999", json={"status": "failed"})
    assert r2.status_code == 404

    # exception path (commit fails)
    def boom():
        raise RuntimeError("boom")
    monkeypatch.setattr(db.session, "commit", boom, raising=True)
    r3 = client.put(f"/orders/{target}", json={"status": "pending"})
    assert r3.status_code == 500
    assert "An error occurred" in r3.get_json()["message"]


@pytest.mark.integration
def test_update_order_status_validation(client, seed_orders):
    target = seed_orders[0]["order_id"]

    # A) no body / no JSON -> 500
    r = client.put(f"/orders/{target}")
    assert r.status_code == 500

    # B) malformed JSON -> 500
    r = client.put(f"/orders/{target}", data="{bad json", content_type="application/json")
    assert r.status_code == 500

    # C) empty JSON -> 500
    r = client.put(f"/orders/{target}", json={})
    assert r.status_code == 500

    # D) missing "status" -> 500
    r = client.put(f"/orders/{target}", json={"foo": "bar"})
    assert r.status_code == 500

    # E) extra fields ignored -> 200
    r = client.put(f"/orders/{target}", json={"status": "failed", "unexpected": "ignored", "title": "blahblah"})
    assert r.status_code == 200
    body = r.get_json()
    assert body["data"]["status"] == "failed"
    # ensure the extra field didn't leak into response
    assert "unexpected" not in body["data"]
    assert body["data"]["title"] != "blahblah"


@pytest.mark.integration
def test_get_orders_by_user_no_pagination_and_empty(client, seed_orders):
    # user 1 has 3 orders, sorted desc(order_date)
    r = client.get("/orders/user/1")
    assert r.status_code == 200
    data = r.get_json()["data"]
    assert len(data) == 3

    # check ordering: newer first by order_date
    dates = [d["order_date"] for d in data]
    assert dates == sorted(dates, reverse=True)

    # user 999 has none
    r2 = client.get("/orders/user/999")
    assert r2.status_code == 200
    assert r2.get_json()["data"] == []


@pytest.mark.integration
def test_get_orders_by_user_with_pagination_and_defaults(client, seed_orders):
    r = client.get("/orders/user/1?page=1")
    assert r.status_code == 200
    body = r.get_json()
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["limit"] == 4
    assert body["pagination"]["total"] == 3
    assert body["pagination"]["has_more"] is False
    assert len(body["data"]) == 3

    # limit=2 (page defaults to 1)
    r2 = client.get("/orders/user/1?limit=2")
    b2 = r2.get_json()
    assert b2["pagination"]["page"] == 1
    assert b2["pagination"]["limit"] == 2
    assert b2["pagination"]["total"] == 3
    assert b2["pagination"]["has_more"] is True
    assert len(b2["data"]) == 2

    # page=2&limit=2 -> 1 item
    r3 = client.get("/orders/user/1?page=2&limit=2")
    b3 = r3.get_json()
    assert b3["pagination"]["page"] == 2
    assert b3["pagination"]["limit"] == 2
    assert b3["pagination"]["total"] == 3
    assert b3["pagination"]["has_more"] is False
    assert len(b3["data"]) == 1


@pytest.mark.integration
def test_get_orders_by_user_exception_path(client, monkeypatch):
    # Force .count() to raise inside the paginated branch
    import orders.app as app_module

    class DummyQuery:
        def filter_by(self, **_): return self
        def order_by(self, *_): return self
        def count(self): raise RuntimeError("boom")
        def offset(self, *_): return self
        def limit(self, *_): return self
        def all(self): return []

    class DummyOrder:
        query = DummyQuery()

    monkeypatch.setattr(app_module, "Order", DummyOrder, raising=False)
    r = client.get("/orders/user/1?page=1&limit=2")
    assert r.status_code == 500
    assert "An error occurred" in r.get_json()["message"]


@pytest.mark.integration
def test_get_pending_order_by_user_and_book_true_false_and_exception(client, seed_orders, monkeypatch):
    # True: user 1 has a pending order for book_id 101
    r = client.get("/orders/user/1/book/101")
    assert r.status_code == 200
    j = r.get_json()
    assert j["code"] == 200 and j["hasPending"] is True
    assert j["data"]["status"] == "pending"

    # False: no pending for this pair
    r2 = client.get("/orders/user/1/book/102")
    assert r2.status_code == 200
    assert r2.get_json()["hasPending"] is False

    # exception path: make .first() raise
    import orders.app as app_module
    class DummyQuery2:
        def filter_by(self, **_): return self
        def first(self): raise RuntimeError("boom")
    class DummyOrder2:
        query = DummyQuery2()
    monkeypatch.setattr(app_module, "Order", DummyOrder2, raising=False)
    r3 = client.get("/orders/user/1/book/101")
    assert r3.status_code == 500
    assert "An error occurred" in r3.get_json()["message"]


# ------------------------
# Tiny E2E flow (single service)
# ------------------------

@pytest.mark.e2e
def test_create_fetch_update_list_flow(client):
    # create
    payload = {
        "book_id": 777, "user_id": 5, "price": "19.99", "quantity": 1,
        "status": "pending", "title": "E2E Book", "authors": "E2E", "url": "/img/e2e.png",
    }
    r = client.post("/orders", json=payload)
    assert r.status_code == 201
    oid = r.get_json()["data"]["order_id"]

    # fetch by id
    r2 = client.get(f"/orders/{oid}")
    assert r2.status_code == 200
    assert r2.get_json()["data"]["title"] == "E2E Book"

    # update status
    r3 = client.put(f"/orders/{oid}", json={"status": "completed"})
    assert r3.status_code == 200
    assert r3.get_json()["data"]["status"] == "completed"

    # list by user (no pagination)
    r4 = client.get("/orders/user/5")
    assert r4.status_code == 200
    titles = [o["title"] for o in r4.get_json()["data"]]
    assert "E2E Book" in titles

    # pending check should now be False for (user 5, book 777) since status is completed
    r5 = client.get("/orders/user/5/book/777")
    assert r5.status_code == 200
    assert r5.get_json()["hasPending"] is False
