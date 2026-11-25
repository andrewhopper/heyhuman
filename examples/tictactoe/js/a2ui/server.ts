// A2UI agent for tic-tac-toe. It sends declarative JSON (A2UI v1.0 messages); the client renders it
// with its own trusted catalog. The board layout is sent once; each move only updates the data model.
// EXPERIMENTAL CODE. Do not use in production.
// File UUID: 6c3a9e17-4d82-4b50-a1f6-8e2d7c5b0f39
import express from "express";
import { randomUUID } from "node:crypto";
import { emptyBoard, play, type Board, type Status } from "../shared/game.ts";

const PORT = Number(process.env.A2UI_PORT ?? 4201);
const CATALOG = "https://a2ui.org/specification/v1_0/catalogs/basic/catalog.json";
const games = new Map<string, Board>();
const label = (c: string) => c || " ";
const statusText = (s: Status) => (s === "your-move" ? "Your move: you are X" : s);

function layout(surfaceId: string) {
  const cell = (i: number) => [
    { id: `cell${i}`, component: "Button", child: `cell${i}label`, action: { event: { name: "move", context: { cell: i } } } },
    { id: `cell${i}label`, component: "Text", text: { "@path": `/board/${i}` } },
  ];
  return {
    version: "1.0",
    updateComponents: {
      surfaceId,
      components: [
        { id: "root", component: "Column", children: ["title", "status", "r0", "r1", "r2"] },
        { id: "title", component: "Text", text: "Tic-tac-toe" },
        { id: "status", component: "Text", text: { "@path": "/status" } },
        ...[0, 1, 2].map((r) => ({ id: `r${r}`, component: "Row", children: [0, 1, 2].map((c) => `cell${r * 3 + c}`) })),
        ...Array.from({ length: 9 }, (_, i) => cell(i)).flat(),
      ],
    },
  };
}

const data = (surfaceId: string, board: Board, s: Status) => ({
  version: "1.0",
  updateDataModel: { surfaceId, path: "/", value: { board: board.map(label), status: statusText(s) } },
});

const app = express();
app.use(express.json({ limit: "16kb" }));

app.post("/api/a2ui/start", (_req, res) => {
  const surfaceId = `ttt-${randomUUID()}`;
  const board = emptyBoard();
  games.set(surfaceId, board);
  res.json([{ version: "1.0", createSurface: { surfaceId, catalogId: CATALOG } }, layout(surfaceId), data(surfaceId, board, "your-move")]);
});

app.post("/api/a2ui/action", (req, res) => {
  const action = req.body?.action;
  const board = games.get(action?.surfaceId);
  if (!board || action?.name !== "move") return res.status(400).json({ error: "unknown game or action" });
  const t = play(board, action.context?.cell);
  if (!t.error) games.set(action.surfaceId, t.board);
  res.json([data(action.surfaceId, t.board, t.status)]);
});

app.listen(PORT, "127.0.0.1", () => console.log(`A2UI agent on http://127.0.0.1:${PORT}`));
