---
name: vidseeds-setup
description: Use when connecting to VidSeeds.ai, getting a "Bearer token required" / AUTH_REQUIRED error from the vidseeds MCP server, or asking how to authenticate / what the VidSeeds.ai connector can do. Walks through creating a Personal Access Token and setting VIDSEEDS_PAT.
---

# Connect to VidSeeds.ai

VidSeeds.ai is a **pre-upload video SEO & metadata optimization and multi-platform
publishing** platform. It analyzes a creator's existing video and produces optimized
titles, descriptions, tags, thumbnails, and chapters for YouTube, TikTok, Instagram,
Facebook, LinkedIn, and X — then publishes them. It is **not** a video generator or
editor. This connector exposes that workflow as MCP tools (all prefixed `vidseeds_`).

## The connector needs a Personal Access Token (PAT)

For this plugin (Claude Code / Codex), the `vidseeds` MCP server authenticates with a
**Personal Access Token** — cookie sessions are rejected. If a tool call returns
`401 / AUTH_REQUIRED` ("Bearer token required"), the token is missing or unset.

> The same hosted endpoint also supports **OAuth 2.0** (PKCE + Dynamic Client Registration)
> when added as a custom connector in **Claude.ai** or **Claude Desktop** — no token needed
> there. See <https://vidseeds.ai/settings/developer-tokens>.

> **Paid connector — 14-day free trial.** The MCP server requires a paid VidSeeds.ai
> subscription. Every account gets a **14-day free trial that starts on the first MCP
> connection** (including older accounts that have never connected); after it ends, an
> active subscription is required (a `402 / SUBSCRIPTION_REQUIRED` response means the
> trial has ended — subscribe at <https://vidseeds.ai/pricing>).

Note: creating a token is free, but **connecting requires a paid subscription or an active
trial**. Separately, individual tools spend **seeds** from the account's balance
(read-only tools are free) — connection access and per-tool seed cost are both enforced
server-side per call.

### One-time setup

1. Sign in at **https://vidseeds.ai** (free account).
2. Open **Settings → Developer Tokens**: <https://vidseeds.ai/settings/developer-tokens>.
3. Create a token. Copy it immediately — the secret (`vs_pat_…`) is shown **only once**.
   Tokens default to a 90-day expiry.
4. Expose it to your AI client as the `VIDSEEDS_PAT` environment variable, then restart
   the client / reconnect the server.

**Claude Code** — export before launching (or add to your shell profile):

```bash
export VIDSEEDS_PAT="vs_pat_your_token_here"
claude
```

Verify with `/mcp` — the `vidseeds` server should list its tools. If it shows an auth
error, the variable was not set in the environment Claude Code was launched from.

**Cursor** — same `VIDSEEDS_PAT` + MCP config as in the plugin README. Tool names use
`vidseeds_` (underscore), not `vidseeds.` — dotted names are filtered out by Cursor.

**Codex** — set the same variable in the environment Codex runs in:

```bash
export VIDSEEDS_PAT="vs_pat_your_token_here"
```

> Never paste the raw token into a config file, a prompt, or a committed file. The token
> is read from the environment by name (`VIDSEEDS_PAT`) — the value never lives in the
> plugin. A leaked PAT grants full non-admin access to the owner's account.

## What you can do once connected

The connector surfaces VidSeeds.ai's full creator workflow (148 tools). Highlights:

- **Metadata optimization** — generate/regenerate optimized titles, descriptions, tags,
  and chapters per platform; optimization history.
- **Thumbnails** — AI thumbnail generation, edits, restyles, Thumbnail Studio (trends,
  briefs, subjects, overlay text, style profiles), publish a thumbnail to YouTube.
- **Projects** — create a project from a YouTube video, snapshots, apply a thumbnail,
  per-platform publish config.
- **Analytics & intelligence** — channel/video analytics, channel intelligence, video
  autopsy, outlier detection, public-channel audit, best practices.
- **Discovery & research** — keyword research, trending videos, breakout channels,
  video ideas.
- **Auto-clips** — list/get saved shorts, edit metadata, caption style, reframe, download.
- **Translation & captions** — metadata localization across 85 languages, caption
  upload/get/delete. (No dubbing — VidSeeds.ai has no voice dubbing.)
- **Local video media** — `probe`, frame/clip extraction, and precision-trim/midroll
  analysis return commands to run locally; heavy media stays on the user's machine.
- **Publishing & platform connections** — connect/activate platforms, schedule/confirm
  publishes, direct YouTube upload.
- **Account & billing** — seed balance, subscription, referrals, support tickets.

## Seeds (cost awareness)

Some tools spend **seeds** from the account's balance (e.g. thumbnail generation, AI
channel intelligence, translation). Read-only tools are free. Each tool's `description`
states its cost — surface the expected seed cost to the user before running a
charge-bearing tool, and check `vidseeds_get_seed_balance` if unsure.

## Platform usage quotas (MCP daily call quotas)

Separate from per-tool seed costs, **every** MCP tool call counts toward a generous
**daily platform-usage quota** that refills continuously through the day. Normal daily
production (shorts + adjustments + polling + investigations) fits comfortably inside it.

| Plan    | Included calls / day | Bucket cap |
| ------- | -------------------- | ---------- |
| Sprout  | 1,000                | 2,000      |
| Growth  | 3,000                | 6,000      |
| Harvest | 8,000                | 16,000     |
| Agency  | 20,000               | 40,000     |
| Trial   | 1,000                | 1,000      |

- The bucket refills at the per-plan rate (Sprout = 1,000/day), accumulating up to the
  cap — it is **not** a midnight reset.
- Once the bucket is empty, each extra call costs **1 seed** on top of any per-tool seed
  cost, until the bucket refills.
- Balance/cost reads are **free and exempt**: `vidseeds_get_seed_balance` and
  `vidseeds_get_seed_balance_and_subscription` never consume a call or charge overage.
- Call `vidseeds_get_seed_balance` to see remaining included calls, the daily refill, the
  bucket cap, and the overage rate. An over-quota call with insufficient balance returns
  a clear `MCP_QUOTA_EXCEEDED` error (with a top-up link) — surface it to the user rather
  than retrying in a loop.
