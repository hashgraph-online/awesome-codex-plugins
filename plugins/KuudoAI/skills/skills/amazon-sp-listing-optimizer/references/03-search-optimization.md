# Search Optimization, Browse Nodes & Searchability Triage

Load this when a listing "doesn't show up in search", when classifying a product,
when working on backend keywords, or when auditing discoverability rather than
compliance.

Source: Seller Central "Search optimization", "Keyword attributes explained",
"Classify your products using Browse Tree Guides", "Use search terms effectively",
"Optimize your product discoverability", and the Amazon search glossary (realigned
2026-07-25).

---

## How Amazon Search actually matches — read this before optimizing anything

**Amazon Search does not do partial matching.** A result for the query
`fitbit charge bands` must contain **all** of those words somewhere in its catalog
data. Not a stem, not a fragment — the words.

This single mechanic drives most keyword strategy:

- Coverage beats repetition. A word absent from every field cannot be matched at any
  rank; a word present twice gains nothing.
- The backend keyword field exists to carry the words that don't belong in
  customer-visible copy — synonyms, alternate names, abbreviations.
- "Rank higher for X" when X's words appear nowhere in the catalog data is the wrong
  question. The listing isn't ranked low for X; it's ineligible for X.

Amazon also judges term relevance automatically and may decline to use supplied terms
— relevance shifts over time as Amazon gathers data. Don't promise a seller that
adding a word guarantees matching on it.

---

## Keyword attributes — the full field set

> **Naming.** Seller Central help spells these in the plural
> (`generic_keywords`). In the Listings API the attributes are singular
> (`generic_keyword`, `specific_uses_keyword`, …), which is what you read and
> patch (verified live).

`generic_keywords` is the field sellers know, but it's one of several keyword
attributes, each with its own byte limit and purpose. Most require **valid values from
the Browse Tree Guides (BTGs)**; only `generic_keywords` and `subject_keywords` take
free text.

| Field name | Attribute | Purpose | Values | Bytes |
|---|---|---|---|---|
| **Search Terms** | `generic_keywords` | General discoverability terms | Free text | **249** |
| **Item Type Keywords (ITK)** | `item_type_keyword` | **Automatically assigns products to browse nodes** (primarily US) | BTG valid values | 250 |
| **Style-specific Terms** | `style_keywords` | Apparel descriptors — "ankle-boots", "fur-lined" | BTG valid values | 100 |
| **Subject Matter** | `thesaurus_subject_keywords` | What is *depicted* on the product (a poster of horses) | BTG valid values | 250 |
| **Subject Keywords** | `subject_keywords` | **Media products only** | Free text | 210 |
| Intended Use | `specific_uses_keywords` | Context/activity/location — *being phased out* (US) | — | 150 |
| Other Attributes | `thesaurus_attribute_keywords` | Product features — *being phased out* (US) | — | — |
| Target Audience | `target_audience_keywords` | End users — *being phased out* (US) | — | — |
| Platinum Keywords | `platinum_keywords` | **Redundant — do not populate.** Storefronts were replaced by Stores | — | — |

**Don't recommend work on the phased-out attributes** (`specific_uses_keywords`,
`thesaurus_attribute_keywords`, `target_audience_keywords`) or `platinum_keywords`.
Effort there is wasted. `subject_keywords` is media-only — using it elsewhere is
incorrect, not merely useless.

### Two different overflow behaviors

| Attribute | Over the limit |
|---|---|
| `generic_keywords` | **The entire attribute is ignored by Amazon Search** |
| All other keyword attributes | Indexed up to the limit; only the excess is ignored |

That asymmetry is why the backend keyword field deserves a byte check and the others
mostly don't. Details and the byte-vs-character math are in `01-policy-rules.md` § 5.

### Free text vs. drop-down

In Seller Central's Keywords tab, sellers can pick a drop-down value or type free
text. **Free text must still match a valid value listed in the BTG** — otherwise it
can't participate in browse assignment queries. Amazon does not publish a master list
of valid values; it directs sellers to the BTG for their category.

---

## The two discovery paths

Customers find products by **browsing** and **searching**, and most often by
combining both. Optimizing one and ignoring the other leaves half the traffic on
the table.

### Browse — classification

Amazon maintains a browse-tree structure; customers refine by category and
subcategory until they reach a specific product type. **Item Type Keywords**
classify a product into browse nodes.

The analogy that lands with sellers: classification is putting the product in the
right aisle, on the right shelf. A product with no browse node isn't on a shelf at
all — it is **not indexed**.

A browse path looks like:
`Electronics > Electronics Bags & Cases > Laptop Computer Briefcases`

