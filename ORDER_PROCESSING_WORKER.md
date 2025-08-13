# Order Processing (Worker) — Service README

_Last updated: 2025-08-12_

This is a **background worker** (not an HTTP API) that consumes order messages from RabbitMQ and orchestrates two actions:

1) **Decrement stock** in the Books service.  
2) **Update order status** in the Orders service (to `completed` on success, `failed` on error).

It is designed to run inside your Docker network alongside the **Orders**, **Place Orders** and **Books** services.

---

## Purpose & Responsibilities

- **Input:** Order message from RabbitMQ (published by the *Place Order* service).  
- **Process:** Wait ~5 seconds (simulated processing), decrement book quantity, then update order status.  
- **Output:** Side effects via HTTP requests to *Books* and *Orders* services; the worker **does not** expose HTTP endpoints or persist data.

---

## Message Contract (RabbitMQ)

**Exchange:** `orders` (type: `direct`)  
**Queue:** `order_queue` (durable)  
**Routing key (publisher):** `order.new`  
**Host / Port:** `rabbitmq:5672`  
**Content type:** JSON (UTF-8)

**Expected message shape (minimum required fields):**

```json
{
  "order_id": 1001,
  "book_id": 123,
  "quantity": 1,
  "user_id": 42,
  "price": 24.90,
  "status": "pending",
  "title": "Example Book",
  "authors": "Author One, Author Two",
  "url": "/images/books/0521402301.jpg",
  "order_date": "Tue, 12 Aug 2025 22:19:44 GMT"
}
```

---

## External Dependencies (HTTP calls)

### 1) Books service — decrement stock

```
PUT http://books:5002/books/{{book_id}}/decrement
Content-Type: application/json

{ "quantity_ordered": <quantity> }
```

- **Success:** HTTP `200` → continue to update order as `completed`.
- **Failure:** non-`200` → update order as `failed` and stop.

### 2) Orders service — set status

```
PUT http://orders:5003/orders/{{order_id}}
Content-Type: application/json

{ "status": "completed" | "failed" }
```

- Called once after a successful decrement (→ `completed`), or after any error (→ `failed`).

---

## Error Handling & Acknowledgement

- Any exception results in an attempt to mark the order **`failed`** and the message is **acknowledged** in a `finally` block.  
- **Ack policy:** The worker **always acks** the message, even on failures → **at-most-once** delivery semantics (no automatic retry/requeue).  
- Errors from downstream services are logged to stdout (container logs).

### Idempotency & Retries

- Not idempotent by default (the same message re-processed could double-decrement).  
- Because messages are always acked, failed cases are **not retried** by RabbitMQ.

---

## Configuration

Environment variables (used by the shared RabbitMQ client):

- `RABBITMQ_DEFAULT_USER` — username for RabbitMQ
- `RABBITMQ_DEFAULT_PASS` — password for RabbitMQ

Service endpoints (hard-coded defaults in code):

- `ORDERS_URL = http://orders:5003/orders`
- `BOOKS_URL  = http://books:5002/books`

> These DNS names resolve on the Docker Compose network. If you run locally **outside** Docker, point them to appropriate hosts (e.g., `http://localhost:5003` and `http://localhost:5002`) or add hosts entries.

---

**Docker Compose:**

```yaml
services:
  orderprocessing:
    build: .
    environment:
      - RABBITMQ_DEFAULT_USER=${RABBITMQ_DEFAULT_USER}
      - RABBITMQ_DEFAULT_PASS=${RABBITMQ_DEFAULT_PASS}

  rabbitmq:
    image: rabbitmq:3-management
    ports: ["5672:5672", "15672:15672"]

  orders:
    # your orders service...
  books:
    # your books service...
```

---

## Observability

- **Logs:** stdout/stderr (view via `docker logs`). Consider moving to structured logging (JSON) for easier parsing. 

---

## Security Notes

- No inbound HTTP surface; the worker trusts **internal** network calls to Orders/Books.  
- Limit RabbitMQ and management UI exposure; use credentials and network policies.  
- Validate & sanitize any fields you use from the message before forwarding to downstream services.

---