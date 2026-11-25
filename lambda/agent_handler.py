"""Agent-facing API, behind a Function URL with AWS_IAM auth.

POST /sessions              create a question; returns a one-time link for the human
GET  /sessions/{id}         status and decision (polling fallback for the MQTT path)
POST /runs/{id}/events      append to the agent's own event stream (optimistic: seq must be next)
GET  /runs/{id}/events      read the stream back, to rehydrate after a crash

EXPERIMENTAL CODE. Do not use in production.
"""
# File UUID: 6f1a9d3e-8c24-47b5-a0e6-3d9b2c7f1e48

from __future__ import annotations

import os
import secrets
from typing import Any

import json
import re

from store import load_session, store
from common import (
    DEFAULT_TTL_SECONDS,
    MAX_HTML_BYTES,
    MAX_MESSAGE_CHARS,
    MAX_TTL_SECONDS,
    RECORD_GRACE_SECONDS,
    SESSION_RE,
    json_response,
    method_and_path,
    now,
    parse_body,
    sha256,
    topic_for,
)


def create_session(body: dict[str, Any]) -> dict[str, Any]:
    html = body.get("html")
    message = body.get("message", "Your agent has a question")
    ttl = body.get("ttl_seconds", DEFAULT_TTL_SECONDS)

    if not isinstance(html, str) or not html.strip():
        return json_response(400, {"error": "html is required"})
    if len(html.encode()) > MAX_HTML_BYTES:
        return json_response(413, {"error": f"html is larger than {MAX_HTML_BYTES} bytes"})
    if not isinstance(message, str) or len(message) > MAX_MESSAGE_CHARS:
        return json_response(400, {"error": f"message must be a string of at most {MAX_MESSAGE_CHARS} chars"})
    if not isinstance(ttl, int) or not 30 <= ttl <= MAX_TTL_SECONDS:
        return json_response(400, {"error": f"ttl_seconds must be an integer from 30 to {MAX_TTL_SECONDS}"})

    session_id = secrets.token_urlsafe(16)  # 128 bits
    answer_token = secrets.token_urlsafe(32)  # 256 bits, never stored in clear
    expires_at = now() + ttl

    store().create(
        {
            "session_id": session_id,
            "html": html,
            "message": message,
            "token_hash": sha256(answer_token),
            "status": "pending",
            "created_at": now(),
            "expires_at": expires_at,
            "ttl": expires_at + RECORD_GRACE_SECONDS,
        }
    )

    human_url = os.environ["HUMAN_URL"].rstrip("/")
    return json_response(
        201,
        {
            "session": session_id,
            # The token is in the fragment, so browsers never send it to the server or logs.
            "url": f"{human_url}/f/{session_id}#t={answer_token}",
            "expires_at": expires_at,
            "topic": topic_for(session_id),
        },
    )


def get_status(session_id: str) -> dict[str, Any]:
    if not SESSION_RE.match(session_id):
        return json_response(404, {"error": "not found"})
    item = load_session(session_id)
    if not item:
        return json_response(404, {"error": "not found"})
    status = item["status"]
    if status == "pending" and int(item["expires_at"]) <= now():
        status = "expired"
    out: dict[str, Any] = {"session": session_id, "status": status, "expires_at": int(item["expires_at"])}
    if status == "answered":
        out["decision"] = item.get("decision")
        out["answered_at"] = int(item.get("answered_at", 0))
    return json_response(200, out)


RUN_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
TYPE_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
MAX_EVENT_BYTES = 8 * 1024


def append_run_event(run_id: str, body: dict[str, Any]) -> dict[str, Any]:
    seq, kind, data = body.get("seq"), body.get("type"), body.get("data", {})
    if not isinstance(seq, int) or seq < 1 or not isinstance(kind, str) or not TYPE_RE.match(kind) or not isinstance(data, dict):
        return json_response(400, {"error": "need integer seq >= 1, a type name and a data object"})
    if len(json.dumps(data).encode()) > MAX_EVENT_BYTES:
        return json_response(413, {"error": f"data is larger than {MAX_EVENT_BYTES} bytes"})
    if not store().append(f"run#{run_id}", seq, kind, data, now()):
        events = store().read(f"run#{run_id}")
        return json_response(409, {"error": "seq already used", "last_seq": events[-1]["seq"] if events else 0})
    return json_response(201, {"run": run_id, "seq": seq})


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    method, path = method_and_path(event)
    if method == "POST" and path.rstrip("/") == "/sessions":
        body = parse_body(event)
        if body is None:
            return json_response(400, {"error": "body must be a JSON object"})
        return create_session(body)
    parts = [p for p in path.split("/") if p]
    if len(parts) == 3 and parts[0] == "runs" and parts[2] == "events" and RUN_RE.match(parts[1]):
        if method == "GET":
            return json_response(200, {"run": parts[1], "events": store().read(f"run#{parts[1]}")})
        if method == "POST":
            body = parse_body(event)
            return json_response(400, {"error": "body must be a JSON object"}) if body is None else append_run_event(parts[1], body)
    if method == "GET" and path.startswith("/sessions/"):
        return get_status(path.removeprefix("/sessions/").strip("/"))
    return json_response(404, {"error": "not found"})
