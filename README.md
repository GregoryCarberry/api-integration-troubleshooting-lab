# API Integration Troubleshooting Lab

A small lab environment for reproducing and diagnosing common API
integration failures such as authentication errors, malformed XML
payloads, and incorrect request headers.

This service acts as the **backend API** in the **API Troubleshooting
Lab Series**, a small multi‑service environment designed to simulate
real‑world API platform debugging and integration support workflows.

Companion project:

API Gateway Troubleshooting Lab\
https://github.com/GregoryCarberry/api-gateway-troubleshooting-lab

------------------------------------------------------------------------

## Lab Series Architecture

The backend API works together with the API Gateway project to simulate
a simple API platform architecture.

Client\
│\
▼\
API Gateway (FastAPI)\
│\
▼\
Backend API (Flask -- this repository)

The gateway provides:

-   API key authentication
-   rate limiting
-   request tracing
-   gateway‑level error handling

The backend API focuses on validating requests and reproducing common
integration failures.

------------------------------------------------------------------------

## Overview

Many integration problems occur not because the API is unavailable, but
because requests are malformed or authentication is incorrect. This lab
simulates several common failure scenarios and demonstrates how they can
be reproduced and diagnosed using typical developer and support tools.

The goal is to provide a small, reproducible environment for practicing
API troubleshooting workflows.

------------------------------------------------------------------------

## Requirements

-   Python 3.10+
-   pip
-   Postman (optional, for manual testing)

------------------------------------------------------------------------

## Project Structure

    api-integration-troubleshooting-lab/
    │
    ├── api-server/
    │   ├── app.py
    │   └── requirements.txt
    │
    ├── python-tests/
    │   └── api_test.py
    │
    ├── xml-examples/
    │   ├── valid-order.xml
    │   └── malformed-order.xml
    │
    ├── postman/
    ├── screenshots/
    └── README.md

------------------------------------------------------------------------

## Running the Lab

Start the API server:

    cd api-server
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python app.py

In another terminal, run the troubleshooting script:

    python python-tests/api_test.py

------------------------------------------------------------------------

## Architecture

The API validates authentication headers, parses XML payloads, and
returns appropriate HTTP status codes when errors occur.

    Client
       │
       ▼
    Flask API Server
       │
       ▼
    Authentication Check
       │
       ├── Invalid → 401 Unauthorized
       │
       ▼
    XML Validation
       │
       ├── Invalid → 400 Bad Request
       │
       ▼
    Order Processing
       │
       ▼
    201 Created

------------------------------------------------------------------------

## Example Failure Scenarios

### Successful Request

Valid XML payload and authentication header.

Expected response:

    HTTP 201 Created

Example response:

    <OrderCreated>
      <OrderID>...</OrderID>
    </OrderCreated>

------------------------------------------------------------------------

### Authentication Failure

Request sent **without API key header**.

Response:

    401 Unauthorized

Cause:

Missing authentication header.

Fix:

    X-API-Key: test-api-key-123

------------------------------------------------------------------------

### Malformed XML Payload

Broken XML payload sent to API.

Response:

    400 Bad Request
    Malformed XML

Cause:

Invalid XML structure.

------------------------------------------------------------------------

### Incorrect Content-Type

Payload sent with the wrong header.

Response:

    400 Bad Request
    Content-Type must be application/xml

Cause:

Incorrect request header.

------------------------------------------------------------------------

## Example Requests

### Successful Request (Postman)

![Successful Request](screenshots/postman-success.png)

### Authentication Failure

![Auth Error](screenshots/postman-auth-error.png)

### Python Troubleshooting Script

![Python Script Output](screenshots/python-test-output.png)

------------------------------------------------------------------------

## Example Server Logs

When running the API locally, request lifecycle events are logged with a
request ID to help trace individual requests during troubleshooting.

Example:

    2026-03-06 22:47:31 [INFO] [request_id=3f2c1f8a] Incoming request: POST /api/orders
    2026-03-06 22:47:31 [INFO] [request_id=3f2c1f8a] Authentication successful
    2026-03-06 22:47:31 [INFO] [request_id=3f2c1f8a] Order created successfully: 6e7c...

The `X-Request-ID` header returned in responses allows a specific
request to be correlated with its server-side logs.

------------------------------------------------------------------------

## Future Improvements

Possible extensions:

-   OAuth authentication support
-   JSON API version
-   request tracing integration with gateway logs
-   containerised test environment
