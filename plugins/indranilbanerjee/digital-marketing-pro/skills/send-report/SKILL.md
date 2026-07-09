---
name: send-report
description: "Deliver performance reports. Use when: sending KPI summaries via Slack, email, or Google Sheets with analysis."
disable-model-invocation: false
argument-hint: "[destination]"
---

# /digital-marketing-pro:send-report

## Purpose

Generate a formatted performance report from connected analytics sources and deliver it via Slack, email, or Google Sheets. Supports weekly pulse, monthly review, QBR, and custom report types. Pulls live metrics from connected platforms, calculates KPIs against targets and previous periods, adds trend analysis with anomaly detection, generates actionable recommendations, then formats and delivers through the user's preferred channel with appropriate approval gates.

## Execution gate (MANDATORY — cannot be skipped)

1. Present the full preview — recipients / spend / changes / compliance — as an **Execution Summary** before touching any live system.
2. The user must type `yes` (or an equivalent explicit approval). ANY other input — ambiguous, implied, partial, or absent approval — cancels the run.
3. Never proceed on ambiguous input. Never auto-retry a failed execution; a failure needs human review before any re-run.
4. Record the approval with `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action create-approval --data '{"risk_level":"<tier>","summary":"..."}'` **before** executing, then `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action mark-executed --id {approval_id}` after the platform confirms success.

## Input Required

The user must provide (or will be prompted for):

- **Report type**: The report format — weekly-pulse (top-line metrics and highlights, 1 page), monthly-review (full channel breakdown with trends, 3-5 pages), qbr (quarterly business review with strategic analysis and recommendations, 8-12 pages), or custom (user-defined metric selection and structure)
- **Delivery channel**: Where to send the report — Slack (channel post or DM with formatted blocks), email (HTML report via SendGrid or connected email MCP), or Google Sheets (new spreadsheet or append to existing tracking sheet)
- **Date range**: Reporting period — last 7 days, last 30 days, last quarter, custom start and end dates, or "since last report" to auto-detect the last delivery timestamp from execution logs
- **Recipients**: Optional — Slack channel name or user handles, email addresses for distribution list, or Google Sheets sharing permissions and notification settings for the target audience
- **Custom metrics**: Optional — specific metrics to include or exclude beyond the report type defaults, custom KPI definitions, calculated fields (e.g., blended CAC, marketing-influenced pipeline), or specific campaign IDs to isolate
- **Comparison period**: Optional — compare against previous period (WoW, MoM, QoQ, YoY), a specific custom date range, or targets and forecasts defined in brand profile
- **Report branding**: Optional — include brand logo, custom color scheme, header and footer text, or white-label formatting for client-facing or agency delivery
- **Narrative depth**: Optional — executive summary only (3-5 sentences), standard (summary plus channel commentary), or deep dive (full analysis with hypotheses and test recommendations)
- **Campaign filter**: Optional — isolate performance data for specific campaigns, channels, or audience segments rather than reporting on all activity
- **Benchmarks**: Optional — include industry benchmarks for context, competitive intelligence from previous analyses, or custom benchmarks defined by the brand
- **Annotations**: Optional — key events to overlay on the report (campaign launches, promotions, seasonal events, budget changes) that provide context for metric movements
- **Distribution schedule**: Optional — set this report to recur automatically at the specified cadence (weekly, monthly, quarterly) with the same configuration
- **Executive audience**: Optional — name the specific stakeholders who will read the report, so narrative tone and metric abstraction level can be adjusted accordingly

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Pull metrics from connected analytics**: Run `performance-monitor.py` to gather data from connected analytics MCP servers — Google Analytics (traffic, conversions), Google Ads (spend, CPC, ROAS), Meta Ads (spend, reach, frequency), LinkedIn Ads (spend, leads), email platforms (opens, clicks, deliverability), and any other configured sources. Aggregate metrics for the specified date range and comparison period.
3. **Calculate KPIs against targets**: Compare actual performance against targets defined in `profile.json` and against the comparison period. Calculate period-over-period deltas, percentage changes, trend direction, and statistical significance for key movements. Flag metrics that are more than 10% above or below target with severity indicators (warning, critical).
4. **Identify trends and anomalies**: Analyze metric trajectories across the reporting window — identify sustained upward or downward trends (3+ consecutive periods), sudden spikes or drops (single-period movements exceeding 2 standard deviations), seasonal patterns, and correlations between channels that suggest attribution shifts or budget reallocation opportunities.
5. **Overlay event annotations**: Map any user-provided annotations (campaign launches, promotions, budget changes, external events) to the timeline so metric movements can be contextualized against known events. Auto-detect annotations from execution logs if available.
6. **Generate recommendations**: Based on the performance data, produce 3-5 actionable recommendations ranked by expected impact — what to scale (high performers with headroom), what to pause (underperformers burning budget), what to test (hypotheses from anomalies), and what to investigate (unexplained movements). Tie each recommendation to specific data points with estimated impact range.
7. **Generate report content**: Run `report-generator.py` to compile the full report per the selected type — executive summary (what happened, why it matters, what to do next), KPI dashboard section with sparklines and status indicators, channel-by-channel breakdown with period-over-period comparisons, trend analysis with visualizations, anomaly flags with investigation prompts, and prioritized recommendations. Apply the appropriate template depth for the report type.
8. **Format for delivery channel**: Format the report content for the selected channel — Slack (structured message blocks with bold metrics, emoji indicators, and chart images as attachments), email (responsive HTML template with inline charts, summary table, and deep-link buttons to platform dashboards), or Google Sheets (structured tabs for summary, channel detail, and raw data, with conditional formatting, sparkline formulas, and chart objects). Apply brand formatting if specified.
9. **Create approval record**: Create the record via `approval-manager.py --action create-approval` with the risk level inside the `--data` JSON — `{"risk_level":"low",...}` for internal team recipients, `"medium"` for external stakeholders, client-facing delivery, or reports containing revenue/financial data. There is no `--risk-level` flag; see the Execution gate above for the exact command. Generate a report preview with delivery configuration.
10. **Present report preview**: Display the complete report content for user review — executive summary, key metrics with trend indicators, channel highlights, anomaly flags, and recommendations. Show delivery configuration — channel, recipients, formatting, and branding. Wait for explicit approval before sending.
11. **Deliver via MCP**: On approval, deliver the report through the connected MCP server — post to Slack channel with threaded detail, send HTML email via email platform with tracking, or create and share Google Sheets document with appropriate permissions. Handle attachments, chart images, and formatting per channel requirements.
12. **Verify delivery**: Confirm the report was successfully delivered — check Slack message posted status, email delivery confirmation, or Google Sheets sharing permissions applied. Retry on failure with error details.
13. **Archive report snapshot**: Save a copy of the report content and key metrics to the brand's insight history for historical comparison and trend tracking across reporting periods.
14. **Log delivery**: Run `execution-tracker.py` to log the report delivery with timestamp, report type, date range, delivery channel, recipient list, key metric values, and a hash of the report content for deduplication and cadence tracking.

