# PostHog, hardened

Session replay, heatmaps, dead clicks and exceptions, only with consent
(model B), with nothing personal in what is sent. Written and tested against
**posthog-js 1.438.3**. On a newer version, re-run `verify.mjs` with
`--posthog`; PostHog changes behaviour between releases.

## Files

- `assets/posthog-guard.mjs`: `startPostHog`, `follow`, `stopPostHog`,
  `purgePostHog`, `posthogConfig`, `makeBeforeSend`, and the URL cleaners.
- `assets/posthog-proxy.mjs`: a same-origin proxy (`/ingest/*`) with a header allowlist.

## Wiring

```js
import { startPostHog, stopPostHog, purgePostHog } from './posthog-guard.mjs';
const site = {
  token: 'phc_…',                      // the project token: public, may be in client code
  hosts: ['example.com', 'www.example.com'],
  origin: 'https://example.com',
  private: [/^\/account(\/|$)/, /^\/reset\//],
  apiHost: '/ingest', uiHost: 'https://eu.posthog.com',
  consented: () => window.analyticsConsent?.get() === 'granted',
};
// Bundled (Next.js, Vite): import('posthog-js'). Plain HTML: serve a copy of
// node_modules/posthog-js/dist/module.mjs and import('/vendor/posthog.mjs').
const load = () => import('posthog-js');   // nothing of PostHog is downloaded before consent
// consent.js must run first (deferred before this module, or beforeInteractive): it defines analyticsConsent.
if (site.consented()) startPostHog(site, load); else purgePostHog();
window.addEventListener('consent:changed', (e) => { if (e.detail === 'granted') startPostHog(site, load); });
window.consentConfig = Object.assign(window.consentConfig || {}, {
  onWithdraw: () => stopPostHog(),
  onDecline: () => purgePostHog(),
});
```

- **Next.js.** Start it from a client component or `instrumentation-client.ts`
  once the page is idle (`requestIdleCallback`). Never import it
  statically: the SDK is about 100 KB gzipped (about 320 KB minified).
- **Recipes per stack.** `references/recipes.md` has the whole wiring.
- **GPC and DNT.** `startPostHog` refuses to start under Global Privacy
  Control or Do Not Track, whatever consent is stored.
- **Page speed.** PostHog's web vitals are on only with `site.webVitals:
  true`: set it from the same answer as k.js's `data-vitals`, so the
  privacy text names page speed for both or neither.
- **Self-hosted PostHog, staging and tests.** `createPostHogProxy({
  upstream: { api, assets } })` replaces PostHog Cloud's hosts.
- **Error tracking.** `capture_exceptions` is off unless `site.exceptions`
  is `true`. Error messages are whatever the code put in them; with it on,
  `before_send` cleans the URLs in stack frames and messages.

## Why each setting

| Setting | Why |
|---|---|
| `api_host: '/ingest'` + the proxy | Same origin: simpler CSP, and one place to control headers |
| `before_send: makeBeforeSend(site)` | Drops everything without current (stored) consent, read from shared storage on every event: a withdrawal in any tab stops all tabs. Drops events on private pages or about them (`$prev_pageview_*` of a private page). Cleans every URL: `$current_url`, `$referrer`, `$session_entry_*`, `$initial_*`, `$elements_chain` hrefs, heatmap keys, web-vitals objects, the replay's meta href |
| `mask_all_element_attributes: true`, and `before_send` keeps an allowlist | Autocapture otherwise sends every attribute of the clicked element and its ancestors: a form's `action` with a reset token, an image's signed `src`, `data-user`, `title`, `aria-label`. With this option it collects none (link targets included). `before_send` rebuilds `$elements_chain` and `$elements` from an allowlist anyway: tag, classes and id that do not look personal, `href` cleaned, position. Its parser ends a value only at a quote followed by a key, the next element or the end: PostHog escapes `"` but not `\`, so a value ending in a backslash cannot shift it |
| `mask_all_text: true`, and `before_send` drops `$el_text` | Autocapture otherwise sends the text of every clicked link or button (`$el_text`, and `text=` in `$elements_chain`), which can be a name, an e-mail or an order number. `before_send` also strips it from `$elements_chain` and `$elements`, and drops `$selected_content` (copied text) |
| `before_send` drops `$fbc`, `$fbp` | Meta's click id and browser id. posthog-js reads them by default: `$fbc` from `fbclid` since 1.426.0 and from the `_fbc` cookie, `$fbp` from the `_fbp` cookie since 1.433.0 |
| `strict_script_versioning: true` | The recorder and other extensions load lazily from PostHog's CDN. The default (`'fallback'`) retries an unversioned URL when the versioned one fails, which can serve a newer, untested build. `true` loads only `/static/<this SDK's version>/…` |
| `mask_personal_data_properties: true` + `custom_personal_data_properties` | The SDK masks `gclid`/`fbclid`… and these query keys in every URL it builds, including `$initial_*`, which are stored as person properties that `before_send` never sees |
| `advanced_disable_feature_flags: true` | `/flags` carries the first URL a browser saw, outside `before_send`. Enable it only if the site uses flags, and then clean that URL first |
| `opt_out_persistence_by_default: true` | When opted out, PostHog keeps nothing in the browser |
| `request_batching: false` | A queued batch would still be sent after a withdrawal (or after the reload that follows it) |
| `session_recording.maskAllInputs` | Typed text never enters a recording |
| `recordHeaders/recordBody: false` + `maskCapturedNetworkRequestFn` | In posthog-js 1.438.3 the recorder ORs the project's network-payload switch with the client's, so a project with network capture on starts the network plugin whatever the client says. The function then returns `null` for every network request (they carry `entryType`, `initiatorType` or `method`), so no request URL, header or body is kept. It passes bare `{ name }` objects, which are how the recorder runs page URLs through it. A plain `() => null` blanks every page URL in recordings. What can still appear, if the project turns network capture on, is the page's own navigation timing with its URL blanked. Keep that project switch off |
| `session_recording.maskAttributeFn` | The recorder stores every attribute of the page, with links and sources as absolute URLs, so `<a href="#faq">` carries the page's query string, tokens included. The function (`maskAttribute`) works like this: URL attributes (`href`, `src`, `data-src`, `lowsrc`, `itemid`…, and any value that reads as a URL with a query or fragment) go through `cleanUrl`, which keeps the host (also of `//host/…`), replaces token-like path segments and drops the query except utm values; `srcset` lists part by part; `url(…)` and quoted URLs in `style`; a refresh target in `<meta content>` keeps its shape. `data:` and `blob:` URLs and plain anchors (`#faq`) stay. `mailto:`, `tel:` and `javascript:` links become `mailto://` and so on, dead in the replay by design. A class token that looks personal is dropped. Structural attributes (SVG geometry, `integrity`, `datetime`, ARIA state, `type`, `role`…) stay as they are. Every other attribute (`title`, `alt`, `aria-label`, `data-*`, `x-data`, `hx-vals`, `for`, `srcdoc`, custom ones) has the URLs in its text cleaned and is blanked when it still looks personal (an e-mail, a phone number, a token). **Never set the recorder's `session_recording.maskAllElementAttributes` as well** (not to be confused with autocapture's `mask_all_element_attributes` above): since posthog-js 1.413.3 it wins when both are set, and `maskAttributeFn` is silently ignored. Text in the page itself is recorded as shown, so a page that prints its own URL or a visitor's e-mail needs `ph-no-capture` there |
| `enable_recording_console_log: false` | Console messages can contain anything |
| `disable_session_recording: isPrivate(pathname)` | Not even a first snapshot of a private page |
| `capture_performance.network_timing: false` | Request URLs, with their queries, stay out |
| `respect_dnt: true` | A third guard. k.js and consent.js honour GPC/DNT, and `startPostHog` refuses to start; posthog-js 1.438.3's `respect_dnt` reads GPC too |
| `disable_surveys: true` | Not part of this setup |

