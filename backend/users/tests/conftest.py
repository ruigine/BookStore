import os
import sys
import pytest

# Configure env BEFORE importing the app
os.environ["dbURL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET_KEY"] = "test-secret"

from users.app import app as flask_app  # noqa: E402
from users.model import db, User        # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402


@pytest.fixture()
def client():
    """Plain Flask test client"""
    with flask_app.app_context():
        db.create_all()
        try:
            yield flask_app.test_client()
        finally:
            db.session.remove()
            db.drop_all()


@pytest.fixture()
def seed_user():
    """Create a user and return plain data (no ORM instance) to avoid detachment."""
    raw = "secret123"
    with flask_app.app_context():
        u = User(
            username="alice",
            email="alice@example.com",
            password_hash=generate_password_hash(raw),
        )
        db.session.add(u)
        db.session.commit()
        return {
            "user_id": u.user_id,
            "email": u.email,
            "username": u.username,
            "password": raw,
        }