## Output

A structured report delivery confirmation containing:

- **Report content**: The full generated report with executive summary, KPI dashboard, channel-by-channel breakdown, trend analysis, anomaly flags, and prioritized recommendations
- **Delivery confirmation**: Channel, recipients, timestamp, and delivery status (sent, posted, or shared) with direct link to the delivered report — Slack message URL, email tracking ID, or Google Sheets URL
- **Metrics summary**: Top-line KPIs in a compact table — metric name, actual value, target, delta versus target, period-over-period change, and trend direction indicator (up/down/flat)
- **Performance highlights**: Top 3 wins (strongest performers) and top 3 concerns (underperformers or anomalies) from the reporting period with supporting data points and context
- **Recommendations**: 3-5 prioritized action items with expected impact estimate (revenue, efficiency, or growth), effort level (quick win, medium, significant), and urgency rating (act now, this week, this month)
- **Trend analysis**: Key metric trajectories with direction, velocity of change, inflection points, and any detected anomalies with hypothesized causes and investigation prompts
- **Comparison data**: Period-over-period and target-vs-actual comparison tables for all reported metrics with percentage changes and statistical significance flags
- **Report metadata**: Report type, date range, data sources used with freshness timestamps, metrics excluded due to missing or incomplete data, and comparison baseline applied
- **Benchmark context**: Industry benchmark comparisons where available, showing how the brand's performance ranks relative to sector averages for key metrics
- **Data quality notes**: Any data gaps, delayed metrics, platform API issues, or estimated values used in calculations — transparency for stakeholders reviewing the report
- **Next report schedule**: Suggested date for the next report based on the current cadence (weekly, monthly, quarterly) with a reminder to set up automated delivery if desired
- **Event annotations**: Timeline overlay of campaign launches, promotions, budget changes, and external events that contextualize metric movements in the reporting period
- **Report archive reference**: Link to the archived report snapshot for historical comparison — allows tracking how the same metrics evolved across consecutive reporting periods
- **Distribution schedule status**: If recurring delivery was requested, confirmation of the automated schedule setup with next delivery date and cadence
- **Execution log entry**: Timestamped record of the report generation and delivery for audit trail, cadence tracking, and historical report archive reference

## Agents Used

- **analytics-analyst** — Metrics aggregation from connected platforms, KPI calculation against targets, trend analysis and anomaly detection, event annotation mapping, performance scoring, benchmark comparison, cross-channel correlation, and actionable recommendation generation with impact estimates
- **execution-coordinator** — Report formatting per delivery channel specifications, approval workflow with audience-based risk levels, MCP delivery execution, delivery verification, report archival for historical comparison, and execution logging with cadence tracking
