"""Run HeyHuman as one local process: the same handlers as the Lambdas, behind a stdlib HTTP server.

  python3 local/serve.py                         SQLite, no MQTT, agents poll (simplest)
  python3 local/serve.py --public-url https://box.tailnet.ts.net   links your phone can reach

Agent routes (/sessions...) accept loopback callers, or any caller with
"Authorization: Bearer $HEYHUMAN_AGENT_KEY" when that key is set (needed in Docker, where
the agent is not on loopback). Human routes (/f/...) are open and need the one-time token.

Docker Compose sets HEYHUMAN_STORE=dynamodb with DYNAMODB_ENDPOINT (DynamoDB Local) and
HEYHUMAN_PUBLISH=mqtt with HEYHUMAN_MQTT_URL (Mosquitto); see docker-compose.yml.

EXPERIMENTAL CODE. Do not use in production.
"""
# File UUID: 8b2e6d15-4a93-4c07-b1f8-3d9e7a2c5f40

from __future__ import annotations

import argparse
import hmac
import ipaddress
import os
import socket
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lambda"))
MAX_BODY = 128 * 1024


def lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


def ensure_dynamodb_table() -> None:
    """Create the table on DynamoDB Local when it does not exist yet."""
    import boto3

    client = boto3.client("dynamodb", endpoint_url=os.environ["DYNAMODB_ENDPOINT"])
    name = os.environ["TABLE"]
    events = os.environ.setdefault("EVENTS_TABLE", f"{name}-events")
    have = client.list_tables()["TableNames"]
    specs = {
        name: ([{"AttributeName": "session_id", "KeyType": "HASH"}], [{"AttributeName": "session_id", "AttributeType": "S"}]),
        events: ([{"AttributeName": "stream_id", "KeyType": "HASH"}, {"AttributeName": "seq", "KeyType": "RANGE"}],
                 [{"AttributeName": "stream_id", "AttributeType": "S"}, {"AttributeName": "seq", "AttributeType": "N"}]),
    }
    for table, (keys, attrs) in specs.items():
        if table not in have:
            client.create_table(TableName=table, KeySchema=keys, AttributeDefinitions=attrs, BillingMode="PAY_PER_REQUEST")
            client.get_waiter("table_exists").wait(TableName=table)


def make_handler():
    import agent_handler
    import human_handler

    key = os.environ.get("HEYHUMAN_AGENT_KEY", "")

    class Handler(BaseHTTPRequestHandler):
        server_version = "heyhuman-local"

        def _agent_allowed(self) -> bool:
            if ipaddress.ip_address(self.client_address[0]).is_loopback:
                return True
            got = self.headers.get("Authorization", "")
            return bool(key) and hmac.compare_digest(got, f"Bearer {key}")

        def _go(self, method: str) -> None:
            path = self.path.split("?")[0]
            n = int(self.headers.get("content-length") or 0)
            if n > MAX_BODY:
                self.send_error(413)
                return
            event = {"rawPath": path, "requestContext": {"http": {"method": method}}, "body": self.rfile.read(n).decode() if n else None}
            if path.startswith(("/sessions", "/runs")):
                if not self._agent_allowed():
                    self.send_error(403, "agent routes need loopback or HEYHUMAN_AGENT_KEY")
                    return
                r = agent_handler.handler(event, None)
            else:
                r = human_handler.handler(event, None)
            self.send_response(r["statusCode"])
            for k, v in r.get("headers", {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(r["body"].encode())

        def do_GET(self) -> None:
            self._go("GET")

        def do_POST(self) -> None:
            self._go("POST")

        def log_message(self, fmt: str, *args: object) -> None:
            # Never log query strings or bodies; tokens travel in the fragment and POST body anyway.
            sys.stderr.write(f"[heyhuman] {self.command} {self.path.split('?')[0][:60]}\n")

    return Handler


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Run HeyHuman locally (experimental).")
    ap.add_argument("--host", default=os.environ.get("HEYHUMAN_HOST", "0.0.0.0"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("HEYHUMAN_PORT", "8787")))
    ap.add_argument("--public-url", default=os.environ.get("HUMAN_URL"), help="base URL your phone uses, e.g. a Tailscale or tunnel URL")
    ap.add_argument("--db", default=os.environ.get("HEYHUMAN_DB", "heyhuman.db"))
    a = ap.parse_args(argv)

    os.environ.setdefault("HEYHUMAN_STORE", "sqlite")
    os.environ.setdefault("HEYHUMAN_PUBLISH", "none")
    os.environ.setdefault("TABLE", "heyhuman-local")
    os.environ["HEYHUMAN_DB"] = a.db
    os.environ["HUMAN_URL"] = a.public_url or f"http://{lan_ip()}:{a.port}"
    if os.environ["HEYHUMAN_STORE"] == "dynamodb" and os.environ.get("DYNAMODB_ENDPOINT"):
        ensure_dynamodb_table()

    print(f"[heyhuman] EXPERIMENTAL. Store={os.environ['HEYHUMAN_STORE']} publish={os.environ['HEYHUMAN_PUBLISH']}", file=sys.stderr)
    print(f"[heyhuman] agent API:  http://127.0.0.1:{a.port}  (set HEYHUMAN_AGENT_URL to this)", file=sys.stderr)
    print(f"[heyhuman] phone links: {os.environ['HUMAN_URL']}/f/...", file=sys.stderr)
    if not a.public_url:
        print("[heyhuman] links use your LAN address; use --public-url with Tailscale or a tunnel to reach other networks", file=sys.stderr)
    ThreadingHTTPServer((a.host, a.port), make_handler()).serve_forever()


if __name__ == "__main__":
    main()
