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
            return FakeResp(409, payload={"code": 409, "message": "New quantity should not go below 0."})
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
    calls = []

    def fake_put(url, json=None):
        calls.append((url, json))
        # fail to reach books
        if url.endswith("/books/500/decrement"):
            raise RuntimeError("network down")
        # Orders status update succeeds
        return FakeResp(200, ok=True)

    monkeypatch.setattr(module.requests, "put", fake_put, raising=True)

    module.process_order(ch, method, None, _body(order_id=3, book_id=500, qty=1))

    # 1) tried to decrement stock
    assert calls[0][0] == f"{module.BOOKS_URL}/500/decrement"
    # 2) then marked the order failed
    assert calls[1][0] == f"{module.ORDERS_URL}/3"
    assert calls[1][1].get("status") == "failed"
    # guard against extra unexpected calls
    assert len(calls) == 2
    # always ack
    assert ch.acks == [method.delivery_tag]
