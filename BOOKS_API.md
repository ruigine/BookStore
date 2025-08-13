# Books Service API

_Last updated: 2025-08-12_

A simple Python Flask + SQLAlchemy microservice that exposes a catalog of books with filtering, search, pagination, lookup by ID, and a quantity decrement operation.

## Overview

- **Default port:** `5002`
- **Base URL (examples):** `http://localhost:5002`
- **Environment:** set `dbURL` to a valid SQLAlchemy database URI (e.g., `mysql+mysqlconnector://user:pass@host/db`). The service reads this from the environment variable `dbURL`.
- **CORS:** Enabled for all routes.
- **Health endpoint:** `/health`

## Data Model

**Book**

| Field        | Type                | Required | Notes                    |
|--------------|---------------------|----------|--------------------------|
| `book_id`    | integer (PK)        | yes      | Auto-increment           |
| `title`      | string(255)         | yes      |                          |
| `description`| text                | no       |                          |
| `ISBN`       | string(20)          | yes      |                          |
| `authors`    | text                | no       | Comma-separated strings  |
| `publishers` | string(255)         | no       |                          |
| `format`     | string(50)          | no       | e.g., Paperback, eBook   |
| `genre`      | string(50)          | yes      |                          |
| `price`      | numeric(10,2)       | yes      |                          |
| `quantity`   | integer             | yes      | Current stock quantity        |
| `url`        | text                | no       | Cover image URL |

JSON representation returned by the API:

```json
{
  "book_id": 12,
  "title": "Example",
  "description": "…",
  "ISBN": "9781234567890",
  "authors": "Author One, Author Two",
  "publishers": "Pub House",
  "format": "Paperback",
  "genre": "Fantasy",
  "price": 19.99,
  "quantity": 42,
  "url": "/images/books/0521402301.jpg"
}
```

---

## Endpoints

### 1) `GET /health`

Simple liveness check.

**Response**

- `200 OK`

```json
{ "status": "ok" }
```

---

### 2) `GET /books`

List books with optional filters, search, and pagination.

**Query parameters**

| Name        | Type   | Required | Example           | Description                                              |
|-------------|--------|----------|-------------------|----------------------------------------------------------|
| `genre`     | string | no       | `Fantasy`         | Exact match on `genre`.                                  |
| `min_price` | number | no       | `10`              | Minimum price filter (`>=`).                             |
| `max_price` | number | no       | `50`              | Maximum price filter (`<=`).                             |
| `search`    | string | no       | `wizard`          | Case-insensitive search on `title`, `authors`, or `ISBN`.|
| `page`      | int    | no       | `1` (default)     | Page index.                                      |
| `limit`     | int    | no       | `8` (default)     | Items returned per page                                               |

**Response**

- `200 OK`

```json
{
  "code": 200,
  "data": [ /* array of Book JSON objects */ ],
  "pagination": {
    "page": 1,
    "limit": 8,
    "total": 60,
    "has_more": true
  }
}
```

**Errors**

- `500 Internal Server Error` — unexpected exception.

**Examples**

```bash
# Page 1, default limit
curl "http://localhost:5002/books"

# Filter by genre
curl "http://localhost:5002/books?genre=Fantasy"

# Price range + search
curl "http://localhost:5002/books?min_price=10&max_price=30&search=wizard"

# Pagination (page 2, 12 items per page)
curl "http://localhost:5002/books?page=2&limit=12"
```

---

### 3) `GET /books/<book_id>`

Returns a single book by id.

**Path params**

- `book_id` — integer, required

**Responses**

- `200 OK`

```json
{
  "code": 200,
  "data": { /* Book JSON */ }
}
```

- `404 Not Found`

```json
{
  "code": 404,
  "message": "Book was not found."
}
```

- `500 Internal Server Error` — unexpected exception.

**Example**

```bash
curl "http://localhost:5002/books/12"
```

---

### 4) `PUT /books/<book_id>/decrement`

Decrements stock quantity of a book by the integer amount in the request body.

**Path params**

- `book_id` — integer, required

**Request body (JSON)**

| Field               | Type | Required | Constraints     |
|---------------------|------|----------|-----------------|
| `quantity_ordered`  | int  | yes      | 0 < quantity_ordered <= avaiilable stock     |

**Responses**

- `200 OK`

```json
{
  "code": 200,
  "message": "Quantity updated to 37.",
  "data": { /* Book JSON after update */ }
}
```

- `400 Bad Request` — invalid quantity provided.

```json
{
  "code": 400,
  "message": "Invalid quantity provided. Must be more than 0."
}
```

- `404 Not Found` — book not found.

```json
{
  "code": 404,
  "message": "Book not found."
}
```

- `409 Conflict` — decrement would drive quantity below zero.

```json
{
  "code": 409,
  "message": "New quantity should not go below 0."
}
```

- `500 Internal Server Error` — unexpected exception.

**Example**

```bash
curl -X PUT "http://localhost:5002/books/123/decrement"   -H "Content-Type: application/json"   -d '{ "quantity_ordered": 5 }'
```

---

## Conventions & Notes

- All success responses wrap data as `{"code": 200, "data": ...}` and include pagination metadata for list endpoints.
- Errors return `{"code": <http-status-code>, "message": "<description>"}`.
- Search uses case-insensitive `ILIKE` for `title`, `authors`, and `ISBN` with `%<search>%` pattern.
- Pagination is implemented with `page`, `limit`, and `has_more` calculated as `(page-1)*limit + limit < total`.
- Quantity decrement uses a single transaction and will reject non-positive decrements or underflow attempts.
- CORS is enabled for all endpoints.


## Example Docker

> This service is commonly run via Docker Compose with other services.
> Replace the image/build context as needed.

```yaml
services:
  books:
    build: .
    environment:
      - dbURL=${BOOKS_DB_URL}
    ports:
      - "5002:5002"
```

## Changelog

- v1.0 — Initial public documentation.
