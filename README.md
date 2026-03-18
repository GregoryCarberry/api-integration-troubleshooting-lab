# Backend API (Flask)

This service is the backend component of the API Troubleshooting Lab. It is responsible for processing XML-based requests, validating input, simulating failures, and providing structured logging to support debugging and observability.

## Overview

The backend is intentionally designed to mimic a real-world service that:

- accepts structured input (XML)
- validates requests and returns meaningful errors
- simulates downstream failures
- supports request tracing across services

It is consumed by the API Gateway, which handles authentication, rate limiting, and external access.

---

## Responsibilities

- XML request parsing and validation
- business logic simulation (order handling)
- failure simulation for testing resilience
- structured logging
- request ID propagation for tracing

---

## Request Flow

1. Request received (typically via gateway)
2. `X-Request-ID` extracted or generated
3. XML payload parsed and validated
4. Failure mode applied (if specified)
5. Response returned with appropriate status code

---

## Failure Modes

The backend supports controlled failure simulation via the `X-Failure-Mode` header.

| Mode        | Behaviour                  | Status |
|-------------|---------------------------|--------|
| timeout     | Simulated delay           | 504    |
| dependency  | Downstream failure        | 503    |
| exception   | Internal error            | 500    |

This allows consistent reproduction of failure scenarios for testing and troubleshooting.

---

## Validation Rules

The API enforces strict validation:

- valid XML structure required
- required fields must be present
- numeric fields must be valid

Common responses:

| Scenario              | Status |
|----------------------|--------|
| malformed XML        | 400    |
| missing fields       | 422    |
| invalid values       | 422    |

---

## Observability

The backend emits structured JSON logs including:

- request ID (`X-Request-ID`)
- request details
- validation errors
- failure mode triggers

This enables:

- correlation with gateway logs
- end-to-end request tracing
- easier debugging of failures

---

## Example Payload

```xml
<Order>
  <Item>Widget</Item>
  <Quantity>2</Quantity>
</Order>
```

---

## Testing

The backend includes a pytest-based test suite covering:

- valid requests
- validation errors
- failure modes
- request tracing behaviour

Run tests:

```bash
pytest -q
```

---

## Relationship to Gateway

This service is not intended to be accessed directly in normal operation.

The API Gateway provides:

- authentication
- rate limiting
- request routing
- unified entry point

The backend focuses purely on service logic and failure handling.

---

## Purpose

This service exists to demonstrate:

- input validation and error handling
- controlled failure simulation
- observability and tracing
- behaviour under different failure conditions

It is designed as part of a multi-service system to replicate real-world troubleshooting scenarios.
