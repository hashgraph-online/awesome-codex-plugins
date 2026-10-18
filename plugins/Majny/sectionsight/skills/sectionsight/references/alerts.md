# Health and anomaly alerts

The collector answers `204` to everything, on purpose: a browser never
waits, and a hostile client learns nothing. The price is that a database
outage, a tracker that stopped loading after a deploy, or a sign-up form
that broke goes unnoticed. `assets/health.mjs` looks for those from the totals
and posts a short line to an **ops** channel when something is off, and a
"recovered" line when it clears.

## What the collector records

Every store keeps a health record per collector instance, written off the
hot path:

- never awaited by a request;
- at most once a minute, on reports as well as writes, so a stored record
  shows reports arriving while writes do not;
- and at once when writes start or stop failing, or a deletion is dropped.


| Field | Meaning |
|---|---|
| `lastWrite` | the minute of the last successful write (ISO) |
| `writeErrors` | failed writes since the last success |
| `lastError` | the class of the last failure (`MongoNetworkError ECONNREFUSED`), never its message, which can quote data |
| `lastReport` | the minute the last valid report arrived, written or not |
| `reports`, `since` | valid reports this process has received, and since when |
| `delDropped`, `lastDelDrop` | visitors' deletion requests dropped (their own rate limit, a store error), and the minute of the last |
| `instance`, `savedAt` | a random id of the process, and when it saved |

**Several instances** (serverless, autoscaling, rolling deploys) each keep
their own record. `store.health()` merges them: the newest `lastWrite` and
`lastReport` of any instance, and the failures (worst `writeErrors`,
dropped deletions added up) of instances that saved within the last 2
hours (`HEALTH_LIVE_MS`), so a failure of an instance that is gone does not
alert forever. Records older than 7 days are dropped on save.

Times are rounded to the minute, and only the latest record is kept: it
holds no id and no path.

- **Memory, files, Mongo, SQL** keep it (`store.health()`, or
  `readHealth(store)`): files in `<dir>/health.json`, Mongo in `web_health`,
  SQL in the `web_health` table.
- **The collector's own process** always has it in memory:
  `collect.health()`. An alert job in the same process (a Node server with a
  timer) should pass it as `health`, because a failing database cannot
  store its own failure.
- **Analytics Engine** cannot be read back cheaply and keeps no record.
  `analyticsEngineReader({ accountId, apiToken, dataset })` reads the totals
  and the newest data point over the SQL API, so rules (a), (b), (c) and (e)
  work, and (d) alerts when the newest data point is older than
  `staleMinutes` while those hours usually bring visits (below). Failed
  writes exist only in the Worker's `collect.health()`; expose them on a
  private route if wanted. Tested against a stand-in for the SQL API only.

The collector also counts visits per hour of the day (`hour.<HH>` on the
day's visits document, in the owner's time zone), which rules (a) and (b)
need. `hourly: false` turns that off; those two rules then say they cannot
run. It is a count per hour, no more, but on a very quiet day it narrows
when a visit happened: mention it to the owner of a tiny site.

## The rules

Each rule compares with the **median of the same weekday** (and, for (a)
and (b), the same hours) **over the last 4 weeks** (`weeks`), and stays
quiet below a minimum baseline, so a small site does not flap. Missing
weeks count as zero, so a new install stays quiet until it has history.

| Rule | Fires when | Defaults |
|---|---|---|
| **(a) silence** | no visit stored in the last `hours` hours (and the current one), while the same hours usually have at least `minExpected` | 3 h, 5 |
| **(b) low** | visits so far today (complete hours) under `percent`% of the usual for those hours, and the usual is at least `minBaseline` | 40%, 20 |
| **(b2) high** | visits so far today at least `factor`× the usual for those hours and at least `min` (an info line: a big link, or bots inflating the totals) | 3×, 30 |
| **(c) goal** | a goal at 0 for `days` full days while its median over the 28 days before is at least `minPerDay` | 3 days, 1/day |
| **(c2) forms** | a `data-kform` form submitted at least `minSubmits` times today and the `days`-1 days before, while the goal of the same name stayed at 0, once that goal has been reached in the 28 days before. It works on a small site too: it needs no baseline of daily goals | 2 days, 3 |
| **(d) writes** | `writeErrors > 0`; or reports arrive with no write for `staleMinutes`; or the last write is older than `staleMinutes` while the same hours of earlier weeks brought at least `silence.minExpected` visits (this works from a separate job, after the collector instance is gone, and on Analytics Engine; it needs the hourly counts) | 30 min |
| **deletions** | a visitor's deletion request was dropped in the last `withinHours` | 24 h |
| **(e) notFound** | 404s today (`nf.*`) at least `factor`× a usual whole day and at least `min` | 3×, 20 |
| **(e) brokenLinks** | a `nfin.<path>` (a 404 reached from the site's own page) today or yesterday that the 28 days before did not have | on |
| **(f) errors** | a JavaScript error (k.js `data-errors`, `err.<fp>` summed over the day's pages) that the 28 days before did not have, at least `newMin` times today (a first-ever `err.(other)`, errors past the day's cap of distinct ones, counts as a flood); or one they had, at least `factor`× its usual whole day (median of the same weekday) and at least `min`. At most `max` listed, the most frequent first. An error is named by fingerprint, file and line; its scrubbed message only with `checkHealth({ showErrorText: true })`, because scrubbing cannot see a name written without quotes | 5; 3×, 20; 5 |
| **store** | the totals cannot be read at all | always |

**After a deploy.** When a deploy marker (`markDeploy`, `notifications.md`)
is less than 24 hours old, every alert ends with "(after deploy abc1234 at
2026-01-15 14:10 Europe/Berlin)", in the `timeZone` given to `checkHealth`:
the newest marker of today or yesterday. A "Recovered" line does not.

