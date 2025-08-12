import sys
import types
import pytest

# --- Stub the RabbitMQ client BEFORE importing order_processing.app ---
# Create a fake "shared" package and "shared.rabbitmq" submodule
shared_pkg = types.ModuleType("shared")
rabbitmq_mod = types.ModuleType("shared.rabbitmq")

class DummyRabbitMQClient:
    def __init__(self, *_, **__):
        self.consumed = None
    def consume(self, handler):
        # record the handler
        self.consumed = handler

rabbitmq_mod.RabbitMQClient = DummyRabbitMQClient
shared_pkg.rabbitmq = rabbitmq_mod

sys.modules.setdefault("shared", shared_pkg)
sys.modules.setdefault("shared.rabbitmq", rabbitmq_mod)

import order_processing.app as op_app  # noqa: E402


@pytest.fixture(autouse=True)
def no_sleep(monkeypatch):
    """Make time.sleep a no-op to keep tests fast."""
    monkeypatch.setattr(op_app.time, "sleep", lambda *_: None, raising=True)


@pytest.fixture()
def module():
    """Expose the imported module."""
    return op_app


@pytest.fixture()
def fake_ch_method():
    """A fake AMQP channel + method with ack tracking."""
    class Ch:
        def __init__(self):
            self.acks = []
        def basic_ack(self, delivery_tag):
            self.acks.append(delivery_tag)

    class Method:
        def __init__(self, tag=123):
            self.delivery_tag = tag

    return Ch(), Method()
