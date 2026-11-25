"""Where each stack's UI can be shown, in the marker-sketch blog style.

Sources: MCP Apps launch post (2026-01-26) for hosts; A2UI 1.0 post and renderer list
for A2UI; CopilotKit docs for AG-UI; Vercel AI SDK docs; this repo for HeyHuman.
"""
# File UUID: 5e1a7c39-8d24-4b06-a3f9-0c6d2e8b4f71
import deps
from deps import N, P, Y

deps.STAMP = "v1 · 8c4f1a · 2026-11-25"
deps.ROWS = [
    ("AI CHAT APP: CLAUDE, CHATGPT, GOOSE",
     [(P, "LINK IN THE REPLY, OPENS A BROWSER TAB"), (Y, "INLINE IN THE CHAT"), (P, "INSIDE AN MCP APP"), (N, ""), (N, "")]),
    ("IDE CHAT: VS CODE COPILOT",
     [(P, "LINK"), (Y, "IN THE CHAT PANEL"), (N, ""), (N, ""), (N, "")]),
    ("TERMINAL AGENT: CLAUDE CODE CLI",
     [(Y, "CLI PRINTS THE LINK; ANSWER ON ANY DEVICE"), (N, "TOOL RESULT SHOWS AS TEXT"), (P, "COMMUNITY TERMINAL RENDERER"), (N, ""), (N, "")]),
    ("YOUR OWN WEB APP, DESKTOP",
     [(P, "STANDALONE PAGE, NOT EMBEDDED"), (Y, "AS THE HOST, VIA @MCP-UI/CLIENT"), (Y, "REACT, LIT, ANGULAR"), (Y, "COPILOTKIT FRONTEND"), (Y, "USECHAT IN REACT")]),
    ("PHONE, NO APP INSTALLED",
     [(Y, "MOBILE BROWSER, ANY PERSON WITH THE LINK"), (N, "HUMAN SITS AT THE HOST"), (P, "IF YOUR WEB APP IS DEPLOYED"), (P, "IF YOUR WEB APP IS DEPLOYED"), (P, "IF YOUR WEB APP IS DEPLOYED")]),
    ("NATIVE MOBILE APP",
     [(N, "BROWSER ONLY"), (N, ""), (Y, "FLUTTER; SWIFTUI, COMPOSE COMING"), (N, ""), (P, "EXPO / REACT NATIVE")]),
    ("SLACK OR EMAIL",
     [(P, "LINK IN A MESSAGE, OPENS A BROWSER"), (N, ""), (P, "COPILOTKIT SLACK RENDERER"), (N, ""), (N, "")]),
]

if __name__ == "__main__":
    svg = deps.build()
    svg = svg.replace("WHAT EACH STACK NEEDS BEFORE THE FIRST QUESTION", "WHERE EACH STACK'S UI CAN SHOW UP")
    import re
    svg = re.sub(r"ORANGE ROW = [^<]*", "ORANGE ROW: ONLY MCP APPS RENDERS INSIDE THIRD-PARTY CHAT APPS. HEYHUMAN SHOWS A LINK THERE.", svg)
    open("surfaces-8c4f1a-v1.svg", "w").write(svg)
    print("ok")
