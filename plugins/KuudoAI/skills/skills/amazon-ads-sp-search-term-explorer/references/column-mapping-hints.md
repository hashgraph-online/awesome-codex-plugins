# Column mapping — SP Search Term report (MCP v1)

This skill processes **MCP-generated** SP Search Term reports from `allv1_AdsApiv1CreateReport`. The downloaded CSV uses **v1 dotted field IDs** as column headers (`searchTerm.value`, `metric.totalCost`, etc.) — **not** legacy Console headers like `Customer Search Term` or `7 Day Total Sales`.

If the user pastes a CSV with legacy headers, it is **not** an MCP report — refuse or fall back gracefully (this skill cannot adapt to ad-hoc shapes; see [`agent-codegen-v1.md`](agent-codegen-v1.md) for the strict DictReader required-column check).

## Role → v1 field ID (authoritative)

| Role | v1 field ID | Notes |
|------|-------------|-------|
| Time dimension | `date.value` | Exactly **one** time dimension per query |
| Search term (query **or** PAT ASIN) | `searchTerm.value` | Customer queries **and** ASIN strings from product targeting — **partition** before keyword negatives (see [`segment-rules.md`](segment-rules.md)) |
| Cost / spend | `metric.totalCost` | **Not** `metric.cost` or `metric.spend` — rejected as unknown. Requires `budgetCurrency.value` in the same query |
| Sales | `metric.sales` | Amazon **v1 default** attribution window for this field (undocumented at field level; commonly treated as **~14d** SP — disclose, don't assert precision). Requires `budgetCurrency.value` |
| Clicks | `metric.clicks` | |
| Impressions | `metric.impressions` | |
| Orders / purchases | `metric.purchases` | v1 default attribution (pair with sales disclosure) |
| Campaign context | `campaign.id`, `campaign.name` | At least one **LOD** dimension required by the query shape |
| Ad group context | `adGroup.id`, `adGroup.name` | |
| Currency (required companion) | `budgetCurrency.value` | **Must** be in `fields` whenever any currency-valued metric (cost, sales) is requested |
| SP-only scope | Filter | `adProduct.value` `EQUALS` `SPONSORED_PRODUCTS` — **not** `sponsoredProducts.adProduct` or other legacy prefix |

## Pinned field list (empirically valid for SP search term mining)

Use this list for `report_fields` `mode=validate` and `CreateReport` (full workflow in [`mcp-workflow.md`](mcp-workflow.md)):

`date.value`, `campaign.id`, `campaign.name`, `adGroup.id`, `adGroup.name`, `searchTerm.value`, `metric.impressions`, `metric.clicks`, `metric.totalCost`, `metric.sales`, `metric.purchases`, `budgetCurrency.value`

Plus query **filter** on `adProduct.value` `EQUALS` `SPONSORED_PRODUCTS`.

## ASINs inside the `searchTerm.value` column

Product targeting (PAT) campaigns surface **ASIN strings** alongside real customer queries in the same `searchTerm.value` column. This is a format-agnostic fact about how SP reports work — it's not an MCP quirk.

- **Detect:** `^B0[A-Z0-9]{8}$` for modern ASINs (10 characters; extend per catalog for legacy IDs).
- **Never** keyword-negate ASIN strings — those need negative product targets / PAT workflow, not keyword negation.
- **Default:** exclude from keyword gold/rising/negatives. See [`segment-rules.md`](segment-rules.md) for the full ASIN-vs-query partition rules.

## Do **not** expect on this v1 CreateReport path

These show up in legacy/console exports or in older v3 APIs but are **not** v1 outputs:

- `metric.cost`, `metric.spend`, `metric.spendAmount` — unknown / rejected at validate time
- `metric.sales7d`, `metric.purchases7d`, or other **suffix-attributed** variants — not supported here; agents needing strict 7d/14d labels need a different reporting path (the v3 API or `rp_*` v3 tools)
- `keyword.text`, `keyword.value`, `keyword.matchType` — not available as v1 **output** fields for this pattern
- **Spaced Title Case headers** (`Customer Search Term`, `7 Day Total Sales`) — legacy export shape, **not** v1 API CSV
- Any column prefixed `sponsoredProducts.*` — v1 namespace for this report is **flat**: `metric.*`, `campaign.*`, `adGroup.*`, `searchTerm.*`, `date.*`, `budgetCurrency.*`, with `adProduct.*` only used in **filters**

## Grain

Default: `searchTerm.value × campaign.id × adGroup.id × date.value`. For portfolio mining: sum additive metrics, then ASIN-vs-text split, then brand markers, then sufficiency gates (see [`segment-rules.md`](segment-rules.md)).

For per-campaign or per-ad-group views, the LOD dimensions are already in the pinned field list — just group differently in the parsing step ([`agent-codegen-v1.md`](agent-codegen-v1.md) Pattern 3).

## Pitfalls

- **Percent / currency strings** are normalized to numerics by the v1 export, but defensive parsing helps when the locale produces unexpected separators (`,` vs `.` decimal in some EU marketplaces).
- **Keyword actions on ASIN rows** → wrong recommendations. Always partition before applying gold/rising/negative logic.
- **Sales-attribution drift** — `metric.sales` reflects whatever the v1 default attribution window is, which may differ from what the user remembers from v3 Console. Disclose this in the deliverable's §1 provenance line.
