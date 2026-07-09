---
name: budget-tracker
description: "Track budget pacing in real time. Use when: cross-platform spend tracking, overspend alerts, reallocation recommendations."
---

# /digital-marketing-pro:budget-tracker

## Purpose

Track advertising budget in real-time across all connected ad platforms. Analyze spend pacing against targets, project end-of-period totals, flag overspend risks and underspend inefficiencies, calculate daily burn rates, and recommend budget reallocations to maximize ROI within the remaining budget window. Designed for media buyers and marketing managers who need a single view of where money is going and whether it is being spent effectively.

## Input Required

The user must provide (or will be prompted for):

- **Budget period**: This month, this quarter, or a custom date range (e.g., "Feb 1 - Mar 31").
  Determines the pacing denominator and projection horizon
- **Ad platforms to include**: All connected platforms or specific ones (e.g., "Google Ads and Meta only").
  Defaults to all connected ad MCPs
- **Budget targets per platform** (optional): Specific spend targets per platform for the period.
  If omitted, targets are pulled from `profile.json` budget_range and any saved platform allocations
- **Total budget** (optional): Overall budget cap for the period.
  If omitted, pulled from `profile.json` budget_range
- **Alert thresholds** (optional): Custom thresholds for overpace (default: >110% of expected pacing) and
  underspend (default: <70% of expected pacing) flags
- **Include efficiency metrics** (optional): Whether to pull CPA, ROAS, and conversion data alongside spend.
  Defaults to yes

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Extract budget targets**: Pull `budget_range` from `profile.json` and any saved per-platform allocations from
   previous budget-optimizer or media-plan runs. If user provided explicit targets, use those as overrides.
   Calculate the target daily spend rate for each platform (budget / days in period).
3. **Pull spend data from connected ad MCPs**: Query each connected advertising platform
   (google-ads, meta-marketing, linkedin-marketing, tiktok-ads) for current-period spend — total spend to date,
   daily spend breakdown, campaign-level spend distribution, and cost metrics (CPC, CPM, CPA per campaign).
4. **Calculate pacing per platform**: Execute `python "${CLAUDE_PLUGIN_ROOT}/scripts/ad-budget-pacer.py" --budget {total} --period-days {N} --days-elapsed {N} --spend-to-date {amount}` with spend data
   and budget targets to compute days elapsed/remaining, budget consumed vs expected pacing percentage, pacing
   ratio (actual / expected), daily burn rate (7-day average), and burn rate trend (accelerating/steady/decelerating).
5. **Project end-of-period spend**: Extrapolate current daily burn rate to end of period for each platform —
   produce best-case (lowest recent daily spend), expected (7-day average), and worst-case (highest recent daily
   spend) projections.
6. **Compare to budget targets**: For each platform, calculate the gap between projected end-of-period spend and
   the budget target — express as both dollar amount and percentage variance.
7. **Flag pacing issues**: Generate alerts — overpace critical (>120%, immediate action: reduce bids, pause
   low-performers, set daily caps), overpace warning (110-120%, proactive adjustments this week), underspend
   warning (<70%, increase bids or expand targeting or reallocate), underspend info (70-85%, monitor).
8. **Pull efficiency metrics**: For each platform, retrieve CPA, ROAS, conversion volume, and cost per conversion
   so reallocation decisions are performance-informed, not just pacing-based.
9. **Recommend reallocations**: Execute `python "${CLAUDE_PLUGIN_ROOT}/scripts/budget-optimizer.py"` with current spend
   efficiency data to suggest specific dollar-amount shifts from underspending or low-efficiency platforms to
   high-performing ones with room to scale. Include rationale for each recommended move.
10. **Save budget snapshot**: Persist the current pacing snapshot via
    `python "${CLAUDE_PLUGIN_ROOT}/scripts/performance-monitor.py" --brand {slug} --action save-snapshot --data '{...pacing metrics...}'`
    for historical tracking, trend analysis, and comparison in future budget-tracker runs.

## Output

A structured budget dashboard containing:

- **Budget summary**: Total budget for the period, total spent to date, total remaining, overall pacing
  percentage, days elapsed, days remaining, projected end-of-period total, and overall health status
  (on track, overpacing, underpacing)
- **Per-platform spend table**: Platform name, budget target, actual spend to date, pacing percentage,
  daily burn rate (7-day avg), projected end-of-period spend, variance from target ($ and %),
  and status flag (green/yellow/red)
- **Pacing visualization data**: Daily spend trajectory vs ideal linear pacing for each platform —
  highlights where spend is accelerating, decelerating, or tracking evenly across the period
- **Overspend/underspend alerts**: Priority-ordered list of pacing issues with severity, platform,
  current pacing %, projected variance, and specific recommended corrective action
- **Reallocation recommendations**: Specific dollar-amount shifts between platforms with rationale — e.g.,
  "Move $2,000 from LinkedIn (62% pacing, $85 CPA) to Google Ads (98% pacing, $22 CPA, room to scale)"
- **Efficiency context**: Per-platform CPA, ROAS, conversion volume, and cost trend alongside spend data
  so budget decisions account for performance quality, not just pacing
- **Daily burn rate breakdown**: Current daily spend per platform vs target daily spend, with 7-day trend
  direction and acceleration/deceleration indicator
- **Projection scenarios**: Best-case, expected, and worst-case end-of-period spend projections per platform
  and in aggregate, with confidence ranges
- **Executive summary**: 2-3 sentence overview — total budget health, biggest risk or opportunity, and the
  single most important action to take now

## Agents Used

- **performance-monitor-agent** — Spend data aggregation from connected ad MCPs, pacing calculations, projection modeling, snapshot persistence, and historical spend trend analysis
- **media-buyer** — Budget optimization strategy, reallocation recommendations, platform-specific spend tactics (bid strategies, daily caps, audience expansion), and auction dynamics expertise
