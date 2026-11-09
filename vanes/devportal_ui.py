"""Cyberpunk developer portal to test every VANES subsystem in one place."""

# pylint: disable=line-too-long

from .theme import CSS_BASE, DEVELOPER_EMAIL, FONT_LINK, TRADEMARK_LINE


def devportal_page():
    """Return the self-contained VANES developer testing portal."""
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VANES-AI V2 | Developer Portal</title>
""" + FONT_LINK + """
<style>
""" + CSS_BASE + """
.wrap{max-width:1080px;margin:auto;padding:22px}
.top{display:flex;align-items:center;justify-content:space-between;gap:14px;margin-bottom:16px;flex-wrap:wrap}
.brand{font-size:24px;font-weight:900;letter-spacing:.08em;color:#fff;text-shadow:0 0 12px var(--cyan),0 0 30px #00fff055}.brand .bolt{color:var(--gold);text-shadow:0 0 14px var(--gold)}
.tag{color:var(--muted);font-size:11px;letter-spacing:.2em}
.badge{background:#0d1830;border:1px solid #22456b;border-radius:999px;padding:7px 15px;font-size:11px;letter-spacing:.12em;color:var(--cyan);box-shadow:0 0 18px #00fff022}
.badge b{color:var(--gold)}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.panel{background:var(--panelsoft);border:1px solid var(--line);border-radius:14px;padding:20px;box-shadow:0 0 0 1px #ffffff08,0 18px 50px #0009,inset 0 0 40px #9d00ff0a;backdrop-filter:blur(4px)}
h2{font-size:14px;margin:0 0 14px;letter-spacing:.14em;color:var(--magenta);text-transform:uppercase;text-shadow:0 0 12px #ff2bd655}
table{width:100%;border-collapse:collapse;font-size:13px}
td,th{text-align:left;padding:9px 8px;border-bottom:1px solid var(--line);vertical-align:middle}
th{color:var(--muted);font-size:11px;letter-spacing:.12em;text-transform:uppercase}
.pill{font-size:11px;font-weight:800;letter-spacing:.1em;padding:3px 10px;border-radius:999px}
.on{background:#06251c;color:var(--ok);box-shadow:0 0 12px #00ffa344}
.off{background:#25101a;color:var(--err);box-shadow:0 0 12px #ff3b6b44}
.muted{color:var(--muted);font-size:12px}
button{background:linear-gradient(135deg,var(--cyan),#00b3ff);border:0;border-radius:8px;padding:11px 18px;font-weight:800;cursor:pointer;margin:6px 6px 0 0;color:#02121a;font-family:var(--mono);letter-spacing:.1em;box-shadow:0 0 18px #00fff055}button:hover{filter:brightness(1.15)}
button.ghost{background:#0d1830;color:var(--cyan);border:1px solid #22456b;box-shadow:none}
pre{background:#050a14;border:1px solid var(--line);border-radius:10px;padding:13px;font-size:12px;overflow:auto;max-height:280px;color:var(--text);white-space:pre-wrap;word-break:break-word}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.tm{margin-top:18px;text-align:center;color:var(--muted);font-size:11px;letter-spacing:.16em}
.tm b{color:var(--cyan)}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
</style></head>
<body><main class="wrap">
<header class="top">
<div><div class="brand"><span class="bolt">⚡</span> VANES-AI V2</div><div class="tag">DEVELOPER PORTAL • TEST EVERYTHING</div></div>
<div class="badge">DEVELOPER <b>""" + DEVELOPER_EMAIL + """</b></div>
</header>
<section class="grid">
<div class="panel"><h2>Required APIs &amp; keys</h2>
<div class="row" style="margin-bottom:10px"><button class="ghost" onclick="loadEnv()">↻ Refresh</button></div>
<table><tbody id="env"></tbody></table>
<div class="muted" id="envNote" style="margin-top:10px"></div></div>
<div class="panel"><h2>Offline self-tests</h2>
<div class="row" style="margin-bottom:10px"><button onclick="runSelftest()">▶ Run all checks</button><span class="tag" id="testSummary"></span></div>
<table><tbody id="tests"></tbody></table></div>
</section>
<section class="panel" style="margin-top:16px"><h2>Live endpoint tester</h2>
<div class="row">
<button class="ghost" onclick="hit('/state')">GET /state</button>
<button class="ghost" onclick="hit('/health')">GET /health</button>
<button class="ghost" onclick="hit('/api/strategies')">GET /api/strategies</button>
<button class="ghost" onclick="hit('/api/sellers')">GET /api/sellers</button>
<button class="ghost" onclick="chatPing()">POST /chat</button>
<button class="ghost" onclick="hit('/api/dev/env')">GET /api/dev/env</button>
</div>
<pre id="out">Pick an endpoint to fire a live request against the running bridge…</pre></section>
<div class="tm"><b>""" + TRADEMARK_LINE + """</b> &nbsp;•&nbsp; Developer access: """ + DEVELOPER_EMAIL + """</div>
</main>
<script>
const $=id=>document.getElementById(id);
const ENV_LABELS={metatrader5:'MetaTrader 5 package',gemini_api_key:'Gemini API key (VANES_GEMINI_API_KEY)',cloudflare_api_token:'Cloudflare token (CLOUDFLARE_API_TOKEN)',jwt_secret:'JWT secret (VANES_JWT_SECRET)',publish_token:'Publish token (VANES_PUBLISH_TOKEN)',kv_namespace_created:'Cloudflare KV namespace',local_bridge:'Local HTTP bridge'};
function pill(ok){return '<span class="pill '+(ok?'on':'off')+'">'+(ok?'READY':'MISSING')+'</span>'}
async function loadEnv(){try{const r=await fetch('/api/dev/env',{cache:'no-store'});const d=await r.json();
$('env').innerHTML=Object.keys(ENV_LABELS).map(k=>'<tr><td>'+ENV_LABELS[k]+'</td><td>'+pill(d[k])+'</td></tr>').join('');
const missing=Object.keys(ENV_LABELS).filter(k=>!d[k]);
$('envNote').textContent=missing.length?'Not configured yet: '+missing.map(k=>ENV_LABELS[k]).join(', ')+'. Local self-tests still run without these.':'All external dependencies detected.'}catch(e){$('env').innerHTML='<tr><td class="muted">Bridge offline — start VANES first.</td></tr>'}}
async function runSelftest(){try{$('testSummary').textContent='running…';const r=await fetch('/api/dev/selftest',{cache:'no-store'});const list=await r.json();
const pass=list.filter(t=>t.ok).length;
$('testSummary').textContent=pass+'/'+list.length+' passed';
$('tests').innerHTML=list.map(t=>'<tr><td>'+esc(t.name)+'</td><td>'+pill(t.ok)+'</td><td class="muted">'+esc(t.detail)+'</td></tr>').join('')}catch(e){$('tests').innerHTML='<tr><td class="muted">Self-test unavailable — bridge offline.</td></tr>';$('testSummary').textContent=''}}
async function hit(url){try{const r=await fetch(url,{cache:'no-store'});const d=await r.json();$('out').textContent=url+' → '+r.status+'\\n'+JSON.stringify(d,null,2)}catch(e){$('out').textContent=url+' → error: '+e}}
async function chatPing(){try{const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:'status'})});const d=await r.json();$('out').textContent='POST /chat → '+r.status+'\\n'+JSON.stringify(d,null,2)}catch(e){$('out').textContent='POST /chat → error: '+e}}
function esc(t){const d=document.createElement('div');d.textContent=t==null?'':String(t);return d.innerHTML}
loadEnv();runSelftest();
</script></body></html>"""
