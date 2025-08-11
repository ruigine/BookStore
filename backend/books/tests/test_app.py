# Purpose: Cover all routes in books/app.py (success + error branches).
import json
import pytest
from typing import Set
import urllib.parse
from books.model import Book
from decimal import Decimal


@pytest.mark.unit
def test_book_json_includes_all_fields_and_values():
    b = Book(
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
    )
    
    # simulate DB autoincrement
    b.book_id = 3

    j = b.json()
    assert j == {
        "book_id": 3,
        "title": "Detective Tales",
        "description": "Short mysteries featuring a sharp-eyed sleuth solving tough cases.",
        "ISBN": "333WZ",
        "authors": "J. Doe",
        "publishers": "Cloak & Dagger",
        "format": "Paperback",
        "genre": "Mystery",
        "price": Decimal("7.25"),
        "quantity": 1,
        "url": "/img/detective.png",
    }


@pytest.mark.unit
def test_book_json_keeps_optional_keys_when_none():
    b = Book(
        title="Untitled",
        description=None,
        ISBN="000",
        authors=None,
        publishers=None,
        format=None,
        genre="Fantasy",
        price=Decimal("1.00"),
        quantity=0,
        url=None,
    )
    b.book_id = 1

    j = b.json()

    # keys exist even if values are None
    for k in ["description", "authors", "publishers", "format", "url"]:
        assert k in j

    # spot-check a few values/types
    assert j["book_id"] == 1
    assert j["title"] == "Untitled"
    assert j["ISBN"] == "000"
    assert j["genre"] == "Fantasy"
    assert j["price"] == Decimal("1.00")
    assert j["quantity"] == 0


@pytest.mark.integration
def test_get_books_defaults(client):
    res = client.get("/books")
    assert res.status_code == 200
    body = res.get_json()

    # top-level response
    assert body["code"] == 200
    assert isinstance(body["data"], list)

    # pagination defaults
    pg = body["pagination"]
    assert pg["page"] == 1
    assert pg["limit"] == 8
    assert pg["total"] == 5          # seeded 5 rows in conftest
    assert pg["has_more"] is False

    # exactly 5 books returned
    books = body["data"]
    assert len(books) == 5

    # expected fields from your Book model/json
    expected_fields: Set[str] = {
        "book_id", "title", "description", "ISBN", "authors",
        "publishers", "format", "genre", "price", "quantity", "url",
    }

    for b in books:
        # has all required keys
        assert expected_fields.issubset(b.keys())

        # light sanity checks
        assert isinstance(b["title"], str)
        assert isinstance(b["authors"], str)
        assert isinstance(b["ISBN"], str)
        assert isinstance(b["genre"], str)
        assert isinstance(b["quantity"], int)
        assert isinstance(b["url"], str)

        # price may be float or string;
        _ = float(b["price"])


@pytest.mark.integration
def _first_book(client):
    out = client.get("/books?limit=1").get_json()
    assert out["code"] == 200
    assert out["data"], "Expected at least one seeded book"
    return out["data"][0]


@pytest.mark.integration
def test_get_books_with_pagination(client):
    # page 2
    res = client.get("/books?page=2&limit=2")
    assert res.status_code == 200
    body = res.get_json()
    assert body["code"] == 200
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 2
    assert body["pagination"]["page"] == 2
    assert body["pagination"]["limit"] == 2
    assert body["pagination"]["total"] == 5
    assert body["pagination"]["has_more"] is True

    # page 3
    res = client.get("/books?page=3&limit=2")
    assert res.status_code == 200
    body = res.get_json()
    assert body["code"] == 200
    assert isinstance(body["data"], list)
    assert len(body["data"]) == 1
    assert body["pagination"]["page"] == 3
    assert body["pagination"]["limit"] == 2
    assert body["pagination"]["total"] == 5
    assert body["pagination"]["has_more"] is False


@pytest.mark.integration
def test_get_books_genre_filter(client):
    res = client.get("/books?genre=Non-fiction")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert len(data) == 2
    assert all(b["genre"] == "Non-fiction" for b in data)


