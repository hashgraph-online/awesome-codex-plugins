# Decisions to make with the owner

Ask these before building. Each question has options, trade-offs and a
recommended default. Write the answers down: they become the configuration
and the privacy text.

## 1. The consent model (ask, always)

| | A. Totals only | B. Consent-tiered | C. Visits without a banner |
|---|---|---|---|
| k.js `ids` / collector `ids` | `never` | `consent` | `always` (+ secret) |
| Banner | the owner decides (see "About model A") | yes | no |
| Without consent the site gets | daily totals | daily totals | per-visit stories |
| With consent | the same | + per-visit rows, PostHog replay and heatmaps | not applicable |
| Stored in the browser | nothing | before consent: only the answer; after Accept: PostHog's storage (and the visit id, if `data-visit-store="session"`) | nothing |
| Server-side identity | none | a random visit id from the browser | a daily HMAC of the date, a shortened IP and the user agent |
| Relative legal risk (not legal advice) | lowest | low; the banner must be right | higher; see below |

**What the totals give** (all models): visits, sources (a known
`utm_source` such as `newsletter` counts as the source unless
`campaignTotals: false`), countries, device classes and languages. Campaign
and medium values never enter the totals. Per page: views, active and visible
seconds, seconds and reads per section, scroll depth (25/50/75/100%), link
clicks by kind, goals, dead and rage clicks, copies and prints. A histogram
of visit length gives the median and "stayed over a minute". Nothing in
them describes one visit. On a small site, though, a count of 1 on a quiet
day can still point at someone. Keep the totals for the owner's eyes.

**What only rows give** (B with consent, C): the path of one visit through the
site, time per page and per section in that visit, its clicks in order, the
link to its recording (B), and the Slack or e-mail line per visit.

**About model A, and the totals in model B.** No consent is asked for the
daily totals. That rests on the audience-measurement exemptions some
regulators publish. CNIL's is the best known, and it has three layers that
should not be mixed up:

- **Binding conditions** (CNIL Guidelines 2020-091, paras 50–51): the
  measurement serves the site's own audience measurement only; it does not
  follow people across sites; it produces anonymous statistics only; the
  data is not combined with other data; and it is not passed to third
  parties.
- **Recommendations** (CNIL Recommendation 2020-092, consolidated
  16 January 2026): trackers live at most 13 months, the data is kept at
  most 25 months, and users are informed.
- **The self-assessment tool** (July 2025): IP addresses used at most for a
  city-level location and then truncated (at least the last octet); an
  objection link; cookieless or fingerprint-style identifiers only if salted
  per site and limited in time; small counts rounded to tens. It
  **excludes** session replay and UTM or other campaign identifiers.

What this means here:

- k.js and the collector are designed with these conditions in mind:
  same-origin only, no identifiers in the totals, no IP stored, nothing
  shared, totals kept 2 years by default (under 25 months), nothing stored
  in the browser for the totals. Whether a given setup meets them is for
  the owner and their counsel. One default does not follow CNIL's
  self-assessment profile: a known `utm_source` goes into the totals as
  the source.
- **Campaigns in the totals are the owner's decision.** By default a known
  `utm_source` becomes the visit's source in the totals. Under CNIL's
  self-assessment profile it should not: set `campaignTotals: false` in the
  collector, so the totals use only the referrer and campaign tags reach
  rows alone (which need consent in model B). `utm_campaign` values stay
  out of the totals unless the owner lists the campaigns to count
  (`campaigns: ['spring-sale']`; any other tag counts as `(other)`, so a
  tag made for one recipient never becomes a key). `campaignTotals: false`
  turns that off too.
