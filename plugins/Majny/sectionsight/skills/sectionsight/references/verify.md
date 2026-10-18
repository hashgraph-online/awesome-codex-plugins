# Verifying it

`scripts/verify.mjs` drives a real Chromium against the running site and
checks what is stored and sent, before consent, after it, after withdrawal,
and under Global Privacy Control. It exits non-zero on any failure and
writes a JSON report (`--json`, default `privacy-check.json`).

## Running it

```bash
# once, in a scratch directory (not the project: it would change the lockfile,
# and the report is written to the current directory)
mkdir -p /tmp/sectionsight-verify && cd /tmp/sectionsight-verify && npm i playwright && npx playwright install chromium
node <this skill's directory>/scripts/verify.mjs \
  --url http://192.168.1.20:3000 \      # the site; see "Which host" below
  --pages /,/pricing,/blog/some-post \  # public pages that have sections
  --private /account/x,/reset/abc \     # private paths that must stay silent
  --mode consent \                      # never | consent | always (k.js data-ids)
  --banner yes \                        # yes for model B; no for A and C
  --collector /api/k \                  # the collector path
  --posthog /ingest                     # the PostHog proxy prefix, if PostHog is used
```

**Other flags:**

- `--accept` / `--decline` / `--settings`: selectors for Accept, Decline and
  "Privacy settings". The defaults match consent.js.
- `--settings-page /privacy`: where the withdrawal control is, if it is not
  on the first page. Every page should have one; this flag is for checking
  sites that do it differently.
- `--allow-storage k1,k2`: storage keys allowed before consent. The default
  is the consent keys.
- `--allow-cookies name`: cookies allowed before consent. Only strictly
  necessary ones, each justified.
- `--no-write`: reports and PostHog events are captured in the browser and
  answered there, so nothing reaches the server. **Use it against
  production.**
- `--resolve example.com`: the browser resolves that name to 127.0.0.1, so a
  local server is checked under its production name. Use it when
  `data-hosts` lists only production hosts, and with `next dev`, which
  refuses LAN-IP origins. posthog-js also behaves differently on localhost.
  It does not work with `http://` on HSTS-preloaded top-level domains
  (`.dev`, `.app`, `.page` and others): the browser forces https there.
  Serve the local copy over https, or resolve a name under another TLD
  (`example.test`) and add it to `data-hosts` and the collector's `hosts`
  in the development build.
- `--path-probe /blog/<token>`: a path whose last segment is token-like,
  visited before and after consent; that segment must never appear in a
  report, a PostHog event or a recording. The default is the first page
  plus a nanoid-shaped segment (`/Pq7xK2mZ9_wR4tY-8sLnB`). A 404 there is
  fine (a 404 page usually runs the tracker); if no report comes from it,
  the check is skipped, not passed. `--path-probe no` turns it off.
- `--settle 8000`: how long (ms) the last page stays open before storage
  and cookies are read again, for scripts that write late. `0` skips it.
- `--allow-hosts fonts.example.net`: other hosts the page may contact before
  consent (a CDN). Every other host contacted before consent fails a check.
