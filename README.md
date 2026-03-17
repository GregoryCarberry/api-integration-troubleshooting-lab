# API Troubleshooting Lab – Backend Service

This repository contains the **Flask backend service** for the API Troubleshooting Lab project.

It simulates an internal service sitting behind an API gateway and is designed to support realistic troubleshooting scenarios, including malformed requests, validation failures, dependency issues, timeouts, and structured request tracing.

This project demonstrates real-world API troubleshooting techniques, including structured logging, request tracing, and failure simulation across a gateway-backend architecture.

---

## What This Service Does

The backend is responsible for:

- processing XML-based order requests
- validating request structure and data
- storing orders in memory for retrieval tests
- simulating controlled failure scenarios
- returning consistent response headers for request tracing

The gateway handles concerns such as API key authentication, rate limiting, request correlation, and forwarding.

---

## Role in the Architecture

```text
Client
  │
  ▼
API Gateway (FastAPI)
  │
  ▼
Backend API (Flask)
  │
  ▼
Response
```

The backend deliberately focuses on **business logic and service behaviour**, while the gateway acts as the **control and protection layer** in front of it.

---

## Technology

- Python
- Flask
- XML request payloads
- In-memory order storage
- Structured JSON logging
- `X-Request-ID` request tracing

---

## Endpoints

### `GET /health`

Used to confirm the backend service is running.

Example:

```bash
curl -i http://127.0.0.1:5000/health
```

Example response:

```http
HTTP/1.1 200 OK
Content-Type: text/plain; charset=utf-8
X-Request-ID: 6064b9e6-4a05-474b-a2b2-de47fbb94f9e

ok
```

---

### `POST /api/orders`

Accepts XML payloads in the following format:

```xml
<Order>
  <CustomerID>123</CustomerID>
  <ProductID>ABC-001</ProductID>
  <Quantity>1</Quantity>
</Order>
```

Example request:

```bash
curl -X POST http://127.0.0.1:5000/api/orders \
  -H "Content-Type: application/xml" \
  -d '<Order><CustomerID>123</CustomerID><ProductID>ABC-001</ProductID><Quantity>1</Quantity></Order>'
```

Successful response:

```xml
<OrderCreated><OrderID>generated-order-id</OrderID></OrderCreated>
```

---

### `GET /api/orders/<order_id>`

Returns an existing order in XML format.

Example:

```bash
curl http://127.0.0.1:5000/api/orders/generated-order-id
```

Successful response:

```xml
<Order>
  <OrderID>generated-order-id</OrderID>
  <CustomerID>123</CustomerID>
  <ProductID>ABC-001</ProductID>
  <Quantity>1</Quantity>
</Order>
```

---

## Failure Simulation

The backend supports controlled failure injection using the `X-Failure-Mode` header. This makes it possible to reproduce specific conditions during testing and troubleshooting.

Example:

```http
X-Failure-Mode: timeout
```

Supported modes:

| Mode | Behaviour | Status |
|------|-----------|--------|
| `none` | normal processing | normal response |
| `timeout` | simulates upstream timeout behaviour | `504` |
| `dependency` | simulates dependency/service failure | `503` |
| `exception` | simulates unhandled internal exception | `500` |

---

## Natural Validation and Error Scenarios

These responses occur without failure injection:

| Scenario | Status |
|----------|--------|
| malformed XML | `400` |
| invalid XML structure or missing fields | `422` |
| unsupported content type | `415` |
| invalid failure mode header | `400` |
| order not found | `404` |

---

## Observability & Request Tracing

The backend uses structured JSON logging and request-level tracing to support debugging, failure analysis, and log correlation across services.

Each request is assigned an `X-Request-ID`, which is:

- accepted from the gateway if already present
- generated automatically if missing
- returned in response headers
- included in structured log output

### Example Response Header

```http
X-Request-ID: ce5830c1-895a-40ae-a7b3-4e4a44373eb4
```

### Example Log Output

```json
{
  "timestamp": "2026-03-17T22:17:08.122882",
  "level": "INFO",
  "service": "api-backend",
  "message": "Health check received",
  "request_id": "ce5830c1-895a-40ae-a7b3-4e4a44373eb4"
}
```

### End-to-End Trace Example

A single request can be correlated across both services using the same request ID.

**Response header:**

```http
X-Request-ID: ce5830c1-895a-40ae-a7b3-4e4a44373eb4
```

**Gateway log:**

```json
{
  "message": "Gateway request received",
  "request_id": "ce5830c1-895a-40ae-a7b3-4e4a44373eb4"
}
```

**Backend log:**

```json
{
  "message": "Health check received",
  "request_id": "ce5830c1-895a-40ae-a7b3-4e4a44373eb4"
}
```

### Why This Matters

This enables:

- end-to-end request tracing
- faster debugging of failures
- correlation of logs across gateway and backend services
- cleaner visibility during timeout and dependency simulations
- more production-like observability in a multi-service lab

---

## Development

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the service:

```bash
python app.py
```

The service starts on:

```text
http://127.0.0.1:5000
```

---

## Project Context

This service is part of the **API Troubleshooting Lab** multi-repository project.

The full architecture, diagrams, and cross-repository documentation are maintained in the hub repository:

```text
api-troubleshooting-lab
```
