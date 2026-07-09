---
name: executive-dashboard
description: "Design executive marketing dashboards. Use when: building CMO reports, board metrics, or leadership views."
---

# /digital-marketing-pro:executive-dashboard

## Purpose

Design a C-suite marketing dashboard that translates marketing metrics into business outcomes for executive decision-making. Bridges the gap between marketing activity data and business impact, giving senior leaders the clarity to make faster, better-informed strategic decisions without drowning in operational detail.

## Input Required

The user must provide (or will be prompted for):

- **Executive role**: Primary audience — CEO, CMO, CFO, VP Marketing, or board — each requires different metric emphasis and abstraction level
- **Business model and revenue drivers**: How the company makes money — SaaS, e-commerce, lead gen, marketplace, subscription — and the key revenue levers marketing influences
- **Strategic priorities this quarter**: The 2-4 business priorities the executive team is focused on that marketing should ladder up to
- **Reporting frequency**: How often the dashboard will be reviewed — weekly executive standup, monthly leadership meeting, quarterly board review
- **Current data sources and tools**: Analytics platforms, CRM, ad platforms, attribution tools, and BI systems currently in use with data freshness and reliability notes
- **Existing reports being replaced**: Current reporting artifacts the dashboard will consolidate or replace — helps identify gaps and redundancies
- **Key decisions the dashboard should inform**: Specific decisions executives make that this dashboard should support — budget allocation, channel mix, hiring, campaign scaling, market expansion
- **Stakeholder data literacy level**: How comfortable the audience is with marketing metrics — determines labeling, context, and narrative density needed

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Identify north-star metrics**: Select 5-7 metrics that directly tie marketing activity to business outcomes — revenue influenced, pipeline generated, customer acquisition cost, lifetime value, market share, brand equity indicators
3. **Design metric hierarchy**: Organize metrics into three tiers — leading indicators (predict future performance), lagging indicators (confirm past results), and health metrics (signal system stability and sustainability)
4. **Select visualization type per metric**: Choose the optimal chart type for each metric based on data shape and decision context — trend lines for trajectory, gauges for targets, bar charts for comparisons, sparklines for density
5. **Define alert thresholds and anomaly triggers**: Set green/yellow/red thresholds for each metric with specific trigger values, and configure anomaly detection rules for unexpected spikes or drops
6. **Map data sources to each metric**: Document which system provides each metric, how it is calculated, data freshness (real-time, daily, weekly), and known limitations or lag
7. **Design layout for scanning speed**: Structure the dashboard for F-pattern or Z-pattern scanning — most critical metrics top-left, summary before detail, consistent visual hierarchy, minimal cognitive load
8. **Add narrative guidance**: Write "how to read this" instructions for each section — what good looks like, what bad looks like, and what action to take in each scenario
9. **Build drill-down structure**: Design three levels of depth — summary view (the dashboard itself), detail view (campaign or channel breakdowns), and root cause view (diagnostic data for investigating anomalies)
10. **Create mobile-friendly variant**: Adapt the dashboard layout for mobile or tablet viewing — prioritize top 3-5 metrics, stack vertically, enlarge touch targets, and simplify visualizations
11. **Add comparison baselines**: Define what each metric is compared against — plan/target, prior period (MoM, QoQ, YoY), industry benchmark, and competitive estimate — with comparison display format

## Output

A structured executive dashboard design containing:

- **North-star metrics (5-7)**: Selected metrics with business rationale explaining why each matters to the executive audience and how it connects to strategic priorities
- **Metric hierarchy diagram**: Visual framework showing leading, lagging, and health metrics with causal relationships and directional influence between them
- **Visualization recommendations**: Chart type, scale, color coding, and annotation style for each metric with rationale for the design choice
- **Alert threshold definitions**: Green/yellow/red boundaries for each metric with specific trigger values, anomaly detection rules, and notification routing
- **Data source mapping**: Metric-by-metric documentation of source system, calculation method, refresh frequency, data latency, and known quality issues
- **Dashboard wireframe layout**: Spatial layout showing metric placement, section grouping, visual hierarchy, and scanning flow optimized for the target audience
- **Narrative guide**: Section-by-section presentation guide explaining how to read each area, what questions it answers, and what actions to consider based on the data shown
- **Drill-down structure**: Three-level depth design — summary (dashboard), detail (channel/campaign breakdown), and root cause (diagnostic investigation) with navigation flow
- **Mobile layout variant**: Adapted design for mobile viewing with prioritized metrics, vertical stacking, simplified charts, and touch-optimized interactions
- **Comparison baseline definitions**: For each metric, the comparison standard (target, prior period, benchmark, competitive) with display format and context notes
- **Refresh cadence and data latency notes**: Documentation of how often each metric updates, expected data lag, and implications for decision timing
- **Executive summary template**: A 3-sentence written narrative template that synthesizes dashboard findings into a verbal briefing — what happened, why it matters, what to do next
- **Glossary of terms**: Plain-language definitions of all metrics and marketing terminology for non-marketing stakeholders with examples and context

## Agents Used

- **analytics-analyst** — Metric selection, hierarchy design, visualization recommendations, data source mapping, alert thresholds, drill-down architecture, refresh cadence, and dashboard layout optimization
