"""Shared helpers for the hardened HeyHuman Lambdas.

EXPERIMENTAL CODE. Do not use in production.
"""
# File UUID: 2b7e4c19-5a83-4d6f-9e02-71c3a8f4d5b6

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from typing import Any

SESSION_RE = re.compile(r"^[A-Za-z0-9_-]{22}$")  # secrets.token_urlsafe(16)
MAX_HTML_BYTES = 64 * 1024
MAX_MESSAGE_CHARS = 500
MAX_DECISION_CHARS = 2000
DEFAULT_TTL_SECONDS = 600
MAX_TTL_SECONDS = 3600
RECORD_GRACE_SECONDS = 86400  # DynamoDB deletes the record a day after expiry

def topic_for(session_id: str) -> str:
    return f"{os.environ.get('TOPIC_PREFIX', 'heyhuman')}/{session_id}/response"


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def now() -> int:
    return int(time.time())


def json_response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        },
        "body": json.dumps(body),
    }


def parse_body(event: dict[str, Any]) -> dict[str, Any] | None:
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64

        raw = base64.b64decode(raw).decode()
    try:
        body = json.loads(raw)
    except ValueError:
        return None
    return body if isinstance(body, dict) else None


def method_and_path(event: dict[str, Any]) -> tuple[str, str]:
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    return method, event.get("rawPath", "/")
