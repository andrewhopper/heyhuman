<!-- File UUID: 2e8f4a16-7c93-4b50-a1d7-6f0c9e3b8d42 -->
# Security notes (experimental)

**Experimental code. Do not use in production.**

## What this version fixes, compared with the prototype

| Prototype problem | This version |
|---|---|
| 8-hex session ID was the only credential | 128-bit session ID, plus a 256-bit one-time answer token that travels in the URL fragment and is stored only as a SHA-256 hash |
| Anyone could create a form (`/setup` was public) | Creating questions and reading answers need SigV4 (Function URL with `AWS_IAM` auth) and the stack's managed policy |
| Answer links could be reused | A conditional DynamoDB write accepts one answer per session, only while pending and unexpired |
| Agent HTML ran with full page rights | It is served from its own path with a `sandbox` CSP and `connect-src 'none'`, framed with `sandbox="allow-scripts"`, so it cannot read the token, call the network or answer by itself |
| A form could label a button "Cancel" and send `approved` | The host page shows the exact value in its own confirm bar before anything is sent |
| Listener race: an answer sent before `--wait` subscribed was lost | Answers are stored; the CLI polls stored status as well as listening on MQTT |
| A crashed agent or lost record lost the run | Event-sourced state: records rebuild from their stream; `resume --run` reattaches the agent |
| 180-day form records | Links expire in 10 minutes by default (max 1 hour); records are deleted a day later |
| Wildcard CORS, broad IAM | No CORS; per-action IAM on one table and one topic prefix |

## Known gaps

1. Anyone who holds the link (session ID plus token) can answer. There is no human identity yet; that is the auth-broker work.
2. Any principal with the agent policy can read every session's answers and subscribe to every topic under the prefix.
3. The public Function URL has no WAF or rate limit beyond Lambda's account concurrency. A budget alert is created only when you pass `EMAIL=`.
4. An agent can still write a misleading question. The confirm bar shows the value, not its meaning.
5. Not load-tested, not pen-tested, no failure injection.

## Local mode (`serve --local`, Docker Compose)

1. Links are plain HTTP unless you put the server behind Tailscale or a tunnel that adds TLS. On a shared network, someone sniffing traffic could read the token.
2. Agent routes trust any loopback caller. In Docker the agent is not on loopback, so Compose requires `HEYHUMAN_AGENT_KEY`.
3. Mosquitto allows anonymous clients; Compose publishes it on 127.0.0.1 only.

## Event log

1. `SessionCreated` holds the form HTML and the token hash, the same data as the session record, for 7 days.
2. Run streams hold whatever the agent writes (8 KB per event). Any principal with the agent policy can read every run.
