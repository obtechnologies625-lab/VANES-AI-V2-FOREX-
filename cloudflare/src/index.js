import { callGemini } from "./gemini";

const FAVICON_SVG = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 200" role="img" aria-labelledby="vlT vlD"><title id="vlT">VANES AI logo</title><desc id="vlD">The VANES AI six turbine wheel beside the VANES AI wordmark and the line Versatile Adaptive Neuro Emergent System.</desc><defs><radialGradient id="vlBg" cx=".5" cy=".42" r=".9"><stop stop-color="#101a3a"/><stop offset=".7" stop-color="#050916"/><stop offset="1" stop-color="#02040c"/></radialGradient><linearGradient id="vlN" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#eaffff"/><stop offset=".28" stop-color="#27e9ff"/><stop offset=".66" stop-color="#7654ff"/><stop offset="1" stop-color="#ff2bd6"/></linearGradient><linearGradient id="vlRule" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#27e9ff"/><stop offset=".5" stop-color="#7654ff"/><stop offset="1" stop-color="#ff2bd6"/></linearGradient><filter id="vlG" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="4" result="x"/><feMerge><feMergeNode in="x"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><rect width="760" height="200" rx="34" fill="url(#vlBg)"/><g transform="translate(102 100) scale(.332)" filter="url(#vlG)"><circle r="206" fill="none" stroke="url(#vlN)" stroke-width="16"/><g stroke="#7fd8ff" stroke-width="6" opacity=".8"><path d="M0-206V-186" transform="rotate(30)"/><path d="M0-206V-186" transform="rotate(90)"/><path d="M0-206V-186" transform="rotate(150)"/><path d="M0-206V-186" transform="rotate(210)"/><path d="M0-206V-186" transform="rotate(270)"/><path d="M0-206V-186" transform="rotate(330)"/></g><g fill="url(#vlN)" stroke="#eaffff" stroke-width="7" stroke-linejoin="round"><path d="M-14-58 26-186 66-158 24-50Z"/><path d="M-14-58 26-186 66-158 24-50Z" transform="rotate(60)"/><path d="M-14-58 26-186 66-158 24-50Z" transform="rotate(120)"/><path d="M-14-58 26-186 66-158 24-50Z" transform="rotate(180)"/><path d="M-14-58 26-186 66-158 24-50Z" transform="rotate(240)"/><path d="M-14-58 26-186 66-158 24-50Z" transform="rotate(300)"/></g><circle r="74" fill="#070d20" stroke="url(#vlN)" stroke-width="16"/><circle r="42" fill="#101936" stroke="#d7fbff" stroke-width="6"/><circle r="19" fill="url(#vlN)"/></g><g font-family="'Segoe UI',Roboto,Arial,sans-serif"><text x="200" y="104" font-size="60" font-weight="900" letter-spacing="3" fill="#f3fbff">VANES <tspan fill="#27e9ff">AI</tspan></text><rect x="203" y="122" width="512" height="3" fill="url(#vlRule)"/><rect x="452" y="118.5" width="10" height="10" transform="rotate(45 457 123.5)" fill="#ff2bd6"/><text x="204" y="156" font-size="13" font-weight="700" letter-spacing="3.5" fill="#9eb2cf">VERSATILE ADAPTIVE NEURO EMERGENT SYSTEM</text></g></svg>`;

const DEFAULT_STATE = {
  symbol: "EURUSD",
  direction: "WAIT",
  confidence: 0,
  bid: 0,
  ask: 0,
  spread: 0,
  reason: "Cloud VANES is online. Connect a market-data source for live analysis.",
  stop_loss: 0,
  take_profit: 0,
  risk_gate: "WAITING",
  broker_ready: false,
  paper_balance: 10000,
  paper_daily_pnl: 0,
  paper_open_trades: 0,
  point_size: 0,
  updated_at: new Date().toISOString(),
};

const cors = (h) => ({
  ...h,
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
  "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
});

