# Amazon Listing Policy Rules

The hard, non-negotiable rules. Load this when checking a listing for compliance, drafting copy that must pass review, or diagnosing a suppression.

Source of record: Seller Central "Product title requirements and guidelines", "Product bullet point requirements", "Attributes guide", "A+ Content guide", and "Search optimization" (realigned 2026-07-25). When current Seller Central help disagrees with this file, the live page wins and this file is stale.

## Table of contents

1. Title rules
2. Item highlights
3. Bullet point rules
4. Product description rules
5. Backend search term rules
6. Image rules
7. Brand name policy
8. Variation rules
9. Suppression triggers (what makes a listing disappear from search)
10. Prohibited content (universal)
11. EU DSA compliance
12. Listing hijacking & tamper detection

---

## 1. Title rules

Title requirements apply to **all product types except media**, in **all stores except Saudi Arabia, Egypt, Türkiye, and the UAE**.

### Length — 75 characters

**Amazon's policy limit is 75 characters including spaces.** This is the number that matters. A title over 75 characters is non-compliant; Amazon may auto-correct it or drop the listing out of search results.

Two numbers get confused here, so be precise when reporting:

| Number | What it is |
|---|---|
| **75 chars** | The **policy limit**. Enforced on new listings, and existing non-compliant titles get auto-corrected or suppressed from search. This is what to audit against and what to write to. |
| 200 chars | The **technical field cap** — what `item_name` will still physically accept via PATCH. A patch under 200 but over 75 can be accepted by the API and still be non-compliant. |

Never tell a user a 120-character title is "fine because it's under 200." It is accepted but non-compliant. Say so plainly.

If the product genuinely needs more descriptive text than 75 characters allows, that overflow belongs in **item highlights** (§2), not in the title.

Policy-violating titles are visible in **Manage All Inventory**; brand owners can also see them in **Review listing changes**.

### Characters

- **Never allowed:** `!`, `$`, `?`, `_`, `{`, `}`, `^`, `¬`, `¦`.
- **Allowed only in specific, functional contexts:** `~`, `#`, `<`, `>`, `*`. Legitimate uses are product identifiers (`Style #4301`) and measurements (`<10 lb`). **Decorative use is non-compliant** — e.g. `Paradise Towel Wear Co. Beach Coverup << Size Kids XXS >>` fails on excessive symbols around the size.
- **Allowed punctuation:** hyphens `-`, forward slashes `/`, commas `,`, ampersands `&`, periods `.`.
- **No non-language ASCII characters:** `Æ`, `Š`, `Œ`, `Ÿ`, `Ž` and similar.
- No emoji.
- **Brand names containing prohibited characters are exempt** — they go in the **Brand name** field, not the title. The brand byline renders them on the detail page and in search results.

### Formatting

- Capitalize the first letter of each word **except** prepositions (in, on, over, with), conjunctions (and, or, for), and articles (the, a, an).
- **No ALL CAPS and no all-lowercase.** `NIKE AIR RUNNING SHOES` and `nike air running shoes` both fail; `Nike Air Running Shoes with Cushioned Sole` passes.
- Use numerals, not spelled-out numbers: `2-Pack Cotton Towels, 24 x 48 inches`, not `Two-Pack ... Twenty-Four x Forty-Eight`.
- **Abbreviate measurements** — `cm`, `oz`, `in`, `kg`. `Samsung 55-inch 4K Smart TV, 55 in, 2023 Model`, not `Fifty-Five inch ... Television`.

### Content

