# Marketing Dashboard Design — Architecture & Best Practices

## Dashboard Hierarchy

Marketing dashboards should exist in three tiers, each serving a different audience, cadence, and depth of detail.

```
Executive Dashboard (C-Suite, VP)
├── 5-7 KPIs | Monthly review | Strategic decisions
│
Operational Dashboard (Directors, Managers)
├── 15-20 metrics | Weekly review | Tactical adjustments
│
Campaign Dashboard (Specialists, Analysts)
└── 30+ metrics | Daily/real-time | Execution optimization
```

| Tier | Audience | KPI Count | Review Cadence | Time Range | Update Frequency |
|------|----------|-----------|----------------|------------|-----------------|
| Executive | C-suite, VP, Board | 5-7 | Monthly | MoM, QoQ, YoY | Weekly refresh |
| Operational | Directors, Managers | 15-20 | Weekly | WoW, MoM | Daily refresh |
| Campaign | Specialists, Analysts | 30+ | Daily | Daily, hourly | Real-time or hourly |

---

## Executive Dashboard Template

### Purpose
Give leadership a single-screen view of marketing's impact on business outcomes. No scrolling. No tabs. Every metric has context (vs. target, vs. prior period).

### Required Metrics (5-7 maximum)

| Metric | Visualization | Context Needed |
|--------|--------------|----------------|
| Marketing-sourced revenue | Scorecard with sparkline | vs. target, vs. same month last year |
| Blended CAC | Scorecard with trend arrow | vs. target, MoM change |
| Marketing-influenced pipeline | Scorecard with sparkline | vs. target, vs. prior month |
| Blended ROAS or ROI | Scorecard with trend arrow | vs. target, channel breakdown in tooltip |
| Total qualified leads (MQL/SQL/PQL) | Bar chart (monthly, 6-month trend) | vs. target line overlay |
| Channel mix (% revenue by channel) | Stacked bar or donut | MoM shift highlighted |
| Funnel conversion rate | Horizontal funnel chart | vs. benchmark, vs. prior period |

### Executive Dashboard Layout

```
┌────────────────────────────────────────────────────────────────┐
│  MARKETING PERFORMANCE — [Month] [Year]          [Date range] │
├──────────┬──────────┬──────────┬──────────┬──────────┐        │
│ Revenue  │ CAC      │ Pipeline │ ROAS     │ Leads    │        │
│ $1.2M    │ $142     │ $4.8M    │ 5.2x     │ 3,841    │        │
│ ▲ +12%   │ ▼ -8%    │ ▲ +18%   │ ▲ +0.3x  │ ▲ +15%   │        │
│ vs target│ vs target│ vs target│ vs target│ vs target│        │
├──────────┴──────────┴──────────┴──────────┴──────────┘        │
│                                                                │
│  ┌─── Revenue by Channel (6-mo) ──┐  ┌── Funnel (MoM) ──────┐│
│  │ [Stacked bar chart]             │  │ Visitors → Leads      ││
│  │                                 │  │ Leads → MQLs          ││
│  │                                 │  │ MQLs → SQLs           ││
│  │                                 │  │ SQLs → Closed Won     ││
│  └─────────────────────────────────┘  └───────────────────────┘│
└────────────────────────────────────────────────────────────────┘
```

### Executive Dashboard Rules

- [ ] Every metric shows comparison context (vs. target, vs. prior period, vs. same period last year)
- [ ] Color coding: green = on track, yellow = within 10% of target, red = more than 10% off target
- [ ] No more than 7 metrics on the primary view
- [ ] Trend direction arrows on every scorecard
- [ ] Date range selector defaults to current month with prior month comparison
- [ ] No jargon — use business language, not platform-specific terms

---

## Operational Dashboard Template

### Purpose
Enable marketing managers to identify issues, spot opportunities, and make weekly tactical adjustments across all channels.

### Metric Groups

#### Traffic & Acquisition

| Metric | Visualization | Alert Threshold |
|--------|--------------|-----------------|
| Daily sessions (total + by channel) | Line chart with channel breakdown | >20% drop vs. 7-day average |
| New vs returning visitors | Stacked area chart | Returning visitor share drop >15% |
| Organic search sessions | Line chart with trend | >15% WoW decline |
| Paid traffic sessions | Line chart by platform | Budget pacing >120% or <80% |
| Referral traffic | Bar chart top 10 sources | New high-volume referrer alert |
| Direct traffic | Line chart | Spike may indicate tracking issue |

#### Conversion & Revenue

