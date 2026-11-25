// MCP App guest: renders the board inside the host's sandbox and calls the server tool on each tap.
// EXPERIMENTAL CODE. Do not use in production.
// File UUID: 8b4f2d61-9e37-4a05-b6c1-2d7e9a3f5c80
import { App } from "@modelcontextprotocol/ext-apps";

type Turn = { board: string[]; status: string; error?: string };
const root = document.getElementById("root")!;
const app = new App({ name: "tic-tac-toe", version: "0.1.0" });
let state: Turn = { board: Array(9).fill(""), status: "your-move" };

function render(t: Turn): void {
  state = t;
  const over = t.status !== "your-move";
  root.innerHTML = `<div class="ttt"><span class="tag">MCP Apps · via MCP UI</span><h2>Tic-tac-toe</h2>
  <p id="status">${over ? t.status : "Your move: you are X"}</p><div class="grid">${t.board
    .map((c, i) => `<button data-cell="${i}" class="${c === "O" ? "o" : ""}" ${c || over ? "disabled" : ""}>${c}</button>`)
    .join("")}</div></div>`;
}

root.addEventListener("click", async (e) => {
  const cell = (e.target as HTMLElement).closest("button")?.dataset.cell;
  if (cell === undefined) return;
  root.querySelectorAll("button").forEach((b) => (b.disabled = true));
  const r = await app.callServerTool({ name: "ttt_move", arguments: { board: state.board, cell: Number(cell) } });
  render(r.structuredContent as Turn);
});

app.ontoolresult = (r) => render(r.structuredContent as Turn);
render(state);
await app.connect();
