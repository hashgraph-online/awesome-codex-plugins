# Pitfalls and their fixes

Each line gives a problem this kind of setup tends to have, then the fix.
They come from adversarial reviews of the skill's code: each one was
reproduced with real code. SDK facts were checked against posthog-js
1.438.3; re-check them on newer versions.

## PostHog

- **A `rewrites()` proxy leaks.** It forwards every header (cookies, the
  login session) → build the header allowlist proxy (`posthog-proxy.mjs`).
- **The client-IP header breaks assets.** Forwarding `CF-Connecting-IP`
  makes PostHog's asset CDN answer 403 (Cloudflare error 1000), so replay
  never loads → never forward `cf-*` headers. Send the IP only as
  `X-Forwarded-For`, only on event calls.
- **Assets on the wrong host.** `/static` and `/array` belong on the
  *assets* host, everything else on the API host. Keep trailing slashes
  (`/e/`), and in Next.js set `skipTrailingSlashRedirect`.
- **No timeout on the proxy.** With no abort signal, a stalled upstream holds
  sockets for ~300 s → combine the request's signal with
  `AbortSignal.timeout(10_000)` (`AbortSignal.any` on Node 18.17+/20.3+;
  posthog-proxy.mjs falls back to a manual combination on older Node);
  answer 504 on a timeout, 502 otherwise.
- **Bad proxy responses.**
  - Copying `content-encoding`/`content-length` breaks bodies that fetch
    already decoded.
  - A body with 204/304 throws.
  - `Retry-After` should pass through.

  → use a response header allowlist and null bodies for empty statuses.
- **Logs bypass `before_send`.** The project can turn console capture
  ("Logs") on remotely; those records go to `/i/v1/logs` and carry the raw
  URL → the proxy answers 204 to `/i/v1/logs` and `/i/v1/metrics`.
- **`reset()` clears the opt-out.** Withdrawal that calls `reset()` after
  `opt_out_capturing()` switches capture back on → `stopSessionRecording()`
  → `reset(true)` → `opt_out_capturing()` last.
- **Purging the opt-out flag re-enables other tabs.** Every tab reads
  `__ph_opt_in_out_<token>` → purge `ph_*` but keep that flag. Collect the
  keys first, then remove them: removal reorders `storage.key(i)`.
- **Other tabs keep capturing after a withdrawal** → `before_send` reads the
  shared consent on **every** event. Add listeners for `storage`, the
  consent event and `pageshow` (persisted), and reload the withdrawing tab.
- **Other tabs keep PostHog's window id.** sessionStorage is per tab, so
  the withdrawing tab's purge cannot reach `ph_*_window_id` in the others →
  every tab purges its own storage when it sees the withdrawal (`follow`).
- **A tab skips its own reset.** Decide the reset from the tab's own state
  (an `identified` flag), not from the shared opt-out flag, or another tab's
  timing leaves the old identity behind.
- **The Decline click is captured and flushed after the withdrawal** →
  `ph-no-capture` on the banner and on "Privacy settings";
  `request_batching: false`.
- **`/flags` leaks the first URL.** It sends the first URL a browser saw
  (`$initial_*`) outside `before_send` → `advanced_disable_feature_flags: true`
  unless flags are used.