| Metric | Visualization | Alert Threshold |
|--------|--------------|-----------------|
| Overall conversion rate | Line chart with 30-day average | >15% drop vs. 30-day average |
| Conversion rate by channel | Bar chart (horizontal) | Any channel >20% below average |
| Revenue by channel (daily) | Stacked area chart | >25% drop in any channel |
| Average order value | Line chart with trend | >10% drop vs. trailing average |
| Cart abandonment rate | Line chart | >5 point increase over baseline |
| Lead-to-MQL rate | Funnel percentage | Drop below 20% |
| MQL-to-SQL rate | Funnel percentage | Drop below 30% |

#### Email Performance

| Metric | Visualization | Alert Threshold |
|--------|--------------|-----------------|
| Email send volume (weekly) | Bar chart | N/A |
| Open rate by campaign type | Grouped bar chart | Drop below 15% |
| Click rate by campaign type | Grouped bar chart | Drop below 2% |
| Unsubscribe rate | Line chart | Spike above 0.5% per campaign |
| List growth rate (net) | Line chart | Negative growth for 2+ weeks |
| Revenue per email sent | Scorecard with trend | Drop below $0.10 |

#### Social Media

| Metric | Visualization | Alert Threshold |
|--------|--------------|-----------------|
| Engagement rate by platform | Bar chart (horizontal) | Drop >25% vs. trailing average |
| Follower growth (net) | Line chart by platform | Negative growth on any platform |
| Social traffic to website | Line chart | >30% drop WoW |
| Top-performing posts (weekly) | Table with engagement metrics | N/A (informational) |

#### Paid Advertising

| Metric | Visualization | Alert Threshold |
|--------|--------------|-----------------|
| Daily spend by platform | Stacked bar chart | Pacing >120% of daily budget |
| CPA by platform | Line chart | CPA >130% of target |
| ROAS by platform | Bar chart | ROAS <80% of target |
| Impression share (search) | Line chart | Drop below 70% for brand terms |
| Quality Score distribution | Histogram | >30% of keywords below QS 5 |

---

## Campaign Dashboard Template

### Purpose
Provide real-time performance data for active campaigns so specialists can optimize execution daily.

### Campaign-Level Metrics

| Metric | Update Frequency | Visualization |
|--------|-----------------|--------------|
| Impressions (cumulative + daily) | Real-time | Line chart with target pace line |
| Clicks and CTR | Real-time | Scorecard + line chart |
| Conversions and CVR | Hourly | Scorecard + line chart |
| Cost and CPA | Hourly | Scorecard + budget burn-down chart |
| ROAS | Hourly | Scorecard with trend |
| Budget pacing | Real-time | Progress bar (% of budget spent vs. % of period elapsed) |
| A/B test status | Daily | Table (variant, impressions, CVR, confidence level) |
| Ad-level performance | Daily | Table sortable by CTR, CPA, ROAS |
| Keyword performance | Daily | Table with QS, CPC, conversions |
| Audience performance | Daily | Table by audience segment |
| Placement performance | Daily | Table by device, location, time of day |

### Budget Pacing Visualization

```
Budget: $10,000 | Period: Nov 1-30 | Today: Nov 15 (50% elapsed)

Ideal pace:   ████████████████░░░░░░░░░░░░░░░░  50% ($5,000)
Actual spend:  ███████████████████░░░░░░░░░░░░░  58% ($5,800)  ⚠️ Over-pacing

Status: Over-pacing by 8% — reduce bids by 5-10% or pause low-performers
```

---

## Visualization Best Practices

### Chart Type Selection Guide

| Data Type | Best Visualization | When to Use | Avoid |
|-----------|-------------------|-------------|-------|
| Single KPI (current value) | Scorecard / Big number | Executive summary, key metrics | Using a chart for a single number |
| Trend over time (1 metric) | Line chart with sparkline | Traffic, conversion rate, revenue trends | Pie chart for time-series data |
| Trend over time (multiple) | Multi-line or stacked area | Channel comparison over time | More than 5 lines on one chart |
| Comparison (categories) | Horizontal bar chart | Channel performance, campaign comparison | 3D charts, vertical bars with long labels |
| Part of whole | Donut chart or stacked bar | Budget allocation, traffic mix | Pie chart with more than 6 slices |
| Distribution | Histogram | Quality Score distribution, CPC ranges | Line chart for non-continuous data |
| Funnel / flow | Funnel chart or Sankey | Conversion funnel stages | Bar chart for sequential flow data |
| Performance vs target | Bullet chart or gauge | KPI vs target tracking | Complicated gauge with multiple needles |
| Two metrics correlation | Scatter plot | CPC vs conversion rate, spend vs revenue | Without clear axis labels and context |
| Time-of-day/day-of-week | Heatmap | Engagement patterns, conversion timing | Line chart with 168 hourly data points |
| Geographic | Choropleth map | Regional performance | Maps for non-geographic data |
| Comparison of many items | Table with conditional formatting | Keyword reports, ad comparisons | Overly complex charts |

### Design Principles

