import pytest

from place_order.app import app as flask_app


@pytest.fixture()
def client():
    """Plain Flask test client."""
    return flask_app.test_client()
