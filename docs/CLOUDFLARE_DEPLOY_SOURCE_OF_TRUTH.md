# Cloudflare Deploy Source Of Truth

This repo now includes Cloudflare Worker deploy config in git:

- `/Users/mariusgaarder/Documents/treningscoach/wrangler.toml`
- `/Users/mariusgaarder/Documents/treningscoach/cloudflare/worker.js`

## Why this exists

- Fixes dashboard drift where Cloudflare "Latest build failed" can happen with no matching config in repo.
- Keeps one deterministic deploy path for Cloudflare in version control.
- Does **not** move backend runtime away from Render.

## Runtime model

1. Cloudflare Worker receives request on `*.workers.dev`.
2. Worker proxies request to `ORIGIN_URL`.
3. Render Flask backend remains the runtime source of truth (`main.py`).

## Config

`wrangler.toml` defines:

- Worker name: `treningscoach-backend`
- Entry: `cloudflare/worker.js`
- Compatibility date
- `ORIGIN_URL` default: `https://treningscoach-backend.onrender.com`

## Deploy

```bash
cd /Users/mariusgaarder/Documents/treningscoach
npx wrangler deploy
```

## Verify

```bash
curl -I https://treningscoach-backend.cryptomarius.workers.dev/health
curl -I https://treningscoach-backend.onrender.com/health
```

Expect HTTP 200 for both.

## Dashboard settings to align once

In Cloudflare Workers project:

1. Set project to use repo root.
2. Ensure build/deploy uses `wrangler.toml`.
3. Remove old static-assets-only build settings if present.
4. Redeploy latest commit.

After that, config is controlled from git instead of ad-hoc dashboard edits.
