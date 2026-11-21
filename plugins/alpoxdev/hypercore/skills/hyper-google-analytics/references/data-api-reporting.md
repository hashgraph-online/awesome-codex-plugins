# Data API Reporting

Read this reference for an `analyze` run that answers a question from report data. It owns the method choice, the name checks that run before a request is sent, the request recipes for the common questions, the row limit, the quota budget, and the data-quality flags every result must carry.

> Korean version: [`data-api-reporting.ko.md`](data-api-reporting.ko.md)

## Contents

- Method choice
- Names before tokens
- Request recipes
- Row limit and response shape
- Quota budget
- Data-quality flags
- Reporting rule

## Method choice

| Question shape | Method | Version |
|---|---|---|
| One report over one date range | `properties.runReport` | v1beta |
| Up to five reports in one HTTP call | `properties.batchRunReports` | v1beta |
| A pivoted table, or several pivots in one call | `properties.runPivotReport`, `properties.batchRunPivotReports` | v1beta |
| The last few minutes | `properties.runRealtimeReport` | v1beta |
| Which dimension and metric names the property accepts | `properties.getMetadata` | v1beta |
| Whether two or more dimensions and metrics can be asked together | `properties.checkCompatibility` | v1beta |
| A funnel with explicit steps | `properties.runFunnelReport` | v1alpha only |

- `runFunnelReport` is "introduced at alpha stability with the intention of gathering feedback on syntax and capabilities before entering beta". Treat it as a separate decision from the v1beta surface: on a production property whose report must be repeatable, build the funnel from `runReport` over `eventName` instead, and say in the report that the alpha method was the rejected option and why.
- `batchRunReports` saves round trips, not quota. "Each report in a batch still counts individually toward token and `concurrentRequests` quotas", so a batch of five costs five reports' worth of tokens.
- `runPivotReport` is the right surface for a two-dimensional cross-tab; `runReport` plus an `orderBys` chain is not a substitute because it cannot pivot.

## Names before tokens

Every request spends quota tokens, and a rejected dimension name spends them too. Resolve names first.

1. Call `getMetadata` once per property per run: `GET https://analyticsdata.googleapis.com/v1beta/properties/<property_id>/metadata`. Keep the returned dimension and metric names for the rest of the run instead of asking again.
2. For a dimension-and-metric combination this run has not used, call `checkCompatibility` first: `POST https://analyticsdata.googleapis.com/v1beta/properties/<property_id>:checkCompatibility` with the same `dimensions` and `metrics` arrays the report will send. An incompatible pair is settled before a report request is built.
3. A display name in the GA4 UI is not an API name. `Session default channel group` in the UI is `sessionDefaultChannelGroup` in the request, and the metadata response is the authority on which spelling the property accepts.
4. Custom definitions use a prefixed grammar, not the name that was typed in the UI:

| Definition | Name in a request |
|---|---|
| Event-scoped custom dimension | `customEvent:<parameter>` |
| User-scoped custom dimension | `customUser:<parameter>` |
| Event-scoped custom metric | `customEvent:<metric>` |
| Event-scoped custom metric reported as an average | `averageCustomEvent:<metric>` |
| Key event rate for one event | `sessionKeyEventRate:<eventName>` |
| Custom channel group | `customChannelGroup:<id>` |

5. A name that returns an error from `getMetadata` is reported as a missing definition with the name that was asked, never retried with a guessed spelling.

## Request recipes

All bodies go to `https://analyticsdata.googleapis.com/v1beta/properties/<property_id>:<method>` with the ADC bearer token. Every body below sets `returnPropertyQuota` so the response reports what the request cost.

### Traffic by channel

Answers "where did the sessions come from this month".

```json
{
  "dateRanges": [{"startDate": "2026-10-01", "endDate": "2026-10-31"}],
  "dimensions": [{"name": "sessionDefaultChannelGroup"}],
  "metrics": [
    {"name": "sessions"},
    {"name": "totalUsers"},
    {"name": "engagedSessions"},
    {"name": "keyEvents"}
  ],
  "orderBys": [{"metric": {"metricName": "sessions"}, "desc": true}],
  "limit": 25,
  "returnPropertyQuota": true
}
```

`sessionDefaultChannelGroup` answers the channel question; `sessionSource` and `sessionMedium` answer "which source inside that channel" and are a second request, not a wider first one.

### Landing pages

Answers "which entry pages produced engaged sessions and key events".

```json
{
  "dateRanges": [{"startDate": "2026-10-01", "endDate": "2026-10-31"}],
  "dimensions": [{"name": "landingPage"}],
  "metrics": [
    {"name": "sessions"},
    {"name": "engagementRate"},
    {"name": "keyEvents"},
    {"name": "sessionKeyEventRate"}
  ],
  "orderBys": [{"metric": {"metricName": "sessions"}, "desc": true}],
  "limit": 50,
  "returnPropertyQuota": true
}
```

