"""UML sequence diagrams for the five tic-tac-toe builds, in the marker-sketch blog style.

Messages are taken from the actual test apps in comparisons/tictactoe and hardened/.
kind: '>' call, '-' reply (dashed), 's' self message, 'n' out-of-band (dashed, orange-free).
acc=1 marks where the UI comes from (burnt-orange accent).
"""
# File UUID: 4f8a2d61-9c37-4e05-b1a8-7d3e6c2f0b94
import html

OR = "#c85a00"; INK = "#1a1a1a"; BG = "#f5f0e6"; FILL = "#fffdf7"; ACC_FILL = "#fbe7d6"
FONT = "Kalam,Comic Relief,cursive"
TITLE_FONT = "Permanent Marker,Kalam,cursive"
import base64
_F = "/tmp/fonts/node_modules/@fontsource/"
FONTFACE = "".join(f"@font-face{{font-family:{n};font-weight:{w};src:url(data:font/woff2;base64,{base64.b64encode(open(_F + p, 'rb').read()).decode()}) format('woff2')}}" for n, w, p in [("Kalam", 400, "kalam/files/kalam-latin-400-normal.woff2"), ("Kalam", 700, "kalam/files/kalam-latin-700-normal.woff2"), ("Permanent Marker", 400, "permanent-marker/files/permanent-marker-latin-400-normal.woff2")])
STAMP = "v1 · 5e2c8b · 2026-11-25"

