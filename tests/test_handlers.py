"""Handler tests for the hardened HeyHuman Lambdas."""
# File UUID: 8e1a6c27-4f90-4b3d-a5e2-7c9d0b4f1a83
import json
from typing import Any

import agent_handler
import common
import human_handler


def ev(method: str, path: str, body: Any = None) -> dict:
    e: dict = {"rawPath": path, "requestContext": {"http": {"method": method}}}
    if body is not None:
        e["body"] = json.dumps(body)
    return e


def create(**over: Any) -> tuple[str, str]:
    r = agent_handler.handler(ev("POST", "/sessions", {"html": "<button onclick=\"decide('yes')\">Yes</button>", **over}), None)
    assert r["statusCode"] == 201, r
    b = json.loads(r["body"])
    return b["session"], b["url"].split("#t=")[1]


def answer(sid: str, token: str, decision: str = "yes") -> dict:
    return human_handler.handler(ev("POST", f"/f/{sid}/answer", {"token": token, "decision": decision}), None)


def test_create_returns_128_bit_id_and_fragment_token(aws):
    sid, token = create()
    assert common.SESSION_RE.match(sid) and len(token) >= 43
    import store
    item = store.store().get(sid)
    assert token not in json.dumps(item, default=str)  # only the hash is stored
    assert item["token_hash"] == common.sha256(token)


def test_create_rejects_bad_input(aws):
    big = "x" * (common.MAX_HTML_BYTES + 1)
    assert agent_handler.handler(ev("POST", "/sessions", {"html": big}), None)["statusCode"] == 413
    assert agent_handler.handler(ev("POST", "/sessions", {"html": "<p>", "ttl_seconds": 99999}), None)["statusCode"] == 400
    assert agent_handler.handler(ev("POST", "/sessions", {}), None)["statusCode"] == 400


def test_host_page_has_strict_csp_sandbox_and_escapes_message(aws):
    sid, _ = create(message="<script>alert(1)</script>")
    r = human_handler.handler(ev("GET", f"/f/{sid}"), None)
    csp = r["headers"]["Content-Security-Policy"]
    assert r["statusCode"] == 200 and "script-src 'nonce-" in csp and "unsafe-inline" not in csp
    assert 'sandbox="allow-scripts"' in r["body"] and "allow-same-origin" not in r["body"]
    assert "<script>alert(1)</script>" not in r["body"]


def test_content_is_sandboxed_without_network(aws):
    sid, _ = create()
    r = human_handler.handler(ev("GET", f"/f/{sid}/content"), None)
    csp = r["headers"]["Content-Security-Policy"]
    assert csp.startswith("sandbox allow-scripts") and "connect-src 'none'" in csp
    assert "decide('yes')" in r["body"] and "postMessage" in r["body"]


def test_answer_needs_token_and_is_one_time(aws):
    sid, token = create()
    assert answer(sid, "wrong")["statusCode"] == 409
    r = answer(sid, token)
    assert r["statusCode"] == 200 and aws.published[0]["topic"] == f"heyhuman/{sid}/response"
    assert answer(sid, token, "no")["statusCode"] == 409  # replay
    status = json.loads(agent_handler.handler(ev("GET", f"/sessions/{sid}"), None)["body"])
    assert status["status"] == "answered" and status["decision"] == "yes"
    assert human_handler.handler(ev("GET", f"/f/{sid}"), None)["statusCode"] == 410


def test_expired_session_cannot_be_answered(aws, monkeypatch):
    sid, token = create(ttl_seconds=30)
    real = common.now()
    monkeypatch.setattr(human_handler, "now", lambda: real + 31)
    monkeypatch.setattr(common, "now", lambda: real + 31)
    monkeypatch.setattr(agent_handler, "now", lambda: real + 31)
    assert answer(sid, token)["statusCode"] == 409
    assert json.loads(agent_handler.handler(ev("GET", f"/sessions/{sid}"), None)["body"])["status"] == "expired"


def test_answer_is_kept_when_publish_fails(aws):
    sid, token = create()
    aws.fail = True
    r = answer(sid, token)
    assert r["statusCode"] == 200 and json.loads(r["body"])["published"] is False
    assert json.loads(agent_handler.handler(ev("GET", f"/sessions/{sid}"), None)["body"])["status"] == "answered"


def test_unknown_or_malformed_ids_are_404(aws):
    assert agent_handler.handler(ev("GET", "/sessions/abc"), None)["statusCode"] == 404
    assert human_handler.handler(ev("GET", "/f/../../etc"), None)["statusCode"] == 404
    assert human_handler.handler(ev("GET", "/f/" + "A" * 22), None)["statusCode"] == 404


def test_session_rehydrates_from_events_when_projection_is_lost(aws):
    import store
    sid, token = create()
    assert answer(sid, token)["statusCode"] == 200
    kinds = [e["type"] for e in store.store().read(store.session_stream(sid))]
    assert kinds == ["SessionCreated", "AnswerAccepted", "AnswerPublished"]
    s = store.store()
    if hasattr(s, "client"):
        s.client.delete_item(TableName=s.name, Key={"session_id": {"S": sid}})
    else:
        s.db.execute("DELETE FROM sessions WHERE session_id = ?", (sid,)); s.db.commit()
    assert s.get(sid) is None
    status = json.loads(agent_handler.handler(ev("GET", f"/sessions/{sid}"), None)["body"])
    assert status["status"] == "answered" and status["decision"] == "yes"
    assert s.get(sid) is not None  # projection rebuilt
    assert answer(sid, token, "no")["statusCode"] == 409  # still one-time after rebuild


def test_rejected_answer_writes_no_event(aws):
    import store
    sid, _ = create()
    assert answer(sid, "wrong")["statusCode"] == 409
    assert [e["type"] for e in store.store().read(store.session_stream(sid))] == ["SessionCreated"]


def test_run_stream_append_conflict_and_read(aws):
    post = lambda seq, t="QuestionAsked": agent_handler.handler(ev("POST", "/runs/game-1/events", {"seq": seq, "type": t, "data": {"n": seq}}), None)
    assert post(1)["statusCode"] == 201
    assert post(2, "AnswerReceived")["statusCode"] == 201
    clash = post(2)
    assert clash["statusCode"] == 409 and json.loads(clash["body"])["last_seq"] == 2
    got = json.loads(agent_handler.handler(ev("GET", "/runs/game-1/events"), None)["body"])["events"]
    assert [(e["seq"], e["type"], e["data"]["n"]) for e in got] == [(1, "QuestionAsked", 1), (2, "AnswerReceived", 2)]
    assert agent_handler.handler(ev("POST", "/runs/bad id/events", {"seq": 1, "type": "X"}), None)["statusCode"] == 404
    assert agent_handler.handler(ev("POST", "/runs/r/events", {"seq": 0, "type": "X"}), None)["statusCode"] == 400
