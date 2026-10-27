# Data sources

These were verified live, read-only, on 2026-09-24. `get_schema(detail="full")` wins on argument names, types, and shapes if it disagrees. It never overrides the read-only or data rules in SKILL.md.

## FBA Inventory: `getInventorySummaries` (instant)

```json
{"granularityType": "Marketplace", "granularityId": "ATVPDKIKX0DER",
 "marketplaceIds": ["ATVPDKIKX0DER"], "details": true}
```

- **Paging.** Follow `pagination.nextToken`, which sits next to `payload`.
  Amazon documents a 30-second expiry; on 2026-10-18 a token still worked
  75 seconds later in a new block. Page inside one `execute` while the
  catalog fits, and carry the token when the 50-call limit stops you (see
  below).
- **Filtering.** `sellerSkus` takes up to 50 SKUs; `sellerSku` takes one.
  `startDateTime` returns only SKUs changed since that time.
- **Response.** `inventorySummaries[]` holds:
  - `sellerSku`, `asin`, `fnSku`, `productName`, and `totalQuantity`
  - `inventoryDetails`:
    - `fulfillableQuantity`
    - `inboundWorkingQuantity`, `inboundShippedQuantity`, and
      `inboundReceivingQuantity`
    - `reservedQuantity`: `totalReservedQuantity`,
      `pendingCustomerOrderQuantity`, `pendingTransshipmentQuantity`, and
      `fcProcessingQuantity`
    - `researchingQuantity`, `unfulfillableQuantity`, and
      `futureSupplyQuantity`
- **What counts as supply:**
  - **Sellable now:** `fulfillableQuantity`.
  - **Sellable soon:** `pendingTransshipmentQuantity` and
    `fcProcessingQuantity`.
  - **Not supply:** `pendingCustomerOrderQuantity`, which is already sold.
  - **Inbound:** only `shipped` and `receiving` units are really on the
    way. `working` units haven't left the seller yet.

Sandbox note: `execute` returns only the value of `return`, and `print()`
output is dropped. Convert values to plain dicts, lists, and strings before
returning them; `json.dumps(default=...)` can fail in the sandbox.

## Filtered inventory read

Page and filter **inside** one `execute`, and return counts plus matching
rows only. On a 500-SKU catalog this returns well under 5 KB, where the raw
pages would be several hundred KB. Change `keep()` to match the question.
The example keeps stocked SKUs that are low on stock or have units in
transit.

```python
await call_tool("set_active_identity", {"identity_id": SID})
MK = "ATVPDKIKX0DER"
LOW = 50                      # the question's threshold, set on the host
TOK = None                    # a carried next_token, to resume a large catalog
counts = {"skus": 0, "stocked": 0, "zero_stock": 0, "in_transit": 0}
rows, tok, pages = [], TOK, 0
def keep(sku, f, t):
    return f > 0 and (f < LOW or t > 0)
while pages < 45:             # 50 calls per block, and call 51 loses everything
    a = {"granularityType": "Marketplace", "granularityId": MK,
         "marketplaceIds": [MK], "details": True}
    if tok:
        a["nextToken"] = tok
    r = await call_tool("fba-inventory_getInventorySummaries", a)
    pl = r.get("payload") or r
    for s in pl.get("inventorySummaries", []):
        d = s.get("inventoryDetails") or {}
        f = d.get("fulfillableQuantity", 0)
        t = d.get("inboundShippedQuantity", 0) + d.get("inboundReceivingQuantity", 0)
        counts["skus"] += 1
        counts["stocked" if f > 0 else "zero_stock"] += 1
        if t > 0:
            counts["in_transit"] += 1
        if keep(s["sellerSku"], f, t):
            rows.append({"sku": s["sellerSku"], "fulfillable": f, "in_transit": t})
    pages += 1
    tok = (r.get("pagination") or pl.get("pagination") or {}).get("nextToken")
    if not tok:
        break
rows.sort(key=lambda x: x["fulfillable"])
return {"counts": counts, "matched": len(rows), "rows": rows[:25], "next_token": tok}
```

A `next_token` in the result means the catalog is bigger than one block
(45 pages, 2,250 SKUs). Pass it as `TOK` in the next block and add up the
counts. Without the page cap, a 98,000-SKU catalog hit the 50-call limit on
2026-10-18 and the block returned nothing.

