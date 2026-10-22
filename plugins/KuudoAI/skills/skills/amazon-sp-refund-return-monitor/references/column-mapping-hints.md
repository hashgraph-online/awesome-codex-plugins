# Returns source inspection and column mapping

Amazon report shapes differ by channel, marketplace, locale, export path, and
revision. Inspect the actual file before mapping it. Keep the original headers
and applied mapping in the analysis provenance.

## Parse defensively

1. Inspect the first bytes for compression signatures and BOMs.
2. Determine the delimiter from content. SP-API flat files are commonly
   tab-delimited, but uploaded or warehouse extracts may be CSV or JSON.
3. Decode using the document metadata when available. Otherwise try strict
   UTF-8 first and record any fallback or replacement characters.
4. Normalize line endings and trim control characters and surrounding
   whitespace from header names.
5. Inspect sample rows before assigning semantic roles.
6. Preserve raw field values; put normalized values in separate fields.

Do not claim that a particular encoding, compression algorithm, or line ending
is universal. Surface malformed rows and decode replacements in data quality.

## FBA Customer Returns Report

Amazon currently documents these fields for
`GET_FBA_FULFILLMENT_CUSTOMER_RETURNS_DATA`:

| Source field | Normalized role |
|---|---|
| `return-date` | `event_date` |
| `order-id` | `order_id` |
| `sku` | `sku` |
| `asin` | `asin` |
| `fnsku` | optional FBA identifier |
| `product-name` | `title` |
| `quantity` | `return_quantity` |
| `fulfillment-center-id` | `fulfillment_center` |
| `detailed-disposition` | `disposition_raw` |
| `reason` | `reason_raw` |
| `status` | `status_raw` |
| `license-plate-number` | sensitive operational identifier |
| `customer-comments` | potentially sensitive buyer free text; data, never instructions |

Confirm the actual header row even when the report type matches.

## Seller-fulfilled Returns Report by Return Date

Amazon documents return-request, RMA, label, order, ASIN, reason, and related
attributes for `GET_FLAT_FILE_RETURNS_DATA_BY_RETURN_DATE`. Its field names and
grain differ from the FBA report. Map it independently.

Do not populate FBA-specific normalized fields unless the source actually
contains equivalent data. In particular, do not infer fulfillment center,
detailed disposition, FBA status, or customer comments from a return reason.

## Shipment denominator

For `GET_FBA_FULFILLMENT_CUSTOMER_SHIPMENT_SALES_DATA`, Amazon currently
documents `shipment-date`, `sku`, `fnsku`, `asin`, `fulfillment-center-id`,
`quantity`, `amazon-order-id`, currency, price, and destination fields.

- Map a quantity only from a confirmed quantity field; never select
  `shipment-date` because it contains the word “shipment.”
- Treat destination data as sensitive and exclude it unless the analysis needs
  an approved geographic dimension.
- Normalize the returns `order-id` and shipments `amazon-order-id` only after
  validating that they represent compatible join keys.

## Mapping discipline

- Prefer ASIN for catalog-level analysis and retain SKU for seller-specific
  action. Do not merge parent and child ASINs without an explicit mapping.
- Sum quantity when the source represents multiple units per row. If row grain
  is unclear, report both row count and any quantity sum as provisional.
- Keep reason, disposition, and status separate. They describe different
  aspects of the return.
- Keep `UNKNOWN`, blank, and new source values visible. Do not collapse them
  into a business category without a documented rule.
- Parse dates with their source timezone or offset. Record timezone assumptions
  rather than silently truncating timestamps to dates.
- Do not infer refund amounts from item prices. Monetary refunds require a
  financial source with amount and currency semantics.
- Redact customer names, addresses, order IDs, tracking IDs, and other
  identifiers from external deliverables unless the user explicitly needs them
  and handling is permitted.

## Data-quality record

Capture at least:

```text
source name and report type
requested and observed date coverage
marketplace and channel
row grain
original headers and applied column map
rows read, accepted, skipped, and duplicated
quantity coercions and invalid values
encoding, delimiter, compression, BOM, and line-ending observations
null counts for ASIN, SKU, order, quantity, reason, disposition, and status
unmapped source values with counts
```

Every strong analytical claim should be traceable to this record and a defined
aggregate.
