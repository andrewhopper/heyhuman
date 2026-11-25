// AG-UI frontend: plain TypeScript with @ag-ui/client's HttpAgent. Renders the board from STATE_SNAPSHOT events.
// EXPERIMENTAL CODE. Do not use in production.
// File UUID: 0a8c5e23-6b41-4f97-8d2e-3c9f7b1a4e56
import { HttpAgent } from "@ag-ui/client";
import "../shared/board.css";

type State = { board: string[]; status: string; thinking?: boolean };
const root = document.getElementById("root")!;
const log = document.getElementById("events")!;
const agent = new HttpAgent({ url: "/api/agui" });
let state: State = { board: Array(9).fill(""), status: "your-move" };

function render(s: State): void {
  state = s;
  const over = s.status !== "your-move";
  root.innerHTML = `<div class="ttt"><span class="tag">AG-UI · @ag-ui/client</span><h2>Tic-tac-toe</h2>
  <p id="status">${over ? s.status : s.thinking ? "Agent is thinking…" : "Your move: you are X"}</p><div class="grid">${s.board
    .map((c, i) => `<button data-cell="${i}" class="${c === "O" ? "o" : ""}" ${c || over || s.thinking ? "disabled" : ""}>${c}</button>`)
    .join("")}</div></div>`;
}

agent.subscribe({
  onEvent: ({ event }) => { log.textContent = `${event.type}\n` + log.textContent!.split("\n").slice(0, 7).join("\n"); },
  onStateSnapshotEvent: ({ event }) => render(event.snapshot as State),
});

root.addEventListener("click", async (e) => {
  const cell = (e.target as HTMLElement).closest("button")?.dataset.cell;
  if (cell === undefined || state.thinking) return;
  agent.setState({ board: state.board });
  await agent.runAgent({ forwardedProps: { cell: Number(cell) } });
});

render(state);
await agent.runAgent({});
