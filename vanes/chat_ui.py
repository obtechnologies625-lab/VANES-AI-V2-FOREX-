"""Embedded browser UI for the VANES realtime chatbot."""

# pylint: disable=line-too-long

def html_page():
    """Return the self-contained chat application."""
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VANES-AI V2 • Realtime Chat</title>
<style>
body{font-family:system-ui,sans-serif;max-width:900px;margin:0 auto;padding:20px;background:#111;color:#eee}
header{display:flex;justify-content:space-between;align-items:center}#state{font-size:.9rem;opacity:.8}
#chat{height:65vh;overflow:auto;border:1px solid #444;border-radius:12px;padding:14px;background:#181818}
.msg{margin:10px 0;padding:10px 12px;border-radius:10px;white-space:pre-wrap}.user{background:#26384d;margin-left:15%}.bot{background:#252525;margin-right:15%}
form{display:flex;gap:8px;margin-top:12px}input{flex:1;padding:12px;border-radius:8px;border:1px solid #555;background:#222;color:#fff}button{padding:12px 16px;border:0;border-radius:8px}
small{opacity:.65}
</style></head><body>
<header><h1>VANES-AI V2</h1><div id="state">Connecting…</div></header><div id="chat"></div>
<form id="form"><input id="input" autocomplete="off" placeholder="Ask VANES: What's the signal?"><button>Send</button></form>
<small>Realtime market observer • paper/read-only • no broker orders</small>
<script>
const chat=document.getElementById('chat'),stateEl=document.getElementById('state');
function add(text,cls){const d=document.createElement('div');d.className='msg '+cls;d.textContent=text;chat.appendChild(d);chat.scrollTop=chat.scrollHeight;}
async function refresh(){try{const r=await fetch('/state',{cache:'no-store'}),s=await r.json();stateEl.textContent=(s.symbol||'VANES')+' • '+s.direction+' • '+Number(s.confidence||0).toFixed(0)+'% • '+s.risk_gate;}catch(e){stateEl.textContent='Bridge unavailable';}}
async function send(message){add(message,'user');const r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message})});const data=await r.json();add(data.text||data.error||'No response','bot');}
document.getElementById('form').addEventListener('submit',e=>{e.preventDefault();const i=document.getElementById('input'),v=i.value.trim();if(v){i.value='';send(v);}});
add('VANES online. Ask about the live quote, signal, risk, paper account, or why the strategy is waiting.','bot');refresh();setInterval(refresh,1000);
</script></body></html>"""
