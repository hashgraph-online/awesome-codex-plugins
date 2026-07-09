---
name: exec-summary
description: "Generate C-suite executive summaries. Use when: preparing board reports, portfolio ROI, or strategic reviews."
---

# /digital-marketing-pro:exec-summary

## Purpose

Generate a concise, C-suite-ready executive summary of marketing performance. Focuses on business-level metrics — ROI, CAC, LTV, market share — rather than operational detail. Synthesizes strategic wins and risks, competitive positioning, and high-level recommendations into a format designed for executive decision-making. Supports single-brand summaries or portfolio-wide aggregation across all managed brands, and adapts depth and terminology to the target audience (CEO, CMO, board).

Designed to be the single artifact an executive needs to understand marketing's business impact, make resource allocation decisions, and assess strategic direction — without requiring follow-up questions or supplementary reports.

## Input Required

The user must provide (or will be prompted for):

- **Scope**: Whether to summarize a single brand (uses active brand) or the entire portfolio (aggregates across all brands in `~/.claude-marketing/brands/`). Portfolio mode requires at least two configured brands
- **Time period**: The reporting window — this month, this quarter, this year, last 30 days, last 90 days, or a custom date range. Determines which data is pulled and which comparison baselines are used
- **Focus areas** (optional): Specific topics to emphasize — e.g., "paid media ROI", "customer acquisition", "content performance", "email revenue", "brand awareness". If omitted, the summary covers all active channels proportionally
- **Audience**: Who will read this — CEO (business outcomes, market position, growth trajectory), CMO (channel performance, team efficiency, strategic initiatives), CFO (ROI, CAC payback, budget utilization), VP Marketing (tactical wins, pipeline impact), or board (high-level portfolio health, competitive position, strategic direction)
- **Delivery format** (optional): How the summary should be delivered — markdown (default), Slack message, email draft, Google Sheets, or Google Slides. Multiple formats can be requested simultaneously
- **Competitive context** (optional): Whether to include competitive positioning analysis — requires prior competitor data from `/digital-marketing-pro:competitor-analysis` or connected competitive intelligence MCPs
- **Comparison baseline** (optional): What to compare against — prior period (MoM, QoQ), same period last year (YoY), plan/target, or industry benchmark. Defaults to prior period and YoY if data is available
- **Prior executive summary** (optional): Reference to a previous exec summary to enable period-over-period narrative continuity — tracks whether prior risks were mitigated, prior recommendations were acted on, and whether the trajectory improved

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Gather performance data**: For single brand — pull metrics from all connected MCPs (Google Analytics, Google Ads, Meta Ads, HubSpot, Salesforce, etc.), load campaign history from execution logs, load prior performance snapshots for trend comparison. For portfolio — iterate all brands in `~/.claude-marketing/brands/`, aggregate metrics per brand, then roll up to portfolio totals with currency normalization if brands operate in different regions.
3. **Calculate executive KPIs**: Compute the five core executive metrics — Total Marketing ROI (revenue attributed to marketing / total marketing spend), Customer Acquisition Cost (total spend / new customers acquired), Customer Lifetime Value (average revenue per customer x average retention period), estimated market share trend (if competitive data available), and Brand Health Score (composite of awareness, sentiment, engagement, and loyalty indicators). Use the scripts for standardized computation (all have required args):
   ```bash
   python "${CLAUDE_PLUGIN_ROOT}/scripts/clv-calculator.py" --model simple --avg-purchase-value {value} --purchase-frequency {per-year} --customer-lifespan {years} --margin 0.30
   python "${CLAUDE_PLUGIN_ROOT}/scripts/roi-calculator.py" --channels '[{"name":"google_ads","spend":10000,"revenue":42000}]' --attribution last_touch --period "{YYYY-MM}"
   ```
4. **Analyze trends and comparisons**: Compare each KPI against the prior period (MoM or QoQ depending on time range), the same period last year (YoY), and targets or plan if set. Calculate percentage change and flag significant movements — improvement above 10% as a win, decline above 10% as a risk. Project end-of-period trajectory from the current run rate: `python "${CLAUDE_PLUGIN_ROOT}/scripts/revenue-forecaster.py" --historical '[{"period":"2026-05","revenue":120000}]' --forecast-months 3 --growth-assumption 0.05` (SYNTHETIC EXAMPLE — fabricated for illustration; never reuse these numbers).
5. **Review prior summary continuity**: If a prior executive summary was referenced, compare current period against prior recommendations — which were acted on, which were deferred, and how the trajectory changed. Track whether previously flagged risks materialized or were mitigated, and whether prior wins were sustained or regressed.
6. **Identify top 3 wins**: Select the three most impactful positive outcomes in the period — largest ROI improvement, most efficient channel, best-performing campaign, fastest-growing segment, or strongest competitive gain. Each win must include specific data (numbers, percentages, dollar values), business impact framing, and a recommendation to scale or sustain the momentum.
7. **Identify top 3 risks**: Select the three most critical risk signals — declining channel performance, rising CAC, budget overrun, competitive threat, compliance exposure, or market shift. Each risk must include severity assessment (watch, concern, critical), supporting data, projected business impact if unaddressed, and a specific mitigation action with recommended owner and timeline.
8. **Generate strategic recommendations**: Based on wins, risks, and trend data, produce 3-5 prioritized strategic recommendations. Each recommendation includes the action, expected impact (quantified where possible), required investment or effort, timeline, and the data supporting the recommendation. Tailor language and framing to the target audience — financial language for CFO, growth language for CEO, operational language for CMO.
9. **Assess competitive positioning**: If competitive data is available, summarize relative market position — share of voice, share of search, ad impression share, content authority, and social engagement benchmarks versus key competitors. Identify competitive gaps and opportunities. If no competitive data exists, note this as a gap and recommend running `/digital-marketing-pro:competitor-analysis`.
10. **Calculate budget utilization**: Analyze total spend vs. plan, channel-level pacing (over/under), burn rate trajectory, and projected end-of-period spend. Flag channels pacing more than 15% above or below plan. Generate reallocation recommendations for underperforming or overspending channels: `python "${CLAUDE_PLUGIN_ROOT}/scripts/budget-optimizer.py" --channels '[{"name":"google_ads","spend":10000,"roas":4.2}]' --total-budget {amount}` (`--total-budget` is required).
11. **Generate portfolio breakdown** (portfolio mode): For multi-brand portfolios, create per-brand summary cards showing each brand's top KPIs, largest win, biggest risk, and relative contribution to portfolio totals. Rank brands by ROI and flag any brands significantly underperforming the portfolio average. Calculate portfolio-level diversification health — how dependent overall performance is on any single brand.
12. **Format for target audience**: Adapt the summary structure and language for the specified audience — CEO gets a one-page business narrative with bottom-line impact and market trajectory, CMO gets channel-level performance with strategic initiative progress, CFO gets financial efficiency metrics with budget utilization and payback periods, board gets portfolio health with strategic direction and market context.
13. **Deliver via requested channel**: Format the final summary — markdown for direct use, Slack-formatted message for Slack MCP delivery, email draft for email delivery, structured data for Google Sheets, or slide outline for Google Slides. If multiple formats requested, generate each variant. Include data freshness timestamp and methodology footnotes on all outputs.

