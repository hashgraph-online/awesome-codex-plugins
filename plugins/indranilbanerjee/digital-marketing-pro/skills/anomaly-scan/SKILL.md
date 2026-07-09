---
name: anomaly-scan
description: "Detect marketing anomalies. Use when: traffic drops, cost spikes, conversion changes, deliverability issues, budget overruns."
---

# /digital-marketing-pro:anomaly-scan

## Purpose

Scan all connected marketing platforms for anomalies — statistically significant deviations from established baselines that could indicate problems (traffic drops, CPA spikes, deliverability collapse, budget overruns) or opportunities (viral content, conversion rate improvements, unexpected channel growth). Designed to catch issues early, before they compound into costly problems, and to surface wins worth amplifying.

## Input Required

The user must provide (or will be prompted for):

- **Sensitivity level**: Strict (flags deviations >1.5 standard deviations from baseline), normal (>2 std dev),
  or relaxed (>3 std dev). Defaults to normal
- **Time period**: The window to scan for anomalies — today, last 3 days, last 7 days, last 30 days, or custom range.
  Defaults to last 7 days
- **Platforms** (optional): Specific platforms to focus the scan on (e.g., "Google Ads and Meta only").
  If omitted, all connected platforms are scanned
- **Metrics focus** (optional): Specific metrics to prioritize (e.g., "CPA and conversion rate only").
  If omitted, all available metrics are evaluated
- **Baseline period** (optional): Custom baseline for comparison instead of the default.
  Defaults to the rolling 30-day average maintained by performance-monitor.py
- **Exclude known events** (optional): List of known events to filter out (e.g., "Black Friday sale",
  "site migration on Jan 15") so expected deviations are not flagged as anomalies

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Pull current metrics from all connected MCPs**: Query each connected analytics platform
   (google-analytics, google-ads, meta-marketing, linkedin-marketing, tiktok-ads, mailchimp, stripe, mixpanel,
   amplitude, shopify, etc.) for all available metrics across the specified scan period. Include traffic, spend,
   conversions, CPA, ROAS, engagement rates, deliverability, and revenue metrics.
3. **Load historical baselines**: Execute `python "${CLAUDE_PLUGIN_ROOT}/scripts/performance-monitor.py" --brand {slug} --action get-baseline`
   to retrieve rolling averages, standard deviations, and expected ranges for each metric. If no baseline exists yet,
   use the comparison period data to establish a temporary baseline and note this in the output.
4. **Run anomaly detection**: Execute `python "${CLAUDE_PLUGIN_ROOT}/scripts/performance-monitor.py" --brand {slug} --action detect-anomalies --data '{...current-period metrics...}'`
   to flag metrics that fall outside the expected ranges computed from the stored baseline (mean ± standard deviations).
   Apply day-of-week and seasonality adjustments where historical data supports it.
5. **Cross-reference with recent executions**: Check execution history via
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/execution-tracker.py" --brand {slug} --action get-history --limit 14`
   to correlate anomalies with recent changes — did a campaign launch, pause, budget shift, creative swap,
   landing page change, or audience expansion precede the anomaly?
6. **Cross-reference with known factors**: Check for known platform outages, algorithm updates
   (Google core updates, Meta policy changes), industry events, seasonal patterns, and any user-provided
   known events that could explain the deviation.
7. **Classify anomalies by severity**: Critical (revenue-impacting, requires immediate action — tracking broken,
   CPA 3x+ baseline, budget overspend >20%, deliverability below 80%), Warning (significant deviations worth
   investigating within 24 hours — traffic down 30%+, engagement halved, CTR dropped 40%+), or Info (notable
   but non-urgent — gradual trend shifts, minor CPA increases, seasonal patterns emerging).
8. **Determine probable causes**: For each anomaly, analyze root causes using the diagnostic framework from
   `skills/analytics-insights/anomaly-diagnosis.md`. Categorize as data/tracking issue, external factor
   (algorithm update, competitor action, seasonal shift), internal change (campaign modification, landing page
   update), or platform change (policy update, feature deprecation, auction dynamics shift).
9. **Save critical anomalies as insights**: For critical and warning-level anomalies, persist via
   `python "${CLAUDE_PLUGIN_ROOT}/scripts/campaign-tracker.py" --brand {slug} --action save-insight --data '{"type":"anomaly","insight":"...","context":"..."}'`
   so they are tracked, surface in future reports, and can be referenced in post-mortems.

## Output

A structured anomaly report containing:

- **Scan summary**: Platforms scanned, time period analyzed, sensitivity level used, baseline period,
  total anomalies detected (by severity), and overall marketing health assessment (healthy, caution, or critical)
- **Critical anomalies** (if any): Metric name, platform, expected range (mean +/- threshold), actual value,
  deviation magnitude (in std devs and percentage), probable cause, estimated revenue impact, and recommended
  immediate action
- **Warning anomalies**: Same structure as critical, with recommended investigation steps and a 24-hour
  action plan for each
- **Info anomalies**: Notable deviations worth monitoring with watch criteria — what to look for to determine
  if the trend continues or reverses
- **Correlation analysis**: Connections between anomalies and recent execution history — which changes may have
  caused which deviations, with confidence levels (strong, possible, unlikely)
- **Platform health summary**: Per-platform health indicator (green/yellow/red) based on the number and severity
  of anomalies detected, plus a trend vs the last scan if previous scan data exists
- **Recommended actions**: Priority-ordered list of responses — immediate fixes for critical issues, investigations
  for warnings, monitoring adjustments for info items, and any baseline recalibrations needed
- **Baseline update notes**: Whether any baselines need recalibration due to structural changes (e.g., new campaign
  launched, channel added, seasonal shift, or pricing change that permanently alters expected ranges)

## Agents Used

- **performance-monitor-agent** — Anomaly detection engine, baseline management, statistical threshold evaluation, historical trend analysis, severity classification, and seasonality adjustment
- **analytics-analyst** — Root cause interpretation, cross-platform correlation, contextual analysis (seasonality, algorithm updates, competitive shifts), impact estimation, and actionable recommendation generation