Amazon classifies products using **Item Type Keywords** (US) or a **recommended browse
node** (other marketplaces), plus the product description, bullet points, and other
detail-page elements. That last part matters: **high-quality title, bullets, and
description are themselves inputs to browse assignment**, not just to search ranking.

**How assignment actually works:** browse nodes run assignment queries against
attribute values. The query `style_keywords:sport-sandals` assigns every product
carrying that `style_keywords` value to the Sports Sandals node. This is why a value
must match the BTG exactly — a near-miss value matches no query and lands in no node.

**Rules:**
- Get item type keywords from the **Browse Tree Guides (BTG)** — category-specific
  documents listing the valid keywords and their browse node IDs.
- The item type keyword must match the BTG **spelling and formatting exactly**.
- **Choose the most specific subcategory available.** For women's running shoes:
  - Too broad: "Shoes", "Athletic shoes"
  - Correct: "Women's road running shoes"
- When searching in All Departments, Amazon may limit results to products matching
  specific category classifications — misclassification silently removes the
  product from those results.

**The two failure modes are different in severity:**

| Situation | Consequence |
|---|---|
| **Not in any browse node** | The product is **unavailable in both search and browse results** — total invisibility, not reduced ranking |
| In a node, but not the **most specific** one | Searchable, but customers browsing deeper into subcategories never reach it — lost sales at the bottom of the funnel |

### How to classify — by plan and volume

| Situation | Method |
|---|---|
| Individual plan | **Select a product category** — one product at a time (only option) |
| Professional, ~20–30 listings | **Add Products via Upload (Product Classifier)** |
| Professional, 30+ listings | **Browse Tree Guide** — download from *Inventory File Templates and BTG*, choose categories, use the corresponding **browse node IDs** in the inventory template upload |

Volume thresholds are guidance for time-saving, not hard rules — any plan-eligible
method works at any volume.

**Wrong node?** It can be corrected — see "Change a product's category or browse node".

### Why search and browse return different counts

A frequent seller question: searching "pressure cookers" returns 1,000+ results, but
navigating the browse tree to Pressure Cookers returns ~684. **Neither is broken.**

Keyword search matches query words against all of an ASIN's attributes (title,
bullets, description). Browse-based results depend solely on **browse assignment**.
The gap between the two numbers is the population of ASINs that match the words but
aren't assigned to that node — i.e. a measure of catalog-wide misclassification. If
everything were assigned correctly, the counts would converge.

Restrictions on searchability also apply to browse: **an ASIN that isn't searchable
won't appear in browse results either.**

**Audit check:** confirm `product_type` and `item_type_keyword` are coherent with
each other and with the catalog `classifications` path. A hair product typed as a
kitchen product is a browse-node problem that buries the listing regardless of how
good the copy is.

### Search — keywords

Search terms are keywords the engine uses for lexical matching between an ASIN and
a query. For a stainless steel refrigerator, plausible terms include: fridge,
freezer, icebox, cooler, energy-efficient, frost-free, adjustable shelves,
temperature control, stainless steel, kitchen, household, French door, ice maker.

Backend search terms live in the **Generic Keyword** field, are **not visible on
the detail page**, and should contain **generic words only** — synonyms a shopper
might use ("earphones", "earbuds" for headphones).

Full `generic_keyword` rules, the byte limit, and the prohibited list are in
`01-policy-rules.md` § 5.

**Violating the search-term rules can suppress the ASIN and put account health at
risk** — this is not a soft style guideline.

### What Amazon does not promise

Amazon reserves the right not to use all supplied content (including bullets) for
retrieval — reasons include computational efficiency, manipulation prevention,
irrelevant terms, and offensive or illegal terms. Keep the content compliant and
current anyway; just don't promise a seller that every word they write becomes an
indexed keyword.

---

## Searchability triage — "my product isn't in search results"

Run these **before** rewriting any copy. Copy optimization on a listing with no
browse node or no offer is wasted work.

| Issue | Why it blocks | How to check | Resolution |
|---|---|---|---|
| **No offer** | An ASIN needs a buyable offer to be searchable; an expired offer makes it unsearchable | Check for an active offer in Manage All Inventory | Update the listing with Item Price, Quantity, and Offering Release Date |
| **No browse node** | ASINs without a browse node are **not indexed** at all | Review the product detail page for its category assignment | Assign a specific, relevant browse node ("change a product's category") |
| **Listing quality** | Search-suppressed or detail-page-removed listings aren't searchable | **Fix Your Products** in Seller Central | Follow the prompts in the issue description; see `01-policy-rules.md` § 9 |
| **Future launch date** | An ASIN with a launch/offering release date in the future is not searchable | Check the Offering Release Date | Set the Offering Release Date to a past date |
| **Adult categorization** | Products classified adult are restricted from All Departments searches **by design** | Manage All Inventory → select ASIN → Add missing offer details / ⋯ → Edit listing → product type classification | If correctly classified, no fix — explain the behavior. If misclassified, the user opens a Selling Partner Support case to request review |

