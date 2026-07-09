---
name: pdf-report
description: "Generate branded PDF reports. Use when: creating executive summaries, campaign reports, or client deliverables."
---

# /digital-marketing-pro:pdf-report

## Purpose

Generate professionally branded marketing reports as structured, downloadable documents. Supports executive summaries, campaign performance reports, channel reports, competitor reports, and monthly/quarterly reviews. Reports include brand theming (colors, logos, fonts) and are structured for the intended audience (C-suite, marketing team, or client). Designed to eliminate manual report assembly by pulling live data from connected sources, applying brand-consistent formatting, and producing audience-appropriate deliverables that are ready to share without further editing.

## Input Required

The user must provide (or will be prompted for):

- **Report type**: `executive-summary` (1-page strategic overview with 3-5 headline KPIs), `campaign-report` (full campaign performance with channel breakdowns and A/B results), `channel-report` (deep-dive into a single channel — paid, organic, email, social), `competitor-report` (competitive landscape with share-of-voice and positioning), or `monthly-review` / `quarterly-review` (period-over-period performance with trend analysis and forward plan)
- **Data sources and metrics to include**: Which campaigns, channels, or metric categories to pull into the report — e.g., "all paid media campaigns from Q4", "email + social metrics", "top 5 competitors". Specific KPIs can be requested (ROAS, CAC, LTV, conversion rate, pipeline) or left to auto-select based on report type and business model
- **Time period**: The reporting window — specific dates, relative periods (last 30 days, Q4 2024, YTD), or comparison periods (this month vs. last month, Q4 vs. Q3). For reviews, the primary period and comparison period are both required
- **Intended audience**: `c-suite` (executive summary focus — strategic insights, trend arrows, recommendations), `team` (full operational detail — granular metrics, test results, action items), or `client` (branded presentation format — objectives recap, performance against goals, competitive context, next steps)
- **Brand theme preferences (optional)**: Override stored brand theme — custom color palette, logo placement, font selection, header/footer content. If omitted, uses the brand profile's stored report theme from `pdf-generator.py brand-theme`

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, industry context, and report theme (colors, logo URL, fonts from brand profile or `pdf-generator.py brand-theme`). Check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load visual and tone restrictions. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Gather report data from relevant sources**: Pull data based on report type — `campaign-tracker.py` for campaign performance data and status, `performance-monitor.py` for performance metrics and threshold comparisons, `competitor-tracker.py` for competitive intelligence data, analytics MCPs (Google Analytics, Google Ads, Meta) for live channel metrics. Cross-reference data freshness timestamps and flag any stale sources (older than the reporting period).
3. **Structure report by audience**: Apply audience-specific report architecture. For C-suite: 1-page executive summary with 3-5 headline KPIs displayed as metric cards with trend arrows, a strategic narrative paragraph, and 2-3 prioritized recommendations. For Team: full metrics tables with channel-by-channel breakdowns, A/B test results with statistical significance indicators, pacing against targets, and numbered action items with owners. For Client: branded cover page with report title and period, executive summary section, performance by stated objective with goal vs. actual, competitive context section, and next period plan with proposed initiatives and expected impact.
4. **Generate report content with visualizations**: Write narrative analysis sections connecting data to business outcomes. Describe data visualizations with specifications (chart type, data series, axis labels, colors from brand theme) — bar charts for channel comparisons, line charts for trends over time, pie charts for budget allocation, funnel charts for conversion paths. Format data tables with conditional highlighting (green for above target, red for below). Include methodology notes for any calculated metrics.
5. **Save structured report**: Execute `pdf-generator.py generate-report` with the complete report payload — content sections, visualization specs, data tables, brand theme configuration, metadata (report type, period, audience, generation timestamp). The script produces the formatted document with brand theming applied.
6. **Present report preview for review**: Display a structured preview of the report — table of contents, section summaries, key metrics highlighted, and visualization descriptions — for user review before finalizing. Allow the user to request adjustments to sections, add or remove metrics, change emphasis, or modify the narrative tone before the final version is saved.

## Output

A structured report delivery containing:

- **Structured report document**: The branded report with all sections, data visualizations, and narrative analysis — formatted according to audience type and brand theme with consistent typography, color usage, and layout
- **Report ID**: Unique identifier for retrieval, versioning, and reference in future reports or notifications
- **Sections summary**: Table of contents with section titles and page references — executive summary, performance metrics, channel breakdowns, competitive analysis, recommendations, next steps (sections vary by report type)
- **Data freshness indicator**: Per-source timestamp showing when each data source was last updated — flags any sources older than the reporting period or with known data gaps
- **Report metadata**: Generation date, reporting period, report type, intended audience, brand theme applied, data sources used, and version number

## Agents Used

- **analytics-analyst** — Data gathering from campaign trackers, performance monitors, and analytics MCPs, metric analysis with period-over-period comparisons and target pacing, data visualization planning with chart type selection and data series mapping, and narrative insight generation connecting metrics to business outcomes and strategic recommendations
- **execution-coordinator** — Report generation orchestration, brand theme application from stored profile or user overrides, PDF creation via `pdf-generator.py` with section assembly, visualization rendering specifications, and branded formatting, plus report storage and retrieval ID assignment
