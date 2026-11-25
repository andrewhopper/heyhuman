import html
OR='#c85a00';INK='#1a1a1a';BG='#f5f0e6'
D={
'heyhuman':('HEYHUMAN: AGENT WRITES THE HTML, MQTT CARRIES THE ANSWER',['AGENT','CLOUD','PHONE'],[
(0,'WRITE THE FORM AS HTML',1),(0,'--start POSTS FORM + SESSION ID',0),(1,'LAMBDA STORES IT IN DYNAMODB, RETURNS URL',0),(0,'SHOW URL, --wait SUBSCRIBES TO MQTT',0),(2,'OPEN LINK, LAMBDA SERVES THE FORM',0),(2,'TAP decide(value)',0),(1,'/save, LAMBDA PUBLISHES TO IOT CORE',0),(0,'CLI PRINTS ANSWER, EXITS 0',0)],'ORANGE = WHERE THE UI COMES FROM'),
'mcpapps':('MCP APPS: SERVER DECLARES THE UI, HOST RENDERS IT IN A SANDBOX',['MCP SERVER','HOST (CLAUDE DESKTOP)','VIEW (IFRAME)'],[
(0,'TOOL POINTS AT A ui:// HTML RESOURCE',1),(1,'HOST CALLS THE TOOL',0),(1,'FETCHES ui:// VIA resources/read',0),(2,'RENDERED IN SANDBOXED IFRAME',0),(2,'GETS TOOL ARGS + RESULT, USER INTERACTS',0),(1,'JSON-RPC OVER postMessage',0),(0,'SERVER TOOL CALL OR CHAT MESSAGE',0)],'ORANGE = WHERE THE UI COMES FROM. CLAUDE CODE SHOWS TEXT ONLY.'),
'a2ui':('A2UI: AGENT SENDS JSON, CLIENT DRAWS FROM ITS CATALOG',['AGENT','CLIENT APP','USER'],[
(1,'CLIENT ADVERTISES ITS CATALOG',0),(0,'LLM COMPOSES A2UI JSON FROM THE CATALOG',1),(0,'SENDS IT OVER A2A OR AG-UI',0),(1,'VALIDATES AGAINST THE CATALOG',0),(1,'RENDERS NATIVE COMPONENTS',0),(2,'TAPS OR SELECTS',0),(1,'SENDS THE INTERACTION BACK',0),(0,'UPDATES THE UI INCREMENTALLY',0)],'ORANGE = WHERE THE UI COMES FROM'),
'agui':('AG-UI + COPILOTKIT: EVENT STREAM TO THE APP, INPUT BACK',['AGENT BACKEND','AG-UI TRANSPORT','FRONTEND APP','USER'],[
(2,'USER INPUT GOES TO THE AGENT',0),(0,'AGENT RUNS, EMITS STANDARD EVENTS',0),(1,'SSE, WEBSOCKET OR WEBHOOK',0),(2,'EVENTS BECOME CHAT, STATE, TOOL CALLS',0),(2,'RENDERS UI: A2UI, MCP APPS OR OWN COMPONENTS',1),(3,'APPROVES OR ANSWERS',0),(2,'SENDS THE INPUT BACK TO THE AGENT',0)],'ORANGE = WHERE THE UI COMES FROM. THE PROTOCOL LEAVES IT TO THE APP.'),
}
def wrap(t,n=19):
    ws=t.split();L=[];c=''
    for w in ws:
        if len(c)+len(w)+1>n and c:L.append(c);c=w
        else:c=(c+' '+w).strip()
    L.append(c);return L
for k,(title,lanes,steps,cap) in D.items():
    LW=190;CW=190;BW=170;BH=84;LH=150;top=100
    W=LW+CW*len(steps)+20;H=top+LH*len(lanes)+60
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}"><defs><marker id="a" markerUnits="userSpaceOnUse" markerWidth="12" markerHeight="10" refX="11" refY="5" orient="auto"><path d="M0 0L12 5L0 10z" fill="{INK}"/></marker></defs>',f'<rect width="{W}" height="{H}" fill="{BG}"/>',f'<text x="30" y="52" font-family="Comic Sans MS,Comic Neue,cursive" font-size="32" font-weight="700" fill="{INK}">{html.escape(title)}</text>']
    for i,l in enumerate(lanes):
        y=top+i*LH
        o.append(f'<rect x="20" y="{y}" width="{W-40}" height="{LH}" fill="none" stroke="{INK}" stroke-width="2.5" stroke-dasharray="2 0"/>')
        [o.append(f'<text x="{LW/2+10}" y="{y+LH/2-8+q*24}" text-anchor="middle" font-family="Comic Sans MS,cursive" font-size="18" font-weight="700" fill="{INK}">{html.escape(w)}</text>') for q,w in enumerate(wrap(l,13))]
    pos=[]
    for j,(ln,t,acc) in enumerate(steps):
        x=LW+j*CW+(CW-BW)/2;y=top+ln*LH+(LH-BH)/2;pos.append((x,y))
        c=OR if acc else INK
        o.append(f'<rect x="{x}" y="{y}" width="{BW}" height="{BH}" rx="12" fill="{"#fbe7d6" if acc else "#fffdf7"}" stroke="{c}" stroke-width="3"/>')
        L=wrap(t);y0=y+BH/2-(len(L)-1)*9+5
        for q,line in enumerate(L):o.append(f'<text x="{x+BW/2}" y="{y0+q*18}" text-anchor="middle" font-family="Comic Sans MS,cursive" font-size="14" font-weight="700" fill="{c}">{html.escape(line)}</text>')
        o.append(f'<text x="{x+10}" y="{y-6}" font-family="Comic Sans MS,cursive" font-size="14" fill="{INK}">{j+1}</text>')
    for j in range(len(steps)-1):
        (x1,y1),(x2,y2)=pos[j],pos[j+1]
        if y1==y2:o.append(f'<path d="M{x1+BW} {y1+BH/2} H{x2}" stroke="{INK}" stroke-width="3" fill="none" marker-end="url(#a)"/>')
        else:
            xm=x1+BW+(x2-x1-BW)/2
            o.append(f'<path d="M{x1+BW} {y1+BH/2} H{xm} V{y2+BH/2} H{x2}" stroke="{INK}" stroke-width="3" fill="none" marker-end="url(#a)"/>')
    o.append(f'<text x="30" y="{H-22}" font-family="Comic Sans MS,cursive" font-size="20" font-weight="700" fill="{OR}">{html.escape(cap)}</text></svg>')
    open(f'swim-{k}.svg','w').write('\n'.join(o))
    open(f'{k}.html','w').write(f'<body style="margin:0">'+'\n'.join(o))
    print(k,W,H)