**Checking through the API:** the audit's `getListingsItem` call answers most of
this table without Seller Central. A missing `DISCOVERABLE` flag in
`summaries[].status` confirms the listing isn't searchable, and `offers` plus
`fulfillmentAvailability` show a missing offer or zero stock. These causes often
come with an **empty `issues[]`**, so don't read "no issues" as "should be
searchable". Status flags and the buyability diagnostic are in
`10-status-and-buyability.md`.

**Propagation:** changes to an ASIN's offer, browse node, or launch date take **up to
72 hours** to reflect in shopping results. Say this before a user concludes the fix
didn't work.

---

## Search behavior that looks like a bug but isn't

Three things sellers routinely misread as problems. Naming them saves a pointless
optimization cycle:

- **Query auto-correction.** Amazon may correct the search query; the customer sees
  "Showing results for …" with a "Search instead for [original]" link. The ASIN may
  be fine — the query changed.
- **Position fluctuation.** Amazon does not guarantee placement. Position varies by
  search location, account type, and desktop vs. mobile. A position that differs
  from the Search Troubleshooter's report is **expected behavior**, not a defect.
- **Result-count limits.** Amazon caps how many ASINs appear across search result
  pages. Beyond that limit the ASIN can't be reached by paging — a more specific
  query or a filter is needed. "I paged to the end and didn't find it" is not
  evidence of suppression.

---

## Seller Central diagnostic tools

All of these are run by the **user** in Seller Central, not by this skill. Point at
them precisely — the access path is non-obvious and both diagnostic tools are reached
by searching help rather than from a menu.

| Tool | How to reach it | What it does |
|---|---|---|
| **Determine why an ASIN is not searchable** | Search **"ASIN is unsearchable"** in Seller Central help | Takes the Search URL + a **child (non-parent) ASIN**; diagnoses why it isn't searchable |
| **Determine why a listing is not displaying** | Search **"inactive"** in Seller Central help | Takes an ASIN; diagnoses why it may not be discoverable |
| **Search Query Performance Dashboard** | Brand Analytics | Bulk auditing of query-level performance |
| **Listing Quality Dashboard** | Seller Central | Continuous inventory auditing, error correction, discoverability |
| **Manage Inventory → Search Suppressed** | Inventory → Manage Inventory | Lists suppressed listings; Edit to fix. Fixed products may become searchable **within 72 hours** |

**Supplying a parent ASIN is the usual reason the unsearchable tool returns nothing
useful** — it requires a child ASIN.

---

## Glossary — terms that change the diagnosis

Definitions worth knowing precisely, because each one implies a different fix:

- **Index suppressed** — a catalog attribute. When `True`, the ASIN is suppressed from
  search and undiscoverable. Check via Inventory → Manage Inventory → Search
  Suppressed. Fixed listings may return within 72 hours.
- **Latency** — up to **72 hours** between a change to an ASIN and it going live.
  Varies with site traffic. This is the single most common reason a correct fix
  "didn't work" — check the clock before re-diagnosing.
- **Launch date** — `YYYY-MM-DD`. Products with a **future** launch date are not
  searchable.
- **Browse node** — products must be assigned to **at least one specific, relevant**
  node to be searchable. Every node has a non-customer-facing **browse node ID** used
  for ASIN assignment.
- **Browse refinements** — the color/size/brand filters. Powered by attribute values,
  which is why attribute completeness is a discoverability issue (see
  `02-attributes-and-error-codes.md`).
- **Valid values** — the acceptable inputs used in browse assignment queries. `blue`
  is a valid value for Color name; `midnight blue` is **not**. A plausible-sounding
  value that isn't on the list simply fails to match.
- **Catalog spam** — catalog data that violates the seller program: other brands'
  names, ASINs, or data irrelevant to the product (listing "phone cover" in the
  catalog data of shoes). This is an account-health matter, not a style issue.
- **Search constraint** — some queries carry constraints beyond keywords. "red
  dresses" is constrained to ASINs in a dress browse node **and** carrying the red
  color refinement. Matching the words alone is insufficient when a constraint applies
  — another reason node and attribute correctness beat keyword volume.
- **Position** — placement in the featured (default sort) shopping results. Not
  guaranteed; see the fluctuation note above.
- **All Product Search (APS)** — a non-category-specific search, e.g. from the home
  page.
- **Parent ASIN** — holds the variation family together and gives all variants one
  detail page. **Parent ASINs are not buyable.**
- **Adult products** — products designed for sexual activity or containing explicit
  content. Restricted from All Departments searches by design.