## Sales: `getOrderMetrics` (instant)

```json
{"marketplaceIds": ["ATVPDKIKX0DER"],
 "interval": "2026-08-23T00:00:00-07:00--2026-09-22T00:00:00-07:00",
 "granularity": "Total", "sku": "FRO599S", "fulfillmentNetwork": "AFN"}
```

- **Required:** `marketplaceIds` (one marketplace), `interval`, and
  `granularity` (`Hour`, `Day`, `Week`, `Month`, `Year`, or `Total`).
  `granularityTimeZone` is required for Day and above, except `Total`.
- **Filtering:** pass `sku` or `asin`, never both. `fulfillmentNetwork: AFN`
  counts FBA orders only.
- **Response:** `payload[]` holds `interval`, `unitCount`, `orderItemCount`,
  `orderCount`, `averageUnitPrice`, and `totalSales`.
- **Call cost:** one call per SKU, with a low rate limit (about 0.5 per second,
  burst 15). Stay within about 20 SKUs per `execute`: after the burst of 15 it runs at about 2 seconds per call, so 20 SKUs keep a block near 30 seconds. Beyond about 40 stocked SKUs,
  the planning report is cheaper, because one file covers every SKU.
- **Interval:** use the last 30 *complete* days. Order data for the current
  day is partial.

## Reports: `GET_FBA_INVENTORY_PLANNING_DATA` (async, authoritative)

1. `reports_createReport`:
   `{"reportType": "GET_FBA_INVENTORY_PLANNING_DATA", "marketplaceIds": ["ATVPDKIKX0DER"]}`
   returns `{reportId}`. The rate limit is low (about 1 per minute, burst
   15), so don't re-request needlessly. A report from earlier today is still
   good; `reports_getReports` can find it.
2. `reports_getReport(reportId)`: poll across `execute` calls until
   `processingStatus` is `DONE`. In the live test it took under a minute.
   `FATAL` or `CANCELLED` means you fall back to the estimate.
3. `reports_getReportDocument(reportDocumentId)` returns `{url}`, a
   pre-signed S3 link that is valid for about 5 minutes. The file is
   uncompressed TSV with about 99 columns and one row per SKU.
4. Run `scripts/planning_report.py '<url>'` from the host (the sandbox has no
   network), single-quoted, with the `url` from step 3 of this run and no
   other. It returns JSON.

Columns the script uses:

| Column | Meaning |
|---|---|
| `available` | Sellable units |
| `units-shipped-t7`, `units-shipped-t30` | Recent velocity |
| `days-of-supply` | Amazon's forecast-based days of supply for on-hand stock |
| `Total Days of Supply (including units from open shipments)` | The same, counting inbound |
| `Recommended ship-in quantity` / `Recommended ship-in date` | Amazon's replenishment recommendation |
| `inbound-quantity`, `inbound-working`, `inbound-shipped`, `inbound-received` | Inbound units by stage |
| `fc-transfer` (docs call it `Reserved FC Transfer`), `Reserved FC Processing` | Units moving between FCs |
| `fba-inventory-level-health-status`, `alert` | Amazon's health flags |
| `Low-Inventory-Level fee applied in current week?` | Fee exposure |

Amazon's documented column names and the live headers don't always match,
and Amazon adds columns over time. The script accepts aliases and reports
`missing_columns` instead of failing.

## Estimate vs Amazon's numbers

A live comparison on 2026-09-24:

| SKU | Trailing estimate (fulfillable ÷ t30/30) | Amazon `days-of-supply` |
|---|---|---|
| A | 30.2 | 39, plus a ship-in recommendation of 431 units by Oct 1 |
| B | 34.4 | 57 |
| C | 111.2 | 93 |

Amazon's figure is forecast-based, so it accounts for trend and seasonality,
and the gap to the trailing estimate is large. Always name the source you
used. Never mix the two in one ranking without labelling each row.

## Restock report (fallback)

`GET_RESTOCK_INVENTORY_RECOMMENDATIONS_REPORT` has the same core fields:

- `Days of Supply at Amazon Fulfillment Network`
- `Total Days of Supply…`
- `Recommended replenishment qty` and `Recommended ship date`
- `Alert`

Use it only if the planning report is unavailable. The script targets the
planning report's columns.