- [ ] Use consistent color palettes across all dashboards (assign one color per channel permanently)
- [ ] Left-to-right reading order: most important metrics on the top-left
- [ ] White space between sections — do not cram metrics together
- [ ] Every chart has a title that states the insight, not just the metric name ("Revenue is trending 12% above target" not "Revenue")
- [ ] Include the date range and last refresh time on every dashboard page
- [ ] Use consistent number formatting (currency, percentages, abbreviations)
- [ ] Add annotations for known events (campaign launch, site outage, holiday, algorithm update)
- [ ] Sparklines for compact trend visualization on scorecards
- [ ] Conditional formatting: red/yellow/green tied to specific thresholds, not arbitrary ranges

---

## Alert Threshold Configuration

### Critical Alerts (Immediate Notification)

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Website traffic drop | >30% vs. 7-day average (hourly check) | Check for site issues, tracking breaks, algorithm changes |
| Conversion rate collapse | >40% drop vs. 7-day average | Check landing pages, checkout, forms, tracking |
| Ad spend spike | >150% of daily budget | Check for automated bid runaway, budget caps |
| Revenue drop | >25% vs. same day last week | Cross-reference traffic, CVR, AOV to diagnose |
| Campaign disapprovals | Any ad or keyword disapproved | Review disapproval reason, fix, resubmit |

### Warning Alerts (Next Business Day)

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Traffic decline | >20% vs. 7-day average (daily check) | Investigate by channel |
| Conversion rate drop | >15% vs. 30-day average | A/B test check, landing page audit |
| CPA increase | >20% above target for 3+ consecutive days | Bid adjustments, audience review |
| Email bounce rate | >5% on any send | List hygiene, domain reputation check |
| Bounce rate spike | >10 point increase over baseline | Content relevance, page speed, mobile UX |
| Ad budget under-spend | <70% of daily budget by end of day | Check bid competitiveness, targeting restrictions |

### Informational Alerts (Weekly Review)

| Condition | Threshold | Action |
|-----------|-----------|--------|
| Keyword quality score drop | Any keyword drops 2+ points | Review ad relevance and landing page |
| New high-traffic referrer | Referral source sends 100+ sessions/week | Investigate source, consider partnership |
| Audience fatigue | Frequency >10 per user per week | Refresh creative, expand audience |
| Organic ranking change | Any top-10 keyword drops out of page 1 | Content refresh, technical audit |

---

## Tool Recommendations

| Tool | Price | Best For | Key Strengths |
|------|-------|----------|---------------|
| Google Looker Studio | Free | GA4-native dashboards, small teams | Deep Google integration, custom connectors, shareable links |
| Tableau | $70-150/user/mo | Enterprise analytics, complex data blending | Powerful data modeling, advanced visualizations, large datasets |
| Power BI | $10-20/user/mo | Microsoft ecosystem teams | Excel integration, affordable, DAX for custom calculations |
| Databox | $0-199/mo | Multi-source dashboard aggregation | 70+ native integrations, mobile-first, goal tracking |
| Klipfolio | $90-400/mo | Agency reporting (multi-client) | White-label, automated distribution, 100+ data sources |
| Supermetrics | $29-579/mo | Data pipeline to spreadsheets/BI tools | Pulls from 100+ marketing platforms, scheduled refreshes |
| Google Sheets + Supermetrics | ~$30/mo | Lean teams, custom analysis | Flexible, scriptable, familiar interface |
| Mixpanel / Amplitude | $0-custom | Product and growth dashboards | Event-based analytics, funnel and cohort analysis |

### Tool Selection Decision Tree

```
Do you primarily use Google ecosystem (GA4, Google Ads)?
├── Yes → Looker Studio (free, native integration)
│   └── Need advanced modeling? → Add Supermetrics for data pipeline
│
├── No → Multi-platform data sources?
│   ├── Yes, many sources → Databox or Klipfolio (pre-built connectors)
│   └── Few sources → Power BI (affordable) or Tableau (powerful)
│
└── Agency with multiple clients?
    └── Klipfolio (white-label) or Databox (automated reports)
```

---

## Data Freshness Trade-offs

| Freshness Level | Update Frequency | Typical Use | Trade-off |
|----------------|-----------------|-------------|-----------|
| Real-time | Continuous/seconds | Campaign dashboards, spend monitoring | Higher API costs, more complex infrastructure |
| Near-real-time | Every 15-60 minutes | Operational dashboards, budget pacing | Moderate complexity, most actionable |
| Daily | Once per day (overnight) | Operational and executive dashboards | Simple to build, sufficient for most decisions |
| Weekly aggregate | Weekly rollup | Executive dashboards, trend analysis | Smooths noise, misses daily anomalies |
| Monthly aggregate | Monthly rollup | Board reports, strategic reviews | Long-term trends only, no tactical value |

