#!/usr/bin/env python3
"""HeyHuman CLI for the hardened stack. EXPERIMENTAL CODE. Do not use in production.

  heyhuman.py ask --html form.html --message "Deploy?"   prints the link, waits, prints the answer
  heyhuman.py start --html form.html                      create only; prints JSON with session and url
  heyhuman.py wait <session>                              wait for an answer to a session started earlier
  heyhuman.py ask --template approve-deny --data '{"title":"Deploy?"}'   built-in forms, no HTML
  heyhuman.py ask --html - < form.html                    read the form from stdin
  heyhuman.py status <session>
  heyhuman.py ask --run game-1 ...        also record QuestionAsked / AnswerReceived in run stream game-1
  heyhuman.py resume --run game-1         after a crash: wait on the open question, no new link
  heyhuman.py events --run game-1         print the run's event stream

  heyhuman.py serve --local [--public-url URL]            run the whole stack as one local process

Env: HEYHUMAN_AGENT_URL (stack output AgentUrl, or http://127.0.0.1:8787 when local), plus
AWS credentials for the AWS stack. HEYHUMAN_AGENT_KEY sends a bearer key instead of SigV4
(local server in Docker). HEYHUMAN_MQTT_URL subscribes to a plain MQTT broker (Mosquitto).
Waiting: subscribes over MQTT when awsiotsdk is installed, and always polls the stored
status as well, so an answer given before the subscription is never missed.
Exit codes: 0 answered, 2 timed out or expired, 1 error.
"""
# File UUID: 4d8e1b37-9c62-4a05-b1f3-e7a2c6d9f048

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

import boto3
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest


def agent_url() -> str:
    url = os.environ.get("HEYHUMAN_AGENT_URL")
    if not url:
        sys.exit("Set HEYHUMAN_AGENT_URL to the stack's AgentUrl output.")
    return url.rstrip("/")


