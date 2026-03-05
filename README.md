# API Integration Troubleshooting Lab

## Overview

This project simulates common API integration problems that developers
encounter when connecting to external services.

The lab demonstrates how to investigate and troubleshoot issues such as
authentication failures, malformed payloads, and incorrect request
headers.

Rather than building a complex infrastructure project, the goal is to
demonstrate a **structured troubleshooting workflow** similar to what an
API platform support engineer or service analyst would perform when
diagnosing customer integration issues.

------------------------------------------------------------------------

## Technologies Used

-   Python
-   Flask
-   REST APIs
-   XML payloads
-   Postman
-   HTTP troubleshooting
-   Python `requests` library

------------------------------------------------------------------------

## Architecture

Client (Postman / Python Script) \| HTTP Requests \| Flask API Server \|
XML Validation + Authentication \| Response Codes (201 / 400 / 401)

------------------------------------------------------------------------

## Project Structure

api-integration-troubleshooting-lab/

api-server/ app.py

python-tests/ api_test.py

xml-examples/ valid-order.xml malformed-order.xml

postman/

screenshots/

README.md

------------------------------------------------------------------------

# Troubleshooting Scenarios

## 1. Successful API Request

Valid XML payload and authentication header.

Expected result:

HTTP 201 Created

Example response:

`<OrderCreated>`{=html}`<OrderID>`{=html}...`</OrderID>`{=html}`</OrderCreated>`{=html}

------------------------------------------------------------------------

## 2. Authentication Failure

Request sent **without API key header**.

Problem:

401 Unauthorized

Root cause:

Missing authentication header.

Resolution:

Add the required header:

X-API-Key: test-api-key-123

------------------------------------------------------------------------

## 3. Malformed XML Payload

Broken XML payload sent to API.

Problem:

400 Bad Request

Malformed XML

Root cause:

XML payload structure invalid.

Resolution:

Validate XML before submission.

------------------------------------------------------------------------

## 4. Incorrect Content-Type Header

Payload sent with wrong content type.

Problem:

400 Bad Request\
Content-Type must be application/xml

Root cause:

Incorrect request header.

Resolution:

Ensure request uses:

Content-Type: application/xml

------------------------------------------------------------------------

# Key Skills Demonstrated

-   API integration troubleshooting
-   XML payload validation
-   HTTP request debugging
-   Authentication troubleshooting
-   Reproducing integration errors
-   Structured incident investigation

------------------------------------------------------------------------

# Future Improvements

Possible extensions:

-   OAuth authentication flow
-   JSON API version
-   Logging and request tracing
-   Containerised test environment
