# GA Workflow

Use this rule to pick a mode and to run its phases. It owns mode selection, the phases of each mode, and the fixed order `diagnose` walks.

## 1. Pick The Mode

The mode follows the requested output, not the words in the request.

| Requested output | Mode |
|---|---|
| A findings list about what is set up now, with no change | `audit` |
| GA4 added or fixed in the repository, with the tag live | `install` |
| One property setting changed and read back | `configure` |
| A number or a comparison answered from reporting data | `analyze` |
| A cause for data that is missing, duplicated, or wrong | `diagnose` |

A request can carry two modes: "점검하고 빠진 것도 넣어줘" is `audit` then `install`. Run them in that order and give each its own completion evidence.

## 2. Identify Before Writing

Before the first write to a property or a live site, state all of:

- the account, the property ID (`properties/<number>`), and the stream ID or measurement ID (`G-`)
- the environment: production site, preview, or local
- the exact method and body the write would send

Read `accountSummaries.list` and then `dataStreams.list` to get them; never infer a property ID from a measurement ID alone.

## 3. Mode Phases

### `audit`

1. Run `scripts/ga-detect.sh <repo-root>`, which lists the tag, the measurement ID, the tag manager, a framework integration, the consent defaults, the CSP header, a server-side send, and a possible `api_secret` with the file and line of each. Read the files it names, and add what a static scan cannot see, such as a tag injected at run time or one set by a Tag Manager container.
2. Load the live page and capture its `/g/collect` requests. Record the query's `tid` and `en`, and the response status.
3. Read the property read-only: streams and their measurement IDs, enhanced measurement toggles, key events, custom dimensions and metrics, data retention, data filters, unwanted referrals, cross-domain settings.
4. Compare all three: code that never fires, a tag whose measurement ID differs from the property's stream, a page view sent twice, a consent default that blocks collection, an event over a published limit, a filter that hides real traffic.
5. Score every finding by severity (blocks all data, corrupts a metric, misleads a report, cosmetic) and give it a fix owner: code, property, tag manager, or consent banner.

### `install`

1. Choose the method from the framework and the site's constraints: the framework's official integration, the `gtag.js` snippet, or a server-side call. State why the chosen method fits and what the rejected one would have cost. When the page already loads a `GTM-` container, do not add a second tag and do not edit the container in this run: its tags, triggers, and variables are a separate change with its own approval, so name the exact tag the property needs and keep this run to the page code - consent default order, one page-view source, CSP entries, and any `dataLayer` push the container will read.
2. Write the consent default before any tag call, on every page, ahead of every measurement command. Without a consent platform the default blocks storage until the user acts; state that explicitly.
3. Pick exactly one page-view source. With a tag manager, do not also enable automatic history tracking. Without one, either keep `send_page_view` on and let history events drive it, or turn both off and send `page_view` yourself on route change. Never leave both on.
4. Add the CSP entries the tag needs: `script-src-elem https://www.googletagmanager.com`, `connect-src` and `img-src` for `https://*.google-analytics.com`, and a nonce for inline container code.
5. Prove collection: reload the page, capture a `/g/collect` request with the expected `tid` and `en=page_view`, and record its status; or show the event in DebugView, which needs `debug_mode` present (omitting it is the only way to turn debug off).

### `configure`

1. Read the current value first and quote the field and its path.
2. State the account, property, and stream, then the exact change: the method, the field that changes, and the value before and after.
3. For a change in the approval tier, stop here and follow `rules/safety-gates.md` §5.
4. Write once, then read the resource back with a `get` and quote the field that changed.
5. When the setting only takes effect after processing - a data filter, a key event, an altered event - say how long it takes and what the read-back alone cannot prove.

### `analyze`

