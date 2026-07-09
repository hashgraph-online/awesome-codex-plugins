---
name: qbr-plan
description: "Prepare a Quarterly Business Review. Use when: building QBR presentations, client performance reviews, or strategy updates."
---

# /digital-marketing-pro:qbr-plan

## Purpose

Prepare a comprehensive Quarterly Business Review presentation with performance retrospective, strategic insights, and forward-looking roadmap. Translates raw campaign data into a compelling narrative that demonstrates value, addresses challenges transparently, and builds confidence in the next quarter's strategy.

## Input Required

The user must provide (or will be prompted for):

- **Quarter being reviewed**: Specific quarter and year (e.g., Q4 2025) and the exact date range covered
- **Active campaigns and channels**: All campaigns that ran during the quarter with channels, objectives, and status (active, paused, completed)
- **Goals vs actual results**: Original quarterly targets and actual performance for each KPI — traffic, leads, conversions, revenue, ROAS, etc.
- **Budget vs actual spend**: Planned budget allocation by channel and actual spend with variance explanations
- **Key wins and challenges**: Notable successes worth highlighting and obstacles encountered with impact assessment
- **Next quarter objectives**: Business goals and marketing priorities already identified for the upcoming quarter
- **Client satisfaction signals**: NPS scores, feedback received, support tickets, or qualitative sentiment from the client team
- **Upsell/cross-sell opportunities**: Additional services, expanded scope, or new channels the client could benefit from
- **Competitive shifts**: Notable competitor moves, market changes, or industry trends observed during the quarter
- **Team changes**: Any staffing changes on agency or client side that affected the engagement

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Aggregate campaign performance data**: Organize all campaign metrics by channel and objective — impressions, clicks, conversions, spend, revenue, and derived metrics (CTR, CPC, CPA, ROAS, conversion rate)
3. **Compare results against goals and benchmarks**: Map actual performance to quarterly targets, prior quarter results, and industry benchmarks to show progress, regression, or breakthrough performance
4. **Identify top wins with attribution**: Select the 3 most impactful wins from the quarter and build attribution stories — what was done, why it worked, and how it connects to business outcomes
5. **Analyze underperformance with root causes**: For any KPI that missed target, conduct root cause analysis — external factors (market, seasonality, competition), internal factors (budget, creative, timing), and corrective actions taken or recommended
6. **Calculate ROI and budget efficiency**: Compute overall and per-channel ROI, cost-per-acquisition trends, budget utilization rate, and efficiency gains or losses compared to prior quarters
7. **Assess competitive landscape changes**: Summarize notable competitor activity — new campaigns, market entries, pricing changes, or positioning shifts that affected or could affect performance
8. **Develop strategic recommendations for next quarter**: Formulate 3-5 specific, actionable recommendations tied to data insights — what to scale, what to cut, what to test, and what to monitor
9. **Identify upsell opportunities**: Map gaps in current coverage or emerging opportunities to additional services with business case justification (projected impact and investment required)
10. **Build executive slide structure**: Design the presentation flow — executive summary first, then performance deep-dive, strategic insights, and forward plan — optimized for a 45-60 minute meeting
11. **Create appendix with detailed data**: Compile granular data tables, campaign-level breakdowns, and supporting metrics that back up the main narrative without cluttering the core slides
12. **Add next-steps action items with owners**: Define specific action items emerging from the QBR with responsible party (agency or client), deadline, and success criteria for each

## Output

A structured QBR presentation package containing:

- **Executive summary slide**: One-page overview with quarter highlights, overall score against goals, and key takeaway for leadership
- **Performance scorecard**: Goals vs actuals vs benchmarks in a scannable table format with color-coded status indicators (on track, at risk, missed)
- **Campaign-by-campaign analysis**: Individual campaign performance summaries with metrics, insights, and optimization actions taken
- **Budget efficiency analysis**: Spend vs return by channel with utilization rate, cost trend lines, and efficiency comparison to prior quarters
- **Top 3 wins with attribution story**: Detailed breakdown of biggest successes — what drove them, measured impact, and how to replicate
- **Underperformance analysis with corrective actions**: Honest assessment of misses with root cause, impact quantification, and specific corrective steps (taken and planned)
- **Competitive intelligence update**: Summary of notable competitor moves and market shifts with implications for strategy
- **Strategic recommendations (3-5)**: Data-backed recommendations for next quarter with expected impact, investment needed, and implementation timeline
- **Upsell/cross-sell opportunities with business case**: Additional service or scope recommendations with projected ROI and investment requirements
- **Next quarter roadmap with milestones**: Phase-based plan for the upcoming quarter with key deliverables, launch dates, and checkpoint reviews
- **Appendix with raw data tables**: Granular performance data, full campaign metrics, and supporting calculations for reference
- **Action items with owners and deadlines**: Specific next steps from the QBR with assigned owner (agency/client), due date, and success criteria
- **Account health score (1-10)**: Composite score based on performance, relationship health, growth trajectory, and risk factors with scoring rationale

## Agents Used

- **analytics-analyst** — Performance data aggregation, goal vs actual analysis, ROI calculations, benchmarking, budget efficiency analysis, scorecard design, and appendix data compilation
- **marketing-strategist** — Strategic recommendations, competitive assessment, upsell opportunity identification, executive narrative, roadmap development, and account health scoring
