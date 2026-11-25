// Vercel AI SDK UI tic-tac-toe: a chat route that answers each move with a UI message stream.
// The board is a custom data part (data-board); the client maps it to its own component.
// No LLM: the "agent" is the shared minimax player. Swap in streamText + a tool to use a model.
// EXPERIMENTAL CODE. Do not use in production.
// File UUID: 2c9f6a41-8b73-4e15-a0d2-5e7b3c8d1f94
import express from "express";
import { createUIMessageStream, pipeUIMessageStreamToResponse, type UIMessage } from "ai";
import { emptyBoard, play, status, type Board } from "../shared/game.ts";

const PORT = Number(process.env.AISDK_PORT ?? 4401);
const app = express();
app.use(express.json({ limit: "256kb" }));

/** The game state lives in the chat history: the last data-board part the agent wrote. */
function lastBoard(messages: UIMessage[]): Board {
  for (const m of [...messages].reverse()) {
    for (const p of [...m.parts].reverse()) {
      if (p.type === "data-board") return (p as { data: { board: Board } }).data.board;
    }
  }
  return emptyBoard();
}

app.post("/api/chat", (req, res) => {
  const messages: UIMessage[] = req.body?.messages ?? [];
  const last = messages.at(-1);
  const text = last?.parts.find((p) => p.type === "text") as { text?: string } | undefined;
  const cell = /^move (\d)$/.exec(text?.text ?? "")?.[1];
  const stream = createUIMessageStream({
    execute: async ({ writer }) => {
      const board = lastBoard(messages);
      if (cell === undefined) {
        writer.write({ type: "text-start", id: "t" });
        writer.write({ type: "text-delta", id: "t", delta: "New game. You are X." });
        writer.write({ type: "text-end", id: "t" });
        writer.write({ type: "data-board", id: "board", data: { board: emptyBoard(), status: "your-move" } });
        return;
      }
      const t = play(board, Number(cell));
      const say = t.error ? `That move is not allowed (${t.error}).` : t.agentCell === null ? `Game over: ${t.status}.` : `I take square ${t.agentCell}.`;
      writer.write({ type: "text-start", id: "t" });
      writer.write({ type: "text-delta", id: "t", delta: say });
      writer.write({ type: "text-end", id: "t" });
      writer.write({ type: "data-board", id: "board", data: { board: t.board, status: t.error ? status(board) : t.status } });
    },
  });
  pipeUIMessageStreamToResponse({ response: res, stream });
});

app.listen(PORT, "127.0.0.1", () => console.log(`AI SDK UI route on http://127.0.0.1:${PORT}/api/chat`));
