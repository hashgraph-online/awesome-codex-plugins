# Size Charts

Load this when working on apparel, shoes, or any sized product — especially when a
listing has size-related returns, missing size guidance, or a variation family whose
children differ by size.

Source: Seller Central "Create a Size Chart for Your Products".

---

## Why this belongs in a listing audit

A size chart is not decoration. In apparel, wrong-size returns are the dominant return
reason, and returns are the expensive failure mode — the seller pays shipping both
ways, the unit may be unsellable, and the return rate feeds listing quality signals. A
missing size chart on a sized product is a conversion *and* a returns problem, so it
belongs in the "what's missing or thin" section of a review rather than as an
afterthought.

It also pairs directly with two rules elsewhere in this skill:
- Size belongs in **child** ASIN titles, never the parent (`01-policy-rules.md` § 1).
- Shoes children are suppressed without `Department`, `Size`, and `Color`
  (`01-policy-rules.md` § 9).

The size chart is the customer-facing counterpart to those structured attributes.

---

## Eligibility and access

**Size charts apply only to Brand-registered listings.** Confirm Brand Registry before
promising one — same gate as A+ Content (`05-aplus-content.md`).

**Self-service path:** Catalog → **Add size charts**. The tool downloads a template,
accepts an upload, previews the chart, and publishes it to the product detail page.

**If the tool isn't accessible:** it's a permissions issue, not an eligibility one. The
primary account manager enables **size chart permissions** in **User Permissions** under
**Settings**. Check this before concluding the account is ineligible — the two failure
modes look identical from the seller's side and have completely different fixes.

**Fallback when the tool still isn't available** (brand *is* registered, account owner
*doesn't* have the tool):

1. Download the template for the product's subcategory.
2. Fill in all details.
3. Contact Seller Support with the completed template, specifying **brand name,
   product subtype, and department**.
4. Amazon's team reviews the file and creates the chart.

That's a user action — this skill can prepare the values and tell them exactly what to
specify, but it does not open Amazon support cases.

---

## Available templates by category

| Category | Subcategory | Variants |
|---|---|---|
| **Apparel** | Accessories | Men, Women |
| | Clothing | Baby, Boys, Girls |
| | Blazer | Men, Women |
| | Bra | Women |
| | Dress | Women |
| | Ethnic Wear | Men, Women |
| | Hat | Men, Women |
| | Outerwear | Men, Women |
| | Pants | Men, Women |
| | Shirt | Men, Women |
| | Shorts | Men, Women |
| | Skirt | Women |
| | Sleepwear | Men, Women |
| | Socks | Men, Women |
| | Suit | Men, Women |
| | Sweater | Men, Women |
| | Swimwear | Men, Women |
| | Underwear | Men, Women |
| **Auto** | Powersports Riding Helmet | Hard Goods |
| **Shoes** | Shoes | Baby, Boys, Girls, Men, Women |
| **Sports** | Sporting Goods | Boys, Girls, Hard Goods, Men, Unisex, Women |

---

## ⚠️ Marketplace scope — read before using any of this

The published template set is **Amazon India (amazon.in)**. The evidence is
unambiguous: mandatory size columns are `IN`-prefixed (`INDressSize`, `INBlazerSize`,
`INCupSize`, `INBandSize`, `INPantsSize`), and **Ethnic Wear** is an India-specific
apparel category.

Amazon states it follows a global size chart format, so the *structure* — a size-label
column plus body-measurement columns, with units and mandatory flags — carries across
marketplaces. The *specific size-label columns do not*. A US listing needs
`USDressSize` semantics, not `INDressSize`.

**So:** treat the schemas below as the shape of the problem and the checklist of body
measurements to collect. Do **not** hand a seller India size labels for a US, UK, DE,
or JP listing. When the marketplace isn't India, confirm the correct template by
downloading it from that marketplace's Seller Central rather than assuming this
mapping transfers.

---

## Template structure

Every template shares one layout:

- A header block declaring, per column: the **dimension name**, whether it's
  **mandatory** or **optional**, and the **unit**.
