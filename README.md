<!-- File UUID: 5c1d9e48-2a76-4f3b-90e8-d7b6a4c2f135 -->
# HeyHuman (experimental)

> **Experimental code. Do not use in production.** See [SECURITY.md](SECURITY.md) for what is fixed and what is not.

An agent writes a small form (or picks a template), gets a one-time link, and waits. Anyone
holding the link answers on any device: you on your phone, or a coworker you make the approver.
The answer comes back to the agent as a string.

It works from any agent harness that can run a shell command, with no host app to configure.
On AWS, Lambda and IoT Core cost nothing while idle, so the stack sleeps until an agent asks a
question. It also runs as one local Python process, or under Docker Compose.

| Folder | What |
|---|---|
| `lambda/` `infra/cdk/` | The AWS stack (CDK) |
| `cli/heyhuman.py` | Agent CLI: `ask`, `start`, `wait`, `resume`, `events`, `serve --local` |
| `local/` `docker-compose.yml` | Run without AWS |
| `packages/` | MCP server, Claude Code skill, Kiro power |
| `examples/tictactoe/` | The same game on HeyHuman, MCP Apps, A2UI, AG-UI and Vercel AI SDK UI, with Playwright tests |
| `tests/` | Handler tests (DynamoDB and SQLite), stack checks, browser check |

Background: the blog series [AI Partnership: how humans and AI can work better together](https://blog.andrewhopper.com/blog/exploring-generative-ui-human-agent-collaboration).

```
agent ──SigV4──► AgentUrl  POST /sessions  → link with one-time token (in the #fragment)
                           GET  /sessions/{id} → status, for polling
you  ──link──►   HumanUrl  GET  /f/{id}          host page, strict CSP
                           GET  /f/{id}/content  agent HTML, sandboxed, no network
                           POST /f/{id}/answer   one-time, then published to IoT Core
```

## One-click deploy (CloudFormation)

No CDK, Node or Python needed: the button opens the CloudFormation console with the template filled in.

[![Launch Stack](https://s3.amazonaws.com/cloudformation-examples/cloudformation-launch-stack.png)](https://console.aws.amazon.com/cloudformation/home?region=us-east-1#/stacks/quickcreate?templateURL=https://HEYHUMAN_RELEASE_BUCKET.s3.us-east-1.amazonaws.com/heyhuman/latest/heyhuman.template.json&stackName=heyhuman)

1. Click the button (region us-east-1), optionally enter an email for the budget alert, tick the IAM acknowledgement and create the stack.
2. From the stack's Outputs, copy `AgentUrl` and attach `AgentPolicyArn` to the IAM user or role your agent runs as.
3. `export HEYHUMAN_AGENT_URL=<AgentUrl>` and run `python3 cli/heyhuman.py ask --template approve-deny --data '{"title":"Hello"}'`.

Maintainers publish the template and Lambda zip with `make publish-oneclick BUCKET=<public-read bucket> PROFILE=<p>`
(once per region; the Lambda code must sit in a bucket in the stack's region). `make synth-oneclick` builds the template without uploading.

## Deploy (CDK)

Or hand it to Claude Code with [this prompt](docs/deploy-with-claude-code.md).

Needs Python 3.12+, Node 20+ (for the CDK CLI) and AWS credentials for an account you own.

```bash
make install
make bootstrap PROFILE=my-profile            # once per account and region
make deploy PROFILE=my-profile EMAIL=me@example.com
make outputs
```

Attach the `AgentPolicyArn` output to the IAM user or role your agent runs as.

## Use

```bash
export HEYHUMAN_AGENT_URL=<AgentUrl output>
python3 cli/heyhuman.py ask --html form.html --message "Deploy to prod?"
```

The CLI prints the link on stderr, waits, and prints the answer on stdout. In the form, call
`decide('value')` from any button. `make smoke` sends a tic-tac-toe board as a test.

## Event-sourced state

Every change is appended to an event table (`stream_id`, `seq`), in the same transaction as
the session record it changes:

| Stream | Events |
|---|---|
| `session#{id}` | `SessionCreated`, `AnswerAccepted`, `AnswerPublished` |
| `run#{id}` | Whatever the agent records; the CLI writes `QuestionAsked` and `AnswerReceived` |

If a session record is lost, the next read rebuilds it from its stream. If the agent dies
while waiting, `heyhuman.py resume --run <id>` finds the open question and waits on the same
link; the human never sees a second one. Appends are optimistic: a `seq` that is already
taken returns 409 with the last `seq`. Events expire after 7 days.

```bash
python3 cli/heyhuman.py ask --run deploy-42 --html form.html --message "Ship it?"
# ...agent crashes, human answers anyway...
python3 cli/heyhuman.py resume --run deploy-42     # prints the answer
python3 cli/heyhuman.py events --run deploy-42
```

## Run it locally instead of on AWS

**One Python process (SQLite, no broker; the CLI polls):**

```bash
python3 cli/heyhuman.py serve --local                      # links use your LAN address
python3 cli/heyhuman.py serve --local --public-url https://box.your-tailnet.ts.net
export HEYHUMAN_AGENT_URL=http://127.0.0.1:8787
python3 cli/heyhuman.py ask --html form.html --message "Deploy?"
```

**Docker Compose (DynamoDB Local + Mosquitto + HeyHuman):**

```bash
export HEYHUMAN_AGENT_KEY=$(openssl rand -hex 24)
docker compose up --build
export HEYHUMAN_AGENT_URL=http://127.0.0.1:8787 HEYHUMAN_MQTT_URL=mqtt://127.0.0.1:1883
python3 cli/heyhuman.py ask --html form.html --message "Deploy?"
```

Agent routes accept loopback callers, or a bearer `HEYHUMAN_AGENT_KEY`. Human routes still need
the one-time token. Running locally trades the AWS dependency for one on your machine: it must
stay on, and a phone on another network needs Tailscale or a tunnel to reach it.

Tested here: the single-process mode end to end with the CLI, and the Compose configuration's
code path with stand-ins (moto server for DynamoDB Local, amqtt for Mosquitto). The Compose
file itself has not been run, because this environment has no Docker daemon.

## Test

`make test` runs the handler tests against both DynamoDB (moto) and SQLite, the event-stream
and rehydration tests, and checks the synthesized stack. For the browser
check, `python3 -I tests/browser/run_browser_check.py <out-dir>` drives a real Chrome through
the host page, the sandboxed form and the confirm bar against a local server.

## Remove

`make destroy PROFILE=my-profile`. The table is deleted with the stack.
