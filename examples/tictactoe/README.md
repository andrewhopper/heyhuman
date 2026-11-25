<!-- File UUID: 6e3b9d27-4c81-4f50-a2d6-8b1e7c0f5a93 -->
# Tic-tac-toe on five generative-UI stacks

> **Experimental code. Do not use in production.** These are test apps for a blog comparison.

The same game runs on HeyHuman, MCP Apps (via MCP UI), A2UI, AG-UI and the Vercel AI SDK UI. Every
stack plays against the same agent, a perfect minimax player (`js/shared/game.ts`), so no LLM or
API key is needed. Each test opens real Chrome, plays X until the game ends, checks the board after
every move, and saves screenshots and timings in `results/`.

![Five boards after two moves each](results/tictactoe-five-stacks-9b41e7-v1.png)

## Results (2026-11-25, all processes on one machine)

| Stack | What the agent sends | Where it renders | Local IPC or remote | Our code (lines) | What you must run | Avg move round trip |
|---|---|---|---|---|---|---|
| HeyHuman (hardened) | An HTML form, one per turn | Any browser, from a link | Remote: agent and human meet only through the AWS stack | 10 (form + API call) | The AWS stack (here: its handlers locally, DynamoDB faked with moto) | 0.21 s, including the confirm tap |
| MCP Apps via MCP UI | A `ui://` HTML app once, then tool calls | A sandboxed iframe in an MCP host | The app talks to the host over in-browser `postMessage`; host to server over Streamable HTTP (or stdio for a local server) | 109, plus an 87-line sandbox proxy copied from the ext-apps reference host | An MCP server, a host with MCP Apps support, and a sandbox proxy on a second origin | 0.24 s |
| A2UI v1.0 | Component JSON once, then data-model updates | The client app's own renderer and catalog | Transport-agnostic; here plain HTTP | 82 | An agent and a client app with an A2UI renderer | 0.14 s |
| AG-UI | `STATE_SNAPSHOT` events over SSE | A frontend you write | Remote: HTTP and SSE | 63 | An agent server and a frontend | 0.26 s |
| Vercel AI SDK UI | A `data-board` part in a UI message stream | Your React app via `useChat` | Remote: HTTP streaming | 86 | A chat route and a React app | 0.10 s |

All five finished the scripted game the same way (human plays 4, 1, 2, 3; O wins), which
confirms each stack carried every move both ways. Latencies are local and include the
browser re-render; they say nothing about real networks. The AG-UI agent waits 150 ms on
purpose so its two-step stream (your X, then the agent's O) is visible.

Things the tests surfaced:

1. **A2UI's catalog is enforced.** The v1.0 basic catalog rejected `variant: "h3"` on `Text`
   (only `caption` and `body` are allowed) and rejected component ids with hyphens.
2. **MCP Apps needs a second origin.** The host must load the app through a sandbox proxy on a
   different origin before any HTML runs.
3. **HeyHuman opens one link per turn.** The hardened stack accepts one answer per session, so a
   five-move game is five links. The others keep one surface open.
4. **Package versions must match.** `@mcp-ui/client` 7 uses ext-apps 1 with MCP SDK 1; ext-apps 2
   needs the split v2 SDK packages.

## Run

```bash
cd js && npm install --legacy-peer-deps && npm test   # builds the MCP bundles, plays all five
```

Needs Node 20+, Python 3.12+ with `playwright`, `boto3` and `moto`, and Chrome at
`/usr/bin/google-chrome`. The HeyHuman test uses `../../hardened` (override with `HEYHUMAN_HARDENED`).
Ports: 5180 (Vite), 4101–4102 (MCP), 4201 (A2UI), 4301 (AG-UI), 4401 (AI SDK), 8790 (HeyHuman).
