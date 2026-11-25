// A2UI client: renders the agent's JSON with the basic catalog and sends button actions back.
// EXPERIMENTAL CODE. Do not use in production.
// File UUID: 9e5b2c84-1f37-4d06-b8a3-4c7e0d9f6a21
import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { MessageProcessor } from "@a2ui/web_core";
import { basicCatalog } from "@a2ui/web_core/catalogs/basic/v1";
import { A2uiSurface } from "@a2ui/react";

async function post(path: string, body: unknown): Promise<unknown[]> {
  const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  return r.json();
}

function App() {
  const [processor] = useState(() => {
    const p: MessageProcessor<any> = new MessageProcessor([basicCatalog], async (action: any) => {
      p.processMessages((await post("/api/a2ui/action", { action })) as any);
    });
    return p;
  });
  const [surfaces, setSurfaces] = useState(() => Array.from(processor.model.surfacesMap.values()));
  useEffect(() => {
    const sync = () => setSurfaces(Array.from(processor.model.surfacesMap.values()));
    const sub = processor.onSurfaceCreated(sync);
    post("/api/a2ui/start", {}).then((m) => processor.processMessages(m as any));
    return () => sub.unsubscribe();
  }, [processor]);
  return (
    <main style={{ font: "16px system-ui", maxWidth: 560, margin: "24px auto" }}>
      <p style={{ color: "#7a7466" }}>Client: React + @a2ui/react, basic catalog · Agent: Node server sending A2UI v1.0 JSON</p>
      <p><b>You:</b> let's play tic-tac-toe</p>
      <div className="ttt-a2ui" style={{ border: "1px solid #d9d3c4", borderRadius: 12, padding: 16, maxWidth: 360 }}>
        {surfaces.map((s) => <A2uiSurface key={s.id} surface={s} />)}
      </div>
    </main>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
