# Purpose: Simple route tests to prove your service works:
# - list books with pagination
# - fetch by id (found + not found)
# - decrement quantity (happy path, invalid qty, oversubscribe)

import json


def test_list_books_basic(client):
    res = client.get("/books?page=1&limit=2")
    assert res.status_code == 200
    body = res.get_json()
    assert body["code"] == 200
    assert "data" in body and isinstance(body["data"], list)
    assert "pagination" in body
    # we seeded 3 rows; with limit=2 there should be has_more
    assert body["pagination"]["has_more"] is True


def test_filter_and_search(client):
    # genre filter
    res = client.get("/books?genre=Fantasy")
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert len(data) >= 1
    assert all(b["genre"] == "Fantasy" for b in data)

    # search across title/authors/ISBN
    res = client.get("/books?search=Wizard")
    assert res.status_code == 200
    titles = [b["title"] for b in res.get_json()["data"]]
    assert any("Wizard" in t for t in titles)


def test_get_book_by_id_found_and_not_found(client):
    # grab an id from list endpoint
    first = client.get("/books?limit=1").get_json()["data"][0]
    book_id = first["book_id"]

    ok = client.get(f"/books/{book_id}")
    assert ok.status_code == 200
    assert ok.get_json()["data"]["book_id"] == book_id

    not_found = client.get("/books/999999")
    assert not_found.status_code == 404
    assert not_found.get_json()["message"].lower().startswith("book")


def test_decrement_success_and_conflicts(client):
    # take a book with quantity >= 2 (we seeded Sci-Fi with 5)
    sci = next(b for b in client.get("/books").get_json()["data"] if b["genre"] == "Sci-Fi")
    book_id = sci["book_id"]

    # happy path: decrement by 2
    res = client.put(
        f"/books/{book_id}/decrement",
        data=json.dumps({"quantity_ordered": 2}),
        content_type="application/json",
    )
    assert res.status_code == 200
    new_qty = res.get_json()["data"]["quantity"]
    assert new_qty == sci["quantity"] - 2

    # invalid quantity (0 or negative) -> 400
    bad = client.put(
        f"/books/{book_id}/decrement",
        data=json.dumps({"quantity_ordered": 0}),
        content_type="application/json",
    )
    assert bad.status_code == 400

    # oversubscribe -> 409
    too_much = client.put(
        f"/books/{book_id}/decrement",
        data=json.dumps({"quantity_ordered": 999}),
        content_type="application/json",
    )
    assert too_much.status_code == 409
