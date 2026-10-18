# The collector

`assets/collector.mjs` is one POST endpoint written against the Fetch API,
with no dependencies. It checks every report, cuts it down to what the
totals and rows use, and stores it. The same endpoint takes a visitor's
own deletion request (see "Deletion" below). Every POST gets `204` with no
body (other methods get `405`).

## What it does with a request

1. **Not POST:** `405`.
2. **Who:** the report is ignored (nothing is stored) if any of these
   apply:
   - Global Privacy Control (`Sec-GPC: 1`) or Do Not Track (`DNT: 1`);
   - no user agent;
   - a bot user agent (crawlers, headless browsers, Lighthouse, uptime checkers).

   Otherwise: the country from the CDN header (see below) and a device
   class (`mobile`, `tablet`, `desktop`). Nothing else from the request is kept.
3. **Origin:** the `Origin` (or `Referer`) hostname must be one of `hosts`.
4. **Throttle:** 150 reports per 5 minutes per IPv4 address, or per /64 for
   IPv6. The count lives in memory only and the IP is never logged or stored.
   Expired windows are swept on a timer where the runtime allows one, and on
   each request otherwise. On Workers, an address can stay in the isolate's
   memory until a later request or until the isolate is recycled.
   - **Where the IP comes from** depends on what is in front of the server.
     Pass `clientIp: (request) => …`. The default (`defaultClientIp`) reads
     CF-Connecting-IP, else the *last* X-Forwarded-For entry (the one the
     nearest proxy added; the first is whatever the client sent). It never
     reads X-Real-IP, which many proxies pass through from the client; if
     yours sets it, pass `clientIp: (r) => r.headers.get('x-real-ip')`.
     CF-Connecting-IP is trustworthy only when every request comes through
     Cloudflare, and with no proxy in front the client writes the whole
     X-Forwarded-For header.
   - **The edge does better.** The real rate limit belongs there, e.g. a
     Cloudflare rule on the collector path. The per-day row cap protects
     storage either way.
5. **Size:** 4 KB at most. Real reports are under 600 bytes.
6. **Parse:** the path must be public (not in `skip`, no token-like
   segment), the event known, and every field in range. `skip` takes a
   RegExp, a string in the form k.js uses (`'^/account(/|$)'`, or
   `'/^\/account(\/|$)/i'` with flags), or an array of them; a rule that
   does not parse throws when the collector is created. Names from the page
   (`cta`, `ui` and `goal` kinds) that look personal drop the report. Any
   other failed check also drops the whole report, silently.
   - Dead and rage click labels that look personal are cut to their tag.
   - utm values that look personal are dropped.
   - A `utm_source` becomes the visit's source only if it is a known value
     (`linkedin`, `newsletter`, `qr`, `chatgpt.com`…). A link made for one
     recipient can carry a value that points at that person.
   - AI assistants are sources of their own (`chatgpt`, `perplexity`,
     `claude`, `gemini`, `copilot`, `deepseek`, `grok`, `meta-ai`,
     `mistral`, `you`), from their referrer hosts and `utm_source` values
     (`ai-visibility.md` has the table); `AI_SOURCES` lists them and
     `sourceClass()` maps any source to a coarse class.
   - A `utm_campaign` reaches the totals only if the owner listed it
     (`campaigns`); any other tag counts as `campaign.(other)`.
   - A `consent` report is dropped unless `consentCounts: true`.
   - An unknown referrer is reduced to its site
     (`jane-doe.github.io` → `github.io`).
7. **Store:**
   - the day's totals, always;
   - a row only when the report carries ids the mode allows:
     - `consent`: `vi` and `v`;
     - `always`: `v`, with the visitor hashed on the server.
   - never a row for an `err` or a `consent` report (ids are ignored on
     them, as is an entry), and never the `cv` vitals of a `time` report in
     its row: all three are totals only;
   - for an `err` report, one scrubbed sample per error and day (below).

## Modes

