# Review Requests performance review

A read-only review of Review Requests results. It builds one unified v1
report, derives cost-per-review figures, and interprets them within what the
product can and can't do.

## 1. Scope

- **Campaigns.** List the Review Requests campaigns with `goalFilter`
  `ENGAGEMENT` (see [api-calls.md](api-calls.md#queries)) and keep their IDs,
  names, daily budgets, bids, and states.
  - Always filter the report to these IDs. A report scoped only to
    `SPONSORED_PRODUCTS` mixes in the account's ordinary SP campaigns.
  - If the server rejects `ENGAGEMENT` (see
    [the known server gap](api-calls.md#known-server-gap-checked-2026-10-28)),
    ask the user for the campaign IDs.
  - In that case, budgets come from the user or the console. Without them,
    report budget utilization as `N/A`; the review metrics don't depend on
    them.
- **Account.** Unified v1 reporting needs the advertiser account ID
  (`amzn1.ads-account.g.…`), not the numeric profile ID. Map the profile to
  the account with `allv1_QueryAdvertiserAccount` (`alternateIds`) or
  `amazon-ads-accounts`.
- **Period.** Use the user's dates. Otherwise propose the last 30 complete
  days, and say that the most recent days may still be filling in: reviews
  pass moderation before they post, and Amazon doesn't document the
  attribution window for these metrics.

## 2. Build the report

When `amazon-ads-reporting` is installed, use its ad-hoc path: field
discovery, validation, submission, polling, and download. Otherwise follow the
same shape: `accessRequestedAccounts` plus one `reports[]` entry with
`format`, `periods`, and `query`.

What to request:

| Purpose | Fields (confirm names in the live catalog) |
|---|---|
| Time | exactly one time dimension: daily for budget-utilization checks, otherwise a summary over the range |
| Level of detail | campaign ID and name. For per-ASIN results, add the ad-level or advertised-product dimension if the catalog allows it alongside the review metrics. |
| Delivery | impressions, clicks, cost/spend, and the currency dimension the catalog requires for money |
| Review metrics | `reviews`, `writtenReviews`, `ratingOnlyReviews`, `percentOfReviewsWritten`, `averageStarRating` |
| Filter | ad product `SPONSORED_PRODUCTS` **and** campaign ID in the Review Requests campaign IDs |

Amazon names the five review metrics without prefixes. Unified v1 report
fields are usually namespaced (`metric.impressions`), so `metric.reviews` and
so on are the likely names. Confirm them in the catalog rather than assuming.

CreateReport validates the whole field set and rejects a bad one with a 400
that names each problem, before creating anything. Fix the list from that
error and resubmit. If the catalog has no per-ASIN grain that works with the
review metrics, report at campaign level and say so. Don't approximate
per-ASIN numbers.

Creating a report job changes nothing in the account and needs no approval.
Before submitting, state the account, period, fields, and filter. Keep the
report ID so a later turn can resume retrieval.

## 3. Derived metrics

| Metric | Formula | When undefined |
|---|---|---|
| Cost per review | spend ÷ `reviews` | `N/A` when `reviews` = 0. Report spend with no reviews as its own finding. |
| Cost per written review | spend ÷ `writtenReviews` | `N/A` when 0 |
| Written share | `writtenReviews` ÷ `reviews`, checked against `percentOfReviewsWritten` | Amazon's field is canonical. Flag a gap of more than 1 percentage point. |
| Rating-only share | `ratingOnlyReviews` ÷ `reviews` | `N/A` when 0 |
| Card click-through | clicks ÷ impressions | `N/A` when 0 impressions |
| Reviews per 1,000 impressions | `reviews` ÷ impressions × 1,000 | `N/A` when 0 impressions |
| Budget utilization (per day) | that day's spend ÷ that day's daily budget | Needs daily grain. The budget comes from the campaign query, which shows the current value; say so if it may have changed during the period. |
| Average cost vs bid | spend ÷ clicks, compared with the bid | Average cost above the bid is unexpected. Flag it. |

**Combining rows:**

- **Star rating across campaigns or ASINs:** weight each row's
  `averageStarRating` by its `reviews`. Never average the averages.
- **Billable clicks vs reviews:** the billable click *is* a rating or review
  left on the card, so `clicks` and `reviews` should be close. If they differ
  materially, show both. Don't explain the gap with a guess; attribution and
  timing may differ between the fields.

## 4. Interpretation rules

Keep three things apart:

- **Observations:** numbers, each with its formula and period.
- **Hypotheses:** possible causes, labeled as such.
- **Proposals:** reversible changes the user can approve through the skill's
  manage flow.

What these results mean:

- **The card reaches only recent verified purchasers.** Volume is capped by
  how many people bought and received the product. Low impressions on a
  low-sales ASIN usually reflect few eligible shoppers, not a bid problem,
  and raising the bid can't create purchasers. Say this before proposing a
  bid increase.
- **Budget-capped.** If spend reaches the daily budget on most days, more
  reviews may be available at a higher budget. Show the arithmetic:
  - At the observed cost per review, each extra $X/day buys about
    X ÷ cost-per-review more reviews per day.
  - State the threshold you used (for example, "spend ≥ 95% of budget on
    ≥ 70% of days"). It is a working rule, not an Amazon standard.
- **Under-delivering.** If spend stays well below budget, the bid may be too
  low to win the card, or there may be few eligible purchasers. These are
  two hypotheses. Use sales context if the user has it.
- **The star rating is honest product feedback.** Review Requests speeds up
  reviews of every kind; it doesn't make them better.
  - If an ASIN's `averageStarRating` is low, or below the listing's current
    rating, the ad is speeding up negative reviews. Propose pausing that
    ASIN's ad while the product, packaging, or listing accuracy is fixed,
    and suggest checking returns and customer feedback.
  - Never propose ways to influence ratings or choose which shoppers are
    asked. Both are impossible in this product and against Amazon's
    Community Guidelines.
- **ASINs at 1,000 reviews pause on their own.** The Ads API can't show a
  product's total review count. If an ad stopped delivering partway through
  the period, list "reached 1,000 ratings and reviews" as one hypothesis and
  ask the user to check.
- **Attributed reviews are not total reviews, and not lift.** The report
  counts ratings and reviews left on the card. Organic reviews continue
  separately. Without a control period or group, don't claim the campaign
  caused an increase in total reviews.

## 5. Output template

```
# Review Requests performance: <account name>, <start> to <end> (UTC dates)

Scope: advertiser account <amzn1.ads-account.g.…> (profile <id>, US) ·
<n> Review Requests campaigns · report <reportId> · grain <daily|summary> ·
fields <exact list>

## Headline
Spend $<x> · <reviews> ratings and reviews (<written> written, <rating-only>
rating-only; <pct>% written) · average <stars>★ (weighted by reviews) ·
$<cpr> per review · $<cpwr> per written review

## By campaign
| Campaign | State / delivery | Budget/day | Bid | Spend | Reviews | Written % | Avg ★ | $/review | Budget-capped days |

## By ASIN   (or: "Not available: <reason>")
| ASIN | Ad state | Spend | Reviews | Written % | Avg ★ | $/review |

## Observations
- <fact, with formula, period, and source field>

## Hypotheses
- <possible cause, labeled>

## Proposed changes (nothing has been changed)
- <change, evidence, expected effect, the call it needs>. Say "yes" to
  apply it through the approval gate.

## Data notes
- <N/A fields and why; any missing per-ASIN grain; recent days possibly
  incomplete; current budget used for utilization>
```
