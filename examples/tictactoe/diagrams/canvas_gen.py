import json
U={'index':'a747dd74987a0026fb75649fa06d7885','p1top':'a0d1c74c9a4f8fa00bfbfdacc156a745','p2top':'681fee988b795a5149bd4fbe28baa6f8','p1full':'5de901f281997997782fce6b869f0e12','p2full':'de927e88488cb0ece5a023b49f7039dd','p3full':'6b7e3228746334ec9d46f53db971fc95','arch':'ec1c66cd5d5b915ca43ddf552e6e9767','sh':'39a523092abd5b7b1e6c37d5ae04ee96','sm':'8aba3e487ef211b0e5b463279256f9fb','sa':'1878a91a475cfdf68cdb781f062a7f2e','sg':'d54cf7623bc53fff21ca59056a4febb9','ttt3':'13784244eccca7be64310ee58269c26d','tttr':'9f994e1024e4cb58c4abff729fbc9661','v1':'ab1659d3e456306efacdeb90ef8461eb','v2':'96377902074bb0f86ed3cfa19d4cf8fb','ag1':'f44732cd1f8104ba33f038c5dfdb05e9','ag2':'bc5df1a0c908dd511f045094a0823a1c','mui':'280a924a778d1f082e422a33d4edbfa0','a2':'80f02a46afc914b7c1b417ca86a409c1','ttt5':'a2e033ec37cd0ccbf700e388ce00e971','qh':'686f19c02cd56c13c050c0e48486c44e','qm':'4b586215e022fa558c04046931e9964b','qa':'eca5838bf5b4974a004edb8e7556754e','qg':'5939d8d0894e77d9882e8400d8666904','qv':'bd0cd833b2b0fb6b2e828a49b5374ea3','hconf':'b93494e43a400944a95c92a768320225','deps':'11a0c0b60b7ac28f61731d6f9f081824'}
def img(k,w,h,alt,extra=''):
    return f'<img src="/_blob/{U[k]}" alt="{alt}" style="display:block;width:{w}px;height:{h}px;border:1px solid #d9d3c4;border-radius:8px;background:#fff;{extra}">'
def fig(k,w,h,alt,cap):
    return f'<figure style="margin:0;display:flex;flex-direction:column;gap:10px">{img(k,w,h,alt)}<figcaption style="font-size:15px;line-height:1.4;color:#4a463d;max-width:{w}px">{cap}</figcaption></figure>'
