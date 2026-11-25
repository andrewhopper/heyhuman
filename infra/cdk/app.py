#!/usr/bin/env python3
"""CDK app for the hardened HeyHuman stack. EXPERIMENTAL CODE. Do not use in production."""
# File UUID: 1e6c3a84-9b27-4d5f-8a10-c4e7b2f9d036
import os

import aws_cdk as cdk

from stack import HeyHumanStack

app = cdk.App()
HeyHumanStack(
    app,
    "HeyHumanExperimental",
    env=cdk.Environment(account=os.environ.get("CDK_DEFAULT_ACCOUNT"), region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1")),
)
app.synth()
