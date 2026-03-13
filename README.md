# API Troubleshooting Lab – Backend Service

This repository contains the **backend service** for the API Troubleshooting Lab project.

The backend simulates a typical internal service that processes requests forwarded from an API gateway. It intentionally supports multiple failure scenarios to allow debugging and troubleshooting exercises.

---

## Role in the Architecture

The backend sits **behind the API gateway**.

The gateway is responsible for:

- API key authentication
- rate limiting
- request tracing
- forwarding validated requests

The backend focuses purely on **business logic and request processing**.

```
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

---

## Technology

- Python
- Flask
- XML request payloads
- In‑memory order storage (for simulation purposes)

---

## Endpoints

### Health Check

`GET /health`

Used to confirm the service is running.

Example:

```
curl http://localhost:5000/health
```

Response:

```
{
  "success": true,
  "status": "ok"
}
```

---

### Create Order

`POST /api/orders`

Accepts XML payloads.

Required XML structure:

```
<order>
  <customerId>123</customerId>
  <item>Widget</item>
  <quantity>1</quantity>
</order>
```

Example request:

```
curl -X POST http://localhost:5000/api/orders   -H "Content-Type: application/xml"   -d '<order><customerId>123</customerId><item>Widget</item><quantity>1</quantity></order>'
```

Success response:

```
{
  "success": true,
  "orderId": "abc123"
}
```

---

### Get Order

`GET /api/orders/<order_id>`

Returns order details if the order exists.

Example:

```
curl http://localhost:5000/api/orders/abc123
```

---

## Supported Failure Modes

The backend can intentionally simulate failures using the `X-Failure-Mode` header.

This allows reproducible troubleshooting scenarios.

Header example:

```
X-Failure-Mode: timeout
```

Supported modes:

| Mode | Result |
|-----|------|
| none | Normal processing |
| timeout | Simulated upstream timeout |
| dependency | Simulated dependency failure |
| exception | Simulated internal exception |

---

## Natural Error Scenarios

These errors occur without using failure simulation.

| Scenario | Status |
|--------|--------|
| malformed XML | 400 |
| validation failure | 422 |
| unsupported content type | 415 |
| order not found | 404 |

---

## Development

Install dependencies:

```
pip install -r requirements.txt
```

Run the service:

```
python app.py
```

The service will start on:

```
http://localhost:5000
```

---

## Project Context

This service is part of the **API Troubleshooting Lab** multi‑repository project.

The full architecture and diagrams are documented in the hub repository:

```
api-troubleshooting-lab
```
