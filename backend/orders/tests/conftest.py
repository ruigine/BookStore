import os
import pytest
from decimal import Decimal
from datetime import datetime, timedelta

# Use an in-memory DB for tests
os.environ["dbURL"] = "sqlite:///:memory:"

from orders.app import app as flask_app  # noqa: E402
from orders.model import db, Order       # noqa: E402


@pytest.fixture()
def client():
    with flask_app.app_context():
        db.create_all()
        try:
            yield flask_app.test_client()
        finally:
            db.session.remove()
            db.drop_all()


@pytest.fixture()
def seed_orders():
    """Insert a small set of orders for two users. Return plain dicts."""
    rows = []
    with flask_app.app_context():
        # fixed timestamps (for most recent first)
        t0 = datetime(2024, 1, 1, 12, 0, 0)
        orders = [
            # user 1
            Order(book_id=101, user_id=1, price=Decimal("9.99"),  quantity=1, status="pending",
                  title="Budget Cooking", authors="Chef A", url="/img/cook.png"),
            Order(book_id=102, user_id=1, price=Decimal("14.50"), quantity=2, status="completed",
                  title="Deep Space", authors="A. Nova", url="/img/space.png"),
            Order(book_id=103, user_id=1, price=Decimal("7.25"),  quantity=1, status="failed",
                  title="Detective Tales", authors="J. Doe", url="/img/detective.png"),
            # user 2
            Order(book_id=201, user_id=2, price=Decimal("99.99"), quantity=1, status="pending",
                  title="Premium Atlas", authors="Carto B", url="/img/atlas.png"),
        ]
        for i, o in enumerate(orders):
            # give ascending times to check desc(order_date)
            o.order_date = t0 + timedelta(minutes=i)
            db.session.add(o)
        db.session.commit()

        for o in orders:
            rows.append({
                "order_id": o.order_id,
                "book_id": o.book_id,
                "user_id": o.user_id,
                "price": o.price,           # Decimal
                "quantity": o.quantity,
                "status": o.status,
                "title": o.title,
                "authors": o.authors,
                "url": o.url,
                "order_date": o.order_date, # datetime
            })
    return rows
