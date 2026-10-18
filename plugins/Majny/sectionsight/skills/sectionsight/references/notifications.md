# Notifications: a line per notable visit, and a weekly digest

The per-visit lines (`assets/visits.mjs`) and the weekly "what changed"
digest (`assets/digest.mjs`) are shipped code. A daily digest is a recipe
at the end: the agent writes it for the project from the totals if wanted.

`assets/visits.mjs` turns rows into visits and visits into one Slack line
(`visitLine`) or a short plain-text block (`visitText`). `planVisits`
decides what to post and when. It needs rows, so it only works in model B
(consented visits) or C.

```text
🎯 🇨🇿 · mobile · google · / 0:42 ↓75% (pricing 0:20 · intro 0:12) → /signup 1:10 → 🎯 signup · ▶ replay
```

Each line has these parts:

- the country flag, the device class and the source;
- each page with its active time, depth and top sections;
- what the visitor clicked or reached;
- a replay link, when a recording exists.

**Never** an IP, a city, a name, an e-mail, a phone number, an id or a URL
with a token. Everything from the browser is escaped for Slack, so a source
of `<!channel>` cannot ping anyone.

## When a visit is posted

- **Grouping.** Rows are grouped per visit id and split after 30 quiet
  minutes. A late report from a view that is already known (a tab left
  open, then closed) still joins its visit.
- **Settling.** A visit is evaluated once, 30 minutes after its last report
  (`settleMs`). If its last page sent no time report (the page may still be
  open), it waits `openWaitMs` (25 min) longer.
- **What counts as notable** (`isNotable`, replaceable): any of 10 s active,
  two pages, a click that is not internal navigation, a goal, a copy, or a
  print.
- **Caps.** At most `dayCap` (25) lines a day. A visit with a goal still
  gets one, up to `hardCap` (100). Skipped visits are counted, so a daily
  parent message can say "+N not shown".
- **The day.** A visit belongs to the day it started on.

## The runner (write it for the project's scheduler)

Every 2–10 minutes:

1. Read the rows of yesterday and today, **newest first**, with a limit (e.g.
   20,000). Log a warning when the limit is hit.
2. Load the state document. It defaults to `{ seen: {}, views: {}, days: {} }`.
   It remembers the visits and page views evaluated in the last `keepDays`
   days, so a visit that crosses midnight is never posted twice. A runner
   may keep its own fields in `state.days[day]`, e.g. the Slack `ts` of the
   day's parent message.
3. `const { state, lines } = planVisits(rows, prior, new Date(), options)`:

   | Option | Default | Meaning |
   |---|---|---|
   | `replayUrl` | — | the recording link prefix; a visit with a recording gets `▶ replay` |
   | `timeZone` | `UTC` | for `visitText`'s times |
   | `settleMs` | 30 min | how long a visit must be quiet before it is evaluated |
   | `openWaitMs` | 25 min | the extra wait while its last page may still be open |
   | `dayCap` | 25 | lines a day |
   | `hardCap` | 100 | lines a day, counting goal visits past `dayCap` |
   | `keepDays` | 3 | how long evaluated visits are remembered |
   | `notable` | `isNotable` | `(visit) => boolean` |
4. **Save the state before posting.** If saving fails, post nothing: a
   failed save then cannot post a visit twice.
