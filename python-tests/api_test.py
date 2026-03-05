from __future__ import annotations

import pathlib
import sys
import requests

BASE_URL = "http://127.0.0.1:5000"
CREATE_ORDER_URL = f"{BASE_URL}/api/orders"
API_KEY = "test-api-key-123"

ROOT = pathlib.Path(__file__).resolve().parents[1]
XML_DIR = ROOT / "xml-examples"

VALID_XML = (XML_DIR / "valid-order.xml").read_text(encoding="utf-8")
MALFORMED_XML = (XML_DIR / "malformed-order.xml").read_text(encoding="utf-8")


def print_result(name: str, resp: requests.Response) -> None:
    print(f"\n=== {name} ===")
    print(f"Request: {resp.request.method} {resp.request.url}")
    print(f"Status : {resp.status_code}")
    ct = resp.headers.get("Content-Type", "")
    print(f"CT     : {ct}")
    print("Body   :")
    body = (resp.text or "").strip()
    print(body if body else "<empty>")


def post_order(xml_payload: str, include_api_key: bool = True, content_type: str = "application/xml") -> requests.Response:
    headers = {"Content-Type": content_type}
    if include_api_key:
        headers["X-API-Key"] = API_KEY

    return requests.post(
        CREATE_ORDER_URL,
        headers=headers,
        data=xml_payload.encode("utf-8"),
        timeout=10,
    )


def main() -> int:
    # 1) Success path
    resp1 = post_order(VALID_XML, include_api_key=True, content_type="application/xml")
    print_result("1) Successful request (expected 201)", resp1)

    # 2) Auth failure
    resp2 = post_order(VALID_XML, include_api_key=False, content_type="application/xml")
    print_result("2) Missing API key (expected 401)", resp2)

    # 3) Malformed XML
    resp3 = post_order(MALFORMED_XML, include_api_key=True, content_type="application/xml")
    print_result("3) Malformed XML (expected 400)", resp3)

    # Optional: Content-Type mismatch (useful bonus scenario)
    resp4 = post_order(VALID_XML, include_api_key=True, content_type="application/json")
    print_result("4) Wrong Content-Type (expected 400)", resp4)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())