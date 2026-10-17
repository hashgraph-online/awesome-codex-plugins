# MorningAI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776AB.svg)](https://python.org)
[![Entities](https://img.shields.io/badge/Tracked_Entities-80%2B-orange.svg)](#tracked-entities-80)
[![Sources](https://img.shields.io/badge/Data_Sources-6-green.svg)](#how-it-works)
[![Platforms](https://img.shields.io/badge/Platforms-6%2B-purple.svg)](#install)

**What happened in AI today?** — An AI news tracking skill that runs inside your coding agent. No Docker, no servers — just invoke `/morning-ai` in Claude Code, Codex, OpenCode, Hermes, Cursor, or any SKILL.md-compatible tool. Monitors 80+ entities across 6 sources, generates scored daily reports with optional infographics.

## Features

- **Skill-Native** — Runs inside your AI coding tool (Claude Code, Codex, OpenCode, Hermes, Cursor). No Docker, no servers, no extra infra — just `/morning-ai`
- **Entity-Centric Tracking** — 80+ curated entities across AI labs, model infra, coding agents, apps, vision/media, benchmarks, KOLs. Per-entity cross-platform handles (X, GitHub, HF, arXiv), not keyword search
- **6 Sources** — Reddit, HN, GitHub, HuggingFace, arXiv, X/Twitter. All sources free — no API keys required
- **Smart Scoring** — Two-stage scoring: automated initial scoring from metadata (relevance, engagement, source reliability, recency), then agent evaluation across 5 qualitative dimensions (Impact, Differentiation, Breakthrough, Coverage, Timeliness). Score 7+ items auto-verified across multiple independent sources
- **Custom Watchlists** — Add your own entities via simple markdown files — no code changes needed
- **5 Infographic Styles** — `classic`, `dark`, `glassmorphism`, `newspaper`, `tech` — ready for social sharing
- **Message Digest** — Concise, copy-paste-friendly digest with one-line summaries + links, optimized for WeChat, Telegram, Slack and other messaging platforms
- **Email Subscription** — Push the daily digest to a recipient list via SMTP (Gmail/QQ/Outlook/etc.). Multipart HTML + plain-text, optional infographic attachment, per-recipient language overrides, dry-run preview mode, RFC 8058 one-click unsubscribe headers
- **Scheduled & Unattended** — Idempotent daily runs, no interactive prompts, partial success support

## Sample Output

Here's what a MorningAI daily report looks like — 26 updates scored, deduplicated, and verified across multiple sources in under 50 seconds:

<details>
<summary><b>TLDR — Today's 7+ Score Updates (click to expand)</b></summary>

- **[Model] Anthropic - Claude 4.5 Sonnet released** (9.2): New mid-tier model with +18% SWE-Bench, 200K context, 40% faster output
- **[Model] Google DeepMind - Gemini 2.5 Flash public preview** (8.8): 1M context, native multimodal, free tier on AI Studio
- **[Product] Cursor - Background Agents GA** (8.5): Autonomous agents, cloud sandbox, multi-file refactoring
- **[Model] DeepSeek - V3-0407 open-weight release** (8.3): 671B MoE, MIT license, weights on HuggingFace
- **[Product] OpenAI - Codex CLI open-sourced** (8.0): Terminal agent, suggest/auto-edit/full-auto modes
- **[Benchmark] LMSYS - Chatbot Arena April rankings** (7.5): Claude 4.5 Sonnet #2 overall, Gemini 2.5 Pro #1 coding
- **[Product] GitHub - Copilot Coding Agent preview** (7.3): Autonomous agent on issues, creates PRs in sandbox
- **[Funding] Windsurf - $200M Series C at $3B** (7.1): Largest round in coding tools space

</details>

> Full sample report: [samples/report_2026-04-14.md](samples/report_2026-04-14.md)
> Infographic style previews: [docs/styles.md](docs/styles.md)

## How It Works

```
SKILL.md (loaded by any AI tool)
    |
    +- Step 1: python3 skills/tracking-list/scripts/collect.py  ->  data_{date}.json
    |           (5 sources, concurrent, score + dedupe)
    |           + Agent searches X/Twitter via web search
    |
    +- Step 2: Read skills/tracking-list/SKILL.md  ->  scoring & format spec
    |
    +- Step 3: Write report_{date}.md  ->  structured daily report
    |
    +- Step 4: (optional) Read skills/gen-infographic/SKILL.md  ->  cover image
    |
    +- Step 6: (optional) Read skills/gen-message/SKILL.md  ->  message digest + image
    |
    +- Step 7: (optional) python3 skills/gen-email/scripts/send_email.py  ->  SMTP delivery to subscribers
```

The Python collector runs 5 sources concurrently (Reddit, HN, GitHub, HuggingFace, arXiv), then scores, deduplicates, and cross-links results. The AI tool also searches X/Twitter via web search for tracked entities, then reads the JSON output and generates a formatted Markdown report.

## Install

### Claude Code

```bash
# Step 1: Add marketplace source
marketplace add octo-patch/MorningAI

# Step 2: Install the plugin
/plugin install morning-ai

# Step 3: Restart Claude Code, then use
/morning-ai
```

Or manual install:

```bash
git clone https://github.com/octo-patch/MorningAI.git ~/.claude/skills/morning-ai
```

### ClawHub

```bash
clawhub install morning-ai
```

### OpenCode

OpenCode auto-discovers skills from `.agents/skills/` and `.claude/skills/` directories — the same paths MorningAI already supports. Install as a skill:

```bash
git clone https://github.com/octo-patch/MorningAI.git ~/.config/opencode/skills/morning-ai
```

Or use any of the compatible paths:

```bash
# Any of these work — OpenCode scans all three
git clone https://github.com/octo-patch/MorningAI.git ~/.config/opencode/skills/morning-ai
git clone https://github.com/octo-patch/MorningAI.git ~/.agents/skills/morning-ai
git clone https://github.com/octo-patch/MorningAI.git ~/.claude/skills/morning-ai
```

Then invoke in OpenCode: type `morning-ai` or let the agent load the skill on demand.

> **Tip**: OpenCode also reads `AGENTS.md` at the repo root. If you clone the repo into any project directory, OpenCode will auto-discover it.

### Hermes Agent

Install directly from GitHub:

```bash
hermes skills install octo-patch/MorningAI
```

Or clone manually:

```bash
git clone https://github.com/octo-patch/MorningAI.git ~/.agents/skills/morning-ai
```

Then invoke in Hermes: type `morning-ai` or use `/skills` to browse installed skills.

> **Tip**: Hermes also supports `AGENTS.md` auto-discovery. Clone the repo into your project and Hermes will find it.

### OpenAI Codex

If cloned or forked, Codex auto-discovers the plugin via `.codex-plugin/plugin.json` and `AGENTS.md` — no manual setup needed.

Or install as a skill:

```bash
git clone https://github.com/octo-patch/MorningAI.git ~/.agents/skills/morning-ai
```

### Other Tools (Cursor, etc.)

`AGENTS.md` at the repo root is an open standard recognized by Codex, Cursor, OpenCode, Hermes and more. Clone the repo and the tool will auto-discover it.

### Manual (any tool)

```bash
git clone https://github.com/octo-patch/MorningAI.git
cd MorningAI
```

## Setup

Create a config file at `~/.config/morning-ai/.env`:

```env
GITHUB_TOKEN=gh_xxx               # GitHub (optional, higher rate limits)
MESSAGE_ENABLED=true               # Message digest (optional, for messaging platforms)

# Collector tuning (optional)
ARXIV_LOOKBACK_DAYS=3              # arXiv window in days; default 3 (today + 2 prior)
                                   # — most days arXiv has no fresh papers in a strict 24h window

# Email subscription (optional — push the digest to your inbox / team)
EMAIL_ENABLED=true
EMAIL_RECIPIENTS=you@example.com,teammate@example.com
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_SMTP_USER=you@gmail.com
EMAIL_SMTP_PASSWORD=xxxx-xxxx-xxxx-xxxx   # Gmail App Password (NOT account password)
EMAIL_FROM=MorningAI <you@gmail.com>
```

See [docs/email-setup.md](docs/email-setup.md) for SMTP walkthroughs (Gmail / QQ / Outlook / Alibaba Cloud Enterprise Mail).

Without any API keys, all sources work out of the box: **Reddit**, **Hacker News**, **GitHub**, **HuggingFace**, **arXiv**, and **X/Twitter**.

## Custom Entity Watchlist

Track your own entities beyond the built-in 80+ by creating a markdown file:

```bash
cp entities/custom-example.md entities/custom/my-watchlist.md
```

Edit the file with your entities:

```markdown
## My Startup

| Platform | Value |
|----------|-------|
| X | @my_startup, @founder |
| GitHub | my-startup-org |
| HuggingFace | my-startup |
| Reddit | MyStartup |
```

Each entity starts with a `## Name` heading followed by a `| Platform | Value |` table. Not all platforms are required — add only what you need. Supported platforms: `X`, `GitHub`, `HuggingFace`, `arXiv`, `Web`, `Reddit`, `HN`.

Custom entity files are loaded from (in priority order):

1. `CUSTOM_ENTITIES_DIR` env var
2. `~/.config/morning-ai/entities/`
3. `entities/custom/` in the project directory

Files in `entities/custom/` are gitignored, so your watchlists stay local.

## Usage

Invoke the skill in your AI tool:

```
/morning-ai
```

Or run the collector standalone:

```bash
python3 skills/tracking-list/scripts/collect.py --date 2026-04-14 --output report.json
```

## Infographic Styles

Set `IMAGE_STYLE` in your `.env` to choose a visual style for generated infographics:

| Style | Description |
|-------|-------------|
| `classic` | Clean editorial magazine — off-white background, navy/coral/teal accents **(default)** |
| `dark` | Dark mode — charcoal background, electric blue/violet accents |
| `glassmorphism` | Frosted glass cards on soft gradient background — modern SaaS feel |
| `newspaper` | Classic newsprint — serif typography, cream/black/crimson, broadsheet layout |
| `tech` | Terminal aesthetic — dark background, monospace, cyan/green/amber accents |

```env
IMAGE_STYLE=dark
IMAGE_GEN_PROVIDER=gemini
```

## Tracked Entities (80+)

| Group | Entities | Count |
|-------|----------|-------|
| **ai-labs** | OpenAI, Anthropic, Google, Meta AI, xAI, Microsoft, Qwen, DeepSeek, Doubao, GLM, Kimi, MiniMax, Kling, InternLM, LongCat, Yi, Baichuan, StepFun, Hunyuan | 19 |
| **model-infra** | NVIDIA, Mistral AI, Cohere, Perplexity AI, AWS, Together AI, Groq, Apple/MLX, vLLM, SGLang, KTransformers | 11 |
| **coding-agent** | Cursor, Cline, OpenCode, Droid, OpenClaw, Windsurf, Augment, Aider, Devin, browser-use, Hermes Agent | 11 |
| **ai-apps** | v0, bolt.new, Lovable, Replit, Lovart, Manus, Genspark, Character.ai | 8 |
| **vision-media** | Midjourney, FLUX, Ideogram, Adobe Firefly, Leonardo AI, Stability AI, Lightricks, Runway, Pika, Luma AI, ElevenLabs, Udio/Suno | 12 |
| **benchmarks-academic** | LMSYS, LMArena, Artificial Analysis, HuggingFace, Scale AI SEAL, OpenCompass, LiveBench, WildBench, Terminal-Bench, Vals AI, Design Arena, Vending-Bench, SimpleBench, Repo Bench, Replicate, 5 paper channels, 2 Reddit communities, 4 industry media | 20+ |
| **kol** | Andrej Karpathy, AK, Andrew Ng, Rowan Cheung, Ben Tossell, Elie Bakouch, Swyx, Simon Willison | 8 |
| **trending-discovery** | GitHub Trending, Product Hunt, Hacker News, Reddit | 4 sources |

All items are classified into 4 types: **Product**, **Model**, **Benchmark**, **Funding**.

## Deploy to Multiple Tools

```bash
bash scripts/sync.sh
```

Distributes the skill to `~/.claude/skills/`, `~/.agents/skills/`, `~/.codex/skills/`, and `~/.config/opencode/skills/`.

## License

MIT
