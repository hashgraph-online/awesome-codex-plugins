---
name: performance-check
description: "Pull live marketing metrics for a performance snapshot: KPIs vs targets, trend comparison, and cross-platform overview. Use when checking current marketing performance, monitoring KPI health, comparing to benchmarks, or getting a quick status update across analytics platforms."
user-invocable: true
triggers:
  - check marketing performance
  - pull current KPIs
  - performance snapshot
  - how are our marketing metrics
  - compare performance to targets
  - marketing performance check
  - quick KPI health check
  - check campaign performance
---

# /digital-marketing-pro:performance-check

## Purpose

Pull live metrics from all connected analytics MCPs and produce a comprehensive performance snapshot. Compares current performance to KPI targets defined in the brand profile, previous-period benchmarks, and industry averages. Designed for quick health checks — run it daily, weekly, or on-demand to stay on top of marketing performance without switching between platforms.

**Scope (vs `/digital-marketing-pro:performance-report`):** this skill is the **live-pull + snapshot-persistence** layer — it fetches current metrics from the platforms and saves a snapshot for trend history. When you need a formatted, narrative deliverable for stakeholders (executive summary, channel commentary, prioritized recommendations, branded formatting), run `/digital-marketing-pro:performance-report`, which consumes the snapshots this skill persists rather than re-pulling. Use `performance-check` to *see the numbers now*; use `performance-report` to *tell the story*.

## Input Required

The user must provide (or will be prompted for):

- **Time period**: Today, this week, this month, this quarter, or a custom date range (e.g., "last 14 days", "Jan 1 - Jan 31")
- **Channel focus** (optional): Specific channels or platforms to prioritize (e.g., "paid search only", "email and social").
  If omitted, all connected platforms are included
- **Comparison period** (optional): Period to compare against — previous period, same period last year, or custom range.
  Defaults to the equivalent previous period
- **KPI targets** (optional): Override targets for this check.
  If omitted, targets are pulled from profile.json goals and KPI settings
- **Granularity** (optional): Daily, weekly, or aggregate view. Defaults to aggregate for the selected period

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Detect connected analytics MCPs**: Check `.mcp.json` and active MCP connections to identify which platforms are available
   (google-analytics, google-ads, meta-marketing, linkedin-marketing, tiktok-ads, mailchimp, stripe, mixpanel, amplitude, shopify, etc.).
   Log any expected platforms that are not connected so the user knows about gaps in coverage.
3. **Pull metrics from each connected platform**: Request key metrics for the specified time period:
   - Traffic: sessions, users, pageviews, new vs returning (break out GA4's **"AI Assistant"** default channel — referrals from ChatGPT, Gemini, Copilot, Perplexity, etc. — so AI-sourced traffic isn't buried under Referral/Direct)
   - Ads: impressions, clicks, spend, CPC, CPM
   - Conversions: leads, purchases, sign-ups, goal completions
   - Revenue: total revenue, average order value, transaction count
   - Engagement: open rate, click rate, bounce rate, time on site
   - Platform-specific: email deliverability, social reach, video views, app installs
4. **Aggregate into unified dashboard**: Normalize metrics across platforms into a single cross-channel view with consistent
   naming, currency conversion if multi-currency, and de-duplicated conversion counts where platforms overlap
5. **Calculate KPIs vs targets**: Compare actuals to targets from `profile.json` goals — flag green (on track or exceeding),
   yellow (within 10% of target), or red (missing by >10%). Include absolute and percentage variance for each KPI.
6. **Compare to previous period**: Calculate period-over-period change for every metric and attach trend direction
   (up/down/flat) with percentage change. If year-over-year data is available, include as a secondary reference point.
7. **Benchmark against industry**: Reference `skills/context-engine/industry-profiles.md` for the brand's industry to
   contextualize performance relative to category averages. Flag metrics significantly above or below industry norms.
8. **Identify notable findings**: Surface the top 3 wins (best-performing metrics or biggest improvements), top 3 concerns
   (underperforming or declining metrics), and any material changes that warrant deeper investigation. Before labelling a
   conversion-rate change "statistically significant," confirm it with `python "${CLAUDE_PLUGIN_ROOT}/scripts/significance-tester.py" --control-visitors {n} --control-conversions {n} --variant-visitors {n} --variant-conversions {n} --confidence 0.95` — do not call a movement significant off a raw percentage delta.
9. **Generate recommended actions**: Based on the data, produce 3-5 specific, actionable next steps — e.g., "Pause
   underperforming ad set X", "Increase budget on high-ROAS channel Y", "Investigate traffic drop on Z",
   "Scale winning creative variant", "Run /digital-marketing-pro:anomaly-scan for deeper diagnosis".
10. **Save performance snapshot**: Execute `python "${CLAUDE_PLUGIN_ROOT}/scripts/performance-monitor.py" --brand {slug} --action save-snapshot --data '{...current metrics...}'`
    to persist the snapshot for historical comparison and trend tracking across future runs.
11. **Log significant insights**: For any metric with a notable deviation, save via
    `python "${CLAUDE_PLUGIN_ROOT}/scripts/campaign-tracker.py" --brand {slug} --action save-insight --data '{"type":"anomaly","insight":"...","context":"..."}'`
    so findings surface in future reports and campaign planning.

## Output

A structured performance snapshot containing:

- **Executive summary**: 2-3 sentence overview of overall marketing health with the single most important finding highlighted
- **Channel-by-channel metrics table**: Traffic, impressions, clicks, conversions, revenue, spend, CPA, ROAS, and engagement
  rate per platform — sortable by any column
- **KPI scoreboard**: Each tracked KPI with actual value, target value, percentage to target, variance (absolute and %),
  trend arrow (vs previous period), and RAG status (red/amber/green)
- **Cross-channel summary**: Total spend, total conversions, blended CPA, blended ROAS, total revenue, marketing efficiency
  ratio, and overall health assessment
- **Period-over-period comparison**: Percentage change for all key metrics vs the comparison period with directional
  indicators and sparkline-style trend data
- **Industry benchmark context**: How key metrics compare to industry averages from industry-profiles.md, with percentile
  ranking where data is available
- **Notable findings**: Top 3 wins, top 3 concerns, and any anomalies worth investigating further — each with supporting
  data points and severity indicator
- **Recommended actions**: 3-5 specific next steps with priority ranking, expected impact, and the platform or campaign
  each action applies to
- **Data gaps**: Any platforms that were expected but not connected, metrics that could not be retrieved, or time periods
  with incomplete data — so the user knows what is missing from the picture

## Agents Used

- **analytics-analyst** — Metrics interpretation, KPI analysis, cross-channel normalization, trend identification, industry benchmarking, insight generation, and action recommendation
- **performance-monitor-agent** — Data aggregation from connected MCPs, baseline comparison, snapshot persistence, historical trend analysis, and gap detection
