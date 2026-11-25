<!-- File UUID: 1c7e3a95-4b28-4d60-9f13-8a2e5d7b0c46 -->
# HeyHuman packages (experimental)

Three ways for an agent to use the same CLI (`cli/heyhuman.py`):

| Package | For | How |
|---|---|---|
| `mcp-server/` | Any MCP client | `heyhuman_start`, `heyhuman_wait`, `heyhuman_resume` tools; tested against a real local server |
| `claude-code-skill/heyhuman/` | Claude Code | Copy into `.claude/skills/`; uses the MCP tools when present, the CLI otherwise |
| `kiro-power/` | Kiro | `POWER.md`, `mcp.json` and steering files |
