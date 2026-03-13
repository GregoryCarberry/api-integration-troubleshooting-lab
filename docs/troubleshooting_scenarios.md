# Troubleshooting Scenarios

This document captures reproducible troubleshooting scenarios for the API Troubleshooting Lab backend service.

These scenarios are designed to simulate common integration and debugging issues that can occur when a client sends requests through an API gateway to a backend service.

The goal is not only to demonstrate successful API behaviour, but also to show how failures can be identified, interpreted, and resolved.

---

## Scope

This document describes reproducible troubleshooting scenarios for the backend service in the API Troubleshooting Lab.

The scenarios focus on failures that originate within the backend application itself, including:

- malformed XML payloads
- request validation failures
- unsupported content types
- simulated dependency failures
- simulated timeouts
- simulated internal exceptions
- resource lookup failures

These scenarios are intended to support manual testing, automated tests, and debugging exercises when integrating with the backend API.

---

## Scenario 1: Malformed XML

### Symptom

The client receives a `400 Bad Request` response.

### Example request

```bash
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/xml" \
  -d '<order><customerId>123<customerId><item>Widget</item><quantity>1</quantity></order>'
```

### Likely response

```json
{
  "success": false,
  "error": "malformed_xml",
  "message": "Malformed XML payload."
}
```

### Cause

The XML body is not well-formed. In this example, the `customerId` tag is not closed correctly.

### Troubleshooting approach

1. Check that every opening tag has a valid closing tag.
2. Validate the payload in an XML validator or editor with XML linting.
3. Confirm the request body has not been altered by copy/paste or escaping issues.
4. Retest with a known-good sample from the `examples/` directory.

---

## Scenario 2: Validation Failure

### Symptom

The client receives a `422 Unprocessable Entity` response.

### Example request

```bash
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/xml" \
  -d '<order><customerId>123</customerId><item>Widget</item></order>'
```

### Likely response

```json
{
  "success": false,
  "error": "validation_failed",
  "message": "Missing required field: quantity"
}
```

### Cause

The XML is well-formed, but one or more required fields are missing or invalid.

### Troubleshooting approach

1. Compare the payload against the documented required structure.
2. Confirm all mandatory fields are present.
3. Check values for empty strings, invalid numbers, or incorrect element names.
4. Retest with a valid sample payload to isolate whether the issue is structural or data-related.

---

## Scenario 3: Unsupported Content Type

### Symptom

The client receives a `415 Unsupported Media Type` response.

### Example request

```bash
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"customerId":"123","item":"Widget","quantity":1}'
```

### Likely response

```json
{
  "success": false,
  "error": "unsupported_media_type",
  "message": "Content-Type must be application/xml."
}
```

### Cause

The backend expects XML, but the client submitted JSON or another unsupported format.

### Troubleshooting approach

1. Confirm the `Content-Type` header is set to `application/xml`.
2. Verify the body format matches the declared content type.
3. Check Postman, curl, or client library defaults if the wrong type keeps being sent.
4. Retest with a minimal valid XML request.

---

## Scenario 4: Simulated Dependency Failure

### Trigger

Set the following header:

```text
X-Failure-Mode: dependency
```

### Symptom

The client receives a `503 Service Unavailable` response.

### Example request

```bash
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/xml" \
  -H "X-Failure-Mode: dependency" \
  -d '<order><customerId>123</customerId><item>Widget</item><quantity>1</quantity></order>'
```

### Likely response

```json
{
  "success": false,
  "error": "dependency_failure",
  "message": "Simulated upstream dependency failure."
}
```

### What this simulates

This represents a backend dependency becoming unavailable, such as:

- a database outage
- an internal service failure
- a third-party API outage

### Troubleshooting approach

1. Confirm whether the failure is reproducible only when the dependency mode is triggered.
2. Review backend logs for request ID correlation.
3. Distinguish between an application bug and an upstream availability issue.
4. Check dependency health, timeout settings, and retry behaviour.

---

## Scenario 5: Simulated Timeout

### Trigger

Set the following header:

```text
X-Failure-Mode: timeout
```

### Symptom

The client receives a `504 Gateway Timeout` response.

### Example request

```bash
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/xml" \
  -H "X-Failure-Mode: timeout" \
  -d '<order><customerId>123</customerId><item>Widget</item><quantity>1</quantity></order>'
```

### Likely response

```json
{
  "success": false,
  "error": "upstream_timeout",
  "message": "Simulated upstream timeout occurred."
}
```

### What this simulates

This represents a backend request that takes too long to complete, such as:

- a slow dependency
- network latency
- resource contention
- backend overload

### Troubleshooting approach

1. Confirm the request is timing out rather than failing immediately.
2. Compare backend processing time with client or gateway timeout settings.
3. Check whether the problem is isolated to a particular dependency or operation.
4. Review logs and trace IDs to determine where latency was introduced.

---

## Scenario 6: Simulated Internal Exception

### Trigger

Set the following header:

```text
X-Failure-Mode: exception
```

### Symptom

The client receives a `500 Internal Server Error` response.

### Example request

```bash
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/xml" \
  -H "X-Failure-Mode: exception" \
  -d '<order><customerId>123</customerId><item>Widget</item><quantity>1</quantity></order>'
```

### Likely response

```json
{
  "success": false,
  "error": "internal_server_error",
  "message": "Simulated unhandled backend exception."
}
```

### What this simulates

This represents an application bug or unhandled runtime condition inside the backend service.

### Troubleshooting approach

1. Check backend logs for stack traces or exception details.
2. Correlate the failure using the request ID if one was sent through the gateway.
3. Distinguish between bad input and a genuine server-side defect.
4. Reduce the request to a minimal reproducible example and retest.

---

## Scenario 7: Order Not Found

### Symptom

The client receives a `404 Not Found` response.

### Example request

```bash
curl http://localhost:5000/api/orders/does-not-exist
```

### Likely response

```json
{
  "success": false,
  "error": "not_found",
  "message": "Order not found."
}
```

### Cause

The requested order ID does not exist in the backend's in-memory store.

### Troubleshooting approach

1. Confirm the order ID was created successfully before retrieval.
2. Check for typos or truncated IDs.
3. Remember that in-memory storage resets when the application restarts.
4. Recreate the order and repeat the request.

---

## Notes

These scenarios are intentionally simple and reproducible.

They are designed to support:

- manual testing with curl or Postman
- automated tests
- troubleshooting documentation
- future gateway tracing and observability work

As the lab evolves, this document can be expanded to include cross-repository scenarios, such as gateway authentication failures, rate limiting, backend unavailability, and end-to-end request tracing.
