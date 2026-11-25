"""Hardened HeyHuman stack.

EXPERIMENTAL CODE. Do not use in production.

Context values (cdk.json or -c):
  ttlTopicPrefix   MQTT topic prefix (default "heyhuman")
  budgetUsd        monthly AWS Budgets limit for an alert (default 5)
  alertEmail       email for the budget alert (optional; no budget alert without it)
"""
# File UUID: 7d3b9e52-1c46-4a8f-b2e7-0f5a6c8d3e91

from __future__ import annotations

from pathlib import Path

from aws_cdk import (
    CfnOutput,
    Duration,
    RemovalPolicy,
    Stack,
    Tags,
    aws_budgets as budgets,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_logs as logs,
)
from constructs import Construct

LAMBDA_DIR = str(Path(__file__).resolve().parents[2] / "lambda")


class HeyHumanStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)
        prefix = str(self.node.try_get_context("topicPrefix") or "heyhuman")
        Tags.of(self).add("project", "heyhuman")
        Tags.of(self).add("experimental", "true")

        table = dynamodb.Table(
            self,
            "Sessions",
            partition_key=dynamodb.Attribute(name="session_id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Append-only event log: session#{id} streams written with each state change, and
        # run#{id} streams the agent writes for itself. Projections can be rebuilt from it.
        events = dynamodb.Table(
            self,
            "Events",
            partition_key=dynamodb.Attribute(name="stream_id", type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(name="seq", type=dynamodb.AttributeType.NUMBER),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            time_to_live_attribute="ttl",
            removal_policy=RemovalPolicy.DESTROY,
        )

        code = lambda_.Code.from_asset(LAMBDA_DIR, exclude=["__pycache__", "*.pyc"])
        env = {"TABLE": table.table_name, "EVENTS_TABLE": events.table_name, "TOPIC_PREFIX": prefix}
        topic_arn = f"arn:aws:iot:{self.region}:{self.account}:topic/{prefix}/*"

        human_fn = lambda_.Function(
            self,
            "HumanFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="human_handler.handler",
            code=code,
            memory_size=256,
            timeout=Duration.seconds(10),
            environment=env,
            log_group=logs.LogGroup(
                self, "HumanLogs", retention=logs.RetentionDays.TWO_WEEKS, removal_policy=RemovalPolicy.DESTROY
            ),
        )
        human_fn.add_to_role_policy(
            iam.PolicyStatement(actions=["dynamodb:GetItem", "dynamodb:UpdateItem", "dynamodb:PutItem"], resources=[table.table_arn])
        )
        human_fn.add_to_role_policy(
            iam.PolicyStatement(actions=["dynamodb:PutItem", "dynamodb:Query"], resources=[events.table_arn])
        )
        human_fn.add_to_role_policy(iam.PolicyStatement(actions=["iot:Publish"], resources=[topic_arn]))
        # Public by design: the human opens the link on any device. Answers need the one-time token.
        human_url = human_fn.add_function_url(auth_type=lambda_.FunctionUrlAuthType.NONE)

        agent_fn = lambda_.Function(
            self,
            "AgentFn",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="agent_handler.handler",
            code=code,
            memory_size=256,
            timeout=Duration.seconds(10),
            environment={**env, "HUMAN_URL": human_url.url},
            log_group=logs.LogGroup(
                self, "AgentLogs", retention=logs.RetentionDays.TWO_WEEKS, removal_policy=RemovalPolicy.DESTROY
            ),
        )
        agent_fn.add_to_role_policy(
            iam.PolicyStatement(actions=["dynamodb:PutItem", "dynamodb:GetItem"], resources=[table.table_arn])
        )
        agent_fn.add_to_role_policy(
            iam.PolicyStatement(actions=["dynamodb:PutItem", "dynamodb:Query"], resources=[events.table_arn])
        )
        # Only callers with SigV4 credentials and the policy below can create questions or read answers.
        agent_url = agent_fn.add_function_url(auth_type=lambda_.FunctionUrlAuthType.AWS_IAM)

        agent_policy = iam.ManagedPolicy(
            self,
            "AgentPolicy",
            description="Attach to the IAM user or role your agent runs as (experimental HeyHuman).",
            statements=[
                iam.PolicyStatement(
                    actions=["lambda:InvokeFunctionUrl"],
                    resources=[agent_fn.function_arn],
                    conditions={"StringEquals": {"lambda:FunctionUrlAuthType": "AWS_IAM"}},
                ),
                iam.PolicyStatement(actions=["iot:DescribeEndpoint"], resources=["*"]),
                iam.PolicyStatement(
                    actions=["iot:Connect"],
                    resources=[f"arn:aws:iot:{self.region}:{self.account}:client/{prefix}-*"],
                ),
                iam.PolicyStatement(
                    actions=["iot:Subscribe"],
                    resources=[f"arn:aws:iot:{self.region}:{self.account}:topicfilter/{prefix}/*"],
                ),
                iam.PolicyStatement(actions=["iot:Receive"], resources=[topic_arn]),
            ],
        )

        budget_usd = float(self.node.try_get_context("budgetUsd") or 5)
        alert_email = self.node.try_get_context("alertEmail")
        if alert_email:
            budgets.CfnBudget(
                self,
                "Budget",
                budget=budgets.CfnBudget.BudgetDataProperty(
                    budget_type="COST",
                    time_unit="MONTHLY",
                    budget_limit=budgets.CfnBudget.SpendProperty(amount=budget_usd, unit="USD"),
                    cost_filters={"TagKeyValue": ["user:project$heyhuman"]},
                ),
                notifications_with_subscribers=[
                    budgets.CfnBudget.NotificationWithSubscribersProperty(
                        notification=budgets.CfnBudget.NotificationProperty(
                            comparison_operator="GREATER_THAN",
                            notification_type="ACTUAL",
                            threshold=80,
                            threshold_type="PERCENTAGE",
                        ),
                        subscribers=[budgets.CfnBudget.SubscriberProperty(address=alert_email, subscription_type="EMAIL")],
                    )
                ],
            )

        CfnOutput(self, "AgentUrl", value=agent_url.url)
        CfnOutput(self, "HumanUrl", value=human_url.url)
        CfnOutput(self, "AgentPolicyArn", value=agent_policy.managed_policy_arn)
        CfnOutput(self, "TopicPrefix", value=prefix)
