# Reproducible theme comparisons

Use this for multi-query analysis. These are configurable analyst triage conventions, not Amazon thresholds, statistical significance tests or lift predictions. Assess full-query relevance and compatible product needs first; the helper trusts those supplied assessments and cannot infer compatibility from tokens.

## Input and helper

Run from this skill's directory:

```sh
python3 scripts/rollup_sqp.py --input INPUT.json --output OUTPUT.json
```

Python 3.10+, standard library only. Input is normalized JSON, not an arbitrary Seller Central export. Parse the export with the [metric definitions](sqp-metrics.md), retaining the source report separately. Never substitute Amazon's reported rate fields for counts. Input has `config` (optional overrides) and `rows`:

```json
{
  "config": {},
  "rows": [{
    "row_id": "q1", "marketplace_id": "ATVPDKIKX0DER", "asin": "B0TESTBED01",
    "period": "WEEK", "start": "2026-10-04", "end": "2026-10-10",
    "query": "large dog bed", "query_volume": 2000, "relevance": "exact",
    "market": {"impressions": 4000, "clicks": 200, "cart_adds": null, "purchases": 20},
    "asin_counts": {"impressions": 400, "clicks": 40, "cart_adds": null, "purchases": 2}
  }]
}
```

Apply explicit user corrections before passing input to the helper. Never report an earlier rollup beside a later missing-data hold; regenerate affected tables from the corrected rows. Counts and query volume are nonnegative integers or null; missing counts stay unknown rather than zero. Preserve `searchQueryScore`, reported rates, prices and evidence in diagnostic records outside this helper. `relevance` accepts exact, substitute, complement, irrelevant, unknown. Optional `tokens` supplies language-appropriate tokens. Default is Unicode NFKC/casefold and whitespace splitting, with punctuation retained; it is unsuitable for unsegmented languages unless tokens are supplied. Keep original query text. Do not strip negation, units, model numbers or size constraints.

Reject inconsistent scopes, conflicting duplicate data, and ASIN counts exceeding known same-stage market totals before comparison. Different-stage event counts, such as purchases exceeding clicks, remain valid ratios with interval limitations. Complete WEEK is Sunday–Saturday; MONTH and QUARTER must be a single complete period. When an export lacks marketplace, obtain request metadata or ask. Resolve missing/conflicting counts before rerunning the affected comparison; continue unaffected scopes separately.

## Aggregation

1. Separate `(marketplace_id, period, start, end, asin)` scopes. Deduplicate normalized query rows within a scope, including repeated imports with another row ID. Conflicting duplicates require repair. Query-wide market counts and volume must agree across ASINs; per-ASIN comparisons never sum different ASIN copies.
2. Generate contiguous 1/2/3-grams, one contribution per source query to each gram. Skip-grams and semantic clustering are not implemented. Do not pool incompatible needs just because they share a token; analyze compatible slices separately and document membership.
3. Keep exact and substitute cohorts separate; show excluded/unknown members. A mismatched member does not exclude an eligible theme. All-ineligible/unknown themes remain discoverable in returned `rows` even when there is no eligible rollup.
4. Sum counts, then divide. Unknown constituents make the affected sum/ratio unavailable. Each theme compares its ASIN counts against market counts for the same members and against the **disjoint remainder** of the same relevance slice and ASIN/report scope, with its own market comparison.
5. Alias grams with identical complete membership and relevance. The helper chooses the longest phrase then lexical order; choose the most meaningful alias for display and retain the rest. Never combine different exclusion sets silently.
6. Overall reach comes from the union of rows (`scope_totals`), never the sum of overlapping themes. Market totals in different ASIN scopes are repeated benchmarks, not additive portfolio totals.

The helper output is supporting analysis, not the seller-facing answer. Present it using the [seller-answer contract](decision-records.md).

The helper returns `schema_version: "2.1"`, effective thresholds, original normalized rows, duplicate provenance, scope totals, and theme rollups. It performs arithmetic, not evidence assessment or copy recommendations. Use [decision records](decision-records.md) next.

## Gates and uncertainty

| Configuration | Default | Meaning |
|---|---:|---|
| `minimum_market_impressions` | 200 | Sum of market query impressions over unique compatible members |
| `minimum_asin_clicks` | 20 | Pooled ASIN clicks |
| `minimum_queries` | 3 | Distinct queries for recurring-theme comparison |
| `minimum_asin_purchases` | 5 | ASIN purchases in each cohort; also require positive market clicks and purchases |
| `dominant_click_fraction` | 0.70 | Above this, recompute the theme without its leading query |
| `maximum_theme_index` | 0.80 | Candidate theme's ASIN/market purchase-per-click index at most this |
| `minimum_remainder_index` | 1.00 | Remainder's index at least this |

Volume requires both impressions and clicks. Theme and remainder must pass volume, recurrence and purchase gates for a localized-gap candidate. Pool thin rows before these tests. A dominant query requires the remaining theme to pass all gates and its index threshold; otherwise do not claim recurrence. Report offsetting winners/losers, not just aggregate weakness. Broad weakness in theme and remainder, or no valid remainder, does not establish a localized content problem.

In supporting output, retain 95% Wilson intervals for ASIN purchase-per-click in theme and remainder. For `p = purchases/clicks`, `z = 1.959963984540054`, center is `(p + z²/(2n))/(1+z²/n)` and half-width is `z*sqrt(p*(1-p)/n + z²/(4n²))/(1+z²/n)`. These are descriptive binomial approximations: SQP event counts do not establish independent click trials. They are unavailable for unknown counts, zero clicks or purchases exceeding clicks; retain valid event ratios and disclose that limitation. Never cap counts to force an interval.

In decision text, explain the practical consequence of uncertainty in everyday language: small purchase counts can make an apparent difference unstable, so the numbers alone do not establish a lasting problem or justify a rewrite. Keep interval values and whether they overlap in the supporting calculations; neither overlap nor non-overlap alone proves a reliable effect. Gates and intervals do not prove causation or justify a content edit without a verified gap. For the size fixture, 6/120 has an interval of 2.3–10.5%, and 12/120 has 5.8–16.7%: the edit is supported by missing confirmed dimensions, not established performance harm.

Without Python, follow the same grouping/summing/gating recipe in a spreadsheet or equivalent arithmetic tool; report calculation limitations rather than inventing intervals. Keep membership IDs and effective thresholds so the result can be reproduced.
