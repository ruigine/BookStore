# Place Order Service API

_Last updated: 2025-08-12_

A microservice built with Python Flask + SQLAlchemy, which **creates orders on behalf of the authenticated user** and publishes an order message to RabbitMQ for downstream processing.  
Also exposes helpers to check an order’s status and to see if the current user has a pending order for a specific book.

## Overview

- **Default port (dev):** `5004`
- **Base URL (examples):** `http://localhost:5004`
- **Auth:** `Authorization: Bearer <access-token>` (validated via shared `@jwt_required`)
- **Upstream dependency:** **Orders** service at `http://orders:5003/orders`
- **Health endpoint:** `/health`

## Environment Variables

- `JWT_SECRET_KEY` — HMAC secret used to sign JWTs
- `RABBITMQ_DEFAULT_USER` — RabbitMQ username (for publisher connection)
- `RABBITMQ_DEFAULT_PASS` — RabbitMQ password (for publisher connection)

**RabbitMQ defaults (from the shared client):**
- Host: `rabbitmq`, Port: `5672`
- Exchange: `orders` (type: `direct`), Queue: `order_queue`
- Routing key when publishing: `order.new`
- Durable exchange/queue; messages are published as persistent

---

## Data Model (from upstream Orders service)

This service **does not** store data; it posts to the Orders service which returns an Order payload like:

```json
{
  "order_id": 11,
  "book_id": 13,
  "user_id": 42,
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

### 1) `GET /health`

Liveness check.

**Response**

- `200 OK`

```json
{ "status": "ok" }
```

---

### 2) `POST /placeorder`  _(requires JWT access token)_

Create an order for the **current user** by forwarding to the Orders service, then publish the created order to RabbitMQ.

**Headers**

- `Authorization: Bearer <access-token>` — must be an **access** token (JWT claim `type: "access"`).

**Request body (JSON)**

> The service injects `user_id` from the token’s `sub` claim and forces `status: "pending"`.

| Field       | Type    | Required | Notes                                 |
|-------------|---------|----------|---------------------------------------|
| `book_id`   | int     | yes      |                                       |
| `price`     | number  | yes      | price at time of order                |
| `quantity`  | int     | yes      |                                       |
| `title`     | string  | yes      | book title snapshot                   |
| `authors`   | string  | no       | comma-separated names       |
| `url`       | string  | no       | book cover URL           |

**Behavior**

1. Builds `order_payload` with `user_id = request.user["sub"]` and `status = "pending"`.
2. `POST http://orders:5003/orders` with the payload.
3. If upstream returns **201**, publish the returned order JSON to RabbitMQ (`exchange: orders`, `routing_key: order.new`), and return the same order JSON with **201**.
4. If upstream is not **201**, return the upstream JSON and status **unchanged**.
5. On exception, return **500** with `{ "code": 500, "message": "An error occurred: ..." }`.

**Responses**

- `201 Created`

```json
{
  "code": 201,
  "data": { /* Order JSON from Orders service */ }
}
```

- Non-201 from upstream — same JSON/status as upstream.
- `500 Internal Server Error` — unexpected exception.

**Example**

```bash
curl -X POST "http://localhost:5004/placeorder"   -H "Authorization: Bearer $ACCESS_TOKEN"   -H "Content-Type: application/json"   -d '{
    "book_id": 123,
    "price": 24.90,
    "quantity": 1,
    "title": "Example Book",
    "authors": "Author One",
    "url": "https://example.com/cover.jpg"
  }'
```

---

### 3) `GET /checkorder/<order_id>`  _(requires JWT)_

Fetch an order from the Orders service and return **only** the `order_id` and `status`, **but only if it belongs to the current user**.

**Path params**

- `order_id` — integer, required

**Behavior**

- Calls `GET http://orders:5003/orders/{order_id}`.
- If not `200`, returns the upstream JSON/status.
- If `order.user_id` != authenticated `sub`, returns **403**:

```json
{ "code": 403, "message": "Forbidden. Order does not belong to this user." }
```

- If OK and authorized, returns:

```json
{
  "code": 200,
  "data": { "order_id": 11, "status": "pending" }
}
```

**Example**

```bash
curl -H "Authorization: Bearer $ACCESS_TOKEN"   "http://localhost:5004/checkorder/11"
```

---

### 4) `GET /pendingorder/<book_id>`  _(requires JWT)_

Check if the current user has a **pending** order for the **given book**. Proxies directly to Orders:

- `GET http://orders:5003/orders/user/{sub}/book/{book_id}`

**Responses**

- Upstream passthrough, e.g.:

```json
{ "code": 200, "hasPending": false }
```

or

```json
{
  "code": 200,
  "hasPending": true,
  "data": { /* Order JSON */ }
}
```

**Example**

```bash
curl -H "Authorization: Bearer $ACCESS_TOKEN"   "http://localhost:5004/pendingorder/123"
```

---

## RabbitMQ Publisher Behavior

- On successful order creation, the **entire order JSON** is published to the exchange `orders` with routing key `order.new`.
- Exchange and queue are declared as **durable**; messages marked **persistent**.
- Connection is resilient: the client retries connection/channel setup.

**Consumer Example (pseudo-Python)**

```python
def process_order(ch, method, properties, body):
    data = json.loads(body)
    # ... process order (e.g., charge, decrement stock, send email) ...
    ch.basic_ack(delivery_tag=method.delivery_tag)
```

---

## Error Format

Errors are JSON with an HTTP status, e.g.:

```json
{ "code": 500, "message": "An error occurred: <details>" }
```

---

## Example Docker

```yaml
services:
  placeorder:
    build: .
    environment:
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - RABBITMQ_DEFAULT_USER=${RABBITMQ_DEFAULT_USER}
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_DEFAULT_PASS}
    ports:
      - "5004:5004"

  orders:
    # ...

  rabbitmq:
    image: rabbitmq:3-management
    environment:
      - RABBITMQ_DEFAULT_USER=${RABBITMQ_DEFAULT_USER}
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_DEFAULT_PASS}
    ports:
      - "5672:5672"
      - "15672:15672"
```

## Security Notes

- This service always uses the authenticated token’s `sub` and **does not accept** a `user_id` in request bodies.
- Keep the Orders service internal (reachable via service DNS like `orders`) and avoid exposing it publicly.
- Ensure appropriate auth/ACLs for RabbitMQ management UI if exposed.

## Changelog

- v1.0 — Initial public documentation.
