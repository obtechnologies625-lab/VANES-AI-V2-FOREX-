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