## Output

A structured executive summary containing:

- **Executive headline**: One-sentence summary of the period's marketing performance — e.g., "Marketing drove $2.4M in attributed revenue at 4.2x ROI, up 18% QoQ, with paid media and email as top performers"
- **5 key KPIs with trend indicators**: Total Marketing ROI, CAC, LTV (CLV), market share estimate, and Brand Health Score — each showing current value, trend arrow (up/down/flat), percentage change vs. prior period, percentage change YoY, and status vs. target (on track, ahead, behind)
- **Top 3 wins**: Each with specific data, business impact, contributing factors, and recommendation to scale or sustain. Framed in executive language — outcome first, then supporting detail
- **Top 3 risks**: Each with severity level (watch/concern/critical), supporting data, projected business impact if unaddressed, specific mitigation action with recommended owner and timeline
- **Strategic recommendations** (3-5): Prioritized list of actions — what to do, why (data-backed), expected impact (quantified), required investment, and recommended timeline. Ordered by expected ROI or strategic importance
- **Prior period follow-up**: Status update on previous recommendations (acted on, deferred, or dropped), prior risk mitigation progress, and whether prior wins were sustained — providing narrative continuity between reporting periods
- **Competitive positioning snapshot**: Share of voice, search visibility, ad presence, and content authority relative to key competitors — with directional trend, competitive gaps, and strategic implications
- **Channel performance summary**: One-line performance summary per active channel — spend, revenue attributed, ROI, trend vs. prior period, and pacing vs. plan — sorted by contribution to overall performance
- **Budget utilization**: Total spend vs. plan, burn rate trajectory, projected end-of-period spend, channel-level pacing flags, and reallocation recommendations for over or under-pacing channels
- **Revenue forecast**: Projected end-of-period revenue based on current trajectory, with confidence range and key assumptions that could shift the outcome
- **One-page visual summary**: Structured layout designed for printing or screen sharing — KPIs at top, wins and risks in the middle, recommendations at bottom, with visual hierarchy optimized for executive scanning
- **Portfolio breakdown** (portfolio mode only): Per-brand summary cards showing each brand's top KPIs, largest win, biggest risk, and relative contribution to portfolio totals. Includes portfolio diversification score and brand-level ROI ranking
- **Data quality notes**: Transparency section documenting which metrics are based on complete data, which have gaps or estimates, which platforms had data latency, and overall confidence level of the summary — ensuring executives know where the numbers are solid and where they should be interpreted with caution
- **Next period outlook**: Forward-looking section with projected KPI trajectories, upcoming campaign launches or strategic initiatives that will affect next period's numbers, and key dates or decisions on the horizon
- **Detailed appendix**: Supporting data tables, channel breakdowns, campaign-level performance, methodology notes, data source documentation, and data freshness timestamps for stakeholders who want to drill deeper
- **Executive talking points**: Three to five bullet points the executive can use verbally in leadership meetings — pre-written sound bites that accurately represent the data without oversimplifying, suitable for board presentations or investor updates
- **Action items with owners**: Extracted from the strategic recommendations — a discrete list of next steps with assigned owners, deadlines, and success criteria so the summary drives action rather than just informing
- **Methodology footnotes**: Brief explanation of how key metrics were calculated, which attribution model was used, and any adjustments made for seasonality, data gaps, or platform reporting discrepancies — ensuring the numbers are defensible if questioned

## Agents Used

- **agency-operations** — Portfolio aggregation, executive formatting, multi-brand data consolidation, currency normalization, delivery channel formatting, and summary structure optimization
- **analytics-analyst** — Metrics calculation, KPI computation, trend analysis, comparison baselines, competitive benchmarking, channel performance analysis, budget utilization tracking, and revenue forecasting
- **marketing-strategist** — Strategic recommendation generation, competitive positioning assessment, risk identification and mitigation planning, win framing, and audience-specific narrative adaptation
