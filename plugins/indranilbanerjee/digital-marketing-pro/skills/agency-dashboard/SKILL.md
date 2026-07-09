---
name: agency-dashboard
description: "Portfolio-level agency dashboard aggregating health metrics across all client brands — campaign status, budget pacing, KPI attainment, team utilization. Use when reviewing cross-brand portfolio health, preparing for agency leadership standups, or getting a single-view snapshot of all client accounts."
user-invocable: true
triggers:
  - agency portfolio dashboard
  - cross-brand campaign status
  - budget pacing all clients
  - agency KPI overview
  - portfolio health check
  - multi-client dashboard
  - agency team utilization
  - overview of all client accounts
---

# /digital-marketing-pro:agency-dashboard

## Purpose

Generate a portfolio-level dashboard aggregating health metrics across ALL client brands. Shows campaign activity, budget pacing, KPI attainment, content pipeline, and team utilization at a glance — giving agency leadership a single view of operational health without opening each account individually. Designed for daily standups, weekly agency reviews, or on-demand health checks.

## Input Required

The user must provide (or will be prompted for):

- **Dashboard scope**: All brands or a specific list of brand slugs to include in the portfolio view
- **Time period**: Current week, month, or quarter — determines the pacing calculations and comparison windows
- **Detail level**: Summary (top-line health scores per client) or detailed (campaign-level breakdowns per client with individual campaign metrics)
- **Sort/filter preferences**: Sort clients by health score, spend, revenue, or alphabetical — and optionally filter to only at-risk (amber/red) accounts
- **Team filter (optional)**: Filter by account lead or team pod if the agency has multiple pods managing different client sets
- **Comparison baseline (optional)**: Compare current period against prior period, same period last year, or plan/target — defaults to prior period
- **Alert threshold overrides (optional)**: Custom thresholds for performance drop alerts or budget pacing tolerance — defaults to 20% performance drop and 10% pacing variance
- **Export format (optional)**: Whether to output as markdown, Google Sheets, or Slack message — defaults to markdown

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Enumerate all brands**: Scan `~/.claude-marketing/brands/` for all configured brand directories (excluding `_active-brand.json`). For each brand, load `profile.json` to get client name, industry, engagement type, contract dates, assigned team members, and KPI targets
3. **Pull campaign data per brand**: For each brand in scope, run `campaign-tracker.py --brand {slug} --action list` to retrieve active campaigns, statuses, budgets, objectives, and recent performance snapshots
4. **Pull execution status per brand**: For each brand, run `execution-tracker.py --brand {slug} --action list` to get pending deliverables, in-progress tasks, completed items this period, and overdue items with age in days
5. **Check budget pacing per brand**: For each brand, compare actual spend-to-date against planned spend for the current period — calculate pacing percentage and project end-of-period spend at current run rate
6. **Calculate per-client health score**: Apply the RAG scoring formula from `skills/context-engine/agency-operations-guide.md`:
   - Green: On track across KPIs, budget on pace (within 10%), no overdue items, content pipeline flowing
   - Amber: 1-2 KPIs at risk, minor pacing drift (10-20%), items approaching deadline, or pending approvals aging
   - Red: Significant KPI misses, budget overspend (>20%), missed deadlines, stalled campaigns, or MCP disconnections
