"""HeyHuman (hardened stack, run locally): the agent writes a board form each turn and waits for the answer.

python3 -I tests/play_heyhuman.py [out_dir]
Uses the hardened Lambda handlers behind a local HTTP server (moto for DynamoDB). Each turn is one
session: one link, one answer, as in the hardened stack. The human side is real Chrome.
EXPERIMENTAL CODE. Do not use in production.
"""
# File UUID: 1d7b4e92-6c30-4a85-b2f1-9e3a8c5d0f67
import asyncio, json, os, signal, subprocess, sys, time, urllib.request
from pathlib import Path
from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).parent))
from play import wait_port, FINAL  # noqa: E402

HARDENED = Path(os.environ.get("HEYHUMAN_HARDENED", Path(__file__).resolve().parents[3]))
PORT = 8790
LINES = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6), (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def status(b):
    for a, c, d in LINES:
        if b[a] and b[a] == b[c] == b[d]:
            return f"{b[a]} wins"
    return "draw" if all(b) else "your-move"


def score(b, turn, depth):
    s = status(b)
    if s == "O wins": return 10 - depth
    if s == "X wins": return depth - 10
    if s == "draw": return 0
    vals = []
    for i in range(9):
        if not b[i]:
            n = b[:]; n[i] = turn; vals.append(score(n, "X" if turn == "O" else "O", depth + 1))
    return max(vals) if turn == "O" else min(vals)


def agent_move(b):
    best, best_s = -1, -99
    for i in range(9):
        if not b[i]:
            n = b[:]; n[i] = "O"; s = score(n, "X", 1)
            if s > best_s: best, best_s = i, s
    return best


def board_form(b, note):
    cells = "".join(f'<button data-cell="{i}" {"disabled" if c else ""} onclick="decide(\'{i}\')">{c}</button>' for i, c in enumerate(b))
    return ("<style>.g{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;max-width:300px;margin:8px auto}"
            ".g button{aspect-ratio:1;font-size:36px;font-weight:700;border:2px solid #1c1b19;border-radius:12px;background:#fff}"
            "p{text-align:center;font:16px sans-serif;margin:8px}</style>"
            f"<p id=\"status\">{note}</p><div class=\"g\">{cells}</div>")


def api(method, path, body=None):
    req = urllib.request.Request(f"http://localhost:{PORT}{path}", method=method, headers={"content-type": "application/json"},
                                 data=json.dumps(body).encode() if body is not None else None)
    return json.loads(urllib.request.urlopen(req).read())


async def main(out: Path):
    board, moves, latencies, links = [""] * 9, [], [], 0
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 760}, device_scale_factor=2)
        note, turn = "Your move: you are X", 0
        while status(board) == "your-move":
            s = api("POST", "/sessions", {"html": board_form(board, note), "message": "Tic-tac-toe: your move", "ttl_seconds": 300})
            links += 1
            await pg.goto(s["url"]); await pg.wait_for_timeout(300)
            frame = pg.frame_locator("#form")
            if turn == 0:
                await pg.screenshot(path=str(out / "heyhuman-start.png"))
            open_cells = [i for i, c in enumerate(board) if not c]
            pick = 4 if 4 in open_cells else open_cells[0]
            t1 = time.time()
            await frame.locator(f"button[data-cell='{pick}']").click()
            await pg.wait_for_selector("#bar:not([hidden])")
            if turn == 1:
                await pg.screenshot(path=str(out / "heyhuman-mid.png"))
            await pg.click("#send")
            # the agent's side: poll stored status, as the CLI does
            while (st := api("GET", f"/sessions/{s['session']}"))["status"] != "answered":
                time.sleep(0.05)
            latencies.append(round(time.time() - t1, 2))
            cell = int(st["decision"]); assert not board[cell]; board[cell] = "X"; moves.append(cell)
            if status(board) == "your-move":
                a = agent_move(board); board[a] = "O"; note = f"Agent took square {a}. Your move."
            turn += 1
        final = status(board)
        s = api("POST", "/sessions", {"html": board_form(board, final), "message": f"Game over: {final}", "ttl_seconds": 60})
        await pg.goto(s["url"]); await pg.wait_for_timeout(400)
        await pg.screenshot(path=str(out / "heyhuman-end.png"))
        await b.close()
    assert final in FINAL
    return {"stack": "heyhuman", "result": final, "moves": moves, "board": board, "links_opened": links,
            "move_latency_s_incl_confirm": latencies}


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[1] / "shots"); out.mkdir(parents=True, exist_ok=True)
    srv = subprocess.Popen([sys.executable, "-I", str(HARDENED / "tests/browser/local_server.py"), str(PORT)], stdout=open("/tmp/ttt-heyhuman.log", "w"), stderr=subprocess.STDOUT, start_new_session=True)
    try:
        wait_port(PORT)
        res = asyncio.run(main(out))
        (out / "heyhuman-result.json").write_text(json.dumps(res, indent=2)); print(json.dumps(res))
    finally:
        os.killpg(srv.pid, signal.SIGTERM)