@pytest.mark.integration
def test_get_books_price_filters(client):
    # min only
    res = client.get("/books?min_price=10")
    data = res.get_json()["data"]
    assert res.status_code == 200
    assert len(data) == 2
    assert all(float(b["price"]) >= 10 for b in data)

    # max only
    res = client.get("/books?max_price=10")
    data = res.get_json()["data"]
    assert res.status_code == 200
    assert len(data) == 3
    assert all(float(b["price"]) <= 10 for b in data)

    # both
    res = client.get("/books?min_price=5&max_price=15")
    data = res.get_json()["data"]
    assert res.status_code == 200
    assert len(data) == 3
    assert all(5 <= float(b["price"]) <= 15 for b in data)


@pytest.mark.integration
def test_get_books_search_title_authors_isbn(client):
    # title
    res = client.get("/books?search=Wizard")
    data = res.get_json()["data"]
    assert res.status_code == 200
    assert len(data) == 1
    assert any("Wizard" in b["title"] for b in data)

    # authors
    res = client.get("/books?search=Nova")
    data = res.get_json()["data"]
    assert res.status_code == 200
    assert len(data) == 1
    assert any("Nova" in b["authors"] for b in data)

    # ISBN
    res = client.get("/books?search=WZ")
    data = res.get_json()["data"]
    assert res.status_code == 200
    assert len(data) == 1
    assert any("WZ" in b["ISBN"] for b in data)


@pytest.mark.integration
@pytest.mark.integration
def test_filters_combined(client):
    params = {
        "genre": "Non-fiction",
        "min_price": 5,
        "max_price": 100,
        "search": "Atlas",
        "page": 1,
        "limit": 999
    }
    qs = urllib.parse.urlencode(params)
    res = client.get(f"/books?{qs}")
    assert res.status_code == 200
    body = res.get_json()
    assert body["code"] == 200

    titles = {b["title"] for b in body["data"]}
    assert titles == {"Premium Atlas"}
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["limit"] == 999
    assert body["pagination"]["total"] == len(body["data"])
    assert body["pagination"]["has_more"] is False


@pytest.mark.integration
def test_books_ignores_invalid_query_params(client):

    def assert_default_response(res):
        body = res.get_json()
        assert body["code"] == 200
        pg = body["pagination"]
        assert pg["page"] == 1
        assert pg["limit"] == 8
        assert pg["total"] == 5
        assert pg["has_more"] is False
        assert len(body["data"]) == min(8, 5)

    # A) Non-numeric page/limit
    q = urllib.parse.urlencode({"page": "abc", "limit": "zzz"})
    res = client.get(f"/books?{q}")
    assert res.status_code == 200
    assert_default_response(res)

    # B) Non-numeric min/max
    q = urllib.parse.urlencode({"min_price": "ten", "max_price": "five"})
    res = client.get(f"/books?{q}")
    assert res.status_code == 200
    assert_default_response(res)

    # C) Unknown params
    res = client.get("/books?foo=bar&bar=baz")
    assert res.status_code == 200
    assert_default_response(res)

    # D) Nonsensical range: min > max -> empty set (but still 200)
    q = urllib.parse.urlencode({"min_price": 1000, "max_price": 1, "limit": 999})
    res = client.get(f"/books?{q}")
    assert res.status_code == 200
    body = res.get_json()
    assert body["code"] == 200
    assert body["data"] == []
    assert body["pagination"]["total"] == 0
    assert body["pagination"]["has_more"] is False


@pytest.mark.integration
def test_get_book_by_id_found(client):
    res = client.get(f"/books/3")
    data = res.get_json()["data"]
    assert res.status_code == 200
    assert data["book_id"] == 3
    assert data["title"] == "Detective Tales"
    assert data["description"] == "Short mysteries featuring a sharp-eyed sleuth solving tough cases."
    assert data["ISBN"] == "333WZ"
    assert data["authors"] == "J. Doe"
    assert data["publishers"] == "Cloak & Dagger"
    assert data["format"] == "Paperback"
    assert data["genre"] == "Mystery"
    assert float(data["price"]) == 7.25
    assert data["quantity"] == 1
    assert data["url"] == "/img/detective.png"


