# Theme decisions and exact proposals

Default to at most three distinct decisions, adjustable by the user. Each decision selects one primary change. A table of diagnostic states or an investigation checklist does not count as a recommendation.

## Seller answer: what to change → why → what to watch

Use short, connected paragraphs. The seller must be able to choose without reading the supporting analysis. Adapt the same structure to the outcome:

| Outcome | What to change | Why | What to watch or supply |
|---|---|---|---|
| Supported edit | Name the listing location in ordinary words and give the exact replacement text. | Explain the verified information problem and use only the few numbers that matter. Explain uncertainty through its effect on this decision. | Name one relevant measure and the searches to follow over complete reporting weeks. |
| No change | Say to keep the relevant content as it is. | Explain that it already answers the shopper's need; weak numbers alone do not reveal a missing fact or justify a rewrite. | State what new evidence would justify revisiting it only if useful. Do not manufacture a monitoring task or another investigation. |
| Missing evidence | Ask for the one fact or piece of listing content that blocks the choice. | Explain what it would let you decide. | Say how that answer changes the next step. Do not present an unverified edit alongside the request. |

For example:

- Edit: “Replace the first bullet with ‘Large size: 40 × 30-inch sleeping surface.’ Buyers need the dimensions to judge the fit. The purchase counts are small, so they do not yet establish a lasting sales problem. After the edit, watch purchases per 100 clicks from the same large-bed searches over full weeks.”
- No change: “Keep the size bullet. It already gives the confirmed 40 × 30-inch dimensions. The small purchase difference does not give us a reason to rewrite it.”
- Missing evidence: “Please confirm this bed's sleeping-surface dimensions. The bullet says 36 × 24 inches, while the catalog says 40 × 30. That will tell us whether the bullet needs correcting.”

These are examples of the explanation, not numbers or conclusions to reuse. State relevant uncertainty honestly, with its practical consequence: a few purchases could change an apparent difference, so it is too early to treat it as a lasting problem. Do not imply that overlapping ranges prove no difference, or that a verified information gap proves lost sales. Do not turn clicks into unique shoppers.

Keep internal labels, statistical methods and API syntax out of the default seller answer. Say “searches containing large”, “other relevant searches”, “first bullet”, and “purchases per 100 clicks” rather than “theme cohort”, “disjoint remainder”, `bullet_point[0]`, or unexplained indices. If the user asks for technical detail, define unfamiliar terms and explain why they matter.

Mention a limitation in the main answer only when it changes the recommendation or how the seller should judge it. Missing cart-add data, unavailable images, scope IDs, the full threshold list and unchanged listing fields usually belong in supporting records. Do not append a blanket caution paragraph or a list of work that was not performed. Clearly propose an edit without implying it has been applied.

## Supporting records

Keep the complete calculations and handoff separate from the seller answer: raw/reported values, count-derived ratios, effective thresholds, uncertainty intervals, query membership, source dates and coverage, unavailable calculations, decision codes and exact API selectors. Save them as a separate artifact when supported, or a clearly separated appendix when an audit is requested. Do not automatically paste the full appendix into a routine recommendation. The main answer must stand alone; do not make the seller open a file to discover the proposed change or its reason.

Requirements below and in metric/QA references to record, display or disclose technical fields apply to these supporting records unless they materially affect the seller's decision. Preserve all data-quality safeguards; simplify their explanation, not the analysis. Explicit requests for full diagnostics or structured output still receive those fields.

## Evidence before action

Fetch available decisive evidence once per ASIN/marketplace and reuse it. Record source, date, coverage and confirmation status separately for product facts and listing presentation. Catalog is useful discovery evidence but merges multiple sources: disagreement with a listing does not prove the listing is wrong. `product_fact_correction` requires a seller-confirmed specification or the user's explicit confirmation for this variant. Repetition of the disputed listing claim is not independent confirmation. Otherwise return `hold_missing_evidence` naming the single fact to confirm.