def signed(method: str, url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        return signed_raw(method, url, body)
    except urllib.error.HTTPError as err:
        detail = err.read().decode(errors="replace")[:300]
        sys.exit(f"HeyHuman API error {err.code}: {detail}")


def signed_raw(method: str, url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    key = os.environ.get("HEYHUMAN_AGENT_KEY")
    local = urllib.parse.urlparse(url).hostname in ("127.0.0.1", "localhost", "::1")
    if key:
        headers["Authorization"] = f"Bearer {key}"
    elif not local:
        session = boto3.Session()
        req = AWSRequest(method=method, url=url, data=data, headers=headers)
        creds = session.get_credentials()
        if creds is not None:
            SigV4Auth(creds.get_frozen_credentials(), "lambda", session.region_name or "us-east-1").add_auth(req)
        headers = dict(req.headers)
    prepared = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(prepared, timeout=15) as r:
        return json.loads(r.read())


def plain_mqtt_listen(url: str, topic: str, got: threading.Event, box: dict[str, Any]) -> None:
    """Subscribe on a plain MQTT broker such as Mosquitto (local and Docker runs)."""
    try:
        import paho.mqtt.client as paho  # type: ignore[import-not-found]

        u = urllib.parse.urlparse(url)
        c = paho.Client(paho.CallbackAPIVersion.VERSION2, client_id=f"heyhuman-cli-{os.getpid()}")

        def on_msg(_c: Any, _u: Any, msg: Any) -> None:
            box["decision"] = json.loads(msg.payload).get("decision")
            got.set()

        c.on_message = on_msg
        c.connect(u.hostname or "localhost", u.port or 1883)
        c.subscribe(topic, qos=1)
        c.loop_start()
        got.wait()
        c.loop_stop()
        c.disconnect()
    except Exception as err:  # noqa: BLE001
        print(f"[heyhuman] MQTT unavailable ({err.__class__.__name__}); polling only", file=sys.stderr)


def mqtt_listen(topic: str, got: threading.Event, box: dict[str, Any]) -> None:
    """Best effort: if awsiotsdk is missing or the connection fails, polling still works."""
    if os.environ.get("HEYHUMAN_MQTT_URL"):
        return plain_mqtt_listen(os.environ["HEYHUMAN_MQTT_URL"], topic, got, box)
    if urllib.parse.urlparse(agent_url()).hostname in ("127.0.0.1", "localhost", "::1"):
        return  # local server without a broker: poll only
    try:
        from awscrt import mqtt  # type: ignore[import-not-found]
        from awsiot import mqtt_connection_builder  # type: ignore[import-not-found]

        endpoint = boto3.client("iot").describe_endpoint(endpointType="iot:Data-ATS")["endpointAddress"]
        conn = mqtt_connection_builder.websockets_with_default_aws_signing(
            endpoint=endpoint,
            region=boto3.Session().region_name or "us-east-1",
            credentials_provider=__import__("awscrt.auth", fromlist=["x"]).AwsCredentialsProvider.new_default_chain(),
            client_id=f"{topic.split('/')[0]}-{os.getpid()}-{int(time.time())}",
            clean_session=True,
        )
        conn.connect().result(timeout=15)

        def on_msg(topic: str, payload: bytes, **_: Any) -> None:
            box["decision"] = json.loads(payload).get("decision")
            got.set()

        conn.subscribe(topic=topic, qos=mqtt.QoS.AT_LEAST_ONCE, callback=on_msg)[0].result(timeout=15)
        got.wait()
        conn.disconnect()
    except Exception as err:  # noqa: BLE001
        print(f"[heyhuman] MQTT unavailable ({err.__class__.__name__}); polling only", file=sys.stderr)


def wait(session: str, topic: str, timeout: int, poll: float, use_mqtt: bool, box: dict[str, Any] | None = None) -> int:
    got = threading.Event()
    box = {} if box is None else box
    if use_mqtt:
        threading.Thread(target=mqtt_listen, args=(topic, got, box), daemon=True).start()
    deadline = time.time() + timeout
    while time.time() < deadline:
        if got.wait(timeout=poll):
            box["final"] = box["decision"]
            print(box["decision"])
            return 0
        status = signed("GET", f"{agent_url()}/sessions/{session}")
        if status["status"] == "answered":
            box["final"] = status["decision"]
            print(status["decision"])
            return 0
        if status["status"] == "expired":
            print("[heyhuman] expired without an answer", file=sys.stderr)
            return 2
        print(f"[heyhuman] waiting ({int(deadline - time.time())}s left)", file=sys.stderr)
    print("[heyhuman] timed out", file=sys.stderr)
    return 2


def run_events(run: str) -> list[dict[str, Any]]:
    return signed("GET", f"{agent_url()}/runs/{run}/events")["events"]


def run_append(run: str, kind: str, data: dict[str, Any]) -> None:
    """Append with optimistic concurrency: retry at the next free seq if another writer won."""
    for _ in range(5):
        seq = (run_events(run) or [{"seq": 0}])[-1]["seq"] + 1
        try:
            signed_raw("POST", f"{agent_url()}/runs/{run}/events", {"seq": seq, "type": kind, "data": data})
            return
        except urllib.error.HTTPError as err:
            if err.code != 409:
                raise
    sys.exit(f"[heyhuman] could not append {kind} to run {run}")


def open_question(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    answered = {e["data"].get("session") for e in events if e["type"] == "AnswerReceived"}
    asked = [e["data"] for e in events if e["type"] == "QuestionAsked"]
    return next((q for q in reversed(asked) if q["session"] not in answered), None)


def esc(v: Any) -> str:
    import html as _html

    return _html.escape(str(v), quote=True)


def template_html(name: str, data: dict[str, Any]) -> str:
    """Built-in forms, rendered on the agent side, so the agent does not have to write HTML."""
    btn = "display:block;width:100%;min-height:56px;margin:8px 0;font-size:18px;border-radius:12px;border:2px solid #1c1b19;background:#fff"
    title = f"<h2 style='font-family:sans-serif'>{esc(data.get('title', 'Your agent has a question'))}</h2>"
    if name == "approve-deny":
        yes, no = data.get("approveLabel", "Approve"), data.get("denyLabel", "Deny")
        return title + f"<button style='{btn}' onclick=\"decide('approved')\">{esc(yes)}</button>" \
                       f"<button style='{btn}' onclick=\"decide('denied')\">{esc(no)}</button>"
    if name == "single-choice":
        opts = data.get("options") or []
        if not isinstance(opts, list) or not opts:
            sys.exit("single-choice needs data.options, a non-empty list")
        return title + "".join(
            f"<button style='{btn}' data-v='{esc(o)}' onclick='decide(this.dataset.v)'>{esc(o)}</button>" for o in opts
        )
    if name == "text":
        return title + ("<textarea id='t' rows='4' style='width:100%;font-size:16px'></textarea>"
                        f"<button style='{btn}' onclick=\"decide(document.getElementById('t').value)\">Send</button>")
    sys.exit(f"unknown template {name!r}; use approve-deny, single-choice or text")


def load_form(args: argparse.Namespace) -> str:
    if args.template:
        try:
            data = json.loads(args.data or "{}")
        except ValueError:
            sys.exit("--data must be JSON")
        return template_html(args.template, data)
    if not args.html:
        sys.exit("give --html FILE (or -) or --template NAME")
    return sys.stdin.read() if args.html == "-" else open(args.html, encoding="utf-8").read()


def topic_for(session: str) -> str:
    return f"{os.environ.get('HEYHUMAN_TOPIC_PREFIX', 'heyhuman')}/{session}/response"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ask")
    a.add_argument("--html", help="path to the form HTML, or - for stdin")
    a.add_argument("--template", help="approve-deny, single-choice or text (instead of --html)")
    a.add_argument("--data", help="JSON for the template, e.g. '{\"title\": \"Deploy?\"}'")
    a.add_argument("--message", default="Your agent has a question")
    a.add_argument("--ttl", type=int, default=600, help="seconds the link stays valid (30-3600)")
    a.add_argument("--timeout", type=int, default=600, help="seconds to wait for an answer")
    a.add_argument("--poll", type=float, default=3.0)
    a.add_argument("--no-mqtt", action="store_true")
    a.add_argument("--run", help="record this question in an event stream so a crashed agent can resume")
    st = sub.add_parser("start")
    st.add_argument("--html")
    st.add_argument("--template")
    st.add_argument("--data")
    st.add_argument("--message", default="Your agent has a question")
    st.add_argument("--ttl", type=int, default=600)
    st.add_argument("--run")
    w = sub.add_parser("wait")
    w.add_argument("session")
    w.add_argument("--timeout", type=int, default=600)
    w.add_argument("--poll", type=float, default=3.0)
    w.add_argument("--no-mqtt", action="store_true")
    w.add_argument("--run")
    r = sub.add_parser("resume")
    r.add_argument("--run", required=True)
    r.add_argument("--timeout", type=int, default=600)
    r.add_argument("--poll", type=float, default=3.0)
    r.add_argument("--no-mqtt", action="store_true")
    e = sub.add_parser("events")
    e.add_argument("--run", required=True)
    s = sub.add_parser("status")
    s.add_argument("session")
    sv = sub.add_parser("serve", help="run HeyHuman locally")
    sv.add_argument("--local", action="store_true", required=True)
    args, rest = ap.parse_known_args()

    if args.cmd == "serve":
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "local"))
        from serve import main as serve_main

        serve_main(rest)
        return 0

    if args.cmd == "status":
        print(json.dumps(signed("GET", f"{agent_url()}/sessions/{args.session}"), indent=2))
        return 0
    if args.cmd == "events":
        print(json.dumps(run_events(args.run), indent=2))
        return 0
    if args.cmd == "resume":
        q = open_question(run_events(args.run))
        if q is None:
            print(f"[heyhuman] run {args.run} has no open question", file=sys.stderr)
            return 3
        print(f"[heyhuman] resuming session {q['session']} (link still valid until {q['expires_at']})", file=sys.stderr)
        box: dict[str, Any] = {}
        code = wait(q["session"], q["topic"], args.timeout, args.poll, not args.no_mqtt, box)
        if code == 0:
            run_append(args.run, "AnswerReceived", {"session": q["session"], "decision": box["final"]})
        return code

    if args.cmd == "start":
        created = signed("POST", f"{agent_url()}/sessions", {"html": load_form(args), "message": args.message, "ttl_seconds": args.ttl})
        if args.run:
            run_append(args.run, "QuestionAsked", {"session": created["session"], "topic": created["topic"],
                                                   "expires_at": created["expires_at"], "message": args.message})
        print(json.dumps(created))
        return 0
    if args.cmd == "wait":
        box = {}
        code = wait(args.session, topic_for(args.session), args.timeout, args.poll, not args.no_mqtt, box)
        if code == 0 and args.run:
            run_append(args.run, "AnswerReceived", {"session": args.session, "decision": box["final"]})
        return code

    html = load_form(args)
    created = signed("POST", f"{agent_url()}/sessions", {"html": html, "message": args.message, "ttl_seconds": args.ttl})
    if args.run:
        run_append(args.run, "QuestionAsked", {"session": created["session"], "topic": created["topic"],
                                               "expires_at": created["expires_at"], "message": args.message})
    print(f"[heyhuman] open on your phone: {created['url']}", file=sys.stderr)
    box = {}
    code = wait(created["session"], created["topic"], min(args.timeout, args.ttl + 5), args.poll, not args.no_mqtt, box)
    if code == 0 and args.run:
        run_append(args.run, "AnswerReceived", {"session": created["session"], "decision": box["final"]})
    return code


if __name__ == "__main__":
    sys.exit(main())
