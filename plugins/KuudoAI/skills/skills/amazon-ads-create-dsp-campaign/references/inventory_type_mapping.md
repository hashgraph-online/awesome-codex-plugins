# Inventory Type: Campaign vs Ad Group Enum Names

The same concept — "inventory type" — uses **different enum values** at the campaign level vs the ad group level. This is an API naming inconsistency, not a different concept.

When the user says "I want display and streaming TV", that maps to:
- Campaign `primaryInventoryTypes`: `["DISPLAY", "VIDEO_STV"]`
- Ad Group `inventoryType`: `DISPLAY` or `STREAMING_TV`

## Translation Table

| User intent | Campaign field: `primaryInventoryTypes` | Ad Group field: `inventoryType` |
|---|---|---|
| Display | `DISPLAY` | `DISPLAY` |
| Streaming TV | `VIDEO_STV` | `STREAMING_TV` |
| Online Video | `VIDEO_OLV` | `ONLINE_VIDEO` |
| Live Events | `LIVE_EVENTS` | `LIVE_EVENTS` |
| Audio | `AUDIO` | `AUDIO` |

## When to translate

- **Step 2 (create campaign)**: Use the campaign column values in `optimizations.primaryInventoryTypes`
- **Step 4 (query eligible tactics)**: The response returns `primaryInventoryType` (campaign-level names)
- **Step 5 (create ad group)**: Translate `primaryInventoryType` from the eligible tactics response to the ad group column value for the `inventoryType` field

## Example

Eligible tactics response returns:
```json
{ "primaryInventoryType": "VIDEO_STV", "tacticType": "PROSPECTING" }
```

When creating the ad group, translate `VIDEO_STV` → `STREAMING_TV`:
```json
{ "inventoryType": "STREAMING_TV", "automatedTargetingTactic": "PROSPECTING" }
```

## Tactic ↔ Goal KPI Compatibility

| Tactic Type | Compatible KPIs | Campaign Goal |
|---|---|---|
| CUSTOMER_ACQUISITION (P+) | ROAS | CONVERSIONS |
| RETENTION (P+) | ROAS | CONVERSIONS |
| REMARKETING (P+) | ROAS | CONVERSIONS |
| MAXIMIZE_PERFORMANCE (P+) | COST_PER_DETAIL_PAGE_VIEW, DETAIL_PAGE_VIEW_RATE | CONVERSIONS |
| PROSPECTING (B+) | REACH, FREQUENCY_AVERAGE, COST_PER_VIDEO_COMPLETION, VIDEO_COMPLETION_RATE | AWARENESS |
