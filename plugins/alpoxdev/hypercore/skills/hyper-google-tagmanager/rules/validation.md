# Validation

**Purpose**: Define the evidence each mode must have before the run reports success, so a working tag is never claimed from a status code, a dashboard glance, or the agent's own reading of the code.

## 1. Completion Evidence Per Mode

| Mode | Evidence required |
|---|---|
| `audit` | The JSON of each script that ran; for every finding, the file and line, the page offset, or the container item it came from; every page listed with the method used (served HTML or rendered browser) |
| `install` | The diff of the changed files; a second `gtm-detect.sh` run with one container ID, one loader, and no direct Google tag for the same ID; the `verify` table |
| `configure` | The workspace items or import JSON that changed; a `gtm-container-audit.sh` run after the change with no new `error` finding; the `verify` table; the publish result (version ID) or the proposed publish action |
| `verify` | One row per planned tag, as in §2 |
| `diagnose` | The symptom, the layer that explained it, the change, and the same check before and after |
| `analyze` | The container counts and findings, the plan-versus-container comparison, and for data checks the report, date range, and data-quality flags |

## 2. Verification Row

| Column | Content |
|---|---|
| Tag | The tag name and type |
| Trigger event | The dataLayer event or built-in event that fired it |
| Fired | `yes`, `no`, or `blocked by consent` from Preview, Tag Assistant, or the rendered page |
| Request | The destination request (for example a `/g/collect` request with its `en` value) or `none` |
| Key parameters | The parameters the plan requires, as seen in the request or the debug view |
| Consent state | The consent types and their state at the time |
| Result | `verified`, `failed`, or `not verified` with the reason |

A tag is `verified` only when its request or debug event was observed in this run. When no browser or debug capability exists, mark the row `not verified` and give the exact check the user can run.

## 3. Disallowed Proof

- `gtm.js` answering HTTP 200. An unknown container ID also answers 200 with an empty container (resource version `1`, no tags).
- A GA4 standard report from the last 24 to 48 hours, or the absence of data there.
- The code reading correct, or a script finding list that is empty.
- A Tag Assistant run with "no tags found" when ad blockers, CSP, an iframe, or a late-loading tag can explain it.

## 4. Report Gate

- `.hyper/gtm/<slug>/report.md` exists and follows `references/report-template.md`.
- Every number in the report has its source (script output, request, or report) and its date.
- Approval-tier actions appear either with the approval quote and their result, or in the proposed actions list.
- The residual-risk section lists every `not verified` row and every finding left open.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Standard reports take 24 to 48 hours; network requests and DebugView are the immediate checks | <https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot> |
| Tag Assistant connection failures from ad blockers, CSP, iframes, late loading, and AMP | <https://support.google.com/tagassistant/answer/10039345> |
| Unknown container IDs answer 200 with an empty container | execution check, 2026-11-08, `references/verification.md` §4 |

### Evidence grade

`LOCAL` - the evidence table is this package's design over the sources above.