def page(title,w,h,body,tid):
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<script src="./support.js"></script>
</head>
<body>
<x-dc>
<helmet>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&amp;display=swap" rel="stylesheet">
<style>
body{{margin:0;font-family:Inter,system-ui,sans-serif}}
a{{color:#9a4300}}a:hover{{color:#6b2e00}}
</style>
</helmet>
<div style="width:{w}px;height:{h}px;box-sizing:border-box;padding:40px 80px;background:#f6f4ee;color:#1a1a1a;display:flex;flex-direction:column;gap:28px;position:relative">
<h1 style="margin:0;font-size:44px;line-height:1.1;font-weight:700">{title}</h1>
{body}
<p style="margin:0;font-size:14px;color:#4a463d;position:absolute;left:80px;bottom:24px">v1 · {tid} · 2026-11-25</p>
</div>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{"$preview":{{"width":{w},"height":{h}}}}}'>
class Component extends DCLogic {{
renderVals() {{ return {{}}; }}
}}
</script>
</body>
</html>'''
F={}
# Main
F['Main.dc.html']=page('The posts: blog index and the two posts',2000,760,'<div style="display:flex;gap:32px">'+fig('index',600,422,'Blog index filtered to Design Concept, showing one post','Blog index with the new Design Concept type filter and the series label.')+fig('p1top',600,422,'Top of part 1: Exploring Generative UI to accelerate human agent collaboration','Part 1, the design concept post: badge, title, concept block, about panel. Draft, rendered locally.')+fig('p2top',600,422,'Top of part 2: HeyHuman, The Proof of Concept','Part 2, the proof of concept. Same series. Draft, rendered locally.')+'</div>','4f2a9c')
F['Post1Full.dc.html']=page('Part 1, generative ephemeral UI (v3 · b71e03 · 2026-11-25)',880,9420,'<div>'+img('p1full',800,9176,'Full-page screenshot of part 1, generative ephemeral UI')+'</div>','b71e03')
F['Post2Full.dc.html']=page('Part 2, remote interaction patterns (v3 · d90c5e · 2026-11-25)',880,6560,'<div>'+img('p2full',800,6317,'Full-page screenshot of part 2, remote interaction patterns')+'</div>','d90c5e')
F['Post3Full.dc.html']=page('Part 3, HeyHuman proof of concept (v1 · e4a17c · 2026-11-25)',880,2740,'<div>'+img('p3full',800,2497,'Full-page screenshot of part 3, the HeyHuman proof of concept')+'</div>','e4a17c')
F['Diagrams.dc.html']=page('Diagrams and the tic-tac-toe comparison',2160,1980,
 '<div style="display:flex;gap:40px">'+fig('arch',1000,567,'HeyHuman architecture diagram','HeyHuman architecture: form path and answer path.')+fig('ttt3',1000,562,'Tic-tac-toe three ways: real HeyHuman board, illustrations for MCP Apps and A2UI','Tic-tac-toe three ways. Only the HeyHuman panel is a real render; the other two are labeled illustrations.')+'</div>'
 +'<div style="display:flex;gap:40px">'+fig('sh',1000,353,'HeyHuman swimlane','Swimlane: HeyHuman.')+fig('sm',1000,396,'MCP Apps swimlane','Swimlane: MCP Apps. Claude Code shows text only; the UI renders in a host such as Claude Desktop.')+'</div>'
 +'<div style="display:flex;gap:40px">'+fig('sa',1000,353,'A2UI swimlane','Swimlane: A2UI, from its docs, not a trace of a running system.')+fig('sg',1000,494,'AG-UI and CopilotKit swimlane','Swimlane: AG-UI with CopilotKit, from its docs, not a trace of a running system.')+'</div>','e2a46f')
F['Videos.dc.html']=page('Video stills and the real board',2400,1080,
 '<div style="display:flex;gap:40px;align-items:flex-start">'+fig('v1',900,506,'Poster frame of the 26 second walkthrough','Walkthrough video, 26 s: the five steps. Animated, not a screen recording. File: heyhuman-design-concept.mp4.')+fig('v2',900,506,'Poster frame of the 40 second use-cases video','Use-cases video, 40 s: compose a form (now with slider and toggle), tic-tac-toe, a series of questions, rating options. Animated. File: heyhuman-use-cases.mp4.')+fig('tttr',390,760,'Real HeyHuman tic-tac-toe board on a phone','The real board page from the repo test run, move 5.')+'</div>','0c58b7')
card=lambda t,items:f'<section style="flex:1;background:#fffdf7;border:1px solid #d9d3c4;border-radius:12px;padding:24px"><h2 style="margin:0 0 12px;font-size:24px">{t}</h2><ul style="margin:0;padding-left:20px;font-size:17px;line-height:1.6">'+''.join(f'<li>{i}</li>' for i in items)+'</ul></section>'
F['Packages.dc.html']=page('Packaging and pull requests',1400,720,
 '<div style="display:flex;gap:24px">'+card('MCP server',['heyhuman_start, heyhuman_wait, heyhuman_ask_template','7 tests and a stdio client call, against a fake CLI','Validates session IDs and template names'])+card('Claude Code skill',['packages/claude-code-skill/heyhuman/SKILL.md','Portable: HEYHUMAN_CLI and HEYHUMAN_URL','Prefers the MCP tools when present'])+card('Kiro power',['POWER.md, mcp.json, two steering files','Edit mcp.json for your URL and path','Newer plugin.json layout not built'])+'</div>'
 +'<p style="margin:0;font-size:18px;line-height:1.6">Pull requests, both draft: myblog <a href="https://github.com/andrewhopper/myblog/pull/147">#147</a> (post type, two posts, media) and hopperlabs <a href="https://github.com/andrewhopper/hopperlabs/pull/212">#212</a> (packaging). Nothing here has been run against a live HeyHuman stack.</p>','5a93d8')
F['LiveRuns.dc.html']=page('The others, running locally (v1 · 7c3e91 · 2026-11-25)',3200,760,
 '<div style="display:flex;gap:40px;align-items:flex-start">'+fig('ag1',640,511,'AG-UI dojo mid-run with steps streaming','AG-UI dojo, scripted Python agent: STATE_SNAPSHOT and STATE_DELTA events redraw the plan live.')+fig('ag2',640,511,'AG-UI human-in-the-loop checklist with Reject and Confirm','AG-UI human in the loop: the run waits for Confirm or Reject inside the app.')+fig('mui',816,510,'MCP Inspector rendering the showRawHtml UI resource','MCP UI: typescript-server-demo in ui-inspector; the tool result renders as HTML. The MCP Apps demo showed text only in this host.')+fig('a2',816,510,'A2UI Composer gallery widgets','A2UI Composer gallery (spec v0.9), stored JSON drawn by the React renderer. Icon font missing, so icons show as names.')+'</div>','7c3e91')
F['TicTacToe.dc.html']=page('Tic-tac-toe on five stacks (v1 · 9b41e7 · 2026-11-25)',3200,1060,
 fig('ttt5',3000,895,'Five tic-tac-toe boards mid-game','Same minimax agent on HeyHuman, MCP Apps via MCP UI, A2UI, AG-UI and Vercel AI SDK UI. Each was played to the end by a Playwright script in Chrome; all on one machine, no LLM.'),'9b41e7')
F['Sequences.dc.html']=page('Sequence diagrams per stack (v1 · 5e2c8b · 2026-11-25)',5100,1040,
 '<div style="display:flex;gap:40px;align-items:flex-start">'+img('qh',1057,900,'HeyHuman sequence')+img('qm',925,900,'MCP Apps sequence')+img('qa',1053,900,'A2UI sequence')+img('qg',801,900,'AG-UI sequence')+img('qv',995,900,'AI SDK UI sequence')+'</div>','5e2c8b')
F['Hardened.dc.html']=page('Hardened HeyHuman, local browser test (v1 · 7a1d40 · 2026-11-25)',520,1000,
 fig('hconf',390,844,'Hardened HeyHuman host page with sandboxed form and confirm bar','The host page frames the agent HTML in a sandbox and shows the exact value before it is sent.'),'7a1d40')
F['Deps.dc.html']=page('Dependencies per stack (v1 · 3d7f2a · 2026-11-25)',2100,1360,img('deps',2000,1231,'Dependency matrix for five stacks'),'3d7f2a')
for k,v in F.items(): open(f'root/project/{k}','w').write(v)
boards={'Main.dc.html':(0,0,2000,760),'Post1Full.dc.html':(0,880,880,9420),'Post2Full.dc.html':(960,880,880,6560),'Post3Full.dc.html':(960,7560,880,2740),'Diagrams.dc.html':(1920,880,2160,1980),'Videos.dc.html':(1920,2980,2400,1080),'Packages.dc.html':(1920,4180,1400,720),'LiveRuns.dc.html':(1920,5020,3200,760),'TicTacToe.dc.html':(1920,5900,3200,1060),'Hardened.dc.html':(5240,5900,520,1000),'Sequences.dc.html':(1920,7080,5100,1040),'Deps.dc.html':(1920,8240,2100,1360)}
titles={'Main.dc.html':'Posts','Post1Full.dc.html':'Part 1: generative UI','Post2Full.dc.html':'Part 2: remote interaction','Post3Full.dc.html':'Part 3: proof of concept','Diagrams.dc.html':'Diagrams','Videos.dc.html':'Videos and real board','Packages.dc.html':'Packaging','LiveRuns.dc.html':'AG-UI, MCP UI, A2UI running locally','TicTacToe.dc.html':'Tic-tac-toe test case','Hardened.dc.html':'Hardened HeyHuman','Sequences.dc.html':'Sequence diagrams','Deps.dc.html':'Dependencies'}
cj={"v":3,"createdOnFiles":{"v":1,"at":"2026-11-25T18:00:00Z"},"title":"HeyHuman and Generative UI: posts, diagrams and videos","launch":{"view":"canvas"},"pages":[],"boards":{k:{"x":x,"y":y,"w":w,"h":h,"title":titles[k]} for k,(x,y,w,h) in boards.items()},"order":list(boards),"notes":{"t":{"x":0,"y":-300,"text":"HeyHuman and Generative UI","kind":"title1","maxW":2000}},"designSystems":[]}
json.dump(cj,open('root/project/canvas.json','w'),indent=1)
print(list(F))
