"""Synth the CDK stack and check its security-relevant settings."""
# File UUID: 0c7d4b19-2e85-4a6f-b3c1-9f8e5d2a7b64
import aws_cdk as cdk
from aws_cdk.assertions import Match, Template

from stack import HeyHumanStack


def synth(**ctx: object) -> Template:
    app = cdk.App(context=ctx)
    return Template.from_stack(HeyHumanStack(app, "T", env=cdk.Environment(account="111111111111", region="us-east-1")))


def test_function_urls_iam_for_agent_none_for_human_and_no_cors():
    t = synth()
    urls = t.find_resources("AWS::Lambda::Url")
    assert sorted(u["Properties"]["AuthType"] for u in urls.values()) == ["AWS_IAM", "NONE"]
    assert all("Cors" not in u["Properties"] for u in urls.values())


def test_two_tables_events_keyed_by_stream_and_seq():
    t = synth()
    t.resource_count_is("AWS::DynamoDB::Table", 2)
    t.has_resource_properties("AWS::DynamoDB::Table", {"KeySchema": [{"AttributeName": "stream_id", "KeyType": "HASH"}, {"AttributeName": "seq", "KeyType": "RANGE"}]})


def test_table_ttl_and_encryption():
    synth().has_resource_properties(
        "AWS::DynamoDB::Table",
        {"TimeToLiveSpecification": {"AttributeName": "ttl", "Enabled": True}, "SSESpecification": {"SSEEnabled": True}},
    )


def test_no_wildcard_dynamodb_or_iot_publish():
    policies = synth().find_resources("AWS::IAM::Policy")
    for p in policies.values():
        for st in p["Properties"]["PolicyDocument"]["Statement"]:
            actions = st["Action"] if isinstance(st["Action"], list) else [st["Action"]]
            assert not any(a.endswith(":*") for a in actions)
            if any(a.startswith("iot:Publish") for a in actions):
                assert "topic/heyhuman/*" in str(st["Resource"])


def test_budget_only_with_email():
    synth().resource_count_is("AWS::Budgets::Budget", 0)
    synth(alertEmail="me@example.com").resource_count_is("AWS::Budgets::Budget", 1)


def test_log_retention_two_weeks():
    synth().all_resources_properties("AWS::Logs::LogGroup", {"RetentionInDays": 14})
