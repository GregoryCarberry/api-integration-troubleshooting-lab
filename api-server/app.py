from __future__ import annotations

from flask import Flask, Response, request
import xml.etree.ElementTree as ET
from uuid import uuid4

app = Flask(__name__)

# Simple in-memory store for demo purposes
ORDERS: dict[str, dict[str, str]] = {}

# Fake API key used to simulate auth success/failure
EXPECTED_API_KEY = "test-api-key-123"


def require_api_key() -> tuple[bool, Response | None]:
    """Check API key in header. Return (ok, response_if_not_ok)."""
    api_key = request.headers.get("X-API-Key", "")
    if api_key != EXPECTED_API_KEY:
        return False, Response(
            "Unauthorized: missing or invalid X-API-Key\n",
            status=401,
            mimetype="text/plain",
        )
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

    # Validate quantity looks like a positive integer
    if not quantity.isdigit() or int(quantity) <= 0:
        raise ValueError("Invalid XML: <Quantity> must be a positive integer")

    return {"customer_id": customer_id, "product_id": product_id, "quantity": quantity}


@app.get("/health")
def health() -> Response:
    return Response("ok\n", status=200, mimetype="text/plain")


@app.post("/api/orders")
def create_order() -> Response:
    ok, resp = require_api_key()
    if not ok:
        return resp  # 401

    content_type = request.headers.get("Content-Type", "")
    if "xml" not in content_type.lower():
        return Response(
            "Bad Request: Content-Type must be application/xml\n",
            status=400,
            mimetype="text/plain",
        )

    try:
        order = parse_order_xml(request.data)
    except ValueError as e:
        return Response(
            f"Bad Request: {e}\n",
            status=400,
            mimetype="text/plain",
        )

    order_id = str(uuid4())
    ORDERS[order_id] = order

    # Return minimal XML response to keep the theme consistent
    response_xml = (
        f"<OrderCreated><OrderID>{order_id}</OrderID></OrderCreated>\n"
    )
    return Response(response_xml, status=201, mimetype="application/xml")


@app.get("/api/orders/<order_id>")
def get_order(order_id: str) -> Response:
    ok, resp = require_api_key()
    if not ok:
        return resp  # 401

    order = ORDERS.get(order_id)
    if not order:
        return Response("Not Found\n", status=404, mimetype="text/plain")

    response_xml = (
        "<Order>"
        f"<OrderID>{order_id}</OrderID>"
        f"<CustomerID>{order['customer_id']}</CustomerID>"
        f"<ProductID>{order['product_id']}</ProductID>"
        f"<Quantity>{order['quantity']}</Quantity>"
        "</Order>\n"
    )
    return Response(response_xml, status=200, mimetype="application/xml")


if __name__ == "__main__":
    # Bind to localhost only (safe default)
    app.run(host="127.0.0.1", port=5000, debug=True)