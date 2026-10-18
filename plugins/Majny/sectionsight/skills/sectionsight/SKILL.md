---
name: sectionsight
description: Sets up privacy-first website analytics that show what visitors actually read (active seconds per page section and whether it was read; scroll depth, CTA and goal clicks, dead and rage clicks, copies, prints, video plays) with no cookies. Adds a consent banner designed around the EDPB Cookie Banner Taskforce report and CNIL guidance, optional PostHog session replay only after consent, a Slack or e-mail line per notable visit, a weekly digest, AI referral and crawler counts, health alerts, enforced retention, and self-service deletion of a visitor's data. Then proves it in a real browser (nothing stored and no ids before consent, no e-mail or token in any request, withdrawal works across tabs). Use when adding, replacing or auditing web analytics, cookieless tracking, a GDPR/ePrivacy consent banner, PostHog privacy settings, or visit notifications, on any stack (plain HTML, Astro, Next.js, React SPAs, Cloudflare, Node).
license: MIT
compatibility: The reference code needs a server or function that can take a same-origin POST (Node 18+, Workers, Deno, Bun). verify.mjs needs Node 20+, Playwright and Chromium (network access to install them).
metadata:
  author: Jakub Dvořák (kubadvorak.com)
  version: "1.0.1"
---

# Privacy-first analytics

This skill wires up website analytics that respect visitors and still tell the
owner what people read. It bundles the decisions to make, the reference
code, and the checks that prove it works, for static sites, server-rendered
sites and SPAs alike.

The reference code in `assets/` is tested in a real browser (`scripts/verify.mjs`).
Copy what you need into the project, adapt the wiring to its stack, and keep the
code's behaviour. Do not rewrite it from memory. Paths below are relative to
the directory that contains this SKILL.md.

## Rules that do not bend

1. **Nothing personal leaves the page.** No query string except `utm_*` values
   that do not look personal, no typed text, no copied text. Path segments
   that look like an e-mail, phone number, token or id become `[id]`. That
   rule cannot recognise a name in a slug (`/u/jane-doe`), so rule 2 is
   the real protection for such pages. Every report, event and Slack line
   follows this.
2. **Private pages are never measured.** These are URLs that carry a credential
   or name a person (password reset, invite, payment, `/account`, a profile
   page, the signed-in app). No tracker and no PostHog run there, and no
   banner shows.
3. **Nothing is stored in the browser before consent.** The exception is the
   consent answer itself. Global Privacy Control and Do Not Track mean no.
4. **The collector never stores an IP address or a full user agent.** Use
   the CDN's country header and a device class. The collector uses an IP
   only in memory, for throttling and for a daily hash in model C. If you use
   the PostHog proxy or `umamiForwarder`: the proxy forwards the full IP to
   PostHog (turn on "Discard client IP data" in the project), and the
   forwarder sends Umami the IP shortened to its /24 with the full user agent; say so in the
   privacy text.
5. **Nothing in Slack or e-mail that identifies a visitor.** A line says
   where a visit came from and what it did, never who it was.
6. **Legal choices belong to the owner.** Ask about the consent model, retention
   and anything else marked *ask*. Never write "GDPR compliant" anywhere. Say what
   was built, and that a lawyer should review the policy text. If nobody can
   answer (an unattended run), stop after Discover and write the questions
   into your report. If the owner answered the consent model, storage,
   retention and private paths up front, build with the recommended
   defaults for the rest and list each one as unconfirmed.
7. **Secrets stay secret.** Slack tokens, webhook URLs, PostHog personal API
   keys and hashing secrets go in environment variables. Never commit them,
   never print them, never put them in client code. The PostHog *project* token
   is public by design.

## Workflow

### 1. Discover (read the project, change nothing)

- Stack, rendering (static, server, client-side routing), hosting and CDN.
  The CDN determines the country header; see `references/collector.md`.
- Where a same-origin POST endpoint can live (route handler, function, server).
  If the site has none, stop and ask the owner before building anything
  (`references/recipes.md`, "When something does not fit").