D = {
    "heyhuman": ("HEYHUMAN (HARDENED): ONE LINK PER MOVE",
        ["AGENT CLI", "AGENT URL λ (IAM)", "DYNAMODB", "HUMAN URL λ (PUBLIC)", "IOT CORE", "PHONE BROWSER"],
        [], [
        (0, 1, ">", "POST /sessions {HTML BOARD}", 1),
        (1, 2, ">", "PUT ITEM: TOKEN HASH, TTL", 0),
        (1, 0, "-", "LINK /f/{ID}#t=TOKEN", 0),
        (0, 4, ">", "SUBSCRIBE heyhuman/{ID}/response", 0),
        (0, 5, "n", "LINK SENT TO HUMAN", 0),
        (5, 3, ">", "GET /f/{ID} + /content", 0),
        (3, 5, "-", "HOST PAGE + SANDBOXED AGENT HTML", 1),
        (5, 5, "s", "TAP SQUARE, CONFIRM BAR SHOWS VALUE", 0),
        (5, 3, ">", "POST /answer {TOKEN, DECISION}", 0),
        (3, 2, ">", "CONDITIONAL UPDATE (ONE-TIME)", 0),
        (3, 4, ">", "PUBLISH DECISION", 0),
        (4, 0, "-", "DECISION \"4\"", 0),
        (0, 0, "s", "MINIMAX PICKS O, WRITES NEXT BOARD", 0),
    ], "ORANGE = WHERE THE UI COMES FROM: THE AGENT'S OWN HTML. REMOTE: AGENT AND PHONE NEVER CONNECT DIRECTLY."),
    "mcp": ("MCP APPS VIA MCP UI: SERVER SHIPS THE APP, HOST SANDBOXES IT",
        ["USER", "HOST PAGE", "SANDBOX PROXY (2ND ORIGIN)", "APP IFRAME", "MCP SERVER"],
        [
        (1, 4, ">", "tools/call tic_tac_toe", 0),
        (4, 1, "-", "RESULT {BOARD}", 0),
        (1, 4, ">", "resources/read ui://tic-tac-toe/board.html", 0),
        (4, 1, "-", "APP HTML", 1),
        (1, 2, ">", "sandbox-resource-ready {HTML}", 0),
        (2, 3, ">", "document.write(HTML)", 0),
        (3, 1, ">", "ui/initialize (JSON-RPC, postMessage)", 0),
        (1, 3, "-", "TOOL INPUT + TOOL RESULT", 0),
    ], [
        (0, 3, ">", "TAP SQUARE", 0),
        (3, 1, ">", "tools/call ttt_move (VIA PROXY)", 0),
        (1, 4, ">", "tools/call ttt_move {BOARD, CELL}", 0),
        (4, 4, "s", "PLAY X, MINIMAX O", 0),
        (4, 1, "-", "structuredContent {BOARD, STATUS}", 0),
        (1, 3, "-", "RESULT, APP RE-RENDERS", 0),
    ], "ORANGE = WHERE THE UI COMES FROM: A ui:// RESOURCE. APP-HOST IS IN-BROWSER IPC; SERVER CAN BE LOCAL (STDIO) OR REMOTE (HTTP)."),
    "a2ui": ("A2UI v1.0: AGENT SENDS JSON, CLIENT DRAWS FROM ITS CATALOG",
        ["USER", "REACT CLIENT (RENDERER + CATALOG)", "A2UI AGENT"],
        [
        (1, 2, ">", "POST /api/a2ui/start", 0),
        (2, 1, "-", "createSurface + updateComponents (GRID OF BUTTONS) + updateDataModel", 1),
        (1, 1, "s", "VALIDATE AGAINST BASIC CATALOG, RENDER NATIVE COMPONENTS", 0),
    ], [
        (0, 1, ">", "TAP BUTTON", 0),
        (1, 2, ">", "ACTION {NAME: move, CONTEXT: {CELL}}", 0),
        (2, 2, "s", "PLAY X, MINIMAX O", 0),
        (2, 1, "-", "updateDataModel {BOARD, STATUS}", 0),
        (1, 1, "s", "RE-RENDER BOUND TEXT (@path /board/i)", 0),
    ], "ORANGE = WHERE THE UI COMES FROM: DECLARATIVE JSON, LAYOUT SENT ONCE. TRANSPORT-AGNOSTIC (HTTP HERE)."),
    "agui": ("AG-UI: THE AGENT STREAMS EVENTS, THE FRONTEND DRAWS",
        ["USER", "FRONTEND (TS)", "HttpAgent (@ag-ui/client)", "AGENT SERVER"],
        [
        (1, 2, ">", "runAgent({})", 0),
        (2, 3, ">", "POST RunAgentInput (SSE)", 0),
        (3, 2, "-", "RUN_STARTED, STATE_SNAPSHOT, RUN_FINISHED", 0),
        (2, 1, "-", "onStateSnapshotEvent", 0),
        (1, 1, "s", "RENDER BOARD FROM STATE", 1),
    ], [
        (0, 1, ">", "TAP SQUARE", 0),
        (1, 2, ">", "setState(BOARD); runAgent({forwardedProps: {CELL}})", 0),
        (2, 3, ">", "POST RunAgentInput {STATE, CELL}", 0),
        (3, 2, "-", "RUN_STARTED", 0),
        (3, 2, "-", "STATE_SNAPSHOT: YOUR X, THINKING", 0),
        (2, 1, "-", "RENDER", 0),
        (3, 2, "-", "STATE_SNAPSHOT: AGENT'S O", 0),
        (2, 1, "-", "RENDER", 0),
        (3, 2, "-", "RUN_FINISHED", 0),
    ], "ORANGE = WHERE THE UI COMES FROM: CODE IN THE FRONTEND. REMOTE: HTTP + SSE."),
    "aisdk": ("VERCEL AI SDK UI: DATA PARTS IN A CHAT STREAM",
        ["USER", "REACT (useChat)", "CHAT ROUTE (createUIMessageStream)"],
        [
        (1, 2, ">", "POST /api/chat \"LET'S PLAY\"", 0),
        (2, 1, "-", "TEXT PART + data-board PART", 0),
        (1, 1, "s", "MAP data-board TO <Board> COMPONENT", 1),
    ], [
        (0, 1, ">", "TAP SQUARE", 0),
        (1, 2, ">", "sendMessage \"move N\" + FULL HISTORY", 0),
        (2, 2, "s", "LAST data-board IN HISTORY, PLAY X, MINIMAX O", 0),
        (2, 1, "-", "TEXT \"I TAKE SQUARE N\"", 0),
        (2, 1, "-", "data-board {BOARD, STATUS}", 0),
        (1, 1, "s", "RE-RENDER <Board>", 0),
    ], "ORANGE = WHERE THE UI COMES FROM: YOUR COMPONENT. REMOTE: HTTP STREAMING. STATE LIVES IN THE CHAT HISTORY."),
}
# HeyHuman has no setup phase: every move is a fresh session.
D["heyhuman"] = (D["heyhuman"][0], D["heyhuman"][1], [], D["heyhuman"][3], D["heyhuman"][4])


def wrap(t, n):
    out, cur = [], ""
    for w in t.split():
        if len(cur) + len(w) + 1 > n and cur:
            out.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    out.append(cur)
    return out


def text(x, y, s, size=15, anchor="middle", color=INK, weight=700, family=None, halo=True):
    h = f' stroke="{BG}" stroke-width="6" stroke-linejoin="round" paint-order="stroke"' if halo else ""
    return f'<text x="{x:.0f}" y="{y:.0f}" text-anchor="{anchor}" font-family="{family or FONT}" font-size="{size}" font-weight="{weight}" fill="{color}"{h}>{html.escape(s)}</text>'


