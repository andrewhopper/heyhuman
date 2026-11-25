"""Open a real form in Chrome, tap a button inside the sandboxed iframe, confirm, and check the stored answer."""
# File UUID: 6a0d3c58-1f42-4e9b-b7a6-2c8e9f5d1b07
import asyncio, json, subprocess, sys, time, urllib.request
from pathlib import Path
from playwright.async_api import async_playwright

PORT = 8787
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp")
srv = subprocess.Popen([sys.executable, str(Path(__file__).parent / "local_server.py"), str(PORT)])
time.sleep(4)
html = Path(__file__).with_name("tictactoe.html").read_text()
req = urllib.request.Request(f"http://localhost:{PORT}/sessions", method="POST", headers={"content-type": "application/json"},
                             data=json.dumps({"html": html, "message": "Your move: you are X"}).encode())
s = json.loads(urllib.request.urlopen(req).read())

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
        pg = await b.new_page(viewport={"width": 390, "height": 844}, device_scale_factor=2)
        errors = []
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        await pg.goto(s["url"]); await pg.wait_for_timeout(800)
        assert "#t=" not in pg.url, "token should be stripped from the address bar"
        frame = pg.frame_locator("#form")
        await frame.locator("button[data-cell='4']").click()
        await pg.wait_for_selector("#bar:not([hidden])")
        await pg.screenshot(path=str(OUT / "hardened-confirm.png"))
        assert (await pg.text_content("#val")) == "4"
        await pg.click("#send"); await pg.wait_for_timeout(800)
        await pg.screenshot(path=str(OUT / "hardened-sent.png"))
        assert "Sent: 4" in (await pg.text_content("#msg"))
        # agent cannot fetch out of the sandbox
        status = json.loads(urllib.request.urlopen(f"http://localhost:{PORT}/sessions/{s['session']}").read())
        assert status["status"] == "answered" and status["decision"] == "4", status
        # replay from a second tab with the same link fails
        pg2 = await b.new_page(); await pg2.goto(s["url"]); await pg2.wait_for_timeout(500)
        assert "already been answered" in (await pg2.text_content("h1"))
        print("OK", status, "console errors:", errors)
        await b.close()

try:
    asyncio.run(main())
finally:
    srv.terminate()
