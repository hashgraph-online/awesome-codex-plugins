# Verification

Read this reference when a run must prove collection or explain a gap. It owns the transport checks, the debug surfaces, the Measurement Protocol validation path, the diagnosis order, and the boundary of what a report can prove.

> Korean version: [`verification.ko.md`](verification.ko.md)

## Contents

- The one rule
- `/g/collect`
- DebugView
- Tag Assistant
- Realtime
- Measurement Protocol validation
- The diagnose order

## The one rule

A collection claim rests on a transport observation, not on a report. Standard reports are a lagging aggregate and prove nothing about this run: **standard reports are not collection proof.** They take 24 to 48 hours to process, so an empty report is consistent both with a broken tag and with a working tag whose data has not been processed yet. Never open the finding with "no data, so the tag is broken", and never close a run as fixed because a report changed.

The four accepted proofs, in the order to try them:

1. a `/g/collect` request whose `tid` is the property's measurement ID and whose `en` is the expected event, answered `200` or `204`
2. DebugView showing the event and its parameters for a session this run started
3. a Realtime report showing the event inside its minutes-long window
4. for a server-side send, the `/debug/mp/collect` response with an empty `validationMessages`

An Admin API read-back proves a setting, not collection. A `2xx` from `/mp/collect` proves the request was accepted, not that an event exists.

## `/g/collect`

- The endpoints are `google-analytics.com/g/collect` and `analytics.google.com/g/collect`. "A `200 OK` or `204 No Content` status code indicates a successful transmission."
- Capture from the network panel or a proxy, filter on the endpoint, and record three things: the URL with its query, the response status, and the timestamp.
- Endpoint choice matters: a request to a third-party or proxied host is a different finding from a request to Google, because a gateway or a Partytown setup changes the host on purpose.
- Bound the capture to one page load or one interaction. A loop of replays inflates the property's event volume and makes the next observation unreliable.

The query string carries fields that identify and describe the hit. These are observed fields, not a published contract:

| Field | Observed meaning |
|---|---|
| `tid` | measurement ID (`G-`) |
| `en` | event name, for example `page_view` |
| `cid` | client identifier |
| `ep.*` / `epn.*` | event parameter, string and numeric forms |
| `seg` | session engagement flag |
| `_p` | page-load identifier |
| `gcs` | storage consent state |
| `gcd` | consent state that is always sent |

Document them as observed values. No official page publishes them, so do not call a mismatch an API violation, and do not build an assertion on a field's spelling. If a field is absent where a sibling field is present, record the observation and its source rather than a schema verdict.

## DebugView

- "You must enable debug mode to use DebugView." Enable it with `gtag('config', 'G-12345ABCDE', { debug_mode: true })` or by installing the Google Analytics Debugger extension.
- "setting the parameter to `false` doesn't disable debug mode." Omitting the parameter is the only way to turn it off. A `debug_mode: false` left in production still streams debug traffic.
- A debug session appears only while the debug-enabled page is being used; a page loaded earlier without debug mode never shows up.
- Device and browser filters inside DebugView hide events that are actually arriving. Clear them before reporting an event as missing.
- Debug traffic should later be excluded by the Developer Traffic filter, so do not leave debug mode enabled in a release build.

## Tag Assistant

- Tag Assistant (`tagassistant.google.com` or the extension) shows the tags that loaded, their firing order, and the Consent events. It is the right tool for "which tag fired" and for consent ordering.
- It is not a volume or a timing tool. Use it to confirm a tag exists and fires, then use `/g/collect` or DebugView for the event-level detail.

## Realtime

- Realtime shows events from the last 5 to 30 minutes, and it is "best effort … without a formal Service Level Objective". A card can hold at most 700 rows on desktop.
- Use it as a fast presence check and as a second opinion after DebugView. Do not use it as a count, because thresholding and the short window change the number.
- A Realtime hit that appears without a matching `/g/collect` observation means the capture missed the request, not that the request did not happen.

## Measurement Protocol validation

