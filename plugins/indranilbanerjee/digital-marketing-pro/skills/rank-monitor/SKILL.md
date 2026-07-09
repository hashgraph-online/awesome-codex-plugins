---
name: rank-monitor
description: "Monitor keyword rankings and SERP features. Use when: tracking keyword positions, detecting ranking drops, alerting on position changes, or tracking SERP-feature presence (AI Overviews, snippets, PAA, local pack)."
argument-hint: "[brand-name] [--features]"
---

# /digital-marketing-pro:rank-monitor

## Purpose

Set up and manage keyword ranking monitoring — and, with `--features`, SERP-feature tracking in the same run. Track target keyword positions across Google, establish baselines, detect drops greater than 5 positions, and generate alerts when rankings change significantly. In `--features` mode, also track which SERP features appear for each query (AI Overviews, Featured Snippets, People Also Ask, Knowledge Panels, Local Pack, Image Pack, Video Carousel, Shopping) and whether the brand owns them. This gives ongoing visibility into organic performance — catching ranking declines early, spotting upward trends, and tracking the increasingly feature-rich results page.

> **Merged skill (was `rank-monitor` + `serp-tracker`).** SERP-feature tracking is now the `--features` mode of this one skill. The old `/digital-marketing-pro:serp-tracker` is a deprecation pointer to here.

### Data sources (read this before configuring)

- **Google Search Console MCP** is the authoritative position + impressions source for verified properties. GSC returns per-query/per-page positions, impressions, clicks, and CTR — it does **not** return the full per-query SERP-feature layout or AI Overview citation lists. Do not claim otherwise.
- **Rank-tracker MCPs** (Ahrefs / Semrush / SE Ranking, if connected) fill in positions for keywords/competitors GSC can't see and provide their own SERP-feature flags.
- **Moz MCP** (`mcp-moz`) is **optional** — verify the package exists on npm before use (`npm view mcp-moz`); `npx` executes remote code, so don't wire an unverified package. If Moz isn't connected, use GSC + whichever rank-tracker MCP the brand already has.
- **AI Overview presence** in `--features` mode records only *whether* an AI Overview appeared and *whether the brand was cited in it* (a binary SERP-feature signal). For scored AI-visibility measurement across the 6 canonical AI surfaces, use `/digital-marketing-pro:geo-monitor` / `/digital-marketing-pro:aeo-audit` (the canonical AI-visibility scoring standard) and, for actual impressions, `/digital-marketing-pro:gsc-ai-performance`. Do not re-implement AI-visibility scoring here.

## Input Required

The user must provide (or will be prompted for):