const json = (x, s = 200) =>
  new Response(JSON.stringify(x), {
    status: s,
    headers: cors({ "Content-Type": "application/json", "Cache-Control": "no-store" }),
  });

const num = (v, f = 0) => {
  const n = Number(v);
  return Number.isFinite(n) ? n : f;
};

const normalize = (s) => {
  const alerts = Array.isArray(s.alerts)
    ? s.alerts
        .slice(-10)
        .map((a) => ({
          kind: typeof a.kind === "string" ? a.kind.slice(0, 20) : "info",
          message: typeof a.message === "string" ? a.message.slice(0, 300) : "",
        }))
    : [];
  const trades = Array.isArray(s.paper_trades)
    ? s.paper_trades
        .slice(-20)
        .map((t) => ({
          direction: ["BUY", "SELL"].includes(t.direction) ? t.direction : "WAIT",
          entry: num(t.entry),
          stop_loss: num(t.stop_loss),
          take_profit: num(t.take_profit),
          size: Math.max(0, num(t.size)),
          opened_at: num(t.opened_at),
          closed_at: t.closed_at == null ? null : num(t.closed_at),
          exit_price: t.exit_price == null ? null : num(t.exit_price),
        }))
    : [];
  return {
    ...DEFAULT_STATE,
    ...s,
    symbol: typeof s.symbol === "string" && s.symbol.length <= 20 ? s.symbol : DEFAULT_STATE.symbol,
    direction: ["BUY", "SELL", "WAIT"].includes(s.direction) ? s.direction : "WAIT",
    confidence: Math.max(0, Math.min(1, num(s.confidence))),
    bid: num(s.bid),
    ask: num(s.ask),
    spread: num(s.spread),
    stop_loss: num(s.stop_loss),
    take_profit: num(s.take_profit),
    paper_balance: num(s.paper_balance, 10000),
    paper_daily_pnl: num(s.paper_daily_pnl),
    paper_open_trades: Math.max(0, Math.floor(num(s.paper_open_trades))),
    paper_trades: trades,
    alerts,
    point_size: num(s.point_size),
    broker_ready: s.broker_ready === true,
    risk_gate: typeof s.risk_gate === "string" && s.risk_gate.length <= 40 ? s.risk_gate : "WAITING",
    reason: typeof s.reason === "string" ? s.reason.slice(0, 500) : DEFAULT_STATE.reason,
    updated_at: typeof s.updated_at === "string" ? s.updated_at : DEFAULT_STATE.updated_at,
  };
};

const verifyJwt = (token, secret) => {
  try {
    const parts = token.split(".");
    if (parts.length !== 3) return null;
    const [headerB64, payloadB64, signatureB64] = parts;
    const data = `${headerB64}.${payloadB64}`;
    const expectedSig = await crypto.subtle.importKey(
      "raw",
      new TextEncoder().encode(secret),
      { name: "HMAC", hash: "SHA-256" },
      false,
      ["verify"]
    ).then((key) =>
      crypto.subtle.verify("HMAC", key, hexToUint8Array(signatureB64), new TextEncoder().encode(data))
    );
    if (!expectedSig) return null;
    const payload = JSON.parse(atou(payloadB64));
    if (payload.exp && Date.now() >= payload.exp * 1000) return null;
    return payload;
  } catch (_) {
    return null;
  }
};

const atou = (b64) => {
  const pad = b64.length % 4;
  const adjusted = pad ? b64.padEnd(b64.length + (4 - pad), "=") : b64;
  return new TextDecoder().decode(
    Uint8Array.from(atob(adjusted), (c) => c.charCodeAt(0))
  );
};

const hexToUint8Array = (hex) => {
  const bytes = new Uint8Array(Math.ceil(hex.length / 2));
  for (let i = 0; i < bytes.length; i++) bytes[i] = parseInt(hex.substr(i * 2, 2), 16);
  return bytes;
};