- **Remote config overrides unset options.** It can switch on heatmaps,
  console logs, network headers and bodies → pin every capture option in
  `init`. For network capture the recorder ORs the project's switch with the
  client's (posthog-js 1.438.3), so a project with it on starts the network
  plugin anyway. Pin `recordHeaders/recordBody: false` and the selective
  `maskCapturedNetworkRequestFn` (it drops every network request and
  keeps the recording's page URLs), and keep the
  project switch off.
- **Recordings keep the page's links as full URLs.** rrweb stores
  `<a href="#faq">` as the whole URL, including the query string and tokens, and
  `before_send` cannot reach inside the compressed recording →
  `session_recording.maskAttributeFn` cleans `href`, `src`, `srcset` and the
  other URL attributes (`imagesrcset`, `ping`, URL-like `content`, `url(…)`
  in `style`) before they are recorded. Never combine it with
  `maskAllElementAttributes`: since 1.413.3 that option wins and the
  function is ignored.
- **`maskCapturedNetworkRequestFn: () => null` blanks replays.** It also
  drops the recording's page URLs → return null only for objects with
  `entryType`, `initiatorType` or `method`.
- **Autocapture sends every attribute of the clicked element** (a form's
  `action` with a token, a signed image `src`, `data-user`) → autocapture's
  `mask_all_element_attributes: true`, and rebuild `$elements_chain` from an
  allowlist in `before_send`. Do not clean it with one regex: PostHog
  escapes `"` but not `\`, so a value ending in a backslash swallows the
  next pair.
- **`before_send` must go deep.** URLs and text hide in:
  - `$elements_chain` hrefs and `$elements[]`;
  - `$heatmap_data`, keyed by URL;
  - `$web_vitals_*_event` objects;
  - the replay meta event's `href`;
  - `$prev_pageview_*`, `$session_entry_*`, `$initial_*`;
  - `ph_keyword` (search terms);
  - personal `utm_*` values;
  - element text (`$el_text`, `text=` in `$elements_chain`) and copied text
    (`$selected_content`);
  - Meta ids (`$fbc`, `$fbp`).

  → clean them all (`cleanProperties`). Also set
  `mask_personal_data_properties: true` with your own sensitive parameter
  names.
- **Upgrades add identifiers silently.** `$device_model` (from client
  hints) came in 1.394.0, `$fbc` (from `fbclid`) in 1.426.0, and `_fbp` /
  `$fbp` (from Meta's cookies) in 1.433.0, all on by default →
  `disableDeviceModel: true`, `mask_personal_data_properties: true`, and
  `before_send` drops `$fbc` and `$fbp`. Diff the default config before
  every upgrade.
- **Lazy scripts can be a different version.** The recorder loads from the
  CDN at runtime, and the default `strict_script_versioning: 'fallback'`
  retries an unversioned URL → `strict_script_versioning: true`.
- **Storage from an older setup** (a 365-day cookie on the parent domain,
  `$initial_person_info` with a token URL) is resumed after consent → purge
  on every load without consent, and once more before the first consented
  `init`.
- **Replay records the signed-in visitor.** `maskAllInputs` hides inputs, not
  text or images, so the account menu, avatar, name and e-mail end up in
  recordings → `ph-no-capture` on every element that shows identity, or do
  not record signed-in visitors.
- **`ph-no-capture` on a full-screen overlay** paints the whole replay as
  stripes → put it on a zero-size container, and do not block canvases.
- **Data from unmeasured pages leaks out with a later event.** Buffered
  heatmap points, `$prev_pageview_*` and web vitals from private pages leave
  later, from a public page → drop events whose `$pathname` or
  `$current_url` is private, and drop private heatmap keys.
- **The SDK finishes loading on a private page.** Accept, then a quick
  route into a private page → decide `disable_session_recording` from the
  page PostHog starts on, and stop or start recording on every route.
- **"Recording started" ≠ "recording kept".** Sampling, minimum duration
  and triggers mean some started recordings are never stored → link a replay
  only for sessions with a shipped `$snapshot` (`on('eventCaptured')`).
- **Defaults capture without consent.** By default PostHog captures and
  records → never import it before consent.
- **`cookieless_mode: 'on_reject'` still processes people who decline.** It counts them
  with a server hash and captures nothing until an answer → not used here.
  The first-party totals cover people who decline.
- **Bot filtering misses Lighthouse.** It emulates "moto g power (2022)"
  without saying Lighthouse → filter that UA string in the project and the
  collector.
- **`$prev_pageview_duration` is wall-clock time.** Tabs left open give
  days → measure active seconds yourself (k.js).
- **Destinations and webhooks forward data.** A forgotten destination can
  send page data to Slack, and the API can return its webhook URL unmasked
  → audit them all, disable unknown ones, rotate exposed URLs.
- **The SDK delays first paint.** ~100 KB gzipped → load it only after consent, when
  idle. Start the small tracker early.
- **GeoIP stores a location.** "Discard client IP" still stores a location
  derived from the IP (city level by default) → disclose it, or limit
  GeoIP to country.

## Headers

- **The heatmap viewer needs framing.** It frames your pages on PostHog's
  domain → `frame-ancestors 'self' https://eu.posthog.com` on public pages
  only, and `X-Frame-Options` elsewhere. Exactly one framing header per path.
- **Loose path patterns.** `(?!dashboard)` also excludes `/dashboardx` →
  anchor patterns to whole segments: `(?:dashboard|account)(?:/|$)`. Test
  look-alike paths with curl.
- **Same-origin Referer.** Same-origin requests carry the full page URL,
  including the query → never forward Referer; send only the referrer **host**
  from the tracker.
- **Spoofable client-IP headers.** `CF-Connecting-IP` can be forged when the
  origin is reachable directly → trust it only behind the CDN, or remove the
  public origin hostname. The first X-Forwarded-For entry and X-Real-IP are
  whatever the client or a pass-through proxy says → use the last
  X-Forwarded-For entry, or the one header your own proxy sets.
- **A private-path rule that does not parse fails silently** (a missing
  closing slash, an unknown flag) and the private pages get measured →
  parse it one way everywhere and fail closed.
- **Server jobs may be blocked by your own CDN.** If bot protection
  challenges datacenter IPs, a scheduled job cannot fetch the site's public
  domain → read the database directly, or use an internal hostname.

## Tracker

- **Click labels can carry typed text and identity.** Textarea content
  (React mirrors it into the DOM) and an account e-mail in the nav end up
  in them → label only allowlisted elements inside `<main>`, never anything that
  is or holds a field; the collector also cuts personal-looking labels.
- **Rage clicks on working controls** (carousels, divs with React
  `onClick`) → skip interactive elements. Give clickable divs
  `role="button"`, which also fixes their accessibility.
- **A route change measures the old view against the new DOM** (100% depth
  from a one-screen page) → ignore measurements while `location.pathname`
  differs from the view's path.
- **A scroll-locked menu fakes 100% depth**
  (`body { position: fixed }` collapses the height) → skip measuring while
  the body is fixed.
- **Smooth scrolling after a route** records depth nobody reached →
  `data-scroll-behavior="smooth"` on `<html>` (Next.js 16).
- **Plain `<a>` links split visits.** They do full loads → `next/link`, or
  the router, for internal links on measured pages.
- **Reload, back/forward and same-site loads double-count.** They count as
  new visits, and the "same-site referrer" rule misses visits that start on
  private pages → continue a visit only on reload/back_forward, or a
  same-host referrer that is a *measured* path. Continued loads send no entry
  and no histogram moves.
- **Per-visit rows lack country, device and source** when the entry rides only
  on the first view, which comes before consent → repeat the entry once (`en: 2`) on
  the first report with ids; the collector counts it only once.
- **A stored visit id links visits.** A sessionStorage id can survive reloads,
  session restore, and even days → the id lives in memory by default; the opt-in
  `session` store expires after 30 idle minutes and is deleted on withdrawal.
- **Client and server path rules drift apart.** A path the collector rejects
  uses up a visit's entry and corrupts the histogram → one path rule on both
  sides; never start a view the collector would drop.
- **Videos never stop counting.** A "playing" flag stays on when the file
  stalls → count activity from `timeupdate` while the playhead moves.
- **The Clipboard API fires no `copy` event** → mark copy buttons
  (`data-kui="copy-…"`).
- **Forms need explicit goals.** Clicks on buttons are not conversions →
  dispatch `k:goal` from the success path.
- **Classify CTAs by intent, not by URL.** A "Buy" link to the app counts
  as "sign in" → name kinds with `data-kcta`; the totals keep only the kind.
- **Funnels cannot be joined later from totals** → decide "goal after X" in
  the browser, where the visit's steps are known.
- **Section keys from headings drift** with copy and language → `data-k` on
  every measured section, the same key in every language.
- **Wrapper components drop `data-*` props** → check the rendered HTML.
- **The team's visits dominate a small site** → the owner opt-out (`?k=off`),
  plus a host allowlist so staging never reports.
- **Beacons sent as JSON trigger a preflight, and unload fetches are
  cancelled** → `sendBeacon` with a text/plain string, `fetch` keepalive as
  fallback, flush on `visibilitychange` and `pagehide`.
- **Error messages quote what the code had at hand** (an e-mail, a URL with
  its query, a JSON body) → scrub in the browser and again on the server,
  keep the file name only, never ids on an error, and read the samples.
- **An error thrown from `page.evaluate` or `addScriptTag` has no file**, so
  a same-origin filter drops it and a test passes for the wrong reason →
  inject an inline `<script>` into the served HTML (verify's `--errors`).
- **Chrome skips low-detail images as LCP candidates** (under 0.05 bits per
  pixel, e.g. a one-colour SVG) and the banner's text can win instead → test
  LCP with a real image, with the banner answered.
- **A soft route has no LCP or TTFB of its own** → vitals belong to the page
  load's first view; a bfcache restore resets CLS and INP only.

## Collector and storage

- **Browser strings become keys in the totals.** Personal utm values and
  referrer subdomains turn into keys kept for 2 years → only known
  `utm_source` values become sources; drop personal-looking values; reduce
  unknown referrers to their site; cap distinct keys per day.
- **Exact timestamps date a visitor.** On a quiet day, the totals' timestamps
  identify the one visitor → date totals by day (noon UTC), no `updatedAt`.
- **Anyone can attach ids**, so rows can be flooded → cap rows per day;
  past the cap, count in the totals only.
- **A throttle can keep IPs.** A naive one holds them forever, keys IPv6
  by the full address and can be blinded by a flood → sweep on a timer, key IPv6 by /64, evict the
  oldest rather than refuse. The real rate limit belongs at the edge.
- **Mongo index failures.** A failed `createIndex` can leak clients, and
  changing a TTL constant fails with code 85 → create TTL indexes before the
  first write, close the client on failure, change a TTL with `collMod`.
- **A 204 hides a database outage** → the collector keeps a health record
  (last write, failed writes by error class) off the hot path, and
  `assets/health.mjs` alerts an ops channel on failed writes, hours without a
  visit, a day far below usual, a goal that stopped, and 404 spikes; see
  `alerts.md`. Log failures at most once a minute.
- **A retention period that nothing enforces.** SQL and file stores have no
  TTL, and Slack keeps a bot's lines → `assets/retention.mjs` once a day
  (`enforceRetention`, `deleteOldSlackLines`), and `retentionStatus` to show
  the promise holds (`collector.md`, "Retention").
- **Day boundaries.** Days in UTC split European evenings → compute days in
  the owner's time zone, in the writer and the reader alike.

## Consent banner

- **A smaller or greyer Decline, or a close button that means neither,**
  makes refusing harder than accepting, which regulators have cited as making
  consent not freely given → one style for both buttons, no "X".
- **On phones, the banner over a fixed bar takes taps meant for it** → keep
  it under menus and sheets, and clear of bottom bars.
- **The banner flashes, or hydration warnings** → read the answer with
  `useSyncExternalStore` (React).
- **Screen readers miss the banner, keyboard users tab through the whole
  page, and focus is lost** → a live region in the server HTML, the banner
  early in the DOM, focus to Decline on reopen and back afterwards.
- **Blocked storage makes the banner undismissable** → keep the answer in
  memory for the page load; a newer stored answer from another tab wins.
- **No date, no expiry.** Store the answer with its date, and let it
  expire (12 months is a common default; check your regulator's guidance,
  for example CNIL's).
- **Error pages often lack "Privacy settings"**, or the footer link is
  unreadable → put the control on every template, with real contrast.
- **Banner text that names only one tool.** When Accept also enables per-visit
  rows and Slack lines, the consent may not count as informed → name
  everything Accept turns on, and its retention.
- **Other cookies on page load also need consent.** A "convenience" cookie
  (time zone, referral) set for every visitor is not strictly necessary →
  write it only when the visitor starts the action that needs it.
- **Library defaults.** Common consent libraries default to longer expiries,
  load modes that run before consent, or styles that favour Accept → set
  every option explicitly.

## Slack

- **Slack lines that quote app data.** Post only what the visitor did;
  never mirror message text, form input or data from third-party
  integrations.
- **Visits crossing midnight get posted twice**, and saving state after
  posting duplicates lines → one state document, saved before posting.
- **The visit count on a Slack parent message can go stale** (nested
  objects shared between old and new state hide changes) → deep-copy the
  state, and redraw parent messages on the first poll after a restart.
- **A daily cap silently drops conversions** → only goal visits pass the
  cap; say "+N not shown".
- **Reading the oldest rows first** cuts today's visits → newest first, and
  log when the read limit is hit.
- **Slack keeps the bot's copies forever** → set channel retention, or
  state the real period.

## Process

- **A privacy sentence can drift from the code.** Words like "anonymous",
  a deletion promise or a retention period stop being true when the code
  or a vendor setting changes → check every sentence against the code and
  settings, and again after every change.
- **Tests that never run.** If your project is a monorepo, check that CI
  actually runs the analytics tests.
- **Mutation-test the wiring.** Deleting a listener registration or a single
  option can keep a suite green → test through the real init path.
