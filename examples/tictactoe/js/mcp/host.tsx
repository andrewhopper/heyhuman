// A minimal MCP Apps host: connects to the server, calls the app tool, renders it with MCP UI's AppRenderer.
// EXPERIMENTAL CODE. Do not use in production.
// File UUID: 5d1c8f47-2a93-4e60-b7f5-9a4e3d0c6b18
import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StreamableHTTPClientTransport } from "@modelcontextprotocol/sdk/client/streamableHttp.js";
import { AppRenderer } from "@mcp-ui/client";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";

const SANDBOX = new URL("http://127.0.0.1:4102/sandbox.html");

function Host() {
  const [client, setClient] = useState<Client | null>(null);
  const [result, setResult] = useState<CallToolResult | null>(null);
  useEffect(() => {
    (async () => {
      const c = new Client({ name: "ttt-host", version: "0.1.0" });
      await c.connect(new StreamableHTTPClientTransport(new URL("/api/mcp", location.href)));
      setResult((await c.callTool({ name: "tic_tac_toe", arguments: {} })) as CallToolResult);
      setClient(c);
    })().catch((e) => console.error(e));
  }, []);
  return (
    <main style={{ font: "16px system-ui", maxWidth: 560, margin: "24px auto" }}>
      <p style={{ color: "#7a7466" }}>Host: a minimal React page using @mcp-ui/client · Agent: the MCP server</p>
      <p><b>You:</b> let's play tic-tac-toe</p>
      <p><b>Agent:</b> called <code>tic_tac_toe</code></p>
      <div style={{ height: 460, border: "1px solid #d9d3c4", borderRadius: 12 }}>
        {client && result && (
          <AppRenderer client={client} toolName="tic_tac_toe" sandbox={{ url: SANDBOX }} toolInput={{}} toolResult={result} onError={(e) => console.error(e)} />
        )}
      </div>
    </main>
  );
}
createRoot(document.getElementById("root")!).render(<Host />);
