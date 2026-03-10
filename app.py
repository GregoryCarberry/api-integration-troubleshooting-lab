from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from uuid import uuid4

from flask import Flask, Response, g, request

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

logger = logging.getLogger(__name__)

app = Flask(__name__)

# Simple in-memory store for demo purposes
ORDERS: dict[str, dict[str, str]] = {}

# Fake API key used to simulate auth success/failure
EXPECTED_API_KEY = "test-api-key-123"


@app.before_request
def attach_request_id() -> None:
    g.request_id = str(uuid4())[:8]


def get_request_id() -> str:
    if not hasattr(g, "request_id"):
        g.request_id = str(uuid4())[:8]
    return g.request_id


def require_api_key() -> tuple[bool, Response | None]:
    """Check API key in header. Return (ok, response_if_not_ok)."""
    api_key = request.headers.get("X-API-Key", "")

    if api_key != EXPECTED_API_KEY:
        logger.error(
            "[request_id=%s] Authentication failed: missing or invalid X-API-Key",
            get_request_id(),
        )
        response = Response(
            "Unauthorized: missing or invalid X-API-Key\n",
            status=401,
            mimetype="text/plain",
        )
        response.headers["X-Request-ID"] = get_request_id()
        return False, response

    logger.info("[request_id=%s] Authentication successful", get_request_id())
    return True, None


def parse_order_xml(xml_bytes: bytes) -> dict[str, str]:
    """
    Parse <Order> XML.
    Expected:
      <Order>
        <CustomerID>...</CustomerID>
        <ProductID>...</ProductID>
        <Quantity>...</Quantity>
      </Order>
    """
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        logger.error("[request_id=%s] Malformed XML payload received: %s", get_request_id(), e)
        raise ValueError(f"Malformed XML: {e}") from e

    if root.tag != "Order":
        raise ValueError("Invalid XML: root element must be <Order>")

    def get_text(tag: str) -> str:
        el = root.find(tag)
        if el is None or el.text is None or not el.text.strip():
            raise ValueError(f"Invalid XML: missing or empty <{tag}>")
        return el.text.strip()

    customer_id = get_text("CustomerID")
    product_id = get_text("ProductID")
    quantity = get_text("Quantity")

    if not quantity.isdigit() or int(quantity) <= 0:
        raise ValueError("Invalid XML: <Quantity> must be a positive integer")

    logger.info(
        "[request_id=%s] Parsed XML payload: customer_id=%s product_id=%s quantity=%s",
        get_request_id(),
        customer_id,
        product_id,
        quantity,
    )

    return {
        "customer_id": customer_id,
        "product_id": product_id,
        "quantity": quantity,
    }


def text_response(message: str, status: int) -> Response:
    response = Response(message, status=status, mimetype="text/plain")
    response.headers["X-Request-ID"] = get_request_id()
    return response


def xml_response(body: str, status: int) -> Response:
    response = Response(body, status=status, mimetype="application/xml")
    response.headers["X-Request-ID"] = get_request_id()
    return response


@app.get("/health")
def health() -> Response:
    return Response("ok\n", status=200, mimetype="text/plain")


@app.post("/api/orders")
def create_order() -> Response:
    logger.info("[request_id=%s] Incoming request: POST /api/orders", get_request_id())
    logger.info("[request_id=%s] Headers: %s", get_request_id(), dict(request.headers))

    ok, resp = require_api_key()
    if not ok:
        return resp

    content_type = request.headers.get("Content-Type", "")
    if "xml" not in content_type.lower():
        logger.error(
            "[request_id=%s] Invalid Content-Type received: %s",
            get_request_id(),
            content_type,
        )
        return text_response(
            "Bad Request: Content-Type must be application/xml\n",
            status=400,
        )

    try:
        order = parse_order_xml(request.data)
    except ValueError as e:
        logger.error("[request_id=%s] XML validation failed: %s", get_request_id(), e)
        return text_response(f"Bad Request: {e}\n", status=400)

    order_id = str(uuid4())
    ORDERS[order_id] = order

    logger.info("[request_id=%s] Order created successfully: %s", get_request_id(), order_id)

    response_xml = f"<OrderCreated><OrderID>{order_id}</OrderID></OrderCreated>\n"
    return xml_response(response_xml, status=201)


@app.get("/api/orders/<order_id>")
def get_order(order_id: str) -> Response:
    logger.info(
        "[request_id=%s] Incoming request: GET /api/orders/%s",
        get_request_id(),
        order_id,
    )

    ok, resp = require_api_key()
    if not ok:
        return resp

    order = ORDERS.get(order_id)
    if not order:
        logger.warning("[request_id=%s] Order not found: %s", get_request_id(), order_id)
        return text_response("Not Found\n", status=404)

    logger.info("[request_id=%s] Order retrieved successfully: %s", get_request_id(), order_id)

    response_xml = (
        "<Order>"
        f"<OrderID>{order_id}</OrderID>"
        f"<CustomerID>{order['customer_id']}</CustomerID>"
        f"<ProductID>{order['product_id']}</ProductID>"
        f"<Quantity>{order['quantity']}</Quantity>"
        "</Order>\n"
    )
    return xml_response(response_xml, status=200)


if __name__ == "__main__":
    logger.info("Starting API server on http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
