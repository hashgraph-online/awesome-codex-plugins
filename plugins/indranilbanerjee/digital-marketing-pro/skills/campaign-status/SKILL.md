---
name: campaign-status
description: "Check active campaign status. Use when: cross-platform execution history, performance metrics, pending approvals."
---

# /digital-marketing-pro:campaign-status

## Purpose

Provide a unified view of all active campaigns across every connected platform — ads, email, social, blog — with their current status, live performance metrics, execution history, and any pending approvals or scheduled actions. Eliminates the need to check each platform individually and surfaces issues (paused campaigns, failed executions, stale content) before they become problems.

## Input Required

The user must provide (or will be prompted for):

- **Scope**: All active campaigns, a specific campaign by name or ID, or a specific platform
  (e.g., "Google Ads campaigns only", "email campaigns", "campaign named Q1-Launch")
- **Detail level**: Summary (one-line status per campaign) or detailed (full metrics, execution history,
  and next actions per campaign)
- **Time window** (optional): How far back to include execution history. Defaults to last 7 days
- **Status filter** (optional): Filter by campaign status — active, paused, scheduled, completed, failed.
  Defaults to active + paused + scheduled
- **Sort order** (optional): Sort campaigns by spend, performance, recency, or status.
  Defaults to platform grouping

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **List all tracked campaigns**: Execute `scripts/campaign-tracker.py --brand {slug} --action list-campaigns`
   to get the campaign registry with names, platforms, statuses, creation dates, and assigned KPI targets.
3. **Pull execution history**: Execute `scripts/execution-tracker.py --brand {slug} --action get-history --days {time_window}`
   to retrieve recent execution logs — what ran, when it ran, outcome (success/failure/skipped), error messages if any,
   and the user or automation that triggered it.
4. **Check pending approvals**: Execute `scripts/approval-manager.py --brand {slug} --action list-pending`
   to surface any campaigns, creatives, or content pieces awaiting review before they can go live.
   Include submission date and age in hours for each pending item.
5. **Pull live metrics from connected MCPs**: For each active campaign, query the relevant platform MCP
   (google-ads, meta-marketing, linkedin-marketing, tiktok-ads, mailchimp, etc.) for current performance:
   - Spend: total spend, daily spend, budget consumed
   - Performance: impressions, clicks, CTR, conversions, CPA, ROAS
   - Engagement: open rate, click-through rate, bounce rate, video views
   - Platform-specific: quality score, relevance score, deliverability rate
6. **Aggregate by platform and status**: Group campaigns by platform and status, calculate platform-level totals
   (total campaigns, total spend, total conversions, average CPA/ROAS), and flag any discrepancies between
   tracked campaigns and what the live platform reports.
7. **Calculate performance vs KPIs**: For each active campaign with defined targets, compute actual vs target
   for primary KPIs. Classify as:
   - **On track** (green): Meeting or exceeding targets
   - **At risk** (yellow): Within 15% of target with negative trend
   - **Behind** (red): Missing target by >15%
8. **Flag issues requiring attention**: Identify problems that need action:
   - Campaigns paused unexpectedly or by the platform (policy violation, billing issue)
   - Executions that failed with errors
   - Campaigns running past their planned end date
   - Stale campaigns with no activity in 7+ days
   - Campaigns exceeding budget pacing by >20%
   - Approval bottlenecks older than 48 hours
9. **Compile next scheduled actions**: List upcoming scheduled launches, budget changes, creative rotations,
   A/B test completions, or automated optimizations from the execution log with dates and dependencies.

## Output

A structured campaign status dashboard containing:

- **Campaign summary table**: Campaign name, platform, status (active/paused/scheduled/completed/failed),
  days running, total spend, key metric (conversions or leads), CPA or ROAS, and health indicator (green/yellow/red)
- **Active campaigns by platform**: Grouped view with platform-level totals — number of campaigns, total spend,
  total conversions, average CPA, average ROAS, and platform health status
- **Execution history** (last 7 days): Chronological log of actions taken — campaign launches, pauses, budget
  changes, creative swaps, bid adjustments, email sends — with timestamps, outcomes, and actor (manual or automated)
- **Pending approvals**: List of items awaiting review with requester name, submission date, type (creative,
  campaign launch, budget change, content), age in hours, and direct reference to the item
- **Performance vs KPIs**: For each active campaign, actual performance vs the KPI targets set at campaign
  creation — on track, at risk, or behind, with variance percentage and trend direction
- **Flagged issues**: Priority-ordered list of problems requiring attention with severity (critical/warning/info),
  description, affected campaign, and recommended resolution
- **Next scheduled actions**: Upcoming automated or planned actions with dates, descriptions, dependencies,
  and responsible party
- **Quick actions**: Suggested immediate next steps based on current status — approve pending items, investigate
  failures, pause underperformers, scale winners, extend successful campaigns

## Agents Used

- **execution-coordinator** — Execution history retrieval, approval queue management, scheduled action tracking, cross-platform status aggregation, and issue flagging
- **analytics-analyst** — Live performance metrics interpretation, KPI comparison, campaign health assessment, and performance-based recommendations