Use `landingPage`, not `pagePath`, for an entry-page question. `pagePath` counts a page every time it is viewed, including mid-session, so it answers a different question and produces a larger number.

### Key event rates

Answers "which events convert, and at what rate".

```json
{
  "dateRanges": [{"startDate": "2026-10-01", "endDate": "2026-10-31"}],
  "dimensions": [{"name": "eventName"}],
  "metrics": [
    {"name": "eventCount"},
    {"name": "keyEvents"},
    {"name": "sessionKeyEventRate"}
  ],
  "orderBys": [{"metric": {"metricName": "keyEvents"}, "desc": true}],
  "limit": 100,
  "returnPropertyQuota": true
}
```

`sessionKeyEventRate` needs the event name as a suffix when one event's rate is the question: `sessionKeyEventRate:purchase`. Asking for the bare metric returns the property-wide rate, which is a different number.

### Ecommerce funnel

Answers "where the purchase path drops".

```json
{
  "dateRanges": [{"startDate": "2026-10-01", "endDate": "2026-10-31"}],
  "dimensions": [{"name": "eventName"}],
  "metrics": [
    {"name": "eventCount"},
    {"name": "addToCarts"},
    {"name": "checkouts"},
    {"name": "ecommercePurchases"},
    {"name": "purchaseRevenue"}
  ],
  "dimensionFilter": {
    "filter": {
      "fieldName": "eventName",
      "inListFilter": {
        "values": ["view_item", "add_to_cart", "begin_checkout", "purchase"]
      }
    }
  },
  "limit": 10,
  "returnPropertyQuota": true
}
```

- The four funnel steps are the filtered event names `view_item`, `add_to_cart`, `begin_checkout`, and `purchase`. The event-scoped metrics `addToCarts`, `checkouts`, and `ecommercePurchases` are property-wide counts of the same events, so they repeat on every row and are read once, not per step. `eventCount` is the per-step volume, which is what separates "the metric is empty" from "the event never fired".
- `purchaseRevenue` and `transactions` only fill when the purchase event carries a `transaction_id` and a currency. A funnel whose last step has `eventCount` but zero `purchaseRevenue` is a parameter finding, not a funnel finding.
- A funnel built on `runFunnelReport` is v1alpha. The v1beta equivalent above is repeatable, and its caveat is that it counts events per step rather than deduplicating users across them.

### Realtime

Answers "is this arriving right now".

```json
{
  "dimensions": [{"name": "eventName"}],
  "metrics": [{"name": "eventCount"}, {"name": "activeUsers"}],
  "limit": 20,
  "returnPropertyQuota": true
}
```

- The body goes to `:runRealtimeReport` and takes no `dateRanges`; the window is the last 30 minutes.
- Realtime is a presence check. A number from it is not a daily total, and a card is capped at a small row count, so never quote it as a count.
- Realtime data is not final: an event visible here can still be processed differently in the standard report.

## Row limit and response shape

- "The API returns a maximum of 250,000 rows per request, no matter how many you ask for." The default `limit` is 10,000.
- `keepEmptyRows` defaults to false, so a row whose every metric is zero is dropped from the response. Set `"keepEmptyRows": true` only when a zero row is itself the answer, such as proving an event exists with no volume on one day; otherwise the default is the honest shape.
- Read `rowCount` against the rows returned. When `rowCount` is larger than the row list, the answer is truncated and the report says so with the number that was cut.
- The response carries `dimensionHeaders`, `metricHeaders`, `rows`, `rowCount`, `metadata`, and `propertyQuota`. Quote the header order when a row's values are transcribed, because a positional read of the wrong column is the most common transcription error.

## Quota budget

Standard-property core token quotas:

| Bucket | Standard property |
|---|---|
| Tokens per property per day | 200,000 |
| Tokens per property per hour | 40,000 |
| Tokens per project per property per hour | 14,000 |
| Concurrent requests | 10 |

- "A single API request's token charge is deducted simultaneously from `tokensPerDay`, `tokensPerHour`, and `tokensPerProjectPerHour`", so the smallest bucket, not the daily total, decides how many requests a run can make.
- Exhausting any bucket returns `429 RESOURCE_EXHAUSTED`. The error names the bucket; report that bucket and stop spending on it instead of retrying, because a retry does not create tokens.
- The daily bucket refreshes at midnight PST, and the hourly buckets "within an hour but not necessarily on the whole hour boundaries". A run that hits an hourly bucket records when it may resume.
- `returnPropertyQuota: true` adds `propertyQuota` to the response with the remaining values for `tokensPerDay`, `tokensPerHour`, `tokensPerProjectPerHour`, `concurrentRequests`, `serverErrorsPerProjectPerHour`, and `potentiallyThresholdedRequestsPerHour`. Set it on every request of an `analyze` run and stop before the hourly bucket runs out rather than after a `429`.
- Thresholding has its own budget: up to 120 potentially thresholded requests per hour. A report over demographic or audience dimensions spends from it.
- `GOOGLE_CLOUD_PROJECT` attributes the request to a cloud project for quota, so two projects can share a property without sharing the per-project bucket.