- Include the **minimum information needed to clearly describe the product** — "Amazon Essentials Dress", "Columbia Hiking Boots", "Sony Headphones". Long or cluttered titles are harder to read and truncate on mobile.
- **Word repetition: no word more than twice.** Prepositions, articles, and conjunctions are exempt. **Brand names are NOT exempt** — they are subject to the same two-instance limit. Part of a brand name reused in a different sense doesn't count as a duplicate ("Old Navy" and "Navy Blue" are distinct). Non-compliant example: `Baby Boy Outfits Baby Boy fall Winter Clothes Baby Boy Long Sleeve Suspender Outfit Sets`.
- **No redundancy** generally — `Levi's Men's Jeans Men's 501 Original Fit Men's Denim Jeans` repeats "Men's" and "Jeans" pointlessly.
- **No promotional content**: "free shipping", "100% quality guaranteed", "Sale", "Discount", "Best Price".
- **No subjective commentary**: "Hot Item", "Best Seller", "Top Rated", "#1".
- **No restricted phrases** such as "FSA/HSA eligible".
- No seller name, no price, no time-sensitive language ("New", "Latest", "Now Available").
- **Model numbers** are recommended in titles for certain categories — check the category-specific style guide (query `amazon_atlas`) rather than assuming.

### Information order

`Brand name → flavor or style → product type → key attribute → color → size or pack count → model number`

Order the words so the most important product information comes first.

- Compliant: `Amazon Fresh Decaf Colombia Whole Bean Coffee, Medium Roast, 12 Ounce`
- Non-compliant: `Medium Roast Decaf Coffee 12oz Pack of 3 Colombia Whole Bean Amazon Fresh`

Multi-pack count belongs in the size/pack-count position.

### Parent vs. child titles

**Size and color go in child ASIN titles only — never in the parent title.**

| | Compliant | Non-compliant |
|---|---|---|
| Parent | `Amazon Essentials T-Shirt` | `Amazon Essentials T-Shirt, Available in Multiple Colors and Sizes` |
| Child | `Amazon Essentials T-Shirt, White, Medium` | *(same as parent)* |

The detail page displays the **parent** title. The child title only appears once the ASIN is in the customer's cart — so a child title identical to the parent wastes the one place variant-specific copy is read.

### Title suppression — troubleshooting

If a title is suppressed or blocked:

1. Go to **Manage All Inventory** → **Search suppressed and inactive listings** to confirm suppression.
2. Review the specific policy violations identified.
3. Edit the title to comply (remove prohibited characters, promotional content, excessive repetition, over-length).
4. Submit. Amazon re-checks automatically and lifts the suppression once the title meets requirements.

Category-specific title formulas live in `amazon_atlas` (`doc_type: style_guide`).

---

## 2. Item highlights

**Item highlights is a distinct field from the title**, introduced alongside the 75-character title limit as the place for detail the title can no longer carry. It is the correct answer to "the title is too short for all my product details" — do not solve that by overstuffing the title.

