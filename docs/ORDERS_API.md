# Orders Service API

_Last updated: 2025-08-12_

Order management microservice built with Python Flask + SQLAlchemy.  
Provides order creation, status updates, single-order retrieval, user order listing (with optional pagination), and a helper to check if a user has a **pending** order for a specific book.

## Overview

- **Default port (dev):** `5003`
- **Base URL (examples):** `http://localhost:5003`
- **Environment:** `dbURL` — SQLAlchemy database URI (e.g., `mysql+mysqlconnector://user:pass@host/db`  )
- **CORS:** Enabled for all routes

---

## Data Model

**Order**

| Field        | Type             | Required | Notes                            |
|--------------|------------------|----------|----------------------------------|
| `order_id`   | integer (PK)     | yes      | Auto-increment                   |
| `book_id`    | integer          | yes      |                                  |
| `user_id`    | integer          | yes      |                                  |
| `price`      | numeric(10,2)    | yes      | Price of book at time of order           |
| `quantity`   | integer          | yes      |  Quantity ordered                                |
| `status`     | string(20)       | yes      | e.g., `pending`, `completed`, `failed`     |
| `title`      | string(255)      | yes      | Book title (snapshot)             |
| `authors`    | text             | no       | Comma-separated author names (snapshot)     |
| `url`        | text             | no       | Cover image  URL        |
| `order_date` | datetime         | yes      | Defaults to current time           |

**JSON representation (returned by API):**

```json
{
  "order_id": 10,
  "book_id": 12,
  "user_id": 7,
  "price": 24.90,
  "quantity": 1,
  "status": "pending",
  "title": "Example Book",
  "authors": "Author One, Author Two",
  "url": "/images/books/0521402301.jpg",
  "order_date": "Tue, 12 Aug 2025 22:19:44 GMT"
}
```

---

## Endpoints

### 1) `POST /orders`

Create a new order.

**Request body (JSON)**

| Field       | Type          | Required | Constraints/Notes                    |
|-------------|---------------|----------|--------------------------------------|
| `book_id`   | integer       | yes      |                                      |
| `user_id`   | integer       | yes      |                                      |
| `price`     | number        | yes      | numeric(10,2)                        |
| `quantity`  | integer       | yes      |                                      |
| `status`    | string        | yes      | e.g., `pending`                      |
| `title`     | string        | yes      | book title snapshot                   |
| `authors`   | string        | yes       | author snapshot                              |
| `url`       | string        | yes       |                               |

**Responses**

- `201 Created`

```json
{ "code": 201, "data": { /* Order JSON */ } }
```

- `500 Internal Server Error` — unexpected error.

**Example**

```bash
curl -X POST "http://localhost:5003/orders"   -H "Content-Type: application/json"   -d '{ 
    "book_id": 13,
    "user_id": 7,
    "price": 24.90,
    "quantity": 1,
    "status": "pending",
    "title": "Example Book",
    "authors": "Author One",
    "url": "/images/books/0521402301.jpg"
  }'
```

---

### 2) `PUT /orders/<order_id>`

Update an order’s `status` field.

**Path params**

- `order_id` — integer, required

**Request body (JSON)**

| Field    | Type   | Required | Notes                  |
|----------|--------|----------|------------------------|
| `status` | string | yes      | New status value  |

**Responses**

- `200 OK`

```json
{ "code": 200, "data": { /* Order JSON */ } }
```

- `404 Not Found` — Order not found.
- `500 Internal Server Error` — unexpected error.

**Example**

```bash
curl -X PUT "http://localhost:5003/orders/1001"   -H "Content-Type: application/json"   -d '{ "status": "completed" }'
```

---

### 3) `GET /orders/<order_id>`

Fetch an order by ID.

**Responses**

- `200 OK`

```json
{ "code": 200, "data": { /* Order JSON */ } }
```

- `404 Not Found` — Order not found.
- `500 Internal Server Error` — unexpected error.

**Example**

```bash
curl "http://localhost:5003/orders/11"
```

---

### 4) `GET /orders/user/<user_id>`

List orders of a user, ordered by most recent. Supports optional pagination.

**Query parameters (optional)**

| Name    | Type | Default | Notes                                |
|---------|------|---------|--------------------------------------|
| `page`  | int  | `1`     | Page index                   |
| `limit` | int  | `4`     | Page size                            |

**Responses**

- Without pagination params:

```json
{ "code": 200, "data": [ /* Order JSON */ ] }
```

- With pagination params:

```json
{
  "code": 200,
  "data": [ /* Order JSON */ ],
  "pagination": {
    "page": 1,
    "limit": 4,
    "total": 12,
    "has_more": true
  }
}
```

- `500 Internal Server Error` — unexpected error.

**Example**

```bash
# All orders
curl "http://localhost:5003/orders/user/7"

# Page 2, limit 6
curl "http://localhost:5003/orders/user/7?page=2&limit=6"
```

---

### 5) `GET /orders/user/<user_id>/book/<book_id>`

Check if a **user** has a **pending** order for a **given book**. Returns a boolean flag and the order if one exists.

**Responses**

- If a pending order exists:

```json
{
  "code": 200,
  "hasPending": true,
  "data": { /* Order JSON */ }
}
```

- If no pending order exists:

```json
{ "code": 200, "hasPending": false }
```

- `500 Internal Server Error` — unexpected error.

**Example**

```bash
curl "http://localhost:5003/orders/user/7/book/12"
```

---

## Error Format

Errors are returned as JSON with an HTTP status code, e.g.:

```json
{ "code": 404, "message": "Order not found." }
```

---

## Example Docker

```yaml
services:
  orders:
    build: .
    environment:
      - dbURL=${dbURL}
    # this API is not authenticated
    # (ports are not meant to be exposed)
    ports:
      - "5003:5003"
```

## Notes & Conventions

- Success responses follow `{ "code": 200|201, "data": ... }`, with pagination metadata where relevant.
- Orders are returned in descending `order_date` for user lists.
- `status` values are free-form strings; commonly `pending`, `completed`, etc..
- CORS is enabled for all endpoints.
- Orders Service API is not secured by JWT token as ports are not meant to be exposed.

## Changelog

- v1.0 — Initial public documentation.
