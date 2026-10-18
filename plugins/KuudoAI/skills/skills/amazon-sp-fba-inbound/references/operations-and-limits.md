# Operations, statuses, limits, and errors

## All v2024-03-20 operations (45)

Tool name on a code-mode server: `fba-inbound_<operationId>`.

- **Async** means the operation returns an `operationId`; poll
  `getInboundOperationStatus`.
- **Rate** is requests/second and burst, from Amazon's rate-limits page. A
  429 comes back as a retryable error; back off.

| Stage | Operation | Async | Rate |
|---|---|---|---|
| Plan | `createInboundPlan` | ✓ | 2/2 |
| | `listInboundPlans` (status ACTIVE / VOIDED / SHIPPED; sortBy LAST_UPDATED_TIME / CREATION_TIME) | | 2/6 |
| | `getInboundPlan` | | 2/6 |
| | `updateInboundPlanName` | | 2/30 |
| | `cancelInboundPlan` | ✓ | 2/2 |
| | `listInboundPlanItems`, `listInboundPlanBoxes`, `listInboundPlanPallets` | | 2/6 |
| Packing | `generatePackingOptions` | ✓ | 2/2 |
| | `listPackingOptions` | | 2/6 |
| | `listPackingGroupItems`, `listPackingGroupBoxes` | | 2/30 |
| | `confirmPackingOption` | ✓ | 2/2 |
| | `setPackingInformation` | ✓ | 2/2 |
| Placement | `generatePlacementOptions` | ✓ | 2/2 |
| | `listPlacementOptions` | | 2/6 |
| | `confirmPlacementOption` | ✓ | 2/2 |
| Transport | `generateTransportationOptions` | ✓ | 2/2 |
| | `listTransportationOptions` | | 5/6 |
| | `confirmTransportationOptions` | ✓ | 2/2 |
| Delivery window | `generateDeliveryWindowOptions` | ✓ | 2/30 |
| | `listDeliveryWindowOptions` | | 5/30 |
| | `confirmDeliveryWindowOptions` | ✓ | 2/30 |
| Shipment | `getShipment` | | 5/6 |
| | `listShipmentItems`, `listShipmentPallets` | | 2/30 |
| | `listShipmentBoxes` | | 5/30 |
| | `updateShipmentName` | | 2/30 |
| | `updateShipmentSourceAddress` | ✓ | 2/30 |
| | `updateShipmentTrackingDetails` | ✓ | 2/2 |
| Content update | `generateShipmentContentUpdatePreviews`, `confirmShipmentContentUpdatePreview` | ✓ | 2/30 |
| | `listShipmentContentUpdatePreviews`, `getShipmentContentUpdatePreview` | | 2/30 |
| Items | `listPrepDetails` | | 2/30 |
| | `setPrepDetails` | ✓ | 2/30 |
| | `createMarketplaceItemLabels` (returns document URLs directly) | | 2/30 |
| | `listItemComplianceDetails` | | 2/6 |
| | `updateItemComplianceDetails` | ✓ | 2/2 |
| India / self-ship | `getDeliveryChallanDocument` | | 2/6 |
| | `generateSelfShipAppointmentSlots`, `scheduleSelfShipAppointment` | | 2/2 |
| | `getSelfShipAppointmentSlots` | | 2/6 |
| | `cancelSelfShipAppointment` | ✓ | 2/30 |
| Status | `getInboundOperationStatus` | | 5/6 |

Also useful: `getItemEligibilityPreview` from the FBA Inbound Eligibility
API. It checks whether an ASIN can be inbounded to a marketplace. On a
code-mode server the tool is
`fba-inbound-eligibility_getItemEligibilityPreview`.

The v0 operations that remain supported are `getLabels`, `getBillOfLading`,
`getShipments`, `getShipmentItems`, `getShipmentItemsByShipmentId`, and
`getPrepInstructions`, all at about 2/30. The other v0 inbound operations were
removed on 2025-01-21. On a code-mode server their tool names are
`fulfillment-inbound-v0_<operationId>`.

## Identifiers