| `ids` | Rows | Visitor of a row |
|---|---|---|
| `never` | none | — |
| `consent` | for reports with `vi` + `v` (sent only after consent) | the browser's random visit id |
| `always` | for every report with `v` | `HMAC(secret, day ∣ IP/24 or /48 ∣ user agent)`, 16 hex. It changes every day; without the secret key it cannot be turned back into an address (with the key, a /24 and a user agent could be brute-forced, so guard the key). The view id is hashed with the day too, so an open tab cannot tie two days together. |

`always` needs a `secret` (32+ random bytes, in an environment variable).
Rotating the secret only breaks visits that span the rotation.

## The country header

The collector never looks up an IP itself. It reads the first of these
headers it finds:

| Host / CDN | Header |
|---|---|
| Cloudflare Workers / Pages Functions | `request.cf.country` (read first, no header needed) |
| Cloudflare (proxied DNS, any origin) | `CF-IPCountry`, added when "IP Geolocation" is on for the zone |
| Vercel | `x-vercel-ip-country` |
| CloudFront | `CloudFront-Viewer-Country` (add it to the origin request policy) |
| Others | `x-country-code` (set it at the proxy) or none: the country is `xx` |

Trust these only when the CDN sets them. A client can send them itself when
there is no CDN in front. That only skews the country counts.

## What is stored

### Totals: one document per day and page, and one per day for visits

`_id: "<day> <path>"`, with counters that only ever grow (`$inc`):

```text
views, entries, active, visible
sec.<section>.s          active seconds in that section
sec.<section>.r          reads of that section
depth.25|50|75|100       views that reached that depth
cta.<kind>, out.<site>, nav.<path>
ui.<name>, dead.<section>, rage.<section>, copy.email|text, print
err.<fp>                 JavaScript errors (k.js data-errors) by fingerprint; err.(other) past the cap
cwv.<device>.<metric>.<bucket>   Core Web Vitals (k.js data-vitals): views per bucket, per device class
cwvs.lcp|inp.<section>   of those, views whose LCP or INP was poor, by the section of its element
```

`_id: "<day> *"` (the day's visits):

```text
visits, hist.<bucket>    visit length: buckets start at 0,5,10,20,30,60,120,300,600 s
src.<source>, geo.<cc>, dev.<class>, lang.<code>
hour.<HH>                visits that started in that hour (owner's time zone; hourly: false turns it off)
goal.<name>
form.<name>              submits of a data-kform form (k.js), next to its goal
goalsrc.<name>.<class>   of those, by the class of the visit's entry: google, bing, search, ai,
                         social, newsletter, direct, other (never a referrer; see tracker.md)
campaign.<name>          visits from an allowlisted utm_campaign (option campaigns), campaign.(other) the rest
consent.shown|accept|decline|withdraw   the banner's events (options consentCounts + k.js data-consent-counts)
deploys                  [{ sha, at, note? }]: deploy markers (markDeploy, notifications.md), the newest 20
crawl.<bot>.<class>      AI crawler requests by status class, crawlp.<bot>.<path> by page (crawlers.mjs)
nf.<path>                views of the 404 page at that path (k.js data-k404)
nfin.<path>              of those, from a link on the site: a broken link on this site (see below)
```

`nfin` rests on k.js's word that the link was internal, so the collector
also requires the request's own `Referer` to be a page of the site (which
`sendBeacon` sends under the default referrer policy); without it the 404
counts in `nf` only. A crafted request can still send both, so treat a
`nfin` path as a strong hint, not proof.

`nf` and `nfin` keys are the path as k.js cleaned it, with `.` written
`%2E` so the key does not nest (`nf./docs/v1%2E2`). At most 100 distinct
404 paths a day per process; the rest count as `nf.(other)`. 404 paths are
whatever visitors and bots asked for, so the collector checks the whole
path with `looksPersonal` once more and drops the report when it looks
personal. Every store keeps these like any other counter (Mongo nests them
under `nf`, Analytics Engine has one data point per key).

### JavaScript errors (`err`)

