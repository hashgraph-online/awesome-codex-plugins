# Amazon returns analysis template

Adapt depth and presentation to the request. Omit sections that the source does
not support, but state material omissions and their effect.

## 1. Scope and provenance

Include:

- seller account label or redacted identifier when known;
- marketplace and fulfillment channel;
- requested and observed date coverage with timezone;
- source report types or file names;
- row grain and unit definition;
- comparison period, if any; and
- whether the analysis used fresh or previously validated normalized data.

## 2. Headline

Report available counts in a compact table:

- return units or return requests;
- unique ASINs, SKUs, and orders;
- compatible shipped units, if available;
- portfolio rate with numerator, denominator, and method label; and
- change versus a comparable prior period.

If there is no denominator, use counts and `share_of_returns`; do not display a
return rate.

## 3. Product priorities

Rank ASINs or SKUs using the user's threshold or the stated watch-list method.
For every listed item show the evidence that is available:

| Field | Requirement |
|---|---|
| ASIN and SKU | Preserve both when present |
| Title | Truncate only for presentation |
| Return units or requests | State the unit |
| Denominator and rate | Show sample size and method label, or `N/A` |
| Change | Use a comparable prior period only |
| Leading raw reason/disposition | Do not replace with an inferred cause |
| Priority rationale | Explain the ranking method |

Keep low-denominator rate outliers separate from high-impact products. If no
product meets a user-defined threshold, show a watch list only when it adds
decision value.

## 4. Return evidence

Include only supported views:

- raw reason distribution;
- detailed disposition and status distributions for FBA;
- ASIN/SKU concentration;
- daily or weekly trend;
- fulfillment-center distribution; and
- bounded, redacted comment themes.

Label inferred themes and causal hypotheses. Do not translate an Amazon value
into an action category without a disclosed mapping.

## 5. Prior-period comparison

When comparable data exists, show current, prior, absolute change, and relative
or percentage-point change as appropriate for:

- total returns;
- properly defined return rate;
- product concentration;
- leading raw reasons and dispositions; and
- products entering or leaving the priority list.

If coverage or definitions differ, explain the mismatch and avoid a direct
comparison until normalized.

## 6. Reimbursement review candidates

Include this section only when the request or evidence makes it relevant.

Return-report disposition/status discrepancies are review signals, not claims.
Show:

- candidate records or units;
- the exact selection rule;
- reimbursement or ledger matches, if available;
- excluded and unresolved records; and
- additional evidence required before estimating eligibility or value.

Never label a simple damaged-minus-reimbursed calculation as money owed.

## 7. Recommendations

For each recommendation, provide:

1. **Observed signal:** the measured pattern and source.
2. **Scope:** concrete ASINs, SKUs, or cohort.
3. **Hypothesis:** the possible explanation being tested.
4. **Action:** the proposed intervention or investigation.
5. **Expected impact or priority rationale:** quantify only when the assumptions
   are supportable.
6. **Confirmation evidence:** the future metric or evidence that would support
   or refute the hypothesis.

Rank by expected impact when it can be estimated; otherwise state the ranking
criteria. Keep facts and recommendations in separate sections.

## 8. Data quality and methodology

Disclose:

- rows read, accepted, skipped, and duplicated;
- quantity and row-grain decisions;
- applied column map and missing fields;
- delimiter, compression, encoding, and parse issues;
- nulls in key identifiers and analytical fields;
- actual date coverage and partial periods;
- unmapped source values;
- rate numerator, denominator, method, and join quality; and
- privacy redactions or omitted sensitive fields.

## Empty-result template

For a completed zero-row report, return only:

1. the empty result;
2. the confirmed scope and report status;
3. actual coverage or freshness information available;
4. checks for marketplace, channel, dates, and account; and
5. a concrete re-pull or upstream-data next step.

Do not render empty product, reason, trend, or recommendation sections.