const reply = (m, s) => {
  m = String(m || "").toLowerCase();
  if (!m.trim())
    return "Ask VANES about status, quote, signal, risk, paper trading, or why it is waiting.";
  if (/status|overview|summary/.test(m))
    return (
      s.symbol +
      " is " +
      s.direction +
      " at " +
      (s.confidence * 100).toFixed(0) +
      "% confidence. " +
      s.reason
    );
  if (/quote|price|bid|ask|spread/.test(m))
    return (
      s.symbol +
      ": bid " +
      s.bid.toFixed(5) +
      ", ask " +
      s.ask.toFixed(5) +
      ", spread " +
      s.spread.toFixed(5) +
      "."
    );
  if (/signal|direction|setup/.test(m))
    return (
      "Guidance: " +
      s.direction +
      " (" +
      (s.confidence * 100).toFixed(0) +
      "% confidence). " +
      s.reason
    );
  if (/risk|stop|target|sl|tp/.test(m))
    return (
      "Risk gate: " +
      s.risk_gate +
      ". Reference SL " +
      s.stop_loss.toFixed(5) +
      ", TP " +
      s.take_profit.toFixed(5) +
      ". Broker ready: " +
      s.broker_ready +
      "."
    );
  if (/paper|balance|pnl/.test(m))
    return (
      "Paper balance: " +
      s.paper_balance.toFixed(2) +
      "; daily P/L: " +
      s.paper_daily_pnl.toFixed(2) +
      "; open trades: " +
      s.paper_open_trades +
      "."
    );
  if (/why|reason|wait|explain/.test(m))
    return "Current guidance is " + s.direction + ": " + s.reason;
  return "I can explain live state, quote, signal, risk, paper account, and WAIT reasons. I cannot place broker orders.";
};

const analyzeWithGemini = async (packet, env) => {
  const apiKey = env.VANES_GEMINI_API_KEY || "";
  if (!apiKey) {
    return { analysis: "Gemini API key not configured", sources: [] };
  }
  const parts = [
    { text: `You are VANES-AI, a forex intelligence assistant. Analyze this market packet and return JSON with fields: analysis (string), direction (BUY|SELL|WAIT), confidence (0-1), reason (string), sources (array of strings). Subscription tier: ${packet.subscription_tier}. Symbol: ${packet.symbol}. Bid: ${packet.bid}. Ask: ${packet.ask}. Spread: ${packet.spread}.` },
  ];
  if (packet.screen_frames && packet.screen_frames.length > 0) {
    const frame = packet.screen_frames[0];
    parts.push({
      inline_data: {
        mime_type: frame.format === "JPEG" ? "image/jpeg" : "image/png",
        data: frame.data,
      },
    });
  }
  if (packet.audio_chunks && packet.audio_chunks.length > 0) {
    parts.push({
      text: `Audio context: ${packet.audio_chunks.length} chunk(s) captured.`,
    });
  }
  try {
    const res = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=${apiKey}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{ parts }],
          generationConfig: {
            response_mime_type: "application/json",
            temperature: 0.2,
          },
        }),
      }
    );
    if (!res.ok) {
      const errText = await res.text();
      return { analysis: `Gemini error ${res.status}: ${errText.slice(0, 200)}`, sources: [] };
    }
    const data = await res.json();
    const text =
      data?.candidates?.[0]?.content?.parts?.[0]?.text ||
      data?.candidates?.[0]?.content?.parts?.[0]?.inline_data?.data ||
      "";
    if (!text) return { analysis: "Empty Gemini response", sources: [] };
    try {
      const parsed = JSON.parse(text);
      return {
        analysis: parsed.analysis || text,
        direction: parsed.direction || packet.direction,
        confidence: parsed.confidence ?? packet.confidence,
        reason: parsed.reason || packet.reason,
        sources: parsed.sources || [],
      };
    } catch (_) {
      return { analysis: text, sources: [] };
    }
  } catch (e) {
    return { analysis: `Gemini request failed: ${e.message}`, sources: [] };
  }
};

