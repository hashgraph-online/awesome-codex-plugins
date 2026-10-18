# Read patterns

Load this before reading listing data for an audit or a scan. It covers the
context budget, the one-SKU audit read, the multi-SKU health scan, and the
response shapes those reads rely on. Payload sizes and shapes were verified
live, read-only, on 2026-09-24.

## Context budget

Raw payloads are large (measured live):

| Read | Size |
|---|---|
| `getListingsItem`, all `includedData` | 2–13 KB per SKU |
| `getCatalogItem`, audit `includedData` | 8–10 KB per ASIN |
| `searchListingsItems`, `summaries` + `issues` + `fulfillmentAvailability` + `relationships` | about 0.9 KB per SKU |
| `searchListingsItems`, with `attributes` and `offers` | about 7.7 KB per SKU |

So return **counts for everything and rows only for the slice the user
needs**, and reduce every response inside `execute` before returning it.

### One SKU: the audit read

Use one block with two reads, plus a third for FBA stock. Keep these fields
and drop the rest; live, this cut about 18 KB of raw payload to about 3 KB.

| From | Keep |
|---|---|
| `listings_getListingsItem` (`summaries`, `attributes`, `issues`, `offers`, `fulfillmentAvailability`, `relationships`) | `summaries[0]`: `asin`, `productType`, `status`. `issues[]`: `code`, `severity`, `message` (verbatim), `attributeNames`, `enforcements.actions[].action`. `offers[]`: type, price, currency. The copy: `item_name`, `bullet_point[]`, `product_description`, `generic_keyword` (and its UTF-8 byte count), `item_type_keyword`, and any highlights attribute. `dsa_responsible_party_address`. Any attribute a claim touches (`material`, `care_instructions`, `color`, `size`, `country_of_origin`). The **names** of all attributes present, for the completeness check |
| `catalog_getCatalogItem` (`summaries`, `classifications`, `relationships`, `images`, `salesRanks`) | `summaries[0]`: `itemClassification`, `brand`, `browseClassification`, `adultProduct`. Parent and child ASIN counts. Distinct image `variant` slots (`MAIN`, `PT01`, …). Top sales rank |
| `fba-inventory_getInventorySummaries` (only when a fulfillment channel is `AMAZON_*`) | `inventoryDetails.fulfillableQuantity`. Call it with `granularityType: "Marketplace"`, `granularityId`, `marketplaceIds`, `sellerSkus`, `details: true` |

Localized attribute values are lists of `{value, language_tag,
marketplace_id}` objects; read `[0].value` for single-value attributes.

### Many SKUs: the health scan

1. **Count first.** `searchListingsItems` returns `numberOfResults` for any
   filter, so each count is one call with `pageSize: 1` and no paging:

   | Filter | Counts |
   |---|---|
   | none | all listings (the total) |
   | `withStatus: ["BUYABLE"]` | buyable |
   | `withStatus: ["DISCOVERABLE"]` | discoverable |
   | `withIssueSeverity: ["ERROR"]` | listings with at least one error |
   | `withIssueSeverity: ["WARNING"]` | listings with warnings |

   **Not buyable = total − buyable.** Don't count it with `withoutStatus:
   ["BUYABLE"]`. Live, that filter returned 41 when 55 listings weren't
   buyable. It left out the 7 variation parents and the 7 SKUs with no
   fulfillment channel. (The same goes for `DISCOVERABLE`.)

2. **Scan the slice.** Page with `pageSize: 20` (the maximum),
   `includedData: ["summaries", "issues", "fulfillmentAvailability",
   "relationships"]` (about 0.9 KB per row), and `pagination.nextToken` →
   `pageToken`. Never scan with `attributes`; it costs about eight times as
   much per row. Apply the user's filter server-side (`identifiers` +
   `identifiersType`, `withIssueSeverity`, `withStatus`). Live, 4 pages took
   under 3 seconds, so about 25 pages (500 SKUs) fit in one block. If a scan
   stops early, return the token as a cursor for the next block.
3. **Reduce everything inside the block, and return only the summary.**
   Build these three things in the sandbox and return nothing else:
   - **Issue groups**, one per issue code: code, severity, enforcement
     actions, attribute, the number of SKUs, up to 3 example SKUs, and
     Amazon's message once. This is usually the most useful view, because
     one fix often clears a whole group.
   - **The not-buyable breakdown.** For each SKU without `BUYABLE`, sort it
     as a variation parent (the listing relationships have `childSkus`;
     never buyable by design), no fulfillment channel (empty
     `fulfillmentAvailability`), merchant-fulfilled with quantity 0, or FBA.
     FBA quantity isn't in Listings, so an FBA SKU is only *likely* out of
     stock until `getInventorySummaries` confirms it; batch its `sellerSkus`.
   - **The top 25 SKU rows**, ranked, with `rows_omitted`. Each row holds
     SKU, ASIN, status, error and warning counts, enforcement actions, and
     the top issue's code and attribute. Leave out titles and other text.
4. **Rank by enforcement action first, whatever the severity.** Live data had
   `LISTING_SUPPRESSED` on a `WARNING`-severity issue. The order is: listing
   suppressed → search suppressed → attribute suppressed → error with no
   enforcement → not buyable with no error → warning only → healthy.
5. **Report** the counts, the not-buyable breakdown, and the issue groups.
   Offer the full SKU list, and warn that it's large.
6. **Deep-audit only the SKUs the user picks**, with the one-SKU read, about
   3 per block.

## Response shapes worth knowing

- **Classification comes from the catalog.** Listing `summaries` have no
  `itemClassification`. Catalog `summaries[].itemClassification` is
  `BASE_PRODUCT`, `VARIATION_PARENT`, or `PRODUCT_BUNDLE`. A variation child
  is a `BASE_PRODUCT` whose catalog relationships include `parentAsins`.
- **Relationships are nested one level.** In the catalog:
  `relationships[].relationships[].childAsins` / `parentAsins`. In the
  listing: `relationships[].relationships[].childSkus`, with
  `variationTheme`. A child SKU's listing can show no relationship even when
  the catalog lists its parent.
- **Status is an array, in no fixed order.** Test membership, never
  position.
- **FBA stock isn't in Listings.** `fulfillmentAvailability` reports
  `quantity` only for merchant-fulfilled (`DEFAULT`) stock. FBA entries carry
  a channel code and no quantity.
- **`enforcements` is often absent.** That means Amazon hasn't acted yet,
  not that the issue is minor.
- **Attribute names are singular in the API:** `generic_keyword`,
  `specific_uses_keyword`, `item_type_keyword`, `bullet_point`. Seller
  Central help pages spell some of them in the plural.
