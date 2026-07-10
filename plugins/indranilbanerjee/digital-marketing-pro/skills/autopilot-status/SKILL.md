---
name: autopilot-status
description: "Check campaign autopilot status. Use when: health scores, auto-corrections, guardrail review, campaigns needing attention."
---

# /digital-marketing-pro:autopilot-status

## Purpose

Campaign operations autopilot dashboard. Show health scores for all active campaigns, list any auto-corrections taken recently, display current guardrail configuration, flag campaigns needing human attention, and report savings from automated interventions. Provides a single-view operational picture of how the autopilot system is managing campaign health — so the user can trust what's running smoothly, focus attention on what needs it, and quantify the value of automated monitoring.

## Input Required

The user must provide (or will be prompted for):

- **Time period**: The lookback window for correction history and savings calculation — defaults to "last 24 hours". Accepts "last 1 hour", "last 12 hours", "last 24 hours", "last 7 days", "last 30 days", or a custom date range. Shorter periods for real-time operational checks, longer periods for performance reviews and reporting
- **Campaign filter (optional)**: Narrow the dashboard to specific campaigns by name, ID, channel, or status — e.g., "Q1 brand awareness campaigns only", "all Google Ads campaigns", or "campaign-id-12345". If omitted, shows all active campaigns across all channels
- **Detail level (optional)**: `summary` (default — health scores, correction count, top-line savings) or `detailed` (full correction logs with before/after metrics, guardrail rule explanations, per-campaign savings breakdown). Use summary for daily check-ins, detailed for weekly reviews or troubleshooting

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand-specific campaign naming conventions, KPI targets, and budget constraints to contextualize health scores and savings calculations. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Gather campaign health scores**: Execute `python "${CLAUDE_PLUGIN_ROOT}/scripts/campaign-health-monitor.py" --brand {slug} --action health-score --campaign-id {id} --metrics '{...campaign metrics...}'` for each active campaign (or filtered subset). Each campaign receives a composite health score (0-100) based on performance vs. KPI targets, budget pacing accuracy, audience delivery, creative fatigue indicators, and anomaly detection. Campaigns are classified as healthy (80-100), attention-needed (50-79), or critical (below 50).
3. **Retrieve recent auto-corrections**: Query `python "${CLAUDE_PLUGIN_ROOT}/scripts/campaign-health-monitor.py" --brand {slug} --action corrections-history --since {YYYY-MM-DD}` for the specified time period. Each correction record includes the campaign affected, what was detected (the trigger condition), what action was taken (bid adjustment, budget reallocation, audience modification, creative rotation, pause), the before and after metric values, and the timestamp of the intervention.
4. **Load current guardrails configuration**: Read the active guardrail rules — maximum budget deviation percentage, minimum ROAS threshold before pause, click-through rate floor, cost-per-acquisition ceiling, frequency cap limits, creative fatigue rotation triggers, and any custom brand-specific rules. Display which guardrails are active, their threshold values, and what automated action each triggers when breached.
5. **Identify campaigns needing human attention**: Flag campaigns where the health score is below the attention threshold, where issues exceed what guardrails can auto-correct (e.g., strategic pivot needed, creative refresh required, audience saturation detected, or budget reallocation beyond autopilot authority), or where the autopilot took a correction but metrics haven't recovered within the expected timeframe. Rank flagged campaigns by urgency.
6. **Calculate savings from auto-corrections**: Execute `python "${CLAUDE_PLUGIN_ROOT}/scripts/campaign-health-monitor.py" --brand {slug} --action savings-report --since {YYYY-MM-DD}` for the specified time period. Estimate waste prevented by each auto-correction — budget saved from pausing underperforming segments, revenue protected by catching anomalies early, efficiency gained from automated bid adjustments. Aggregate into total estimated savings with per-correction breakdown.

## Output

- **Campaign health dashboard**: All active campaigns (or filtered set) listed with their health score (0-100), risk classification (healthy, attention-needed, critical), key contributing factors to the score, and trend indicator (improving, stable, declining) compared to the previous period
- **Auto-corrections taken**: Chronological list of automated interventions within the time period — campaign name, trigger condition, action taken, before/after metrics, and estimated impact. Grouped by correction type (bid, budget, audience, creative, pause) with counts per category
- **Campaigns needing attention**: Prioritized list of campaigns requiring human review — each with the specific issue, why it exceeds autopilot authority, recommended action, and urgency level. These are the items that need the user's decision
- **Guardrails status**: Current guardrail configuration displayed as a rule table — rule name, threshold value, automated action on breach, status (active or paused), and number of times triggered in the time period
- **Savings report**: Total estimated waste prevented by automated interventions — broken down by correction type, with per-campaign attribution where applicable. Includes budget saved, revenue protected, and efficiency improvements expressed in both absolute numbers and percentages
- **Overall operations health score**: A single composite score (0-100) representing the autopilot system's effectiveness — factoring in campaign health distribution, correction success rate, unresolved issues, and guardrail coverage. Trend compared to previous period

## Agents Used

- **performance-monitor-agent** — Campaign health scoring with composite metrics across KPI performance, budget pacing, audience delivery, and creative fatigue, anomaly detection and issue classification by severity, auto-correction history retrieval with before/after impact analysis, savings calculation estimating waste prevented per intervention, and trend analysis comparing current health to previous periods
- **execution-coordinator** — Guardrail configuration management with rule status and threshold display, correction execution tracking with authority-level classification (what autopilot can handle vs. what needs human decision), campaign flagging for human attention with urgency ranking and recommended actions, and operational health scoring across the full autopilot system
