# VidSeeds.ai MCP marketplace and connector catalog

[![VidSeeds.ai trust badge](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dvidseeds-ai%252Fvidseeds%26metric%3Dtrust%26style%3Dflat)](https://hol.org/registry/plugins/vidseeds-ai%2Fvidseeds)
[![VidSeeds.ai security badge](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dvidseeds-ai%252Fvidseeds%26metric%3Dsecurity%26style%3Dflat)](https://hol.org/registry/plugins/vidseeds-ai%2Fvidseeds)

Drive **VidSeeds.ai** - pre-upload video **SEO & metadata optimization** and
multi-platform publishing - directly from your AI coding client.

> **VidSeeds.ai** analyzes a creator's existing video and produces optimized titles,
> descriptions, tags, thumbnails, and chapters for YouTube, TikTok, Instagram, Facebook,
> LinkedIn, and X, then publishes them. It is **not** a video generator or editor.

This repo is the public marketplace/catalog source for the hosted
[MCP](https://modelcontextprotocol.io) connector that exposes the VidSeeds.ai workflow
(**247 tools**, all prefixed `vidseeds_`). It ships the machine-readable metadata that
different clients expect:

| Client / catalog                              | What this repo provides                                                                                      |
| --------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| Claude Code                                   | `.claude-plugin/marketplace.json`, `.claude-plugin/plugin.json`, `.mcp.json`, and workflow skills            |
| Codex                                         | `.agents/plugins/marketplace.json`, `.codex-plugin/plugin.json`, `codex.mcp.json`, and workflow skills       |
| Official MCP Registry and downstream catalogs | root `server.json` for `mcp-publisher` and registry-compatible crawlers                                      |
| ChatGPT                                       | source metadata/assets plus docs for the separate Apps SDK endpoint at `https://vidseeds.ai/api/mcp/chatgpt` |
| Cursor and other MCP clients                  | copy-paste Streamable HTTP config for `https://vidseeds.ai/api/mcp`                                          |

The connector ships no credentials - it tells your client how to call the hosted endpoint
with a token you supply.

- **Endpoint:** `https://vidseeds.ai/api/mcp` (MCP Streamable HTTP)
- **Auth (this plugin):** Personal Access Token (`Authorization: Bearer vs_pat_…`)
- **Auth (Claude.ai / Desktop):** the same endpoint also supports **OAuth 2.0** (PKCE + Dynamic Client Registration) - add it as a custom connector, no token needed. See the in-app guide below.
- **ChatGPT App:** a dedicated endpoint `https://vidseeds.ai/api/mcp/chatgpt` powers the **OpenAI ChatGPT App** (Apps SDK) with rendered result widgets. Local-only tools (ffmpeg/ffprobe recipes, precision-trim, local-audio transcription) are hidden there since ChatGPT has no local shell - use this Claude Code / Codex plugin for those. ChatGPT distribution is through the ChatGPT Apps submission/directory flow, not by adding this Git repo as a custom marketplace.
- **Server:** `vidseeds` v1.9.2 (agent orientation: routing-first server instructions sized for client truncation limits, vidseeds_guide tool, workflow prompts)

> **More clients & a copy-paste walkthrough:** the in-app setup guide at
> <https://vidseeds.ai/settings/mcp-settings> covers **Claude.ai & Desktop (OAuth)**,
> **Claude Code**, **Cursor**, **Codex**, and any other MCP client - with ready-to-copy
> snippets for each.

> **💳 Paid connector - 14-day free trial.** The MCP server is available to paid
> VidSeeds.ai subscribers. Every account gets a **14-day free trial that starts on the
> first MCP connection** - including older accounts that have never connected before;
> once it ends, an active subscription is required to keep using the connector. Manage
> plans at <https://vidseeds.ai/pricing>.

> **If you are editing the VidSeeds.ai source code:**
> Do not keep the `vidseeds` MCP server connected in the same coding agent session you use
> to work on this repository. The catalog (even with `?toolset=core`) is the _product surface_
> for operating on user videos/channels. It will consume context you need for the actual code
> changes. Use your agent's normal file system / grep / edit tools. Only connect the MCP
> (with `?toolset=core` recommended) when you are specifically testing the MCP layer, a new
> tool, the route handler, etc. See the root `AGENTS.md` "Context Hygiene" section.

---

## 1. Get a Personal Access Token (required)

1. Sign in at <https://vidseeds.ai> (free account).
2. Open **Settings → MCP Settings**: <https://vidseeds.ai/settings/mcp-settings>.
3. Create a token and copy the secret (`vs_pat_…`) - it is shown **only once**
   (90-day default expiry).
4. Expose it to your client as the `VIDSEEDS_PAT` environment variable (below).

> 🔒 The token value never belongs in any file. This package references it **by name**
> (`VIDSEEDS_PAT`); your client injects the value from the environment at connect time.
> A leaked PAT grants full non-admin access to your account - treat it like a password.

> ℹ️ Creating a token is free, but **connecting requires a paid subscription or an active
> 14-day trial** (see above). Beyond access, individual tools spend **seeds** from your
> balance (read-only tools are free) - connection access and per-tool seed cost are
> separate, both enforced server-side per call.

---

## 2. Install in Claude Code

### Option A - install the plugin (recommended)

```text
/plugin marketplace add CarrotGamesStudios/vidseeds-mcp
/plugin install vidseeds@vidseeds
```

Then make the token available in the environment Claude Code is launched from:

```bash
export VIDSEEDS_PAT="vs_pat_your_token_here"
claude
```

Run `/mcp` to confirm the `vidseeds` server is connected and listing tools. If you see an
auth error, `VIDSEEDS_PAT` was not set in the launching shell - export it and restart.

> The plugin's `.mcp.json` injects your token via `Bearer ${VIDSEEDS_PAT}` - the same
> shape Anthropic's official GitHub connector uses. Set `VIDSEEDS_PAT` before launching;
> if it is unset, Claude Code flags the `vidseeds` server as needing configuration.

### Option B - add the server directly (no plugin)

For a quick test without installing the plugin. Prefer Option A for daily use - it
keeps the token in the environment (`VIDSEEDS_PAT`) and reads it at runtime, instead
of writing the resolved token into `~/.claude.json`.

Reference the env var rather than pasting the raw token, so the secret never lands in
your shell history or terminal scrollback:

```bash
export VIDSEEDS_PAT="vs_pat_your_token_here"
claude mcp add --transport http vidseeds https://vidseeds.ai/api/mcp?toolset=core \
 --header "Authorization: Bearer $VIDSEEDS_PAT"
```

---

## 3. Install in Codex

Codex does not yet offer self-serve central plugin publishing, so the most reliable
path is to add the server to your Codex config.

### Option A - `~/.codex/config.toml` (recommended)

```toml
[mcp_servers.vidseeds]
url = "https://vidseeds.ai/api/mcp"
bearer_token_env_var = "VIDSEEDS_PAT"
```

Then export the token in the environment Codex runs in:

```bash
export VIDSEEDS_PAT="vs_pat_your_token_here"
```

### Option B - CLI

```bash
codex mcp add vidseeds --url https://vidseeds.ai/api/mcp?toolset=core --bearer-token-env-var VIDSEEDS_PAT
```

### Option C - repo/team marketplace

```bash
codex plugin marketplace add CarrotGamesStudios/vidseeds-mcp
codex plugin add vidseeds@vidseeds
```

This repo also ships a Codex repo marketplace at `.agents/plugins/marketplace.json` and a
plugin manifest at `.codex-plugin/plugin.json` (MCP config in `codex.mcp.json`). Point a
Codex marketplace at this repo and install `vidseeds` with `codex plugin add` or via
`codex` → `/plugins`. The same
`VIDSEEDS_PAT` environment variable applies.

---

## 4. Install in Cursor

Add the server to `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (per project).
Cursor resolves `${env:…}` in `url` / `headers`, so reference the token by name rather
than pasting the secret:

```json
{
  "mcpServers": {
    "vidseeds": {
      "url": "https://vidseeds.ai/api/mcp",
      "headers": {
        "Authorization": "Bearer ${env:VIDSEEDS_PAT}"
      }
    }
  }
}
```

Set `VIDSEEDS_PAT` in your environment, then enable the `vidseeds` server in
**Cursor Settings → MCP**. Tool names use the `vidseeds_` prefix (underscore, not dot) .
Cursor rejects dotted names like `vidseeds.generate_thumbnail`.

---

## 5. Official MCP Registry and other catalogs

The root [`server.json`](server.json) is the registry-compatible description of the hosted
remote server:

- Name: `io.github.CarrotGamesStudios/vidseeds-mcp`
- Remote: `streamable-http` at `https://vidseeds.ai/api/mcp`
- Auth header: required secret `Authorization` value, for example
  `Bearer vs_pat_your_token_here`
- Repository: `https://github.com/CarrotGamesStudios/vidseeds-mcp`

Maintainership note: publish or republish `server.json` with the official `mcp-publisher`
CLI whenever the connector version, endpoint, auth requirements, or canonical description
changes. Directory sites that ingest the official registry can then discover VidSeeds.ai
without needing a Claude/Codex-specific plugin marketplace.

---

## 6. ChatGPT

ChatGPT does not install this Git repo as a custom marketplace. Use the VidSeeds.ai ChatGPT
App once it is published in the ChatGPT Apps directory, or use a client that supports
custom MCP connectors with the hosted endpoint. The ChatGPT endpoint is
`https://vidseeds.ai/api/mcp/chatgpt`; it exposes the ChatGPT-safe subset of tools and
rendered widgets.

---

## 7. Agent skills (workflow guides)

This plugin ships skills under [`skills/`](skills/) so agents use MCP efficiently without guessing tool chains. Read **`vidseeds-efficiency`** before expensive workflows.

| Skill                  | When to use                              |
| ---------------------- | ---------------------------------------- |
| `vidseeds-setup`       | PAT/OAuth, trial, first connect          |
| `vidseeds-efficiency`  | Seeds, daily MCP quota, async polling    |
| `vidseeds-thumbnails`  | Generate, edit, studio, apply to project |
| `vidseeds-projects`    | YouTube → project → metadata             |
| `vidseeds-analytics`   | Channel intel, autopsy, discovery        |
| `vidseeds-local-video` | Local files, ffmpeg recipes, trim        |
| `vidseeds-publishing`  | Connections, preflight, publish          |

Per-tool parameters and seed costs come from the hosted server's `tools/list` descriptions. Skills teach **composition**, not a full catalog. Maintainer sync: [`MAINTAINERS.md`](MAINTAINERS.md).

---

## 8. What the connector can do

247 tools spanning the full VidSeeds.ai creator workflow:

| Area                     | Examples                                                                                                                    |
| ------------------------ | --------------------------------------------------------------------------------------------------------------------------- |
| Metadata optimization    | titles, descriptions, tags, chapters; optimization history                                                                  |
| Thumbnails               | AI generation, edit, restyle; Thumbnail Studio (trends, briefs, subjects, overlay text, style profiles); publish to YouTube |
| Projects                 | create from a YouTube video, snapshots, apply thumbnail, per-platform config                                                |
| Analytics & intelligence | channel/video analytics, channel intelligence, video autopsy, outlier detection, public-channel audit                       |
| Discovery & research     | keyword research, trending videos, breakout channels, video ideas                                                           |
| Auto-clips               | list/get saved shorts, edit metadata, caption style, reframe, download                                                      |
| Translation & captions   | metadata localization (85 languages), caption upload/get/delete                                                             |
| Local video media        | `probe`, frame/clip extraction, precision-trim & midroll analysis (commands run locally)                                    |
| Publishing               | platform connections, schedule/confirm publish, direct YouTube upload                                                       |
| Account                  | seed balance, subscription, referrals, support                                                                              |

> **Seeds:** some tools (thumbnail generation, AI intelligence, translation, …) spend
> seeds from your VidSeeds.ai balance. Read-only tools are free. Every tool's description
> states its cost; check `vidseeds_get_seed_balance` if unsure.

---

## 9. Tool catalog size management

**247 tools is a lot.** When VidSeeds.ai connects to your MCP client, the full tool
catalog (~46K tokens) loads into the agent's context. If your agent feels slow or
overwhelmed, you can switch to a **leaner toolset**:

### 9a. Use `?toolset=core` on the MCP URL

Add `?toolset=guide` for the absolute minimum (only the orientation `vidseeds_guide` tool + instructions, ~1 tool).
Add `?toolset=core` to reduce from ~247 to ~74 essential tools (~16K tokens) - the recommended default for most usage:

**Claude Code** (recommended for most):

```bash
claude mcp add --transport http vidseeds https://vidseeds.ai/api/mcp?toolset=core \
 --header "Authorization: Bearer $VIDSEEDS_PAT"
```

For ultra-light (guide only):

```bash
claude mcp add --transport http vidseeds https://vidseeds.ai/api/mcp?toolset=guide \
 --header "Authorization: Bearer $VIDSEEDS_PAT"
```

**Cursor** (recommended default):

```json
{
  "mcpServers": {
    "vidseeds": {
      "url": "https://vidseeds.ai/api/mcp?toolset=core",
      "headers": {
        "Authorization": "Bearer ${env:VIDSEEDS_PAT}"
      }
    }
  }
}
```

(Use `?toolset=guide` for lightest.)

**Codex** (recommended):

```toml
[mcp_servers.vidseeds]
url = "https://vidseeds.ai/api/mcp?toolset=core"
bearer_token_env_var = "VIDSEEDS_PAT"
```

**Claude Desktop** - add when defining the custom MCP connector:

```
URL: https://vidseeds.ai/api/mcp?toolset=core
```

> ⚠️ **You can always upgrade back.** If a core-only agent needs a tool not in the
> core set (e.g. deep intelligence, precision trim, comment management), just remove
> `?toolset=core` from the URL and reconnect. The full catalog is always available.

Tools that survive the `core` toolset: projects, metadata optimization, publishing,
thumbnails, basic analytics, channel management, translation, connections, billing,
and referrals. Everything else (deep intelligence, competitive research, local video
tools, admin, autoclips, bulk edit, comments, assistant workflows) is excluded.

### 9b. Make your AI default to VidSeeds.ai tools

Sometimes generalist agents fall back to writing raw python, ffmpeg command templates, or
browser automation instead of the connected VidSeeds.ai tools. The server ships
routing-first instructions sized for those truncation limits (v1.9.2), but you can make
the routing deterministic by telling your client directly:

**Claude.ai / Claude Desktop** - paste into _Settings → Profile → Preferences_ (applies
everywhere) or your Project's custom instructions:

```text
When my request involves my videos, channels, titles, descriptions, tags,
thumbnails, video SEO, keywords, analytics, comments, clips, captions,
translations, scheduling, or publishing, ALWAYS use the connected VidSeeds.ai
tools (vidseeds_*) first - search the available tools for "vidseeds" if none
are loaded. Do not use web search, browser automation, or general knowledge
for these tasks: VidSeeds.ai has authenticated access to my actual channel data,
transcripts, and analytics.
```

**Claude Code** - add the same block to your project's `CLAUDE.md` (or
`~/.claude/CLAUDE.md` for all projects).

**Codex / Cursor** - add it to `AGENTS.md` / project rules respectively.

---

## Platform usage quotas (MCP daily call quotas)

Beyond per-tool seed costs, **every** MCP tool call - read or write - counts toward a
generous **daily platform-usage quota** that refills continuously throughout the day.
This keeps real production workloads (daily shorts, adjustments, polling, agent-driven
investigations) comfortable on every plan, while pricing sustained high-volume scraping
or abuse in real money.

| Plan    | Included calls / day | Bucket cap |
| ------- | -------------------- | ---------- |
| Sprout  | 1,000                | 2,000      |
| Growth  | 3,000                | 6,000      |
| Harvest | 8,000                | 16,000     |
| Agency  | 20,000               | 40,000     |
| Trial   | 1,000                | 1,000      |

- **Continuous refill, not a midnight reset.** Your bucket refills at the per-plan rate
  (e.g. Sprout = 1,000/day), accumulating up to the cap so a quiet day carries a
  reasonable burst into the next.
- **Overage:** once the bucket is empty, each additional tool call costs **1 seed**
  (`MCP_OVERAGE_SEED_COST`), on top of any per-tool seed cost. The bucket keeps refilling,
  so you stop paying overage as soon as it tops up again.
- **Balance and cost reads are free and exempt** - `vidseeds_get_seed_balance` and
  `vidseeds_get_seed_balance_and_subscription` never consume a call or charge overage.
- **Check your remaining included calls** any time with `vidseeds_get_seed_balance` (it
  returns your daily refill, bucket cap, available included calls, and the overage rate).

> If a call is over quota and your balance can't cover the 1-seed overage, the tool
> returns a clear `MCP_QUOTA_EXCEEDED` error with a top-up link - no surprise charges.

### YouTube thumbnail upload limits

YouTube rate-limits custom-thumbnail uploads separately from VidSeeds.ai seeds and
MCP call quota. For bulk thumbnail replacements, plan **no more than about 100
thumbnail uploads per connected YouTube channel/account per rolling 24 hours**.
If `vidseeds_publish_thumbnail_to_youtube` returns `uploadRateLimitExceeded` or
"too many thumbnails recently", stop the batch, save the next video id, and resume
later.

---

## Security

- This package contains **no credentials**. It declares how Claude Code / Codex should
  call `https://vidseeds.ai/api/mcp` with a user-supplied PAT read from `VIDSEEDS_PAT`.
- Never commit, paste, or share a `vs_pat_…` token. Rotate or revoke tokens at
  <https://vidseeds.ai/settings/mcp-settings>.
- Cookie/session auth is rejected by the server by design - a PAT is the only accepted
  credential, so a misconfigured client can't piggyback on a dashboard login.

## Versioning

The plugin version tracks the VidSeeds.ai MCP connector package (currently **1.9.2** - routing-first server `instructions` sized for client truncation limits so tool-search clients default to VidSeeds tools, plus the `vidseeds_guide` tool, the `vidseeds://guide` resource, and workflow prompts).
The wildcard PAT scope reaches new tools automatically as the server grows, so existing
tokens keep working without being recreated.

## Links

- Product: <https://vidseeds.ai>
- MCP settings: <https://vidseeds.ai/settings/mcp-settings>
- MCP: <https://modelcontextprotocol.io>

## License

MIT - see [`LICENSE`](./LICENSE).
