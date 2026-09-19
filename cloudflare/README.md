# VANES-AI V2 — Cloudflare

This folder is the public cloud web layer for VANES-AI V2.

## Deploy directly from GitHub

In the Cloudflare dashboard:

1. Open **Workers & Pages**.
2. Choose **Create application** → **Workers**.
3. Choose the option to connect a **Git repository / GitHub**.
4. Authorize GitHub and select `obtechnologies625-lab/VANES-AI-V2-FOREX-`.
5. Set the project/root directory to `cloudflare`.
6. Build command: `npm install`
7. Deploy command: `npx wrangler deploy`
8. Save and deploy.

After that, pushes to the configured GitHub branch can trigger Cloudflare deployments through Workers Builds.

## What works in the cloud

- Responsive VANES command-center dashboard
- Cloud health endpoint: `/api/health`
- Market state endpoint: `/api/state`
- Read-only cloud chatbot: `/api/chat`
- Safe default WAIT state when no market source is connected

## Important MT5 architecture

Cloudflare Workers cannot run the Python MetaTrader5 package or the Tkinter desktop app. Keep the MT5/Python agent on a Windows machine and expose only sanitized market state to the cloud if live cloud data is needed.

Do not put MT5 passwords, broker credentials, or order-execution code in browser JavaScript or public Worker variables.

The current Worker deliberately starts without a database/KV requirement so the first GitHub → Cloudflare deployment is straightforward and safe.


## Live MT5 → Cloudflare state bridge

The desktop app can publish a sanitized read-only state to this Worker. Publishing is **disabled by default** and requires both `VANES_CLOUD_URL` and `VANES_CLOUD_TOKEN`.

### 1. Create the KV namespace

From the `cloudflare` directory:

```bash
npx wrangler kv namespace create VANES_STATE
```

Copy the returned namespace ID into `wrangler.toml`:

```toml
[[kv_namespaces]]
binding = "VANES_STATE"
id = "YOUR_REAL_NAMESPACE_ID"
```

Do not commit a publish token to GitHub.

### 2. Configure the Worker secret

```bash
npx wrangler secret put VANES_PUBLISH_TOKEN
```

Enter a long random token when prompted.

### 3. Deploy

```bash
npm install
npx wrangler deploy
```

### 4. Configure the Windows/MT5 machine

Set these environment variables before starting VANES:

```text
VANES_CLOUD_URL=https://YOUR-WORKER.YOUR-SUBDOMAIN.workers.dev
VANES_CLOUD_TOKEN=the_same_token_used_for_VANES_PUBLISH_TOKEN
VANES_CLOUD_PUBLISH_INTERVAL=3
VANES_CLOUD_TIMEOUT=5
```

The publisher sends only market guidance, prices, risk references, paper-account values, and broker-readiness state. It does **not** send broker passwords, account credentials, or order commands.

### Health behavior

`GET /api/health` reports `stale: true` when the last published state is older than 15 seconds or has no valid bid. KV entries expire after 120 seconds, so a stopped desktop publisher will not leave an apparently live market state forever.

### Cloudflare project settings

For Git-connected deployment, use **Workers**, not a static Pages deployment, and set the project root directory to `cloudflare`. The repository root contains the Python application and must not be treated as the Worker project.