7. **Aggregate portfolio KPIs**: Sum total active campaigns, total monthly spend, average ROAS across clients, total leads/conversions, total pending deliverables, and overall portfolio health distribution (count and percentage of green/amber/red)
8. **Check team utilization**: Run `team-manager.py --action check-capacity` to assess current team workload — available capacity per team member, overloaded staff flagged, accounts at risk of under-service, and billable hours tracking. **Also pull Claude Code consumption** via `/usage --since 7d` (Claude Code v2.1.149+, May 2026) — this exposes per-model token consumption (Opus 4.7, Sonnet 4.6, Haiku 4.5) for the working directory and projects billed cost in USD. Brand-per-directory workspaces (`~/work/clients/{slug}`) make this brand-attributable automatically; aggregate the figures into a "Claude Code consumption" line in the dashboard so leadership can see runaway AI cost before the monthly invoice.
9. **Identify pending approvals**: Scan execution logs across all brands for items awaiting client or internal approval — flag anything older than 48 hours as overdue, group by brand and urgency tier (routine, time-sensitive, blocking)
10. **Surface upcoming deadlines**: Compile deadlines from all brands for the next 7 and 14 days — campaign launches, content due dates, reporting deadlines, contract milestones, renewal dates, and QBR schedules
11. **Detect alerts and anomalies**: Flag any brand with sudden performance drops (>20% week-over-week on primary KPI), budget pacing issues (>10% ahead or behind plan), stalled campaigns (no activity in 5+ days), MCP connection failures, or expiring credentials
12. **Check content pipeline**: Aggregate content status across all brands — items in draft, in review, approved, scheduled, and published — identify bottlenecks where content is stalling at a particular stage
13. **Generate trend comparison**: Compare current portfolio health against the selected baseline period — show improving, stable, or declining trajectory for each client and the portfolio overall with directional arrows
14. **Compile portfolio dashboard**: Assemble all data into a structured dashboard sorted by the user's preference, with drill-down detail available for any individual client

## Output

A structured portfolio dashboard containing:

- **Portfolio health summary**: Total clients in scope, health distribution (green/amber/red count and percentage), overall portfolio health score (weighted by client spend), and period-over-period trend direction
- **Per-client health cards**: For each brand — client name, health score (RAG), active campaigns count, monthly spend with pacing status, primary KPI vs target with delta, next deadline, top alert if any, and assigned account lead
- **Aggregate KPI table**: Total spend across portfolio, average ROAS, total active campaigns, total leads/conversions generated, cost efficiency trends, and period-over-period comparison with directional arrows
- **Budget pacing summary**: Per-brand pacing status (on pace, underspending, overspending) with projected end-of-period spend, variance from plan in dollars and percentage, and portfolio-level pacing aggregate
- **Team utilization matrix**: Per-team-member workload (accounts managed, hours allocated, capacity percentage, billable ratio), overloaded alerts, available bandwidth for new work, and staffing recommendations
- **Claude Code consumption (per brand)**: Aggregated `/usage` output per working directory mapped to brand — Opus 4.7 / Sonnet 4.6 / Haiku 4.5 token totals and USD cost for the reporting window. Flag any brand whose Claude Code spend is >2× the portfolio median for the same retainer tier as a candidate for engagement-pattern review or rate renegotiation
- **Pending approvals queue**: All items awaiting approval across brands with item description, age in hours, responsible owner, brand, urgency level, and estimated impact of delay
- **Upcoming deadlines (7/14 day)**: Chronological list of upcoming deadlines with brand, deliverable type, responsible owner, days remaining, dependency status, and risk assessment if missed
- **Content pipeline status**: Aggregate view of content in draft, review, approved, and scheduled stages across all brands with stage-by-stage counts and bottleneck identification
- **Alerts and anomalies panel**: Performance drops, pacing issues, stalled campaigns, MCP connection failures, expiring credentials, or overdue items requiring immediate attention — sorted by severity
- **Contract and renewal tracker**: Upcoming contract renewals, engagement milestones, and retention risk indicators for clients approaching renewal windows
- **Drill-down guidance**: Instructions for investigating any individual client in detail using `/digital-marketing-pro:performance-report`, `/digital-marketing-pro:client-report`, or `/digital-marketing-pro:credential-switch` to activate that brand's context

## Agents Used

- **agency-operations** — Portfolio aggregation, per-client health scoring, team utilization analysis, approval tracking, deadline compilation, budget pacing calculations, content pipeline aggregation, and alert detection
- **analytics-analyst** — Metrics analysis, KPI aggregation, trend calculations, anomaly detection, performance benchmarking across the portfolio, and comparison baseline computations
