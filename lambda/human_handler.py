"""Human-facing pages, behind a public Function URL.

GET  /f/{id}            host page: strict CSP, sandboxed iframe, host-rendered confirm bar
GET  /f/{id}/content    the agent's HTML, served with a CSP sandbox and no network access
POST /f/{id}/answer     one-time answer: token must match, session pending and unexpired

EXPERIMENTAL CODE. Do not use in production.
"""
# File UUID: 9c4e2a71-3d58-4b06-8f1e-5a7b3c9d2e60

from __future__ import annotations

import json
import secrets
from typing import Any

from common import (
    MAX_DECISION_CHARS,
    SESSION_RE,
    json_response,
    method_and_path,
    now,
    parse_body,
    sha256,
    topic_for,
)
from store import load_session, publisher, session_stream, store
from page import content_page, host_page, status_page

CONTENT_CSP = (
    "sandbox allow-scripts; default-src 'none'; script-src 'unsafe-inline'; "
    "style-src 'unsafe-inline'; img-src data:; font-src data:; connect-src 'none'; "
    "form-action 'none'; base-uri 'none'; frame-ancestors 'self'"
)


def host_csp(nonce: str) -> str:
    return (
        f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'nonce-{nonce}'; "
        "frame-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; "
        "form-action 'none'; frame-ancestors 'none'"
    )


def html_response(status: int, body: str, csp: str) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "text/html; charset=utf-8",
            "Content-Security-Policy": csp,
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        },
        "body": body,
    }


def load_open_session(session_id: str) -> tuple[dict[str, Any] | None, str]:
    """Return (item, state) where state is pending, answered, expired or missing."""
    if not SESSION_RE.match(session_id):
        return None, "missing"
    item = load_session(session_id)
    if not item:
        return None, "missing"
    if item["status"] != "pending":
        return item, str(item["status"])
    if int(item["expires_at"]) <= now():
        return item, "expired"
    return item, "pending"


def show_host(session_id: str) -> dict[str, Any]:
    nonce = secrets.token_urlsafe(16)
    item, state = load_open_session(session_id)
    if state != "pending" or item is None:
        return html_response(404 if state == "missing" else 410, status_page(state, nonce), host_csp(nonce))
    return html_response(200, host_page(session_id, str(item.get("message", "")), nonce), host_csp(nonce))


def show_content(session_id: str) -> dict[str, Any]:
    item, state = load_open_session(session_id)
    if state != "pending" or item is None:
        return html_response(404, "<!doctype html><p>Not available.</p>", CONTENT_CSP)
    return html_response(200, content_page(str(item["html"])), CONTENT_CSP)


def answer(session_id: str, event: dict[str, Any]) -> dict[str, Any]:
    body = parse_body(event)
    if body is None or not SESSION_RE.match(session_id):
        return json_response(400, {"error": "bad request"})
    token, decision = body.get("token"), body.get("decision")
    if not isinstance(token, str) or not isinstance(decision, str):
        return json_response(400, {"error": "token and decision are required"})
    if not decision or len(decision) > MAX_DECISION_CHARS:
        return json_response(400, {"error": f"decision must be 1 to {MAX_DECISION_CHARS} chars"})

    answered_at = now()
    if not store().answer(session_id, sha256(token), decision, answered_at):
        # Same answer for a wrong token, a reused link and an expired one.
        return json_response(409, {"error": "this link can no longer be answered"})

    # If publishing fails the answer is still stored; the agent's status poll gets it.
    published = publisher().publish(topic_for(session_id), json.dumps({"session": session_id, "decision": decision, "answered_at": answered_at}))
    store().append(session_stream(session_id), 3, "AnswerPublished", {"published": published}, now())
    return json_response(200, {"status": "answered", "published": published})


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    method, path = method_and_path(event)
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2 and parts[0] == "f":
        session_id = parts[1]
        rest = parts[2:]
        if method == "GET" and not rest:
            return show_host(session_id)
        if method == "GET" and rest == ["content"]:
            return show_content(session_id)
        if method == "POST" and rest == ["answer"]:
            return answer(session_id, event)
    return json_response(404, {"error": "not found"})