Absence requires complete relevant fields: a complete title/bullet read can establish omission there, not across the entire PDP. Image claims require images; unavailable A+ or images do not become defects. Current evidence is not historical listing evidence. A proposed omission edit must use supported product facts and remain within inspected fields. If dimensions already appear clearly, do not add them again just because the cohort underperforms.

## Precedence

Apply full-query relevance first. Mixed themes keep eligible exact/substitute slices and list excluded members. One mismatched query never excludes the whole eligible theme.

| Condition | Decision | Output |
|---|---|---|
| Invalid scope/counts or comparison-affecting conflict | `hold_invalid_input` | One repair needed; continue unaffected analysis |
| All members known complement/irrelevant, none eligible or unknown | `exclude_theme_targeting` | Unsupported needs and member IDs |
| Seller/user-confirmed fact contradicts listing | `product_fact_correction` | Exact correction even with thin SQP; performance impact unproven |
| Unconfirmed catalog/listing conflict, or only unknown members | `hold_missing_evidence` | One fact to confirm |
| Recurring localized candidate plus verified specific omission/ambiguity | `listing_content_test` | One exact draft, uncertainty disclosure and cohort measure |
| Adequate theme, decisive product/listing evidence unavailable | `hold_missing_evidence` | One missing fact/read, after attempting available retrieval |
| Insufficient counts/recurrence | `hold_insufficient_data` | Failed gate and observations needed |
| Complete relevant evidence but no supported change | `no_change` | Brief explanation; preserve already useful content |

An inferred use case alone cannot qualify. Substitutes may warrant truthful clarification, never copy pretending to meet an unmet requirement. Observed weaker purchases do not require inventing a remedy. Read [ASIN rules](asin-rules.md) for secondary offer/operations findings.

Sort actions: confirmed corrections, then supported content tests; within each class by affected ASIN clicks descending, query volume descending (missing last), theme and ASIN lexical ties. Deduplicate same-field/fact proposals: prefer the more specific supported theme, then clicks, then lexical order. Preserve aliases and union membership rather than summing duplicated reach. Keep hold codes in supporting records; explain the blocker in ordinary words. Default to no action if none qualifies.

## Additive contract 2.1

Use one `schema_version: "2.1"`. Retain 2.0 diagnostic record fields and meanings (`reported`, `derived`, `product_evidence`, `relevance`, `intent_hypotheses`, `qa`, `priority`, `observations`, `recommendations`, report/scope/query/ASIN). A diagnostic recommendation may remain conditional; it does not automatically become an actionable theme decision. Empty recommendations are valid. Version 2.0 consumers must accept the new schema tag before reading additive fields.

In the structured supporting output, add `theme_rollups` (helper output) and `theme_decisions`. Each decision includes:

- Stable theme ID (scope + gram + relevance), member IDs and aliases; decision class.
- Evidence references with source/confirmation and coverage; before text, exact after text or concrete image brief; observed gap and bounded rationale.
- Selector: ASIN, seller SKU when known, marketplace, Amazon attribute (such as `bullet_point`), zero-based array index and language tag. Missing seller SKU can be resolved by the owning skill before a write; never guess it. Asset proposals name the actual observed slot/asset.
- Cohort counts, named-denominator ratios, Wilson intervals and uncertainty statement, effective thresholds; affected traffic explains priority without projected lift.
- Single blocker for holds; comparable complete periods and an affected-cohort measure for tests, with concurrent changes recorded.

Example proposal selector: `{"asin":"B0TESTBED01","sku":"BED-L","marketplace_id":"ATVPDKIKX0DER","attribute":"bullet_point","index":0,"language_tag":"en_US"}`. The listing optimizer re-reads that entry and validates the marketplace/product-type attribute schema before an approved write. The index is a proposal locator, not permission to overwrite a changed array blindly.

Hand a user-selected proposal to `amazon-sp-listing-optimizer` when available. Preserve its preview/approval flow. This skill performs analysis and drafting only.
