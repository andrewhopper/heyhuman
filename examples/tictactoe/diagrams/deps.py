"""Dependency matrix for the five tic-tac-toe builds, in the marker-sketch blog style.

Rows are what each stack needs in place before the first question reaches a human.
Values come from the builds in comparisons/tictactoe and hardened/.
"""
# File UUID: 2a9c5e48-1b73-4f60-8d2e-6c4b0f7a3e15
import html
from seq import BG, FILL, FONT, FONTFACE, INK, OR, TITLE_FONT, text, wrap

STAMP = "v2 · 3d7f2a · 2026-11-25"
COLS = ["HEYHUMAN", "MCP APPS / MCP UI", "A2UI", "AG-UI", "AI SDK UI"]
Y, N, P = "yes", "no", "part"
ROWS = [
    ("WORKS FROM A PASTED CLI CALL, NO HOST CONFIG",
     [(Y, ""), (N, "SERVER ADDED TO A HOST"), (N, "APP WITH A RENDERER"), (N, "FRONTEND YOU BUILD"), (N, "APP YOU BUILD")]),
    ("HUMAN NEEDS ONLY A BROWSER",
     [(Y, "ANY DEVICE, ANY PERSON WITH THE LINK"), (N, "A HOST WITH MCP APPS"), (N, "YOUR APP"), (N, "YOUR APP"), (N, "YOUR APP")]),
    ("REQUIRES A REMOTE SERVICE",
     [(P, "AWS, OR YOUR MACHINE + A TUNNEL"), (P, "ONLY FOR A REMOTE SERVER"), (P, "ONLY IF THE AGENT IS REMOTE"), (P, "ONLY IF THE AGENT IS REMOTE"), (P, "ONLY IF THE APP IS DEPLOYED")]),
    ("REQUIRES A LOCAL PROCESS TO STAY OPEN",
     [(P, "AGENT CLI WAITS; ANSWER IS STORED"), (Y, "HOST APP + SERVER (STDIO)"), (Y, "CLIENT APP"), (Y, "FRONTEND DURING THE RUN"), (Y, "BROWSER DURING THE STREAM")]),
    ("HUMAN AND AGENT CAN BE ON DIFFERENT NETWORKS",
     [(Y, "VIA AWS, OR A TUNNEL WHEN LOCAL"), (N, "HUMAN SITS AT THE HOST"), (P, "IF THE CLIENT IS DEPLOYED"), (P, "IF THE FRONTEND IS DEPLOYED"), (P, "IF THE APP IS DEPLOYED")]),
    ("LOCAL IPC ON THE UI PATH",
     [(N, ""), (Y, "postMessage APP-HOST"), (N, ""), (N, ""), (N, "")]),
    ("EXTRA SECURITY PIECE TO RUN",
     [(Y, "ANSWER TOKENS, CSP SANDBOX"), (Y, "SANDBOX PROXY ON 2ND ORIGIN"), (N, "CATALOG IS THE GUARD"), (N, ""), (N, "")]),
    ("CLOUD ACCOUNT NEEDED",
     [(P, "AWS, OR NONE WHEN LOCAL"), (N, ""), (N, ""), (N, ""), (N, "ANY HOST")]),
]


def mark(x, y, v):
    if v == Y:
        return f'<path d="M{x-14} {y} l9 10 l19 -22" stroke="{INK}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'
    if v == N:
        return f'<path d="M{x-11} {y-11} l22 22 M{x+11} {y-11} l-22 22" stroke="{INK}" stroke-width="5" fill="none" stroke-linecap="round"/>'
    return f'<path d="M{x-14} {y} h28" stroke="{INK}" stroke-width="5" stroke-linecap="round"/><circle cx="{x}" cy="{y}" r="17" fill="none" stroke="{INK}" stroke-width="2.5"/>'


def build():
    LW, CW, RH, top = 360, 250, 96, 150
    W = 40 + LW + CW * len(COLS) + 20
    H = top + RH * len(ROWS) + 110
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
         f'<defs><style>{FONTFACE}</style></defs>', f'<rect width="{W}" height="{H}" fill="{BG}"/>',
         text(30, 52, "WHAT EACH STACK NEEDS BEFORE THE FIRST QUESTION", 30, "start", INK, 400, TITLE_FONT),
         text(32, 80, STAMP, 13, "start", INK, 400)]
    for j, c in enumerate(COLS):
        x = 40 + LW + CW * j
        o.append(f'<rect x="{x+6}" y="{top-48}" width="{CW-12}" height="40" rx="10" fill="{FILL}" stroke="{INK}" stroke-width="3"/>')
        o.append(text(x + CW / 2, top - 22, c, 16))
        o.append(text(x + 14, top - 54, f"{j+1}.0", 12, "start", INK, 400))
    for i, (label, cells) in enumerate(ROWS):
        y = top + RH * i
        o.append(f'<line x1="30" y1="{y+RH}" x2="{W-20}" y2="{y+RH}" stroke="{INK}" stroke-width="1.5" stroke-dasharray="3 7"/>')
        ls = wrap(label, 30)
        for q, line in enumerate(ls):
            o.append(text(40, y + RH / 2 + 6 - (len(ls) - 1) * 10 + q * 20, line, 16, "start", OR if i == 0 else INK))
        o.append(text(36, y + 18, f"R{i+1}", 12, "start", INK, 400))
        for j, (v, note) in enumerate(cells):
            cx = 40 + LW + CW * j + CW / 2
            o.append(mark(cx, y + 34, v))
            for q, line in enumerate(wrap(note, 26)):
                o.append(text(cx, y + 70 + q * 17, line, 13, "middle", INK, 700))
    ly = H - 34
    o.append(mark(46, ly - 6, Y)); o.append(text(70, ly, "YES", 15, "start"))
    o.append(mark(150, ly - 6, P)); o.append(text(176, ly, "SOMETIMES", 15, "start"))
    o.append(mark(320, ly - 6, N)); o.append(text(344, ly, "NO", 15, "start"))
    o.append(text(420, ly, "ORANGE ROW = HEYHUMAN'S EDGE: NO HOST, APP OR CONFIG. ITS COST: AWS, OR A MACHINE THAT STAYS ON (R3, R8).", 15, "start", OR))
    o.append("</svg>")
    return "\n".join(o)


if __name__ == "__main__":
    open("deps.svg", "w").write(build())
    print("ok")
