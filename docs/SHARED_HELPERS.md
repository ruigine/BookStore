# Shared Helpers

_Last updated: 2025-08-12_

##  1) Auth Helper `auth.py`

Lightweight JWT utilities used by gateway/proxy/services to protect routes. Provides:

- `verify_jwt(token)` — decode & validate an **access** token
- `@jwt_required` — Flask decorator that enforces the presence of a valid access token and attaches the decoded payload to `request.user`

---

### Environment

- `JWT_SECRET_KEY` — HMAC secret for verifying JWTs (alg: **HS256**). **Required.**

### Functions

#### `verify_jwt(token) -> dict | payload`

Validates a JWT string using `HS256` and the secret above. Enforces that `payload["type"] == "access"`.

**Returns**

- **Payload (dict-like)** — on success (contains claims like `sub`, `name`, `type`, `iat`, `exp`)
- **Error dict** — on failure, with one of:
  - `{"error": "Invalid token type"}`
  - `{"error": "Token has expired"}`
  - `{"error": "Invalid token"}`

#### `jwt_required(fn) -> fn`

Flask route decorator. Behavior:

1. Read `Authorization` header.
2. Expect **`Bearer <token>`** format (case-insensitive scheme check).
3. If missing or malformed → return `401`:
   - `{"code": 401, "message": "Missing Authorization header"}`
   - `{"code": 401, "message": "Invalid Authorization format"}` *(exact string varies in code path)*
4. Call `verify_jwt(token)`; on error → `401` with error message.
5. On success, set `request.user = payload` and invoke the wrapped view.

**Example**

```python
from auth import jwt_required

@app.get("/me")
@jwt_required
def me():
    # request.user contains the decoded JWT payload
    return { "code": 200, "data": { "user": request.user } }, 200
```

### Security Notes

- Only **access** tokens are accepted. Refresh tokens should never hit protected endpoints.
- Keep `JWT_SECRET_KEY` strong and rotate when needed.
- Use HTTPS in production so bearer tokens are not exposed in transit.

## 2) Shared RabbitMQ Client (`rabbitmq.py`)

Thin wrapper around **pika** for publishing/consuming order messages with built-in setup and reconnection.

### Defaults (can be overridden via constructor)

- **Host:** `rabbitmq`
- **Port:** `5672`
- **Credentials:** `RABBITMQ_DEFAULT_USER` / `RABBITMQ_DEFAULT_PASS`
- **Exchange:** `orders`
- **Exchange type:** `direct`
- **Queue:** `order_queue`
- **Routing key:** `order.new`

### Connection & Reliability

- Declares exchange/queue/binding on start (`durable=True` for both).
- Publisher sets `delivery_mode=2` (persistent messages).
- Consumer uses `basic_qos(prefetch_count=1)` (fair dispatch, one unacked message at a time).
- Connection params include `heartbeat=600`, `blocked_connection_timeout=300`.
- Both publisher and consumer attempt reconnection; consumer loop waits **2 seconds** before retry.

### API

#### `RabbitMQClient(...)`

```python
RabbitMQClient(
    host='rabbitmq',
    port=5672,
    username=os.getenv('RABBITMQ_DEFAULT_USER'),
    password=os.getenv('RABBITMQ_DEFAULT_PASS'),
    exchange='orders',
    exchange_type='direct',
    queue='order_queue',
    routing_key='order.new',
)
```

#### `.publish(payload: dict) -> None`

Ensures connection/setup and publishes JSON-encoded `payload` to the configured exchange/routing key with persistent delivery.

```python
client = RabbitMQClient()
client.publish({"order_id": 1001, "book_id": 123, "quantity": 1})
```

#### `.consume(callback: Callable)`

Starts a long-running consumer that invokes `callback(ch, method, properties, body)` for each message.

```python
def handle(ch, method, properties, body):
    data = json.loads(body)
    # ... process ...
    ch.basic_ack(delivery_tag=method.delivery_tag)

client = RabbitMQClient()
client.consume(handle)
```

> The implementation calls your callback as `callback(ch, method, properties, body)` and prints `" [*] Consumer waiting for messages..."` once started.

### Error Handling

- Catches AMQP and generic exceptions; on any error it safely closes the connection and retries after **2 seconds**.
- For consumers, you are responsible for calling `basic_ack` inside your `callback` once processing succeeds.

### Notes

- Use exchange `orders` and routing key `order.new` to interoperate with your Place Order service and Order Processing worker.
