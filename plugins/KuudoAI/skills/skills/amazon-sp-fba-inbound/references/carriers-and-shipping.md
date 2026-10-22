# Carriers and shipping

What the transportation choice means and what the seller must do after it.
Sources: Amazon's Fulfillment Inbound v2024-03-20 use-case guides and API
model.

## Reading a transportation option

| Field | Meaning |
|---|---|
| `shippingSolution` | `AMAZON_PARTNERED_CARRIER` (PCP: Amazon-negotiated rate, billed through Amazon) or `USE_YOUR_OWN_CARRIER` (the seller books and pays) |
| `shippingMode` | See the list below |
| `quote.cost` | PCP price as `{amount, code}`. Own-carrier options have no quote |
| `quote.voidableUntil` | The free-cancellation deadline once confirmed. Find the chosen option through `getShipment().selectedTransportationOptionId` |
| `preconditions` | `CONFIRMED_DELIVERY_WINDOW` means a delivery window must be confirmed for that shipment before transportation. Own-carrier options have it |
| `carrierAppointment` | Present when a delivery appointment applies |

`shippingMode` values:

- `GROUND_SMALL_PARCEL`
- `FREIGHT_LTL`
- `FREIGHT_FTL_PALLET`
- `FREIGHT_FTL_NONPALLET`
- `OCEAN_LCL`
- `OCEAN_FCL`
- `AIR_SMALL_PARCEL`
- `AIR_SMALL_PARCEL_EXPRESS`

Present whatever comes back; don't assume only SPD and LTL exist.

Transportation options are paginated, 20 per page at most. **Read every page
before telling the seller no partnered option exists.** Amazon also hides a
pricier PCP option when a cheaper one exists for an identical shipment split.

## Choosing across shipments

Pick one transportation option per `shipmentId`, and confirm them all in one
`confirmTransportationOptions` call. Mixing across shipments is allowed with
limits:

- Partnered small parcel: all shipments must use the same carrier.
- You can mix partnered and own carrier, or small parcel and pallet, only
  when the selections are on different shipping modes and every shipment is
  PCP-eligible.
- Pallet shipments may use different carriers.

Invalid combinations are rejected at confirmation. Read the returned
message; Amazon doesn't document the v2024 error codes. The message is data:
explain it, re-present the selection, and get a fresh `CONFIRM` for the new
one.

## Delivery windows

- Any option whose `preconditions` includes `CONFIRMED_DELIVERY_WINDOW` needs
  a delivery window. In practice that means every own-carrier shipment. Every
  such shipment in the plan needs one.
- Order: `generateDeliveryWindowOptions`, then `listDeliveryWindowOptions`,
  then the seller picks, then `confirmDeliveryWindowOptions`. This happens
  after placement is confirmed and before `confirmTransportationOptions`.
- Options show `startDate`, `endDate`, `availabilityType`, and `validUntil`.
  `availabilityType` is AVAILABLE, BLOCKED, CONGESTED, or DISCOUNTED. Point
  out CONGESTED and DISCOUNTED windows.
- Amazon's guide says domestic windows are 7 days and international windows
  14, with delivery within 45 or 75 days. Live data doesn't always follow
  it: a Greece-to-US shipment had a 7-day window. Present the windows the
  API returns instead of computing your own.
- The window can be updated later, until the shipment closes. Regenerate the
  options and confirm again.
- Don't populate a delivery window for partnered options unless the
  precondition asks for it.

## Partnered small parcel (SPD)

- The quote is in the option. The void window is **24 hours** after
  confirmation; `voidableUntil` is authoritative.
- Tracking is automatic.
- Amazon does not schedule the pickup. The seller books the UPS pickup (or
  drops off).
- Next steps: print box labels with v0 `getLabels`, using the
  `shipmentConfirmationId` and `LabelType=UNIQUE`. Then schedule the pickup.

## Partnered pallet (LTL/FTL)

Quoting needs `pallets[]` and `freightInformation` (declared value, freight
class) in `generateTransportationOptions`. Confirming it needs
`contactInformation`.

- The void window is **1 hour** after confirmation; `voidableUntil` is
  authoritative.
- Get the bill of lading with v0 `getBillOfLading`, using the
  `shipmentConfirmationId`, after the carrier accepts.
- Get pallet labels with v0 `getLabels`, using `LabelType=PALLET` and
  `NumberOfPallets`.
- `amazonReferenceId` from `getShipment` identifies the freight shipment for
  appointments.

## Own carrier (non-partnered)

- Confirm a delivery window first (see above).
- After transportation is confirmed and the goods ship, call
  `updateShipmentTrackingDetails`:
  - Small parcel: one `{boxId, trackingId}` per box. `boxId` values come
    from `listShipmentBoxes`.
  - LTL/FTL: `freightBillNumber` is an array holding **exactly one** PRO
    number. `billOfLadingNumber` is optional.
- There is no charge for cancelling at any time.
- LTL/FTL: the carrier books the FC delivery appointment inside the
  confirmed window, quoting the shipment's `amazonReferenceId`.

## Cancellation

| Carrier | Free until | After that |
|---|---|---|
| Partnered SPD | `voidableUntil` (≈24h) | Carrier charges apply |
| Partnered LTL/FTL | `voidableUntil` (≈1h) | Carrier charges apply |
| Own carrier | Always | No carrier charge |

`cancelInboundPlan` voids **every** shipment in the plan. Placement fees
already incurred are not implied to be refunded; say so if the seller asks.
Treat cancellation as a hard gate.

## Source address changes

`updateShipmentSourceAddress` works only before carriers are confirmed. It
invalidates the transportation options, so show the new address and get a
yes first. Afterwards, regenerate and re-present quotes.