- The production endpoint is `POST https://www.google-analytics.com/mp/collect` (EU: `https://region1.google-analytics.com/mp/collect`), and `api_secret` travels in the query string while `client_id` travels in the body.
- The protocol "does not return HTTP error codes, even if an event is malformed", so a `2xx` is not acceptance and the request must not be retried on that basis.
- Validate against `https://www.google-analytics.com/debug/mp/collect`. It returns `validationMessages`; an empty array is the pass. Message codes include `VALUE_INVALID`, `VALUE_REQUIRED`, `NAME_INVALID`, `NAME_RESERVED`, `VALUE_OUT_OF_BOUNDS`, `EXCEEDED_MAX_ENTITIES`, and `NAME_DUPLICATED`.
- The validation server does not validate the `api_secret`, so a clean `validationMessages` does not prove the secret is right.
- Limits to respect: up to 25 events per request, 25 parameters per event, a body under 130 kB, and backdating up to 72 hours. Events should reach Google within 48 hours to join the client-side session.
- Never print the `api_secret`. An `api_secret` found in client-side code is a security finding with its own severity, and it shows at most its first four characters in any report.

## The diagnose order

Walk this order and stop at the first cause that explains the symptom. Do not jump ahead to a cheaper test.

1. **No request at all.** The tag never loads: a missing snippet, a bundler that drops it, an event call above the snippet, or a build that strips it. Evidence: no `/g/collect` on any page load.
2. **Wrong measurement ID.** The page sends a `tid` that is not this property's stream, an old tag still fires, or a test ID reached production. Evidence: a request exists and its `tid` differs from the stream's measurement ID.
3. **Consent denied.** The default blocks storage and the update never arrives, or the default arrives after the tag. Evidence: a request with `gcs` showing denied storage, or no request until the banner is accepted.
4. **CSP or network block.** A missing `connect-src` or `script-src-elem`, an extension in the test browser, or a proxy that drops the call. Evidence: a console CSP violation with the blocked host named.
5. **Duplicate tags or page views.** Two snippets, a framework component plus a manual snippet, automatic history tracking plus a manual `page_view`, or a `purchase` without `transaction_id`. Evidence: two requests with the same `en` and the same `cid` in one navigation.
6. **Filters or referrals.** An internal-traffic or developer-traffic filter, a hostname filter blocking empty hostnames, a self-referral, or an expired `_gl` linker parameter. Evidence: a request that arrives while the report shows the traffic attributed elsewhere or missing.
7. **Processing delay.** The request is correct and arrived; the standard report simply has not processed it yet. This is a delay, reported as a delay, and never as fixed. Evidence: a `200`/`204` on the expected `tid` plus a report that lags 24 to 48 hours.

Loop rules mirror `rules/ga-workflow.md`: three attempts per cause, a fresh transport observation as the checker, and no fix that weakens a check.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| A `/g/collect` request answered `200` or `204` indicates a successful transmission, and standard reports take 24 to 48 hours while Realtime appears within minutes | <https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot> |
| DebugView requires debug mode, and setting `debug_mode` to `false` does not disable it | <https://support.google.com/analytics/answer/7201382> |
| Realtime covers the last 5 to 30 minutes, is best effort without an SLO, and caps a card at 700 rows | <https://support.google.com/analytics/answer/9271392> |
| The earliest Consent event is the page default and the latest is the update | <https://developers.google.com/tag-platform/security/guides/consent-debugging> |
| The Measurement Protocol does not return HTTP error codes for a malformed event | <https://developers.google.com/analytics/devguides/collection/protocol/ga4/validating-events> |
| `/debug/mp/collect` returns `validationMessages` with codes such as `VALUE_INVALID` and `NAME_RESERVED`, and does not validate the `api_secret` | <https://developers.google.com/analytics/devguides/collection/protocol/ga4/validating-events> |
| The `api_secret` is private and must not be exposed in client-side code; the request takes `measurement_id` and `client_id` | <https://developers.google.com/analytics/devguides/collection/protocol/ga4/sending-events> |
| Up to 25 events per request, 25 parameters per event, a 130 kB body limit, and 72-hour backdating | <https://developers.google.com/analytics/devguides/collection/protocol/ga4/reference> |
| The Developer Traffic filter excludes events sent in debug mode and takes 24 to 36 hours to apply | <https://support.google.com/analytics/answer/13296662> |
| No official page documents the `/g/collect` query parameters | direct search of <https://developers.google.com/analytics/devguides/collection/ga4/> on 2026-11-08 returned no parameter reference page |

### Evidence grade

`MEASURED` for the status codes, the debug-mode rule, the Realtime window, the validation endpoint and its codes, and the request limits, from the pages above read on 2026-11-08. `LOCAL` for the seven-step diagnosis order, the four-proof ladder, and the field table; the order and the ladder are this package's design, and the field table records observed traffic because no official reference exists. The absence of an official `/g/collect` parameter page is itself the result of a search on 2026-11-08, not a claim that such a page will never exist.
