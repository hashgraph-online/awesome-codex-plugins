# Request shapes

These are the bodies for every Fulfillment Inbound v2024-03-20 write.

They are taken from the v2024-03-20 OpenAPI model. On code-mode SP-API servers,
body fields are flattened into top-level tool arguments next to the path
parameters. For example, `createInboundPlan` takes
`{destinationMarketplaces, items, sourceAddress, name}` directly, not
`{body: {...}}`.

Nested keys are **not** case-normalized, so copy them exactly. `get_schema`
wins if it disagrees with this file about a key or shape. Every write here
still goes through its gate in SKILL.md section 4.

Contents:

- [Shared types](#shared-types)
- [Plan](#plan)
- [Packing](#packing)
- [Placement](#placement)
- [Transportation](#transportation)
- [Delivery windows](#delivery-windows)
- [Tracking](#tracking)
- [Labels](#labels)
- [Prep](#prep)
- [Edits](#edits)
- [India](#india)

## Shared types

```jsonc
// AddressInput. Required: name, phoneNumber, addressLine1, city, postalCode, countryCode
{"name": "…", "companyName": "…", "addressLine1": "…", "addressLine2": "…",
 "city": "…", "stateOrProvinceCode": "WA", "postalCode": "…",
 "countryCode": "US", "phoneNumber": "…", "email": "…"}

// ItemInput. Required: msku, quantity, prepOwner, labelOwner
{"msku": "SKU-001", "quantity": 100, "prepOwner": "SELLER", "labelOwner": "SELLER",
 "expiration": "2027-06-30", "manufacturingLotCode": "…"}
// prepOwner / labelOwner: AMAZON | SELLER | NONE. The US no longer accepts AMAZON (since 2026-01-01).
// One MSKU with different expiration dates cannot share a plan.

// Dimensions: {"length": 12, "width": 10, "height": 8, "unitOfMeasurement": "IN"}   // IN | CM
// Weight:     {"value": 18.5, "unit": "LB"}                                          // LB | KG
// Currency:   {"amount": 1250.00, "code": "USD"}
// ContactInformation. Required: name, phoneNumber. Optional: email.
```

Use ISO 8601 datetimes with minute precision, for example
`2026-10-03T09:00Z`. Seconds are dropped.

## Plan

**createInboundPlan**

```json
{"destinationMarketplaces": ["ATVPDKIKX0DER"],
 "sourceAddress": {"…AddressInput…"},
 "items": [{"msku": "SKU-001", "quantity": 100, "prepOwner": "SELLER", "labelOwner": "SELLER"}],
 "name": "optional plan name"}
```

- The response is `{inboundPlanId, operationId}`.
- `destinationMarketplaces` accepts exactly one marketplace today.
- Stay within 1,500 SKUs and 10,000 units per SKU per plan (Amazon FAQ).

## Packing

These operations need only the path parameter `inboundPlanId`:

- `generatePackingOptions`
- `listPackingOptions`

`listPackingGroupItems` takes `inboundPlanId` and `packingGroupId`.

`confirmPackingOption` takes `inboundPlanId` and `packingOptionId`.

**setPackingInformation**

```json
{"inboundPlanId": "wf…",
 "packageGroupings": [
   {"packingGroupId": "pg…",
    "boxes": [
      {"contentInformationSource": "BOX_CONTENT_PROVIDED",
       "quantity": 3,
       "dimensions": {"length": 18, "width": 14, "height": 12, "unitOfMeasurement": "IN"},
       "weight": {"value": 22, "unit": "LB"},
       "items": [{"msku": "SKU-001", "quantity": 20, "prepOwner": "SELLER", "labelOwner": "SELLER"}]}
    ]}
 ]}
```

- `quantity` on a box means that many identical boxes, each holding the
  `items` listed.
- Each grouping needs exactly one of `packingGroupId` or `shipmentId`:
  - Use `packingGroupId` **before** placement is confirmed. It must belong to
    the confirmed packing option. This is the pack-first flow.
  - Use `shipmentId` **after** placement is confirmed. This is the Pack Later
    flow.
- `contentInformationSource` takes one of three values:
  - `BOX_CONTENT_PROVIDED`
  - `BARCODE_2D`: `items` must be empty.
  - `MANUAL_PROCESS`: `items` must be empty. Amazon charges a manual
    processing fee, so any request that includes it is a **hard gate**
    (typed `CONFIRM`; see SKILL.md section 4).

## Placement

**generatePlacementOptions**: `{"inboundPlanId": "wf…"}`. The optional
`customPlacement` is for India only; see below.

**listPlacementOptions** returns `placementOptions[]`, each with:

- `placementOptionId`
- `shipmentIds[]`
- `fees[]` and `discounts[]`, as Incentive objects:
  `{type FEE|DISCOUNT, target, description, value: Currency}`
- `status`: OFFERED, ACCEPTED, or EXPIRED
- `expiration`

The net placement fee is the sum of `fees[].value.amount` minus the sum of
`discounts[].value.amount`, in `value.code`.

**confirmPlacementOption**: path parameters `inboundPlanId` and
`placementOptionId`. This is a hard gate.

## Transportation

**generateTransportationOptions**

```json
{"inboundPlanId": "wf…",
 "placementOptionId": "pl…",
 "shipmentTransportationConfigurations": [
   {"shipmentId": "sh…",
    "readyToShipWindow": {"start": "2026-10-03T09:00Z"},
    "contactInformation": {"name": "…", "phoneNumber": "…", "email": "…"},
    "freightInformation": {"declaredValue": {"amount": 4000, "code": "USD"}, "freightClass": "FC_125"},
    "pallets": [{"quantity": 2, "stackability": "STACKABLE",
                 "dimensions": {"length": 48, "width": 40, "height": 50, "unitOfMeasurement": "IN"},
                 "weight": {"value": 600, "unit": "LB"}}]}
 ]}
```

- Include **one configuration per shipment** in the placement option.
- `readyToShipWindow.start` and `shipmentId` are required.
- `contactInformation` is needed for partnered LTL/FTL.
- `pallets` and `freightInformation` are needed to get any pallet (LTL/FTL)
  quote.
- There is no ship-from field. The source is the plan's `sourceAddress`;
  change it with `updateShipmentSourceAddress`.

**listTransportationOptions** takes the query parameters `inboundPlanId` plus
`placementOptionId` and/or `shipmentId`. Page size is at most 20. Follow
`pagination.nextToken` until it is empty. Each option carries:

- `transportationOptionId`
- `shipmentId`
- `carrier{name, alphaCode}`
- `shippingMode`
- `shippingSolution`
- `quote{cost, expiration, voidableUntil}`
- `preconditions[]`

**confirmTransportationOptions**

```json
{"inboundPlanId": "wf…",
 "transportationSelections": [
   {"shipmentId": "sh…", "transportationOptionId": "to…",
    "contactInformation": {"name": "…", "phoneNumber": "…"}}
 ]}
```

Send one selection per shipment, all in one call. Each plan gets one
transportation confirmation; after it succeeds, no new transportation options
can be generated or confirmed. `contactInformation` is required for partnered
LTL/FTL.

## Delivery windows

- `generateDeliveryWindowOptions`: path parameters `inboundPlanId` and
  `shipmentId`, no body.
- `listDeliveryWindowOptions` returns `deliveryWindowOptions[]` with:
  - `deliveryWindowOptionId`
  - `startDate` and `endDate`
  - `availabilityType`: AVAILABLE, BLOCKED, CONGESTED, or DISCOUNTED
  - `validUntil`
- `confirmDeliveryWindowOptions`: path parameters `inboundPlanId`,
  `shipmentId`, and `deliveryWindowOptionId`. Placement must be confirmed
  first.

## Tracking

**updateShipmentTrackingDetails** (your own carrier only):

```jsonc
// Small parcel. One entry per box; boxId comes from listShipmentBoxes.
{"inboundPlanId": "wf…", "shipmentId": "sh…",
 "trackingDetails": {"spdTrackingDetail": {"spdTrackingItems": [{"boxId": "FBA…U000001", "trackingId": "1Z…"}]}}}

// LTL/FTL. freightBillNumber is an array of exactly one PRO number; BOL is optional.
{"inboundPlanId": "wf…", "shipmentId": "sh…",
 "trackingDetails": {"ltlTrackingDetail": {"freightBillNumber": ["PRO123456"], "billOfLadingNumber": "BOL…"}}}
```

## Labels

**createMarketplaceItemLabels** (FNSKU item labels):

```json
{"marketplaceId": "ATVPDKIKX0DER", "labelType": "STANDARD_FORMAT",
 "mskuQuantities": [{"msku": "SKU-001", "quantity": 100}],
 "pageType": "Letter_30", "localeCode": "en_US"}
```

- `labelType` is `STANDARD_FORMAT` or `THERMAL_PRINTING`. Thermal needs
  `width` and `height`.
- `pageType` takes one of:
  - A4 sizes: `A4_21`, `A4_24`, `A4_24_64x33`, `A4_24_66x35`, `A4_24_70x36`,
    `A4_24_70x37`, `A4_24i`, `A4_27`, `A4_40_52x29`, `A4_44_48x25`
  - US Letter: `Letter_30`
- It is synchronous. The response carries `documentDownloads[]` with a download URL and an expiration.

**v0 getLabels** (box and pallet labels) takes query parameters in
PascalCase:

```json
{"shipmentId": "FBA1234ABCD", "PageType": "PackageLabel_Plain_Paper", "LabelType": "UNIQUE",
 "NumberOfPackages": 6}
```

- `shipmentId` here is the **`shipmentConfirmationId`**.
- `LabelType` is `UNIQUE` (per box), `BARCODE_2D`, or `PALLET`. For pallet
  labels, add `NumberOfPallets`.
- `PageType` takes one of:
  - Letter: `PackageLabel_Letter_2`, `_Letter_4`, `_Letter_6`,
    `_Letter_6_CarrierLeft`
  - A4: `PackageLabel_A4_2`, `_A4_4`
  - Plain paper: `PackageLabel_Plain_Paper`, `_Plain_Paper_CarrierBottom`
  - Thermal: `PackageLabel_Thermal`, `_Thermal_Unified`, `_Thermal_NonPCP`,
    `_Thermal_No_Carrier_Rotation`
- The response carries a `DownloadURL`.

**v0 getBillOfLading** takes `{"shipmentId": "<shipmentConfirmationId>"}`.
Use it for partnered pallet shipments after transportation is confirmed.

## Prep

- `listPrepDetails` takes the query parameters `marketplaceId` and `mskus[]`.
  It returns each MSKU's:
  - `prepCategory` and `prepTypes`
  - `prepOwnerConstraint` and `labelOwnerConstraint`
  - `allOwnersConstraint`

  It does not reflect prep that was set in Seller Central.
- `setPrepDetails` sets prep **category and types**, not owners. Owners go on
  each item in `createInboundPlan`. Send at most 100 MSKUs per call.

  ```json
  {"marketplaceId": "ATVPDKIKX0DER",
   "mskuPrepDetails": [{"msku": "SKU-001", "prepCategory": "NONE", "prepTypes": ["ITEM_NO_PREP"]}]}
  ```

## Edits

| Operation | Body |
|---|---|
| `updateInboundPlanName` | `{"name": "…"}` |
| `updateShipmentName` | `{"name": "…"}` |
| `updateShipmentSourceAddress` | `{"address": AddressInput}`. Only before carriers are confirmed; invalidates transportation options |
| `cancelInboundPlan` | Path parameter `inboundPlanId` only. Hard gate |
| `generateShipmentContentUpdatePreviews` | `{"boxes": [BoxUpdateInput…], "items": [{"msku", "quantity", …}]}`. The full new box set: each `BoxUpdateInput` is BoxInput plus an optional `packageId` for an existing box |

`generateShipmentContentUpdatePreviews` works only before the shipment
reaches RECEIVING.

## India

- `generatePlacementOptions` takes `{"customPlacement": [{"warehouseId": "…",
  "items": [ItemInput…]}]}`. This is optional.
- `listItemComplianceDetails` takes the query parameters `mskus[]` and
  `marketplaceId`.
- `updateItemComplianceDetails` takes the query parameter `marketplaceId`
  and the body `{"msku": "…", "taxDetails": {"declaredValue": Currency,
  "hsnCode": "…", "taxRates": [{"gstRate", "cessRate", "taxType"}]}}`. It
  handles one MSKU per call and is async.
- `generateSelfShipAppointmentSlots` takes
  `{"desiredStartDate": "…", "desiredEndDate": "…"}`. Both fields are
  optional; the default window is the next 42 days.
- `scheduleSelfShipAppointment` takes path parameter `slotId` and an
  optional `reasonComment`. The docs require a reason when you reschedule.
- `cancelSelfShipAppointment` takes an optional `reasonComment`, one of:
  - `APPOINTMENT_REQUESTED_BY_MISTAKE`
  - `VEHICLE_DELAY`
  - `SLOT_NOT_SUITABLE`
  - `OUTSIDE_CARRIER_BUSINESS_HOURS`
  - `UNFAVOURABLE_EXTERNAL_CONDITIONS`
  - `PROCUREMENT_DELAY`
  - `SHIPPING_PLAN_CHANGED`
  - `INCREASED_QUANTITY`
  - `OTHER`