const page = () => `<!doctype html><meta charset=utf-8><link rel="icon" href="/favicon.svg" type="image/svg+xml"><meta name=viewport content='width=device-width,initial-scale=1'><title>VANES-AI V2</title><style>*{box-sizing:border-box}body{margin:0;background:#061019;color:#edf7f8;font:15px system-ui}main{max-width:1150px;margin:auto;padding:24px}.top{display:flex;justify-content:space-between;align-items:center}.brand{font-size:24px;font-weight:900}.tag{font-size:11px;letter-spacing:.15em;color:#7893a0}.live{color:#55e0b8;background:#0b2822;padding:8px 12px;border-radius:20px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:18px}.panel,.card{background:#0d1d28;border:1px solid #1c3948;border-radius:18px;padding:20px}.direction{font-size:64px;font-weight:900;margin:20px 0 4px}.confidence{color:#55e0b8;font-weight:800}.reason{color:#aec3ca;line-height:1.5;margin:15px 0}.metrics,.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}.metric{background:#08151e;padding:13px;border-radius:12px}.label{font-size:10px;color:#7893a0}.value{font-size:18px;font-weight:800;margin-top:4px}.chat{height:350px;overflow:auto;background:#08151e;border-radius:12px;padding:12px}.msg{padding:10px 12px;border-radius:12px;margin:8px 0;max-width:88%;white-space:pre-wrap}.bot{background:#132936}.user{background:#17433b;margin-left:auto}.form{display:flex;gap:8px;margin-top:10px}input{flex:1;padding:13px;border-radius:10px;border:1px solid #294858;background:#07131b;color:white}button{padding:11px 15px;border:0;border-radius:10px;background:#55e0b8;font-weight:900;cursor:pointer}.quick{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0}.quick button{background:#122632;color:#dcebef;border:1px solid #294858;font-weight:600}.chart-wrap{margin-top:16px}.chart{height:250px;width:100%;background:#08151e;border-radius:12px}.history{max-height:260px;overflow:auto;margin-top:10px}.row{display:grid;grid-template-columns:1fr 70px 80px 1.5fr;gap:8px;padding:9px;border-bottom:1px solid #17313d;font-size:13px}.pill{font-weight:800}.cards{grid-template-columns:repeat(3,1fr)}.error-banner{background:#2b1218;border:1px solid #5c2a35;color:#ffb3b8;padding:10px 12px;border-radius:10px;margin:8px 0}.overlay-alert{position:fixed;top:16px;left:50%;transform:translateX(-50%);background:rgba(13,29,40,0.95);border:1px solid #1c3948;color:#edf7f8;padding:10px 14px;border-radius:10px;font-size:13px;z-index:9999;pointer-events:none}.hidden{display:none}</style><script>function showAlert(t){const e=document.createElement('div');e.className='overlay-alert',e.textContent=t,document.body.appendChild(e),setTimeout(()=>e.remove(),4000)}function renderState(s){document.getElementById('v-direction').textContent=s.direction,document.getElementById('v-confidence').textContent=(s.confidence*100).toFixed(0)+'%',document.getElementById('v-reason').textContent=s.reason,document.getElementById('v-bid').textContent=s.bid.toFixed(5),document.getElementById('v-ask').textContent=s.ask.toFixed(5),document.getElementById('v-spread').textContent=s.spread.toFixed(5),document.getElementById('v-sl').textContent=s.stop_loss.toFixed(5),document.getElementById('v-tp').textContent=s.take_profit.toFixed(5),document.getElementById('v-risk').textContent=s.risk_gate,document.getElementById('v-paper').textContent='Paper: '+s.paper_balance.toFixed(2)+' / P/L: '+s.paper_daily_pnl.toFixed(2)}const es=new EventSource('/api/events');es.onmessage=(e)=>{const s=JSON.parse(e.data);renderState(s)};es.onerror=()=>{showAlert('Connection lost. Retrying...')}</script></head><body><main><div class=top><div><div class=brand>VANES-AI V2</div><div class=tag>REALTIME FOREX INTELLIGENCE</div></div><div class=live id='v-status'>Connecting</div></div><div class=grid><div class=panel><div class=direction id='v-direction'>WAIT</div><div class=confidence id='v-confidence'>0%</div><div class=reason id='v-reason'>Starting VANES</div><div class=metrics><div class=metric><div class=label>BID</div><div class=value id='v-bid'>—</div></div><div class=metric><div class=label>ASK</div><div class=value id='v-ask'>—</div></div><div class=metric><div class=label>SPREAD</div><div class=value id='v-spread'>—</div></div></div></div><div class=panel><div class=label>RISK PLAN</div><div class=value style='margin-top:6px' id='v-sl'>SL —</div><div class=value id='v-tp'>TP —</div><div class=value id='v-risk'>Gate —</div><div class=label style='margin-top:10px'>PAPER</div><div class=value id='v-paper'>—</div></div></div><div class=card><div class=label>COMMANDS</div><div class=quick><button onclick=send('status')>Status</button><button onclick=send('quote')>Quote</button><button onclick=send('signal')>Signal</button><button onclick=send('risk')>Risk</button><button onclick=send('paper')>Paper</button></div><div class=chat id='chat'><div class=msg bot>VANES is online. Ask about status, quote, signal, risk, or paper trading.</div></div><form class=form onsubmit='event.preventDefault();send(document.getElementById('m').value)'><input id=m placeholder='Ask VANES...'><button>Send</button></form></div><div class=chart-wrap><div class=chart id='chart'></div><div class=history id='history'></div></div></main><script>function send(m){const c=document.getElementById('chat'),x=document.createElement('div');x.className='msg user';x.textContent=m;c.appendChild(x);fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:m})}).then(r=>r.json()).then(d=>{const b=document.createElement('div');b.className='msg bot';b.textContent=d.text||d.error||'No reply';c.appendChild(b);c.scrollTop=c.scrollHeight}).catch(()=>{showAlert('Chat request failed')})}</script></body></html>`;

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS")
      return new Response(null, { headers: cors({}) });

    const url = new URL(request.url);

    if (url.pathname === "/" || url.pathname === "/chat")
      return new Response(page(), {
        headers: { "Content-Type": "text/html;charset=UTF-8" },
      });

    if (url.pathname === "/favicon.svg")
      return new Response(FAVICON_SVG, {
        headers: { "Content-Type": "image/svg+xml", "Cache-Control": "public, max-age=86400" },
      });

    let state = normalize(DEFAULT_STATE);
    if (env.VANES_STATE) {
      try {
        const x = await env.VANES_STATE.get("latest");
        if (x) state = normalize(JSON.parse(x));
      } catch (_) {}
    }

    if (url.pathname === "/api/state") return json(state);
    if (url.pathname === "/api/history") {
      if (!env.VANES_STATE) return json([]);
      try {
        const x = await env.VANES_STATE.get("history");
        return json(x ? JSON.parse(x) : []);
      } catch (_) {
        return json([]);
      }
    }
    if (url.pathname === "/api/health") {
      const age = (Date.now() - Date.parse(state.updated_at)) / 1000;
      const stale = !Number.isFinite(age) || age > 15 || state.bid <= 0;
      return json({
        status: "ok",
        service: "vanes-cloud",
        market_ready: !stale,
        stale,
        age_seconds: Number.isFinite(age) ? Math.max(0, Math.round(age)) : null,
      });
    }

    if (url.pathname === "/api/events") {
      const stream = new ReadableStream({
        async start(controller) {
          const encoder = new TextEncoder();
          const send = (data) => {
            controller.enqueue(encoder.encode(`data: ${JSON.stringify(data)}\n\n`));
          };
          send(state);
          const interval = setInterval(async () => {
            try {
              if (env.VANES_STATE) {
                const x = await env.VANES_STATE.get("latest");
                if (x) {
                  state = normalize(JSON.parse(x));
                  send(state);
                }
              }
            } catch (_) {}
          }, 1000);
          request.signal.addEventListener("close", () => clearInterval(interval));
        },
      });
      return new Response(stream, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-store",
          Connection: "keep-alive",
        },
      });
    }

    if (url.pathname === "/api/publish" && request.method === "POST") {
      if (!env.VANES_STATE)
        return json({ error: "State storage is not configured" }, 503);
      const expected = env.VANES_PUBLISH_TOKEN || "";
      const auth = request.headers.get("Authorization") || "";
      if (!expected || auth !== "Bearer " + expected)
        return json({ error: "Unauthorized" }, 401);
      try {
        const b = await request.json();
        const next = normalize(b);
        next.updated_at = new Date().toISOString();
        await env.VANES_STATE.put("latest", JSON.stringify(next), { expirationTtl: 120 });
        let old = [];
        try {
          const h = await env.VANES_STATE.get("history");
          old = h ? JSON.parse(h) : [];
        } catch (_) {}
        old = [
          {
            symbol: next.symbol,
            direction: next.direction,
            confidence: next.confidence,
            reason: next.reason,
            updated_at: next.updated_at,
          },
          ...old,
        ].slice(0, 50);
        await env.VANES_STATE.put("history", JSON.stringify(old), { expirationTtl: 604800 });
        return json({ ok: true, updated_at: next.updated_at, history_size: old.length });
      } catch (_) {
        return json({ error: "Invalid JSON" }, 400);
      }
    }

    if (url.pathname === "/api/chat" && request.method === "POST") {
      try {
        const b = await request.json();
        if (typeof b.message !== "string" || b.message.length > 1000)
          return json({ error: "Invalid message" }, 400);
        const replyText = reply(b.message, state);
        return json({ text: replyText, intent: "local" });
      } catch (_) {
        return json({ error: "Invalid JSON" }, 400);
      }
    }

    if (url.pathname === "/api/v1/analyze" && request.method === "POST") {
      const secret = env.VANES_JWT_SECRET || "";
      const authHeader = request.headers.get("Authorization") || "";
      const tierHeader = request.headers.get("X-Subscription-Tier") || "SERVER_B";
      if (!secret) return json({ error: "JWT not configured" }, 500);
      if (!authHeader.startsWith("Bearer ")) return json({ error: "Missing token" }, 401);
      const token = authHeader.slice(7);
      const payload = verifyJwt(token, secret);
      if (!payload) return json({ error: "Invalid or expired token" }, 401);
      if (payload.tier === "SERVER_A" && env.VANES_PAYWALL === "1") {
        return json({ error: "Payment required", paywall: true }, 402);
      }
      if (!["SERVER_A", "SERVER_B", "SERVER_C"].includes(payload.tier)) {
        return json({ error: "Unknown tier" }, 403);
      }
      try {
        const packet = await request.json();
        const result = await analyzeWithGemini(packet, env);
        const response = {
          ok: true,
          tier: payload.tier,
          analysis: result.analysis,
          direction: result.direction || packet.direction,
          confidence: result.confidence ?? packet.confidence,
          reason: result.reason || packet.reason,
          sources: result.sources || [],
          server_ts: new Date().toISOString(),
        };
        if (payload.tier === "SERVER_A") {
          response.order_dispatch = "READY";
          response.order_instructions = {
            symbol: packet.symbol,
            direction: result.direction || packet.direction,
            confidence: result.confidence ?? packet.confidence,
          };
        }
        if (payload.tier === "SERVER_C") {
          response.analysis = "Basic text-only analysis active. Upgrade for multimodal intelligence.";
        }
        return json(response);
      } catch (_) {
        return json({ error: "Invalid packet" }, 400);
      }
    }

    return json({ error: "Not found" }, 404);
  },
};