An `err` report (k.js `data-errors="on"`, `tracker.md`) is checked again
here: the message goes through the same `scrubError` as in k.js (a client
can send anything) and is cut to 120 characters; the file must be a bare
file name (`app.js`, `page-*.js`, `(inline)`), and token-like parts of it
become `*`. Without a message or a file the report is dropped.

- **Fingerprint** `fp`: 8 hex characters, FNV-1a of (scrubbed message,
  file, line) (`errFingerprint`). The same error on any page and in any
  browser gets the same one; a new deploy that moves the line gets a new
  one (no source maps).
- **Totals:** `err.<fp>` per page and day. At most 50 distinct fingerprints
  a day **per process**; the rest count as `err.(other)` and keep no sample.
- **Samples:** the first `{ m, f, l, c, path }` of each fingerprint and day,
  where `path` is the page it was first seen on (cleaned like every path).
  No id, no section, no browser. `store.errSamples(day)` returns
  `{ <fp>: sample }`. Memory and files keep one document per day
  (`<dir>/errs/<day>.json`); Mongo one document per day and fingerprint in
  `web_errs` (`_id: "<day> <fp>"`, `$setOnInsert`, so the first one stays);
  SQL one row per day and fingerprint in `web_errs` (`on conflict do
  nothing`). **Analytics Engine keeps the counters but no samples.**
- **Retention:** samples are text, so they follow the **rows'** period
  (`rowsDays`, 180 days by default): Mongo's TTL on `web_errs`,
  `deleteBefore`'s `rowsBefore` for files and SQL (`enforceRetention`).
- **Read the samples** once after turning errors on: scrubbing cannot
  recognise a name written into a message without quotes.

### Core Web Vitals (`cv` on a `time` report)

Bucket indices are checked against `CWV_BUCKETS` (the same edges as k.js),
section keys like any other. The totals get `cwv.<device>.<metric>.<bucket>`
(`device` is `mobile`, `tablet` or `desktop`); for a **poor** LCP or INP
also `cwvs.<metric>.<section>` (`_` for none), so the documents stay small.
CLS and TTFB have no section. Every store keeps them as ordinary counters.

### How the totals stay safe

- **Keys from the browser are capped.** Distinct paths, sections, sources and
  so on are capped per day and **per process** (`path` 300, `section` 400…),
  and the rest are counted as `other`, so junk from a script cannot grow the
  documents. With several instances the caps multiply.
- **No free utm values in the totals.** Only a known `utm_source` becomes
  the visit's source, and only a campaign the owner listed in `campaigns`
  becomes a key (`campaign.<name>`; any other tag is `(other)`). Medium
  values never do: a tag can be made for one recipient. Rows keep the utm
  values that do not look personal. With `campaignTotals: false` neither a
  known `utm_source` nor a listed campaign reaches the totals: the source is
  the referrer's (see `decisions.md`, model A, for when the owner wants that).
- **The day is dated, not the moment.** A totals document's `at` is noon UTC
  of its day, never the moment of the first report: on a quiet day that
  moment would date one visitor.
- **Visits are counted without an id.** The visit-length histogram counts
  each new visit in bucket 0, and a `time` report moves it up (-1 from the
  old bucket, +1 to the new). The median comes from the bucket counts.

### Rows (model B with consent, model C)

```json
{ "at": "2026-10-05T08:12:03Z", "day": "2026-10-05", "visit": "…16 hex…", "view": "…16 hex…",
  "path": "/pricing", "e": "time", "d": { "sec": 42, "secs": [["plans", 30]], "dn": [25, 50] },
  "entry": { "source": "google", "utm": {}, "lang": "cs", "country": "cz", "device": "mobile" },
  "replay": "<PostHog recording id>" }
```

At most 5,000 rows a day **per process** by default (`rowsPerDay`). Past
that, reports still count in the totals.

### Retention

The defaults are 2 years for totals and 180 days for rows. A period in the
privacy text must be enforced, not just intended:

