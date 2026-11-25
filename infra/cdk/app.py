#!/usr/bin/env python3
"""CDK app for the hardened HeyHuman stack. EXPERIMENTAL CODE. Do not use in production."""
# File UUID: 1e6c3a84-9b27-4d5f-8a10-c4e7b2f9d036
import os

import aws_cdk as cdk

from stack import HeyHumanStack

app = cdk.App()
if str(app.node.try_get_context("oneclick") or "").lower() == "true":
    # Portable template for the one-click Launch Stack button: no bootstrap, no account/region.
    HeyHumanStack(app, "HeyHumanExperimental", synthesizer=cdk.BootstraplessSynthesizer())
else:
    HeyHumanStack(
        app,
        "HeyHumanExperimental",
        env=cdk.Environment(account=os.environ.get("CDK_DEFAULT_ACCOUNT"), region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1")),
    )
app.synth()