- A data area of up to **20 rows** — one row per size offered. Amazon's instruction:
  *"complete as many rows as you need only."*
- An optional **chart footer** note (`POST_TABLE_NOTE`) beneath the table.

Units are per-column, not per-chart — a single chart commonly mixes `inches` for body
measurements with an unitless size label, and `underwear_men` uses `cms`. Always read
the unit row rather than assuming inches.

## Measurement schemas

Mandatory columns per template (`*` = mandatory). Use this to know **what to ask the
seller to measure** before starting a chart.

| Template | Units | Mandatory columns |
|---|---|---|
| blazer_men | inches | INBlazerSize\*, ChestSize\*, WaistSize\* |
| blazer_women | inches | INBlazerSize\*, BustSize\*, WaistSize\* |
| dress | inches | INDressSize\*, BustSize\*, WaistSize\* |
| ethnic_women | inches | BustSize\*, WaistSize\*, Height\* |
| outer_wear_women | inches | INOuterwearSize\*, BustSize\*, WaistSize\* |
| pants_men | inches | INPantsSize\*, WaistSize\*, InseamLength\* |
| pants_women | inches | INPantsSize\*, WaistSize\* |
| shirt_men | inches | INShirtSize\*, ChestSize\*, WaistSize\* |
| shorts_men | inches | INPantsSize\*, WaistSize\*, InseamLength\* |
| shorts_women | inches | INPantsSize\*, WaistSize\* |
| skirt_women | inches | INSkirtSize\*, UKSkirtSize\* |
| sleepwear_women | inches | INSleepGownsSize\*, WaistSize\* |
| sports_women | inches | WaistSize\* |
| suit_men | inches | INJacketSize\*, ChestSize\*, WaistSize\* |
| suit_women | inches | INJacketSize\*, BustSize\*, WaistSize\* |
| sweater_men | inches | INSweaterSize\*, ChestSize\*, WaistSize\* |
| sweater_women | inches | INSweaterSize\*, BustSize\* |
| swimwear_men | — | INSwimSize\*, WaistSize\* |
| swimwear_women | inches | INSwimOnePieceSize\*, BustSize\*, HipSize\* |
| under_wear_women | inches | INCamisoleSize\*, HipSize\*, BustSize\* |
| underwear_men | cms | INUnderwearSize\*, ChestSize\* |
| sports_hard_goods | years, feet, inches | age\*, Height\*, Length\*, Width\* |
| bra | inches | *(none mandatory)* — INCupSize, INBandSize, UnderbustSize, OverbustSize |
| shirt_women | inches | *(none mandatory)* — INBlouseSize, BustSize, WaistSize |
| socks_women | — | *(none mandatory)* — UKShoeSize, USShoeSize, EUShoeSize, Height, Weight |

Optional columns commonly available across apparel templates: `UKSize`/`USSize`
equivalents, `HipSize`, `SleeveLength`, `ShoulderWidth`, `NeckSize`, `Height`,
`Length`, `Rise`.

Shoe templates key off `FootLength` with `USShoeSize` / `UKShoeSize` / `EUShoeSize`
conversion columns — the conversion columns are what make a shoe chart useful, since
shoppers know their local size but not their foot length in inches.

**The pattern worth internalizing:** every apparel template makes the *size label*
plus **two body measurements** mandatory (usually chest/bust and waist). If a seller
has only a size label and no measurements, the chart cannot be built — that's the
first thing to check when someone asks for one.

---

## Working a size chart in an audit

1. Confirm the product is sized and Brand-registered.
2. Check whether a chart already exists on the detail page.
3. Identify the correct subcategory template from the table above — and the correct
   **marketplace**, per the scope warning.
4. Collect the mandatory measurements for every size offered. Missing measurements,
   not tooling, is the usual blocker.
5. Confirm the chart's sizes match the actual child SKUs in the variation family. A
   chart listing sizes the seller doesn't stock is worse than no chart — it generates
   returns and "size unavailable" frustration.
6. Route to the self-service tool, or to the Seller Support fallback if permissions
   block it.
