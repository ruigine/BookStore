import json
import pytest
from decimal import Decimal


def _body(order_id=1, book_id=101, qty=2):
    return json.dumps({
        "order_id": order_id,
        "book_id": book_id,
        "quantity": qty,
    }).encode()  # process_order calls json.loads on bytes OK


class FakeResp:
    """Minimal requests.Response stand-in."""
    def __init__(self, status_code=200, ok=None, payload=None):
        self.status_code = status_code
        self.ok = (ok if ok is not None else (200 <= status_code < 300))
        self._payload = payload or {}
    def json(self):
        return self._payload


# ------------------------
# Unit tests
# ------------------------

@pytest.mark.unit
def test_success_flow_updates_completed_and_acks(module, monkeypatch, fake_ch_method):
    ch, method = fake_ch_method
    calls = []

    def fake_put(url, json=None):
        calls.append((url, json))
        # first call: books decrement -> 200
        if url.endswith("/books/101/decrement"):
            return FakeResp(200, payload={"code": 200})
        # second call: orders status -> 200 OK
        return FakeResp(200, ok=True)

    monkeypatch.setattr(module.requests, "put", fake_put, raising=True)

    module.process_order(ch, method, None, _body(order_id=1, book_id=101, qty=2))

    # URLs and payloads in order
    assert calls[0] == (
        f"{module.BOOKS_URL}/101/decrement",
        {"quantity_ordered": 2},
    )
    assert calls[1] == (
        f"{module.ORDERS_URL}/1",
        {"status": "completed"},
    )
    # ack always
    assert ch.acks == [method.delivery_tag]


@pytest.mark.unit
def test_decrement_failure_marks_failed_and_acks(module, monkeypatch, fake_ch_method):
    ch, method = fake_ch_method
    calls = []

    def fake_put(url, json=None):
        calls.append((url, json))
        if url.endswith("/books/101/decrement"):
            # simulate business error from Books (e.g., oversubscribe)
            return FakeResp(409, payload={"code": 409, "message": "conflict"})
        # Should update order -> failed
        return FakeResp(200, ok=True)

    monkeypatch.setattr(module.requests, "put", fake_put, raising=True)

    module.process_order(ch, method, None, _body(order_id=9, book_id=101, qty=5))

    assert calls[0][0] == f"{module.BOOKS_URL}/101/decrement"
    assert calls[1] == (f"{module.ORDERS_URL}/9", {"status": "failed"})
    assert ch.acks == [method.delivery_tag]


@pytest.mark.unit
def test_update_failure_after_successful_decrement_still_acks(module, monkeypatch, fake_ch_method):
    ch, method = fake_ch_method
    calls = []

    def fake_put(url, json=None):
        calls.append((url, json))
        if url.endswith("/books/101/decrement"):
            return FakeResp(200)  # decrement OK
        # orders update fails (ok=False)
        return FakeResp(500, ok=False)

    monkeypatch.setattr(module.requests, "put", fake_put, raising=True)

    module.process_order(ch, method, None, _body(order_id=2, book_id=101, qty=1))

    # still tried to set completed
    assert calls[1] == (f"{module.ORDERS_URL}/2", {"status": "completed"})
    # and we still ack
    assert ch.acks == [method.delivery_tag]


@pytest.mark.unit
def test_exception_path_marks_failed_and_acks(module, monkeypatch, fake_ch_method):
    ch, method = fake_ch_method
    calls = {"count": 0, "urls": []}

    def fake_put(url, json=None):
        calls["count"] += 1
        calls["urls"].append(url)
        # first call (books decrement) throws exception -> triggers except
        if calls["count"] == 1:
            raise RuntimeError("network down")
        # second call (orders/failed) should succeed
        return FakeResp(200, ok=True)

    monkeypatch.setattr(module.requests, "put", fake_put, raising=True)

    module.process_order(ch, method, None, _body(order_id=3, book_id=500, qty=1))

    # Second call should be orders status=failed
    assert calls["urls"][1] == f"{module.ORDERS_URL}/3"
    assert ch.acks == [method.delivery_tag]


# ------------------------
# Integration tests
# ------------------------

@pytest.mark.integration
def test_success_with_varied_ids_and_quantities(module, monkeypatch, fake_ch_method):
    ch, method = fake_ch_method
    seen = []

    def fake_put(url, json=None):
        seen.append((url, json))
        if url.endswith("/books/555/decrement"):
            # OK decrement
            return FakeResp(200, payload={"code": 200})
        return FakeResp(200, ok=True)

    monkeypatch.setattr(module.requests, "put", fake_put, raising=True)

    module.process_order(ch, method, None, _body(order_id=42, book_id=555, qty=7))

    assert seen[0] == (f"{module.BOOKS_URL}/555/decrement", {"quantity_ordered": 7})
    assert seen[1] == (f"{module.ORDERS_URL}/42", {"status": "completed"})
    assert ch.acks == [method.delivery_tag]


@pytest.mark.integration
def test_books_service_business_error_flows_to_failed(module, monkeypatch, fake_ch_method):
    ch, method = fake_ch_method
    seen = []

    def fake_put(url, json=None):
        seen.append((url, json))
        if url.endswith("/books/2/decrement"):
            return FakeResp(400, payload={"code": 400, "message": "invalid qty"})
        return FakeResp(200, ok=True)

    monkeypatch.setattr(module.requests, "put", fake_put, raising=True)

    module.process_order(ch, method, None, _body(order_id=77, book_id=2, qty=0))

    assert seen[1] == (f"{module.ORDERS_URL}/77", {"status": "failed"})
    assert ch.acks == [method.delivery_tag]


@pytest.mark.integration
def test_orders_update_failure_is_logged_but_ack_happens(module, monkeypatch, fake_ch_method):
    ch, method = fake_ch_method
    seen = []

    def fake_put(url, json=None):
        seen.append((url, json))
        if url.endswith("/books/9/decrement"):
            return FakeResp(200)
        # update fails at Orders
        return FakeResp(503, ok=False)

    monkeypatch.setattr(module.requests, "put", fake_put, raising=True)

    module.process_order(ch, method, None, _body(order_id=88, book_id=9, qty=1))
    assert seen[1] == (f"{module.ORDERS_URL}/88", {"status": "completed"})
    assert ch.acks == [method.delivery_tag]


# ------------------------
# Simple E2E Test
# ------------------------

@pytest.mark.e2e
def test_end_to_end_like_success_sequence(module, monkeypatch, fake_ch_method):
    """Treat process_order as the consumer callback and verify the full happy path call chain."""
    ch, method = fake_ch_method
    order_id, book_id, qty = 9001, 333, 4
    sequence = []

    def fake_put(url, json=None):
        sequence.append((url, json))
        if url.endswith(f"/books/{book_id}/decrement"):
            return FakeResp(200)
        return FakeResp(200, ok=True)

    monkeypatch.setattr(module.requests, "put", fake_put, raising=True)

    module.process_order(ch, method, None, _body(order_id=order_id, book_id=book_id, qty=qty))

    assert sequence == [
        (f"{module.BOOKS_URL}/{book_id}/decrement", {"quantity_ordered": qty}),
        (f"{module.ORDERS_URL}/{order_id}", {"status": "completed"}),
    ]
    assert ch.acks == [method.delivery_tag]
