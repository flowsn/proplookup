#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from urllib.parse import parse_qs

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.api_core import dumps, health, parcel_detail, parcels_bbox


def respond(status: str, body: dict, content_type: str = "application/json") -> None:
    print(f"Status: {status}")
    print(f"Content-Type: {content_type}")
    print("Cache-Control: no-store")
    print()
    print(dumps(body))


def main() -> None:
    path = os.environ.get("PATH_INFO", "") or "/"
    query = parse_qs(os.environ.get("QUERY_STRING", ""))
    try:
        if path == "/health":
            respond("200 OK", health())
        elif path == "/parcels":
            bbox = query.get("bbox", [None])[0]
            if not bbox:
                respond("400 Bad Request", {"error": "bbox required"})
                return
            respond("200 OK", parcels_bbox(bbox))
        elif path.startswith("/parcels/"):
            row = parcel_detail(path.rsplit("/", 1)[-1])
            respond("200 OK", row) if row else respond("404 Not Found", {"error": "not found"})
        else:
            respond("404 Not Found", {"error": "route not found"})
    except Exception as exc:
        respond("500 Internal Server Error", {"error": str(exc)})


if __name__ == "__main__":
    main()
