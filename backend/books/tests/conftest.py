# Purpose: Test fixtures. Wires Flask to in-memory SQLite, seeds books, and returns a test client.
import os
from decimal import Decimal
import pytest

# Ensure the app reads an in-memory DB before import
os.environ["dbURL"] = "sqlite:///:memory:"

from books.app import app as flask_app  # noqa: E402
from books.model import db, Book        # noqa: E402


@pytest.fixture()
def client():
    """Flask test client with a fresh SQLite schema + seeded data."""
    with flask_app.app_context():
        db.create_all()

        # Seed diverse rows for all filters/searches
        books = [
            Book(
                title="The Wizard of Oz",
                description="A classic fantasy tale of Dorothy's journey in Oz.",
                ISBN="111",
                authors="L. Frank Baum",
                publishers="George M. Hill",
                format="Paperback",
                genre="Fantasy",
                price=Decimal("9.99"),
                quantity=3,
                url="/img/oz.png",
            ),
            Book(
                title="Deep Space",
                description="A starship crew explores distant galaxies and strange phenomena.",
                ISBN="222",
                authors="A. Nova",
                publishers="Stellar Press",
                format="Hardcover",
                genre="Sci-Fi",
                price=Decimal("14.50"),
                quantity=5,
                url="/img/space.png",
            ),
            Book(
                title="Detective Tales",
                description="Short mysteries featuring a sharp-eyed sleuth solving tough cases.",
                ISBN="333WZ",
                authors="J. Doe",
                publishers="Cloak & Dagger",
                format="Paperback",
                genre="Mystery",
                price=Decimal("7.25"),
                quantity=1,
                url="/img/detective.png",
            ),
            Book(
                title="Budget Cooking",
                description="Affordable, quick recipes with simple ingredients for everyday meals.",
                ISBN="444",
                authors="Chef A",
                publishers="Kitchen Table",
                format="Paperback",
                genre="Non-fiction",
                price=Decimal("4.00"),
                quantity=10,
                url="/img/cook.png",
            ),
            Book(
                title="Premium Atlas",
                description="A richly illustrated world atlas with detailed maps and infographics.",
                ISBN="555",
                authors="Carto B",
                publishers="Mapwright House",
                format="Hardcover",
                genre="Non-fiction",
                price=Decimal("99.99"),
                quantity=2,
                url="/img/atlas.png",
            ),
        ]
        db.session.add_all(books)
        db.session.commit()

        yield flask_app.test_client()

        db.session.remove()
        db.drop_all()