| Store | How |
|---|---|
| Mongo | TTL indexes on `at`, created by `init()` before the first write, so no row ever exists without its expiry |
| files | `purge()` at start and once a day, or `enforceRetention` |
| SQL (Postgres, SQLite, D1) | no TTL: `enforceRetention` once a day |
| memory | tests only |
| Analytics Engine | 3 months, fixed; it cannot delete sooner |

```js
import { enforceRetention, retentionStatus } from './retention.mjs';
await enforceRetention({ store, totalsDays: 730, rowsDays: 180 });          // daily
console.log(await retentionStatus(store, { totalsDays: 730, rowsDays: 180 }));
// { oldestTotalsDay: '2024-10-10', oldestRowDay: '2026-04-13', totalsOk: true, rowsOk: true }
```

`enforceRetention` deletes by day (totals before today minus `totalsDays`,
rows before today minus `rowsDays`, "today" in the collector's time zone:
pass it the same `timeZone`, and pass that to `fileStore` too) through
each store's `deleteBefore`; on Mongo it acts as a backup to the TTL index,
covering a shortened period or a missing index.
`retentionStatus` shows the oldest day each kind of data still has: show it
to the owner, so they can see the retention period is actually
enforced. Slack copies have their own
period: `deleteOldSlackLines` (`notifications.md`).

### Deletion (a visitor's own data)

A POST of exactly `{"del":"<visit id>"}` to the collector's endpoint deletes
the rows with that visit id and nothing else. consent.js's "Delete my visit
data" sends it through k.js (`consent.md`).

- **Checks:** POST and the `Origin` among `hosts`, like a report. It is
  handled **before** the reports' throttle and has its own limit
  (`deletionsPerAddress`, default 30 per 5 minutes per address), so a busy
  shared address (an office NAT) does not lose a visitor's deletion to other
  people's reports. A deletion dropped by that limit or by a store error is
  counted in the health record (`delDropped`), and `health.mjs` alerts on it.
  A request with any other field, or with an id that is not 16 hex
  characters, is ignored.
- **Always 204,** whether the id existed or not, so nobody learns whether a
  visit id is real.
- **Global Privacy Control does not block it:** deleting is not tracking.
- **Only rows.** Totals are counters with no id and stay as they are.
- **Model B:** the id is the browser's visit id. With the default in-memory
  id that is the current page load's visit; with
  `data-visit-store="session"`, the visit across page loads in that tab.
  Earlier visits used other random ids that nothing in the browser
  remembers, so they cannot be found; they expire with the rows' retention.
- **Model C:** the browser has no id. `{"del":"today"}` deletes the rows of
  **today's** visitor hash, computed again from the request's shortened IP
  and user agent. Yesterday's hash cannot be computed (the day is part of
  it), and a different network or browser gives a different hash. Someone
  on the same network /24 with the same browser version shares the hash, so
  their rows of today could go too (deletion only, never disclosure).
- **Stores:** memory, files (rewritten atomically), Mongo, SQL. Analytics
  Engine cannot delete: the request is a no-op there, and the privacy text
  must say so.
- **Late reports:** a report already on its way when the visitor clicks can
  arrive after the deletion; consent is withdrawn at the same moment, so no
  later report carries the id.
- `deletion: false` turns it off; then do not offer the button.

For a request that reaches the owner by e-mail, `assets/dsar.mjs` has
`exportVisit(store, id)` (the rows, and the PostHog recording ids they
name) and `deleteVisit(store, id)`. `deletePostHogRecordings` is optional:
it needs the owner's personal API key on the server and the exact URL of
their PostHog version's recording-delete endpoint (see the file).

## Mounting it

**Next.js** (`app/api/k/route.ts`):

