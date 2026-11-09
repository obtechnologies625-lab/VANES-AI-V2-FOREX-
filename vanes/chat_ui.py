"""Embedded browser UI for the VANES realtime command center."""

# pylint: disable=line-too-long

from .theme import CSS_BASE, FONT_LINK, TRADEMARK_LINE


def html_page():
    """Return the self-contained VANES command center."""
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VANES-AI V2 | Command Center</title>
""" + FONT_LINK + """
<style>
""" + CSS_BASE + """
.wrap{max-width:1180px;margin:auto;padding:22px}.top{display:flex;align-items:center;justify-content:space-between;gap:15px;margin-bottom:18px}
.brand{display:flex;align-items:center;gap:12px}.orb{width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,var(--cyan),var(--violet) 55%,var(--magenta));box-shadow:0 0 26px var(--cyan),0 0 46px #9d00ff66;border:1px solid #ffffff22}
h1{font-size:22px;margin:0;letter-spacing:.08em;color:#fff;text-shadow:0 0 12px var(--cyan),0 0 30px #00fff055}.sub{color:var(--muted);font-size:11px;letter-spacing:.22em}
.live{border:1px solid #00fff055;background:#00fff012;color:var(--cyan);padding:8px 14px;border-radius:999px;font-size:12px;letter-spacing:.14em;box-shadow:0 0 18px #00fff033,inset 0 0 12px #00fff022}
.grid{display:grid;grid-template-columns:1.1fr .9fr;gap:16px}
.panel{background:var(--panelsoft);border:1px solid var(--line);border-radius:14px;box-shadow:0 0 0 1px #ffffff08,0 18px 50px #0009,inset 0 0 40px #00fff00a;overflow:hidden;backdrop-filter:blur(4px)}
.hero{padding:24px}.eyebrow{font-size:11px;letter-spacing:.24em;color:var(--magenta);text-transform:uppercase;text-shadow:0 0 12px #ff2bd666}
.direction{font-size:60px;font-weight:800;line-height:1;margin:10px 0;letter-spacing:.06em;color:#fff;text-shadow:0 0 16px var(--cyan),0 0 44px #00fff066}
.confidence{color:var(--ok);font-weight:700;letter-spacing:.1em;text-shadow:0 0 12px #00ffa355}.reason{color:#a9c6d6;line-height:1.55;margin-top:12px}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--line)}.metric{padding:15px;border-right:1px solid var(--line)}.metric:last-child{border:0}.label{font-size:10px;color:var(--muted);letter-spacing:.18em}.value{font-size:18px;font-weight:700;margin-top:5px;color:var(--cyan);text-shadow:0 0 10px #00fff044}
.chathead{padding:16px 18px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between;letter-spacing:.12em}.chathead b{color:#fff;text-shadow:0 0 12px var(--magenta)}.chat{height:430px;overflow:auto;padding:15px}
.msg{padding:11px 13px;border-radius:10px;margin:9px 0;max-width:90%;line-height:1.5;white-space:pre-wrap;border:1px solid}
.bot{background:#0e1b2e;border-color:#1e3a5f;box-shadow:inset 0 0 18px #00fff00d}.user{background:#1a0f24;margin-left:auto;border-color:#4a1f52;color:#ffd9f4;box-shadow:inset 0 0 18px #ff2bd614}
form{display:flex;gap:8px;padding:12px;border-top:1px solid var(--line)}
input{flex:1;background:#060b16;border:1px solid #23405f;color:var(--text);padding:13px;border-radius:8px;outline:none;font-family:var(--mono)}input:focus{border-color:var(--cyan);box-shadow:0 0 16px #00fff044}
button{background:linear-gradient(135deg,var(--cyan),#00b3ff);border:0;border-radius:8px;padding:0 20px;font-weight:800;cursor:pointer;color:#02121a;font-family:var(--mono);letter-spacing:.1em;box-shadow:0 0 18px #00fff055}button:hover{filter:brightness(1.15)}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:16px}
.card{padding:14px;background:var(--panelsoft);border:1px solid var(--line);border-radius:12px;box-shadow:inset 0 0 30px #9d00ff0d}.card b{display:block;margin-top:6px;color:#fff}.card .label{color:var(--magenta)}
.ok{color:var(--ok)!important;text-shadow:0 0 12px #00ffa355}.muted{color:var(--muted)}
.quick{display:flex;flex-wrap:wrap;gap:7px;padding:0 15px 14px}.quick button{background:#0d1830;color:var(--cyan);border:1px solid #22456b;padding:7px 11px;box-shadow:none;font-weight:600}
.footer{margin-top:15px;text-align:center;color:var(--muted);font-size:11px;letter-spacing:.14em}
@media(max-width:800px){.grid{grid-template-columns:1fr}.cards{grid-template-columns:repeat(2,1fr)}.direction{font-size:48px}}
</style></head>
<body><main class="wrap">
<header class="top"><div class="brand"><div class="orb"></div><div><h1>VANES-AI V2</h1><div class="sub">FOREX INTELLIGENCE • REALTIME COMMAND CENTER</div></div></div><div class="live" id="live">● CONNECTING</div></header>
<section class="grid">
<div class="panel"><div class="hero"><div class="eyebrow" id="symbol">MARKET</div><div class="direction" id="direction">WAIT</div><div class="confidence" id="confidence">0% confidence</div><div class="reason" id="reason">Waiting for live VANES state…</div></div>
<div class="metrics"><div class="metric"><div class="label">BID</div><div class="value" id="bid">—</div></div><div class="metric"><div class="label">ASK</div><div class="value" id="ask">—</div></div><div class="metric"><div class="label">SPREAD</div><div class="value" id="spread">—</div></div></div></div>
<div class="panel"><div class="chathead"><b>VANES CHAT</b><span class="muted">read-only intelligence</span></div><div id="chat" class="chat"></div><div class="quick"><button onclick="ask('status')">Status</button><button onclick="ask('signal')">Signal</button><button onclick="ask('risk')">Risk</button><button onclick="ask('why wait?')">Why?</button><button onclick="ask('indicators')">Indicators</button></div><form id="form"><input id="input" autocomplete="off" placeholder="Ask VANES anything about the current state…"><button>ASK</button></form></div>
</section>
<section class="cards">
<div class="card"><span class="label">RISK GATE</span><b id="risk">WAITING</b></div>
<div class="card"><span class="label">BROKER DATA</span><b id="broker">NOT READY</b></div>
<div class="card"><span class="label">PAPER BALANCE</span><b id="balance">—</b></div>
<div class="card"><span class="label">PAPER DAILY P/L</span><b id="pnl">—</b></div>
<div class="card"><span class="label">ML REGIME</span><b id="regime">—</b></div>
<div class="card"><span class="label">SENTIMENT</span><b id="sentiment">NEUTRAL</b></div>
<div class="card"><span class="label">TILT</span><b id="tilt">0</b></div>
<div class="card"><span class="label">EXEC SLIPPAGE</span><b id="slippage">—</b></div>
</section>
<div class="footer">VANES is an analytical observer. Chat cannot place broker orders.<br>""" + TRADEMARK_LINE + """</div>
</main>
<script>
const $=id=>document.getElementById(id),chat=$('chat');
function add(text,who='bot'){const d=document.createElement('div');d.className='msg '+who;d.textContent=text;chat.appendChild(d);chat.scrollTop=chat.scrollHeight}
function ask(v){$('input').value=v;$('form').requestSubmit()}
async function refresh(){try{const r=await fetch('/state',{cache:'no-store'});const s=await r.json();$('live').textContent='● LIVE';$('symbol').textContent=s.symbol||'MARKET';$('direction').textContent=s.direction||'WAIT';$('confidence').textContent=(Number(s.confidence||0)*100).toFixed(0)+'% confidence';$('reason').textContent=s.reason||'No explanation';$('bid').textContent=Number(s.bid||0).toFixed(5);$('ask').textContent=Number(s.ask||0).toFixed(5);$('spread').textContent=Number(s.spread||0).toFixed(5);$('risk').textContent=s.risk_gate||'WAITING';$('broker').textContent=s.broker_ready?'READY':'NOT READY';$('broker').className=s.broker_ready?'ok':'';$('balance').textContent=Number(s.paper_balance||0).toFixed(2);$('pnl').textContent=Number(s.paper_daily_pnl||0).toFixed(2);
const sent=s.sentiment||{};
$('regime').textContent=(s.ml_regime||'—')+(s.ml_prob?' '+((Number(s.ml_prob)||0)*100).toFixed(0)+'%':'');
$('sentiment').textContent=sent.label||'NEUTRAL';
$('tilt').textContent=String(s.tilt||0);
$('slippage').textContent=((s.execution_slices||[]).length? (s.execution_slices.length+' slices · '):'— ')+Number(s.est_slippage||0).toFixed(1)+' pts'}catch(e){$('live').textContent='● OFFLINE'}} 
$('form').addEventListener('submit',async e=>{e.preventDefault();const i=$('input'),v=i.value.trim();if(!v)return;i.value='';add(v,'user');try{const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:v})});const d=await r.json();add(d.text||d.error||'No response')}catch(e){add('VANES bridge is offline. Start the application and try again.')}})
add('VANES online. I can explain the live quote, signal, indicators, risk gate, paper account, and why the strategy is waiting.','bot');refresh();setInterval(refresh,1000)
</script></body></html>"""
