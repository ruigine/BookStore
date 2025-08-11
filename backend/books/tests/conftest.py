# Purpose: Test fixtures. Creates a Flask test client wired to an in-memory SQLite DB,
# seeds a few Book rows, and tears everything down after each test.

import os
import pytest

# Make sure the app reads an in-memory DB **at import time**
os.environ["dbURL"] = "sqlite:///:memory:"

from books.app import app as flask_app
from books.model import db, Book

@pytest.fixture()
def client():
    """Flask test client with a fresh SQLite schema + seeded data."""
    with flask_app.app_context():
        db.create_all()

        # Seed a few books (adjust fields to match your Book model)
        books = [
            Book(title="The Wizard of Oz", authors="L. Frank Baum", ISBN="111",
                 price=9.99, genre="Fantasy", quantity=3, url="/img/oz.png"),
            Book(title="Deep Space", authors="A. Nova", ISBN="222",
                 price=14.50, genre="Sci-Fi", quantity=5, url="/img/space.png"),
            Book(title="Detective Tales", authors="J. Doe", ISBN="333",
                 price=7.25, genre="Mystery", quantity=1, url="/img/detective.png"),
        ]
        db.session.add_all(books)
        db.session.commit()

        yield flask_app.test_client()

        # Clean up
        db.session.remove()
        db.drop_all()
