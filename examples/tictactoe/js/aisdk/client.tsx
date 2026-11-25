// Vercel AI SDK UI frontend: useChat renders message parts; data-board parts become a board component.
// EXPERIMENTAL CODE. Do not use in production.
// File UUID: 8d4a1e67-2f59-4b30-9c86-7a0e5d2b3f18
import { useEffect, useRef } from "react";
import { createRoot } from "react-dom/client";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import "../shared/board.css";

type BoardData = { board: string[]; status: string };

function Board({ data, live, onMove }: { data: BoardData; live: boolean; onMove: (i: number) => void }) {
  const over = data.status !== "your-move";
  return (
    <div className="ttt">
      <span className="tag">Vercel AI SDK UI · useChat</span>
      {live && <p id="status">{over ? data.status : "Your move: you are X"}</p>}
      <div className="grid">
        {data.board.map((c, i) => (
          <button key={i} {...(live ? { "data-cell": i } : {})} className={c === "O" ? "o" : ""} disabled={!live || !!c || over} onClick={() => onMove(i)}>{c}</button>
        ))}
      </div>
    </div>
  );
}

function App() {
  const { messages, sendMessage, status } = useChat({ transport: new DefaultChatTransport({ api: "/api/chat" }) });
  const started = useRef(false);
  useEffect(() => { if (!started.current) { started.current = true; sendMessage({ text: "let's play tic-tac-toe" }); } }, [sendMessage]);
  const lastBoardMsg = [...messages].reverse().find((m) => m.parts.some((p) => p.type === "data-board"));
  const busy = status === "submitted" || status === "streaming";
  return (
    <main style={{ font: "16px system-ui", maxWidth: 560, margin: "24px auto" }}>
      <p style={{ color: "#7a7466" }}>Frontend: React + useChat · Route: createUIMessageStream with a data-board part</p>
      {messages.map((m) => (
        <div key={m.id} style={{ margin: "8px 0" }}>
          {m.parts.map((p, i) =>
            p.type === "text" ? <p key={i} style={{ margin: 0 }}><b>{m.role === "user" ? "You" : "Agent"}:</b> {p.text}</p>
            : p.type === "data-board" && m === lastBoardMsg ? (
              <div key={i} style={{ border: "1px solid #d9d3c4", borderRadius: 12, padding: 16, maxWidth: 360, marginTop: 8 }}>
                <Board data={p.data as BoardData} live={!busy} onMove={(c) => sendMessage({ text: `move ${c}` })} />
              </div>
            ) : null,
          )}
        </div>
      ))}
    </main>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
