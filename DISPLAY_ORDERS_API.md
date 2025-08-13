# Display Orders Service API

_Last updated: 2025-08-12_

A microservice built with Python Flask + SQLAlchemy for retrieving a user's orders.
It authenticates the caller (JWT) and forwards requests to the Orders service, returning the downstream payload and status **unchanged**.

## Overview

- **Default port (dev):** `5005`
- **Base URL (examples):** `http://localhost:5005`
- **Environment:**
  - `dbURL` — SQLAlchemy database URI (e.g., `mysql+mysqlconnector://user:pass@host/db`)
  - `JWT_SECRET_KEY` — HMAC secret used to sign JWTs
- **Auth:** `Authorization: Bearer <access-token>` (validated by shared `@jwt_required`)
- **Upstream dependency:** Orders service at `http://orders:5003`
- **Health endpoint:** `/health`

---

## Endpoints

### 1) `GET /health`

Liveness check.

**Response**

- `200 OK`

```json
{ "status": "ok" }
```

---

### 2) `GET /myorders`  _(requires JWT access token)_

Returns the current user’s orders by calling the Orders service:  
`GET http://orders:5003/orders/user/{user_id}`

The `user_id` is taken from the JWT claim `sub`. This service **does not** accept a `user_id` query param for security — it always uses the authenticated user.

**Headers**

- `Authorization: Bearer <access-token>` — access token with `sub` claim

**Query parameters (optional)** — forwarded to upstream

| Name    | Type | Example | Notes                                    |
|---------|------|---------|------------------------------------------|
| `page`  | int  | `2`     | Page index       |
| `limit` | int  | `6`     | Page size        |

**Behavior**

- Builds the upstream URL as `http://orders:5003/orders/user/{sub}[?page=&limit=]`
- Performs `GET` with no auth to the upstream (trusted internal network) with user_id from token
- Returns **exactly** the upstream JSON and HTTP status code
- On internal exception, returns `500` with `{ "code": 500, "message": "An error occurred: ..." }`

**Responses (examples)**

> Without pagination:

```json
{
  "code": 200,
  "data": [
    {
      "order_id": 11,
      "book_id": 12,
      "user_id": 42,
      "price": 24.90,
      "quantity": 1,
      "status": "pending",
      "title": "Example Book",
      "authors": "Author One",
      "url": "/images/books/0521402301.jpg",
      "order_date": "Tue, 12 Aug 2025 22:19:44 GMT"
    }
  ]
}
```

> With pagination (when `page`/`limit` are provided):

```json
{
  "code": 200,
  "data": [ /* array of order objects */ ],
  "pagination": {
    "page": 2,
    "limit": 6,
    "total": 12,
    "has_more": true
  }
}
```

**Error passthrough**

- If upstream returns non-200, that JSON and status are returned as-is
- On exception here, returns:

```json
{
  "code": 500,
  "message": "An error occurred: <details>"
}
```

**Examples**

```bash
# All orders for the authenticated user
curl -H "Authorization: Bearer $ACCESS_TOKEN"   "http://localhost:5005/myorders"

# Paginated
curl -H "Authorization: Bearer $ACCESS_TOKEN"   "http://localhost:5005/myorders?page=2&limit=6"
```

---

## Auth & JWT Expectations

- The `jwt_required` decorator validates the access token and attaches the decoded payload to `request.user`.
- The service uses `request.user["sub"]` as the `user_id` to build the upstream URL.
- Access tokens should be issued by your Users service and include a `type` claim of `"access"` and a `sub` claim (user id).

---

## Example Docker

```yaml
  displayorders:
    build: .
    environment:
      - dbURL=${dbURL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    ports:
      - "5005:5005"
    # ...
```

## Notes

- It always uses the authenticated `sub` to determine the user in upstream requests.
- CORS is enabled for all routes, so the frontend can call it directly.

## Changelog

- v1.0 — Initial public documentation.