- What runs today: grep for `gtag`, `googletagmanager`, `posthog`, `plausible`,
  `umami`, `hotjar`, `clarity`, `fbq`, `_ga`, `document.cookie`, `localStorage`.
  List what each one sets or sends.
- Private paths: routes with tokens or ids in the URL, routes whose path
  names a person (profile or invite slugs), auth and account pages,
  checkout, admin, the app behind a login.
- The page structure: `<main>`, its `<section>`s and headings. Note the
  languages and whether a privacy page exists.

### 2. Decide with the owner

Ask the questions in `references/decisions.md`, with its recommended
defaults. At minimum:

- **The consent model:**
  - **A** totals only, usually without a banner (the owner accepts the residual risk);
  - **B** totals for everyone, per-visit rows (each report stored with a random visit id) and replay only after Accept (needs a banner);
  - **C** per-visit rows without a banner (more legal exposure; the owner decides).
- Where the data lives.
- PostHog replay: yes or no (only with B).
- Notifications: Slack, e-mail or none.
- Retention: totals, rows, and how many days Slack visit lines stay
  (recommend 30, at most 90).
- Model B: offer "Delete my visit data" in the reopened banner, or not.
- Health alerts: where they go (an ops channel or webhook, never the visits
  channel), thresholds, quiet hours (`references/alerts.md`).
- JavaScript errors (`data-errors`) and Core Web Vitals (`data-vitals`):
  on or off (both off by default; totals only, never ids). Forwarding
  errors to GlitchTip, Bugsink or Sentry only after consent, if at all
  (`references/decisions.md`, 4d).
