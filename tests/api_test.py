from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Allow importing app.py when running pytest from repo root
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import ORDERS, app  # noqa: E402


VALID_ORDER_XML = b"""\
<Order>
  <CustomerID>CUST-1001</CustomerID>
  <ProductID>PROD-2002</ProductID>
  <Quantity>3</Quantity>
</Order>
"""

MALFORMED_ORDER_XML = b"""\
<Order>
  <CustomerID>CUST-1001</CustomerID>
  <ProductID>PROD-2002</ProductID>
  <Quantity>3</Quantity>
"""

MISSING_FIELDS_XML = b"""\
<Order>
  <CustomerID>CUST-1001</CustomerID>
  <Quantity>3</Quantity>
</Order>
"""

INVALID_QUANTITY_XML = b"""\
<Order>
  <CustomerID>CUST-1001</CustomerID>
  <ProductID>PROD-2002</ProductID>
  <Quantity>-1</Quantity>
</Order>
"""

WRONG_ROOT_XML = b"""\
<Purchase>
  <CustomerID>CUST-1001</CustomerID>
  <ProductID>PROD-2002</ProductID>
  <Quantity>3</Quantity>
</Purchase>
"""


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    ORDERS.clear()

    with app.test_client() as test_client:
        yield test_client

    ORDERS.clear()


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.data == b"ok\n"
    assert response.headers["Content-Type"].startswith("text/plain")
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]


def test_valid_order(client):
    response = client.post(
        "/api/orders",
        data=VALID_ORDER_XML,
        headers={"Content-Type": "application/xml"},
    )

    assert response.status_code == 201
    assert response.headers["Content-Type"].startswith("application/xml")
    assert "X-Request-ID" in response.headers
    assert b"<OrderCreated>" in response.data
    assert b"<OrderID>" in response.data
    assert len(ORDERS) == 1


@pytest.mark.parametrize(
    ("payload", "expected_status", "expected_text"),
    [
        (MALFORMED_ORDER_XML, 400, b"Bad Request: Malformed XML:"),
        (MISSING_FIELDS_XML, 422, b"Unprocessable Entity: Invalid XML: missing or empty <ProductID>"),
        (INVALID_QUANTITY_XML, 422, b"Unprocessable Entity: Invalid XML: <Quantity> must be a positive integer"),
        (WRONG_ROOT_XML, 422, b"Unprocessable Entity: Invalid XML: root element must be <Order>"),
    ],
)
def test_invalid_xml_variants(client, payload, expected_status, expected_text):
    response = client.post(
        "/api/orders",
        data=payload,
        headers={"Content-Type": "application/xml"},
    )

    assert response.status_code == expected_status
    assert response.data.startswith(expected_text)
    assert "X-Request-ID" in response.headers


def test_empty_body(client):
    response = client.post(
        "/api/orders",
        data=b"",
        headers={"Content-Type": "application/xml"},
    )

    assert response.status_code == 400
    assert response.data == b"Bad Request: request body is empty\n"
    assert "X-Request-ID" in response.headers


def test_unsupported_content_type(client):
    response = client.post(
        "/api/orders",
        data=VALID_ORDER_XML,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 415
    assert response.data == b"Unsupported Media Type: Content-Type must be application/xml\n"
    assert "X-Request-ID" in response.headers


def test_invalid_failure_mode(client):
    response = client.post(
        "/api/orders",
        data=VALID_ORDER_XML,
        headers={
            "Content-Type": "application/xml",
            "X-Failure-Mode": "banana",
        },
    )

    assert response.status_code == 400
    assert b"Bad Request: Invalid X-Failure-Mode." in response.data
    assert "X-Request-ID" in response.headers


@pytest.mark.parametrize(
    ("failure_mode", "expected_status", "expected_text"),
    [
        ("dependency", 503, b"Service Unavailable: Simulated upstream dependency failure\n"),
        ("exception", 500, b"Internal Server Error: simulated backend exception\n"),
    ],
)
def test_failure_modes(client, failure_mode, expected_status, expected_text):
    response = client.post(
        "/api/orders",
        data=VALID_ORDER_XML,
        headers={
            "Content-Type": "application/xml",
            "X-Failure-Mode": failure_mode,
        },
    )

    assert response.status_code == expected_status
    assert response.data == expected_text
    assert "X-Request-ID" in response.headers


def test_timeout_failure_mode(client, monkeypatch):
    monkeypatch.setattr("app.SIMULATED_TIMEOUT_SECONDS", 0)

    response = client.post(
        "/api/orders",
        data=VALID_ORDER_XML,
        headers={
            "Content-Type": "application/xml",
            "X-Failure-Mode": "timeout",
        },
    )

    assert response.status_code == 504
    assert response.data == b"Gateway Timeout: Simulated upstream timeout occurred\n"
    assert "X-Request-ID" in response.headers


def test_get_order_success(client):
    create_response = client.post(
        "/api/orders",
        data=VALID_ORDER_XML,
        headers={"Content-Type": "application/xml"},
    )

    assert create_response.status_code == 201

    order_id = next(iter(ORDERS.keys()))
    get_response = client.get(f"/api/orders/{order_id}")

    assert get_response.status_code == 200
    assert get_response.headers["Content-Type"].startswith("application/xml")
    assert b"<Order>" in get_response.data
    assert f"<OrderID>{order_id}</OrderID>".encode() in get_response.data
    assert b"<CustomerID>CUST-1001</CustomerID>" in get_response.data
    assert b"<ProductID>PROD-2002</ProductID>" in get_response.data
    assert b"<Quantity>3</Quantity>" in get_response.data
    assert "X-Request-ID" in get_response.headers


def test_get_order_not_found(client):
    response = client.get("/api/orders/does-not-exist")

    assert response.status_code == 404
    assert response.data == b"Not Found\n"
    assert "X-Request-ID" in response.headers


def test_request_id_is_propagated_when_supplied(client):
    response = client.post(
        "/api/orders",
        data=VALID_ORDER_XML,
        headers={
            "Content-Type": "application/xml",
            "X-Request-ID": "test-request-123",
        },
    )

    assert response.status_code == 201
    assert response.headers["X-Request-ID"] == "test-request-123"