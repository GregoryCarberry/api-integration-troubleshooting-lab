from __future__ import annotations

import pathlib
import sys
import uuid

import requests

BASE_URL = "http://127.0.0.1:5000"
CREATE_ORDER_URL = f"{BASE_URL}/api/orders"
HEALTH_URL = f"{BASE_URL}/health"

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "examples"

VALID_XML = (EXAMPLES_DIR / "valid-order.xml").read_text(encoding="utf-8")
MALFORMED_XML = (EXAMPLES_DIR / "malformed-order.xml").read_text(encoding="utf-8")
INVALID_XML_MISSING_FIELD = """<Order>
  <CustomerID>cust-001</CustomerID>
  <ProductID>prod-123</ProductID>
</Order>
"""


def print_result(name: str, resp: requests.Response) -> None:
    print(f"\n=== {name} ===")
    print(f"Request : {resp.request.method} {resp.request.url}")
    print(f"Status  : {resp.status_code}")
    print(f"CT      : {resp.headers.get('Content-Type', '')}")
    print(f"Req ID  : {resp.headers.get('X-Request-ID', '<missing>')}")
    body = (resp.text or "").strip()
    print("Body    :")
    print(body if body else "<empty>")


def get_health() -> requests.Response:
    return requests.get(HEALTH_URL, timeout=10)


def post_order(
    xml_payload: str,
    *,
    content_type: str = "application/xml",
    failure_mode: str | None = None,
    request_id: str | None = None,
    timeout: int = 10,
) -> requests.Response:
    headers = {
        "Content-Type": content_type,
        "X-Request-ID": request_id or f"test-{uuid.uuid4().hex[:8]}",
    }

    if failure_mode is not None:
        headers["X-Failure-Mode"] = failure_mode

    return requests.post(
        CREATE_ORDER_URL,
        headers=headers,
        data=xml_payload.encode("utf-8"),
        timeout=timeout,
    )


def main() -> int:
    scenarios: list[tuple[str, requests.Response]] = []

    # 0) Health check
    scenarios.append(("0) Health check (expected 200)", get_health()))

    # 1) Success path
    scenarios.append(
        (
            "1) Successful request (expected 201)",
            post_order(VALID_XML),
        )
    )

    # 2) Malformed XML
    scenarios.append(
        (
            "2) Malformed XML (expected 400)",
            post_order(MALFORMED_XML),
        )
    )

    # 3) Validation failure - missing Quantity
    scenarios.append(
        (
            "3) Validation failure (expected 422)",
            post_order(INVALID_XML_MISSING_FIELD),
        )
    )

    # 4) Wrong Content-Type
    scenarios.append(
        (
            "4) Wrong Content-Type (expected 415)",
            post_order(VALID_XML, content_type="application/json"),
        )
    )

    # 5) Invalid failure mode
    scenarios.append(
        (
            "5) Invalid failure mode header (expected 400)",
            post_order(VALID_XML, failure_mode="banana"),
        )
    )

    # 6) Simulated dependency failure
    scenarios.append(
        (
            "6) Simulated dependency failure (expected 503)",
            post_order(VALID_XML, failure_mode="dependency"),
        )
    )

    # 7) Simulated internal exception
    scenarios.append(
        (
            "7) Simulated internal exception (expected 500)",
            post_order(VALID_XML, failure_mode="exception"),
        )
    )

    # 8) Simulated timeout
    scenarios.append(
        (
            "8) Simulated timeout (expected 504)",
            post_order(VALID_XML, failure_mode="timeout", timeout=15),
        )
    )

    for name, response in scenarios:
        print_result(name, response)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
