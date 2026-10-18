# Step 0: Gather and Validate Inputs

Collect all required inputs from the user, apply defaults for optional inputs, and validate before proceeding.

## Required inputs

| Input | Source | Notes |
|---|---|---|
| marketplace | INPUT | Country code (e.g., `US`). Also used for account selection, conversion tracking domain, and language locale |
| campaign start date | INPUT | ISO 8601 datetime with Z suffix (e.g. `2026-10-01T00:00:00Z`; default: next day) |
| campaign end date | INPUT | ISO 8601 datetime with Z suffix (e.g. `2027-10-01T00:00:00Z`; default: 1 year later) |
| campaign budget | INPUT | Monetary amount, must be positive |
| primaryInventoryTypes | INPUT | Array: `DISPLAY`, `VIDEO_OLV`, `VIDEO_STV`, `AUDIO`, `LIVE_EVENTS`. Ad group level uses different names — see [inventory_type_mapping.md](inventory_type_mapping.md) |
| asins | INPUT | Array of ASINs for conversion tracking (Step 3) AND video ad creative product references (Step 6a) |

## Optional inputs

| Input | Default | Notes |
|---|---|---|
| campaign_name | `DSP\|PB\|Campaign yyyy-MM-dd_HH-mm-ss` | Auto-generated with UTC timestamp if not provided |
| bid_strategy | `SPEND_BUDGET_IN_FULL` | Campaign and ad group level |
| goal_kpi | Derived — see Goal KPI inference below | |
| base_bid | `0.1` | Ad group baseBid |
| fees | omit | Pass-through, include only if user provides |
| frequencies | omit | Pass-through, include only if user provides |
| tags | omit | Pass-through, include only if user provides |
| purchaseOrderNumber | omit | Pass-through, include only if user provides |

## Goal KPI inference

The campaign's `goal_kpi` is set at campaign creation (Step 2) and influences which tactics become eligible at ad group level (Step 5). A single campaign can have ad groups with different tactics (both P+ and B+), but the campaign-level KPI must be compatible with the desired tactics.

### Inference rules (in priority order)

1. **User specifies both KPI and tactic** → validate compatibility using the table below. If incompatible, warn the user and suggest the correct KPI for their tactic.
2. **User specifies tactic only** → derive KPI from the table below.
3. **User specifies KPI only** → use it as-is.
4. **User specifies neither** → default to `ROAS` (P+ conversions focus).

### Tactic ↔ Goal KPI compatibility

| Tactic | Compatible KPIs | Campaign Goal |
|---|---|---|
| CUSTOMER_ACQUISITION (P+) | `ROAS` | Conversions |
| REMARKETING (P+) | `ROAS` | Conversions |
| RETENTION (P+) | `ROAS` | Conversions |
| MAXIMIZE_PERFORMANCE (P+) | `COST_PER_DETAIL_PAGE_VIEW`, `DETAIL_PAGE_VIEW_RATE` | Conversions |
| PROSPECTING (B+) | `REACH`, `FREQUENCY_AVERAGE`, `COST_PER_VIDEO_COMPLETION`, `VIDEO_COMPLETION_RATE` | Awareness |

### Common scenarios

- User says "I want to drive sales" or mentions P+ → `ROAS`
- User says "brand awareness" or "prospecting" or mentions B+ → `REACH`
- User says "detail page views" → `COST_PER_DETAIL_PAGE_VIEW`
- User wants mixed P+ and B+ tactics → the KPI must be chosen for the primary goal; some tactics may appear ineligible based on the chosen KPI. Inform the user of this tradeoff.

## Validation rules

- `marketplace`: valid country code
- `campaign_start_date` < `campaign_end_date`
- `campaign_budget` > 0
- `primaryInventoryTypes`: non-empty array of valid values
- `asins`: non-empty array
- All datetime values must include the `Z` UTC suffix

## Name generation

Generate a shared UTC timestamp `yyyy-MM-dd_HH-mm-ss` at the start of the workflow. This timestamp is reused across all entity names:

| Entity | Pattern |
|---|---|
| Campaign | `DSP\|PB\|Campaign yyyy-MM-dd_HH-mm-ss` |
| Ad Group | `DSP\|PB\|{inventoryType}\|{tactic} yyyy-MM-dd_HH-mm-ss` |
| Ad | `DSP\|PB\|Ad\|{adType} yyyy-MM-dd_HH-mm-ss` |

On failure: ask user to correct input.
