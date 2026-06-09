---
name: vidseeds-setup
description: Use when connecting to VidSeeds.ai, getting AUTH_REQUIRED or SUBSCRIPTION_REQUIRED from the vidseeds MCP server, or setting up VIDSEEDS_PAT / OAuth for the connector. Not for workflow recipes — use vidseeds-efficiency and domain skills after connect.
---

# Connect to VidSeeds.ai

VidSeeds.ai is **pre-upload video SEO, metadata optimization, and multi-platform publishing** for existing videos. It is **not** a video generator or editor. All hosted tools are prefixed `vidseeds_` (underscore — Cursor rejects dotted names like `vidseeds.generate_thumbnail`).

## Authentication (this plugin)

The hosted server at `https://vidseeds.ai/api/mcp` requires:

- **Claude Code / Codex / Cursor (this package):** `Authorization: Bearer vs_pat_…` via **`VIDSEEDS_PAT`** in the environment. Cookie sessions are rejected.
- **Claude.ai / Claude Desktop:** same endpoint supports **OAuth 2.0** (PKCE) as a custom connector — no PAT. See <https://vidseeds.ai/settings/mcp-settings>.

### PAT setup

1. Sign in at <https://vidseeds.ai>.
2. **Settings → MCP Settings:** <https://vidseeds.ai/settings/mcp-settings>.
3. Create a token; copy `vs_pat_…` immediately (shown once, ~90-day default expiry).
4. Export before launching the client:

```bash
export VIDSEEDS_PAT="vs_pat_your_token_here"
```

**Claude Code:** verify with `/mcp` — `vidseeds` should list tools. Auth errors usually mean `VIDSEEDS_PAT` was not set in the shell that launched Claude.

**Codex / Cursor:** same variable; Cursor uses `Authorization: Bearer ${env:VIDSEEDS_PAT}` in MCP config (see plugin README).

Never commit or paste the raw token. A leaked PAT grants full **non-admin** account access.

## Access: subscription and trial

- **Paid connector** with a **14-day free trial** starting on the **first MCP connection** (including accounts that never connected before).
- After trial: active subscription required. `402 / SUBSCRIPTION_REQUIRED` → <https://vidseeds.ai/pricing>.
- Token creation is free; **connecting** requires trial or subscription.

## After you are connected

| Need                                | Skill                  |
| ----------------------------------- | ---------------------- |
| Seeds, quotas, polling, cheap calls | `vidseeds-efficiency`  |
| Thumbnails                          | `vidseeds-thumbnails`  |
| Projects & metadata                 | `vidseeds-projects`    |
| Analytics & research                | `vidseeds-analytics`   |
| Local video files                   | `vidseeds-local-video` |
| Publish & connections               | `vidseeds-publishing`  |

Full capability overview: plugin README and each tool's `description` from `tools/list`.
