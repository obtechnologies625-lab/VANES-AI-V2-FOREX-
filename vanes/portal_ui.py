"""Embedded browser portal where forex pros register and sell strategies."""

# pylint: disable=line-too-long


def portal_page():
    """Return the self-contained VANES strategy marketplace portal."""
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VANES-AI V2 | Strategy Marketplace</title>
<style>
:root{color-scheme:dark;--bg:#071018;--panel:#0d1b26;--line:#1b3545;--text:#eaf4f7;--muted:#7f9aa8;--accent:#53e0b5;--gold:#ffd84d}
*{box-sizing:border-box}body{margin:0;font-family:Inter,system-ui,sans-serif;background:radial-gradient(circle at 20% 0,#102b39 0,#071018 45%);color:var(--text)}
.wrap{max-width:1080px;margin:auto;padding:22px}
.top{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:18px}
.brand{font-size:22px;font-weight:900}.brand .bolt{color:var(--gold)}
.tag{color:var(--muted);font-size:12px;letter-spacing:.12em}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.panel{background:#0d1b26dd;border:1px solid var(--line);border-radius:18px;padding:20px}
h2{font-size:15px;margin:0 0 12px;letter-spacing:.06em;color:var(--accent);text-transform:uppercase}
label{display:block;font-size:12px;color:var(--muted);margin:10px 0 4px}
input,textarea,select{width:100%;background:#07131b;border:1px solid #284352;color:var(--text);padding:11px;border-radius:10px;outline:none;font:inherit}
textarea{min-height:84px;resize:vertical}
button{background:var(--accent);border:0;border-radius:10px;padding:11px 16px;font-weight:800;cursor:pointer;margin-top:12px}
button.ghost{background:#122631;color:#cde0e6;border:1px solid #254655}
.msg{margin-top:10px;font-size:13px;min-height:18px}
.ok{color:var(--accent)}.err{color:#ffb3b8}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin-top:8px}
.card{background:#0d1b26;border:1px solid var(--line);border-radius:14px;padding:14px}
.card b{display:block;font-size:15px}.card .meta{color:var(--muted);font-size:12px;margin-top:6px}
.price{color:var(--gold);font-weight:800}
.note{background:#2b2412;border:1px solid #5c4a2a;color:#ffd84d;padding:10px 12px;border-radius:10px;font-size:12px;margin-bottom:14px}
.empty{color:var(--muted);font-size:13px}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
</style></head>
<body><main class="wrap">
<header class="top"><div><div class="brand"><span class="bolt">⚡</span> VANES-AI V2</div><div class="tag">STRATEGY MARKETPLACE • SELL YOUR EDGE</div></div><div class="tag" id="count"></div></header>
<div class="note">Payments are in preview: listings show “contact for pricing”. No card processor is connected yet — buyers reach sellers directly through VANES.</div>
<section class="grid">
<div class="panel"><h2>1 · Register as a Forex Pro</h2>
<label>Handle</label><input id="handle" placeholder="e.g. pipmaster" maxlength="24">
<label>Full name</label><input id="name" placeholder="Jane Doe" maxlength="60">
<label>Email</label><input id="email" type="email" placeholder="you@example.com">
<label>Short bio</label><textarea id="bio" placeholder="Track record, markets, style…" maxlength="500"></textarea>
<button onclick="register()">Register</button><div class="msg" id="regMsg"></div></div>
<div class="panel"><h2>2 · List a Strategy</h2>
<label>Seller ID</label><input id="sellerId" placeholder="sel-… (from registration)">
<label>Title</label><input id="title" placeholder="London Breakout Scalper" maxlength="80">
<label>Description</label><textarea id="desc" placeholder="Rules, session, instruments, risk per trade…" maxlength="2000"></textarea>
<label>Price (USD, 0 = free)</label><input id="price" type="number" min="0" step="1" value="99">
<label>Risk level</label><select id="risk"><option>low</option><option selected>medium</option><option>high</option></select>
<label>Timeframe</label><select id="tf"><option>M5</option><option>M15</option><option selected>M15</option><option>H1</option><option>H4</option></select>
<button onclick="submitStrategy()">List strategy</button><div class="msg" id="strMsg"></div></div>
</section>
<section class="panel" style="margin-top:16px"><h2>Live listings</h2><div class="cards" id="listings"></div><div class="empty" id="empty">No strategies listed yet. Be the first pro to publish.</div></section>
</main>
<script>
const $=id=>document.getElementById(id);
function show(id,text,ok){const e=$(id);e.textContent=text;e.className='msg '+(ok?'ok':'err')}
async function post(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});return r.json()}
async function register(){try{const d=await post('/api/sellers/register',{handle:$('handle').value,name:$('name').value,email:$('email').value,bio:$('bio').value});
if(d.ok){show('regMsg',d.message+' Seller ID: '+d.seller.seller_id,true);$('sellerId').value=d.seller.seller_id;load()}else show('regMsg',d.error,false)}catch(e){show('regMsg','Portal offline. Start VANES first.',false)}}
async function submitStrategy(){try{const d=await post('/api/strategies',{seller_id:$('sellerId').value,title:$('title').value,description:$('desc').value,price:Number($('price').value||0),risk_level:$('risk').value,timeframe:$('tf').value});
if(d.ok){show('strMsg',d.message,true);load()}else show('strMsg',d.error,false)}catch(e){show('strMsg','Portal offline. Start VANES first.',false)}}
async function load(){try{const r=await fetch('/api/strategies',{cache:'no-store'});const list=await r.json();
$('count').textContent=list.length+' listing'+(list.length===1?'':'s');
$('empty').style.display=list.length?'none':'block';
$('listings').innerHTML=list.map(s=>'<div class="card"><b>'+esc(s.title)+'</b><div class="meta">'+esc(s.timeframe)+' • risk '+esc(s.risk_level)+'</div><div class="meta">'+esc(s.description.slice(0,120))+'</div><div class="meta price">'+(s.price>0?'$'+s.price+' — contact for pricing':'FREE')+'</div></div>').join('')}catch(e){}}
function esc(t){const d=document.createElement('div');d.textContent=t==null?'':String(t);return d.innerHTML}
load();
</script></body></html>"""
