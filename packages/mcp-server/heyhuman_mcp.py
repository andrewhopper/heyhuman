# File UUID: 4b1f6e0a-2c7d-4d83-9a15-e6f0b7c3a291
"""HeyHuman MCP server. EXPERIMENTAL CODE. Do not use in production.

Wraps the HeyHuman CLI (cli/heyhuman.py) so an MCP client can ask a human through a one-time link.
Tools:
  heyhuman_start   create the question (agent HTML or a built-in template); returns session and url
  heyhuman_wait    block until the human answers that session
  heyhuman_resume  after a crash, wait on the open question of a run stream

Environment:
  HEYHUMAN_AGENT_URL  the stack's AgentUrl, or http://127.0.0.1:8787 for `heyhuman.py serve --local`
  HEYHUMAN_CMD        command that runs the CLI (default: this repo's cli/heyhuman.py with this Python)
  plus AWS credentials (AWS stack) or HEYHUMAN_AGENT_KEY (local server in Docker)
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import shlex
import sys
from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("heyhuman")
_SESSION_RE = re.compile(r"^[A-Za-z0-9_-]{22}$")
_RUN_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_TEMPLATES = {"approve-deny", "single-choice", "text"}
_TAIL = 4000


def _cmd() -> list[str]:
    raw = os.environ.get("HEYHUMAN_CMD")
    if raw:
        return shlex.split(raw)
    return [sys.executable, "-I", str(Path(__file__).resolve().parents[2] / "cli" / "heyhuman.py")]


async def _run(args: list[str], timeout: float, stdin: str | None = None) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *_cmd(), *args,
        stdin=asyncio.subprocess.PIPE if stdin is not None else None,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    try:
        out, err = await asyncio.wait_for(proc.communicate(stdin.encode() if stdin is not None else None), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return 124, "", "timed out waiting for the CLI"
    return proc.returncode or 0, out.decode(errors="replace"), err.decode(errors="replace")


@mcp.tool()
async def heyhuman_start(
    html: str = "", template: str = "", data: dict[str, Any] | None = None,
    message: str = "Your agent has a question", ttl_seconds: int = 600, run_id: str = "",
) -> dict[str, Any]:
    """Create a question for a human and return at once with a session ID and a one-time link.

    Give either html (the form body; every control must call decide('value')) or a template:
    approve-deny {title, approveLabel, denyLabel}, single-choice {title, options}, text {title}.
    Show the url to the human, then call heyhuman_wait with the session. Pass run_id to record
    the question in a run stream so heyhuman_resume can pick it up after a crash.
    """
    args = ["start", f"--message={message}", f"--ttl={max(30, min(ttl_seconds, 3600))}"]
    if template:
        if template not in _TEMPLATES:
            return {"ok": False, "error": f"template must be one of {sorted(_TEMPLATES)}"}
        args += [f"--template={template}", f"--data={json.dumps(data or {})}"]
        stdin = None
    elif html:
        args.append("--html=-")
        stdin = html
    else:
        return {"ok": False, "error": "give html or template"}
    if run_id:
        if not _RUN_RE.match(run_id):
            return {"ok": False, "error": "run_id: 1-64 letters, digits, - or _"}
        args.append(f"--run={run_id}")
    code, out, err = await _run(args, 60, stdin)
    try:
        created = json.loads(out.strip().splitlines()[-1]) if code == 0 else None
    except (ValueError, IndexError):
        created = None
    if not created:
        return {"ok": False, "exit_code": code, "output": (out + err)[-_TAIL:]}
    return {"ok": True, "session": created["session"], "url": created["url"], "expires_at": created["expires_at"]}


@mcp.tool()
async def heyhuman_wait(session: str, timeout_seconds: int = 300, run_id: str = "") -> dict[str, Any]:
    """Block until the human answers this session. The answer is stored, so a late call still gets it."""
    if not _SESSION_RE.match(session):
        return {"ok": False, "error": "session must be the 22-character id from heyhuman_start"}
    timeout_seconds = max(1, min(timeout_seconds, 3600))
    args = ["wait", session, f"--timeout={timeout_seconds}", "--poll=1"]
    if run_id:
        if not _RUN_RE.match(run_id):
            return {"ok": False, "error": "run_id: 1-64 letters, digits, - or _"}
        args.append(f"--run={run_id}")
    code, out, err = await _run(args, timeout_seconds + 30)
    if code == 0:
        return {"ok": True, "decision": out.strip().splitlines()[-1] if out.strip() else ""}
    return {"ok": False, "exit_code": code, "output": err[-_TAIL:]}


@mcp.tool()
async def heyhuman_resume(run_id: str, timeout_seconds: int = 300) -> dict[str, Any]:
    """After a crash, find the run's open question and wait on the same link (no new link is sent)."""
    if not _RUN_RE.match(run_id):
        return {"ok": False, "error": "run_id: 1-64 letters, digits, - or _"}
    code, out, err = await _run(["resume", f"--run={run_id}", f"--timeout={max(1, min(timeout_seconds, 3600))}", "--poll=1"],
                                timeout_seconds + 30)
    if code == 0:
        return {"ok": True, "decision": out.strip().splitlines()[-1]}
    if code == 3:
        return {"ok": False, "error": "no open question in this run"}
    return {"ok": False, "exit_code": code, "output": err[-_TAIL:]}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
