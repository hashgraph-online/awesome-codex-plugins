---
name: analytics-dashboard-integrity
description: Use when designing, reviewing, or fixing dashboards or analytical reports with cohorts, activation, retention, payments, revenue, forecasts, valuation metrics, denominators, privacy-sensitive rows, or source disagreements.
---

# Analytics Dashboard Integrity

Use this skill when a dashboard or analytical report can drive business decisions and the risk is metric trust, not visual layout alone.

## Metric Trust Gate

Before approving dashboard metrics, define:

1. source of truth;
2. grain;
3. denominator;
4. eligibility filter;
5. event or payment filter;
6. date anchor or `asOf` date;
7. freshness;
8. known disagreement with other sources.

Keep cohort membership filters separate from event and payment filters. A filter that silently changes the denominator must be explicit.

Payment currencies, credits, balances, bonus units, and revenue must stay separate unless a documented conversion rule exists.

When a dashboard or management summary combines several live sources, pin a single canonical snapshot boundary before writing the final numbers. Record the source-specific snapshot times and the report `asOf`; do not silently mix a later API/source refresh into a table or narrative already bound to an earlier sheet/export fact. If a later source disagrees, show it as a separate reconciliation note or refresh the whole dependent metric set together.

For monetary summaries, independently recompute every derived value from the exact source amounts, including currency conversion, rounding, cost per action, subtotals, and totals. After correcting a formula or conversion, recheck the changed formula and the nearest dependent totals before release.

Keep rates at full computational precision until their final display, or format them directly from the retained numerator and denominator. Do not round a fraction and then round its percentage again: for example, 384/542 displays as 70.8% to one decimal, while prematurely storing 0.7085 can incorrectly display 70.9%. Check displayed percentages against the original counts when a value lies near a rounding boundary.

When session recordings, Webvisor/video review, browser screenshots, or other visual behavior evidence suggest a funnel or product defect, size that defect against a source-of-truth denominator before naming it as the main cause or highest-priority opportunity. Record how many users, sessions, accounts, revenue, or eligible events use the observed path, and compare it with competing paths. A vivid replay of a minority path is evidence for a hypothesis, not proof that the defect explains overall conversion, activation, retention, or revenue.

## Attribution And Event Evidence

Before joining page traffic with CRM/Roistat landing-page metrics, compare actual URL variants across both sources. A trailing slash can split one canonical page into separate traffic and revenue rows. Confirm redirects/canonical URLs for the affected paths, preserve query strings and fragments, and require zero collisions within site and channel before normalizing. Do not sum unique visitors across merged URL variants; use an exact combined source query if more than one traffic row maps to a canonical key.

Before calculating advertising cost per lead or return, verify the linkage
between visits, lead events and attributed sources, including telephone-source
assignments when calls contribute. A source label or UTM value on a CRM card does
not itself prove that link. Keep unlinked leads in an explicit unknown bucket;
zero linked leads with unverified tracking is not proof of zero advertising
leads. Expense detail must not be used to invent matching lead attribution.

When CRM UTM sources differ from the advertising-source registry, inspect both
live values before repairing joins. An alternate source match must require the
paid medium and an exact, unambiguous campaign match; never assign all traffic
from a search engine to its advertising account. Verify organic, missing-tag,
unknown-campaign and test-record cases as well as real paid leads. In Trino,
repeated CTE joins can exceed the query-stage limit: reduce redundant joins and
compare old/new totals in separate equivalent queries instead of combining
both full graphs or changing server limits.

For appointment funnels, distinguish booking, actual attendance, an indication
for treatment and performed treatment. Define the evidence source and event date
for each before calculating attendance or treatment conversion. Inspect existing
fields, activities and history before proposing new stages. If the attendance
event is not established, mark attendance metrics unavailable rather than infer
attendance from a treatment-indication status.

When grouped analytics rows do not sum to the total, obtain a comparable
ungrouped control with the same filters, period and attribution. Check a named
segment and its complement using comparable controls. An unsampled response does
not prove that every grouped row was disclosed. Preserve unexplained residuals;
do not distribute them across visible rows or name privacy suppression as the
cause without evidence.

When extending a report with recovered URL rows, recompute every residual from
the current detail and the pinned ungrouped control before generating totals.
Never append recovered rows while retaining the original residual as another
additive row: that double-counts the recovered visits or pageviews. Keep initial
disclosure counts as historical evidence separately, and require the current
detail plus current residual to equal the control for every site and channel.

After excluding robot, test, or out-of-scope records, recheck membership of the
final detail list. Keep groups with zero in-scope activity and no in-scope
commercial events in the raw audit, but exclude them from a list presented as
"visited pages" or another list of observed in-scope entities.

## Lost Advertising Identifier Recovery

When a CRM lead has a paid campaign but an empty ad identifier, inspect the
actual capture and serialization functions as well as the reporting join. Test
real-length identifiers through the full metadata chain: a phone privacy regex
can match a substring of a long ad number. Use a field-specific numeric policy
for ad identifiers; preserve contact filtering in other fields. Recover past
identifiers only from an exact click marker and matching campaign/source/medium
in retained access logs. Save the original CRM fields, update existing records
only, read them back, and verify the rendered report. Check every paid form
affected by the same cause, not only the screenshot example.

## Cohorts And Forecasts

For activation, retention, payment, revenue, or funnel cohorts:

- mark immature horizons from the `asOf` date;
- handle right-censoring and partial periods;
- avoid presenting immature periods as stable facts;
- record sample size and denominator for every rate.

Forecasts must be deterministic enough that two implementers compute the same point estimate, interval boundaries, status, and warning order. Negative clipping, interval composition, status precedence, and validation-error signs must be specified before coding.

Small-sample forecasts need uncertainty, backtesting or a reliability status. A single forward trend without reliability is not a management metric.

## Privacy And Live Data

When editing SQL in an Ace editor, do not assume textbox `fill` replaces the
whole document: its textarea can represent only the current line. Select the
whole editor document, paste the replacement, then select/copy it back and
compare the complete text before running or saving. Preserve the full preimage. If the copied text differs, stop before save confirmation; inspect the editor lock and unlock it before replacing the document again. Gate the save action on exact equality, rather than merely printing the comparison.

For pivot tables with CSS-generated header labels, check that every rendered metric has a visible header whenever the metric list changes; updating grid width alone is insufficient. Verify saved CSS after reopening the real report. In Superset, wait for the CSS preview to reflect the edit, close its dialog, save the dashboard, and require the save confirmation before reloading.

Dashboards that expose live user, generation, payment, or revenue aggregates need explicit auth, cache, and privacy review. Do not include direct personal, payment, account, credential, or raw operational rows unless the delivery surface and audience require them and the values are minimized.
