"""Play a full game of tic-tac-toe as the human on one stack, in real Chrome.

python3 -I tests/play.py <stack> [out_dir]
Starts the stack's processes, plays X (center first, then the first open square),
checks the board after every move, saves start/mid/end screenshots, and stops everything.
EXPERIMENTAL CODE. Do not use in production.
"""
# File UUID: 4b9e2c73-1d58-4a06-8f3b-e6c0a7d2b519
import asyncio, json, os, signal, socket, subprocess, sys, time
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
JS = ROOT / "js"
FINAL = ("draw", "O wins", "X wins")
STACKS = {
    "mcp": {"procs": [["npx", "tsx", "mcp/server.ts"]], "ports": [4101, 4102], "url": "http://localhost:5180/mcp.html", "frames": ["iframe", "iframe"], "cells": "[data-cell]", "status": "#status"},
    "a2ui": {"procs": [["npx", "tsx", "a2ui/server.ts"]], "ports": [4201], "url": "http://localhost:5180/a2ui.html", "frames": [], "cells": ".ttt-a2ui a2ui-basic-row button", "status": ".ttt-a2ui a2ui-basic-column > a2ui-basic-text:nth-of-type(2)"},
    "agui": {"procs": [["npx", "tsx", "agui/server.ts"]], "ports": [4301], "url": "http://localhost:5180/agui.html", "frames": [], "cells": "[data-cell]", "status": "#status"},
    "aisdk": {"procs": [["npx", "tsx", "aisdk/server.ts"]], "ports": [4401], "url": "http://localhost:5180/aisdk.html", "frames": [], "cells": "[data-cell]", "status": "#status"},
}


def wait_port(port: int, timeout: float = 60) -> None:
    end = time.time() + timeout
    while time.time() < end:
        try:
            socket.create_connection(("127.0.0.1", port), 1).close(); return
        except OSError:
            time.sleep(0.5)
    raise RuntimeError(f"port {port} never opened")


async def play(cfg: dict, out: Path, name: str) -> dict:
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 760, "height": 760}, device_scale_factor=2)
        errors: list[str] = []
        pg.on("console", lambda m: errors.append(m.text[:160]) if m.type == "error" else None)
        t0 = time.time()
        await pg.goto(cfg["url"], wait_until="domcontentloaded", timeout=120000)
        scope = pg
        for f in cfg["frames"]:
            scope = scope.frame_locator(f)
        cells = scope.locator(cfg["cells"])
        await cells.first.wait_for(timeout=60000)
        first_paint = time.time() - t0
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=str(out / f"{name}-start.png"))
        moves, latencies = [], []
        for turn in range(5):
            texts = [((await cells.nth(i).inner_text()) or "").strip() for i in range(9)]
            open_cells = [i for i, t in enumerate(texts) if not t and await cells.nth(i).is_enabled()]
            if not open_cells:
                break
            pick = 4 if 4 in open_cells else open_cells[0]
            before = texts.count("O")
            t1 = time.time()
            await cells.nth(pick).click()
            moves.append(pick)
            # wait for our X to land and either the agent's O or the game to end
            for _ in range(200):
                now = [((await cells.nth(i).inner_text()) or "").strip() for i in range(9)]
                st = (await scope.locator(cfg["status"]).inner_text()).strip()
                if now[pick] == "X" and (now.count("O") > before or st in FINAL):
                    break
                await pg.wait_for_timeout(100)
            latencies.append(round(time.time() - t1, 2))
            if turn == 1:
                await pg.screenshot(path=str(out / f"{name}-mid.png"))
            if st in FINAL:
                break
        final = [((await cells.nth(i).inner_text()) or "").strip() for i in range(9)]
        st = (await scope.locator(cfg["status"]).inner_text()).strip()
        await pg.wait_for_timeout(300)
        await pg.screenshot(path=str(out / f"{name}-end.png"))
        await b.close()
    assert st in ("draw", "O wins", "X wins"), f"game did not finish: {st} {final}"
    assert final.count("X") == len(moves) and abs(final.count("X") - final.count("O")) <= 1, final
    return {"stack": name, "result": st, "moves": moves, "board": final, "first_paint_s": round(first_paint, 2),
            "move_latency_s": latencies, "console_errors": errors}


def main() -> None:
    name = sys.argv[1]; out = Path(sys.argv[2] if len(sys.argv) > 2 else ROOT / "shots"); out.mkdir(parents=True, exist_ok=True)
    cfg = STACKS[name]
    procs = [subprocess.Popen(c, cwd=JS, stdout=open(f"/tmp/ttt-{name}-{i}.log", "w"), stderr=subprocess.STDOUT, start_new_session=True) for i, c in enumerate(cfg["procs"])]
    procs.append(subprocess.Popen(["npx", "vite", "--strictPort"], cwd=JS, stdout=open("/tmp/ttt-vite.log", "w"), stderr=subprocess.STDOUT, start_new_session=True))
    try:
        for port in cfg["ports"] + [5180]:
            wait_port(port)
        res = asyncio.run(play(cfg, out, name))
        (out / f"{name}-result.json").write_text(json.dumps(res, indent=2))
        print(json.dumps(res))
    finally:
        for pr in procs:
            try: os.killpg(pr.pid, signal.SIGTERM)
            except ProcessLookupError: pass


if __name__ == "__main__":
    main()