- **Small counts.** The totals are stored exact. The weekly digest
  (`notifications.md`) rounds by default: a count under 10 shows as `<10`,
  larger ones are rounded to tens, and percentages come from the rounded
  counts. Ask the owner whether to keep that (recommended for anything that
  leaves the owner's hands) or show exact counts (`rounding: 'none'`). Round
  the same way in any other report written for the project.
- CNIL's tool expects an objection link. Model A has no banner, so add one
  to the privacy page: a link to `?k=off` (for example `/privacy?k=off`)
  switches k.js off in that browser, the same switch the owner uses. It
  stores only that flag.

Sources (checked 2026-10-08):
[Guidelines 2020-091](https://www.cnil.fr/sites/cnil/files/atoms/files/lignes_directrices_de_la_cnil_sur_les_cookies_et_autres_traceurs.pdf),
[Recommendation 2020-092, consolidated](https://www.cnil.fr/sites/default/files/2026-01/recommandation_cookies_consolidee.pdf),
[self-assessment tool](https://www.cnil.fr/sites/default/files/2025-07/outil_d_auto-evaluation_mesure_d_audience.pdf).

Beyond France, the EDPB's Guidelines 2/2023 on the technical scope of
Art. 5(3) ePrivacy (final version 2.0, adopted 7 October 2024) put a
cookieless beacon within Art. 5(3) (para 33): a script that makes the
browser send data is covered even when nothing is stored. Some national
regulators are stricter than CNIL and grant no analytics exemption at all.
One example: the Czech data protection authority (ÚOOÚ) treats analytics
cookies as non-technical, so they need consent (§89(3) of Act No. 127/2005
Coll.). Running the totals without consent is therefore a risk the owner accepts,
not a settled exemption. Say so to the owner.

**A proposal to watch (dated 2026-10-08).** The European Commission's
Digital Omnibus proposal, COM(2025) 837 of 19 November 2025, would add a
GDPR Art. 88a(3)(c) exempting first-party aggregated audience measurement
(roughly model A) and an Art. 88b on machine-readable consent signals. It
is **not law** (as of October 2026): the Council's June 2026 text deleted
Art. 88a, and its position was still open in October 2026. Until something is adopted, the
current ePrivacy rules and national laws apply. Re-check this before
publishing anything that relies on it.

**About model C.** It rests on the controller's legitimate interest and on
storing nothing on the device. EU regulators read the ePrivacy rule on
terminal equipment broadly: EDPB Guidelines 2/2023 cover information a
script obtains from the device, not only cookies. Several national
regulators exempt audience measurement from consent, but only under
conditions, usually aggregate statistics with limited retention. A per-visit
timeline goes beyond what most of those exemptions describe. Present this
neutrally and let the owner decide, ideally with counsel.

**Default recommendation:** B when the owner wants replay or per-visit
detail, A when they want no banner at all, C only as their explicit decision.

**Multi-page sites in model B.** By default the visit id lives in memory for
one page load: an id kept in the browser becomes a link between separate
visits. Each full page load then starts a new visit in the rows.
`data-visit-store="session"` keeps the id in sessionStorage, only after
consent and only until 30 idle minutes, so a visit spans page loads. List it in the privacy text if chosen. On client-side-routed sites
the default is enough.

## 2. Where the data lives (ask)

- **The project's own database or files.** `fileStore` for a small site on
  one Node process, `mongoStore`, or Postgres/SQLite with the schema in
  `collector.md`. Totals are kept 2 years and rows 180 days by default. This
  is the most private option, and the owner holds everything.
- **Umami** (Cloud or self-hosted) through `umamiForwarder`, for a ready-made
  dashboard. Umami gets the path, the referrer site, the language, a
  shortened IP and the **full user agent**. It never gets ids, sections or
  timing. Umami builds its own visitor id from the IP and the user agent
  with a monthly salt, so its data is pseudonymous, not aggregate. That does
  not fit model A's "nothing describes one visit". Ask the owner explicitly,
  name Umami as a processor (DPA, privacy text), and describe its id there.
- **Cloudflare Workers Analytics Engine** (`analyticsEngineStore`). It is read over the SQL API, keeps data **3 months**
  and **samples** at volume. Cheap, and no database.
- A combination: own store for sections and rows, Umami for the dashboard.

Ask how long to keep totals and rows; the defaults are 2 years and 180 days.
SQL and file stores have no TTL: enforcing the period means running
`retention.mjs` once a day (`collector.md`, "Retention").

## 3. PostHog session replay and heatmaps (ask; model B only)

Replay shows where people get stuck, at a cost: a recording of the screen
(inputs masked), a processor (PostHog, choose the EU region), a DPA, and
more text in the banner and policy. Without it, k.js's sections and dead and
rage clicks already show most friction. Default: off unless the owner wants it.

## 4. Notifications (ask)

- **Slack**, one line per notable visit, posted 30 minutes after the visit
  goes quiet. Use a bot token with `chat:write` (it can thread a day's
  visits under one parent message) or an incoming webhook (flat).
- **The weekly digest** (`assets/digest.mjs`): what changed this week, from
  the totals only, so it works in every model. Ask where it goes, on which
  day, and whether counts are rounded (above). A daily digest is a recipe
  in `notifications.md`, not shipped code.
- **E-mail**: one short e-mail per notable visit, plus a daily digest if
  wanted. Cloudflare Email Routing or any SMTP service.
- **None:** the totals in a dashboard or a weekly query are enough.

**Slack retention (ask, with Slack):** how many days the visit lines stay.
`deleteOldSlackLines` (`retention.mjs`) deletes the bot's own lines after
that, from the `ts` values the runner keeps. Recommend 30 days (the lines
are for noticing visits, not for archives), or 90 at most. Also set a
channel retention in Slack as a backstop if the plan allows.

Ask what "notable" means for them. The default is 10 s active, two pages,
any non-internal click, a goal, a copy or a print. Also ask for the daily
cap (default 25 lines; goal visits always get one, up to 100).

## 4b. "Delete my visit data" (ask; model B)

Offer the button in the reopened banner (`consent.md`), or not.

- **Yes** (recommended when the store can delete): a visitor can delete the
  rows of their current visit in one click, and withdraw. It cannot reach
  earlier visits (no id is kept between them) or PostHog recordings.
- **No** (`deleteButton: false`): deletion is "write to us", and only works
  when the visitor can give a visit id. Required with Analytics Engine,
  which cannot delete.
- Model C: a button on the privacy page (`window.__k.deleteMyData()`) deletes
  only today's records from that network and browser. Offer it only if the
  owner accepts that limit, and say it in the policy.

## 4c. Health alerts (ask)

Whether to run `assets/health.mjs` (`alerts.md`), and:

- **where alerts go:** an ops channel or webhook, or e-mail; never the
  visits channel;
- **thresholds:** the defaults (silence 3 h, visits under 40% of usual,
  a goal at 0 for 3 days, 404 spikes at 3×), or the owner's;
- **quiet hours**, in their time zone;
- keeping the hourly visit counts (`hour.<HH>`) that three rules need;
- **forms that matter** (contact, booking, sign-up): mark them with
  `data-kform` and send the goal of the same name on the server's
  confirmation, so a broken backend alerts within a day.

**Outside the site (ask, then suggest; build nothing):** analytics only
sees visits that reach the site. Whether the site is down, or its TLS
certificate or domain is about to expire, needs a check from outside:
suggest [Uptime Kuma](https://github.com/louislam/uptime-kuma) (self-hosted,
checks certificate expiry), UptimeRobot or Better Stack (hosted, with
certificate and domain expiry on their plans), and put it on the owner's
to-do list in step 5's report. Upptime checks status only.

## 4d. JavaScript errors and page speed (ask; both off by default)

- **Errors** (`data-errors="on"`): counts of the site's own JavaScript
  errors per page and day, with one scrubbed example per error
  (`tracker.md`, "JavaScript errors"). Totals only in every model, never a
  row, so model A and B before consent can have them too. Worth it on a site
  with forms or client-side code; the owner then reads the examples once
  (scrubbing cannot see an unquoted name: `Payment failed for Jane Doe`
  is stored as written) and decides on alert thresholds (`alerts.md`, rule
  f). Alerts and the weekly digest name an error by fingerprint, file and
  line; ask whether they may also quote its scrubbed message
  (`showErrorText: true`; default no). **Forwarding to an error tracker** (GlitchTip,
  Bugsink, Sentry) is a further, separate decision: only after consent, a
  new processor in the privacy text (`tracker.md` has the recipe).
- **Core Web Vitals** (`data-vitals="on"`): LCP, CLS, INP and TTFB as
  buckets per page and device class, and the section of a poor LCP or INP.
  Totals only. Useful when the owner wants to know which page and which
  part of it is slow; with Umami's own script loaded, use one source.
- Default: both off; recommend errors on for sites with forms or an app-like
  front end, vitals on when someone will look at them.
- Either adds a line to the privacy text (`privacy-policy.md`).

## 4e. Counting consent answers (ask; off by default)

Whether to count how often the banner is shown and answered:
`consent.shown|accept|decline|withdraw` per day (consent.js events, k.js
`data-consent-counts="on"`, the collector's `consentCounts: true`). The
reports are totals only: no id, also after Accept, and nothing at all under
Global Privacy Control or Do Not Track (k.js does not run).

- **For:** the digest can say how far the per-visit rows can be trusted.
  Rows and visit lines only describe people who accepted; with a 30% accept
  rate they are a small, self-selected sample.
- **Against:** counting the answer is itself measuring a reaction to the
  banner. Some owners and counsel prefer not to measure anything about the
  consent decision. It is the owner's call; the privacy text then lists it.
- Default: off. Recommend it only when the owner reads the visit lines and
  needs to know what share of visitors they cover.

## 4f. AI visibility (ask which pieces; each is optional)

`references/ai-visibility.md`:

- **Visits from AI assistants:** nothing to decide; the sources exist in
  every setup and the digest groups them.
- **AI crawlers** (`assets/crawlers.mjs`): counting requests by AI
  crawlers' user agents on the server, with the pages they read. Needs a
  server, middleware or Worker in front of the pages. On Cloudflare, its
  AI Crawl Control already shows this; recommend it there.
- **Search Console** (`assets/gsc.mjs`): needs a Google Cloud service
  account added to the property, and a daily job. Skip it if the owner uses
  a hosted analytics tool with its own Search Console integration (e.g.
  Plausible).

## 5. Private paths (ask, then confirm against the routes)

Every route that has a token or a person's id in the URL, or shows a
person's data: `/reset/<token>`, `/invite/<token>`, `/pay/<id>`,
`/account`, `/app`, `/admin`, `/dashboard`… These go into `skip` (k.js,
collector, consent.js) and `private` (posthog-guard). Links to them are
reported as `/[private]`.

This list is the real protection. The tracker replaces token-like path
segments (ids, e-mails, JWTs, random codes) with `[id]`, but a slug that
names a person (`/u/jane-doe`) reads like any other slug and cannot be
detected. Every route whose path can name a person goes into `skip`.

Paths are case-sensitive. If the server also answers `/Account`, write the
rule with the `i` flag as `/^\/(account|reset)(\/|$)/i` (k.js, consent.js
and the collector accept that string form; posthog-guard takes the RegExp),
or redirect other spellings to the lowercase path.

## 6. Smaller choices (defaults are fine; mention them)

- **Time zone of "a day"**: the owner's. A day boundary in UTC splits
  evenings in Europe.
- **Owner opt-out**: `?k=off` on any page stores a flag in that browser
  (`?k=on` removes it). Tell the owner to do it once in each of their browsers.
- **Hosts**: the production hostnames. k.js stays off on other hosts when
  `data-hosts` is set, so staging and localhost never mix into the numbers.
- **Languages**: the banner and the policy in every language the site has.
- **Goals**: which actions count as conversions (`data-kgoal` or the
  `k:goal` event after a successful submit, never on the click alone).
  Goals are also counted by the coarse source class of the visit's entry
  (`goalsrc`: google, bing, search, ai, social, newsletter, direct, other).
- **Campaign tags in the address bar**: `data-strip-utm="on"` removes
  `utm_*` from the URL once k.js has read them, so a shared or bookmarked
  link does not carry them on. Off by default; check client-routed sites
  (`tracker.md`).
- **Deploy markers**: whether CI marks production deploys
  (`assets/ci/deploy-marker.yml`), so the digest and alerts can say "after
  deploy abc1234".
