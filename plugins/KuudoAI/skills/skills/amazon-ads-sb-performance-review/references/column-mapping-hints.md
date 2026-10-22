# Column mapping hints (non-authoritative)

Amazon Advertising **Sponsored Brands Campaigns** exports change by report type, API version, and locale. Treat this file as **search ideas** when scanning headers — confirm every mapping on the user’s artifact.

## Semantic roles

| Role | Typical ideas (examples only) | Agent action |
|------|-------------------------------|--------------|
| Campaign key | `campaign`, `campaign name`, `campaignName`, `Campaign` | Prefer stable ID if both ID and name exist for joins |
| Cost / spend | `cost`, `spend`, `Spend` | Same currency as sales |
| Sales | `sales`, `attributed sales`, `purchases sales`, `14 Day Total Sales` | Pick **one** definition per run; document it |
| Impressions | `impressions`, `Impressions` | |
| Clicks | `clicks`, `Clicks` | Exclude columns that are rates if mis-labeled |
| Orders | `orders`, `purchases`, `7 Day Total Orders` | Watch attribution window in header |
| State | `state`, `status`, `campaign status` | Normalize case when filtering enabled |
| Budget | `budget`, `daily budget` | Optional |
| NTB orders | headers containing `new to brand` + `order`, or `ntb` + `order` | Locale-specific spacing |
| NTB sales | `new to brand` + `sales` | |
| Placement / type | `placement`, `top of search`, `video`, `ad type` | Only if present |

## Nested JSON

Exports from APIs may be `{ "reports": [ { "rows": [...] } ] }` or different. The agent must:

1. Print top-level keys.
2. Find the list of row objects or the CSV-equivalent array.
3. Derive column names from the first row’s keys if records are dicts.

## Common pitfalls

- **Multiple sales columns** (1d vs 7d vs 14d): user must choose or default to the window stated in the report name.
- **Percent formatting**: strings like `"12.3%"` need parsing before math.
- **Aggregated vs daily grain**: if each row is campaign-day, aggregate to campaign for “top campaigns” unless the user wants daily charts.