| Property | Value |
|---|---|
| Length | **125 characters** (in addition to the title's 75) |
| Format | **Comma-separated phrases**, not full sentences |
| Visibility | Below the title, both in **search results** and on the **product detail page** |
| Editing | Manage All Inventory, same as titles |
| Availability | Unlocked when the title is brought to the 75-character limit |

**Worked example from Amazon:**

- Instead of the over-long title `Fast Charger Adapter, PPS Supported, Compact Charger for models like MacBook Air/Macbook Pro/iPhone 14/iPhone 13/Galaxy S22/iPad Pro/Pixel and More, Cable Not Included`
- Keep a compliant 75-char title and move the detail to item highlights: `USB-C, PPS Support, Cable not included`

**When auditing:** if a listing has an over-length title *and* an empty item highlights field, that pairing is the fix — trim the title to 75 and relocate the surviving detail into highlights as comma-separated phrases. Report it as one action, not two.

Note: the attribute name for item highlights varies by product type. Confirm it in `listings_getListingsItem.attributes` (or the Product Type Definitions API) before patching — do not guess it.

---

## 3. Bullet point rules

**Count:**
- Up to 5 bullets per listing.
- **At least 3** — this is Amazon's stated minimum, and a listing with 1–2 bullets reads as thin/unfinished.
- Use all 5 where there's real content — empty bullets waste real estate.

**Length — 10 to 255 characters per bullet:**
- **Hard range: 10–255 characters** per bullet. Under 10 isn't a real bullet; over 255 is out of spec.
- **All bullets together must total under 1,000 characters.** This is a stated requirement, not just a scanability preference — and it binds before the per-bullet cap does: five bullets at the 255 maximum would be 1,275 characters and therefore non-compliant as a set. Budget roughly 200 characters per bullet across five.
- Aim for roughly 100–200 per bullet to have room to make a point while staying inside the set total.

Bullets are **not always indexed** by Amazon Search, but they **always appear in full** on the product detail page. Write them for the shopper, not the index.

**Formatting:**
- Begin each bullet with a **capital letter**.
- **Sentence fragment, no end punctuation.**
- **Structure: header, colon, description.** e.g. `Cotton fabric: Made from 100% cotton for softness and breathability`. This is Amazon's recommended shape, and it also scans well on mobile.
- Semicolons separate phrases within a single bullet.
- No ALL CAPS for a whole bullet (a caps LEAD-IN followed by sentence case is tolerated, but the header:description form above is preferred).
- **Lead-in consistency across all bullets.** All-caps lead-ins ("FITS YOU PERFECTLY:") mixed with title-case lead-ins ("Versatile Usage") in the same set looks like uncoordinated rewrites. Pick one style and use it throughout.

**Numbers and measurements — note this differs from titles:**
- **Write numbers one to nine in full** ("five", not "5"). Exceptions: names, model numbers, and measurements, which stay numeric.
- Numbers 10 and above stay numeric.
- **Put a space between digit and unit**: `60 ml`, not `60ml`.

Titles use numerals throughout (§1); bullets spell out one–nine. Don't carry one convention into the other.

**Amazon's own example of a high-quality bullet set:**

```
Cotton fabric: Made from 100% cotton for softness and breathability
Long sleeve: Long sleeves add coverage and style
Loose fit: Relaxed fit allows for easy movement and comfort
Machine washable: Durable construction allows for easy care
Versatile style: Perfect for dance practice, playtime, or outdoor activity
```

**Content rules:**
- **Focus on features, benefits, and how the product meets customer needs.** Avoid brand marketing stories — those belong in A+ Brand Story.
- Each bullet states a feature **plus its benefit** — not just a spec.
- **Every bullet must carry unique information.** Repeating the same point across bullets is prohibited content, not just weak copy.
- **Maintain data consistency across product variants**, and **minimize duplication** with the title, product description, and product overview.
- Maintain consistent order across bullets in the same product family (e.g., always lead with material).
- **Do not divert or refer to other products not covered by this ASIN**, and do not compare the product to competitor brands.
- No promotional language ("Sale", "Limited Time"), price, shipping, or contact info.
- No HTML tags (HTML is no longer rendered in bullets).

**Restricted claims (rejection/suppression without substantiation):**
- **Subjective, performance, or comparative claims** — avoid unless **verifiable on the packaging**. That's the test Amazon applies.
- **Unsubstantiated award claims or consumer survey results** are prohibited.
- **Environmental claims:** "eco-friendly", "environmentally friendly", "ecologically friendly". Amazon restricts unqualified environmental claims; a certification is generally required.
- **Material-sourcing claims:** "made from bamboo", "contains bamboo", "made from soy", "contains soy" — explicitly prohibited (see General listing restrictions).
- **Health/germ claims:** "anti-microbial" / "antimicrobial", "anti-bacterial" / "antibacterial". Regulated claims (EPA/FDA territory), rejected on standard listings.
- **Guarantee language:** "full refund", "if not satisfied, send it back", "unconditional guarantee with no limit", "money back guarantee", "100% guarantee". Warranty terms belong in the warranty attribute.
- **Placeholder / copy residue:** "not applicable", "NA", "n/a", "N/A", "not eligible", "yet to decide", "to be decided", "TBD", "copy pending". A placeholder shipped live reads as an unfinished listing.
- **ASINs** (e.g. `B00UXG4WR5`) must not appear in bullets.
- **External information:** company information, website links, external hyperlinks, contact information.

**Prohibited and risky characters in bullets:**
- **Hard-prohibited** (can cause the bullet to be removed or updated): `™ ® € … † ‡ ° ¢ £ ¥ © ± ~ â`, and emoji (`☺ ☹ ✅ ❌` and any others).
- **Soft / awareness** (indexing or mobile-display risk, not an outright ban): curly quotes `" " « » ‹ ›`, math symbols `× ÷ ≈ ≠`, arrows `→ ← ↑ ↓`. Smart punctuation like the em-dash is fine; the symbols above are not.

**Recommended structure (one pattern):**
1. Material / core spec
2. Feature → benefit
3. Feature → benefit
4. Feature → benefit
5. Care, or "what's in the box"

Note that Amazon reserves the right not to use all supplied bullet content for search retrieval (computational efficiency, manipulation prevention, irrelevant or offensive terms). Write bullets for the shopper first; indexing is a bonus, not the goal.

---

## 4. Product description rules

**Length:**
- Hard cap: 2,000 characters.
- HTML is no longer rendered — line breaks (`</br>`) are the only structural tool.

**Content:**
- Replicate and expand key bullet points with more depth.
- Describe feel, usage, benefits — help the customer imagine ownership.
- Include accurate dimensions, care, warranty.

**Do not include:**
- Seller name, email, website, phone.
- Specific company information.
- Detailed information about other products you sell.
- Promotional language: "Special offer", "Free shipping".
- Quotes or testimonials from customers.
- Time-sensitive references.

**If the listing has A+ Content active**, the description is hidden on the detail page. It's still worth keeping clean — A+ approval can be revoked, and the description re-surfaces.

---

## 5. Backend search term rules (`generic_keyword`)

### Length — and the failure mode that makes it matter

**Limit: 249 bytes** (Keyword attributes explained), documented elsewhere as "less than 250 bytes". Seller Central's Generic keyword field simply **stops accepting input** once the byte limit is reached.

**Exceeding the limit does not truncate — the entire attribute is ignored by Amazon Search.** This is specific to `generic_keywords` (`generic_keyword` in the Listings API). Every other keyword attribute indexes up to its limit and discards only the excess. Lead with this consequence when a user is over: they don't lose the tail, they lose *all* their backend keywords.

Note the one conflicting number in Amazon's own docs: error **97779** ("Generic keywords length exceeded") is documented at **200 bytes** while the keyword-attribute table says 249. Both are current. Practical guidance: **write to under 200 bytes** — it satisfies both, and the cost of being wrong (total loss of indexing, or a rejected feed) is far higher than the cost of a few unused bytes. If asked, say both numbers are published rather than asserting one. Error handling for 97779 is in `02-attributes-and-error-codes.md`.

**Bytes are not characters.** For ASCII (a–z, A–Z, 0–9) one byte is one character. Accented and non-Latin characters (German `ä`, etc.) cost **two or more bytes each**, so a German or Japanese keyword field hits the limit at far fewer visible characters. Count bytes, not characters, whenever the content isn't plain ASCII.

**Spaces and punctuation are not counted** toward the search-term length calculation. Separate terms with spaces for readability at no length cost. Punctuation is tolerated but not recommended.

**Format:**
- Space-separated, no commas, semicolons, colons, or dashes.
- All lowercase.
- Each individual word is independently searchable — order them in natural phrases (2–3 word phrases).
- Use synonyms, spelling variations, and abbreviations; avoid common misspellings.
- Use singular **or** plural, not both.
- Avoid repetition.
- Avoid articles, prepositions, and short filler words ("a", "an", "and", "by", "for", "of", "the", "with").

**Amazon's own example of an effective search-term field:**

```
cutting chopping board butcher block bamboo wood wooden large hybrid
polypropylene food grade plastic non slip kitchen dual sided surface
natural bpa stain scar resistant eco friendly drip groove
```

(Note this is Amazon's illustration of *format and density*. "eco friendly" appears in it, but environmental claims are restricted in customer-visible copy — see § 3. Backend terms are not customer-visible, which is why it survives here.)

### Required for 23 product types

Effective **December 6, 2023**, `generic_keywords` is a **required** attribute for these product types — an empty field is a submission failure, not merely a missed opportunity:

Art and craft supply · Artificial tree · Balloon · Bar tool set · Bath pillow · Bath safety seating · Bath toy · Bathroom container set · Bathtub shower mat · Beauty · Bed linen · Bed linen set · Bed skirt · Bedding set · Blanket · Board game · Body care product · Body deodorant · Body paint · Body positioner · Bookend · Broom · Party favor

**Do not include:**
- Words already in the title, bullets, brand, or product name (no value; redundant).
- Product identifiers: brand names, ASINs, UPCs, model numbers.
- Competitor brand names.
- Profanity, offensive terms, or terms promoting illegal activity or glorifying hatred, violence, or racial/sexual/religious intolerance.
- Inaccurate, misleading, or out-of-context words.
- Wrong category, wrong gender, wrong age group.
- Common misspellings (Amazon auto-corrects).
- Singular/plural variants (Amazon stems automatically).
- Spacing/punctuation variants ("80GB" and "80 GB").

**Amazon's published prohibited-word examples** — useful as a concrete screen when auditing a keyword field:

| Class | Examples |
|---|---|
| **Brand names** | Apple, Nike, Amazon — and the seller's own brand |
| **Temporary words** | available now, brand new, current, discounted, just launched, last chance, last minute, latest, limited time, new, on sale, this week/month/year, today |
| **Subjective words** | amazing, best, cheap, cheapest, effective, fastest, good deal, least, most, popular, trending |

**Violating these can suppress the ASIN and put selling-account health at risk.** Also note Amazon may decline to use supplied search terms for any reason, and judges term relevance automatically — relevance can change over time as Amazon gathers data.

**Where to edit:** Seller Central → Manage products → select product → Fix menu → Edit → Product details tab → Generic keyword field. For bulk updates, enable the Category Listing report (Inventory menu; Selling Partner Support can turn it on), download current listings, and apply an inventory file template using the **partial update** function.

**Sources for good keywords:**
- Customer review language for this listing and competitors.
- Brand Analytics: Search Query Performance, Top Search Terms.
- Search Catalog Performance (which terms drive impressions/clicks/conversions).
- Amazon search bar autocomplete suggestions.
- Google related searches for the product type.

---

## 6. Image rules

### Universal rules (all categories)

- File format: JPEG (preferred), TIFF, PNG, or GIF (static only; no animated GIFs).
- File size: ≤10MB (general); ≤2MB (A+ Content).
- Color space: RGB. CMYK is not supported.
- Resolution: ≥1000px on the longest side for zoom. **1600px+ recommended** for optimal zoom.
- Max: 10,000px on the longest side.
- DPI: ≥72.
- Product fills ≥85% of the image frame.
- Sharp, in focus, evenly lit, no jagged edges, no pixelation.
- No nudity, no sexually suggestive content.

### MAIN image (universal)

- Pure white background: RGB(255,255,255).
- Professional photograph (no drawings, illustrations, mockups, or placeholders).
- Shows only the product for sale.
- No text, logos, watermarks, graphics, color blocks, borders.
- No Amazon logos, trademarks, or look-alikes (no "Amazon", "Prime", "Alexa", Amazon Smile).
- No Amazon badges or look-alikes ("Amazon's Choice", "Premium Choice", "Best Seller", "Top Seller").
- Image must match the title.
- Up to 7 images total recommended; aim for at least 6 + 1 video.

### MAIN image — category specifics

| Category | Requirement |
|---|---|
| Shoes | Single shoe, facing left, 45° downward angle. Cropped backgrounds OK, but shoe should fill 85%+. |
| Women's & Men's clothing | Must show product on a human model, standing, natural pose. |
| Kids & Baby clothing | Lying flat on a surface — NOT on a human model. |
| Kids & Baby underwear/swimwear/tights | Lying flat, no human model. |
| Jewelry | Necklaces may be cropped; everything else fills 85%+. |
| Furniture | Pure white background, full product visible. Light-colored background acceptable for white-on-white products. |
| Thongs/panties | Front view as MAIN; back view as alternate. No human model if coverage is incomplete. |

### Auxiliary (PT01–PT08) images

- Show product in use, in environment, from multiple angles, with detail close-ups.
- Lifestyle imagery permitted.
- Text overlays permitted for infographics (sizing charts, feature callouts) — keep text large enough to read on mobile.
- Variation parents benefit from auxiliary images showing the range of color/size options.

### Apparel-specific image bans (MAIN image)

- No visible mannequins (exception: stockings/socks).
- No models kneeling, leaning, or lying down — standing only.
- No multiple poses of the same model.
- No multiple angles of the same product.
- No packaging, brand tags, or swing tags visible (exception: stockings/socks).
- No text/logos/borders/watermarks/graphics.

---

## 7. Brand name policy

**Three states:**

| State | Brand value | Notes |
|---|---|---|
| Branded, registered | The brand name as registered | If not yet Brand Registry-enrolled, may trigger a review |
| Branded, unregistered | The brand name | New brand names may need Amazon approval before listing |
| Unbranded | `Generic` | Literal string "Generic" — leaving it blank causes suppression |

**Error codes:**
- **5661** — Brand attribute likely abused (suggests brand value doesn't match product/packaging).
- **5664** — Listing is a general product but `Generic` not used.
- **5665** — Brand needs Amazon approval before listing.

**Resolution:** Open a Seller Support case with:
1. The brand name used in the listing.
2. Photo of the product/packaging showing the brand logo (must be permanent, must match the brand attribute exactly — does not need to be ASIN-quality, hand-held or table photo is fine).
3. If the listing was created via inventory file, the Batch ID of the processing report.

Amazon Support is not callable from this skill — give the user the info to file the case themselves.

---

## 8. Variation rules

### Categories that support variations

Apparel, Mother & Infant, Cosmetics, Cameras & Photo, Wireless Mobile Phones & Accessories, Electronics, Gift Cards (limited), Grocery, HPC, Home & Garden, Jewelry Accessories, Lights, Musical Instruments, Office Products, Pet Supplies, Shoes/Handbags/Sunglasses, Sports & Outdoors, Tools & Home Improvement, Automotive Parts & Accessories.

### Categories that do NOT support variations

Auto Tires & Wheels, Books, Personal Computers, Entertainment Collectibles, Industrial & Scientific (most subs), Music, Software & Video Games, Sports Collectibles, Toys & Games, Video & DVD, Watches, Misc.

### What makes a valid variation family

All children must be **the same product** differing only in specific attributes (size, color, scent, count, etc.).

Invalid examples:
- A charging cable and a portable charger (different products).
- A messenger bag and a tote bag in the same color (different products).
- Plate + bowl + cup tableware set (different products even if same pattern).
- Banners "rose gold white" / "black brown gray" / "blue gold silver" — those aren't valid color attribute values.
- A toddler harness with "different animal styles" — Baby category supports size/color, not style.

### Variation themes (most common)

| Theme | Use when |
|---|---|
| `SIZE_NAME` | Products vary only by size |
| `COLOR_NAME` | Products vary only by color |
| `SIZE_NAME/COLOR_NAME` | Products vary by both |
| `STYLE_NAME` | Products vary by style (limited category support) |
| `PATTERN_NAME` | Products vary by pattern |
| `SCENT_NAME` | Beauty/HPC products varying by scent |

### Common warnings

- **Code 8032** — child SKU assigned to multiple parents. Must delete and reassign.
- **Family count mismatch** — `catalog.childAsins` count ≠ `listings.childSkus` count → an orphan SKU.

---

## 9. Suppression triggers

A suppressed listing is invisible in search and browse. Common triggers:

### Universal triggers (all categories unless noted)

| Trigger | Exception categories |
|---|---|
| No main image | Automotive parts/accessories (some OEM), Industrial & Scientific, Books, Music |
| No brand attribute | Apparel, Automotive, Books, Jewelry Accessories, Music, Shoes, Software/Video Games, Video/DVD, Watches |
| No product description | (Same as above) |
| No bullet point | (Same as above) |
| Fewer than 3 bullet points | None — 3 is Amazon's stated minimum |
| Title over **75 characters** | Media product types; SA/EG/TR/AE stores. Elsewhere the title may be auto-corrected or dropped from search results |
| Title with prohibited characters, promotional content, or a word repeated 3+ times | None |
| Missing `product_type` value | Mother & Infant, Cosmetics, Books, Entertainment Collectibles, Artwork, Gift Cards, Grocery, Personal Care & Health, Music, Shoes/Handbags/Sunglasses, Software, Sports Collectibles, Video, DVD, Video Games, Watches |
| Missing valid UPC (when required) | None — category-dependent; check Product ID (GTIN) requirements |

### Category-specific child-SKU triggers (Apparel & Accessories)

**Shoes** children missing: `Department`, `Size`, or `Color` value.

**Watches & Luggage** children missing: `Department` value.

**Jewelry** children: missing/invalid `Department` (except Jewelry Accessories); missing `Material Type` / `Metal Type` / `Gem Type` / `Pearl Type`; missing UPC (for major jewelry brands).

**Consumables** (Grocery, Beauty, Pets, Health & Personal Care) children: missing unit count and value.

### Image-based suppression

- MAIN with non-white background (Apparel/Shoes/Watches/Jewelry/Luggage).
- MAIN with text/logos/borders/watermarks/graphics over product or background.
- MAIN showing multiple views/poses of one product.
- MAIN showing product in packaging or with swing tags (exception: stockings/socks).
- MAIN with model kneeling, leaning, or lying down.
- MAIN with visible mannequin (exception: stockings/socks).
- MAIN with Kid/Baby tights/underwear/swimwear on a human model.
- Blurry, pixelated, or jagged-edged images.
- Product fills less than 85% of image when zoomed.

### How to check

`listings_getListingsItem` `includedData=['issues']` surfaces active warnings. The Listing Quality Dashboard in Seller Central shows suppression status, and **Manage All Inventory → Search suppressed and inactive listings** lists suppressed items directly.

### Suppression is not the only reason a listing is unsearchable

A compliant, unsuppressed listing can still be absent from search results — no buyable offer, no browse node, a future launch date, or adult classification. Those are diagnosed differently and are covered in `03-search-optimization.md`. Don't report "not suppressed" as "should be searchable."

---

## 10. Prohibited content (universal)

Never include in titles, bullets, descriptions, or images:

- Pornographic, obscene, or offensive content.
- Requests for positive customer reviews.
- Reviews, quotes, or testimonials (except in A+ — limited).
- Phone numbers, mailing addresses, email addresses, website URLs.
- Advertisements, promotional material, watermarks.
- Time-sensitive information (dates of events, tours, seminars).
- Availability, price, condition, alternative ordering info, free delivery offers.
- Spoilers for Books, Music, Video, DVD.
- Restricted Products content.
- Safety standard violations.
- HTML, JavaScript, or other executables (line break `</br>` is the only exception, and only in descriptions).
- Symbols: `~`, `!`, `*`, `$`, `?`, `_`, `{`, `}`, `[`, `]`, `#`, `<`, `>`, `|`, `^`, `°`.
- Emoji.

---

## 11. EU DSA compliance

The EU Digital Services Act (DSA) Article 30 requires online marketplaces to display verified contact information for the trader behind each product. Amazon enforces this via the `dsa_responsible_party_address` attribute on each listing.

**Requirements:**
- Must be a real **physical postal address** — not just an email or phone number.
- Address must be traceable (registered office, fulfillment center, or business address).
- Required for products sold in any EU marketplace (DE, FR, IT, ES, NL, PL, SE, BE).
- Amazon increasingly populates this attribute on US-marketplace listings too — the policies are converging globally, and many US sellers also list in EU.

**Common violations:**
- Field set to just an email (e.g., `support@brand.com`) — fails DSA verification.
- Field set to a P.O. box without a registered physical office behind it — may fail verification.
- Field left blank when the listing also exists in an EU marketplace — suppression risk.
- Address belongs to a different legal entity than the seller of record — fails verification.

**Diagnosis pattern:**
If `catalog.attributes.dsa_responsible_party_address[0].value` contains `@`, a URL fragment, or anything that isn't a postal address, the listing has a compliance gap.

**Resolution:**
Don't patch this without the user providing the correct postal address. Wrong addresses are worse than missing ones — they create false compliance signals. Surface the gap to the user, get the correct address, then preview the patch.

The attribute name is `dsa_responsible_party_address`; the value shape varies by product type. Check the structured `attributes` block in `listings_getListingsItem` for the current shape on the listing being edited.

---

## 12. Listing hijacking & tamper detection

A listing's copy can be altered by someone other than the legitimate owner —
a hijacker on a shared/variation listing, a compromised account, or a bad actor
exploiting a contribution path. The injected content is designed either to **get
the listing suppressed** (so a competitor's offer wins) or to **destroy buyer
trust**. This is a security signal, not a copy-quality issue — treat any hit as
**critical** and surface it before anything else.

**Scan these fields:** title, all 5 bullets, product description, and backend
search terms (`generic_keyword`). Hijackers hide injected text in low-visibility
fields (bullet 5, search terms) as often as in the title.

**Three categories to look for:**

| Category | What it looks like | Examples (illustrative, not exhaustive) |
|---|---|---|
| **Adult / sexual content** | Explicit terms wedged into an unrelated product | "sex toy", "dildo", "vibrator", "butt plug", "bondage", "fetish", "erotic", "masturbat*" |
| **Abusive / offensive language** | Profanity or slurs intended to force a policy takedown | "f***", "s***", "b****", slurs, "c***" |
| **Sabotage phrases** | Trust-destroying claims aimed at the buyer | "do not buy", "don't buy", "scam", "fake product", "counterfeit", "knockoff", "stolen", "not genuine", "not authentic", "not original", "seller is fake" |

**Judge in context — avoid false positives.** Match on intent, not raw substring.
"Damascus steel" is not a slur; "class" contains "ass"; "damn good" in a legitimately
edgy brand voice is not sabotage. A medical or anatomy product may legitimately use
clinical terms. Use word boundaries and surrounding meaning before flagging.

**What to do when you find it:**
1. **Stop and surface it immediately** — lead the review with it. Do not silently
   rewrite the field; the user needs to know their listing was tampered with.
2. **Frame it as a possible compromise**, not a typo. Advise the user to check the
   listing's change history, who has account/contributor access, and whether the
   ASIN is shared across sellers or part of a variation family a hijacker joined.
3. **Escalation is the user's.** Securing the account, reporting the hijacker, and
   opening an Amazon abuse/IP case are user actions — this skill diagnoses and
   drafts the clean replacement copy, but does not contact Amazon.
4. Only after the user confirms, draft the cleaned field and run it through the
   normal preview → confirm → submit edit loop.
