# Verification

Read this file before every `verify` step and in `diagnose`. It says which check proves what, and which signals look like proof but are not. Facts marked `volatile` change with Google's tools; recheck them before relying on them.

## Contents

- 1. Preview and Tag Assistant
- 2. Environments
- 3. Rendered-browser checks
- 4. Failure signatures
- 5. Destination checks
- 6. Google-side audit surfaces
- 7. Publishing and rollback
- Sources

## 1. Preview and Tag Assistant

- Start: container > Workspace > **Preview** opens Tag Assistant; enter the site URL and **Connect**. The debug view "will only appear on the same browser that was used to enable preview mode, or for shared users". Preview is session-bound: a headless crawl cannot assert that Preview works.
- Share a session: Tag Assistant > More Actions > **Share**, or Versions > More Actions > **Share Preview**. Imported debug sessions are read-only.
- Older version: Versions > row > More Actions > **Preview**.
- What each view proves:
  - Event list: events "in the order they were fired"; `<>` marks built-in events.
  - **Tags**: Tags Fired and Tags Not Fired for the selected event.
  - **Variables**: each variable's value at that event.
  - **Data Layer**: the dataLayer state after the event; **API Call** shows the `gtag()` or `dataLayer.push()` that produced it.
  - **Consent**: the earliest consent event is the default, the latest is the update.
  - **Page issues**: CSP blocks and other load problems.
- Debug parameters (`volatile`): Tag Assistant adds `_dbg` to the URL. The loader also reads `gtm_debug`, the `tagassistant.google.com` referrer, a `__TAG_ASSISTANT` cookie, and a postMessage handshake. Do not use `gtm.js?id=...&gtm_debug=x` as a curl health check: it answered 403 for every container tested on 2026-11-08.
- Tag Assistant Companion is being merged into one Tag Assistant extension and "will be deprecated in the coming months" (`volatile`).
- Not available: the debug view for mobile app and AMP containers; "AMP is not currently supported by Tag Assistant".

## 2. Environments

- Every container has **Live** (the published version) and **Latest** (the latest version created). Custom environments: Admin > Environments > New; publish to them from Versions > Actions > **Publish To...**. "When you publish a custom environment, you will not send those changes to the live version of your container."
- An environment snippet carries `gtm_auth`, `gtm_preview=env-<n>`, and `gtm_cookies_win=x`. **Reset Link** "will invalidate any container snippets that may be installed". Environments are for non-production sites.
- Use a staging environment for a verification that needs real page loads without touching Live, then publish the same version to Live after approval.

## 3. Rendered-Browser Checks

Use a browser-automation capability when one exists. Record, for each page:

1. Requests to `googletagmanager.com/gtm.js` (count, status, container ID), and to the destinations (`/g/collect` for GA4, the vendor hosts for others).
2. For each `/g/collect` request: `tid` (measurement ID), `en` (event name), `cid` (client ID), event parameters (`ep.*`, `epn.*`), and `gcs` or `gcd` (consent state). These query names are observed, not documented by Google; treat them as `volatile`.
3. `window.dataLayer` after load and after each action, and `Object.keys(window.google_tag_manager || {})`. The loader builds `google_tag_manager` keyed by container ID: it proves the script ran, not that any tag fired.
4. Console errors and CSP violation reports.

A typical capture, written for the runtime's browser tool (Playwright shape shown):

```js
page.on('request', r => {
  const u = r.url();
  if (u.includes('googletagmanager.com/gtm.js') || u.includes('/g/collect')) log.push(u);
});
await page.goto(url);
const keys = await page.evaluate(() => Object.keys(window.google_tag_manager || {}));
const dl = await page.evaluate(() => JSON.stringify(window.dataLayer || []));
```

- `/g/collect` answers 204 even for a bogus `tid`, so assert on the request's parameters, never on its status.
- Next.js `GoogleTagManager` and Nuxt Scripts load the container after hydration: the served HTML has no container ID, the rendered page does.

## 4. Failure Signatures

Observed against the live endpoint on 2026-11-08 (`volatile`):

| Request | Answer | Meaning |
|---|---|---|
| `gtm.js?id=<unknown GTM-ID>` | 200, about 241 KB, `"resource": {"version":"1", "macros":[], "tags":[]...}` | Wrong ID, or a container that was never published; the two look the same from outside, so confirm in the Versions list (a row with a Published date) |
| `gtm.js?id=<published GTM-ID>` | 200, `"tags":[{` with entries | Container served. `resource.version` is the container format version (for example `44`), not the published version number |
| Container ID in lower case | 200, empty container | IDs are case-sensitive |
| Unknown ID with `gtm_auth` and `gtm_preview` | 404 | Environment snippet for a container that does not exist |
| Published container with a wrong `gtm_auth` and `gtm_preview` | 403 | Stale or reset environment snippet (`gtm_auth` alone is ignored) |
| `gtm.js` with no `id` | 400 | Broken snippet |
| `ns.html?id=<any>` | 200, the same tiny body for real and fake IDs | The noscript iframe proves nothing |

A wrong container ID never gives 404; a 404 on a plain `gtm.js` request points at a proxy, CDN, or host rewrite. `scripts/gtm-site-check.sh --check-loader` reports `loaderResourceVersion` and `loaderEmpty` for this reason.