- Whether a known `utm_source` may count as a source in the totals
  (`campaignTotals`; CNIL's self-assessment profile excludes campaign data),
  and which `utm_campaign` names, if any, may be counted (`campaigns`).
  Whether k.js removes `utm_*` from the address bar after reading them
  (`data-strip-utm`; off by default).
- The weekly digest (`assets/digest.mjs`): yes or no, where it goes, and
  whether its counts are rounded (default: under 10 shows `<10`, others to
  tens) or exact (`references/decisions.md`, "Small counts").
- Counting the consent banner's answers (`data-consent-counts`, the
  collector's `consentCounts`): **the owner's decision, off by default**
  (`references/decisions.md`, 4e). It lets the digest say what share of
  visitors the per-visit rows cover; it is totals only, never ids.
- AI visibility, each optional (`references/ai-visibility.md`): AI
  crawler counts on the server (`assets/crawlers.mjs`; on Cloudflare its
  AI Crawl Control is the better source), and Search Console's daily top
  queries and pages (`assets/gsc.mjs`; needs a service account added to the
  property, or Plausible's own integration instead), and whether the
  digest may list search queries (`gscQueries`; a person's name that is
  searched often enough can pass Google's anonymisation threshold). Deploy markers from CI
  (`assets/ci/deploy-marker.yml`): yes or no.
- With `data-errors`: whether alerts and the digest may quote an error's
  scrubbed message (`showErrorText`, off by default: a name written into a
  message without quotes is stored and would be posted as written).
- The time zone the days are counted in.
- The private paths.
- **What must never break** (for verify's broken-things checks): the CTA
  links and where each must point (a sign-up path, a booking or WhatsApp
  link with the right number), which pages must be indexable by search
  engines, and which must not be (thank-you pages, internal search). If
  the owner has no answer, propose the main CTAs found in Discover and
  the pages in the sitemap. For "must not be", name only pages that already
  carry `noindex` and that robots.txt does not block: a blocked page's
  `noindex` is never seen (verify fails it), and pages robots.txt already
  disallows belong in neither list.

Write the answers into the project (e.g. `ANALYTICS_DECISIONS.md`); they go
into the configuration and the privacy text.

### 3. Build

Copy the assets you need from `assets/` into the project, and follow the
recipe for the stack in `references/recipes.md`. Write the private paths as
**one regex** and use it in all four places: k.js `data-skip`, the
collector's `skip`, consent.js `skip`, and posthog-guard's `private`. Paths
are case-sensitive, so prefer the string form with the `i` flag,
`/^\/(account|reset)(\/|$)/i`, which all four read. Never a comma list:
`^/account, ^/reset` is rejected; join paths with `|`. A rule that does not
parse fails closed, differently in each file:

- **k.js** measures nothing and logs a console warning.
- **consent.js** treats every page as private: the banner shows only when
  "Privacy settings" opens it, so nobody is asked. That is silent in
  production; on localhost, `127.0.0.1`, `*.localhost` or with `?k-debug`
  it shows the error at the top of the page.
- **The collector** throws when it is created. An Express server then fails
  at boot; a Next.js route that creates it at the top level fails every
  POST with a 500 (and `next build` may fail); the lazy Cloudflare recipe
  answers 500 to every report, silently.
- **posthog-guard** treats every page as private, and `startPostHog` logs an
  error and never starts PostHog.

So a broken rule never measures a private page, but it can go unnoticed:
run `scripts/verify.mjs` (step 4) after every change to the rule: "the
collector receives reports" fails when the collector answers an error, and
"the banner is shown" when the banner never asks.
Then, in order:

1. **Collector.** Mount `assets/collector.mjs` at a same-origin POST path
   (default `/api/k`). Give it a store, the site's hosts, `skip` (the private
   paths), `ids` (A `never`, B `consent`, C `always` with a secret) and the
   time zone. See `references/collector.md`.
2. **Tracker.** Serve `assets/k.js` from the site, or bundle it, and configure
   it with the same `ids` and `skip`. Mark the sections with `data-k`, the
   important links with `data-kcta`, goals with `data-kgoal`, forms with
   `data-kform`, and accordions, tabs and toggles with `data-kui`. For client-side routing it
   follows `history` on its own. Add `data-errors="on"` and
   `data-vitals="on"` only if the owner said yes. See `references/tracker.md`.
3. **The 404 page:** put `data-k404` on the `<html>` or `<body>` of the 404
   template (`references/tracker.md`), so broken links show up as
   `nfin.<path>` in the totals. A missing path must answer HTTP 404, not
   200 with the home page or an app shell: static hosts (Cloudflare Pages,
   Netlify, Vercel, GitHub Pages) do this when a top-level `404.html`
   exists and no SPA fallback is configured; Node servers set the status
   themselves; Next.js does it with `not-found`. An SPA served by its own
   server answers 404 for paths outside its route list. verify fails a
   missing path that answers 200.
4. **Consent (B):** `assets/consent.js`, or a port that keeps its behaviour.
   Add a "Privacy settings" control (`data-consent-open`) in the footer of
   every page, including the 404 page. The banner text must name what Accept
   turns on and how long data is kept. See `references/consent.md`.
5. **PostHog (B, optional):** `assets/posthog-guard.mjs`,
   `assets/posthog-proxy.mjs` and the project settings in `references/posthog.md`.
   It loads only after Accept and stops in the right order on withdrawal.
6. **Notifications (optional):** `assets/visits.mjs` on a schedule. See
   `references/notifications.md`.
7. **Retention:** `assets/retention.mjs` once a day for every store without
   a TTL (files, SQL), and `deleteOldSlackLines` for the Slack lines. Show
   the owner `retentionStatus`. See `references/collector.md`, "Retention".
8. **Health alerts (if wanted):** `assets/health.mjs` every 15–30 minutes,
   posting to the ops channel. See `references/alerts.md`.
   **Weekly digest (if wanted):** `assets/digest.mjs` once a week, with
   the owner's rounding choice (`references/notifications.md`). **Deploy
   markers (if wanted):** `assets/ci/deploy-marker.yml` and a small
   `mark-deploy` script that calls `markDeploy`.
   **AI visibility (the pieces the owner chose):** `countCrawler` from
   `assets/crawlers.mjs` after each response (`waitUntil`, `after()` or a
   `finish` listener, never awaited before the answer), and `gscDaily` from
   `assets/gsc.mjs` once a day. See `references/ai-visibility.md`.
9. **Deletion:** the collector takes `{ del }` requests; consent.js offers
   "Delete my visit data" unless the owner said no, or the store cannot
   delete (Analytics Engine): then `deleteButton: false` and k.js
   `data-delete="off"`.
   `assets/dsar.mjs` for requests by e-mail.
10. **Privacy page:** the checklist in `references/privacy-policy.md`, in the
   site's languages. List only what was actually built, the periods that
   are actually enforced, and how deletion really works.
11. **Headers:** `connect-src 'self'` and `script-src 'self'` are enough for
   k.js. Inline config scripts need a nonce or hash in `script-src`, or an
   external config file. consent.js's look: on a static host (no
   per-request nonce), serve `assets/consent.css` and set `stylesheet:
   '/consent.css'`, or put its rules in the site's own CSS with `styles:
   false`; with a per-request nonce, give consent.js's tag the nonce (its
   `<style>` inherits it). verify fails a CSP violation from these scripts
   (`references/consent.md`). With
   PostHog heatmaps, allow framing by the PostHog app on public pages only
   (`references/posthog.md`).

### 4. Verify (required)

Run `scripts/verify.mjs` against the running site and fix the code until
every check passes. A check never passes because it was weakened. Then do
the manual checks in `references/verify.md` and run the project's own tests.

Install Playwright in a scratch directory, not in the project: it would
change the project's lockfile, and the report lands in the current directory.
`--resolve example.com` checks the local server under its production name.

```bash
mkdir -p /tmp/sectionsight-verify && cd /tmp/sectionsight-verify && npm i playwright && npx playwright install chromium
node <this skill's directory>/scripts/verify.mjs --url http://example.com:3000 --resolve example.com \
  --pages /,/pricing --private /account/x --mode consent --posthog /ingest
```

If verify cannot run (no network, no browser), say so in the report. Never
report a check as passed that did not run.

With `data-consent-counts="on"`, add `--consent-counts`: the banner's
reports must carry no ids, including the Accept and the withdrawal.

With `data-errors="on"`, add `--errors`: verify throws an error carrying the
probe e-mail and token from an inline script on the first page and checks
that the `err` report arrives scrubbed and without ids, before and after
consent.

Add the owner's answers about what must never break: `--expect` for each
CTA (`'a[data-kcta=signup]@href=^/signup$'`), `--indexable` and
`--noindex` for the pages, `--sitemap`, and `--privacy-page` with
`--processors` for every recipient the browser does not see (a server that
forwards to Umami). These checks are read-only. A
command-line `--expect` is checked on every `--pages` page; for a CTA that
lives on some pages only, use the config file's `expect` entries with their
own `pages` (`references/verify.md`).

**Keep it checked (CI).** Write the settings you just used into
`privacy-check.config.json` (`assets/ci/privacy-check.config.example.json`;
the URL and `--resolve` stay on the command line), so CI and local runs
share them. Then **ask the owner**:

- **On a failed check in a pull request: block the merge, or warn only?**
  Blocking makes the job a required status check; warning keeps it green
  and shows the table in the job summary.
- **Run the check every night against production?** It runs with
  `--no-write`, so it stores nothing. If yes, **who hears about a failure?**
  GitHub's own e-mail to whoever last edited the schedule is the default;
  a Slack webhook step is the alternative.

Then copy `assets/ci/privacy-check.yml` to `.github/workflows/`, fill in its
`env` block (production URL; install, build and start commands and the
local URL; `WARN_ONLY`), and drop the nightly job if the owner said no. If
the host posts GitHub deployment statuses for previews, tell the owner to
set the repository variable `PRIVACY_CHECK_PREVIEW=deployment`. Details:
`references/verify.md`, "In CI". For links across the whole site, also
offer `assets/ci/links.yml` (lychee: internal links on pull requests,
external ones weekly); for uptime and certificate or domain expiry, suggest
a monitor (`references/decisions.md`, 4c) rather than building anything,
and list it in the owner's to-do list. On another CI, run the same command line
(`--config … --json …`) and keep `privacy-check.json`.

### 5. Report to the owner

Write a short summary:

- What was built.
- Which decisions the owner made.
- The verify output, all of it.
- What the owner still has to do, for example:
  - set environment variables;
  - create the Slack app (and the ops channel for alerts);
  - schedule the retention and health jobs;
  - sign the PostHog DPA;
  - change PostHog project settings;
  - have the privacy text reviewed;
  - open the site once with the owner opt-out (`?k=off`) in their own
    browsers.

## Reference

| File | Use it for |
|---|---|
| `references/decisions.md` | The questions to ask, the three consent models, defaults |
| `references/recipes.md` | How the pieces fit together on plain HTML + Node, Next.js, Astro on Cloudflare |
| `references/tracker.md` | What k.js measures, the wire format, config, per-framework setup |
| `references/collector.md` | Validation, storage schema, stores, hosting recipes, reading totals |
| `references/consent.md` | Banner rules, consent.js, porting it to a framework, withdrawal |
| `references/posthog.md` | Hardened PostHog: config, before_send, proxy, project settings |
| `references/notifications.md` | Per-visit lines in Slack or e-mail, the weekly digest, deploy markers, a daily-digest recipe |
| `references/ai-visibility.md` | Visits from AI assistants, AI crawler counts, Search Console's daily top queries |
| `references/alerts.md` | Health and anomaly alerts: rules, defaults, scheduling, what to ask |
| `references/privacy-policy.md` | What the privacy page must say, per model |
| `references/verify.md` | Running verify.mjs, what each check means, the config file, CI, manual checks |
| `references/gotchas.md` | Pitfalls and their fixes |
| `assets/` | k.js, collector.mjs (stores: memory, files, Mongo, SQL, Analytics Engine), visits.mjs, digest.mjs, health.mjs, retention.mjs, dsar.mjs, crawlers.mjs (+ crawlers-list.mjs), gsc.mjs, consent.js, posthog-guard.mjs, posthog-proxy.mjs |
| `assets/ci/` | GitHub Actions workflows: `privacy-check.yml` (verify on pull requests and nightly), `links.yml` (lychee link check), `deploy-marker.yml` (deploy markers); `privacy-check.config.example.json` |
| `scripts/` | verify.mjs (the browser check), update-crawlers.mjs (refreshes the crawler list) |

## Mistakes to avoid (details in references/gotchas.md)

- **A framework rewrite as the PostHog proxy.** It forwards every header,
  including login cookies. Use the header allowlist proxy.
- **Calling PostHog `reset()` after `opt_out_capturing()`.** `reset()` clears
  the opt-out, so withdrawal silently re-enables capture. Opt out last.
- **Event batching on.** A queued batch is sent after the visitor withdraws.
  Set `request_batching: false`.
- **`maskCapturedNetworkRequestFn: () => null`.** It also blanks the page URLs
  in recordings. Use the selective version in `posthog-guard.mjs`.
- **Recordings keep links as full URLs.** rrweb stores `<a href="#faq">` as the
  whole page URL, including the query. Clean them with the guard's `maskAttributeFn`.
- **PostHog feature flags left on.** `/flags` carries the first URL a browser
  saw, outside `before_send`. Disable flags unless the site uses them.
- **The entry sent only with the first view.** Consent usually comes after
  that view, so the per-visit rows lack source, country and device. k.js
  repeats the entry once (`en: 2`) on the first report with ids.
- **A path rule only for lower case.** Paths are case-sensitive; write the
  private-path rule as `/^\/(account|reset)(\/|$)/i` (k.js, consent.js,
  the collector and posthog-guard all read that form) or redirect other
  spellings.
- **Testing in an automated browser without hiding automation.** k.js and
  PostHog stay silent under `navigator.webdriver`, and collectors drop
  "HeadlessChrome". verify.mjs handles this; hand-written tests must too.
- **Slack lines that quote app data.** Post only what the visitor did;
  never mirror message text, form input or data from third-party
  integrations.
