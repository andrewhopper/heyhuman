<!-- File UUID: 6d2b8f40-3a91-4c57-9e16-b0c4a7d2e583 -->
# Deploy with Claude Code

Paste this into Claude Code, run from a checkout of this repo on a machine with your AWS credentials.

```
Deploy the HeyHuman stack from this repo to my AWS account.
1. Read README.md, SECURITY.md and infra/cdk/ first. This is experimental code; use a sandbox or personal account, not a production one.
2. Ask me for the AWS profile, region and the budget-alert email. Show me `aws sts get-caller-identity --profile <p>` output and wait for my OK before changing anything.
3. Run `make install`, then `make bootstrap PROFILE=<p>` only if the account/region is not already CDK-bootstrapped (check for the CDKToolkit stack).
4. Run `cdk diff`, show me the resources it creates (2 Lambda Function URLs, 2 DynamoDB tables, IoT policy, budget, log groups), and wait for my yes.
5. Run `make deploy PROFILE=<p> EMAIL=<email>` and save outputs.json.
6. Smoke test: export HEYHUMAN_AGENT_URL from the AgentUrl output, run `python3 cli/heyhuman.py ask --template approve-deny --data '{"title":"Smoke test"}' --run smoke-1`, give me the link, wait for my answer, then run `python3 cli/heyhuman.py events --run smoke-1` and show the event stream.
7. Report the stack name, both URLs, how to tear it down (`make destroy`), and the expected idle cost.
Do not print any secret values.
```
