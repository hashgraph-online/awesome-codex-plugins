# Patch Construction Reference

Load this when constructing a `listings_patchListingsItem` body, especially for the first edit in a session. The marketplace_id wrapper is the #1 source of validation failures.

---

## The endpoint

`listings_patchListingsItem` corresponds to SP-API `PATCH /listings/2021-08-01/items/{sellerId}/{sku}`.

**Required parameters:**
- `sellerId` — the seller's merchant ID (e.g., `A3433YFPRAEA9F`); on a server with identity selection, this is the selected identity's `label`
- `sku` — the SKU to patch
- `marketplaceIds` — array containing the marketplace ID (e.g., `['ATVPDKIKX0DER']`)
- `productType` — the product type from `listings_getListingsItem` summaries (e.g., `APRON`, `BOOK_DOCUMENT_STAND`, `TABLE_RUNNER`)
- `patches` — the JSON Patch operations array

**Optional parameters:**
- `issueLocale` — for localized error messages
- `mode` — `VALIDATION_PREVIEW` for a dry-run that persists nothing (other wrappers may use `confirm=false`)

---

## JSON Patch operations

Each entry in `patches` is one operation:

```json
{
  "op": "replace" | "add" | "delete" | "merge",
  "path": "/attributes/<attribute_name>",
  "value": [/* new value */]
}
```

### Operations explained

| Op | Effect |
|---|---|
| `replace` | Replace the value at `path` with `value`. Use for attributes that already have a value. |
| `add` | Set the value at `path` if it doesn't exist. Use for attributes that were empty. |
| `delete` | Remove the attribute entirely. Rarely correct — most attributes need a value. |
| `merge` | Merge `value` into the existing object. Use sparingly; only for attributes whose schema is documented as supporting merge. |

### The path

Always: `/attributes/<attribute_name>`. Examples:
- `/attributes/item_name`
- `/attributes/bullet_point`
- `/attributes/product_description`
- `/attributes/generic_keyword`
- `/attributes/material`
- `/attributes/main_product_image_locator`

The attribute name must match the product type's schema. Different product types may have different attribute names for the same conceptual field. When in doubt, look at the output of `listings_getListingsItem` — the `attributes` object shows you the exact names currently in use for this SKU/marketplace.

### The value

**The #1 mistake: forgetting the marketplace_id wrapper.**

Most attribute values are arrays of localized objects:

```json
{
  "language_tag": "en_US",
  "marketplace_id": "ATVPDKIKX0DER",
  "value": "The actual content here"
}
```

All three keys are required. The marketplace_id must match the marketplace the patch is being applied to. The language_tag must be a valid IETF BCP 47 tag (`en_US`, `en_GB`, `de_DE`, `ja_JP`, etc.).

---

## Common attribute schemas

### Single-value attribute (title, description)

```json
{
  "op": "replace",
  "path": "/attributes/item_name",
  "value": [
    {
      "language_tag": "en_US",
      "marketplace_id": "ATVPDKIKX0DER",
      "value": "Encasa XO Adjustable Kitchen Cotton Apron with Pockets"
    }
  ]
}
```

Note: even though it's a single value, it's wrapped in an array of one object.

### Multi-value attribute (bullets)

To change ANY bullet, send ALL 5 bullets. PATCH replaces the array; it does not merge by index.

```json
{
  "op": "replace",
  "path": "/attributes/bullet_point",
  "value": [
    {"language_tag": "en_US", "marketplace_id": "ATVPDKIKX0DER", "value": "First bullet here"},
    {"language_tag": "en_US", "marketplace_id": "ATVPDKIKX0DER", "value": "Second bullet here"},
    {"language_tag": "en_US", "marketplace_id": "ATVPDKIKX0DER", "value": "Third bullet here"},
    {"language_tag": "en_US", "marketplace_id": "ATVPDKIKX0DER", "value": "Fourth bullet here"},
    {"language_tag": "en_US", "marketplace_id": "ATVPDKIKX0DER", "value": "Fifth bullet here"}
  ]
}
```

### Simple text attribute (no localization)

Some attributes use a different shape — a simple `value` and `marketplace_id`:

```json
{
  "op": "replace",
  "path": "/attributes/country_of_origin",
  "value": [
    {"marketplace_id": "ATVPDKIKX0DER", "value": "IN"}
  ]
}
```

`country_of_origin` and similar enum/code attributes don't take `language_tag`. The structure is product-type-dependent — verify with `listings_getListingsItem` first.

### Backend search keywords

```json
{
  "op": "replace",
  "path": "/attributes/generic_keyword",
  "value": [
    {
      "language_tag": "en_US",
      "marketplace_id": "ATVPDKIKX0DER",
      "value": "kitchen apron cotton baking bbq grilling"
    }
  ]
}
```

Single space-separated string. No commas. Lowercase. **Write to under 200 bytes** — see `01-policy-rules.md` § 5 for why 200 rather than 250.

---

## Common attribute names

These are the most common attributes you'll patch. Names can vary by product type — always confirm with `listings_getListingsItem` output.

| Conceptual field | Common attribute name |
|---|---|
| Product title | `item_name` (policy limit 75 chars) |
| Item highlights | *varies by product type* — confirm in `listings_getListingsItem.attributes` or the Definitions API; ≤125 chars, comma-separated phrases |
| Bullet points | `bullet_point` (array of 3–5; 10–255 chars each) |
| Product description | `product_description` |
| Backend search terms | `generic_keyword` |
| Brand | `brand` |
| Manufacturer | `manufacturer` |
| Model number | `model_number` |
| Part number | `part_number` |
| Material | `material` / `fabric_type` (varies) |
| Color | `color` |
| Size | `size` |
| Care instructions | `care_instructions` |
| Country of origin | `country_of_origin` |
| EU DSA contact address | `dsa_responsible_party_address` (postal address required; not email) |
| Item type keyword | `item_type_keyword` |
| Variation theme | `variation_theme` |
| Parentage level | `parentage_level` |
| Main product image | `main_product_image_locator` |
| Other product images | `other_product_image_locator_1` through `_8` |
| Item dimensions | `item_dimensions` |
| Item weight | `item_weight` |
| Package dimensions | `item_package_dimensions` |
| Package weight | `item_package_weight` |
| List price | `list_price` |
| Standard price | `standard_price` |
| Quantity (MFN) | `fulfillment_availability` |

