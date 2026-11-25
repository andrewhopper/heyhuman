"""Pluggable storage and answer publishing for HeyHuman.

Every state change is also an event in an append-only stream (EVENTS_TABLE, or an events
table in SQLite). Session records are projections of their stream and can be rebuilt from it.

HEYHUMAN_STORE      dynamodb (default) | sqlite
DYNAMODB_ENDPOINT  optional, e.g. http://dynamodb-local:8000 (DynamoDB Local)
HEYHUMAN_DB         sqlite file path (default ./heyhuman.db)
HEYHUMAN_PUBLISH    iot (default) | mqtt | none
HEYHUMAN_MQTT_URL   mqtt://host:1883 for the mqtt publisher (e.g. Mosquitto)

EXPERIMENTAL CODE. Do not use in production.
"""
# File UUID: 3e7c1a94-6b28-4d50-9f3e-8a2d5c0b7e16

from __future__ import annotations

import json
import os
import sqlite3
import threading
from typing import Any, Protocol
from urllib.parse import urlparse


class Store(Protocol):
    def create(self, item: dict[str, Any]) -> None: ...
    def get(self, session_id: str) -> dict[str, Any] | None: ...
    def answer(self, session_id: str, token_hash: str, decision: str, at: int) -> bool: ...
    def append(self, stream: str, seq: int, kind: str, data: dict[str, Any], at: int) -> bool: ...
    def read(self, stream: str, after: int = 0) -> list[dict[str, Any]]: ...
    def put_projection(self, item: dict[str, Any]) -> None: ...


EVENT_TTL_SECONDS = 7 * 86400


