"""HTML for the human-facing pages.

The host page is ours: it shows the question, frames the agent's HTML in a sandbox, and
renders the confirm bar itself, so the human sees the exact value before it is sent.

EXPERIMENTAL CODE. Do not use in production.
"""
# File UUID: 4a8d1f63-7e29-4c5b-b3a0-8f6e2d1c9b74

from __future__ import annotations

from html import escape

BASE_CSS = """
*{box-sizing:border-box;margin:0}
body{font:16px/1.5 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f6f5f1;color:#1c1b19;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:16px}
.wrap{width:100%;max-width:480px;display:flex;flex-direction:column;gap:12px}
.tag{font-size:12px;letter-spacing:.06em;text-transform:uppercase;color:#7a7466}
h1{font-size:20px}
iframe{width:100%;height:60vh;border:1px solid #d9d3c4;border-radius:12px;background:#fff}
.bar{position:sticky;bottom:0;background:#fff;border:2px solid #1c1b19;border-radius:12px;padding:12px;display:flex;flex-direction:column;gap:8px}
.val{font-family:ui-monospace,Menlo,monospace;background:#f6f5f1;padding:8px;border-radius:8px;word-break:break-word}
.row{display:flex;gap:8px}
button{flex:1;min-height:48px;font:600 16px/1 inherit;border-radius:10px;border:0;cursor:pointer}
.send{background:#c2410c;color:#fff}.cancel{background:#e7e3d8;color:#1c1b19}
.note{font-size:13px;color:#7a7466}
[hidden]{display:none!important}
"""

HOST_JS = """
const SID = document.body.dataset.sid;
const key = 'heyhuman:' + SID;
const fromHash = new URLSearchParams(location.hash.slice(1)).get('t');
if (fromHash) { sessionStorage.setItem(key, fromHash); history.replaceState(null, '', location.pathname); }
const token = sessionStorage.getItem(key);
const frame = document.getElementById('form');
const bar = document.getElementById('bar');
const val = document.getElementById('val');
const msg = document.getElementById('msg');
let pending = null;
if (!token) { msg.textContent = 'This link is missing its answer token. Open the original link.'; }
addEventListener('message', (e) => {
  if (e.source !== frame.contentWindow) return;
  const d = e.data;
  if (!d || d.heyhuman !== 1) return;
  pending = String(d.decision).slice(0, 2000);
  val.textContent = pending;
  bar.hidden = false;
});
document.getElementById('cancel').addEventListener('click', () => { pending = null; bar.hidden = true; });
document.getElementById('send').addEventListener('click', async () => {
  if (pending === null || !token) return;
  bar.hidden = true;
  msg.textContent = 'Sending...';
  try {
    const r = await fetch(location.pathname.replace(/\\/$/, '') + '/answer', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token, decision: pending }),
    });
    if (r.ok) { sessionStorage.removeItem(key); frame.remove(); msg.textContent = 'Sent: ' + pending; }
    else { msg.textContent = 'Not sent: this link was already used or has expired.'; }
  } catch (err) { msg.textContent = 'Not sent: network error. Try again.'; bar.hidden = false; }
});
"""

SHIM = """<script>
function decide(v){parent.postMessage({heyhuman:1,decision:String(v)},'*')}
function submitRadio(){var s=document.querySelector('input[name="choice"]:checked');if(s)decide(s.value)}
function submitCheckbox(){var c=[].slice.call(document.querySelectorAll('input[name="choice"]:checked')).map(function(x){return x.value});if(c.length)decide(c.join(','))}
</script>"""


def host_page(session_id: str, message: str, nonce: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Your agent has a question</title>
<style nonce="{nonce}">{BASE_CSS}</style></head>
<body data-sid="{escape(session_id)}"><div class="wrap">
<p class="tag">Experimental · HeyHuman</p>
<h1>{escape(message)}</h1>
<iframe id="form" src="/f/{escape(session_id)}/content" sandbox="allow-scripts" title="Question from your agent"></iframe>
<div class="bar" id="bar" hidden>
<p class="note">Your agent will receive exactly this value:</p>
<p class="val" id="val"></p>
<div class="row"><button class="cancel" id="cancel" type="button">Change</button>
<button class="send" id="send" type="button">Send answer</button></div></div>
<p class="note" id="msg" role="status"></p>
<p class="note">The form above was written by an agent. Check the value before you send it.</p>
</div><script nonce="{nonce}">{HOST_JS}</script></body></html>"""


def content_page(agent_html: str) -> str:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">{SHIM}</head>
<body>{agent_html}</body></html>"""


def status_page(state: str, nonce: str) -> str:
    text = {
        "answered": "This question has already been answered.",
        "expired": "This question has expired.",
    }.get(state, "This link is not valid.")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>HeyHuman</title><style nonce="{nonce}">{BASE_CSS}</style></head>
<body><div class="wrap"><p class="tag">Experimental · HeyHuman</p><h1>{escape(text)}</h1></div></body></html>"""
