---
name: budget-optimizer
description: "Optimize budget allocation. Use when: channel spend reallocation, data-driven budget planning, ROI-based justification."
argument-hint: "[total-budget]"
---

# /digital-marketing-pro:budget-optimizer

## Purpose

Data-driven marketing budget optimization across channels using performance data and industry benchmarks. Analyzes current spend efficiency, models diminishing returns per channel, and produces an optimized allocation with projected ROI improvement and a phased reallocation timeline.

## Input Required

The user must provide (or will be prompted for):

- **Current budget by channel**: How spend is distributed today (e.g., paid search, paid social, SEO, email, content, display, affiliate, events, etc.)
- **Performance data by channel**: Key metrics per channel — spend, revenue or conversions, CPA, ROAS, and conversion volume over the measurement period
- **Total budget available**: Overall marketing budget for the optimization period (monthly, quarterly, or annual)
- **Business goals**: Primary objective — maximize revenue, minimize CPA, hit a specific lead or revenue target, balance growth with efficiency
- **Constraints**: Minimum spend requirements, channel mandates from leadership, seasonal considerations, contractual commitments, or platform minimums
- **Measurement period**: Timeframe the performance data covers (last 30, 60, 90 days, or custom range)
- **Attribution model**: How conversions are currently attributed (last-click, first-click, linear, data-driven, or unknown)
- **Seasonality factors**: Upcoming seasonal peaks, promotional periods, or industry events that affect channel performance
- **Historical context**: Whether performance data reflects a typical period or was influenced by one-time events (product launch, viral moment, outage)

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Run budget-optimizer.py script**: Execute `scripts/budget-optimizer.py` with the provided channel data to compute baseline efficiency metrics and generate optimization scenarios
3. **Calculate efficiency metrics per channel**: Compute ROAS, CPA, cost per lead, revenue per dollar, contribution margin, and marginal cost of acquisition for each channel
4. **Rank channels by marginal efficiency**: Order channels by incremental return per additional dollar spent, accounting for current saturation levels and historical performance trends
5. **Apply diminishing returns model**: Model how each channel's efficiency degrades as spend increases — identify the inflection point and saturation ceiling for each channel
6. **Generate optimized allocation**: Redistribute budget to maximize the stated objective while respecting all constraints and minimum viable spend thresholds
7. **Compare current vs optimized**: Build a side-by-side comparison showing spend shifts, projected metric changes, and net improvement across all KPIs
8. **Project ROI improvement**: Estimate total revenue, conversion volume, ROAS, and CPA gains from the reallocation with confidence intervals
9. **Account for minimum viable spend thresholds**: Ensure no channel drops below the minimum spend needed to generate meaningful data, maintain auction competitiveness, or fulfill contractual obligations
10. **Include testing budget**: Reserve 10-15% of total budget for experimentation — new channels, creative testing, audience expansion, or emerging platforms
11. **Flag attribution caveats**: Note where attribution model limitations may skew efficiency calculations and recommend adjustments
12. **Create reallocation timeline**: Phase budget shifts over 4-8 weeks to avoid performance disruption — gradual ramp-up and ramp-down with weekly checkpoints and rollback triggers

## Output

A structured budget optimization plan containing:

- **Current vs optimized allocation table**: Side-by-side channel budgets with dollar amounts, percentage of total, and change from current
- **Projected ROI improvement**: Expected gains in revenue, conversions, ROAS, and CPA with confidence ranges
- **Channel efficiency ranking**: Channels ordered by marginal return with diminishing returns curves and saturation indicators
- **Reallocation recommendations**: Specific dollar shifts with clear rationale for each increase, decrease, or hold
- **Scenario comparison**: Best-case, expected, and conservative projections for the optimized allocation
- **Implementation timeline**: Phased reallocation schedule with weekly checkpoints, performance triggers, and rollback criteria
- **Risk assessment**: Potential downsides of each shift, minimum viable spend warnings, attribution blind spots, and mitigation strategies
- **Testing budget plan**: Recommended experiments with allocated budget, hypotheses, success criteria, and measurement approach
- **Attribution notes**: Caveats on how the current attribution model may over- or under-credit specific channels
- **Executive summary**: 1-page overview of key findings and recommended actions for stakeholder presentation

## Agents Used

- **analytics-analyst** — Performance data analysis, efficiency calculations, diminishing returns modeling, ROI projections, attribution assessment
- **media-buyer** — Channel-level budget strategy, spend threshold expertise, reallocation sequencing, platform-specific benchmarks, auction dynamics