def fold_session(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Rebuild a session record from its event stream."""
    item: dict[str, Any] | None = None
    for e in events:
        if e["type"] == "SessionCreated":
            item = dict(e["data"])
        elif item is not None and e["type"] == "AnswerAccepted":
            item.update(status="answered", decision=e["data"]["decision"], answered_at=e["data"]["answered_at"])
    return item


def session_stream(session_id: str) -> str:
    return f"session#{session_id}"


class Publisher(Protocol):
    def publish(self, topic: str, payload: str) -> bool: ...


class DynamoStore:
    def __init__(self) -> None:
        import boto3
        from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

        kw = {"endpoint_url": os.environ["DYNAMODB_ENDPOINT"]} if os.environ.get("DYNAMODB_ENDPOINT") else {}
        self.client = boto3.client("dynamodb", **kw)
        self.name = os.environ["TABLE"]
        self.events = os.environ.get("EVENTS_TABLE", f"{self.name}-events")
        self.ser, self.de = TypeSerializer(), TypeDeserializer()

    def _m(self, d: dict[str, Any]) -> dict[str, Any]:
        return {k: self.ser.serialize(v) for k, v in d.items() if v is not None}

    def _u(self, d: dict[str, Any]) -> dict[str, Any]:
        from decimal import Decimal

        out = {k: self.de.deserialize(v) for k, v in d.items()}
        return {k: (int(v) if isinstance(v, Decimal) else v) for k, v in out.items()}

    def _event(self, stream: str, seq: int, kind: str, data: dict[str, Any], at: int) -> dict[str, Any]:
        return {"Put": {"TableName": self.events, "ConditionExpression": "attribute_not_exists(seq)",
                        "Item": self._m({"stream_id": stream, "seq": seq, "type": kind, "data": json.dumps(data), "at": at, "ttl": at + EVENT_TTL_SECONDS})}}

    def _cancelled_by_condition(self, err: Exception) -> bool:
        resp = getattr(err, "response", {})
        code = resp.get("Error", {}).get("Code")
        if code == "ConditionalCheckFailedException":
            return True
        reasons = resp.get("CancellationReasons") or []
        return code == "TransactionCanceledException" and any(r.get("Code") == "ConditionalCheckFailed" for r in reasons)

    def create(self, item: dict[str, Any]) -> None:
        self.client.transact_write_items(TransactItems=[
            {"Put": {"TableName": self.name, "Item": self._m(item), "ConditionExpression": "attribute_not_exists(session_id)"}},
            self._event(session_stream(item["session_id"]), 1, "SessionCreated", item, int(item["created_at"])),
        ])

    def get(self, session_id: str) -> dict[str, Any] | None:
        got = self.client.get_item(TableName=self.name, Key={"session_id": {"S": session_id}}).get("Item")
        return self._u(got) if got else None

    def put_projection(self, item: dict[str, Any]) -> None:
        self.client.put_item(TableName=self.name, Item=self._m(item))

    def answer(self, session_id: str, token_hash: str, decision: str, at: int) -> bool:
        from botocore.exceptions import ClientError

        try:
            self.client.transact_write_items(TransactItems=[
                {"Update": {
                    "TableName": self.name, "Key": {"session_id": {"S": session_id}},
                    "UpdateExpression": "SET #s = :answered, decision = :d, answered_at = :t",
                    "ConditionExpression": "token_hash = :h AND #s = :pending AND expires_at > :t",
                    "ExpressionAttributeNames": {"#s": "status"},
                    "ExpressionAttributeValues": self._m({":answered": "answered", ":pending": "pending", ":d": decision, ":t": at, ":h": token_hash}),
                }},
                self._event(session_stream(session_id), 2, "AnswerAccepted", {"decision": decision, "answered_at": at}, at),
            ])
            return True
        except ClientError as err:
            if self._cancelled_by_condition(err):
                return False
            raise

    def append(self, stream: str, seq: int, kind: str, data: dict[str, Any], at: int) -> bool:
        from botocore.exceptions import ClientError

        put = self._event(stream, seq, kind, data, at)["Put"]
        try:
            self.client.put_item(TableName=put["TableName"], Item=put["Item"], ConditionExpression=put["ConditionExpression"])
            return True
        except ClientError as err:
            if self._cancelled_by_condition(err):
                return False
            raise

    def read(self, stream: str, after: int = 0) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        kw: dict[str, Any] = {
            "TableName": self.events, "KeyConditionExpression": "stream_id = :s AND seq > :a",
            "ExpressionAttributeValues": {":s": {"S": stream}, ":a": {"N": str(after)}}, "ConsistentRead": True,
        }
        while True:
            page = self.client.query(**kw)
            for raw in page.get("Items", []):
                e = self._u(raw)
                out.append({"seq": int(e["seq"]), "type": e["type"], "data": json.loads(e["data"]), "at": int(e["at"])})
            if "LastEvaluatedKey" not in page:
                return out
            kw["ExclusiveStartKey"] = page["LastEvaluatedKey"]


class SqliteStore:
    """Single-file store for running HeyHuman as one local process."""

    def __init__(self, path: str | None = None) -> None:
        self.db = sqlite3.connect(path or os.environ.get("HEYHUMAN_DB", "heyhuman.db"), check_same_thread=False)
        self.lock = threading.Lock()
        with self.lock:
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS sessions (session_id TEXT PRIMARY KEY, token_hash TEXT NOT NULL,"
                " status TEXT NOT NULL, expires_at INTEGER NOT NULL, ttl INTEGER NOT NULL, item TEXT NOT NULL,"
                " decision TEXT, answered_at INTEGER)"
            )
            self.db.execute(
                "CREATE TABLE IF NOT EXISTS events (stream_id TEXT NOT NULL, seq INTEGER NOT NULL, type TEXT NOT NULL,"
                " data TEXT NOT NULL, at INTEGER NOT NULL, ttl INTEGER NOT NULL, PRIMARY KEY (stream_id, seq))"
            )
            self.db.commit()

    def create(self, item: dict[str, Any]) -> None:
        rest = {k: v for k, v in item.items() if k not in ("session_id", "token_hash", "status", "expires_at", "ttl")}
        with self.lock:
            self.db.execute("DELETE FROM sessions WHERE ttl < ?", (int(item["created_at"]),))
            self.db.execute("DELETE FROM events WHERE ttl < ?", (int(item["created_at"]),))
            self.db.execute(
                "INSERT INTO sessions (session_id, token_hash, status, expires_at, ttl, item) VALUES (?,?,?,?,?,?)",
                (item["session_id"], item["token_hash"], item["status"], item["expires_at"], item["ttl"], json.dumps(rest)),
            )
            self._insert_event(session_stream(item["session_id"]), 1, "SessionCreated", item, int(item["created_at"]))
            self.db.commit()

    def get(self, session_id: str) -> dict[str, Any] | None:
        with self.lock:
            row = self.db.execute(
                "SELECT session_id, token_hash, status, expires_at, ttl, item, decision, answered_at FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if not row:
            return None
        out = {"session_id": row[0], "token_hash": row[1], "status": row[2], "expires_at": row[3], "ttl": row[4], **json.loads(row[5])}
        if row[6] is not None:
            out.update(decision=row[6], answered_at=row[7])
        return out

    def answer(self, session_id: str, token_hash: str, decision: str, at: int) -> bool:
        with self.lock:
            cur = self.db.execute(
                "UPDATE sessions SET status = 'answered', decision = ?, answered_at = ?"
                " WHERE session_id = ? AND token_hash = ? AND status = 'pending' AND expires_at > ?",
                (decision, at, session_id, token_hash, at),
            )
            if cur.rowcount != 1:
                self.db.rollback()
                return False
            self._insert_event(session_stream(session_id), 2, "AnswerAccepted", {"decision": decision, "answered_at": at}, at)
            self.db.commit()
            return True

    def _insert_event(self, stream: str, seq: int, kind: str, data: dict[str, Any], at: int) -> None:
        self.db.execute("INSERT INTO events (stream_id, seq, type, data, at, ttl) VALUES (?,?,?,?,?,?)",
                        (stream, seq, kind, json.dumps(data), at, at + EVENT_TTL_SECONDS))

    def append(self, stream: str, seq: int, kind: str, data: dict[str, Any], at: int) -> bool:
        with self.lock:
            try:
                self._insert_event(stream, seq, kind, data, at)
                self.db.commit()
                return True
            except sqlite3.IntegrityError:
                self.db.rollback()
                return False

    def read(self, stream: str, after: int = 0) -> list[dict[str, Any]]:
        with self.lock:
            rows = self.db.execute("SELECT seq, type, data, at FROM events WHERE stream_id = ? AND seq > ? ORDER BY seq", (stream, after)).fetchall()
        return [{"seq": r[0], "type": r[1], "data": json.loads(r[2]), "at": r[3]} for r in rows]

    def put_projection(self, item: dict[str, Any]) -> None:
        rest = {k: v for k, v in item.items() if k not in ("session_id", "token_hash", "status", "expires_at", "ttl", "decision", "answered_at")}
        with self.lock:
            self.db.execute(
                "INSERT OR REPLACE INTO sessions (session_id, token_hash, status, expires_at, ttl, item, decision, answered_at) VALUES (?,?,?,?,?,?,?,?)",
                (item["session_id"], item["token_hash"], item["status"], item["expires_at"], item["ttl"], json.dumps(rest), item.get("decision"), item.get("answered_at")),
            )
            self.db.commit()


class IotPublisher:
    def __init__(self) -> None:
        import boto3

        self.client = boto3.client("iot-data")

    def publish(self, topic: str, payload: str) -> bool:
        from botocore.exceptions import ClientError

        try:
            self.client.publish(topic=topic, qos=1, payload=payload)
            return True
        except ClientError:
            return False


class MqttPublisher:
    """Publishes to a plain MQTT broker such as Mosquitto (local/docker use)."""

    def __init__(self, url: str | None = None) -> None:
        u = urlparse(url or os.environ["HEYHUMAN_MQTT_URL"])
        self.host, self.port = u.hostname or "localhost", u.port or 1883

    def publish(self, topic: str, payload: str) -> bool:
        try:
            import paho.mqtt.publish as mqtt_publish

            mqtt_publish.single(topic, payload, qos=1, hostname=self.host, port=self.port)
            return True
        except Exception:  # noqa: BLE001 - the answer is stored; polling still delivers it
            return False


class NullPublisher:
    def publish(self, topic: str, payload: str) -> bool:
        return False


_store: Store | None = None
_publisher: Publisher | None = None


def load_session(session_id: str) -> dict[str, Any] | None:
    """Read the session projection; if it is missing, rebuild it from the event stream."""
    s = store()
    item = s.get(session_id)
    if item is not None:
        return item
    item = fold_session(s.read(session_stream(session_id)))
    if item is not None:
        s.put_projection(item)
    return item


def store() -> Store:
    global _store
    if _store is None:
        _store = SqliteStore() if os.environ.get("HEYHUMAN_STORE") == "sqlite" else DynamoStore()
    return _store


def publisher() -> Publisher:
    global _publisher
    if _publisher is None:
        kind = os.environ.get("HEYHUMAN_PUBLISH", "iot")
        _publisher = {"mqtt": MqttPublisher, "none": NullPublisher}.get(kind, IotPublisher)()
    return _publisher
