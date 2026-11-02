import { test } from "node:test";
import assert from "node:assert/strict";
import worker from "../src/index.js";

const SECRET = "vanes-test-secret-key-32-bytes-min";

function mockKV() {
  const store = new Map();
  return {
    async get(key) {
      return store.has(key) ? store.get(key) : null;
    },
    async put(key, value) {
      store.set(key, String(value));
    },
    _store: store,
  };
}

function makeEnv(overrides = {}) {
  return {
    VANES_STATE: mockKV(),
    VANES_JWT_SECRET: SECRET,
    VANES_PAYWALL: "0",
    ...overrides,
  };
}

function call(path, opts = {}, env = makeEnv()) {
  return worker.fetch(new Request("http://test.local" + path, opts), env);
}

function postJson(path, body, { env, headers } = {}) {
  return call(
    path,
    {
      method: "POST",
      headers: { "Content-Type": "application/json", ...headers },
      body: JSON.stringify(body),
    },
    env
  );
}

const b64u = (buf) => Buffer.from(buf).toString("base64url");

async function signJwt(payload, secret = SECRET) {
  const enc = new TextEncoder();
  const head = b64u(JSON.stringify({ alg: "HS256", typ: "JWT" }));
  const body = b64u(JSON.stringify(payload));
  const data = `${head}.${body}`;
  const key = await crypto.subtle.importKey(
    "raw",
    enc.encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"]
  );
  const sig = await crypto.subtle.sign("HMAC", key, enc.encode(data));
  return `${data}.${Buffer.from(sig).toString("base64url")}`;
}

const future = () => Math.floor(Date.now() / 1000) + 3600;

test("GET / serves the dashboard with the company brand", async () => {
  const res = await call("/");
  assert.equal(res.status, 200);
  assert.match(res.headers.get("content-type"), /text\/html/);
  const html = await res.text();
  assert.ok(html.includes("/brand.svg"), "page references the brand logo");
  assert.ok(html.includes("VANES AI"), "page carries the VANES AI alt text");
});

test("GET /brand.svg serves the canonical logo", async () => {
  const res = await call("/brand.svg");
  assert.equal(res.status, 200);
  assert.match(res.headers.get("content-type"), /image\/svg\+xml/);
  const svg = await res.text();
  assert.ok(svg.includes("VANES") && svg.includes("turbine wheel"));
});

test("GET /favicon.svg serves an icon", async () => {
  const res = await call("/favicon.svg");
  assert.equal(res.status, 200);
  assert.match(res.headers.get("content-type"), /image\/svg\+xml/);
});

test("GET /portal serves the marketplace with the brand", async () => {
  const res = await call("/portal");
  assert.equal(res.status, 200);
  const html = await res.text();
  assert.ok(html.includes("Strategy Marketplace"));
  assert.ok(html.includes("/brand.svg"));
});

test("GET /api/health and /api/state respond", async () => {
  const health = await (await call("/api/health")).json();
  assert.equal(health.status, "ok");
  const state = await (await call("/api/state")).json();
  assert.equal(state.symbol, "EURUSD");
});

test("OPTIONS returns CORS headers", async () => {
  const res = await call("/api/state", { method: "OPTIONS" });
  assert.equal(res.headers.get("Access-Control-Allow-Origin"), "*");
});

test("unknown route returns 404", async () => {
  const res = await call("/nope");
  assert.equal(res.status, 404);
});

test("seller registration: valid, bad handle, bad email, duplicate", async () => {
  const env = makeEnv();
  const good = await (
    await postJson(
      "/api/sellers/register",
      { handle: "pro_trader", name: "Pro", email: "pro@x.com", bio: "bio" },
      { env }
    )
  ).json();
  assert.equal(good.ok, true);
  assert.ok(good.seller.seller_id.startsWith("sel-"));

  const badHandle = await postJson(
    "/api/sellers/register",
    { handle: "x", name: "Pro", email: "a@b.com" },
    { env }
  );
  assert.equal(badHandle.status, 400);

  const badEmail = await postJson(
    "/api/sellers/register",
    { handle: "valid_one", name: "Pro", email: "not-an-email" },
    { env }
  );
  assert.equal(badEmail.status, 400);

  const dup = await postJson(
    "/api/sellers/register",
    { handle: "pro_trader", name: "Other", email: "other@x.com" },
    { env }
  );
  assert.equal(dup.status, 400);
  assert.equal((await dup.json()).ok, false);
});