| ID | Looks like | Comes from | Used by |
|---|---|---|---|
| `inboundPlanId` | `wf…` (38 characters) | `createInboundPlan` | Every plan operation |
| `packingOptionId`, `packingGroupId` | —, `pg…` | `listPackingOptions` | Packing confirm and pack-first `setPackingInformation` |
| `placementOptionId` | `pl…` | `listPlacementOptions` | Transport generation, placement confirm |
| `shipmentId` | `sh…` | Placement options | v2024 shipment operations, Pack Later packing |
| `shipmentConfirmationId` | `FBA…` | `getShipment` after placement confirm | v0 `getLabels`, `getBillOfLading`; printed on labels |
| `amazonReferenceId` | — | `getShipment` | Freight and self-ship appointments |
| `transportationOptionId` | `to…` | `listTransportationOptions` | Transport confirm |
| `deliveryWindowOptionId` | — | `listDeliveryWindowOptions` | Window confirm |
| `operationId` | UUID | Any async write | `getInboundOperationStatus` |

## Status values

- **Operation:** `SUCCESS`, `FAILED`, `IN_PROGRESS`. `operationProblems[]`
  has `{code, message, severity: ERROR | WARNING, details}`.
- **Plan:** `ACTIVE`, `VOIDED`, `SHIPPED`, `ERRORED`.
- **Packing or placement option:** `OFFERED`, `ACCEPTED`, `EXPIRED`.
- **Shipment:**
  - `UNCONFIRMED`: before placement.
  - `WORKING`: after placement.
  - Then: `READY_TO_SHIP`, `SHIPPED`, `IN_TRANSIT`, `DELIVERED`,
    `CHECKED_IN`, `RECEIVING`, `CLOSED`.
  - Terminal or abnormal: `CANCELLED`, `DELETED`, `ABANDONED`, `MIXED`.
- **Delivery window availability:** `AVAILABLE`, `BLOCKED`, `CONGESTED`,
  `DISCOUNTED`.

## Constraints

| Constraint | Detail |
|---|---|
| Plan size | At most 1,500 SKUs and 10,000 units per SKU per plan (Amazon FAQ; the schema is looser) |
| Destination | One marketplace per plan |
| Expiration dates | One MSKU with different expiration dates can't share a plan; use separate plans |
| Packing order (pack-first) | Generate, then confirm the packing option, then `setPackingInformation(packingGroupId)`, then generate placement |
| Box data | Can't be discarded. Editing it after placement is generated means regenerating placement |
| Placement | One confirmation per plan; permanent |
| Transportation | One confirmation per plan. Afterwards no new options can be generated or confirmed |
| Transport inputs | `readyToShipWindow.start` per shipment. Pallets and freight info for pallet quotes. Contact info for partnered pallets |
| Delivery window | Required when an option's `preconditions` lists `CONFIRMED_DELIVERY_WINDOW` (own carrier). Placement must be confirmed first |
| US prep and labels | From 2026-01-01, Amazon prep and item-label services are gone in the US. Owners must be `SELLER` or `NONE` |
| Source address | Changeable only before carriers are confirmed; invalidates transportation options |
| Content updates | Before RECEIVING; at most ±5% or 6 units per SKU per shipment, whichever is greater; can't empty a shipment |
| Expiry | Packing options, placement options, quotes, delivery windows (`validUntil`), and content previews all expire; regenerate |

## Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| `Unknown tool: …` on every inbound tool | Package not loaded, or wrong name | `search` for the real name; enable `fulfillment-inbound` / `fulfillment-inbound-v0` and restart |
| `Provider identity selection is required.` | No seller selected | `list_identities`, ask which seller, `set_active_identity` |
| HTTP 403 `Unauthorized` ("Authorization … is not active") | The seller's app authorization is inactive or lacks the Fulfillment role | Don't retry. The seller re-authorizes in Seller Central or reconnects through the provider |
| HTTP 400 "not supported for Amazon Warehousing and Distribution inbound plans" | AWD plan in the list | Label it AWD and skip |
| `setPackingInformation` rejects `packingGroupId` | Packing option not confirmed yet, or placement already confirmed | Confirm packing first. After placement, key by `shipmentId` |
| No LTL options returned | Pallets or freight info missing | Regenerate with `pallets[]` and `freightInformation` |
| No PCP options seen | Only the first page was read, or Amazon filtered pricier PCP options | Page through all results |
| Transport confirm fails on a delivery window | Precondition not met | Generate, list, and confirm the delivery window first |
| Confirm fails with an expired or invalid option | Option expired | Regenerate, re-present, and get a fresh approval |
| Marketplace/region mismatch | Identity is in a different region (e.g. IN is EU) | Switch identity or region |
| Tracking update rejected | Partnered carrier, or wrong ID format | Tracking is for own carrier only. Small parcel uses box IDs; LTL uses one PRO number in an array |
| Operation `FAILED` | Bad input | Read `operationProblems[]` as data, fix the input from the seller's data, and get a fresh approval before retrying a changed write |