5. Post the lines. Use one parent message per day ("🌐 Visits · Mon 5 Oct ·
   N worth a look") with the lines as thread replies (bot token; keep each
   day's parent `ts` in the state), or flat (webhook).
6. Pace the posts at about 1 per second per channel.
7. **Record each posted message** with `rememberPosted(state, { channel, ts })`
   (parents too) and save the state again. `deleteOldSlackLines`
   (`retention.mjs`) deletes them when the Slack retention ends. If that
   second save fails, those lines are not deleted automatically: keep a
   channel retention in Slack as the backstop.

```js
import { planVisits, postToSlack, rememberPosted } from './visits.mjs';
import { deleteOldSlackLines } from './retention.mjs';
const rows = await db.collection('web_events').find({ day: { $in: [yesterday, today] } }).sort({ at: -1 }).limit(20000).toArray();
const prior = (await db.collection('state').findOne({ _id: 'web-visits' }))?.value ?? { seen: {}, views: {}, days: {} };
const { state, lines } = planVisits(rows, prior, new Date(), {
  replayUrl: 'https://eu.posthog.com/project/<id>/replay/', timeZone: 'Europe/Berlin',
});
if (JSON.stringify(state) !== JSON.stringify(prior)) {
  await db.collection('state').updateOne({ _id: 'web-visits' }, { $set: { value: state } }, { upsert: true });
}
for (const l of lines) {
  const channel = process.env.SLACK_VISITS_CHANNEL;
  const ts = await postToSlack({ token: process.env.SLACK_BOT_TOKEN, channel, text: l.line });
  rememberPosted(state, { channel, ts });
}
// Once a day is enough: delete the lines older than the Slack retention.
const { state: pruned } = await deleteOldSlackLines({ state, slackDays: 30, token: process.env.SLACK_BOT_TOKEN });
await db.collection('state').updateOne({ _id: 'web-visits' }, { $set: { value: pruned } }, { upsert: true });
```

**Schedulers:**

- a Node service with `setInterval`, run only by the leader if there are several instances;
- a Cloudflare Worker cron trigger (e.g. `*/10 * * * *`);
- a Vercel or Netlify scheduled function;
- a GitHub Actions schedule (it drifts by minutes, which is fine).

**Rolling deploys** run two instances at once. Hold a lease in the database
before posting, or the same line can go out twice.

## Slack setup (the owner does this)

- **The app.** Create a Slack app with the bot scope `chat:write` only.
  Install it, then invite the bot to the channel (`/invite @app`). Address
  the channel by its **id** (`C0…`): without `channels:read` the bot cannot
  look names up.
- **Or an incoming webhook.** It is simpler: one channel, no threads, no
  edits.
- **Secrets.** The token or webhook URL is a secret: environment variables
  only, never in code, logs or the client. If a vendor ever shows it back
  unmasked, rotate it.
- **Errors.** On `invalid_auth`, stop posting, log once, and show it on a
  health endpoint rather than failing every poll.
- **Retention.** Slack keeps the bot's messages until someone deletes them.
  The free plan shows 90 days and deletes data older than a year.
  `deleteOldSlackLines` deletes the bot's own lines after `slackDays`
  (`chat:write` covers deleting its own messages; it uses the recorded `ts`
  values and never reads the channel's history). It handles rate limits
  (HTTP 429 or an `error: "ratelimited"` answer, `Retry-After`) and stops
  on a token problem. An entry without a date counts as old enough and is
  deleted on the next run. Set a channel retention too as a backstop, and
  state the real period in the privacy text.
- **One channel per purpose.** Visits go to a channel about people (sign-ups,
  visits). Health alerts (`alerts.md`), deploy and startup noise go to an
  ops channel, or nowhere.

## E-mail instead of Slack

- **With `visits.mjs`.** The same runner sends one e-mail per entry of
  `lines`, with `visitText` as the plain-text body, through any SMTP
  service or Cloudflare Email Routing (a `send_email` binding to the owner's
  verified address).
- **A notifier on Cloudflare** that reads Analytics Engine over its SQL
  API can work from time windows instead of `planVisits`' state document:
  see "Window" below.
- **Format.** A plain-text part, plus optionally simple HTML (tables and
  inline styles, no images or scripts). Escape every value a visitor
  controls.
- **Window.** A 10-minute cron mails each visit that ended 5–15 minutes
  earlier. The windows of consecutive runs meet without overlap, so each
  visit goes out once.
- **Cap.** At most 5 e-mails a run; the rest are summarised in one line of
  the last e-mail.

## The weekly digest (`assets/digest.mjs`, from the totals)

`weeklyDigest({ store, week, timeZone, site })` reads the totals of one week
(Monday to Sunday, in the collector's time zone; default: the last complete
week) and of the 4 weeks before, and returns `{ text, from, to, data }`:
mrkdwn for Slack (`format: 'slack'`, every value escaped with visits.mjs's
`esc`) or plain text for an e-mail (`format: 'text'`). It never reads rows,
so it works in every model, A included.

```text
*Weekly · example.com · 28 Sept – 4 Oct 2026*
Visits 140 · last week 70 (+100%) · 4-week average 70 (+100%)
Page views 280 · last week 140 (+100%) · 4-week average 140 (+100%)
Sources: google 80 (+100%) · direct 30 (0%) · AI assistants 30 (chatgpt 20, perplexity <10)
*Read-rate changes*
/pricing · plans: 43% read (120 of 280), last week 29% (40 of 140), +14 pts
*Goals*
signup 30 · last week 10 · google 10, ai <10, entry unknown <10
*Consent*
Banner shown on 210 page views · accepted 60 · declined 80 · withdrawn <10 · accept rate 43% of answers
Per-visit rows and visit lines cover only the people who accepted (about 43% of those who answered): …
*New this week*
New sources: partner.example 10
New 404 paths: /old.page 20
New JavaScript errors: error 1f2e3d4c · app-*.js:3 (30)
*Slow pages (Core Web Vitals, 75th percentile)*
/pricing · mobile LCP over 6 s (poor, 120 views) · poor mostly in hero (50)
*AI crawlers*
60 requests · last week 60 · fetched live for an answer: 20 · answered 4xx/5xx: <10
*Google Search (data for 7 of 7 days so far; Search Console lags 2–3 days)*
Clicks 70 · last week 40 (+75%) · impressions 7,000
*Deploys*
abcdef1 Wed 30 Sept, 12:00 (v1.4)
_Counts under 10 show as <10, others are rounded to tens; percentages use the rounded counts._
```

What each part reads:

| Part | From |
|---|---|
| Visits, page views | `visits`, `views`, against last week and the average of the earlier weeks that have data |
| Sources | `src.*`; the AI assistants (`AI_SOURCES`) as one group with its members |
| Read-rate changes | `sec.<s>.r ÷ views` per page, only where the views and the reads are at least `minSample` in both weeks; the biggest moves in percentage points |
| Goals | `goal.*`, split by `goalsrc.<goal>.<class>` (`collector.md`); "entry unknown" is a goal on a page load that continued a visit |
| Consent | `consent.*`, only when the owner counts them (`decisions.md`, 4e); no accept rate while either count shows as `<10` |
| New this week | `src.*`, `out.*`, `nf.*`, `nfin.*` and `err.*` keys never seen in the 4 weeks before; an error by fingerprint, file and line (its scrubbed message only with `showErrorText: true`: scrubbing cannot see a name written without quotes) |
| Slow pages | `cwv.<device>.<metric>` p75 (`p75FromBuckets`) for pages with at least `minSample` measured views, worst first, with the section from `cwvs.*` |
| AI crawlers | `crawl.*` and `crawlp.*` (`crawlers.mjs`, `ai-visibility.md`) |
| Google Search | `store.gsc(day)` documents (`gsc.mjs`), the queries whose clicks moved most (`gscQueries: false` shows the totals only) |
| Deploys | `deploys` on the days' `"<day> *"` documents (`markDeploy`, below) |

A part with nothing to say is left out.

**Rounding (the owner decides; default on).** `rounding: 'tens'`: 0 stays
0, a count from 1 to 9 is shown as `<10`, larger counts are rounded to the
nearest ten, and every percentage and rate is computed from the rounded
counts, so the percentages do not undo the rounding. CNIL's self-assessment
tool for exempted audience measurement suggests rounding small counts to
tens (`decisions.md`). `rounding: 'none'` shows exact counts, for a digest
only the owner reads. **Guards:** a percentage needs a base of at least
`minSample` (default 30) after rounding; read-rate movers need `minSample`
views and `minSample` reads in both weeks (a `<10` is never taken as 0);
the accept rate needs both answers at 10 or more and `minSample` in all;
vitals need `minSample` measured views.

```js
import { weeklyDigest } from './digest.mjs';
import { postToSlack } from './visits.mjs';
// Mondays 08:00 in the owner's time zone
const { text } = await weeklyDigest({ store, timeZone: 'Europe/Berlin', site: 'example.com' });
await postToSlack({ token: process.env.SLACK_BOT_TOKEN, channel: process.env.SLACK_DIGEST_CHANNEL, text });
// or postToWebhook(process.env.SLACK_DIGEST_WEBHOOK, text), or e-mail weeklyDigest({ …, format: 'text' }).text
```

Options: `week` (any day of the week to report), `now`, `timeZone`, `site`,
`rounding`, `minSample`, `format`, `top` (entries per list, default 5),
`showErrorText` (default false) and `gscQueries` (default true; Search
Console queries can hold a name Google did not anonymise, see
`ai-visibility.md`).
Post it where the owner reads numbers about the site (the visits channel
or e-mail); record the message with `rememberPosted` if the Slack lines'
retention should cover it too.

## Deploy markers

`markDeploy({ store, sha, at, note, timeZone })` (collector.mjs) adds
`{ sha, at }` to the day's `"<day> *"` document: the commit's first 7 hex
characters and the minute, at most 20 per day, the newest kept
(`DEPLOY_CAP`, the same in every store), once per sha and day. `note` is
kept only as a short plain label (`v1.4`, `hotfix`): never pass a commit
message, which can name people. The weekly digest lists the week's deploys,
and every health alert within 24 hours of one ends with "(after deploy
abc1234 at 2026-01-15 14:10 Europe/Berlin)" (`alerts.md`). Memory, files,
Mongo and SQL keep them (SQL in `web_deploys`; run `init()` again on an
existing install); Analytics Engine answers `{ unsupported }`.

From CI, `assets/ci/deploy-marker.yml` runs a small script of the project
after a successful production deploy:

```js
// scripts/mark-deploy.mjs (the project's; open the store as the collector does)
import { MongoClient } from 'mongodb';
import { mongoStore, markDeploy } from '../lib/analytics/collector.mjs';
const client = await MongoClient.connect(process.env.ANALYTICS_STORE_URL);
try {
  console.log(await markDeploy({ store: mongoStore(client.db()), sha: process.argv[2], timeZone: 'Europe/Berlin' }));
} finally {
  await client.close();
}
```

## A daily digest (a recipe: from the totals, no rows)

The weekly digest is shipped; a daily one is a recipe the agent writes
for the project if the owner wants it, from the same totals. Example, 08:00
in the owner's time zone:

```text
🌐 Web · yesterday: 37 visits · 61 views · median 30s–1m · 9 stayed ≥ 1 min
Most read: /pricing "plans" 0:21 avg · / "how-it-works" 0:14
Clicks: signup 3 · outbound github.com 2 · e-mail 1
Sources: google 14 · direct 11 · linkedin 6 · newsletter 3
Goals: signup 2 (5.4% of visits)
Friction: 4 dead clicks on /pricing "compare"
```

- **Median visit length:** read it from the `hist.*` buckets (see
  `collector.md`, Reading the totals).
- **Compare with last week:** compare the same weekday; percentages lie on
  small numbers, so show both counts, and round them as the weekly digest
  does (`roundCount` in digest.mjs).
- **Slack limits:** a section block holds at most 10 fields of up to 2,000
  characters each.

## Two rules for anything that posts

- **Post what visitors did, never message text.** Never post free text
  that a product or third-party integration produced (messages, titles,
  notes): it can quote personal or third-party data. Some API terms, e.g.
  Google's Limited Use policy, forbid humans from reading such data. Audit every path that can post text: feeds, alerts,
  dead-letter dumps, digests.
- **Read the database directly.** Bot protection on a CDN can block a
  server job that fetches the site's public URL; read the database or use
  private networking.