```ts
import { createCollector, mongoStore } from '@/lib/analytics/collector.mjs';
import { db } from '@/lib/db';   // returns a promise of the driver's Db
export const runtime = 'nodejs';
// The store is made on the first report. If init() fails, that report is
// lost (the collector still answers 204 and logs it once a minute) and the
// next report tries again: a rejected promise is never cached.
let ready: Promise<ReturnType<typeof mongoStore>> | null = null;
const store = () => (ready ??= db().then(async (d) => { const s = mongoStore(d); await s.init(); return s; })
  .catch((e) => { ready = null; throw e; }));
const collect = createCollector({
  hosts: ['example.com', 'www.example.com'], ids: 'consent',
  skip: [/^\/account(\/|$)/], timeZone: 'Europe/Berlin',
  store: { write: async (x) => (await store()).write(x) },
});
export const POST = (req: Request) => collect(req);
```

**Cloudflare Pages Functions** (`functions/api/k.js`): build the collector
once per isolate, with `env` from the handler's context and
`analyticsEngineStore(env.EVENTS)` or a D1 adapter. See
`references/recipes.md`; with Astro's SSR adapter, use an API route instead.

**Express or Node http**: `app.post('/api/k', toNodeHandler(collect))`.
Mount it **before** any body parser: `express.json()` or `express.text()`
would consume the body. Options:
- `trustProxy: true` behind a proxy you run that sets X-Forwarded-For;
- `trustProxy: 'cloudflare'` only when the origin is reachable through
  Cloudflare alone;
- no option: the socket's address.

The adapter answers 204 even for an aborted upload or a malformed request,
and never throws.

**Hono, Bun, Deno**: pass the `Request` straight in.

## Stores

- `memoryStore()`: tests and local development.
- `fileStore(dir, { dailyDays, rowsDays })`: JSON files per day for a small
  site on **one** Node process with no database. Call `purge()` at start and
  every few hours. It also offers `daily(day)` and `rows(day)` for reports.
- `mongoStore(db, { daily, events, health, errs, gsc, dailyDays, rowsDays, gscDays })` (collections `web_daily`, `web_events`, `web_health`, `web_errs`, `web_gsc` by default): for a production MongoDB
  database. Call `init()` before the first write (the wrapper above). A TTL changed later
  needs `collMod`; `createIndex` fails with code 85.
- `analyticsEngineStore(env.EVENTS)`: Cloudflare, append-only, 3 months.
  It cannot delete (no retention shorter than 3 months, no visitor's own
  rows) and keeps no health record (`alerts.md`). Tested against a stand-in
  binding only.
- `sqlStore({ dialect, query })`: Postgres or SQLite (including D1) through one
  `query(sql, params) → rows` function you give it. `init()` creates the
  tables (`SQL_SCHEMA`); run `enforceRetention` daily, since SQL has no TTL.
  Tested against SQLite (node:sqlite) and a stand-in for the Postgres
  placeholders only.

```js
// node-postgres
const store = sqlStore({ dialect: 'postgres', query: async (sql, p) => (await pool.query(sql, p)).rows });
// Cloudflare D1
const store = sqlStore({ dialect: 'sqlite', query: async (sql, p) => (await env.DB.prepare(sql).bind(...p).all()).results });
await store.init();
```

The tables: `web_daily (day, path, key, n)` with one row per counter,
`web_events` for rows, `web_health` for the health record, `web_errs` for
error samples, `web_deploys` for deploy markers and `web_gsc` for Search
Console documents. An existing install gets the new tables from running
`init()` again (`create table if not exists`).

Every store also offers what the helpers use: `totals(day)`,
`errSamples(day)`, `health()`/`saveHealth()`, `deleteBefore()`, `oldest()`,
`visitRows()`, `deleteVisit()`, `markDeploy(day, entry)` and
`saveGsc(day, doc)`/`gsc(day)` (Analytics Engine offers only `write`). Search
Console documents (`gsc.mjs`) are kept 16 months (`gscDays`, 490; Mongo's
TTL on `web_gsc`, `enforceRetention` for files and SQL).

