# Revid Agentic Skills

Drop-in agent skills that turn any link, blog, product, article, tweet, PDF, or
one-line idea into a finished short-form video — by calling the
[**Revid MCP server**](https://www.revid.ai/mcp) (which wraps
[Revid Public API v3](https://documenter.getpostman.com/view/36975521/2sBXcGEfaB)).

**12 skills · works with Claude Code, OpenClaw, Codex, Cursor, Gemini CLI, and
any MCP-capable agent.**

## Install as a Claude plugin

This repo is a Claude plugin marketplace. The `revid` plugin adds the Revid MCP
server (30 tools, OAuth sign-in, no API key to paste) and all the skills below.

In Claude Code:

```
/plugin marketplace add tmakersas/revid-skills
/plugin install revid@revid
```

Then run `/mcp`, select `revid` and choose Authenticate to sign in with your Revid
account. In Claude (web and desktop), add the marketplace under Customize, Plugins,
Add marketplace, with this repo's URL, or connect only the server under Settings,
Connectors, Add custom connector, with `https://www.revid.ai/api/mcp`.

Try: *"Find what is going viral about productivity apps this week, make a 30 second
video from the strongest hook and schedule it on my TikTok for Friday 6pm."*

## Install in Cursor or Gemini CLI

The same repo is a Cursor plugin (`.cursor-plugin/plugin.json`, `mcp.json`) and a Gemini CLI
extension (`gemini-extension.json`).

```
gemini extensions install https://github.com/tmakersas/revid-skills
```

Then run `/mcp auth revid` in Gemini CLI. In Cursor, install Revid from the plugin marketplace, or
add `https://www.revid.ai/api/mcp` under Settings, MCP. Both sign in with your Revid account.

- 🌐 Marketplace: <https://www.revid.ai/skills>
- 🧩 MCP server: <https://www.revid.ai/mcp>
- 📦 ClawHub: <https://clawhub.ai/@api00>
- 🛠 Source: this repo (MIT-licensed)

---

## Install in 30 seconds

### 1. Get a Revid API key

Sign up at <https://www.revid.ai/account> and copy your key.

### 2. Add the Revid MCP server to your agent

Drop this once into your agent's MCP config (Claude Code's `~/.claude.json`,
Cursor's `mcp.json`, OpenClaw's `mcp.json`, etc.):

```json
{
  "mcpServers": {
    "revid": {
      "url": "https://www.revid.ai/api/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_REVID_API_KEY"
      }
    }
  }
}
```

Any of these auth headers also works: `x-revid-api-key`, `x-api-key`, `key`.

That single MCP server exposes 30 tools, such as `search_viral_videos`,
`render_video`, `get_project_status`, `export_video`, `calculate_credits`,
`schedule_publish` and `publish_now`, used by every skill in this catalog. Claude,
ChatGPT, Claude Code, Cursor and VS Code can skip the API key: add the URL alone and
sign in with your Revid account (OAuth).

### 3. Install one skill — pick your agent

| Agent | Install |
|---|---|
| **OpenClaw** *(native)* | `openclaw skills install revid-shopify-product-promo` |
| **Claude Skills** | `npx degit tmakersas/revid-skills/skills/revid-shopify-product-promo ~/.claude/skills/revid-shopify-product-promo` |
| **Codex** | `curl -fsSL https://raw.githubusercontent.com/tmakersas/revid-skills/main/skills/revid-shopify-product-promo/SKILL.md >> AGENTS.md` |
| **Cursor** | `curl -fsSL …/SKILL.md >> .cursorrules` |
| **Gemini CLI** | `curl -fsSL …/SKILL.md -o GEMINI.md` |
| **Anything else** | `curl -fsSL …/SKILL.md` and paste into the agent's context |

### 4. Ask the agent

```
Use Shopify Product Promo to turn https://allbirds.com/products/mens-tree-runners into a TikTok
```

The skill will scrape the URL, call `render_video` on the Revid MCP, poll
`get_project_status` until ready, and hand back an MP4 URL — typically in
2–4 minutes, ~40 credits.

> **No MCP support in your agent?** Every skill still works against the raw
> [Revid Public API v3](https://documenter.getpostman.com/view/36975521/2sBXcGEfaB).
> See the *Direct HTTPS fallback* section in
> [`revid-api-foundations`](skills/revid-api-foundations/SKILL.md#direct-https-fallback)
> and the `examples/run.sh` smoke tests.

---

## The 11 skills

| Skill | Input | Output | Revid workflow |
|---|---|---|---|
| [`revid-api-foundations`](skills/revid-api-foundations/SKILL.md) | — *(read first)* | — | foundation |
| [`revid-research-make-and-post`](skills/revid-research-make-and-post/SKILL.md) | Topic + a connected social account | Researched, finished and posted (or scheduled) video | `search_viral_videos` + `script-to-video` + `schedule_publish` |
| [`revid-shopify-product-promo`](skills/revid-shopify-product-promo/SKILL.md) | Shopify / e-com product URL | 30–45 s 9:16 promo | `article-to-video` |
| [`revid-blog-to-avatar-video`](skills/revid-blog-to-avatar-video/SKILL.md) | Blog post URL + avatar image | Talking-head avatar video | `article-to-video` + avatar block |
| [`revid-article-to-short`](skills/revid-article-to-short/SKILL.md) | News / long-form URL | 30–60 s 9:16 short | `article-to-video` |
| [`revid-product-description-to-ad`](skills/revid-product-description-to-ad/SKILL.md) | Product copy (free text) | 15–30 s ad with hook + CTA | `ad-generator` |
| [`revid-tweet-to-talking-head`](skills/revid-tweet-to-talking-head/SKILL.md) | Tweet / thread URL or text | 20–45 s talking-head | `script-to-video` + avatar |
| [`revid-script-to-video`](skills/revid-script-to-video/SKILL.md) | Pre-written script | Voiceover + auto-cut visuals | `script-to-video` |
| [`revid-prompt-to-video`](skills/revid-prompt-to-video/SKILL.md) | One-line idea | AI-written script + video | `prompt-to-video` |
| [`revid-pdf-to-video`](skills/revid-pdf-to-video/SKILL.md) | PDF URL | 30–90 s summary video | `article-to-video` |
| [`revid-news-to-daily-short`](skills/revid-news-to-daily-short/SKILL.md) | Topic / niche | Daily news short (live news) | `article-to-video` w/ `fetchNews=true` |
| [`revid-script-with-custom-media`](skills/revid-script-with-custom-media/SKILL.md) | Script + your own clips | Branded video, no stock | `script-to-video` w/ `useOnlyProvided` |

---

## How a skill works

Every `SKILL.md` is plain Markdown with YAML frontmatter — no SDK, no runtime
lock-in. The shape is uniform across all 12:

```markdown
---
name: revid-shopify-product-promo
description: One-paragraph "when to invoke this and what it does"
metadata: {"openclaw":{"requires":{"config":["REVID_API_KEY"]}}}
---

## When to use this skill
## Inputs
## Step-by-step                ← render_video → get_project_status → (export_video)
## `render_video` arguments    ← the JSON body to pass as MCP tool input
## Polling                     ← short note, full pseudocode in api-foundations
## Failure modes               ← table of error → fix
## See also
```

The agent reads the markdown, fills in `{PRODUCT_URL}` / `{SCRIPT}` /
`{AVATAR_URL}` / etc. from the user's request, calls the `render_video` MCP
tool, polls `get_project_status`, and returns the `videoUrl`.

---

## Repository layout

```
.
├── skills/                  # the 11 SKILL.md skill folders
│   └── <slug>/
│       ├── SKILL.md         # the prompt agents load
│       └── examples/        # runnable JSON payload + run.sh
├── site/                    # Next.js marketplace UI (deployed to Vercel)
├── docs/                    # full Revid API v3 reference
├── examples/                # standalone curl / Python / TypeScript clients
├── shared/                  # cross-skill snippets (polling pseudocode etc.)
├── PUBLISHING.md            # how to publish updates to ClawHub
└── TODO.md                  # v1.1 backlog (watcher skills, agentic flows)
```

---

## Local smoke test (no agent required)

Every skill ships a `run.sh` that exercises it via the **direct HTTPS fallback**
(plain `curl` against `POST /api/public/v3/render`), so you can verify a payload
without an MCP client at hand:

```bash
export REVID_API_KEY="rk_live_…"
cd skills/revid-shopify-product-promo
./examples/run.sh https://allbirds.com/products/mens-tree-runners
# → submits the render, polls until ready, prints videoUrl
```

To verify the MCP path itself, hit the JSON-RPC endpoint directly:

```bash
curl -sS https://www.revid.ai/api/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H "Authorization: Bearer $REVID_API_KEY" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call",
       "params":{"name":"calculate_credits",
                 "arguments":'"$(cat skills/revid-prompt-to-video/examples/honey-prompt.json)"'}}'
```

`calculate_credits` is free and confirms the payload shape — useful CI smoke
test without burning credits.

---

## Publishing updates to ClawHub

Maintainer-only. See [`PUBLISHING.md`](PUBLISHING.md) for the full workflow.
TL;DR:

```bash
clawhub login
clawhub publish ./skills/<slug> --slug <slug> --name "Display Name" --version 1.0.1
```

Auto-updates on installed agents the next time they sync.

---

## Roadmap

See [`TODO.md`](TODO.md). Highlights:

- **Watcher skills** (`revid-blog-watcher`, `revid-shopify-watcher`,
  `revid-news-watcher`, `revid-x-thread-watcher`) — poll a feed, dedupe, fire
  the right base skill on each new item. Closes the *"watch and react"* gap
  identified in v1 review.
- **Pro tier** (`revid-*-pro`) using `videoModel: veo3` / `sora2` for premium
  output.
- **Optional enrichment proxy** that uses our OpenAI key to auto-craft
  `scrapingPrompt` + `stylePrompt` per URL — under evaluation.

---

## Links

- **Live site** — <https://www.revid.ai/skills>
- **Revid MCP server** — <https://www.revid.ai/mcp>
- **Revid API spec** *(direct HTTPS fallback)* — <https://documenter.getpostman.com/view/36975521/2sBXcGEfaB>
- **Revid Studio** (build manually, then "Get API code") — <https://www.revid.ai/create>
- **OpenClaw** — <https://openclaw.ai>
- **ClawHub** — <https://clawhub.ai>

---

## License

MIT. Fork the repo, adapt SKILL.md for any agent runtime — that's the point.