test("strategy flow: unknown seller, valid submit, bad risk, listing", async () => {
  const env = makeEnv();
  const reg = await (
    await postJson(
      "/api/sellers/register",
      { handle: "seller1", name: "S", email: "s@x.com" },
      { env }
    )
  ).json();
  const sid = reg.seller.seller_id;

  const unknown = await postJson(
    "/api/strategies",
    { seller_id: "sel-nope", title: "EMA Cross", description: "A solid strategy", price: 99, risk_level: "low" },
    { env }
  );
  assert.equal(unknown.status, 400);

  const badRisk = await postJson(
    "/api/strategies",
    { seller_id: sid, title: "EMA Cross", description: "A solid strategy", price: 99, risk_level: "MEDIUM" },
    { env }
  );
  assert.equal(badRisk.status, 400);

  const ok = await (
    await postJson(
      "/api/strategies",
      { seller_id: sid, title: "EMA Cross", description: "A solid EMA crossover strategy", price: 199, risk_level: "medium" },
      { env }
    )
  ).json();
  assert.equal(ok.ok, true);

  const list = await (await call("/api/strategies", {}, env)).json();
  assert.equal(list.length, 1);
  assert.equal(list[0].title, "EMA Cross");
  assert.equal(list[0].payment_mode, "contact");
});

test("marketplace returns 503 when KV is not configured", async () => {
  const env = makeEnv({ VANES_STATE: undefined });
  const res = await postJson(
    "/api/sellers/register",
    { handle: "abc", name: "A", email: "a@b.com" },
    { env }
  );
  assert.equal(res.status, 503);
});

test("/api/v1/analyze enforces the JWT gate", async () => {
  const packet = { symbol: "EURUSD", bid: 1.1, ask: 1.1002, subscription_tier: "PRO" };

  const missing = await postJson("/api/v1/analyze", packet);
  assert.equal(missing.status, 401);

  const bad = await postJson("/api/v1/analyze", packet, {
    headers: { Authorization: "Bearer not.a.valid.token" },
  });
  assert.equal(bad.status, 401);

  const expired = await signJwt({ tier: "PRO", exp: Math.floor(Date.now() / 1000) - 10 });
  const expRes = await postJson("/api/v1/analyze", packet, {
    headers: { Authorization: `Bearer ${expired}` },
  });
  assert.equal(expRes.status, 401);
});

test("/api/v1/analyze tier router: PRO gets order dispatch, BEGINNER is text-only", async () => {
  const packet = { symbol: "EURUSD", bid: 1.1, ask: 1.1002 };

  const proToken = await signJwt({ tier: "PRO", exp: future() });
  const pro = await (
    await postJson("/api/v1/analyze", packet, {
      headers: { Authorization: `Bearer ${proToken}` },
    })
  ).json();
  assert.equal(pro.ok, true);
  assert.equal(pro.tier, "PRO");
  assert.equal(pro.order_dispatch, "READY");
  assert.equal(pro.analysis, "Gemini API key not configured");

  const begToken = await signJwt({ tier: "BEGINNER", exp: future() });
  const beg = await (
    await postJson("/api/v1/analyze", packet, {
      headers: { Authorization: `Bearer ${begToken}` },
    })
  ).json();
  assert.equal(beg.ok, true);
  assert.equal(beg.tier, "BEGINNER");
  assert.equal(beg.order_dispatch, undefined);
  assert.match(beg.analysis, /Basic text-only/);

  const intToken = await signJwt({ tier: "INTERMEDIATE", exp: future() });
  const inter = await (
    await postJson("/api/v1/analyze", packet, {
      headers: { Authorization: `Bearer ${intToken}` },
    })
  ).json();
  assert.equal(inter.ok, true);
  assert.equal(inter.order_dispatch, undefined);
});

test("/api/v1/analyze rejects an unknown tier", async () => {
  const token = await signJwt({ tier: "SERVER_A", exp: future() });
  const res = await postJson(
    "/api/v1/analyze",
    { symbol: "EURUSD", bid: 1.1, ask: 1.1 },
    { headers: { Authorization: `Bearer ${token}` } }
  );
  assert.equal(res.status, 403);
});

test("/api/v1/analyze returns 401 when JWT secret is not configured", async () => {
  const env = makeEnv({ VANES_JWT_SECRET: "" });
  const res = await postJson(
    "/api/v1/analyze",
    { symbol: "EURUSD", bid: 1.1, ask: 1.1 },
    { env, headers: { Authorization: "Bearer x.y.z" } }
  );
  assert.equal(res.status, 500);
});
