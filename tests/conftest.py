"""Test setup: put the Lambda code on sys.path and fake AWS with moto."""
# File UUID: 5b2f8d40-6a13-4e97-9c38-d1e4a7b06f25
import os
import sys
from pathlib import Path

import boto3
import pytest
from moto import mock_aws

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "lambda"))
sys.path.insert(0, str(ROOT / "infra" / "cdk"))

os.environ.update(
    AWS_DEFAULT_REGION="us-east-1", AWS_ACCESS_KEY_ID="testing", AWS_SECRET_ACCESS_KEY="testing",
    TABLE="heyhuman-test", HUMAN_URL="https://human.example/", TOPIC_PREFIX="heyhuman",
)


class FakePublisher:
    def __init__(self) -> None:
        self.published: list[dict] = []
        self.fail = False

    def publish(self, topic: str, payload: str) -> bool:
        if self.fail:
            return False
        self.published.append({"topic": topic, "payload": payload})
        return True


@pytest.fixture(params=["dynamodb", "sqlite"])
def aws(request, tmp_path, monkeypatch):
    import store
    monkeypatch.setenv("HEYHUMAN_STORE", request.param)
    monkeypatch.setenv("HEYHUMAN_DB", str(tmp_path / "h.db"))
    with mock_aws():
        boto3.client("dynamodb").create_table(
            TableName="heyhuman-test",
            KeySchema=[{"AttributeName": "session_id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "session_id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        boto3.client("dynamodb").create_table(
            TableName="heyhuman-test-events",
            KeySchema=[{"AttributeName": "stream_id", "KeyType": "HASH"}, {"AttributeName": "seq", "KeyType": "RANGE"}],
            AttributeDefinitions=[{"AttributeName": "stream_id", "AttributeType": "S"}, {"AttributeName": "seq", "AttributeType": "N"}],
            BillingMode="PAY_PER_REQUEST",
        )
        store._store = None
        fake = FakePublisher()
        store._publisher = fake
        yield fake
        store._store = None
        store._publisher = None
