# BigQuery Export

Read this reference when a question needs event-level rows, exceeds the report row or quota limits, or keeps hitting thresholding or sampling. It owns the export limit, what a paused export does, the table and dataset names, the late-arriving-data window, and the rule for recommending the export instead of setting it up.

> Korean version: [`bigquery-export.ko.md`](bigquery-export.ko.md)

## Contents

- When to recommend it
- The daily limit
- Dataset and table names
- The late-data window
- What the export does not give
- Recommending, not setting up

## When to recommend it

Recommend the BigQuery export, and do not set it up, when the question falls in one of these three shapes:

1. **Event-level rows.** The answer needs the parameters of individual events, a join across events in one session, or a user path rather than an aggregate. A Data API report returns aggregates; no request shape turns it into rows.
2. **Row or quota limits.** The result needs more than the 250,000 rows a single request can return, or the analysis would spend the property's Data API buckets, whose smallest bucket is 14,000 tokens per project per property per hour.
3. **Thresholding or sampling that keeps recurring.** The same question returns `dataLossFromOtherRow` or a `samplingMetadatas` entry on every attempt, or the rows a demographic question needs are withheld. A caveat on every line is not an answer.

Each recommendation names the export, its limit, and what it would take to enable it - which is a property-level change outside this run's scope. It is a recommendation with a reason, never a claim that the export already exists.

## The daily limit

- "Standard properties have a daily BigQuery Export limit of 1 million events." The limit is per day and per property, not per table or per query.
- Exceeding it pauses the export: "the daily BigQuery export will be paused and previous days' exports will not be reprocessed." The paused days are a permanent gap in the export, not a delay that fills in later.
- The export is not a safety net for a volume spike. When a run sees a day near the limit, say so before the pause happens, because after it there is nothing to backfill.
- Analytics 360 has its own, much higher ceiling, and Fresh Daily is a 360-only option. Neither applies to a standard property, so do not quote them as if they lifted the 1-million-event limit.
- Streaming export is best effort and "may contain data gaps", and it excludes the new-user traffic-source fields. An intraday-only question inherits those gaps.

## Dataset and table names

| Item | Name |
|---|---|
| Dataset | `analytics_<property_id>` |
| Daily export table | `events_YYYYMMDD` |
| Streaming (intraday) table | `events_intraday_YYYYMMDD` |

- `<property_id>` is the numeric property ID, the number in `properties/<number>`, not the `G-` measurement ID. A dataset named from a measurement ID is a wrong-dataset finding.
- A daily table named `events_20261001` holds the events for October 1 in the property's time zone, not UTC.
- The intraday table is replaced: once the daily table for a date completes, the intraday table for that date is dropped. A query pinned to `events_intraday_20261001` stops working the next day, and a query that unions both for the same date double-counts while the intraday table still exists.
- Both tables share the schema for the fields they carry, with `traffic_source` and `user_ltv` absent from intraday tables.
- `event_params`, `item_params`, and `user_properties` are repeated RECORDs with a `key` and a `value.string_value` / `value.int_value` / `value.double_value`, so a parameter read is an unnest, not a column reference.

## The late-data window

The two official pages disagree, and this reference records both rather than picking one silently:

| Page | Stated window |
|---|---|
| BigQuery Export schema page | Daily tables are updated for "up to 3 days" after the event date |
| BigQuery Export support page | "up to 2 calendar days, plus today" |

- Recorded value in this package: **72 hours**, the conservative reading. A question asked about a date inside 72 hours is answered with that uncertainty stated, because the two policies differ by whether the third day is included.
- A daily number read before its window closes is provisional. Say that the table may still receive late events and that the final figure can rise.
- An event that arrives after the window is not in the export at all, so a total from the export can be lower than a Data API total for the same dates. That difference is a processing difference, not proof that one surface is wrong.
- Re-read both pages before relying on the number, because a change to either one moves the conservative value.

## What the export does not give

- No SQL is written by this package. The export is recommended as the surface for a question, and writing the query belongs to a run that was asked to write it.
- Enabling the link, choosing the dataset location, and granting BigQuery roles are property and cloud-project changes. They are proposed with their exact steps and never run as part of an `analyze`.
- The export does not replace the collection check. A table with rows proves that events reached the export, not that the tag on the live page is correct today.
- The export carries what was collected. A parameter the site never sent is absent from `event_params` exactly as it is absent from a report; the export does not fill a collection gap.

## Recommending, not setting up

| Situation | What the run does |
|---|---|
| Event-level rows are needed | Name the export, the dataset and table names, and the fact that the answer needs an event-level query; do not enable anything |
| A report hits the row cap or a quota bucket | Recommend the export and state the measured limit or the exhausted bucket |
| Thresholding or sampling recurs | Recommend the export, name the flag that recurred, and state that the export carries no thresholding |
| The request says "link BigQuery" | That is a `configure` action on a property plus a cloud-project change; name the approval it needs, then stop |

The recommendation in the report carries the limit, the table names, the 72-hour caveat, and the reason from the table above. It does not carry a query, a dataset location, or a claim that the export is already enabled.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Standard properties have a daily BigQuery Export limit of 1 million events; 360 has a much higher ceiling and Fresh Daily is 360-only | <https://support.google.com/analytics/answer/9358801> |
| Exceeding the daily limit pauses the export and previous days' exports are not reprocessed | <https://support.google.com/analytics/answer/9823238> |
| Dataset `analytics_<property_id>`, daily table `events_YYYYMMDD`, intraday table `events_intraday_YYYYMMDD` dropped once the daily table completes | <https://support.google.com/analytics/answer/7029846> |
| The schema page states daily tables are updated for up to 3 days after the event date | <https://support.google.com/analytics/answer/7029846> |
| The support page states "up to 2 calendar days, plus today" | <https://support.google.com/analytics/answer/9358801> |
| Streaming export is best effort, may contain data gaps, and omits new-user traffic-source fields | <https://support.google.com/analytics/answer/9358801> |
| `event_params`, `item_params`, and `user_properties` are repeated RECORDs keyed by `key` with string, int, and double values | <https://support.google.com/analytics/answer/7029846> |
| A Data API request returns at most 250,000 rows, and the smallest standard quota bucket is 14,000 tokens per project per property per hour | <https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport>, <https://developers.google.com/analytics/devguides/reporting/data/v1/quotas> |

### Evidence grade

`MEASURED` for the 1-million-event daily limit, the pause and no-reprocessing behaviour, the dataset and table names, the intraday table's lifecycle, the repeated-RECORD schema, the streaming caveats, and both late-data windows as each page states them, from the pages above read on 2026-11-08. `LOCAL` for the 72-hour conservative value chosen because the two pages disagree, the three-shape recommendation rule, and the rule that the export is recommended and not enabled. The disagreement itself is reported as a disagreement rather than resolved by preference, and the conservative value is the one this package records until both pages agree.