def build(key):
    title, parts, setup, loop, cap = D[key]
    COL = 250 if len(parts) <= 4 else 215
    W = max(60 + COL * len(parts) + 120, int(len(title) * 19 + 80), int(len(cap) * 9.6 + 80))
    xs = [60 + COL * i + COL / 2 for i in range(len(parts))]
    ROW = 62
    top, head = 112, 84
    y = top + head + 40
    body, ids = [], []

    def message(n, m, idx):
        nonlocal y
        a, b, kind, label, acc = m
        color = OR if acc else INK
        num = f"{n}.{idx}"
        if kind == "s":
            x = xs[a]; flip = a == len(parts) - 1; sgn = -1 if flip else 1
            body.append(f'<path d="M{x} {y} h{46*sgn} v26 h{-40*sgn}" stroke="{color}" stroke-width="3" fill="none" marker-end="url(#a{"o" if acc else ""})"/>')
            sl = wrap(label, 30)
            for q, line in enumerate(sl):
                body.append(text(x + 56 * sgn, y + 10 + q * 18, line, 14, "end" if flip else "start", color))
            body.append(text(x + 10 * -sgn, y + 4, num, 13, "start" if flip else "end", INK, 400))
            y += ROW + 8 + 20 * (len(sl) - 1)
            return
        x1, x2 = xs[a], xs[b]
        dash = ' stroke-dasharray="9 7"' if kind in "-n" else ""
        lines = wrap(label, int(abs(x2 - x1) / 8.2) or 20)
        y += 20 * (len(lines) - 1)
        body.append(f'<path d="M{x1} {y} H{x2 + (-8 if x2 > x1 else 8)}" stroke="{color}" stroke-width="3" fill="none"{dash} marker-end="url(#a{"o" if acc else ""})"/>')
        mid = (x1 + x2) / 2
        for q, line in enumerate(lines):
            body.append(text(mid, y - 10 - (len(lines) - 1 - q) * 18, line, 14, "middle", color))
        body.append(text(min(x1, x2) + 6, y + 18, num, 13, "start", INK, 400))
        y += ROW

    for i, m in enumerate(setup, 1):
        message(1, m, i)
    loop_top = y - 34
    y += 44
    for i, m in enumerate(loop, 1):
        message(2, m, i)
    loop_bot = y - 30
    H = int(y + 70)

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<defs><style>{FONTFACE}</style>'
         f'<marker id="a" markerUnits="userSpaceOnUse" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto"><path d="M0 0L12 5L0 10z" fill="{INK}"/></marker>'
         f'<marker id="ao" markerUnits="userSpaceOnUse" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto"><path d="M0 0L12 5L0 10z" fill="{OR}"/></marker>'
         '</defs>',
         f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         text(30, 52, title, 30, "start", INK, 400, TITLE_FONT),
         text(32, 80, STAMP, 13, "start", INK, 400)]
    for i, (p, x) in enumerate(zip(parts, xs)):
        o.append(f'<line x1="{x}" y1="{top + head}" x2="{x}" y2="{H - 50}" stroke="{INK}" stroke-width="2" stroke-dasharray="4 8"/>')
        o.append(f'<rect x="{x - COL / 2 + 10}" y="{top}" width="{COL - 20}" height="{head}" rx="12" fill="{FILL}" stroke="{INK}" stroke-width="3"/>')
        ls = wrap(p, 18)
        for q, line in enumerate(ls):
            o.append(text(x, top + head / 2 + 6 - (len(ls) - 1) * 10 + q * 20, line, 16))
        o.append(text(x - COL / 2 + 18, top - 6, f"{i + 1}.0", 12, "start", INK, 400))
    if setup:
        o.append(text(36, top + head + 30, "1 · SETUP", 14, "start", INK))
    o.append(f'<rect x="24" y="{loop_top}" width="{W - 48}" height="{loop_bot - loop_top}" rx="6" fill="none" stroke="{INK}" stroke-width="2.5"/>')
    o.append(f'<path d="M24 {loop_top} h190 v22 l-12 12 H24 z" fill="{INK}"/>')
    o.append(text(34, loop_top + 23, "LOOP [EACH MOVE] · 2", 14, "start", BG, halo=False))
    o += body
    o.append(text(30, H - 20, cap, 16, "start", OR))
    o.append("</svg>")
    return "\n".join(o), W, H


if __name__ == "__main__":
    for k in D:
        svg, w, h = build(k)
        open(f"seq-{k}.svg", "w").write(svg)
        print(k, w, h)
