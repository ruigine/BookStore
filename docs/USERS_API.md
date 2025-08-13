# Users Service API

_Last updated: 2025-08-12_

Authentication and user management microservice built with Python Flask + SQLAlchemy.  
Provides user registration, login (JWT access + HttpOnly refresh cookie), token refresh (rotation), and logout.

## Overview

- **Default port (dev):** `5001`
- **Base URL (examples):** `http://localhost:5001`
- **Environment:**
  - `dbURL` — SQLAlchemy database URI (e.g., `mysql+mysqlconnector://user:pass@host/db`)
  - `JWT_SECRET_KEY` — HMAC secret used to sign JWTs
- **CORS:** Enabled with `supports_credentials=True`
- **Health endpoint:** `/health`
- **Tokens:**
  - **Access token** — JWT in response body, **15 min** expiry
  - **Refresh token** — JWT in **HttpOnly** cookie, **24 hours** expiry, `SameSite=Strict`, `Secure=true`

---

## Data Model

**User**

| Field         | Type            | Required | Notes                         |
|---------------|-----------------|----------|-------------------------------|
| `user_id`     | integer (PK)    | yes      | Auto-increment                |
| `username`    | string(50)      | yes      |                               |
| `email`       | string(100)     | yes      | Unique   |
| `password_hash` | text          | yes      | Hashed via Werkzeug           |
| `created_at`  | datetime        | yes      | Defaults to current time        |

**JSON representation (returned by API where applicable):**

```json
{
  "user_id": 1,
  "username": "john",
  "email": "john@example.com",
  "created_at": "2025-08-01"
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

### 2) `POST /register`

Create a new user account.

**Request body (JSON)**

| Field       | Type   | Required | Constraints/Validation                              |
|-------------|--------|----------|-----------------------------------------------------|
| `username`  | string | yes      | non-empty                                           |
| `email`     | string | yes      | must match common email regex                       |
| `password`  | string | yes      | at least 6 characters                               |

**Responses**

- `201 Created`

```json
{
  "code": 201,
  "data": {
    "user_id": 1,
    "email": "user@example.com",
    "username": "user"
  }
}
```

- `400 Bad Request` — missing fields, invalid email, or short password.

```json
{
  "code": 400,
  "message": "Username, email and password are required."
}
```
```json
{
  "code": 400,
  "data": { "email": "bad@" },
  "message": "Invalid email format."
}
```
```json
{
  "code": 400,
  "data": { "email": "user@example.com" },
  "message": "Password must be at least 6 characters."
}
```

- `409 Conflict` — email already registered.

```json
{
  "code": 409,
  "data": { "email": "user@example.com" },
  "message": "Email is already registered."
}
```

- `500 Internal Server Error` — unexpected error.

**Example**

```bash
curl -X POST "http://localhost:5001/register"   -H "Content-Type: application/json"   -d '{ "username": "john", "email": "john@example.com", "password": "secret123" }'
```

---

### 3) `POST /login`

Authenticate with email + password. Returns a short-lived **access token** in the JSON body and sets a **refresh token** as an HttpOnly cookie (rotated on /refresh-token).

**Request body (JSON)**

| Field      | Type   | Required |
|------------|--------|----------|
| `email`    | string | yes      |
| `password` | string | yes      |

**Successful response**

- `200 OK`

```json
{
  "code": 200,
  "access_token": "<JWT access token>"
}
```

Also sets a cookie:

- Name: `refresh_token`  
- Attributes: `HttpOnly`, `Secure`, `SameSite=Strict`, `Path=/refresh-token`  
- Expiry: **24 hours** from issue

**Error responses**

- `400 Bad Request` — Missing fields.

```json
{
  "code": 400,
  "message": "Email and password are required."
}
```
- `401 Unauthorized` — invalid email or password
```json
{
  "code": 401,
  "message": "Invalid email or password."
}
```
- `500 Internal Server Error` — unexpected error

**Example**

```bash
# Save cookies (including HttpOnly refresh token) to a jar
curl -v -c cookies.txt -X POST "http://localhost:5001/login"   -H "Content-Type: application/json"   -d '{ "email": "regine@example.com", "password": "secret123" }'
```

---

### 4) `POST /refresh-token`

Exchange a valid refresh token cookie for a **new access token** and a **rotated refresh token** (with same expiry as original refresh).

**Auth**

- Requires `refresh_token` cookie (HttpOnly).

**Responses**

- `200 OK`

```json
{
  "code": 200,
  "access_token": "<new JWT access token>"
}
```

Sets a new `refresh_token` cookie with same attributes and original expiry.

- `400 Bad Request` — wrong token type in cookie
- `401 Unauthorized` — missing/invalid/expired refresh token; or user not found
- `500 Internal Server Error` — unexpected error

**Example**

```bash
# Use previously saved cookie jar from /login
curl -v -b cookies.txt -c cookies.txt -X POST "http://localhost:5001/refresh-token"
```

---

### 5) `POST /logout`

Clears the refresh token cookie (sets it to empty with immediate expiry).

**Response**

- `200 OK`

```json
{ "code": 200, "message": "Logged out" }
```

**Example**

```bash
curl -v -b cookies.txt -X POST "http://localhost:5001/logout"
```

---

## JWT Details

- **Algorithm:** HS256
- **Claims (access & refresh):**  
  - `sub` — user id (string)  
  - `name` — username  
  - `iat` — issued-at (UTC)  
  - `exp` — expiry time (UTC)  
  - `type` — `"access"` or `"refresh"`
- **Access token TTL:** 15 minutes  
- **Refresh token TTL:** 24 hours (on /refresh-token the refresh token is rotated and preserves original expiry)

**Example: decoding an access token**

```bash
# Replace $TOKEN and $SECRET accordingly (for testing only)
python - <<'PY'
import jwt, os
print(jwt.decode(os.environ["TOKEN"], os.environ["SECRET"], algorithms=["HS256"]))
PY
```

---

## Error Format

Errors are returned as JSON with an HTTP status code, e.g.:

```json
{ "code": 401, "message": "Invalid email or password." }
```

---

## Example Docker

```yaml
services:
  users:
    build: .
    environment:
      - dbURL=${USERS_DB_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    ports:
      - "5001:5001"
```

## Security Notes

- Always use **HTTPS** in production so the `Secure` cookie is transmitted.
- Keep `JWT_SECRET_KEY` strong and private; rotate if compromised.
- Consider account lockout / rate limiting on `/login` in front of the service.
- Validate email and password strength on the client as well for UX; server remains the source of truth.
- Treat access tokens as bearer tokens in your other services (e.g., `Authorization: Bearer <token>`), and verify signature + `type` claim = `"access"`.
- For cross-origin SPA flows, ensure `CORS` allows the frontend origin and that `credentials: "include"` is used when calling `/login` and `/refresh-token`.

## Changelog

- v1.0 — Initial public documentation.