Duplicate installs: count `gtm.js?id=` requests per ID in the rendered network log, list `document.querySelectorAll('script[src*="googletagmanager.com/gtm.js"]')`, and read `Object.keys(window.google_tag_manager)` without `rm`: two container IDs there means two containers live on one page.

Other signatures:

- Ad blocker: `gtm.js` request missing or `ERR_BLOCKED_BY_CLIENT`, `window.google_tag_manager` undefined, no `/g/collect`, page otherwise fine. Test with blockers off and say so.
- CSP: Page issues in Tag Assistant, violation reports in the console; Custom JavaScript variables resolving to `undefined` without `'unsafe-eval'`.
- Deny-all `gtag('policy')`: a dataLayer entry starting `Arguments(3) ['policy', ...`; measurement pings stop unless `read_event_data`, `read_container_data`, and `configure_google_tags` are allowed.
- `dataLayer = []` after load: later pushes are not seen; the dataLayer view stops updating.
- Tag Assistant "no tags found" can come from ad blockers, CSP, a firewall or proxy, a tag loaded after Tag Assistant connected (click **Retry**), an iframe, or AMP. It is not proof of a broken install.

## 5. Destination Checks

- GA4 DebugView (Admin > Data display > DebugView) shows the debug device's events within seconds. Preview and Tag Assistant enable debug mode for the testing browser; `debug_mode: true` enables it elsewhere, and only removing the parameter turns it off. Events are not visible in DebugView when consent for analytics was not given.
- GA4 Realtime shows events within minutes; standard reports take 24 to 48 hours and are not verification evidence.
- Other vendors: use the vendor's own debugger or test-events view, and record its event ID.

## 6. Google-Side Audit Surfaces

- **Tag Diagnostics** (Google tag > Tag quality > View diagnostics): statuses Excellent, Good, Needs attention, Urgent, No recent data. Urgent when the Google tag was detected before and not in the last 48 hours. Diagnostics include config or consent installed out of order, legacy Universal Analytics tags, missing transaction ID, CSP blocking resources, tag too low on the page, and data restricted without the tag gateway (`volatile` list).
- **Tag coverage** (Google tag > Admin > Tools > Tag coverage): up to 10,000 pages by domain and path; statuses Not tagged, No recent activity (30 days), Tagged; pages with no signal for 60 days drop off; status can lag 24 hours. Redirects, trailing slashes, URL case, and low traffic cause false "not tagged" rows.

## 7. Publishing and Rollback

- Publish: **Submit** > Publish and Create Version > review Workspace Changes > Version Name and Description > optional environment > **Publish**. Approval-tier action (`rules/safety-gates.md` §1).
- Rollback live: Versions > the earlier version > Actions > **Publish**. Also approval-tier.
- Rollback the draft only: Versions > Actions > **Set as Latest Version**; Live does not change until a publish.
- Request Approval exists in Tag Manager 360 only. The version list's Published column is the audit trail.
- After any publish, re-run `gtm-site-check.sh --check-loader` and confirm `gtm.js` now serves the changed tags (for example a new tag's type or event name appears in the response).

## Sources

> Checked 2026-11-08.

| Claim | Source |
|---|---|
| Preview, sharing, older versions, unsupported containers | <https://support.google.com/tagmanager/answer/6107056>, <https://support.google.com/tagmanager/answer/15212893> |
| Tag Assistant views and API Call | <https://support.google.com/tagmanager/answer/15212503> |
| `_dbg`, troubleshooting causes, AMP | <https://support.google.com/tagassistant/answer/10039345> |
| Companion deprecation | <https://support.google.com/tagmanager/answer/16463290> |
| Environments and their snippets | <https://support.google.com/tagmanager/answer/6311518> |
| Publishing, versions, rollback, 360 approvals | <https://support.google.com/tagmanager/answer/6107163> |
| Tag Diagnostics | <https://support.google.com/tagmanager/answer/14681508> |
| Tag coverage | <https://support.google.com/tagmanager/answer/12270036> |
| CSP Page issues and Custom JavaScript variables | <https://developers.google.com/tag-platform/security/guides/csp> |
| `gtag('policy')` measurement stop | <https://developers.google.com/tag-platform/tag-manager/templates/policies> |
| dataLayer re-initialization | <https://developers.google.com/tag-platform/tag-manager/datalayer> |
| DebugView and `debug_mode` | <https://support.google.com/analytics/answer/7201382> |
| Report latency and network checks | <https://developers.google.com/analytics/devguides/collection/ga4/troubleshoot> |
| Request capture API shape | <https://playwright.dev/docs/network> |
| `gtm.js` status and body signatures, `gtm_debug=x` 403, `/g/collect` 204, `google_tag_manager` keys | execution checks against the live endpoints, 2026-11-08; the unknown-ID 200 with `"version":"1"` and empty `tags`, the `gtm_debug=x` 403, `ns.html` 200, and the `/g/collect` 204 re-checked 2026-11-09 |

### Evidence grade

Official Google documentation read 2026-11-08, plus live endpoint observations from one network on that date. The failure-signature table and the `/g/collect` parameter names are observations, not documented contracts; recheck them when a result looks inconsistent.
