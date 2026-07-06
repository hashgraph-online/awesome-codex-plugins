---
name: attribution-model
description: "Set up attribution models. Use when: multi-touch attribution, credit distribution rules, GA4 config, channel contribution."
---

# /digital-marketing-pro:attribution-model

## Purpose

Design and recommend a multi-touch attribution model with implementation guidance, credit distribution rules, and platform-specific configuration. Produces a complete attribution strategy tailored to the business's data maturity, sales cycle, and analytics infrastructure.

## Input Required

The user must provide (or will be prompted for):

- **Sales cycle length**: Average number of days from first touchpoint to conversion (e.g., 7 days for e-commerce, 90+ days for B2B enterprise)
- **Active marketing channels**: All channels currently running — paid search, paid social, organic search, email, display, video, affiliate, direct mail, events, referral, content marketing, etc.
- **Conversion types**: The key conversion events being tracked — lead form, MQL, SQL, opportunity, customer, revenue, or e-commerce purchase
- **Data maturity level**: Current analytics sophistication — beginner (basic GA4, limited tagging), intermediate (UTM tracking, CRM integration, multi-platform), or advanced (data warehouse, CDI, unified user IDs)
- **Current analytics tools**: Platforms in use — GA4, HubSpot, Salesforce, Adobe Analytics, Mixpanel, custom data warehouse, or third-party attribution tools
- **Touchpoint volume**: Approximate monthly interactions across all channels (thousands, tens of thousands, hundreds of thousands)
- **Offline touchpoints**: Whether offline channels (trade shows, phone calls, direct mail, in-store visits, sales meetings) play a role in the customer journey
- **Budget allocation philosophy**: How budget decisions are currently made — gut feel, last-click data, blended ROAS, executive direction, or existing attribution data
- **Previous attribution approach**: Any existing attribution model in use and its known shortcomings or limitations
- **Key business questions**: What specific decisions attribution data needs to inform — budget allocation, channel investment, campaign optimization, executive reporting, or vendor evaluation

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Assess data maturity and touchpoint landscape**: Map all active touchpoints across channels, evaluate tracking coverage (what percentage of interactions are captured), identify user identity resolution capabilities (logged-in vs. anonymous, cross-device stitching), and score overall data readiness on a 1-5 scale.
3. **Evaluate attribution model options**: Analyze seven model types against the business context — last-touch (simple but biased to bottom-funnel), first-touch (biased to top-funnel), linear (equal credit, ignores position importance), time-decay (favors recency), position-based/U-shaped (weights first and last), data-driven (algorithmic, requires volume), and marketing mix modeling (aggregate, handles offline). Score each on data requirements, accuracy, actionability, and implementation complexity.
4. **Recommend primary model with rationale**: Select the best-fit model based on sales cycle length, data maturity, touchpoint volume, and business questions. Provide a clear explanation of why this model fits and where it will still have blind spots. If data maturity is low, recommend a phased approach starting with a simpler model and graduating to data-driven as tracking matures.
5. **Define credit distribution rules**: Specify exactly how conversion credit is allocated — percentage per touchpoint position, time-decay half-life window, position-based weight splits (e.g., 40% first, 40% last, 20% distributed across middle), and rules for single-touch conversions vs. multi-touch journeys.
6. **Design lookback window**: Set the attribution lookback window based on sales cycle data — typically 1.5-2x the average sales cycle length. Define separate windows for click-through and view-through attribution. Justify the window length with sales cycle analysis and explain the tradeoffs of shorter vs. longer windows.
7. **Map implementation steps per analytics platform**: Create platform-specific configuration guides — GA4 attribution model settings and conversion path reports, HubSpot multi-touch revenue attribution setup, Salesforce campaign influence configuration, and custom data warehouse query logic. Include step-by-step setup instructions for each tool in the stack.
8. **Identify data gaps and tracking requirements**: Audit current tracking against the recommended model's requirements — missing UTM parameters, untagged campaigns, broken cross-domain tracking, absent offline touchpoint capture, incomplete CRM integration, and consent management gaps. Prioritize fixes by impact on attribution accuracy.
9. **Create attribution reporting framework**: Design the reporting structure — attribution dashboard layout, key metrics (attributed revenue per channel, cost per attributed conversion, ROAS by model), comparison views (model A vs. model B side-by-side), trend analysis over time, and executive summary format.
10. **Define model evaluation criteria**: Set review cadence (quarterly) and criteria for reassessing the model — changes in channel mix, sales cycle shifts, new touchpoint types, data maturity improvements, or significant discrepancies between attributed performance and actual business outcomes.
11. **Document limitations and known blind spots**: Explicitly state what the model cannot capture — cross-device gaps, walled garden limitations (Meta, Google self-reporting), view-through estimation inaccuracies, offline-to-online stitching failures, privacy regulation impacts on tracking, and the inherent impossibility of perfect attribution. Frame expectations for stakeholders.

## Output

A structured attribution model recommendation containing:

- **Attribution model recommendation** with detailed rationale connecting the model choice to sales cycle, data maturity, and business questions
- **Credit distribution rules** — percentage allocation per touchpoint position with examples showing how a sample multi-touch journey would be credited
- **Lookback window recommendation** with sales cycle justification, click-through vs. view-through windows, and tradeoff analysis
- **Implementation guide per platform** — step-by-step GA4 attribution setup, HubSpot multi-touch configuration, Salesforce campaign influence settings, and custom warehouse query templates
- **Touchpoint taxonomy** — standardized hierarchy of channel, source, medium, and campaign with naming conventions for consistent tracking
- **Data requirements checklist** — what must be tracked, tagged, and integrated for the model to function accurately
- **Tracking gap analysis** — identified gaps ranked by impact on attribution accuracy, with fix recommendations and effort estimates
- **Attribution reporting dashboard spec** — metrics, dimensions, filters, visualizations, comparison views, and executive summary format
- **Model comparison table** — 6-7 models compared side-by-side on pros, cons, data requirements, best-fit scenarios, and implementation complexity
- **Evaluation framework** — quarterly review criteria, model reassessment triggers, and maturity graduation path from simple to advanced models
- **Known limitations and blind spots** — explicit documentation of what the model cannot measure with stakeholder expectation-setting guidance
- **Cross-device and cross-platform considerations** — user identity resolution approaches, deterministic vs. probabilistic matching, and platform-specific limitations
- **Offline-to-online stitching recommendations** — methods for incorporating trade shows, phone calls, direct mail, and in-person interactions into the digital attribution model

## Agents Used

- **analytics-analyst** — Data maturity assessment, attribution model evaluation, credit distribution design, lookback window analysis, platform implementation guidance, tracking gap identification, reporting framework design, and limitation documentation
