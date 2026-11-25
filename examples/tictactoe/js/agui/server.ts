// AG-UI agent for tic-tac-toe. Receives RunAgentInput (state + forwardedProps.cell) and streams
// standard AG-UI events over SSE: RUN_STARTED, STATE_SNAPSHOT (your X), STATE_SNAPSHOT (agent's O), RUN_FINISHED.
// AG-UI carries events; the frontend decides how to draw the board.
// EXPERIMENTAL CODE. Do not use in production.
// File UUID: 7f2d4b96-3e15-4c08-a9b7-1d6e8c2f5a40
import express from "express";
import { EventEncoder } from "@ag-ui/encoder";
import { EventType } from "@ag-ui/core";
import { emptyBoard, play, status } from "../shared/game.ts";

const PORT = Number(process.env.AGUI_PORT ?? 4301);
const app = express();
app.use(express.json({ limit: "64kb" }));
const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

app.post("/api/agui", async (req, res) => {
  const input = req.body ?? {};
  const encoder = new EventEncoder({ accept: req.headers.accept });
  res.setHeader("Content-Type", encoder.getContentType());
  res.setHeader("Cache-Control", "no-store");
  const send = (e: Record<string, unknown>) => res.write(encoder.encode(e as never));
  const { threadId, runId } = input;
  send({ type: EventType.RUN_STARTED, threadId, runId });

  const board = Array.isArray(input.state?.board) ? input.state.board : emptyBoard();
  const cell = input.forwardedProps?.cell;
  if (cell === undefined) {
    send({ type: EventType.STATE_SNAPSHOT, snapshot: { board, status: status(board) } });
  } else {
    const t = play(board, cell);
    if (t.error) {
      send({ type: EventType.STATE_SNAPSHOT, snapshot: { board, status: status(board), error: t.error } });
    } else {
      const mine = [...t.board];
      if (t.agentCell !== null) mine[t.agentCell] = "";
      send({ type: EventType.STATE_SNAPSHOT, snapshot: { board: mine, status: "your-move", thinking: t.agentCell !== null } });
      await sleep(150); // the agent "thinks"; the UI already shows the human's X
      send({ type: EventType.STATE_SNAPSHOT, snapshot: { board: t.board, status: t.status } });
    }
  }
  send({ type: EventType.RUN_FINISHED, threadId, runId });
  res.end();
});

app.listen(PORT, "127.0.0.1", () => console.log(`AG-UI agent on http://127.0.0.1:${PORT}/api/agui`));
