---
name: live-dashboard
description: "Create live Looker Studio dashboards. Use when: connecting marketing data sources with auto-configured visualizations."
disable-model-invocation: true
argument-hint: "[data-source or dashboard-type]"
---

# /digital-marketing-pro:live-dashboard

## Purpose

Create and configure a live Google Looker Studio dashboard connected to the brand's marketing data sources. Auto-selects appropriate metrics, dimensions, and chart types based on the business model (SaaS, eCommerce, B2B, agency). Provides always-current visibility into marketing performance without manual data pulls. Eliminates the need for recurring report generation by giving stakeholders a self-service, real-time view of the metrics that matter most to their business model, with drill-down capability and date range controls built in.

## Input Required

The user must provide (or will be prompted for):

- **Business model**: `saas` (recurring revenue focus — MRR, churn, activation, expansion), `ecommerce` (transaction focus — revenue, AOV, conversion rate, product performance), `b2b-lead-gen` (pipeline focus — MQLs, SQLs, pipeline value, CPL), or `agency` (multi-client focus — client health scores, utilization, cross-client performance). Determines the default metric set, layout template, and visualization priorities
- **Data sources to connect**: Which platforms to pull into the dashboard — Google Analytics (traffic, behavior, conversions), Google Ads (paid search performance, spend), Meta Ads (paid social performance, spend), CRM (pipeline, deal data, customer lifecycle), email platform (campaign performance, list health). Multiple sources can be combined into unified views with cross-platform calculated fields
- **Primary KPIs to feature**: The 3-5 headline metrics to display prominently at the top of the dashboard — e.g., MRR and churn rate for SaaS, revenue and ROAS for eCommerce, SQLs and pipeline value for B2B. These appear as scorecard widgets with trend indicators and target comparisons
- **Dashboard audience**: `executives` (high-level scorecards with trend arrows, minimal drill-down, focused on business outcomes), `marketing-team` (full operational detail with channel breakdowns, campaign-level data, and diagnostic dimensions), or `client` (branded presentation view with performance against stated objectives, competitive context, and clean visual design)
- **Refresh frequency**: How often the data should update — `real-time` (streaming where supported), `daily` (standard for most use cases), `weekly` (for executive dashboards with less granular needs). Determines data source caching configuration and extract schedule

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Extract business model, key metrics, industry vertical, brand colors for dashboard theming, and connected platform credentials. Check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Design dashboard layout based on business model template**: Select the appropriate metric hierarchy and page structure. For SaaS: page 1 overview (MRR scorecard, churn rate, CAC, LTV, CAC:LTV ratio), page 2 acquisition funnel (traffic to trial to activation to paid, by channel), page 3 retention (cohort retention curves, expansion revenue, net revenue retention). For eCommerce: page 1 overview (revenue, AOV, conversion rate, ROAS), page 2 product performance (top products, category breakdown, inventory velocity), page 3 channel mix (attributed revenue by channel, campaign-level ROAS). For B2B: page 1 overview (MQLs, SQLs, pipeline value, win rate), page 2 funnel (lead to MQL to SQL to opportunity to closed, conversion rates per stage), page 3 channel efficiency (CPL, cost per SQL, cost per opportunity by channel). For Agency: page 1 portfolio overview (client health scores, total managed spend, utilization), page 2 per-client drill-down (selectable client filter with full KPI set), page 3 cross-client benchmarks.
3. **Map data sources to dashboard widgets**: For each widget in the layout, identify which connected MCP provides the required data — Google Analytics MCP for traffic and behavior metrics, Google Ads MCP for paid search data, Meta MCP for paid social data, CRM MCP for pipeline and deal metrics, email MCP for campaign performance. Flag any widgets that require data sources not yet connected and provide connection guidance.
4. **Generate Looker Studio configuration**: Produce the complete dashboard specification — data source connection parameters (account IDs, property IDs, date ranges), calculated field formulas (blended ROAS across platforms, weighted conversion rates, custom KPI calculations), chart specifications (chart type, dimensions, metrics, sort order, conditional formatting), filter controls (date range selector, channel filter, campaign filter, audience segment filter), and page layout with widget positioning and sizing.
5. **Create dashboard setup instructions**: Generate step-by-step guidance for implementing the dashboard in Looker Studio — how to create each data source connection, how to build each page and widget matching the specification, how to configure calculated fields with exact formulas, how to set up filter controls and their interactions, and how to apply brand theming (colors, fonts, logo placement). Include screenshots or visual references where helpful.
6. **Provide dashboard template link or export configuration**: If Looker Studio MCP supports direct dashboard creation, execute it to produce a live dashboard link. Otherwise, export the complete configuration as a structured specification document that can be implemented manually, with each widget fully defined and data source mappings documented.

## Output

A structured dashboard delivery containing:

- **Dashboard design specification**: Complete layout document with page structure, widget placement, chart types, metrics, dimensions, data sources per widget, and conditional formatting rules — organized by page with visual layout descriptions
- **Looker Studio setup guide**: Step-by-step implementation instructions from blank dashboard to fully configured live view — including data source creation, page building, widget configuration, calculated field formulas, and filter setup
- **Data source connection instructions per platform**: Platform-specific guidance for connecting each data source — Google Analytics property ID and view selection, Google Ads account linking, Meta ad account authorization, CRM API connection, email platform integration — with required permissions and scopes
- **Calculated field formulas**: All custom calculated fields with exact Looker Studio formula syntax — blended metrics across platforms, custom KPIs, period-over-period calculations, target comparison fields, and conditional formatting logic
- **Filter and drill-down configuration**: Specification for all interactive controls — date range selector with presets, channel and campaign filters, audience segment selectors, and cross-page drill-down links with parameter passing
- **Dashboard maintenance checklist**: Ongoing maintenance tasks — data source credential refresh schedule, new campaign or channel additions, calculated field updates when KPI definitions change, and quarterly review of metric relevance against business model evolution

## Agents Used

- **analytics-analyst** — Metric selection based on business model and industry benchmarks, dashboard layout design with information hierarchy optimized for the target audience, data source mapping to identify which connected MCPs feed which widgets, and visualization best practices including chart type selection, dimension and metric pairing, conditional formatting thresholds, and drill-down path design
- **execution-coordinator** — Looker Studio configuration generation via `google-looker-studio` MCP including data source setup, calculated field creation, widget specification, and filter control configuration, plus dashboard theming with brand colors and export of setup instructions or live dashboard link
