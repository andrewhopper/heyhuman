# File UUID: 7c2e9a41-5d16-4b83-a0f7-3e8d1b6c9f52
"""MCP server tests against a real local HeyHuman server (SQLite) and the real CLI."""
import asyncio
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).parents[1]))
import heyhuman_mcp as m  # noqa: E402


def run(c):
    return asyncio.run(c)


def free_port() -> int:
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    port = free_port()
    db = tmp_path_factory.mktemp("db") / "h.db"
    env = {**os.environ, "HEYHUMAN_STORE": "sqlite", "HEYHUMAN_PUBLISH": "none"}
    proc = subprocess.Popen([sys.executable, "-I", str(REPO / "local" / "serve.py"), "--host", "127.0.0.1",
                             "--port", str(port), "--db", str(db), "--public-url", f"http://127.0.0.1:{port}"],
                            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(50):
        try:
            socket.create_connection(("127.0.0.1", port), 0.2).close(); break
        except OSError:
            time.sleep(0.1)
    os.environ["HEYHUMAN_AGENT_URL"] = f"http://127.0.0.1:{port}"
    os.environ.pop("HEYHUMAN_MQTT_URL", None)
    yield port
    proc.terminate()


def answer(url: str, decision: str) -> int:
    base, token = url.split("#t=")
    req = urllib.request.Request(base + "/answer", method="POST", headers={"content-type": "application/json"},
                                 data=json.dumps({"token": token, "decision": decision}).encode())
    try:
        return urllib.request.urlopen(req).status
    except urllib.error.HTTPError as e:
        return e.code


def test_tools_registered():
    assert {t.name for t in run(m.mcp.list_tools())} == {"heyhuman_start", "heyhuman_wait", "heyhuman_resume"}


def test_start_wait_with_agent_html(server):
    r = run(m.heyhuman_start(html="<button onclick=\"decide('yes')\">Yes</button>", message="Go?"))
    assert r["ok"] and len(r["session"]) == 22 and "#t=" in r["url"]
    assert answer(r["url"], "yes") == 200
    w = run(m.heyhuman_wait(r["session"], 10))
    assert w == {"ok": True, "decision": "yes"}


def test_template_renders_and_rejects_unknown(server):
    r = run(m.heyhuman_start(template="single-choice", data={"title": "Pick", "options": ["A", "B <script>"]}))
    assert r["ok"]
    page = urllib.request.urlopen(r["url"].split("#")[0] + "/content").read().decode()
    assert "B &lt;script&gt;" in page and "<script>" not in page.split("</head>")[1].replace("<script>\nfunction decide", "")
    assert run(m.heyhuman_start(template="../x"))["ok"] is False


def test_resume_after_agent_crash(server):
    r = run(m.heyhuman_start(template="approve-deny", data={"title": "Ship?"}, run_id="mcp-run-1"))
    assert r["ok"]
    assert answer(r["url"], "approved") == 200  # human answers while no agent is waiting
    assert run(m.heyhuman_resume("mcp-run-1", 10)) == {"ok": True, "decision": "approved"}
    assert run(m.heyhuman_resume("mcp-run-1", 5))["ok"] is False  # nothing open now


def test_input_validation():
    assert run(m.heyhuman_wait("--stream", 5))["ok"] is False
    assert run(m.heyhuman_start())["ok"] is False
    assert run(m.heyhuman_start(html="x", run_id="bad id"))["ok"] is False
