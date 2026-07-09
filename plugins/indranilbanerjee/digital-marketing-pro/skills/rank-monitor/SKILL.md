---
name: rank-monitor
description: "Monitor keyword rankings. Use when: tracking keyword positions, detecting ranking drops, or alerting on position changes."
---

# /digital-marketing-pro:rank-monitor

## Purpose

Set up and manage keyword ranking monitoring. Track target keyword positions across Google via Moz and Google Search Console MCPs, establish baselines, detect drops greater than 5 positions, and generate alerts when rankings change significantly. This command provides ongoing visibility into organic search performance — catching ranking declines early before they impact traffic, identifying upward trends to double down on, and tracking competitive position shifts that signal market changes.

## Input Required

The user must provide (or will be prompted for):

- **Target keywords**: A list of keywords to monitor — can be provided directly, imported from a CSV or Google Sheet, or pulled from the brand's existing keyword tracking list at `~/.claude-marketing/brands/{slug}/seo/keywords.json`. Keywords should include search intent classification (informational, navigational, transactional, commercial) if available
- **Monitoring frequency**: `daily` or `weekly` — daily is recommended for high-priority head terms and active campaign keywords, weekly for long-tail and lower-priority terms. Determines how often ranking checks run and how granular the trend data will be
- **Alert thresholds**: Position change that triggers an alert — default is >5 position drop. Can be customized per keyword group (e.g., >3 for brand terms, >5 for head terms, >10 for long-tail). Both drop and gain thresholds are supported
- **Competitor domains (optional)**: Domains to track alongside the brand for the same keywords — see how competitors rank for your target terms and detect when they gain or lose positions. Up to 10 competitor domains
- **Device type**: `mobile`, `desktop`, or `both` — rankings often differ significantly between devices, especially for local and mobile-intent queries
- **Target country**: The Google locale to check rankings in — e.g., US, UK, AU, CA, IN. Determines the search results market for position tracking

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Capture current rankings baseline**: Query Moz MCP and Google Search Console MCP for the current ranking position of each target keyword. Record position, ranking URL, SERP features present (featured snippet, People Also Ask, AI Overview, local pack, image pack, video carousel, sitelinks), click-through rate from GSC where available, and impressions. For competitor domains, capture their positions for the same keywords.
3. **Configure monitoring schedule**: Save the keyword list, monitoring frequency, alert thresholds, competitor domains, device type, and target country to the brand's SEO directory at `~/.claude-marketing/brands/{slug}/seo/rank-monitor-config.json`. Create or update the baseline snapshot at `~/.claude-marketing/brands/{slug}/seo/rank-baseline.json` with the current positions as the reference point.
4. **On each monitoring check: query and compare**: Pull current positions for all tracked keywords via Moz and GSC MCPs. Compare each keyword's current position to both the baseline (original position when monitoring started) and the previous check (last recorded position). Calculate absolute change from baseline, change since last check, rolling 7-day and 30-day trend direction, and average position across all tracked keywords.
5. **Detect significant changes**: Identify keywords that crossed alert thresholds — drops exceeding the configured position threshold, keywords that fell from page 1 (positions 1-10) to page 2 or beyond, keywords that gained >5 positions (potential quick-win opportunities), new SERP feature appearances or losses for the brand's ranking URLs, and competitor rank changes that moved them above or below the brand for tracked terms.
6. **Generate alert if thresholds are breached**: Categorize alerts by severity — `minor` for 3-5 position drops (monitor but no immediate action needed), `major` for 5-10 position drops (investigate content freshness, technical issues, or competitor activity), `critical` for >10 position drops or page 1 to page 2 transitions (immediate investigation required — check for algorithm updates, manual actions, technical errors, or content cannibalization). Include recommended next steps for each severity level.

## Output

A structured ranking report containing:

- **Ranking snapshot**: Current positions for all tracked keywords — position, ranking URL, device, country, date, and comparison to baseline and previous check with directional indicators (up, down, stable)
- **Change report**: Position changes since baseline and since last check — sorted by largest drops first, with trend sparklines showing 7-day and 30-day direction for each keyword
- **Alert summary**: Keywords needing attention — grouped by severity (critical, major, minor) with specific position changes, affected URLs, and recommended investigation steps
- **SERP feature tracker**: Which SERP features are present for each keyword and whether the brand owns them — featured snippets, People Also Ask inclusions, AI Overview citations, local pack presence, and changes since last check
- **Competitor comparison**: Relative position changes for tracked competitor domains — who gained, who lost, head-to-head position for each keyword, and competitive gap trends over time

## Agents Used

- **seo-specialist** — Keyword ranking analysis and interpretation, SERP feature tracking and ownership assessment, ranking change diagnosis (algorithm update vs. technical issue vs. competitive displacement vs. content decay), baseline establishment and trend calculation, and recommended actions for each severity level based on SEO best practices and historical patterns
- **performance-monitor-agent** — Alert generation with severity classification based on configurable thresholds, monitoring schedule management and check execution, threshold breach detection with rolling window comparison, trend tracking with 7-day and 30-day directional analysis, and notification formatting for ranking change alerts
