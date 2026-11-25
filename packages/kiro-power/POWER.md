---
name: "heyhuman"
displayName: "HeyHuman"
description: "Ask a human a question through a one-time link and wait for the answer. The agent writes a small form or uses a template; anyone with the link answers on any device."
keywords: ["ask human", "approval", "human in the loop", "confirm", "rating", "choose", "phone", "approver"]
author: "Andrew Hopper"
---

<!-- File UUID: c8d0e4a6-91f3-4b57-a2e8-5d7f1b3c6094 -->
# HeyHuman (experimental)

Use this power when you need a decision, approval, choice, rating or text answer from a human who may be away from the keyboard, or from a coworker who should approve.

## Onboarding

1. Run a HeyHuman server: deploy the AWS stack (`make deploy` in the heyhuman repo) or run `python3 cli/heyhuman.py serve --local`.
2. Edit `mcp.json`: set `HEYHUMAN_AGENT_URL` and replace `/path/to/heyhuman` with the repo path.
3. Install `uv`. The MCP server runs with `uv run`.

## Tools

- `heyhuman_start(html | template+data, message, ttl_seconds, run_id)`: returns `session` and `url`. Show or send the url.
- `heyhuman_wait(session, timeout_seconds, run_id)`: block until the human answers. Answers are stored, so a late wait still gets them.
- `heyhuman_resume(run_id)`: after a crash, wait on the run's open question without sending a new link.

## Rules

- Every control in your HTML calls `decide('value')`.
- Anyone with the link can answer once. Never put secrets in a form.
- Label buttons for what they submit; the human sees the exact value before sending.

See `steering/forms.md` for form patterns and `steering/games-and-series.md` for multi-step flows.