## Data-quality flags

| Flag | Where it appears | What it means | What the report says |
|---|---|---|---|
| Sampling | `metadata.samplingMetadatas` | The response is an estimate computed over a sample of the property's data, not over all of it | "sampled - an estimate, not an exact count" |
| `(other)` rollup | `metadata.dataLossFromOtherRow` | Cardinality above 500 unique values per day is grouped into one row labelled `(other)` | "includes an `(other)` row; the named values do not sum to the total" |
| Thresholding | Potentially thresholded requests; the demographic and audience dimensions `userAgeBracket`, `userGender`, `brandingInterest`, `audienceId`, `audienceName` | Rows are withheld or aggregated to protect identity, so a small segment can read as zero | "thresholded - a missing row is not proof of zero traffic" |
| Approximate uniques | Any unique-count metric such as `activeUsers` | The API "uses the HyperLogLog++ (HLL++) algorithm to estimate unique counts" | "approximate uniques; two reports can differ slightly" |

- Filters are applied after the `(other)` rollup, so a `dimensionFilter` never sees inside `(other)`. A filtered report that totals less than an unfiltered one is expected when `dataLossFromOtherRow` is true; it is not a broken filter.
- `dataLossFromOtherRow` is the field to read; the visible symptom is a row whose dimension value is literally `(other)`.
- A thresholded result and a genuinely empty segment look identical in the rows. Say which one the response supports instead of picking one.

## Reporting rule

Every number in the report carries four things, or it is not reported:

1. the date range, with both dates and the property's time zone where the range crosses a day boundary
2. the property ID the request went to
3. the request shape: method, dimensions, metrics, filters, and limit
4. every data-quality flag present in the response, named from the table above

A thresholded, sampled, or `(other)`-affected result is labelled as such and never presented as exact. When the question needs event-level rows or keeps hitting thresholding or sampling, the honest answer is the BigQuery export path rather than a caveat on every line.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| v1beta method surface: `runReport`, `batchRunReports`, `runPivotReport`, `batchRunPivotReports`, `runRealtimeReport`, `getMetadata`, `checkCompatibility` | <https://developers.google.com/analytics/devguides/reporting/data/v1/rest> |
| `runFunnelReport` is v1alpha only and introduced at alpha stability | <https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1alpha/properties/runFunnelReport> |
| 250,000 rows per request maximum, 10,000 default, `keepEmptyRows` default false | <https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport> |
| 200,000 tokens per property per day, 40,000 per hour, 14,000 per project per property per hour, 10 concurrent requests, `429 RESOURCE_EXHAUSTED`, midnight PST daily refresh, hourly refresh within the hour | <https://developers.google.com/analytics/devguides/reporting/data/v1/quotas> |
| A request's token charge is deducted from all three buckets at once, and batched reports still count individually toward token and concurrent-request quotas | <https://developers.google.com/analytics/devguides/reporting/data/v1/quotas> |
| `returnPropertyQuota` reports remaining tokens, concurrent requests, server errors, and potentially thresholded requests | <https://developers.google.com/analytics/devguides/reporting/data/v1/quotas> |
| 120 potentially thresholded requests per hour and the five thresholded dimensions | <https://developers.google.com/analytics/devguides/reporting/data/v1/quotas> |
| `samplingMetadatas`, `dataLossFromOtherRow`, the `(other)` rollup above 500 unique values per day, filters applied after the rollup, and HLL++ estimates for unique counts | <https://developers.google.com/analytics/devguides/reporting/data/v1/reporting-data-expectations> |
| `customEvent:<param>`, `customUser:<param>`, `averageCustomEvent:<metric>`, `sessionKeyEventRate:<eventName>`, and `customChannelGroup:<id>` naming | <https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema> |
| Dimension and metric API names including `sessionDefaultChannelGroup`, `landingPage`, and `sessionKeyEventRate` | <https://developers.google.com/analytics/devguides/reporting/data/v1/api-schema> |

### Evidence grade

`MEASURED` for the method list and versions, the 250,000-row cap and 10,000 default, every quota figure, the quota field names, the four data-quality flags and their response fields, and the custom-definition naming grammar, from the pages above read on 2026-11-08. `LOCAL` for the five request recipes, the choice to build the v1beta funnel over `eventName` instead of the alpha method, the rule that `landingPage` answers an entry-page question where `pagePath` does not, and the four-part reporting rule; those are this package's composition of the measured facts. The token cost of one request is not a published number in the sources read, so this reference budgets from the remaining values in `propertyQuota` instead of predicting a charge.
