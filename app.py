from __future__ import annotations

import logging
import os
import time
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

SIMULATED_TIMEOUT_SECONDS = float(os.getenv("SIMULATED_TIMEOUT_SECONDS", "6"))
ALLOWED_FAILURE_MODES = {"none", "timeout", "dependency", "exception"}


@app.before_request
def attach_request_id() -> None:
    incoming_request_id = request.headers.get("X-Request-ID", "").strip()
    g.request_id = incoming_request_id or str(uuid4())[:8]


def get_request_id() -> str:
    if not hasattr(g, "request_id"):
        g.request_id = str(uuid4())[:8]
    return g.request_id


def text_response(message: str, status: int) -> Response:
    response = Response(message, status=status, mimetype="text/plain")
    response.headers["X-Request-ID"] = get_request_id()
    return response


def xml_response(body: str, status: int) -> Response:
    response = Response(body, status=status, mimetype="application/xml")
    response.headers["X-Request-ID"] = get_request_id()
    return response


def get_failure_mode() -> str:
    return request.headers.get("X-Failure-Mode", "none").strip().lower()


def validate_failure_mode(failure_mode: str) -> None:
    if failure_mode not in ALLOWED_FAILURE_MODES:
        raise ValueError(
            "Invalid X-Failure-Mode. Allowed values: none, timeout, dependency, exception"
        )


def simulate_failure_mode(failure_mode: str) -> None:
    if failure_mode == "none":
        return

    if failure_mode == "timeout":
        logger.error(
            "[request_id=%s] Simulating upstream timeout for %.1f seconds",
            get_request_id(),
            SIMULATED_TIMEOUT_SECONDS,
        )
        time.sleep(SIMULATED_TIMEOUT_SECONDS)
        raise TimeoutError("Simulated upstream timeout occurred")

    if failure_mode == "dependency":
        logger.error("[request_id=%s] Simulating upstream dependency failure", get_request_id())
        raise ConnectionError("Simulated upstream dependency failure")

    if failure_mode == "exception":
        logger.error("[request_id=%s] Simulating unhandled backend exception", get_request_id())
        raise RuntimeError("Simulated unhandled backend exception")


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
    except ET.ParseError as exc:
        logger.error(
            "[request_id=%s] Malformed XML payload received: %s",
            get_request_id(),
            exc,
        )
        raise SyntaxError(f"Malformed XML: {exc}") from exc

    if root.tag != "Order":
        raise LookupError("Invalid XML: root element must be <Order>")

    def get_text(tag: str) -> str:
        element = root.find(tag)
        if element is None or element.text is None or not element.text.strip():
            raise LookupError(f"Invalid XML: missing or empty <{tag}>")
        return element.text.strip()

    customer_id = get_text("CustomerID")
    product_id = get_text("ProductID")
    quantity = get_text("Quantity")

    if not quantity.isdigit() or int(quantity) <= 0:
        raise LookupError("Invalid XML: <Quantity> must be a positive integer")

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


@app.get("/health")
def health() -> Response:
    response = Response("ok\n", status=200, mimetype="text/plain")
    response.headers["X-Request-ID"] = get_request_id()
    return response


@app.post("/api/orders")
def create_order() -> Response:
    logger.info("[request_id=%s] Incoming request: POST /api/orders", get_request_id())
    logger.info("[request_id=%s] Headers: %s", get_request_id(), dict(request.headers))

    content_type = request.headers.get("Content-Type", "")
    if "application/xml" not in content_type.lower():
        logger.error(
            "[request_id=%s] Unsupported Content-Type received: %s",
            get_request_id(),
            content_type,
        )
        return text_response(
            "Unsupported Media Type: Content-Type must be application/xml\n",
            status=415,
        )

    if not request.data:
        logger.error("[request_id=%s] Empty request body received", get_request_id())
        return text_response("Bad Request: request body is empty\n", status=400)

    failure_mode = get_failure_mode()
    try:
        validate_failure_mode(failure_mode)
    except ValueError as exc:
        logger.error("[request_id=%s] Invalid failure mode: %s", get_request_id(), exc)
        return text_response(f"Bad Request: {exc}\n", status=400)

    try:
        order = parse_order_xml(request.data)
    except SyntaxError as exc:
        logger.error("[request_id=%s] XML parsing failed: %s", get_request_id(), exc)
        return text_response(f"Bad Request: {exc}\n", status=400)
    except LookupError as exc:
        logger.error("[request_id=%s] XML validation failed: %s", get_request_id(), exc)
        return text_response(f"Unprocessable Entity: {exc}\n", status=422)

    try:
        simulate_failure_mode(failure_mode)
    except TimeoutError as exc:
        return text_response(f"Gateway Timeout: {exc}\n", status=504)
    except ConnectionError as exc:
        return text_response(f"Service Unavailable: {exc}\n", status=503)
    except RuntimeError:
        logger.exception("[request_id=%s] Internal server error", get_request_id())
        return text_response(
            "Internal Server Error: simulated backend exception\n",
            status=500,
        )

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

    failure_mode = get_failure_mode()
    try:
        validate_failure_mode(failure_mode)
    except ValueError as exc:
        logger.error("[request_id=%s] Invalid failure mode: %s", get_request_id(), exc)
        return text_response(f"Bad Request: {exc}\n", status=400)

    try:
        simulate_failure_mode(failure_mode)
    except TimeoutError as exc:
        return text_response(f"Gateway Timeout: {exc}\n", status=504)
    except ConnectionError as exc:
        return text_response(f"Service Unavailable: {exc}\n", status=503)
    except RuntimeError:
        logger.exception("[request_id=%s] Internal server error", get_request_id())
        return text_response(
            "Internal Server Error: simulated backend exception\n",
            status=500,
        )

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