### Recommended Freshness by Dashboard

- **Executive:** Daily refresh is sufficient (decisions are monthly/quarterly)
- **Operational:** Daily refresh minimum, hourly for paid advertising metrics
- **Campaign:** Real-time for spend and impressions, hourly for conversions and CPA

---

## Dashboard Anti-Patterns

| Anti-Pattern | Why It Fails | Fix |
|-------------|-------------|-----|
| Vanity metrics only | Impressions and followers without business outcomes mislead leadership | Always tie to revenue, pipeline, or conversion |
| Too many metrics | 50+ metrics on one screen causes analysis paralysis | Enforce the tier system — 7 max for executive |
| No comparison context | A number without context is meaningless ("1,234 conversions" — is that good?) | Always show vs. target, vs. prior period, vs. benchmark |
| Missing date range | Metrics without clear time period are uninterpretable | Display date range prominently on every page |
| Stale data without notice | Dashboard shows data from 3 days ago without indicating it | Show "Last updated: [timestamp]" prominently |
| Inconsistent definitions | "Conversion" means different things on different charts | Include metric definitions in a glossary tab |
| No drill-down path | Executive sees a red metric but can't investigate further | Link executive → operational → campaign dashboards |
| Chart overload | Every metric in a complex chart when a table would be clearer | Use the simplest effective visualization |
| No annotations | Sudden metric changes with no context on what happened | Add event markers (launches, outages, holidays, updates) |
| Platform-specific jargon | Using "CPM" and "ROAS" with a non-marketing executive audience | Translate to business language for executive dashboards |

---

## Business Model Templates

### SaaS Dashboard Focus Areas

| Dashboard Tier | Key Metrics | Unique Considerations |
|---------------|------------|----------------------|
| Executive | MRR, NRR, CAC, LTV:CAC, Qualified Pipeline | Show MRR waterfall (new + expansion - contraction - churn) |
| Operational | Lead velocity, activation rate, trial-to-paid, feature adoption | Track product-qualified leads alongside marketing-qualified leads |
| Campaign | Demo requests, free trial starts, content downloads by stage | Attribution to pipeline is critical — track through CRM |

### eCommerce Dashboard Focus Areas

| Dashboard Tier | Key Metrics | Unique Considerations |
|---------------|------------|----------------------|
| Executive | Revenue, AOV, CVR, ROAS, Repeat Purchase Rate | Revenue by channel with margin overlay |
| Operational | Traffic by source, cart abandonment, email revenue %, product performance | Segment by new vs returning customer revenue |
| Campaign | ROAS by campaign, product-level performance, dynamic ad metrics | Daily stock-level feed health monitoring |

### B2B Lead Gen Dashboard Focus Areas

| Dashboard Tier | Key Metrics | Unique Considerations |
|---------------|------------|----------------------|
| Executive | Pipeline generated, marketing-sourced revenue, CAC by channel | Long attribution windows (60-180 days) |
| Operational | MQLs, SQLs, lead-to-opportunity rate, content engagement | Track by persona and account tier |
| Campaign | CPL, lead quality score, form completion rate, content downloads | Lead scoring alignment with sales feedback |

### Agency Dashboard Focus Areas

| Dashboard Tier | Key Metrics | Unique Considerations |
|---------------|------------|----------------------|
| Client executive | Client-specific KPIs, ROAS, goal progress | White-labeled, branded, simple |
| Account manager | Cross-client performance, at-risk accounts, upsell signals | Efficiency metrics (hours per account, margin) |
| Specialist | Platform-specific performance, optimization opportunities | Deep platform metrics with benchmark context |

---

## Implementation Checklist

- [ ] Dashboard hierarchy defined (executive, operational, campaign)
- [ ] Metric owners assigned for every metric on every dashboard
- [ ] Data sources connected and validated (cross-check with platform native reports)
- [ ] Refresh frequency configured per dashboard tier
- [ ] Color palette standardized across all dashboards (one color per channel/source)
- [ ] Alert thresholds configured for critical and warning conditions
- [ ] Comparison context added to every metric (vs. target, vs. prior period)
- [ ] Drill-down paths linked between dashboard tiers
- [ ] Glossary tab with metric definitions added to each dashboard
- [ ] Event annotations configured for campaigns, launches, outages
- [ ] Access permissions set (executives see executive tier, not campaign noise)
- [ ] Automated distribution scheduled (email PDFs weekly, link sharing)
- [ ] Quarterly dashboard audit scheduled (remove unused metrics, add new ones)
- [ ] User training completed for all dashboard consumers

---

*A dashboard that nobody checks is worse than no dashboard at all. Design for your audience's decisions, not your analyst's curiosity. Every metric on screen should answer a question someone actually asks, and every answer should suggest an action they can actually take.*
