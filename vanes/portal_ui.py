"""Embedded browser portal where forex pros register and sell strategies."""

# pylint: disable=line-too-long

from .theme import CSS_BASE, FONT_LINK


def portal_page():
    """Return the self-contained VANES strategy marketplace portal."""
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VANES-AI V2 | Strategy Marketplace</title>
""" + FONT_LINK + """
<style>
""" + CSS_BASE + """
.wrap{max-width:1080px;margin:auto;padding:22px}
.top{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:18px}
.brand{font-size:24px;font-weight:900;letter-spacing:.08em;color:#fff;text-shadow:0 0 12px var(--cyan),0 0 30px #00fff055}.brand .bolt{color:var(--gold);text-shadow:0 0 14px var(--gold)}
.tag{color:var(--muted);font-size:11px;letter-spacing:.2em}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.panel{background:var(--panelsoft);border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:0 0 0 1px #ffffff08,0 18px 50px #0009,inset 0 0 40px #9d00ff0a;backdrop-filter:blur(4px)}
h2{font-size:14px;margin:0 0 12px;letter-spacing:.14em;color:var(--magenta);text-transform:uppercase;text-shadow:0 0 12px #ff2bd655}
label{display:block;font-size:11px;color:var(--muted);margin:11px 0 4px;letter-spacing:.12em}
input,textarea,select{width:100%;background:#060b16;border:1px solid #23405f;color:var(--text);padding:11px;border-radius:8px;outline:none;font-family:var(--mono)}
input:focus,textarea:focus,select:focus{border-color:var(--cyan);box-shadow:0 0 16px #00fff044}
textarea{min-height:84px;resize:vertical}
button{background:linear-gradient(135deg,var(--cyan),#00b3ff);border:0;border-radius:8px;padding:11px 18px;font-weight:800;cursor:pointer;margin-top:12px;color:#02121a;font-family:var(--mono);letter-spacing:.1em;box-shadow:0 0 18px #00fff055}button:hover{filter:brightness(1.15)}
button.ghost{background:#0d1830;color:var(--cyan);border:1px solid #22456b;box-shadow:none}
.msg{margin-top:10px;font-size:13px;min-height:18px;letter-spacing:.04em}
.ok{color:var(--ok);text-shadow:0 0 10px #00ffa344}.err{color:var(--err);text-shadow:0 0 10px #ff3b6b44}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px;margin-top:8px}
.card{background:var(--panelsoft);border:1px solid var(--line);border-radius:12px;padding:14px;box-shadow:inset 0 0 30px #00fff00a;transition:.18s}.card:hover{border-color:var(--cyan);box-shadow:0 0 22px #00fff033,inset 0 0 30px #00fff00d;transform:translateY(-2px)}
.card b{display:block;font-size:15px;color:#fff;text-shadow:0 0 10px #00fff033}.card .meta{color:var(--muted);font-size:12px;margin-top:6px}
.price{color:var(--gold);font-weight:800;text-shadow:0 0 12px #f7ff5e44}
.note{background:#1a1206;border:1px solid #5c4a1a;color:var(--gold);padding:11px 13px;border-radius:10px;font-size:12px;margin-bottom:14px;box-shadow:inset 0 0 24px #f7ff5e0d;letter-spacing:.04em}
.empty{color:var(--muted);font-size:13px;letter-spacing:.08em}
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
