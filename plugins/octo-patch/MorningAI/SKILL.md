---
name: morning-ai
version: "1.3.0"
description: "Daily-scheduled AI news tracker. Collects updates from 80+ AI entities across 6 sources every 24 hours (default 08:00 UTC+8). Generates scored, deduplicated Markdown reports. Supports unattended cron/scheduled execution with date-stamped idempotent output."
argument-hint: 'morning-ai, morning-ai --intro, morning-ai --exclude Funding, morning-ai --depth deep, morning-ai --lang zh, morning-ai --schedule "0 9 * * *", morning-ai --lang zh (with MESSAGE_ENABLED=true for message digest, EMAIL_ENABLED=true for email subscription)'
allowed-tools: Bash, Read, Write, Edit, WebSearch
homepage: https://github.com/octo-patch/MorningAI
repository: https://github.com/octo-patch/MorningAI
author: octo-patch
license: MIT
user-invocable: true
schedule:
  frequency: daily
  default-cron: "0 8 * * *"
  timezone: "Asia/Shanghai"
  idempotent: true
  unattended: true
  estimated-duration: "2-5min"
metadata:
  openclaw:
    emoji: "📰"
    requires:
      optionalEnv:
        - GITHUB_TOKEN
      bins:
        - python3
    files:
      - "skills/*/scripts/collect.py"
      - "skills/*/scripts/gen_infographic.py"
      - "lib/*"
    homepage: https://github.com/octo-patch/MorningAI
    tags:
      - ai
      - news
      - tracking
      - daily-report
      - model
      - product
      - benchmark
      - funding
      - multi-source
      - scheduled
      - cron
      - automated
      - unattended
      - ai-skill
      - clawhub
---

# morning-ai: MorningAI Report Generator