A rule alerts **at most once a day** while it fails (the next day it says
"Still: …" once), and posts **"Recovered: …"** when it clears. The state
that remembers this is a small JSON object the caller saves, like
`visits.mjs`'s: **save it before posting**, so a failed save posts nothing
twice. A rule that could not run (the store unreadable, no health record)
neither fails nor recovers.

**Quiet hours** (`quietHours: { from: 22, to: 7 }`, the owner's time zone):
nothing is evaluated or posted and the state is unchanged, so whatever is
still wrong is posted when they end.

**What an alert contains:** counts, medians, goal names and the paths of
broken links that look like the site's own (`nfin.*`: k.js said the link
was internal and the request came with a same-site `Referer`; a crafted
request can fake both, so such a path is listed, escaped, up to 5), and
for rule (f) the error's sample: its scrubbed message, file and line, and
the path it was first seen on (`collector.md`, "JavaScript errors"); a store
without samples (Analytics Engine) gives the fingerprint only. Never
an id, a row, an IP or a visitor's path through the site. Other 404 paths
(`nf.*`, often bots probing) are counted, never listed. Everything is
escaped for Slack.

## Running it

```js
import { checkHealth, postAlerts } from './health.mjs';
const prior = (await db.collection('state').findOne({ _id: 'web-health' }))?.value ?? null;
const { alerts, recovered, state, notes } = await checkHealth({
  store,                                  // the collector's store (or analyticsEngineReader(...))
  timeZone: 'Europe/Berlin',              // the collector's
  rules: { low: { percent: 40 }, quietHours: { from: 22, to: 7 } },
  state: prior,
  health: collect.health?.(),             // only in the collector's own process
});
await db.collection('state').updateOne({ _id: 'web-health' }, { $set: { value: state } }, { upsert: true });
await postAlerts({ alerts, recovered, token: process.env.SLACK_BOT_TOKEN, channel: process.env.SLACK_OPS_CHANNEL,
  visitsChannel: process.env.SLACK_VISITS_CHANNEL, visitsWebhook: process.env.SLACK_VISITS_WEBHOOK, site: 'example.com' });
if (notes.length) console.log('[health]', notes.join('; '));
```

- **Where alerts go:** `SLACK_OPS_CHANNEL` with the bot token, or a
  webhook of their own (`webhook: process.env.SLACK_OPS_WEBHOOK`). **Never
  the visits channel**: that one is about people, this one is about
  machines. Pass `visitsChannel` (and `visitsWebhook`) and `postAlerts`
  refuses a mix-up.
- **E-mail:** `alertText({ alerts, recovered }, { format: 'text' })` gives the
  plain text; send it with the project's mailer.
- **A file instead of a database** for the state: `JSON.parse(await
  readFile('health-state.json'))`, write it with a temporary file and a
  rename.

**Schedule** (every 15–30 minutes is plenty):

- a Node service: `setInterval`, in the leader instance only;
- a Cloudflare Worker cron trigger (`*/15 * * * *`), reading Analytics
  Engine with `analyticsEngineReader` or D1 through `sqlStore`;
- a GitHub Actions schedule (`cron: '*/30 * * * *'`; it drifts by minutes,
  and it needs read access to the store, so mind where its credentials live);
- Vercel or Netlify scheduled functions.

Run it next to the database, not through the public site. Bot protection
on a CDN can block a server job that fetches the site's public URL; read
the database or use private networking (`notifications.md`).

## Ask the owner

- **Where alerts go:** an ops channel (id), a separate webhook, or e-mail.
  Not the visits channel.
- **Thresholds:** the defaults above; a site with steady traffic may want
  (b) at 50%, a spiky one at 25%. Which goals matter enough for rule (c).
- **Quiet hours,** if any, in their time zone.
- **Hourly counts:** keep them (rules a and b need them) or `hourly: false`.
- **JavaScript errors** (rule f, only with k.js `data-errors="on"`): the
  thresholds, or `errors: false`. A site with a noisy third-party widget
  may want `newMin` higher; its errors from other origins are already
  dropped by k.js.

## What it cannot see

- **A tracker that sends but measures wrong** (sections missing, a goal
  attached to the wrong button): the counts look normal. `verify.mjs` and
  its nightly CI run catch those.
- **Sampling** on Analytics Engine at volume makes small counts noisy.
- **Bots** that inflate 404s trigger rule (e); that is by design, and
  harmless.