1. Translate the question into dimensions, metrics, a date range, and any filter or comparison.
2. Check the names against `getMetadata` before sending, and check the pair with `checkCompatibility` when the combination is new.
3. Send one request with an explicit `limit`, and read the quota it returns when the response includes it. A 250,000-row cap per request and a 10,000-row default both apply.
4. Carry every data-quality flag the response returns into the report: thresholding, sampling metadata, the `(other)` rollup and `dataLossFromOtherRow`, and the fact that unique counts are HLL++ estimates.
5. State the conclusion in one sentence, then the numbers, each with its request, date range, and caveat.

### `diagnose`

Walk this order and stop at the first cause that explains the symptom. Do not skip ahead to a later cause because it is easier to test.

1. **No request at all.** The tag never loads: a missing snippet, a script blocked by the bundler, a tag placed after the events it should carry, or a build that strips it.
2. **Wrong measurement ID.** The page sends a `tid` that is not this property's stream, a duplicated tag from an old install, or a test ID left in production.
3. **Consent denied.** The consent default blocks storage before any measurement command, the consent update never runs, or the code order puts the default after the tag.
4. **CSP or network block.** A missing `connect-src` or `script-src-elem`, an ad blocker in the test browser, or a proxy that drops the request.
5. **Duplicates.** Two page-view sources (automatic history tracking plus a manual call), a tag loaded twice, a `purchase` without `transaction_id`, or a Measurement Protocol event that repeats a client event.
6. **Filters and referrals.** An internal-traffic or developer-traffic filter, a hostname filter that blocks empty hostnames, a self-referral, or a cross-domain `_gl` value that expired after two minutes.
7. **Processing delay.** The request is correct and arrives; the number is simply not in the standard report yet, which lags 24 to 48 hours. This is not a defect and is reported as a delay, never as fixed.

Rules for the loop:

- Each cause gets at most three attempts, counted across resumes. The third failure on one cause ends the run with `exhausted` for that cause and the next evidence to collect.
- The checker is a fresh network request, DebugView, or Realtime. A standard report is never the checker.
- Fix the cause, not the symptom: never drop an event to stop a duplicate, never widen a filter to hide a gap, and never disable a check to make the signal appear.

## 4. Report Path

Write `.hyper/google-analytics/<slug>/report.md` following `references/report-template.md`. The slug is the site or property name plus the mode when one repository holds several properties.

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Standard reports lag 24 to 48 hours, Realtime appears within minutes, and a `/g/collect` request answers `200` or `204` on success | <https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot> |
| Debug mode is enabled by adding `debug_mode`; setting it to `false` does not disable it, so it must be omitted | <https://support.google.com/analytics/answer/7201382> |
| Consent defaults must run on every page before any measurement command, and out-of-order consent does not work | <https://developers.google.com/tag-platform/security/guides/consent> |
| With a tag manager, enabling automatic history tracking in Analytics double-counts page views | <https://developers.google.com/analytics/devguides/collection/ga4/single-page-applications> |
| The tag's minimum CSP entries name `googletagmanager.com` for scripts and `google-analytics.com` for connect and image, with a nonce for inline container code | <https://developers.google.com/tag-platform/security/guides/csp> |
| A data filter takes 24 to 36 hours to apply and its effect is permanent | <https://support.google.com/analytics/answer/10104470> |
| Cross-domain linker parameters expire after two minutes | <https://developers.google.com/tag-platform/devguides/cross-domain> |
| `runReport` returns at most 250,000 rows per request and defaults to 10,000 | <https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport> |
| Thresholding, sampling metadata, the `(other)` row, and HLL++ estimates are the data-quality flags a report must carry | <https://developers.google.com/analytics/devguides/reporting/data/v1/reporting-data-expectations> |
| `checkCompatibility` and `getMetadata` exist to validate a dimension and metric pair before spending quota | <https://developers.google.com/analytics/devguides/reporting/data/v1/rest> |

### Evidence grade

`LOCAL` - the mode phases and the seven-step cause order are this package's design over the cited pages. The latency, filter, CSP, and quota values are `MEASURED` from the official pages read on 2026-11-08. The order puts cheap, high-frequency causes first, so it reflects observed failures rather than a published ranking.
