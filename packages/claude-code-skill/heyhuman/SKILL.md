---
name: heyhuman
description: Ask a human a question through a one-time link and wait for the answer. Use when you need a decision, approval, choice, rating or free-text answer and the human may be away from the terminal, or when someone else (a coworker) should approve.
---

<!-- File UUID: 7e2a9c15-3b08-4f6d-8d41-a0c5e9b2d713 -->
# HeyHuman (experimental)

You write a small form (or pick a built-in template), HeyHuman returns a one-time link, any person with the link answers on any device, and the answer comes back to you as a string.

## Prerequisites

- A HeyHuman server: the AWS stack (`make deploy`) or a local one (`python3 cli/heyhuman.py serve --local`).
- `HEYHUMAN_CLI`: path to `cli/heyhuman.py` in the heyhuman repo.
- `HEYHUMAN_AGENT_URL`: the stack's `AgentUrl` output, or `http://127.0.0.1:8787` for a local server.
- If the `heyhuman_*` MCP tools are available, use them instead of the shell commands. They take the same inputs.

## Flow

1. Write the form body as HTML. Every control calls `decide('value')`. Or use a template (below).
2. Start: `python3 "$HEYHUMAN_CLI" start --html form.html --message "Deploy v2.1?" --run <run-id>`. It prints JSON with `session` and `url`.
3. Show the `url` to the human in your reply, or send it to the person who should approve.
4. Wait: `python3 "$HEYHUMAN_CLI" wait <session> --run <run-id>`. It prints the answer and exits 0; exit 2 means expired or timed out.

Answers are stored, so waiting late is fine. If your process dies, `python3 "$HEYHUMAN_CLI" resume --run <run-id>` waits on the same open question; the human does not get a second link.

One-step alternative: `python3 "$HEYHUMAN_CLI" ask --html form.html` prints the link on stderr and blocks until the answer.

## Templates

`--template approve-deny --data '{"title":"Deploy?","approveLabel":"Deploy","denyLabel":"Cancel"}'`
`--template single-choice --data '{"title":"Pick a layout","options":["A","B","C"]}'`
`--template text --data '{"title":"Anything to add?"}'`

## Form rules

- Mobile first: tap targets at least 56px tall, one column.
- Submit one value. For several fields, build a JSON string and pass it to `decide()`.
- The form runs in a sandbox with no network access; fetch calls are blocked.
- The human sees the exact value in a confirm bar before it is sent. Label buttons for what they submit.
- Test your form's JavaScript. A rating form once returned 4 for every item because of a state bug.

## Limits

- Anyone holding the link can answer, once. Do not put secrets in a form.
- Links expire after 10 minutes by default (`--ttl`, max 3600 seconds).
