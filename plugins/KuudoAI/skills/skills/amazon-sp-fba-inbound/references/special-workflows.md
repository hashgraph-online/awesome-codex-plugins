# Special workflows

Detect the variant before creating the plan. Each one changes the order of
the pipeline in SKILL.md.

## Pack Later (box contents unknown at plan creation)

**When to use it:** the seller doesn't yet know what goes in which box.
Placement is chosen first, and packing information is set per shipment
afterwards. This flow is available **only for pallet deliveries** (LTL/FTL),
with a partnered carrier or the seller's own. Small parcel is not offered.

**Order:**

1. Run `createInboundPlan`.
2. Run `generatePlacementOptions`, then `listPlacementOptions`. Only one
   placement option can be confirmed.
3. Hard gate, then `confirmPlacementOption`.
4. Run `setPackingInformation` keyed by **`shipmentId`**, not
   `packingGroupId`. Provide boxes for every shipment. Box data can't be
   discarded, so show the boxes per shipment and get a yes before the call.
   Any `contentInformationSource` is allowed:
   - `BOX_CONTENT_PROVIDED`: include `items`.
   - `BARCODE_2D`: leave `items` empty. The seller prints 2D box-content
     barcodes.
   - `MANUAL_PROCESS`: leave `items` empty. Amazon enters the contents and
     charges a manual-processing fee. **This is a hard gate**, like the
     others in SKILL.md section 4:
     - Present the fee: a per-unit fee under Amazon's current schedule. The
       API doesn't return the amount beforehand, so don't invent one.
     - Offer the fee-free options, `BARCODE_2D` or `BOX_CONTENT_PROVIDED`.
     - Call `setPackingInformation` only after the seller types `CONFIRM`.
5. Run `generateTransportationOptions` with pallets, freight info and
   contact, then `listTransportationOptions`.
6. Own carrier only: generate, list, and confirm the delivery window.
7. Hard gate, then `confirmTransportationOptions`.
8. Get labels (v0 `getLabels`) and the bill of lading for partnered pallets.
   For own carrier, add tracking.

Note: once placement is confirmed, the Send to Amazon UI cannot accept this
packing information. The seller must finish through the API.

Tell the seller: "This is the Pack Later flow. It's pallet shipments only.
We'll lock placement first, then enter the boxes for each shipment."

## India (`A21TJRUUN4KGV`)

The India identity routes through the **EU** endpoint. Differences from the
pack-first flow:

- **Compliance first.** Run `listItemComplianceDetails` for the MSKUs. If tax
  details are missing, collect them and run `updateItemComplianceDetails`,
  one MSKU per call. It is async and is set once per SKU, so show each
  MSKU's values and get a yes before its call. The tax details are:
  - `declaredValue`
  - `hsnCode`
  - GST and cess `taxRates`
- **Packing options.** Amazon's India guide leaves out
  `generatePackingOptions` and `confirmPackingOption`. Follow the guide.
- **Custom placement.** `generatePlacementOptions` can take
  `customPlacement[{warehouseId, items}]` when the seller names FCs.
- **Packing before placement confirmation.** Set packing information for
  **all** shipments before `confirmPlacementOption`.
- **Partnered shipments.** Use `getDeliveryChallanDocument` to get the
  delivery challan.
- **Self-ship drop-off.** See below.

Heads-up: Amazon's FAQ still lists India API support as "to be announced",
while the India guide documents the flow. If a call is rejected as
unsupported, report the error and point the seller to Send to Amazon.

## Self-ship appointments (IN, MX, BR, EG, SA, AE)

These apply to own-carrier drop-offs at FCs in these marketplaces.

1. `getShipment` must show an `amazonReferenceId`. Without one, appointments
   can't be booked yet.
2. Run `generateSelfShipAppointmentSlots`. The desired start and end dates
   are optional; the default is the next 42 days. Then run
   `getSelfShipAppointmentSlots`.
3. The seller picks a slot from the ones you showed; that pick is the yes.
   Then run `scheduleSelfShipAppointment`. Rescheduling uses the same call
   with a `reasonComment`; show the old and new slot first and get a yes.
4. `cancelSelfShipAppointment` takes an optional `reasonComment` from the
   ReasonComment enum. It gives up the booked slot, so it gets its own ask:
   show the shipment, the slot, and the reason, and wait for a yes.

## Changing contents after transportation is confirmed

Use this when quantities change before the shipment reaches RECEIVING.

1. Run `generateShipmentContentUpdatePreviews` with the **complete** new
   `boxes[]` and `items[]`.
   - Change each SKU by at most ±5% or 6 units, whichever is greater.
   - A shipment cannot be emptied.
2. Run `listShipmentContentUpdatePreviews` or
   `getShipmentContentUpdatePreview`. It shows the item changes and the
   transportation cost impact, and the preview has an `expiration`.
3. Show the cost change. Hard gate, then
   `confirmShipmentContentUpdatePreview`.

## Plans created in Send to Amazon

Once placement and transportation are confirmed, their plans can be read
through `listInboundPlans` and the GET operations. Before that point, they
are invisible to the API. Anything the API generated is discarded if the
seller switches to the Send to Amazon UI mid-flow.
