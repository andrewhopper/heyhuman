// Tic-tac-toe rules and a perfect (minimax) agent opponent, shared by every stack.
// EXPERIMENTAL CODE. Do not use in production.
// File UUID: 3c7e1a92-5d48-4f06-b2a9-8e1d6c4f0b37
export type Cell = "" | "X" | "O";
export type Board = Cell[];
export type Status = "your-move" | "X wins" | "O wins" | "draw";
export interface Turn { board: Board; status: Status; agentCell: number | null; error?: string }

const LINES = [[0, 1, 2], [3, 4, 5], [6, 7, 8], [0, 3, 6], [1, 4, 7], [2, 5, 8], [0, 4, 8], [2, 4, 6]];
export const emptyBoard = (): Board => Array(9).fill("") as Board;

export function status(b: Board): Status {
  for (const [a, c, d] of LINES) if (b[a] && b[a] === b[c] && b[a] === b[d]) return `${b[a]} wins` as Status;
  return b.every(Boolean) ? "draw" : "your-move";
}

function score(b: Board, turn: "X" | "O", depth: number): number {
  const s = status(b);
  if (s === "O wins") return 10 - depth;
  if (s === "X wins") return depth - 10;
  if (s === "draw") return 0;
  const scores = b.flatMap((c, i) => (c ? [] : [(() => { const n = [...b]; n[i] = turn; return score(n, turn === "O" ? "X" : "O", depth + 1); })()]));
  return turn === "O" ? Math.max(...scores) : Math.min(...scores);
}

export function agentMove(b: Board): number {
  let best = -1, bestScore = -Infinity;
  b.forEach((c, i) => {
    if (c) return;
    const n = [...b]; n[i] = "O";
    const s = score(n, "X", 1);
    if (s > bestScore) { bestScore = s; best = i; }
  });
  return best;
}

/** Validate the human's move (X), then let the agent answer (O). */
export function play(board: unknown, cell: unknown): Turn {
  const b = Array.isArray(board) && board.length === 9 && board.every((c) => c === "" || c === "X" || c === "O") ? (board as Board) : null;
  if (!b) return { board: emptyBoard(), status: "your-move", agentCell: null, error: "bad board" };
  const i = Number(cell);
  if (!Number.isInteger(i) || i < 0 || i > 8 || b[i] || status(b) !== "your-move") return { board: b, status: status(b), agentCell: null, error: "illegal move" };
  const n = [...b]; n[i] = "X";
  if (status(n) !== "your-move") return { board: n, status: status(n), agentCell: null };
  const a = agentMove(n); n[a] = "O";
  return { board: n, status: status(n), agentCell: a };
}
