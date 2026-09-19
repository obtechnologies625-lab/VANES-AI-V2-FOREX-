"""Embedded browser UI for the VANES realtime command center."""

# pylint: disable=line-too-long


def html_page():
    """Return the self-contained VANES command center."""
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VANES-AI V2 | Command Center</title>
<style>
:root{color-scheme:dark;--bg:#071018;--panel:#0d1b26;--line:#1b3545;--text:#eaf4f7;--muted:#7f9aa8;--accent:#53e0b5;--warn:#ffcc66}
*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,-apple-system,sans-serif;background:radial-gradient(circle at 20% 0,#102b39 0,#071018 45%);color:var(--text)}
.wrap{max-width:1180px;margin:auto;padding:22px}.top{display:flex;align-items:center;justify-content:space-between;gap:15px;margin-bottom:18px}
.brand{display:flex;align-items:center;gap:12px}.orb{width:42px;height:42px;border-radius:14px;background:linear-gradient(135deg,#53e0b5,#3874ff);box-shadow:0 0 35px #53e0b533}
h1{font-size:20px;margin:0}.sub{color:var(--muted);font-size:12px}.live{border:1px solid #275c50;background:#0b251f;color:var(--accent);padding:8px 12px;border-radius:999px;font-size:12px}
.grid{display:grid;grid-template-columns:1.1fr .9fr;gap:16px}.panel{background:#0d1b26dd;border:1px solid var(--line);border-radius:18px;box-shadow:0 12px 40px #0004;overflow:hidden}
.hero{padding:24px}.eyebrow{font-size:11px;letter-spacing:.14em;color:var(--muted);text-transform:uppercase}.direction{font-size:58px;font-weight:800;line-height:1;margin:9px 0}.confidence{color:var(--accent);font-weight:700}.reason{color:#b8cbd3;line-height:1.5;margin-top:12px}
.metrics{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--line)}.metric{padding:15px;border-right:1px solid var(--line)}.metric:last-child{border:0}.label{font-size:11px;color:var(--muted)}.value{font-size:18px;font-weight:700;margin-top:4px}
.chathead{padding:16px 18px;border-bottom:1px solid var(--line);display:flex;justify-content:space-between}.chat{height:430px;overflow:auto;padding:15px}.msg{padding:11px 13px;border-radius:14px;margin:9px 0;max-width:90%;line-height:1.45;white-space:pre-wrap}.bot{background:#132936;border:1px solid #214454}.user{background:#173d37;margin-left:auto;border:1px solid #245d52}
form{display:flex;gap:8px;padding:12px;border-top:1px solid var(--line)}input{flex:1;background:#07131b;border:1px solid #284352;color:var(--text);padding:13px;border-radius:12px;outline:none}input:focus{border-color:var(--accent)}button{background:var(--accent);border:0;border-radius:12px;padding:0 19px;font-weight:800;cursor:pointer}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:16px}.card{padding:14px;background:#0d1b26;border:1px solid var(--line);border-radius:14px}.card b{display:block;margin-top:5px}.ok{color:var(--accent)}.muted{color:var(--muted)}
.quick{display:flex;flex-wrap:wrap;gap:7px;padding:0 15px 14px}.quick button{background:#122631;color:#cde0e6;border:1px solid #254655;padding:7px 10px}
.footer{margin-top:15px;text-align:center;color:#64808d;font-size:11px}
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
</section>
<div class="footer">VANES is an analytical observer. Chat cannot place broker orders.</div>
</main>
<script>
const $=id=>document.getElementById(id),chat=$('chat');
function add(text,who='bot'){const d=document.createElement('div');d.className='msg '+who;d.textContent=text;chat.appendChild(d);chat.scrollTop=chat.scrollHeight}
function ask(v){$('input').value=v;$('form').requestSubmit()}
async function refresh(){try{const r=await fetch('/state',{cache:'no-store'});const s=await r.json();$('live').textContent='● LIVE';$('symbol').textContent=s.symbol||'MARKET';$('direction').textContent=s.direction||'WAIT';$('confidence').textContent=(Number(s.confidence||0)*100).toFixed(0)+'% confidence';$('reason').textContent=s.reason||'No explanation';$('bid').textContent=Number(s.bid||0).toFixed(5);$('ask').textContent=Number(s.ask||0).toFixed(5);$('spread').textContent=Number(s.spread||0).toFixed(5);$('risk').textContent=s.risk_gate||'WAITING';$('broker').textContent=s.broker_ready?'READY':'NOT READY';$('broker').className=s.broker_ready?'ok':'';$('balance').textContent=Number(s.paper_balance||0).toFixed(2);$('pnl').textContent=Number(s.paper_daily_pnl||0).toFixed(2)}catch(e){$('live').textContent='● OFFLINE'}} 
$('form').addEventListener('submit',async e=>{e.preventDefault();const i=$('input'),v=i.value.trim();if(!v)return;i.value='';add(v,'user');try{const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:v})});const d=await r.json();add(d.text||d.error||'No response')}catch(e){add('VANES bridge is offline. Start the application and try again.')}})
add('VANES online. I can explain the live quote, signal, indicators, risk gate, paper account, and why the strategy is waiting.','bot');refresh();setInterval(refresh,1000)
</script></body></html>"""