> **Permissions overview:** Collects public data from Reddit, Hacker News, GitHub, HuggingFace, arXiv, and X/Twitter. Requires optional API keys configured in `.env` or `~/.config/morning-ai/.env`. Writes report files to the current working directory. See [Configuration](#configuration) for details.

Track 80+ AI entities across 6 sources. Collect updates from the past 24 hours, score and deduplicate them, and generate a structured Markdown daily report. Covers 4 types: **Product** (feature launches, version releases), **Model** (new models, open-source weights), **Benchmark** (leaderboard changes, papers), **Funding** (rounds, acquisitions, milestones).

---

## `--intro` — Product Introduction

If the user passes `--intro`, display the following introduction and **stop** (do not proceed to data collection):

---

**MorningAI** — Daily AI news tracker that monitors 80+ entities across 6 sources.

**What it does:**
- Collects updates from Reddit, Hacker News, GitHub, HuggingFace, arXiv, and X/Twitter
- Scores and deduplicates items on a 1-10 scale with cross-source verification
- Generates structured Markdown reports with 4 content types: Product, Model, Benchmark, Funding
- Optional: infographic images (5 visual styles), message digests (WeChat/Telegram/Slack), social media copy (X/Xiaohongshu)

**Sources (all free, no API keys required for basic usage):**
| Source | Method | API Key |
|--------|--------|---------|
| Reddit | Public JSON | Not needed |
| Hacker News | Algolia API | Not needed |
| GitHub | REST API | Optional (`GITHUB_TOKEN` for higher rate limits) |
| HuggingFace | Public API | Not needed |
| arXiv | Public API | Not needed |
| X/Twitter | Web search | Not needed |

**Quick start:**
```
/morning-ai                     # Run with defaults (English, all types)
/morning-ai --lang zh           # Chinese report
/morning-ai --depth deep        # Comprehensive collection
/morning-ai --exclude Funding   # Skip funding news
```

**Optional features (require API keys):**
- Infographic images: set `IMAGE_GEN_PROVIDER` + provider API key
- Social media copy: set `SOCIAL_ENABLED=true`
- Message digest: set `MESSAGE_ENABLED=true`
- Email subscription: set `EMAIL_ENABLED=true` + SMTP credentials (Gmail/QQ/Outlook/etc.)

**Config file:** `~/.config/morning-ai/.env` — run `/morning-ai` without config to trigger guided setup.

**Version:** 1.3.0 | [GitHub](https://github.com/octo-patch/MorningAI) | [ClawHub](https://clawhub.ai/skills/morning-ai)

---

After displaying the introduction, **stop**. Do not proceed to Step 0 or data collection.

---

## Step 0: Configuration Gate (REQUIRED — must complete before any other step)

**Run this command FIRST before doing anything else:**

```bash
if [ -f "$HOME/.config/morning-ai/.env" ] || [ -f ".claude/morning-ai.env" ] || [ -f ".env" ]; then echo "CONFIG_STATUS=READY"; else echo "CONFIG_STATUS=MISSING"; fi
```

**Branch on the output:**

- **If output is `CONFIG_STATUS=READY`** — read the config file, report which sources are active, then proceed to Step 1.
- **If output is `CONFIG_STATUS=MISSING`** — **STOP. You MUST complete the First-Time Onboarding below before proceeding to Step 1.**

### First-Time Onboarding (when `MISSING`)

> **CRITICAL: STOP HERE.**
> You MUST complete all onboarding steps below interactively with the user.
> Do NOT run Step 1 (data collection) until a config file exists and the gate check returns `READY`.
> Running data collection without configuration will produce incomplete results.

Walk the user through setup interactively, waiting for their response at each step:

1. **Welcome** — briefly explain what morning-ai does: tracks 80+ AI entities across 6 sources (Reddit, Hacker News, GitHub, HuggingFace, arXiv, X/Twitter), generates scored daily reports
2. **Show what works for free** — 6 sources (5 need no API keys, 1 optional):
   - Reddit (public JSON), Hacker News (Algolia API), HuggingFace (public API), arXiv (public API), X/Twitter (web search)
   - GitHub (public API, optional `GITHUB_TOKEN` for higher rate limits)
3. **Ask the user** if they want to enable GitHub with higher rate limits:

| Key | Source | Get it at |
|-----|--------|-----------|
| `GITHUB_TOKEN` | GitHub releases & repos (higher rate limit) | https://github.com/settings/tokens |

4. **Ask about infographics** (optional):

| Key | Description |
|-----|-------------|
| `IMAGE_GEN_PROVIDER` | Provider: `gemini` \| `minimax` \| `none` (default: none) |
| `IMAGE_STYLE` | Style: `classic` \| `dark` \| `glassmorphism` \| `newspaper` \| `tech` |
| `GEMINI_API_KEY` | Google Gemini/Imagen (https://aistudio.google.com/apikey) |
| `MINIMAX_API_KEY` | MiniMax global(https://www.minimax.io) |
| `MINIMAX_API_KEY` | MiniMax cn (https://platform.minimaxi.com) |

5. **Ask about social content distribution** (optional):
   - Enable social content generation? Set `SOCIAL_ENABLED=true`
   - Which platforms? X (Twitter), Xiaohongshu (Little Red Book), or both
   - For advanced multi-account/multi-style setup, create `~/.config/morning-ai/social_channels.json` (see `skills/gen-social/SKILL.md` for schema). For quick single-channel setup, just set `SOCIAL_PLATFORM`, `SOCIAL_STYLE`, and `SOCIAL_LANG` env vars.

6. **Ask about message digest** (optional):
   - Enable concise message digest for sharing on messaging platforms (WeChat, Telegram, Slack)?
   - If yes: set `MESSAGE_ENABLED=true`
   - Optional settings: `MESSAGE_MIN_SCORE` (default 5), `MESSAGE_MAX_ITEMS` (default 10), `MESSAGE_LINKS` (`bottom` or `inline`), `MESSAGE_CATEGORY_BALANCE` (default true, distributes slots across content types)

7. **Create the config file** — collect the keys the user provides and write them to `~/.config/morning-ai/.env` in `KEY=value` format (one per line). Create the directory if needed: `mkdir -p ~/.config/morning-ai`
8. **Confirm** — show how many sources are now active (N/9)
9. **Verify** — re-run the gate check to confirm `CONFIG_STATUS=READY`:
   ```bash
   if [ -f "$HOME/.config/morning-ai/.env" ] || [ -f ".claude/morning-ai.env" ] || [ -f ".env" ]; then echo "CONFIG_STATUS=READY"; else echo "CONFIG_STATUS=MISSING"; fi
   ```
   Only proceed to Step 1 if the output is `READY`.
10. If the user wants to skip API key setup and use only free sources, create a minimal config file first, then proceed to Step 1:
   ```bash
   mkdir -p ~/.config/morning-ai && echo "# morning-ai config — free sources only" > ~/.config/morning-ai/.env
   ```

---

## Language

| Parameter | Default | Example |
|-----------|---------|---------|
| `--lang` | `en` (English) | `--lang zh` (Chinese), `--lang ja` (Japanese) |

**Rules:**
- **Default is English. Unless `--lang` is explicitly specified, the report MUST be written entirely in English.** All report text — titles, summaries, section headers, table labels, bullet points, "Why It Matters" analysis, and all other human-readable content — must be in English.
- If `--lang` is specified, use that language for all human-readable content instead.
- **Entity names are proper nouns** (OpenAI, DeepSeek, Midjourney, etc.) — keep them as-is regardless of language.
- When source data is in a different language than the target (e.g. Chinese source → English report), **translate it** into the target language during report generation. Do NOT leave untranslated fragments.
- The `--lang` setting also applies to infographic prompt content (see Step 4).

---

> **Prerequisite:** Step 0 must have returned `CONFIG_STATUS=READY`. If you have not completed Step 0, go back and run it now.

## Step 1: Data Collection

Run the Python collector to gather data from automated sources:

```bash
cd {SKILL_DIR} && python3 skills/tracking-list/scripts/collect.py --date {YYYY-MM-DD} --depth default -o {CWD}/data_{YYYY-MM-DD}.json
```

**Parameters:**
- `--date`: Target date, default today (YYYY-MM-DD)
- `--depth`: Collection depth — `quick` (fast, fewer results), `default`, or `deep` (comprehensive)
- `--skip`: Sources to deliberately skip — e.g. `--skip arxiv`. **Default: skip nothing.** Deny-list on purpose: previous `--sources` allow-list let agents silently drop a collector by forgetting to list it (arxiv was missing from prod for 5 days that way). Naming the skipped source makes the omission visible.
- `-o`: Output JSON file path

**What it does:**
- Runs 6 collectors concurrently (Reddit, HN, GitHub, HuggingFace, arXiv, X/Twitter via sub-agent)
- Time window: `[Yesterday 08:00, Today 08:00) UTC+8`
- Pipeline: collect → score (1-10) → deduplicate → cross-source link → verification bonus
- Returns structured JSON with all items, stats, and collection metadata

**Timeout:** Allow up to 5 minutes for default depth, 10 minutes for deep.

If the user provides `--exclude` types (e.g. `--exclude Funding`), note which **content type** to filter out in Step 3 (this is a Step 3 filter on item types, not a `collect.py` flag).

### X/Twitter Search

After the automated collection completes, use **web search** to discover recent X/Twitter updates from tracked entities. The tracked X handles are listed in `{SKILL_DIR}/lib/entities.py` under `X_HANDLES`.

#### Search Strategy: Multi-Layer Account Checking

Search X/Twitter in **three layers**, in priority order:

**Layer 1 — Official Accounts** (highest priority):
Search for recent posts from official company/product accounts. Handles are listed in entity files under `{SKILL_DIR}/entities/`.
- Focus: Model releases, product launches, API updates, pricing changes

**Layer 2 — CEO / Core Personnel Accounts**:
Check key people's accounts for announcements, previews, and context that official accounts may not cover. Listed as "Key People" in each entity file.
- Focus: Early previews, strategic context, technical details, competitive commentary

**Layer 3 — KOLs & Benchmark Institutions**:
Check AI opinion leaders and evaluation accounts for independent analysis, benchmark results, and trending discoveries. See `{SKILL_DIR}/entities/kol.md` and `{SKILL_DIR}/entities/benchmarks-academic.md`.
- Focus: Paper highlights, benchmark rankings, community trends, independent testing

#### Search Execution

For each search depth:

| Depth | Layer 1 (Official) | Layer 2 (Personnel) | Layer 3 (KOLs) |
|-------|-------------------|--------------------|-----------------| 
| `quick` | Top 5 entities by priority | Skip | Skip |
| `default` | All major entities (~20) | Top CEO accounts (~10) | Top KOLs (~5) |
| `deep` | All entities with X handles | All personnel accounts | All KOLs + benchmark accounts |

Use web search queries like:
- `site:x.com @{handle} since:{yesterday}` — for specific account posts
- `site:x.com "{entity name}" AI announcement` — for broader discovery
- `site:x.com AI model release OR benchmark OR open-source {date}` — for trending AI news

#### RT/Quote Tweet Handling

When a discovered post is a retweet (RT) or quote tweet:
1. **Trace to the original post** — the event timestamp is the **original post time**, not the RT/quote time
2. Validate the **original post time** falls within the 24-hour collection window `[Yesterday 08:00, Today 08:00) UTC+8`
3. Use the **original post URL** as the `source_url`, not the RT/quote URL
4. Credit the original author in `source_label` (e.g., `"@AnthropicAI on X (via @karpathy RT)"`)

#### Timeliness Validation

- All X post times must be converted to **UTC+8** for window validation
- The collection window is `[Yesterday 08:00, Today 08:00) UTC+8`
- Posts outside this window are **rejected** — do NOT include them regardless of relevance
- For RT/quote tweets, validate the **original post time**, not the retweet time

#### Source Priority for X-Sourced Items

| Priority | Source Type | Credibility |
|----------|-----------|-------------|
| 1 | Official blog / changelog | Highest |
| 2 | Official X/Twitter account | High |
| 3 | API changelog / docs | High |
| 4 | Official GitHub release | High |
| 5 | CEO / core personnel X account | Medium-High |
| 6 | Benchmark institution X account | Medium |
| 7 | KOL X account | Reference only — requires cross-verification |

Items sourced **only** from KOL accounts (Priority 7) should be scored conservatively and flagged for cross-verification with an official source.

#### Incorporating X Findings

For each verified X/Twitter update:
1. Create a TrackerItem with `source: "x"`, `source_url` pointing to the original tweet, and `source_label` as `"@{handle} on X"`
2. If the same event was already found by an automated collector (Reddit, HN, GitHub, etc.), merge it as a `cross_ref` rather than creating a duplicate — this strengthens the verification score
3. If it's a genuinely new finding not in the automated data, add it as a new item with appropriate scoring
4. **KOL voice detection** (Layer 3 items only): classify the post and tag accordingly:
   - **KOL original commentary** — independent analysis, paper review, hot-take, prediction, technical review, framework critique. Set `is_kol_voice: true` on the item. **Do NOT dedup-merge into official-source items** even if discussing the same topic — the KOL's *take* is the value, not the underlying news. Score conservatively (4-7 typically) but keep as a standalone item.
   - **KOL restating an official announcement** — direct paraphrase / quote of vendor news with no added angle. Treat as `cross_ref` to the official item (existing behavior). Do NOT set `is_kol_voice`.
   - When in doubt: if the post adds an opinion, comparison, or analysis the official source doesn't have → it's a voice. If it's just "X just shipped Y, link" → it's a cross_ref.

---

## Step 2: Read Specifications

After data collection completes, read the tracking specification to understand scoring criteria, record format, and timeliness rules:

```
Read {SKILL_DIR}/skills/tracking-list/SKILL.md
```

This specification defines:
- 4 tracking types (Product / Model / Benchmark / Funding) with include/exclude criteria
- Source priority rankings
- Scoring criteria (1-10 scale with 5 dimensions)
- Timeliness validation rules (event date ≠ page date)
- Cross-verification requirements (7+ scores need 2+ independent sources)
- Record format for the report

**Internalize the specification before writing the report.** Pay special attention to the scoring reference tables and type classification guide.

---

## Step 3: Generate Report

1. Read the JSON output from Step 1
2. Read the report template: `Read {SKILL_DIR}/templates/report.md`
3. Generate `report_{YYYY-MM-DD}.md` in the working directory

**Report generation rules:**
- **Language**: Default is **English**. Write ALL content in English unless `--lang` is explicitly specified. If source data is in a different language, translate it. Entity names (proper nouns) stay as-is.
- **Source links**: Every item MUST include a clickable source link `[Source Name](URL)` pointing to the original content. This applies to all sections: TLDR, detailed entries, and compact table rows.
- **Detail quality**: Summary bullet points must include specific details — version numbers, percentage improvements, parameter counts, pricing, availability dates, benchmark scores. Avoid vague descriptions without concrete numbers.
- **Factual verification**: See `skills/tracking-list/SKILL.md` → "Factual Detail Verification" for the full protocol. Never write a number from memory or inference — omit unverifiable details.
- Filter out any excluded types (if `--exclude` was specified)
- Sort items by score within each type section
- **TLDR section**: Only items with score 7+ (across all types), sorted high to low. Each item includes a one-line summary with specifics, plus an _Impact_ sentence explaining why it matters. Must include a source link `[[Source](URL)]` at the end.
- **Type sections**: Group by score range (9-10 / 7-8 / 5-6 / 3-4)
- For items with score 7+, include multi-source verification if available
- **Item format**: Follow the record format defined in the tracking specification (read in Step 2), including detail level requirements, "Why It Matters", and "Key Data" sections. For mid-score (5-6) and lower-score (3-4) items, use the compact formats defined there.
- **KOL Voices section** (NEW): From items where `is_kol_voice: true` (set during Step 1 KOL voice detection), select the top 3-5 by score, capped to **max 1 item per KOL handle** (no double-dipping). For each item write:
  - KOL display name + linked X handle + score
  - One-line takeaway in the report's language (`--lang`) explaining why this view matters or what's the unique angle
  - A short excerpt (≤80 chars) from the original post as a blockquote, **kept in the post's original language** (don't translate the quote — preserve voice)
  - A source link `[[Original]({source_url})]`
  If fewer than 3 items qualify, list what's available + append `_(Today's KOL channels were quiet — only N items qualified.)_`. If 0 qualify, write `_Today's KOL channels were quiet._`
- Fill in the statistics summary table

---

## Step 4: Generate Infographics (Optional)

**This step is optional. Skip if no image generation capability is available or configured.**

1. Read the infographic specification:
   ```
   Read {SKILL_DIR}/skills/gen-infographic/SKILL.md
   ```

2. **Generate cover + per-type sections + stitch** (see **Image Strategy** in `skills/gen-infographic/SKILL.md`):
   - Always generate cover (9:16 portrait) + per-type section images (9:16 portrait), then stitch into one long image

3. **Cover image**: Sort by score and select the **top 4-5** updates (across all types). Build prompt using the Cover Prompt Template (9:16 portrait).

4. **Per-type section images**: For each type (Model/Product/Benchmark/Funding/KOL) with qualifying items, build a prompt using the Per-Type Prompt Template (9:16 portrait).
   - Default (`IMAGE_GEN_TYPES=auto`): only types with 7+ score items. **Exception**: the KOL section image is generated whenever ≥1 item has `is_kol_voice: true` (regardless of score), since KOL voices are scored conservatively (4-7) by design — applying the 7+ gate would suppress the section image even when the report has a populated KOL Voices block.
   - KOL section image filename: `news_infographic_{YYYY-MM-DD}_kol.png`. Insert at the top of the report's `## KOL Voices` section (the template already has a stub: `![KOL Voices](news_infographic_{DATE}_kol.png)`).
   - Set `IMAGE_GEN_TYPES=all` for all types, `none` for cover only

5. Generate images and stitch:

   **Option A** — Native tool (Claude Code or other tools with built-in image generation):
   Use your tool's built-in image generation capability, one call per image. Then stitch sections together.

   **Option B** — Python script batch mode (any environment, requires `IMAGE_GEN_PROVIDER` configured):
   Build a manifest JSON with all prompts and outputs, then run:
   ```bash
   cd {SKILL_DIR} && python3 skills/gen-infographic/scripts/gen_infographic.py --batch {CWD}/manifest.json --stitch
   ```
   Supported providers: `gemini`, `minimax`. See [Configuration](#configuration) for API keys. Requires `pip install Pillow`.

   The final output is **`news_infographic_YYYY-MM-DD_combined.png`** — a single long image containing cover + all section images.

6. Insert images into the report:
   - Combined long image at the beginning
   - Individual per-type images optionally at the top of each type section

---

## Step 5: Generate Social Content (Optional)

**Skip this step if `SOCIAL_ENABLED` is not `true` or no social channels are configured.**

Generate platform-optimized copy and images for social media distribution (X, Xiaohongshu, etc.).

1. Read the social content specification:
   ```
   Read {SKILL_DIR}/skills/gen-social/SKILL.md
   ```

2. Load channel configuration:
   - If `SOCIAL_CHANNELS_FILE` exists → read the JSON channel list
   - Else if `SOCIAL_PLATFORM` env var is set → build a single channel from `SOCIAL_PLATFORM` + `SOCIAL_STYLE` + `SOCIAL_LANG`
   - Else → skip this step

3. For each channel:
   a. Read the channel's template: `{SKILL_DIR}/skills/gen-social/templates/{platform}/{style}.md`
   b. Select top items from the report data (filter by `min_score`, limit by `items`, translate if `lang` differs from source)
   c. Generate copy following the template's format rules, tone, and character limits
   d. **Validate character counts** — each tweet ≤ 280 chars, Xiaohongshu title ≤ 20 chars, body ≤ 1000 chars
   e. Write copy to `{CWD}/social/social_{YYYY-MM-DD}_{channel_id}.md`
   f. If channel has `image: true` — generate platform-adapted images using the same providers as Step 4
      - X: 16:9 or 1:1 aspect ratio
      - Xiaohongshu: 3:4 portrait, carousel multi-image supported
   g. Write images to `{CWD}/social/social_{YYYY-MM-DD}_{channel_id}_{N}.png`

4. Write manifest to `{CWD}/social/social_{YYYY-MM-DD}_manifest.json` listing all generated files

**Channel config examples**: See `skills/gen-social/SKILL.md` for the full JSON schema and quick-setup env vars.

---

## Step 6: Generate Message Digest (Optional)

**Skip this step if `MESSAGE_ENABLED` is not `true`.**

Generate a concise, share-friendly message digest suitable for messaging platforms (WeChat, Telegram, Slack, etc.). The digest provides bold titles with one-line summaries and reference links — optimized for copy-paste sharing.

1. Read the message specification:
   ```
   Read {SKILL_DIR}/skills/gen-message/SKILL.md
   ```

2. Read the digest template:
   ```
   Read {SKILL_DIR}/skills/gen-message/templates/digest.md
   ```

3. Select items from the report data (`data_{YYYY-MM-DD}.json`):
   - Filter by score >= `MESSAGE_MIN_SCORE` (default: 5)
   - Apply category balance if `MESSAGE_CATEGORY_BALANCE=true` (default): per-type slot caps (product max 4, model max 3, benchmark max 2, financing max 2), fill remaining with top-scoring items
   - Sort by importance score descending
   - Limit to `MESSAGE_MAX_ITEMS` (default: 10)
   - Use `MESSAGE_LANG` for language (default: from `--lang`)

4. Generate text digest following the template format:
   - Write to `{CWD}/message_{YYYY-MM-DD}.md`
   - Each item: emoji marker + **bold title** + one-line summary + source link
   - Source link (`🔗 URL`) after each item by default (or grouped at bottom if `MESSAGE_LINKS=bottom`)
   - Language-specific header and footer

5. If image generation is available (`IMAGE_GEN_PROVIDER` is configured):
   - Build a 9:16 portrait image prompt from the specification's image prompt template
   - Generate `{CWD}/message_{YYYY-MM-DD}.png` using the same image generation method as Step 4 (native tool or Python script)

**Output files:**
- `message_{YYYY-MM-DD}.md` — copy-paste text for messaging
- `message_{YYYY-MM-DD}.png` — accompanying image (only if image generation is configured)

---

## Step 7: Send Email Subscription (Optional)

**Skip this step if `EMAIL_ENABLED` is not `true`.**

Deliver the daily digest as multipart HTML email via SMTP to a configured recipient list. This is the only step that performs network egress to subscribers — gen-message / gen-social only generate local files.

1. Read the email specification:
   ```
   Read {SKILL_DIR}/skills/gen-email/SKILL.md
   ```

2. Run the sender script:
   ```bash
   python3 {SKILL_DIR}/skills/gen-email/scripts/send_email.py --date {YYYY-MM-DD}
   ```
   The script:
   - Reads `data_{YYYY-MM-DD}.json` and applies the same selection rules as gen-message (filter by `EMAIL_MIN_SCORE`, category balance, sort by importance, cap at `EMAIL_MAX_ITEMS`)
   - Loads recipients from `EMAIL_RECIPIENTS` (env, comma-separated) or `EMAIL_RECIPIENTS_FILE` (default `.claude/recipients.json`)
   - Renders HTML + plain text bodies, writes local previews `email_{YYYY-MM-DD}.html` and `email_{YYYY-MM-DD}.txt`
   - If `EMAIL_DRY_RUN=true`: stops after writing previews (no SMTP traffic)
   - Otherwise sends to each recipient via SMTP, attaches `message_{YYYY-MM-DD}.png` when present, sleeps `EMAIL_RATE_LIMIT_DELAY` seconds between sends
   - Writes `email_{YYYY-MM-DD}_manifest.json` with per-recipient `status` (`sent` / `failed`) and error text

3. **Required env vars** (the script exits with a clear error if missing):
   - `EMAIL_SMTP_HOST`, `EMAIL_SMTP_USER`, `EMAIL_SMTP_PASSWORD`
   - At least one recipient via `EMAIL_RECIPIENTS` or `EMAIL_RECIPIENTS_FILE`

**Output files:**
- `email_{YYYY-MM-DD}.html` / `email_{YYYY-MM-DD}.txt` — local previews of what was sent
- `email_{YYYY-MM-DD}_manifest.json` — send status per recipient (for retry / monitoring)

See `skills/gen-email/SKILL.md` for full configuration and `docs/email-setup.md` for SMTP provider quick-start (Gmail / QQ / Outlook / Alibaba Cloud Enterprise Mail).

---

## Entity Reference

The `entities/` directory contains detailed entity registries organized by tracking group:

| File | Scope | Entities |
|------|-------|----------|
| `entities/ai-labs.md` | Frontier AI Labs + China AI | OpenAI, Anthropic, Google, Meta AI, xAI, Microsoft, Qwen, DeepSeek, + 11 more |
| `entities/model-infra.md` | Model Infrastructure | NVIDIA, Mistral, Cohere, Perplexity, AWS, Together, Groq, Apple |
| `entities/coding-agent.md` | Coding Agent | Cursor, Cline, OpenCode, Droid, OpenClaw, Windsurf, + 5 more |
| `entities/ai-apps.md` | AI Applications | v0, bolt.new, Lovable, Replit, Lovart, Manus, + 2 more |
| `entities/vision-media.md` | Vision & Media | Midjourney, Runway, Pika, FLUX, ElevenLabs, + 7 more |
| `entities/benchmarks-academic.md` | Benchmarks & Academic | LMSYS, HuggingFace, arXiv channels, industry media |
| `entities/kol.md` | Key Opinion Leaders | Andrej Karpathy, AK, Andrew Ng, Swyx, Simon Willison, + 3 more |
| `entities/trending-discovery.md` | Trending Discovery | GitHub Trending, Product Hunt, Hacker News, Reddit |

Each file lists X/Twitter accounts, key people, official blogs, changelogs, GitHub repos, and other source URLs for every tracked entity. Read these files when you need to verify or supplement the automated collection.

### Custom Entities

Users can add their own tracked entities by placing markdown files in `entities/custom/` (or `~/.config/morning-ai/entities/`, or a path set via `CUSTOM_ENTITIES_DIR`). Custom entity files use a simplified format — see `entities/custom-example.md` for the template. Custom entities are automatically merged into the built-in registries at runtime and collected alongside the default 80+ entities.

---

## Scheduling

Morning-AI is designed for daily automated execution. Each run produces date-stamped files (`report_YYYY-MM-DD.md`, `data_YYYY-MM-DD.json`), making it safe to run on a recurring schedule.

### Schedule Configuration

Use `--schedule` to set a custom cron expression (default: `0 8 * * *`):

| Parameter | Format | Default | Example |
|-----------|--------|---------|---------|
| `--schedule` | Cron expression (5-field) | `0 8 * * *` (daily 8am) | `0 9 * * 1-5` (weekdays 9am) |

The schedule is passed to the agent's native scheduler (CronCreate, /loop, system cron, etc.). Morning-AI itself does not run a scheduler — it relies on the host agent or system to trigger runs.

### Unattended Behavior

- **Idempotent**: Re-running on the same date overwrites previous output — no duplicate accumulation
- **No interactive prompts**: All steps run without user input when API keys are configured
- **Partial success**: If some sources fail, the report generates with available data and logs warnings
- **Timeout**: Allow 3 min (default depth) or 5 min (deep)

### Agent Integration Examples

**Claude Code** (CronCreate / loop):
```
/loop 24h /morning-ai
```

With custom schedule:
```
/morning-ai --schedule "0 9 * * 1-5"
```

**System cron** (manual setup):
```bash
0 8 * * * cd /path/to/workspace && claude -p "/morning-ai"
```

**OpenClaw / always-on bot**:
```yaml
schedule: "0 8 * * *"
skill: morning-ai
```

---

## Configuration

### Config File Locations (priority order)

1. **Environment variables** (highest priority)
2. **Project config**: `.env` in skill directory
3. **Global config**: `~/.config/morning-ai/.env`

### Config File Format

```bash
# ~/.config/morning-ai/.env
GITHUB_TOKEN=ghp_xxx
```

### Free Sources (no API key needed)

| Source | API | Rate Limit |
|--------|-----|-----------|
| Reddit | Public JSON | Generous |
| Hacker News | Algolia API | Generous |
| GitHub | Public API (optional token for higher limits) | 60 req/hr (unauthenticated) |
| HuggingFace | Public API | Generous |
| arXiv | Public API | Generous |
| X/Twitter | Web search | Generous |

### Message Digest Configuration

See `skills/gen-message/SKILL.md` for message digest configuration variables (`MESSAGE_ENABLED`, `MESSAGE_MIN_SCORE`, `MESSAGE_MAX_ITEMS`, `MESSAGE_CATEGORY_BALANCE`, etc.).

### Email Subscription Configuration

See `skills/gen-email/SKILL.md` for the full list of email variables (`EMAIL_ENABLED`, `EMAIL_RECIPIENTS`, `EMAIL_SMTP_HOST/PORT/USER/PASSWORD/TLS`, `EMAIL_FROM`, `EMAIL_LANG`, `EMAIL_MIN_SCORE`, `EMAIL_DRY_RUN`, etc.) and `docs/email-setup.md` for SMTP provider walkthroughs.

---

## Security & Permissions

- **Data access**: Reads public web/platform data only. No private or authenticated content is accessed.
- **API keys**: Stored locally in `.env` files. Never transmitted except to their respective APIs.
- **File writes**: Only writes report files (`report_*.md`, `data_*.json`), message digest files (`message_*.md`, `message_*.png`), and cache files to the skill/working directory.
- **Network**: Outbound HTTP/HTTPS requests to public APIs (Reddit, GitHub, etc.). No inbound connections.
- **No telemetry**: No usage data is collected or sent anywhere.