- **Target keywords**: A list of keywords to monitor — provided directly, imported from a CSV or Google Sheet, or pulled from the brand's existing keyword tracking list at `${CLAUDE_PLUGIN_DATA}/{brand}/seo/keywords.json`. Keywords should include search intent classification (informational, navigational, transactional, commercial) if available
- **Mode**: default is rankings-only. Pass `--features` to also build the SERP-feature presence matrix per query in the same run
- **Monitoring frequency**: `daily` or `weekly` — daily for high-priority head terms and active-campaign keywords (and volatile feature sets), weekly for long-tail and lower-priority terms
- **Alert thresholds**: Position change that triggers an alert — default is >5 position drop. Customizable per keyword group (e.g., >3 for brand terms, >5 for head terms, >10 for long-tail). Both drop and gain thresholds are supported
- **Competitor domains (optional)**: Domains to track alongside the brand for the same keywords / features — up to 10
- **Device type**: `mobile`, `desktop`, or `both`
- **Target country**: The Google locale to check rankings in — e.g., US, UK, AU, CA, IN

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Capture current rankings baseline**: Query the connected rank sources (GSC MCP, plus any rank-tracker / Moz MCP available) for the current ranking position of each target keyword. Record position, ranking URL, click-through rate and impressions from GSC where available. In `--features` mode, also record which SERP features are present for the query (from the rank-tracker's feature flags or manual observation) and the owning domain per feature. For competitor domains, capture their positions (and feature ownership) for the same keywords.
3. **Configure monitoring schedule**: Save the keyword list, mode (`rankings` or `rankings+features`), monitoring frequency, alert thresholds, competitor domains, device type, and target country to `${CLAUDE_PLUGIN_DATA}/{brand}/seo/rank-monitor/config.json`. Create or update the baseline snapshot at `${CLAUDE_PLUGIN_DATA}/{brand}/seo/rank-monitor/baseline.json` with the current positions (and, in `--features` mode, the feature matrix) as the reference point.
4. **On each monitoring check: query and compare**: Pull current positions for all tracked keywords. Compare each keyword's current position to both the baseline (original position when monitoring started) and the previous check (last recorded position). Calculate absolute change from baseline, change since last check, rolling 7-day and 30-day trend direction, and average position across all tracked keywords. In `--features` mode, diff the feature matrix against the previous snapshot (features gained/lost, ownership changes, AI Overview appearance/citation changes).
5. **Detect significant changes**: Identify keywords that crossed alert thresholds — drops exceeding the configured position threshold, keywords that fell from page 1 (positions 1-10) to page 2 or beyond, keywords that gained >5 positions (potential quick wins), and (in `--features` mode) new SERP-feature appearances or losses for the brand's ranking URLs, plus competitor rank/feature changes that moved them above or below the brand.
6. **Generate alert if thresholds are breached**: Categorize alerts by severity — `minor` for 3-5 position drops (monitor), `major` for 5-10 position drops (investigate content freshness, technical issues, or competitor activity), `critical` for >10 position drops or page 1 → page 2 transitions (immediate investigation — check for algorithm updates, manual actions, technical errors, or content cannibalization). In `--features` mode, treat a lost owned Featured Snippet or a lost AI Overview citation as at least `major`. Include recommended next steps for each severity level.

## SERP-feature tracking (`--features` mode)

When `--features` is set, the run also builds a query-by-feature matrix. Tracked features and how to read them:

| Feature | What "owned" means | Optimization signal |
|---|---|---|
| **AI Overview** | An AI Overview appeared AND the brand's URL is one of its cited sources | Binary citation-presence signal only. For scored AI visibility use `/digital-marketing-pro:geo-monitor` |
| **Featured Snippet** | Brand holds position 0 for the query | Format for extraction: paragraph (40-60 words), list (5-8 items), or table |
| **People Also Ask** | A brand URL answers a PAA question for the query | Target PAA questions with FAQ-style H2/H3 content |
| **Knowledge Panel** | Panel shows for the brand entity | Strengthen entity signals (Wikidata, GBP, structured data) — see `/digital-marketing-pro:entity-audit` |
| **Local Pack** | Brand appears in the map 3-pack | GBP optimization + local schema — see `/digital-marketing-pro:local-seo` |
| **Image / Video Carousel** | Brand asset appears in the carousel | Optimize alt text / filenames (images) or titles, descriptions, transcripts (video) |
| **Shopping / Sitelinks** | Brand listing present | Product schema / site structure |

Feature opportunities are scored by achievability (how close the brand is to winning the feature given current position and content format) × traffic impact (estimated CTR impact given query volume and feature prominence).

## Output

A structured ranking (and, in `--features` mode, SERP-feature) report containing:

- **Ranking snapshot**: Current positions for all tracked keywords — position, ranking URL, device, country, date, comparison to baseline and previous check with directional indicators (up, down, stable)
- **Change report**: Position changes since baseline and since last check — sorted by largest drops first, with 7-day and 30-day trend sparklines
- **Alert summary**: Keywords needing attention — grouped by severity (critical, major, minor) with specific position changes, affected URLs, and recommended investigation steps
- **SERP-feature matrix** *(--features)*: Query-by-feature grid showing which features appear, who owns them (brand, competitor, or other), and change since last snapshot — including AI Overview appearance + brand-citation status
- **Feature opportunity list** *(--features)*: Ranked unowned features the brand could realistically target, with specific content/schema recommendations
- **Competitor comparison**: Relative position (and feature-ownership) changes for tracked competitor domains — who gained, who lost, head-to-head per keyword, and competitive gap trends over time

## Tips & caveats

- **GSC has no AI Overview citation export.** The `--features` AI Overview signal is observational (did an AIO appear, is the brand cited). Reconcile true AI impressions via `/digital-marketing-pro:gsc-ai-performance` and scored AI visibility via `/digital-marketing-pro:geo-monitor`.
- **Position deltas are noisier than click/impression deltas** — a keyword bouncing between positions 8 and 12 produces big percentage swings that mean little. Trust impression/click moves more for diagnosis.
- **GSC data lags ~3 days.** When pulling "current" data, end the window 3 days ago.
- **Don't over-track.** 50-150 high-value keywords tracked well beats 2,000 tracked as noise.

## Agents Used

- **seo-specialist** — Keyword ranking and SERP-feature analysis, feature-ownership attribution, ranking-change diagnosis (algorithm update vs. technical issue vs. competitive displacement vs. content decay), baseline establishment and trend calculation, and recommended actions per severity level
- **performance-monitor-agent** — Alert generation with severity classification, monitoring-schedule management, threshold-breach detection with rolling-window comparison, trend tracking with 7-day and 30-day directional analysis, and notification formatting

## See also

- `/digital-marketing-pro:geo-monitor` — scored AI visibility across the 6 canonical AI surfaces (the AI-visibility scoring standard)
- `/digital-marketing-pro:gsc-ai-performance` — actual AI Overview / AI Mode impressions from GSC
- `/digital-marketing-pro:seo-drift` — compare two ranking snapshots and surface top movers