- **Umami**: `forward: umamiForwarder({ websiteId, hostname, events: [] })`
  sends page views (and any listed events) to Umami for its dashboard. It
  sends the full user agent and the visitor's IP shortened to its /24
  (IPv6 /48), from which Umami builds a monthly visitor id (see
  `decisions.md`). Pass the collector's `clientIp` to it too
  (`umamiForwarder({ …, clientIp })`); by default it reads the last
  X-Forwarded-For entry. The website id stays in the server environment.

## Options

`createCollector` takes `hosts` and `store` (required), `ids`, `secret`,
`skip`, `campaignTotals`, `campaigns` (the utm_campaign allowlist),
`consentCounts`, `timeZone`, `hourly`, `rowsPerDay`, `deletion`,
`deletionsPerAddress`, `healthEveryMs`, `forward`, `clientIp` and `onError`;
the comment above `createCollector` in `collector.mjs` explains each.

## Health

The collector keeps a health record (last write, failed writes by error
class, last report), off the hot path, in the store and in memory
(`collect.health()`). `assets/health.mjs` turns it and the totals into
alerts for an ops channel: `alerts.md`.

## Reading the totals

`assets/digest.mjs` turns them into the weekly digest
(`references/notifications.md`). By hand:

- **Visits, sources, countries, devices**: the `"<day> *"` documents.
- **Median visit length**: walk `hist.*` until half the visits are covered.
  A negative bucket (a visit that crossed midnight) counts as 0.
- **Most-read sections**: `sec.<s>.r ÷ views` per page. Time per section
  is `sec.<s>.s`. A section many scroll past but few read is a candidate
  to cut.
- **Depth**: `depth.75 ÷ views`.
- **Conversion**: `goal.<name> ÷ visits`; by source class,
  `goalsrc.<name>.<class>` against the visits of that class.
- **AI assistants**: the `src.*` keys in `AI_SOURCES`; AI crawlers in
  `crawl.*` (`ai-visibility.md`).
- **Friction**: `dead.*` and `rage.*` per section.
- **JavaScript errors**: `err.*` per page, with `store.errSamples(day)`
  for what each fingerprint is; `health.mjs` alerts on new ones and spikes
  (`alerts.md`, rule f).
- **Core Web Vitals, p75 per page and device**:
  `p75FromBuckets(doc.cwv.mobile.lcp, 'lcp')` gives the bucket the 75th
  percentile falls in, `{ bucket, from, to, rating }` (`from`–`to` in ms,
  or unitless for CLS; `rating` good, needs-improvement or poor). Add the
  days of a week together first (bucket by bucket) for a steadier number;
  a day with a few views says little.
- **Which section is slow**: `cwvs.lcp.<section>` and `cwvs.inp.<section>`
  count the views whose LCP or INP was poor, by the section the element or
  the interaction was in. Divide by the page's views with that metric
  (the sum of `cwv.*.<metric>.*`). A poor LCP in `hero` is the hero image or
  heading; a poor INP in `signup-form` is that form's handlers. `_` means
  outside every section (a banner, the site header).

```js
import { p75FromBuckets } from './collector.mjs';
const doc = (await store.totals('2026-10-09'))['2026-10-09 /pricing'];
p75FromBuckets(doc?.cwv?.mobile?.inp, 'inp'); // { bucket: 2, from: 200, to: 350, rating: 'needs-improvement', n: 41 }
```

- **Broken links**: `nfin.*` on the `"<day> *"` document: 404s reached
  from the site's own pages. Fix the link, or redirect the old path. A
  large `nf.*` without `nfin` is usually old external links or bots
  probing (`/wp-login.php`); redirect the external ones that matter.

## Testing it by hand

```bash
curl -i -X POST http://localhost:3000/api/k -H 'Origin: http://localhost:3000' \
  -H 'User-Agent: Mozilla/5.0 (Macintosh) Chrome/140 Safari/537.36' \
  --data '{"p":"/","en":1,"r":"","u":{},"l":"en"}'
# 204, and the day's "<day> /" document has views: 1
```

`localhost` must be in the collector's `hosts` for this to be stored, and so
must any host the site is tested under. A 204 proves nothing by itself: the
collector answers 204 to everything, so look at the store.
