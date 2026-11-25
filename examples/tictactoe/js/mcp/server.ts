// MCP server for the MCP Apps tic-tac-toe. Streamable HTTP on /mcp; the board UI is a ui:// resource.
// Also serves the sandbox proxy on a second origin (127.0.0.1), as MCP Apps hosts require.
// EXPERIMENTAL CODE. Do not use in production.
// File UUID: 2e9a5c38-7f14-4b62-a0d8-6c3b1e7f9d42
import express from "express";
import fs from "node:fs";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { registerAppResource, registerAppTool, RESOURCE_MIME_TYPE } from "@modelcontextprotocol/ext-apps/server";
import { z } from "zod";
import { emptyBoard, play, status } from "../shared/game.ts";

const PORT = Number(process.env.MCP_PORT ?? 4101);
const SANDBOX_PORT = Number(process.env.SANDBOX_PORT ?? 4102);
const URI = "ui://tic-tac-toe/board.html";
const css = fs.readFileSync(new URL("../shared/board.css", import.meta.url), "utf8");
const guestJs = () => fs.readFileSync(new URL("../dist/mcp-guest.js", import.meta.url), "utf8");
const boardSchema = z.array(z.enum(["", "X", "O"])).length(9);

function build(): McpServer {
  const server = new McpServer({ name: "tic-tac-toe", version: "0.1.0" });
  registerAppTool(server, "tic_tac_toe", {
    description: "Start a game of tic-tac-toe with the user. Shows an interactive board.",
    inputSchema: {},
    _meta: { ui: { resourceUri: URI } },
  }, async () => {
    const board = emptyBoard();
    return { content: [{ type: "text", text: "New game. The user plays X." }], structuredContent: { board, status: status(board) } };
  });
  server.registerTool("ttt_move", {
    description: "Apply the user's move (X) and reply with the agent's move (O).",
    inputSchema: { board: boardSchema, cell: z.number().int().min(0).max(8) },
  }, async ({ board, cell }) => {
    const t = play(board, cell);
    return { content: [{ type: "text", text: `${t.status}; agent played ${t.agentCell}` }], structuredContent: t as unknown as Record<string, unknown> };
  });
  registerAppResource(server, "Tic-tac-toe board", URI, { mimeType: RESOURCE_MIME_TYPE }, async () => ({
    contents: [{
      uri: URI, mimeType: RESOURCE_MIME_TYPE,
      text: `<!doctype html><html><head><meta charset="utf-8"><style>${css}body{margin:12px}</style></head><body><div id="root"></div><script type="module">${guestJs()}</script></body></html>`,
    }],
  }));
  return server;
}

const app = express();
app.use(express.json());
app.post("/api/mcp", async (req, res) => {
  const server = build();
  const transport = new StreamableHTTPServerTransport({ sessionIdGenerator: undefined }); // stateless
  res.on("close", () => { transport.close(); server.close(); });
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});
app.listen(PORT, "127.0.0.1", () => console.log(`MCP server on http://127.0.0.1:${PORT}/api/mcp`));

const sandbox = express();
sandbox.get("/sandbox.html", (_req, res) => {
  res.type("html").send(`<!doctype html><html><head><meta charset="utf-8"><style>html,body{margin:0;height:100vh}body{display:flex;flex-direction:column}iframe{flex-grow:1;border:0}</style></head><body><script type="module" src="/sandbox.js"></script></body></html>`);
});
sandbox.get("/sandbox.js", (_req, res) => res.type("js").send(fs.readFileSync(new URL("../dist/mcp-sandbox.js", import.meta.url), "utf8")));
sandbox.listen(SANDBOX_PORT, "127.0.0.1", () => console.log(`Sandbox proxy on http://127.0.0.1:${SANDBOX_PORT}/sandbox.html`));
