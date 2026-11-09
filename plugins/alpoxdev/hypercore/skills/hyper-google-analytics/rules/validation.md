# Validation

Use this checklist before declaring a run complete. It owns the completion evidence each mode needs, the rule that standard reports are not collection proof, the report check, and the repair bound.

## 1. The Collection-Proof Rule

A measurement is proven collected only when one of these holds for this run:

1. a network capture shows a `/g/collect` request whose `tid` is the property's measurement ID and whose `en` is the event expected, with a `200` or `204` response
2. DebugView shows the event with its parameters for a session this run started with debug mode present
3. a Realtime report shows the event within its minutes-long window
4. an Admin API read-back shows the configuration value that was written

A standard report, a property dashboard, a report that "should update tomorrow", an upload attempt, a `2xx` from `/mp/collect`, and a CLI exit code of `0` are not collection proof. A standard report lags 24 to 48 hours, so it can neither confirm nor refute anything this run changed.

## 2. Completion Evidence By Mode

| Mode | Claim | Required evidence |
|---|---|---|
| `audit` | "Findings reported" | Every finding with its severity, the file and line or the request and response that shows it, and its fix owner; no property or site file changed; the target line with the measurement ID and property ID and where each came from |
| `install` | "Installed and collecting" | The changed files, the consent default ahead of every measurement command, one page-view source, the CSP entries, and section 1 for a `page_view` with the expected `tid` |
| `configure` | "Changed" | The value before with its field path, the exact method and body, the account, property, and stream stated before the write, the value after from a `get`, and how long the setting takes to apply |
| `analyze` | "Reported" | The request, its date range, the row count against the 250,000 cap, and every data-quality flag the response returned: thresholding, sampling, `(other)` rollup, and HLL++ estimate |
| `diagnose` | "Fixed" | The failing signal before, the cause from the fixed order, the change, the same signal after meeting section 1, and the before-and-after pair |
| `diagnose` | "Exhausted" | Three attempts for the same cause, each with its change and result, the cause's position in the fixed order, and the next evidence to collect |
| any | "Stopped for approval" | The exact call, what it changes, how long it takes to apply, what it cannot restore, and the evidence behind it (`rules/safety-gates.md` §5) |
| any | "Does not apply" | The site root, the files read, and the output shape the request belongs to |

## 3. Report Check

- [ ] `.hyper/google-analytics/<slug>/report.md` exists and follows `references/report-template.md`.
- [ ] Every call in the report ran in this session, or is marked `not run` with the reason.
- [ ] Every captured request is bounded - one URL, one status - and every secret is redacted with the redaction noted.
- [ ] Every analysis number carries its request, date range, and data-quality flags.
- [ ] Missing credentials, an unenabled API, a missing scope, and skipped checks are listed apart from passed checks.
- [ ] The final state line names the mode's terminal result: `audited`, `installed`, `changed`, `reported`, `fixed`, `exhausted`, `stopped-for-approval`, `delayed`, `blocked`, or `handoff`.
- [ ] No finding, number, or proof is copied from a source that was not opened in this run.

## 4. Repair Bound

A failing check sends the run back to the failing step within the mode's budget (`SKILL.md`, loop policy). A check that ran and failed stays visible in the report even when a later attempt passed. A cause whose third attempt failed is reported as `exhausted` with the next evidence to collect, never retried a fourth time under a new name.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Standard reports need 24 to 48 hours while Realtime appears within minutes, and `/g/collect` answers `200` or `204` on a successful transmission | <https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot> |
| DebugView requires debug mode, and omitting the parameter is the only way to turn it off | <https://support.google.com/analytics/answer/7201382> |
| The Measurement Protocol returns no HTTP error code for a malformed event, so a `2xx` is not acceptance | <https://developers.google.com/analytics/devguides/collection/protocol/ga4/validating-events> |
| `runReport` returns at most 250,000 rows per request | <https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport> |
| Thresholding, sampling, the `(other)` rollup, and HLL++ estimates must be carried into a report | <https://developers.google.com/analytics/devguides/reporting/data/v1/reporting-data-expectations> |
| A data filter takes 24 to 36 hours to apply, so a read-back alone is not proof of its effect | <https://support.google.com/analytics/answer/10104470> |

### Evidence grade

`LOCAL` - the state list, the evidence table, and the repair bound are this package's design over the cited pages. The latency, cap, and flag facts are `MEASURED` from the official pages read on 2026-11-08.