---

## Complex attributes and conditional groups

Not every fix is a single simple `replace`.

**`purchasable_offer` (and similar nested attributes) don't replace cleanly.** The offer holds sub-structures — `our_price` schedules, `minimum_seller_allowed_price` / `maximum_seller_allowed_price`, discounted prices, B2B quantity tiers, audience (`ALL` vs `B2B`), `currency`. A blind top-level `replace` on `/attributes/purchasable_offer` can drop the ones you didn't resend. Follow Amazon's supported operations for this attribute ([Manage purchasable offers](https://developer-docs.amazon.com/sp-api/docs/manage-purchasable-offer#supported-operations-for-purchasable_offer)): read the current offer first, change only what the user asked for, and target the precise sub-path where the guide allows it. Use exactly the price the user gives — never propose one.

**One issue can need several attributes.** Product-type schemas carry conditional (`allOf`) rules: setting attribute A can make B and C required (error `99010` is the symptom). Patch the whole group in **one** patch body, and use the preview to confirm no *new* required-attribute error appeared — don't trade one error for another across two submissions.

Respect `"editable": false` in the product-type definition — those attributes can't be changed by patch.

---

## Validation preview ("preview" / dry-run)

On the SP-API, pass `mode: "VALIDATION_PREVIEW"` to `patchListingsItem`. It runs Amazon's full validation and **persists nothing**. Check the schema with `get_schema` (`detail="full"`) before the first patch in a session. Hosts that wrap the operation may use their own dry-run flag instead, such as `confirm=false`.

The preview returns:
- `status` — `VALID` or `INVALID`
- `issues[]` — any validation problems, including ones your change would *introduce*
- Confirmation of which fields would change

Always preview first. Even for "obvious" fixes. If the preview reports issues, fix the patch and preview again; never carry an invalid patch forward.

---

## Confirmation

After the user's explicit confirmation in chat, submit the **same** call without `mode`, in a new `execute` block that calls `set_active_identity` first (see `11-tool-access.md`).

Wrappers that use `confirm=true` also take an `idempotency_key` — a fresh, unique string bound to that patch outcome once consumed. A descriptive format is easiest to trace: `<sku>-<field>-<YYYYMMDD>-<short-desc>` (e.g. `mc-bs-01-bullets-20260512-iron-fix`).

---

## Response shape

A successful submission returns:
- `status` — `ACCEPTED` (the patch was received and validated)
- `submissionId` — Amazon's tracking ID
- `issues[]` — usually empty on acceptance; populated with warnings if Amazon found issues but accepted anyway

**"ACCEPTED" does not mean "live."** Amazon validates and queues the change. Propagation to the public detail page takes minutes to hours. The catalog snapshot in warehouse-backed tools won't reflect the change until the next ingestion.

---

## Common patch failures

| Failure | Cause | Fix |
|---|---|---|
| `INVALID_ATTRIBUTE` | Attribute name doesn't exist for this product type | Check `listings_getListingsItem.attributes` for the correct name |
| `MISSING_ATTRIBUTE` (marketplace_id) | Forgot `marketplace_id` in a localized value | Add `marketplace_id` to each object in the value array |
| `INVALID_LANGUAGE_TAG` | Used `en` instead of `en_US`, or similar | Use full IETF BCP 47 tag |
| `EXCEEDED_LIMIT` / `90225` (length) | Title >200 chars (the field cap — note the **policy** limit is 75), item highlights >125 chars, bullet >255 chars, description >2000 chars, `generic_keyword` over the byte limit (`97779`) | Trim to spec. A title between 76 and 200 will **not** raise this error but is still non-compliant — relocate the surplus to item highlights |
| `PROHIBITED_VALUE` | Used a banned phrase ("free shipping", competitor name, etc.) | Rewrite |
| `IMAGE_NOT_ACCESSIBLE` | Image URL returns 403/404 or isn't reachable from Amazon | Host on a public-accessible URL |
| 404 on the SKU itself | Wrong identity selected, or the SKU belongs to another seller on the ASIN | Re-run `set_active_identity` in the same block, then `searchListingsItems` filtered by ASIN to see who owns which SKU |

When a patch fails, the response will include `issues[]` with codes and messages. Surface these to the user verbatim — don't paraphrase Amazon's error.

---

## Bulk-edit patterns

For applying the same fix across many SKUs:

1. Get the list of target SKUs (`listings_searchListingsItems` with filters, or a user-supplied list).
2. Run `listings_getListingsItem` for each to confirm current state.
3. Build a list of preview patches.
4. **Show the user the full list before any submission.** Bulk preview means bulk diff — make it skimmable (a table is good).
5. Get one explicit "confirm bulk submit" — not one per SKU.
6. Submit in sequence, setting the identity at the top of each write block (and, on hosts that take them, unique idempotency keys like `<sku>-<batch-id>-<short-desc>`). Stay inside the sandbox limits — about 20 SKUs per `execute` block.
7. Report results in a table: SKU, status, submission ID. Surface any failures separately.

Don't parallelize patches without an explicit rate-limit confirmation. SP-API `listings_patchListingsItem` is typically 5 req/sec sustained but burst limits vary.