@pytest.mark.integration
def test_get_book_by_id_not_found(client):
    res = client.get("/books/999999")
    assert res.status_code == 404
    j = res.get_json()
    assert j["code"] == 404
    assert "not found" in j["message"].lower()


@pytest.mark.integration
def test_decrement_invalid_quantities(client):
    first = _first_book(client)
    bid = first.get("book_id")

    # missing body
    r = client.put(f"/books/{bid}/decrement", data="{}", content_type="application/json")
    assert r.status_code == 400

    # non-int
    r = client.put(f"/books/{bid}/decrement",
                   data=json.dumps({"quantity_ordered": "two"}),
                   content_type="application/json")
    assert r.status_code == 400

    # zero
    r = client.put(f"/books/{bid}/decrement",
                   data=json.dumps({"quantity_ordered": 0}),
                   content_type="application/json")
    assert r.status_code == 400

    # negative
    r = client.put(f"/books/{bid}/decrement",
                   data=json.dumps({"quantity_ordered": -1}),
                   content_type="application/json")
    assert r.status_code == 400


@pytest.mark.integration
def test_decrement_not_found(client):
    r = client.put("/books/999999/decrement",
                   data=json.dumps({"quantity_ordered": 1}),
                   content_type="application/json")
    assert r.status_code == 404


@pytest.mark.integration
def test_decrement_conflict_and_success(client):
    # pick a book with quantity >= 2 (Sci-Fi was seeded with 5)
    sci = next(b for b in client.get("/books").get_json()["data"] if b["genre"] == "Sci-Fi")
    bid = sci.get("book_id")

    # oversubscribe
    r = client.put(f"/books/{bid}/decrement",
                   data=json.dumps({"quantity_ordered": sci["quantity"] + 1}),
                   content_type="application/json")
    assert r.status_code == 409

    # happy path: decrement by 2
    r = client.put(f"/books/{bid}/decrement",
                   data=json.dumps({"quantity_ordered": 2}),
                   content_type="application/json")
    assert r.status_code == 200
    after_qty = r.get_json()["data"]["quantity"]
    assert after_qty == sci["quantity"] - 2


@pytest.mark.integration
def test_get_books_exception_path(monkeypatch, client):
    # Patch the Book symbol inside books.app so .count() raises → triggers except: 500
    import books.app as app_module

    class DummyQuery:
        def filter(self, *_, **__): return self
        def count(self): raise RuntimeError("boom")
        def offset(self, *_): return self
        def limit(self, *_): return self
        def all(self): return []

    class DummyBook:
        query = DummyQuery()

    monkeypatch.setattr(app_module, "Book", DummyBook, raising=False)

    r = client.get("/books")
    assert r.status_code == 500
    assert "An error occurred" in r.get_json()["message"]


@pytest.mark.integration
def test_get_book_by_id_exception_path(monkeypatch, client):
    # Patch db.session.get to raise → triggers except: 500
    import books.app as app_module

    def boom(*_, **__):
        raise RuntimeError("boom")

    monkeypatch.setattr(app_module.db.session, "get", boom, raising=True)

    r = client.get("/books/1")
    assert r.status_code == 500
    assert "An error occurred" in r.get_json()["message"]


@pytest.mark.integration
def test_decrement_commit_exception(monkeypatch, client):
    # Cause commit to fail → triggers except: 500
    import books.app as app_module

    # Ensure a valid book exists
    first = _first_book(client)
    bid = first.get("book_id")

    def boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(app_module.db.session, "commit", boom, raising=True)

    r = client.put(f"/books/{bid}/decrement",
                   data=json.dumps({"quantity_ordered": 1}),
                   content_type="application/json")
    assert r.status_code == 500
    assert "An error occurred" in r.get_json()["message"]
