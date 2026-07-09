---
name: client-report
description: "Generate client-facing reports. Use when: white-labeled performance report with KPIs, trends, strategic recommendations."
---

# /digital-marketing-pro:client-report

## Purpose

Generate a professional, white-labeled client report for a specific brand. Uses agency voice (not brand voice), includes KPI performance, channel breakdowns, strategic recommendations, and next steps. Designed for external client delivery via Slack, email, Google Sheets, or markdown — with approval gating before any external send to prevent accidental disclosure or premature delivery of draft findings.

## Input Required

The user must provide (or will be prompted for):

- **Brand slug**: The brand this report covers — must match a configured brand in `~/.claude-marketing/brands/`
- **Report type**: One of:
  - Weekly pulse: Quick KPI snapshot with 3-5 key metrics and brief commentary
  - Monthly review: Full performance analysis with channel breakdowns and recommendations
  - QBR: Quarterly deep-dive with strategic roadmap and forward plan
- **Date range**: Specific start and end dates for the reporting period — defines what data is pulled and analyzed
- **Delivery channel**: Where the report should be sent — slack, email, google-sheets, or markdown-only (no external delivery, just generate the artifact)
- **Custom sections (optional)**: Any additional sections the client has requested — competitive update, creative performance breakdown, audience insights, attribution deep-dive, or ad-hoc investigation topic
- **Comparison period**: What to compare against — prior period, same period last year, plan/target, or all three simultaneously
- **Recipient list (optional)**: Specific client contacts who should receive the report if delivering via email or Slack — names and handles/addresses
- **Narrative emphasis (optional)**: What the client cares most about this period — growth, efficiency, brand awareness, pipeline generation, or revenue — influences which metrics are highlighted first and how insights are framed
- **Include appendix**: Whether to attach raw data tables and campaign-level detail as an appendix — defaults to yes for monthly and QBR, no for weekly pulse
- **White-label settings (optional)**: Agency logo placement, color scheme, and disclaimer text — pulled from agency profile if configured, otherwise uses clean defaults

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Pull all metrics for the brand**: Query connected MCP servers and run `python "${CLAUDE_PLUGIN_ROOT}/scripts/campaign-tracker.py" --brand {slug} --action list-campaigns` (then `--action get-campaign --id {id}` per campaign) to gather performance data across all active channels; filter to the specified date range during analysis
3. **Gather campaign history and execution log**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/execution-tracker.py" --brand {slug} --action get-history` to compile all deliverables completed, campaigns launched, optimizations made, and tests concluded, then filter to the reporting period during analysis
4. **Calculate KPIs vs targets and vs comparison period**: Compute actuals against the brand's stated KPI targets from `profile.json` and against the selected comparison period — calculate deltas, percentage changes, trend direction, and statistical significance where sample sizes allow
5. **Break down performance by channel**: Segment metrics by channel (paid search, paid social, organic search, email, display, video, affiliate, etc.) with per-channel KPIs, spend, efficiency metrics (CPC, CPA, ROAS, CTR), and contribution percentage to overall goals
6. **Identify top wins and attribution**: Select the 3-5 best-performing campaigns or initiatives from the period — document what was done, what drove the result, audience and creative insights, and how it connects to business outcomes
7. **Analyze underperformance with root causes**: For any KPI that missed target, identify root causes:
   - External factors: market shifts, seasonality, competitive moves, platform algorithm changes
   - Internal factors: budget constraints, creative fatigue, audience saturation, timing misalignment
   - Corrective actions: what was already done and what is recommended for next period
8. **Generate strategic recommendations**: Based on performance data, formulate 3-5 actionable recommendations — what to scale, what to pause, what to test next, where budget should shift, and what new opportunities to explore
9. **Write report in agency voice**: Draft the full report using professional, third-person agency voice — NOT the brand's personality. Focus on clarity, data-backed insights, actionable next steps, and a confident but honest tone that builds client trust
10. **Format for delivery channel**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/report-generator.py" --brand {slug} --action format-slack` (or `format-email` / `format-sheets`), passing the report JSON via `--data '{report_json}'`; for a clean markdown artifact use `--action generate-report --data '{report_json}'`
11. **Create approval checkpoint**: Present the full report preview for review. Risk level: low. Require explicit approval before any external delivery — highlight any sensitive data, unexpected results, or negative findings that may need pre-briefing with the client
12. **Deliver via MCP if approved**: On approval, send via the appropriate MCP integration (Slack MCP, email MCP, Google Sheets MCP) if a delivery channel was specified. Handle delivery errors gracefully with retry guidance
13. **Log delivery and archive**: Record the report delivery in the execution log with timestamp, recipients, delivery confirmation status, report version, and a reference to the archived report for future comparison

## Output

A structured client report containing:

- **Executive summary**: 3-5 sentence overview of the period — headline result, key wins, areas of focus, outlook for next period, and one recommended action for the client
- **KPI scorecard**: Actuals vs targets vs comparison period in a scannable table with color-coded status indicators (exceeded, on track, at risk, missed) and trend arrows showing directional momentum
- **Channel performance breakdown**: Per-channel metrics with spend, results, efficiency metrics (CPC, CPA, ROAS, CTR), contribution percentage to overall goals, and channel health assessment
- **Campaign highlights with attribution**: Top-performing campaigns with what drove success, creative and audience insights, measured impact, and replication recommendations for future campaigns
- **Underperformance analysis**: Honest assessment of any misses with root cause categorization (external vs internal), impact quantification, corrective actions taken, and preventive measures for next period
- **Strategic recommendations (3-5)**: Data-backed next steps with expected impact, investment required, implementation timeline, priority ranking, and connection to the client's stated business objectives
- **Budget efficiency analysis**: Spend vs return summary by channel, cost trend lines over the period, budget utilization rate, and efficiency comparison to prior periods with improvement/decline indicators
- **Upcoming deliverables and timeline**: What the agency will deliver next period with dates, milestones, dependencies, and any client actions required to keep the plan on track
- **Appendix (if requested)**: Raw data tables, campaign-level breakdowns, full metric exports, creative performance data, and supporting calculations for detailed review
- **Delivery confirmation**: Channel, timestamp, recipients, delivery status, and report version — or markdown artifact if no external delivery was requested

## Agents Used

- **agency-operations** — Report voice and tone (agency professional, not brand personality), client context awareness, approval workflow management, white-label formatting, and delivery coordination
- **analytics-analyst** — Metrics analysis, KPI calculations, channel breakdowns, trend analysis, comparison computations, attribution modeling, statistical significance checks, and recommendation data support
- **execution-coordinator** — Report formatting for delivery channels, MCP integration delivery, execution logging, delivery error handling, and archival