## The proxy

Use `createPostHogProxy({ region: 'eu', prefix: '/ingest' })` for both GET
and POST on `/ingest/[...path]`. In Next.js, also set
`skipTrailingSlashRedirect: true`, because PostHog's endpoints end in a slash.

- **Forwards** only `content-type`, `accept`, `accept-language`, `user-agent`
  and `origin` (plus the conditional headers on GET), and the visitor's
  **full** IP as `X-Forwarded-For` on event calls, for PostHog's location
  lookup. "Discard client IP data" in the project makes PostHog drop it
  after the lookup. Which header holds the real IP depends on what is in
  front of the server: pass `clientIp` (the same function as the
  collector's). The default reads CF-Connecting-IP, else the **last**
  X-Forwarded-For entry (the first is whatever the client sent), never
  X-Real-IP.
- **Never forwards** cookies (a login session would go to PostHog), Referer
  (the full page URL), or the CDN's `CF-Connecting-IP`. PostHog's own CDN
  answers 403 to that header (Cloudflare error 1000), which silently breaks replay.
- **Refuses** `/i/v1/logs` and `/i/v1/metrics` with 204. The project can
  turn console capture ("Logs") on remotely, and the client has no setting
  to refuse it.
- **Not a framework rewrite.** `next.config` rewrites forward every header.

## Project settings (the owner, in PostHog)

- Region **EU** for EU visitors. Sign PostHog's **DPA**.
- **Discard client IP data**: on.
- Replay: **authorized domains** are the production hosts only. **URL
  blocklist**: the private paths as a regex. Console logs and network
  payload capture: off. The client overrides them anyway; this keeps the
  settings honest.
- Heatmaps and dead clicks are pinned on in the client config, and
  exceptions off unless `site.exceptions` is set. To change them, change the
  client config: project switches for options the client sets do not apply.
- Data retention: as stated in the privacy text.
- **Destinations and webhooks: none** that post events to Slack or elsewhere.
  A forgotten destination forwards page data outside the setup this skill
  describes, and the API may show its webhook URL unmasked.
- **`data-ph-capture-attribute-*`** on an element is copied into autocapture
  events as a property by posthog-js, outside the element chain and its
  allowlist. It is the owner's explicit opt-in; never put personal data in
  such an attribute.
- **Test-account filters**: filter Lighthouse (`moto g power (2022)` in the
  user agent) and the team's browsers.

## Headers

For the heatmap viewer, PostHog shows the site in a frame on its own
domain. Allow that on public pages only:
`Content-Security-Policy: frame-ancestors 'self' https://eu.posthog.com`.

Give the app and the token pages `X-Frame-Options: SAMEORIGIN`, or `DENY`
for payment pages. Anchor the route patterns: `/dashboards` is not
`/dashboard`.

## Linking a recording to k.js's visit

`startPostHog` dispatches `k:replay` with a function that returns the
session id only once PostHog has shipped a `$snapshot` for it. A session that
was sampled out, is still too short or is waiting for a trigger has no
recording, and must not get a dead link. k.js adds that id as `ph` to
reports with ids. The collector stores it as `replay`. `visits.mjs` turns it
into `▶ replay`, using the recording link prefix
`https://eu.posthog.com/project/<project id>/replay/`.

## Testing with PostHog

PostHog drops events from automated browsers. It checks
`navigator.webdriver`, the user agent ("HeadlessChrome") and
`navigator.userAgentData.brands`. verify.mjs hides all three. Without that,
"PostHog loads but sends nothing" is a test artefact, not a bug.
