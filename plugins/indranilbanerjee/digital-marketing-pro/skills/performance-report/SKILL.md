---
name: performance-report
description: "Generate performance reports. Use when: tracking KPIs, trend analysis, anomaly detection, and actionable recommendations."
argument-hint: "[time-period]"
---

# /digital-marketing-pro:performance-report

## Purpose

Generate a structured marketing performance report that transforms raw data into insights. Covers KPI tracking, trend analysis, anomaly detection, and prioritized recommendations for optimization.

## Input Required

The user must provide (or will be prompted for):

- **Reporting period**: Date range for the report
- **Channels to cover**: Which marketing channels to include (all, or specific ones)
- **Data source**: Raw data (paste, CSV, or connected platform)
- **KPIs of interest**: Specific metrics to focus on (or use defaults for the channel)
- **Comparison period**: Previous period, YoY, or custom benchmark
- **Audience**: Who will read the report (executive summary vs. tactical detail)

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. Ingest and validate the provided performance data
3. Calculate core KPIs per channel: traffic, conversions, revenue, ROAS, CPA, engagement, growth
4. Run trend analysis: period-over-period changes, trajectory, seasonality adjustments
5. Detect anomalies: significant spikes or drops with likely root causes
6. Benchmark against industry averages and brand targets
7. Generate insights: what worked, what underperformed, and why
8. Produce prioritized recommendations for the next period
9. Format report for the specified audience (executive vs. tactical)

## Output

A structured performance report containing:

- Executive summary with headline metrics and overall assessment
- Channel-by-channel KPI dashboard with period-over-period comparison
- Trend analysis with visualizable data points
- Anomaly alerts with root cause hypotheses
- Top wins and underperformers with context
- Actionable recommendations ranked by expected impact
- Next period goals and focus areas

## Agents Used

- **analytics-analyst** — Data analysis, KPI calculation, trend detection, anomaly identification, recommendations
