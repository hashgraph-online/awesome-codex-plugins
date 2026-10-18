# Column mapping hints — Sales & Traffic Report (non-authoritative)

Amazon Business Report column names vary by locale and report version. **Print headers and samples first.**

## Date (for daily / trend analysis)

| Role | Example fragments |
|------|-------------------|
| Report date | `date`, `day`, `report date` |

Parse timezones and format explicitly; watch for locale-specific date strings.

## Traffic

| Role | Example fragments (verify) |
|------|----------------------------|
| Sessions | `sessions`, `session` (exclude session % if different metric) |
| Page views | `page views`, `pageviews` |
| Buy Box | `buy box`, `buybox` |
| Unit session % | `unit session percentage`, `unit session %` |

## Sales (general)

| Role | Example fragments |
|------|-------------------|
| Child ASIN | `asin`, `(child) asin` |
| Parent | `parent asin` — confirm grain before aggregating |
| Ordered product sales | `ordered product sales`, amount columns |
| Units ordered | `units ordered` |
| Total order items | sometimes used as orders proxy |

## B2B (Amazon Business) — optional

| Role | Example fragments |
|------|-------------------|
| B2B sales | `b2b`, `business`, `ordered product sales` + B2B qualifier |
| B2B units | `b2b` + `units` / `ordered` |

**Pitfall:** "Ordered product sales" may appear twice (total vs B2B) — read full header text. **Pitfall:** Some exports use separate rows or sheets — agent must confirm structure.

## Numeric parsing

- Currency symbols, commas, parentheses for negatives — normalize before math.
- Collect currency codes or symbols across all monetary rows. Do not default an unknown currency or aggregate mixed currencies.