- `--consent-key analytics-consent`: where the answer is stored, for the
  expiry check (consent.js's default).
- `--headed`: watch it.
- `--config privacy-check.config.json`: read the settings from a file (see
  "The config file" below). Flags on the command line win over it.
- `--json results.json`: where the full results go (default
  `privacy-check.json`; `--report` is the older name).
- `--github`: in GitHub Actions, also append a table of the checks (name,
  PASS/FAIL/SKIP, short detail) to `$GITHUB_STEP_SUMMARY` and print an
  `::error` annotation per failure. Details quote pages and headers, so
  they are printed on one line, never starting with `::`, and between
  `::stop-commands::<random token>` and `::<token>::`: a page cannot issue
  workflow commands (`::add-mask::`, `::error`) through verify's output.
- `--preview`: the URL is a preview deployment. Previews often share the
  production database, so it runs read-only like `--no-write` unless the
  config says `"previewWrites": true` (previews have a store of their own).
  The workflow's preview job passes it.
- `--delete-button '[data-consent-delete]'`: the "Delete my visit data"
  button in the reopened banner (consent.js's default). After an Accept,
  verify reads a page, reopens the banner and clicks it: the request must
  carry `{"del":"<this visit's id>"}` and nothing else (no other field, no
  query in the request URL, no probe), and consent must be withdrawn. SKIP
  when the site offers no such button.
- `--rows-url /__rows`: a same-origin JSON endpoint of a **test or staging**
  store that answers `{ "rows": [...] }`; with it (and without
  `--no-write`) verify also checks that the visit's rows are gone. Never
  expose such an endpoint in production.
- `--errors`: the site runs k.js with `data-errors="on"`. verify answers
  the first page's HTML with one inline `<script>` added (in a context of
  its own with the page's CSP bypassed) that, 1.5 s after load, rejects a
  promise and throws an `Error` whose message holds the probe e-mail (including a
  percent-escaped copy, `%40`), the probe token, `location.href` (the probe
  query) and a relative query (`/account?e=<token>`). An inline script
  reports the page's own URL as its file, so k.js treats it as the site's
  own (`(inline)`); code run through `page.evaluate` or `addScriptTag`
  reports no file and would be dropped, which is why the HTML is changed
  instead. The `err` reports must carry no probe, no URL or query and no
  `vi`/`v`/`ph`, before consent and (after an Accept) after it. SKIP when no
  `err` report arrives (errors off, or an older k.js). With `--no-write`
  the reports are answered in the browser like every other.
- `--consent-counts`: the site counts consent.js's banner events (k.js
  `data-consent-counts="on"`, the collector's `consentCounts`). In the
  consent run (Accept, then a withdrawal from the reopened banner) every
  `consent` report must carry no `vi`/`v`/`ph`, no entry and no probe,
  including the Accept and the withdrawal. SKIP when no `accept` report arrives.
  Under Global Privacy Control the general check "nothing is sent" covers
  them.
- `--fail-on-skip`: a SKIP fails the run too (exit 1). Use it once every
  check applies to the site, so a check that silently stopped running (the
  tracker gone from the 404 page, a removed banner) is noticed.

**Broken things** (read-only, so they also run with `--no-write`; their
visits are answered in the browser, so they never store a report):

- `--expect 'a[data-kcta=whatsapp]@href=^https://wa\.me/\d+'`
  (repeatable): on every `--pages` page the CSS selector matches at least
  one element, and each match's attribute matches the regex. The attribute
  is read as written in the HTML (`getAttribute`), so a relative `href`
  stays relative. Without `@attr=regex` only presence is checked. The
  selector is the part before the first `@` followed by `name=`.
  Client-rendered elements are waited for up to 5 s.
  **The `@` limitation:** the string form splits at the first `@` that is
  followed by an attribute name and `=`, so a selector that itself contains
  such an `@` (rare, e.g. `a[href*="@x="]`) is cut in the wrong place. Use
  the config file's object form, `{ "selector", "attr", "match" }`, which is
  never split. `"expect": false` (or any non-string, non-object) is a
  config error (exit 2).
- `--indexable /,/pricing`: each answers 200 without a redirect, has no
  `noindex` (or `none`) in `<meta name="robots">`/`<meta name="googlebot">`
  (in the server's HTML or added by a script) or in an `X-Robots-Tag`
  header (one scoped to another crawler, `otherbot: noindex`, does not
  count; unscoped, `googlebot:` and `bingbot:` ones do), and robots.txt does not disallow it. A robots.txt that answers
  5xx fails it too: crawlers read that as "disallow all".
- `--noindex /thanks`: has `noindex` in the meta tag or the header, and
  robots.txt does **not** block it (a blocked page's `noindex` is never
  read, and a blocked URL can still be indexed from links to it). A 404
  is a SKIP: probably a wrong path. A `noindex` added only by a script
  passes with a warning in the detail.
- `--sitemap` (or `--sitemap /path.xml`): the sitemap (robots.txt's first
  `Sitemap:` line, else `/sitemap.xml`) answers 200 with XML (a redirect
  within the site is followed and noted in the detail; one to another site
  fails); every `<loc>`
  is on the expected host; up to 20 of them, spread over the list, answer
  200 to HEAD (GET when HEAD is refused) without a redirect. A sitemap
  index is followed to its first 5 sitemaps. The expected host is the
  `--url` host, or `--sitemap-host www.example.com` when the sitemap names
  production while you check a preview: then the `Sitemap:` URL and the
  sampled URLs are fetched from `--url` at the same path.
- **The 404 page** (always): verify opens `/sectionsight-check-missing-page` with
  the probe query. If the page carries k.js's `data-k404` marker, an `nf`
  report must arrive with exactly that path, no query and no probe;
  without the marker it is a SKIP with a hint (mark the template,
  `tracker.md`). A separate check fails when the missing path answers
  anything but 404 or 410: a "soft 404" that search engines may index,
  and on hosts that serve the home page for every path, broken links that
  never show up.
- **Nothing broken** (always): every page opened in the run is watched for
  uncaught errors and console errors. It fails on an error or a CSP
  violation that comes from k.js, consent.js or the PostHog guard, and on a
  hydration error (React #418/#423/#425: a node put into a framework's
  `<body>` before it hydrates; use consent.js `mount: 'end'`). The site's
  own console errors are counted in the detail, not judged.
- `--privacy-page /privacy`: the privacy text names every recipient:
  PostHog (with `--posthog`), each of `--processors` (the ones the browser
  never talks to, such as a server that forwards to Umami), and every other
  host the pages sent a request to, by its domain's own label
  (`eu.i.posthog.com` → "posthog", `cdn.jsdelivr.net` → "jsdelivr").
  `--processors "Google Fonts=fonts.gstatic.com"` names a host's company
  when the label is not what the text says. Read-only. It checks that a
  name is there, not that the text is right, and not that a DPA is signed:
  that stays on the owner's list.
- **The collector's answers**: "the collector receives reports" fails when
  any report is answered with an HTTP error (a skip rule that does not
  parse makes the Cloudflare recipe answer 500 to everything).

**robots.txt, as verify reads it.** Only the `User-agent: *` group, not a
crawler's own group (`User-agent: Googlebot` rules are ignored, while
Googlebot obeys only its own group when one exists); `*` and a final `$`
in paths; the longest matching rule wins and `Allow` wins a tie; no
percent-decoding, no `Crawl-delay`, no `noindex` lines. For a definitive
answer use the search engine's own tester (Google Search Console's
robots.txt report).

Exit codes: 0 all passed, 1 a check failed (or skipped, with
`--fail-on-skip`), 2 a usage or config error, or Playwright missing.

## The config file

`--config` reads a JSON object whose keys are the flags' names, in
camelCase or as written (`allowHosts` or `allow-hosts`). Lists may be
arrays or comma-separated strings, switches are `true`/`false`. Keys that
start with `_` or `$` are ignored (comments, `$schema`); any other unknown
key stops the run with exit 2, so a typo never silently drops a check.
Keep the URL out of the file: CI passes the preview or production URL with
`--url`, and a local run passes its own. Keep `resolve` out too: it maps a
host to 127.0.0.1 and would break a run against production; pass it on
the command line of the local run.

| Key | Flag | Example |
|---|---|---|
| `pages` | `--pages` | `["/", "/pricing"]` |
| `private` | `--private` | `["/account/x", "/reset/abc"]` |
| `mode` (or `ids`) | `--mode` | `"consent"` (`never`, `consent`, `always`: k.js `data-ids`) |
| `banner` | `--banner` | `true` |
| `collector` | `--collector` | `"/api/k"` |
| `posthog` | `--posthog` | `"/ingest"` |
| `accept`, `decline`, `settings`, `settingsPage` | same | selectors and the page with the withdrawal control |
| `consentKey` | `--consent-key` | `"analytics-consent"` |
| `allowStorage`, `allowCookies`, `allowHosts` | same | `["fonts.example.net"]` |
| `pathProbe` | `--path-probe` | `"/blog/Pq7xK2mZ9_wR4tY-8sLnB"` or `false` |
| `settle` | `--settle` | `8000` |
| `noWrite` | `--no-write` | `true` (better passed on the production command line) |
| `failOnSkip` | `--fail-on-skip` | `true` |
| `errors` | `--errors` | `true` (k.js runs with `data-errors="on"`) |
| `consentCounts` | `--consent-counts` | `true` (k.js runs with `data-consent-counts="on"`) |
| `expect` | `--expect` (repeated) | `["footer a@href=^/privacy$", {"selector": "a[data-kcta=whatsapp]", "attr": "href", "match": "^https://wa\\.me/\\d+$", "pages": ["/"]}]`: a string is checked on every page, an object on its own `pages` |
| `indexable` | `--indexable` | `["/", "/pricing"]` |
| `noindex` | `--noindex` | `["/thanks"]` |
| `sitemap` | `--sitemap` | `true`, or a path |
| `sitemapHost` | `--sitemap-host` | `"www.example.com"` |
| `privacyPage` | `--privacy-page` | `"/privacy"` |
| `processors` | `--processors` | `["Umami", "Google Fonts=fonts.gstatic.com"]` |
| `json` | `--json` | `"privacy-check.json"` |

`assets/ci/privacy-check.config.example.json` is a starting point.

## Which host

- **`data-hosts`.** k.js runs only on hosts in `data-hosts` when that is set.
  For local runs, use a host that is in the list: the LAN IP
  (`ipconfig getifaddr en0` on macOS) or a `*.localhost` name. Add it to the
  list in a development build.
- **Collector origins.** The collector drops reports from Origins outside
  its `hosts`. Add the test host there too, in development only.
- **Production.** Use `--no-write`, so the run leaves no data behind.

## What each check means, and the usual fix

| Check | Typical cause of a FAIL | Fix |
|---|---|---|
| before consent: no cookies | an auth library, a chat widget, an A/B tool, a "remember referral" cookie | load it after consent, or justify it as strictly necessary and pass it to `--allow-cookies` |
| before consent: nothing stored | a script writing localStorage, sessionStorage, IndexedDB (`idb:<name>`) or Cache Storage (`cache:<name>`) on load (PostHog loaded too early, theme or referral keys, a service worker's cache) | gate it on consent; for a UI preference, store it only when the visitor sets it; a strictly necessary store goes in `--allow-storage` with its reason |
| no PostHog request before consent | PostHog imported statically or initialised before the answer | dynamic `import()` inside `startPostHog`, only after consent |
| no third-party tracker | GA, GTM, pixels in the template | remove them or put them behind consent |
| a refusal is remembered | Decline stores nothing, so the banner returns on every page | store the refusal (the answer itself needs no consent) |
| the collector receives reports | k.js not loaded, `data-hosts` excludes the test host, automation not hidden, wrong `--collector` | load it; test on a listed host |
| reports carry no ids before consent | `data-ids="always"` on a model-B site, or `consent` reads the wrong key | match `data-consent-key`/`value` to consent.js |
| probe e-mail or token never sent | a query string reaches a report or an event (custom tracking code, a PostHog property) | k.js sends no query; for PostHog, `before_send` and `mask_personal_data_properties` |
| a token in the path is never sent | a tracker or PostHog property that reports `location.pathname` or `href` raw; the page prints its own URL into the recorded DOM | k.js's `cleanPath`; posthog-guard's `cleanUrl` and `maskAttributeFn`; for pages whose path names a person, `skip` |
| view, read and time reports | no sections (`main section` or `data-k`), or the page is too short to cross the 40% line | mark the sections with `data-k` |
| private paths: nothing (before and after consent) | `skip` missing in k.js, the collector, consent.js or posthog-guard's `private` | the same regex in all four |
| before consent: no request to another host | fonts, CDNs, embeds, analytics on other hosts | self-host them, load them after consent, or allow them with `--allow-hosts` and list them in the privacy text |
| GPC after an earlier Accept | consent read without checking GPC/DNT | `analyticsConsent.get()` (consent.js) answers `denied` under GPC; `startPostHog` refuses too |
| a 400-day-old Accept has expired | k.js or PostHog reading the raw stored value | check `<key>-at` (k.js does; set `data-consent-max-age-days` to match `maxAgeDays`) |
| after consent: ids, PostHog sends events | Accept not wired to start PostHog; the `consent` key mismatches | `onGranted` → `startPostHog` |
| withdrawal checks | batching on, no reload, the opt-out flag deleted, a tab that keeps recording | `stopPostHog()` exactly as written; `request_batching: false`; `before_send` reading consent on every event |
| GPC: nothing sent | a script ignoring `navigator.globalPrivacyControl` | check GPC/DNT before loading anything |
| delete my visit data: … | a deletion request that adds the page URL or other fields, a query on the endpoint, k.js missing `deleteMyData`, a collector with `deletion: false` or a store without `deleteVisit` | send exactly `{ del }` (k.js does); keep the collector's deletion on, or do not offer the button |
| consent counts: totals only, no ids (the Accept too) | the banner's events sent through a path that adds ids (a custom `send`, k.js's `noIds` argument removed) | k.js's `consentEvent` as written |
| errors: an err report, scrubbed, without ids | an error report built by custom code from `error.message` or `location.href`, k.js's `scrubError` edited out, ids added to `err` | k.js's `jsError` as written; send nothing of your own with the message |
| 404 page: an nf report with the path only | the marker on the template but k.js not loaded there, `data-skip` matching it, or custom code sending `location.href` | load k.js on the 404 template; send nothing of your own with the URL |
| expect … | a CTA pointing to an old number or a staging URL, a component that dropped `data-kcta`, a link renamed | fix the link; never loosen the regex to make it pass |
| indexable: … | a `noindex` left from staging (meta or `X-Robots-Tag` set by the host for preview domains), a broad `Disallow`, a redirect | remove it in production; list the final URL |
| noindex: … | the page only blocked in robots.txt, or the tag missing | `<meta name="robots" content="noindex">` or the header, and let crawlers fetch it |
| privacy page … names every recipient | a vendor added to the site but not to the privacy text, PostHog turned on later, a font or script CDN nobody listed | name it and what it receives (`privacy-policy.md`), or self-host the file |
| sitemap: … | the sitemap generated with the staging host, removed pages still listed, `http` vs `https` or `www` mismatch | regenerate from the production host, list only live canonical URLs |

**Never make a check pass by weakening it.** Fix the site, or, for a cookie
that is truly necessary, allow it explicitly and write down why.

**What these checks cannot see.**

- An opt-out called *before* `reset()` instead of after is invisible while
  `before_send` checks consent on every event; the order still matters, so
  keep `stopPostHog()` as written.
- A check only covers the pages, paths and query probes it visits: private
  pages it was not told about stay untested.
- **Anything a server does after the request.** verify sees what the
  browser sends. A framework rewrite (`next.config` rewrites, a CDN rule)
  that proxies `/ingest` to a vendor and forwards the visitor's `Cookie`
  and `Referer` looks exactly like the safe proxy from the browser. See the
  manual check below.
- A path segment that names a person (`/u/jane-doe`) cannot be told from
  any other slug. Only the private-path list protects it.
- Legal validity: whether the banner text, the legal basis or the retention
  satisfy the owner's regulator.

## Testing in automated browsers (if you write your own tests)

- **PostHog's bot filter.** PostHog drops events when `navigator.webdriver`
  is true, the user agent contains "HeadlessChrome", or
  `navigator.userAgentData.brands` names a headless browser. Override all
  three (verify.mjs does). Otherwise "PostHog loads but sends nothing" is a
  test artefact.
- **k.js under automation.** It is off under `navigator.webdriver`; use
  `data-allow-automation="1"` only in test builds, or override webdriver.
- **The collector's bot filter.** It drops "HeadlessChrome" user agents. Set
  a normal user agent on the test browser.
- **Seeing beacons.** `sendBeacon` with a string body is visible to
  Playwright. With a Blob it is not, which is why k.js sends a string.
- **Hidden windows.** A browser window off-screen reports
  `document.visibilityState === 'hidden'`, and IntersectionObserver and
  requestAnimationFrame stop. Override `visibilityState` or use a visible
  window.
- **Waiting for visit lines.** A visit line appears 30 minutes after the
  visit goes quiet. Check the rows in the database, not a 204: the
  collector always answers 204, even when the database is down.

## Manual checks after verify passes

- [ ] **Headers.** One framing header per path. With PostHog heatmaps, public
  pages send `frame-ancestors 'self' https://eu.posthog.com`, and the app and
  private pages send `X-Frame-Options`. Test look-alike paths too
  (`/dashboards` is not `/dashboard`):
  `curl -sD - -o /dev/null https://site/path`.
- [ ] **The proxy.**
  - `curl -X POST https://site/ingest/i/v1/logs` answers 204.
  - `/ingest/static/array.js` answers 200, even with a `Cookie` and a
    `CF-Connecting-IP` header.
  - **No header forwarding.** Find what really serves `/ingest` (the
    route file, `next.config` rewrites, CDN or hosting rules, a reverse
    proxy). It must be `posthog-proxy.mjs` or the same header allowlist,
    never a rewrite. To test it, run a development copy with the upstream
    host in your copy of the proxy pointed at a local echo server, then
    `curl -H 'Cookie: session=probe' -H 'Referer: https://site/x?token=probe' https://site/ingest/e/`:
    neither header may arrive.
- [ ] **The collector.**
  - `curl -X GET /api/k` answers 405.
  - A POST from a foreign Origin stores nothing.
- [ ] **Retention.** TTL indexes or the nightly delete exist in the database.
- [ ] **Slack.** A line of a test visit shows no IP, name, e-mail, phone or
  token. Visit with `?email=probe@example.com&token=…` and look.
- [ ] **"Privacy settings"** is present on every page template, including
  404 and error pages.
- [ ] **Phones.** On a 360×640 and a 390×844 viewport, the banner covers no
  control: no tap can hit a button through it.
- [ ] **The privacy page** matches what was built (`privacy-policy.md`).
- [ ] **The owner opt-out.** `?k=off` stops reports from that browser.

## In CI

`assets/ci/privacy-check.yml` is a GitHub Actions workflow template. Copy
it to `.github/workflows/`, copy `scripts/verify.mjs` into the repository
(the template expects `scripts/privacy-check/verify.mjs`), write
`privacy-check.config.json`, and edit the `env` block at the top: the
production URL, and the install, build and start commands and the URL of
the local fallback. It has three jobs:

- **Pull requests, against a preview deployment.** Hosts that post GitHub
  deployment statuses for previews (Vercel, Netlify and Cloudflare Pages
  can, through their GitHub integrations) trigger a `deployment_status`
  event with the preview URL. Set the repository variable
  `PRIVACY_CHECK_PREVIEW` to `deployment` to use it. The job checks out the
  deployed commit and runs verify against `environment_url`. A preview
  behind a login (Vercel's deployment protection, for example) cannot be
  checked this way: turn the protection off for previews or use the local
  fallback. The job skips deployments marked as production
  (`production_environment`), and runs with `--preview`: **previews often
  share the production database**, so nothing is written unless the config
  says `"previewWrites": true` because previews have a store of their own.
- **Pull requests, started on the runner** (the default). The job installs,
  builds and starts the site, waits until `LOCAL_URL` answers, and runs
  verify against it. `k.js`'s `data-hosts` and the collector's `hosts` must
  accept that host in this build; or use a production-like name with
  `LOCAL_URL: http://example.test:3000` and `LOCAL_ARGS: --resolve
  example.test` (see "Which host").
- **Nightly against production, and on demand.** `schedule` and
  `workflow_dispatch` run verify against `PRODUCTION_URL` with
  `--no-write`, so nothing is stored.

Each job installs Playwright in a scratch directory (never in the project),
caches Chromium by Playwright version, runs verify with `--github`, and
keeps `privacy-check.json` as a workflow artifact. The token is read-only
(`permissions: contents: read`) and actions are pinned to a major version
(pin them to a commit SHA if the repository's policy asks for that).

**Blocking or warning** is the owner's choice (SKILL.md asks):

- *Block merges:* keep `WARN_ONLY: 'false'` and mark the pull-request job
  ("privacy check (pull request)", or the preview one) as a required status
  check in the branch protection rules or ruleset.
- *Warn only:* set `WARN_ONLY: 'true'`. The job stays green, and the table
  in the job summary shows what failed.

**Alerting for the nightly run.** GitHub e-mails a failed scheduled run to
the person who last changed the `cron` line, if their notification
settings allow it; that is the default and needs nothing else. For a team
channel, add a final step with `if: failure()` that posts to a Slack
incoming webhook kept in a repository secret, or subscribe the channel to
the repository's workflow runs with the GitHub app for Slack. In public
repositories GitHub disables scheduled workflows after 60 days without
activity in the repository; re-enable them in the Actions tab.

**Run it the same way locally** with the same file:

```bash
node <skill>/scripts/verify.mjs --url http://example.test:3000 --resolve example.test \
  --config privacy-check.config.json
```

**Broken links** across the whole site are lychee's job, not verify's:
`assets/ci/links.yml` checks the links between the built pages offline on
every pull request, and every link on the live pages listed in its `PAGES`
(including other sites') once a week. Set `BUILD_DIR`, `BASE_URL` and
`PAGES` at its top. Broken links that visitors actually follow show up
as `nfin.*` in the collector's totals (`collector.md`). Run `--sitemap` in
the nightly production run rather than on previews, or pass
`--sitemap-host` on previews. Clean URLs (`/pricing` for `pricing.html` or `pricing/index.html`) resolve through lychee's `--fallback-extensions` and `--index-files`; paths that only the running app serves (an account area, API routes) go in `EXCLUDE`.

**Uptime is a different job.** verify runs once a night; it does not tell
you the site is down at noon. Use an uptime monitor for that, such as
[Upptime](https://github.com/upptime/upptime) (GitHub Actions, no server)
or [Uptime Kuma](https://github.com/louislam/uptime-kuma) (self-hosted,
which also warns before the TLS certificate expires).

**Also worth having:**

- **Mutation-test the wiring.** Remove `request_batching: false`, swap the
  withdrawal order, or unwire `before_send`, and make sure a test fails.
  Such mutants can survive unit tests until the wiring itself is tested.
- **A consent auditor** adds a second opinion on the live site:
  [consentdiff](https://github.com/Elijas121/consentdiff),
  [ecom-cookie-audit](https://github.com/kgelster/ecom-cookie-audit) or
  [gdpr-cookie-scanner](https://github.com/Slashgear/gdpr-cookie-scanner).
  Teach it PostHog's `ph_*_posthog` cookie, which common tracker lists lack.
