# Inbound gap: will stock land before the SKU runs out?

Inventory already tells you **how many** units are on the way for each SKU
(`inboundShippedQuantity`, `inboundReceivingQuantity`). This file covers
**when** they arrive. Run it only for OUT_OF_STOCK, CRITICAL, and WARNING SKUs
that have shipped or receiving units.

## Batch every flagged SKU into one pass

Cost should scale with the number of **plans**, not SKUs. A 500-SKU catalog
can flag 50+ SKUs, and searching plans once per SKU repeats the same calls
50 times. Instead:

1. Put every flagged SKU with in-transit units into one `wanted` set.
2. Walk recent SHIPPED plans, then ACTIVE plans, once each. Call
   `listInboundPlanItems` per plan and record any item whose `msku` is in
   `wanted`.
3. Call `getInboundPlan`, `listShipmentItems`, and `getShipment` only for
   the plans that matched.
4. Stop when every wanted SKU's in-transit units are covered, or when the
   plans are older than 90 days.

With about 40 calls per `execute` (there's also a 30-second limit), carry the `paginationToken`, the position in
the current page, and the partial map between blocks.

**Carry state as a JSON string.** Pass it into the next block as
`st = json.loads('<json>')`. Pasting JSON straight into Python breaks on
`null`, `true`, and `false`.

**Measured live on 2026-09-24** (a 251-SKU catalog, 32 SKUs with 1,905
in-transit units):

- 3 blocks, 98 calls, and about 60 seconds
- 89 SHIPPED plans scanned, 69 matched
- all 32 SKUs covered without reaching ACTIVE plans

Searching per SKU would have repeated that 89-plan scan 32 times.

Reading arrival windows (`getShipment`) costs one call per matched shipment.
Fetch them only for the SKUs you actually flag, and take the earliest
window, instead of dating every matched plan.

## Finding the shipments that hold a SKU

`listInboundPlans` returns plan summaries only: no SKUs and no dates. A real
account can hold hundreds of stale ACTIVE drafts, so narrow the search:

1. **List plans, SHIPPED first.** When a plan's shipments leave, the plan's
   status moves from ACTIVE to **SHIPPED**, so in-transit stock sits in
   SHIPPED plans. ACTIVE plans hold `READY_TO_SHIP` shipments, plus many
   stale drafts.

   A live check on 2026-09-24:
   - A SKU's 990 in-transit units were split across SHIPPED plans:
     `IN_TRANSIT`, `SHIPPED`, `RECEIVING`, and `CHECKED_IN` shipments.
   - All ten ACTIVE plans containing that SKU were unshipped July drafts.

   Call `fba-inbound_listInboundPlans` with
   `{"status": "SHIPPED", "sortBy": "LAST_UPDATED_TIME", "sortOrder":
   "DESC", "pageSize": 30}` (30 is the maximum), then repeat with `"status": "ACTIVE"`. To page,
   pass the response's `pagination.nextToken` as the request's
   **`paginationToken`**. Stop once the matched shipment quantities account
   for the SKU's `inboundShipped` plus `inboundReceiving` units.

   In a live smoke test, covering 990 in-transit units took 2 pages and 41
   calls. Plan-level quantities can exceed the in-transit total (1,260
   matched vs 990), because plans also count shipments that were already
   received. Judge what's still coming by each **shipment's** status, not
   by the plan's total.

   **Stop early.** You don't need every shipment, only the arrival dates
   that decide the gap. Once the matched `SHIPPED` and `IN_TRANSIT`
   shipments cover the in-transit units, stop and use the earliest window.
   One live run traced all 13 matching plans and spent about 82 calls; half
   that would have given the same answer.
2. **Find plans that hold the SKU.** The cheapest way is
   `listInboundPlanItems(inboundPlanId)`, one call per plan: match on `msku`,
   then open only the matching plans with `getInboundPlan`. Cover plans
   updated in the last 90 days, about 40 or fewer fast calls per `execute` (30-second limit). Skip this
   entirely if inventory shows no inbound units.
   - A 400 saying "not supported for Amazon Warehousing and Distribution"
     means an AWD plan. Skip it.
   - Keep shipments whose status is `READY_TO_SHIP`, `SHIPPED`, `IN_TRANSIT`,
     `DELIVERED`, `CHECKED_IN`, or `RECEIVING`.
3. **Match the SKU.** For each kept shipment, call
   `listShipmentItems(inboundPlanId, shipmentId)` and match on `msku`.
   Record the quantity.
4. **Find the arrival date.** `getShipment(inboundPlanId, shipmentId)`
   provides it:
   - `selectedDeliveryWindow.startDate` / `endDate` is the confirmed arrival
     window. Own-carrier shipments always have one.
   - `status`: `RECEIVING` means the units are at the FC but not sellable
     yet, which usually means days, not weeks.
   - If there's no window, say the arrival date is unknown. Don't estimate
     one.

Summarize inside the sandbox: SKU, shipment name or FBA ID, units, status, and
window. Don't return raw items.

## Computing the gap

```
stockout_date   = snapshot_date + days_of_cover          (Amazon's DOS, else the estimate)
arrival_start   = earliest selectedDeliveryWindow.startDate among its shipments
gap_days        = arrival_start - stockout_date
```

- **`gap_days > 0`:** the SKU runs out about `gap_days` before stock lands.
  Say so plainly, with dates.
- **`gap_days <= 0`:** stock should land in time. Say so; it isn't a risk.
- **Several shipments:** use the earliest window, and note whether that
  shipment alone covers demand until the next one lands.
- **`READY_TO_SHIP`:** the shipment hasn't left. Its window is a plan, not a
  promise. Flag it: "not yet shipped; the window assumes it leaves on time".

## Edge cases

- **OUT_OF_STOCK SKUs:** the stockout is now. The gap is simply the days
  until `arrival_start`.
- **Inbound units but no matching shipment in the 90-day window:** say that
  some inbound units couldn't be traced to a dated shipment, and offer to
  look further back.
- **Send to Amazon plans:** they're readable once placement and
  transportation are confirmed. Earlier drafts are invisible to the API.
- **Changing shipments:** creating a shipment, moving a delivery window, or
  adding units is outside this skill. Hand off to `amazon-sp-fba-inbound`.
