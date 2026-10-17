/**
 * Health and anomaly alerts from the collector's totals: the collector
 * answers 204 to everything, so a database outage, a tracker that stopped
 * loading or a broken sign-up form goes unnoticed unless something checks.
 * Reference implementation from the sectionsight skill (MIT).
 *
 *   import { checkHealth, postAlerts } from './health.mjs';
 *   const { alerts, recovered, state } = await checkHealth({ store, state: prior, timeZone: 'Europe/Berlin' });
 *   await saveState(state);              // before posting, as visits.mjs does
 *   await postAlerts({ alerts, recovered, token, channel: process.env.SLACK_OPS_CHANNEL });
 *
 * Every rule compares with the median of the same weekday (and the same hours)
 * of the last `weeks` weeks, and stays quiet below a minimum baseline, so a
 * small site does not flap. A rule alerts at most once a day while it fails,
 * and posts a "recovered" line once it clears. Alerts carry totals only:
 * counts, goal names, the site's own broken-link paths and scrubbed JavaScript
 * error samples (store.errSamples), never an id or a row.
 * See references/alerts.md.
 */
import { esc, postToSlack, postToWebhook } from './visits.mjs';
import { readHealth, errorClass, hourOf, dayOf, DAILY_CAPS } from './collector.mjs';

export const DEFAULT_RULES = {
  /** (a) No visit stored for `hours` hours while the same hours usually have at least `minExpected`. */
  silence: { hours: 3, minExpected: 5 },
  /** (b) Visits so far today below `percent`% of the usual, when the usual is at least `minBaseline`. */
  low: { percent: 40, minBaseline: 20 },
  /** (b2) High: visits so far today at least `factor`× the usual and at least `min`: a big link, or bots. */
  high: { factor: 3, min: 30 },
  /** (c) A goal at 0 for `days` full days while its median is at least `minPerDay` a day. */
  goal: { days: 3, minPerDay: 1 },
  /** (c2) Forms (k.js data-kform): at least `minSubmits` submits today and the `days`-1 days before,
   *  and 0 of the goal with the same name, when that goal was reached in the 28 days before. */
  forms: { days: 2, minSubmits: 3 },
  /** (d) Failed writes, or reports arriving without a write for `staleMinutes`. */
  writes: { staleMinutes: 30 },
  /** Deletion requests the collector dropped within the last `withinHours`. */
  deletions: { withinHours: 24 },
  /** (e) 404s today at least `factor`× a usual whole day and at least `min`; and new internal broken links. */
  notFound: { factor: 3, min: 20, brokenLinks: true },
  /** (f) JavaScript errors (k.js data-errors): a fingerprint new today with at least `newMin`,
   *  or one at least `factor`× its usual whole day and at least `min`. At most `max` listed. */
  errors: { newMin: 5, factor: 3, min: 20, max: 5 },
  /** How many earlier weeks make the baseline. */
  weeks: 4,
  /** { from: 22, to: 7 }: hours (owner's time zone) when nothing is posted; it waits. */
  quietHours: null,
};

const MS_DAY = 86_400_000;
/** "2026-10-09" minus n days. */
export function addDays(day, n) {
  return new Date(Date.parse(`${day}T00:00:00Z`) + n * MS_DAY).toISOString().slice(0, 10);
}
export function median(xs) {
  if (!xs.length) return 0;
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}
const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : 0);
const sumOf = (o) => (o && typeof o === 'object' ? Object.values(o).reduce((n, v) => n + num(v), 0) : 0);
const WEEKDAY = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
const weekdayOf = (day) => WEEKDAY[new Date(`${day}T12:00:00Z`).getUTCDay()];
const round = (x) => Math.round(x * 10) / 10;

function inQuiet(hour, q) {
  if (!q || typeof q.from !== 'number' || typeof q.to !== 'number' || q.from === q.to) return false;
  return q.from < q.to ? hour >= q.from && hour < q.to : hour >= q.from || hour < q.to;
}

/**
 * Runs every rule. Options:
 *   store      a collector store with totals(day) (and health() for rule d)
 *   now        default new Date()
 *   timeZone   the collector's time zone (its days and hours)
 *   rules      overrides of DEFAULT_RULES, per rule; a rule set to false is off
 *   state      what the last run returned (null the first time)
 *   health     optional: the collector's in-memory record (collect.health()),
 *              when this runs in the collector's process; else store.health()
 *   showErrorText  default false: rule (f) names an error by fingerprint, file and
 *              line; true adds its scrubbed message, which can still quote a name
 *
 * Returns { alerts, recovered, state, notes, quiet }:
 *   alerts     [{ rule, severity, text }] new today, or still failing on a new day
 *   recovered  [{ rule, text }] rules that alerted and have cleared
 *   state      save it BEFORE posting (a failed save then posts nothing twice)
 *   notes      rules that could not run, and why (no hourly counts yet…)
 *   quiet      true in quiet hours: nothing is evaluated or posted, the state is unchanged
 */
export async function checkHealth({ store, now = new Date(), timeZone = 'UTC', rules = {}, state = null, health, showErrorText = false } = {}) {
  const R = {};
  for (const [k, v] of Object.entries(DEFAULT_RULES)) R[k] = rules[k] === false ? false : v && typeof v === 'object' ? { ...v, ...(rules[k] ?? {}) } : (rules[k] ?? v);
  const prior = { active: { ...(state?.active ?? {}) } };
  const today = dayOf(now, timeZone);
  const hour = Number(hourOf(now, timeZone));
  if (inQuiet(hour, R.quietHours)) return { alerts: [], recovered: [], state: prior, notes: [], quiet: true };

  const failing = new Map(); // key → { rule, severity, text }
  const evaluated = new Set(); // rule names whose keys may recover
  const notes = [];
  const fail = (key, rule, severity, text) => failing.set(key, { rule: key, severity, text });

  // The totals, read once per day.
  const cache = new Map();
  const totalsOf = (day) => {
    if (!cache.has(day)) cache.set(day, Promise.resolve(store.totals(day)).then((t) => t ?? {}));
    return cache.get(day);
  };
  const visitsDoc = async (day) => (await totalsOf(day))[`${day} *`] ?? null;
  // A day's JavaScript errors per fingerprint, summed over its pages.
  const errsOf = async (day) => {
    const out = {};
    for (const [id, doc] of Object.entries(await totalsOf(day))) {
      if (id === `${day} *` || !doc?.err || typeof doc.err !== 'object') continue;
      for (const [fp, n] of Object.entries(doc.err)) out[fp] = (out[fp] ?? 0) + num(n);
    }
    return out;
  };
  const hours = (doc) => (doc?.hour && typeof doc.hour === 'object' ? doc.hour : null);
  const hourCount = (doc, h) => num(hours(doc)?.[String(h).padStart(2, '0')]);
  const weeks = Array.from({ length: Math.max(1, R.weeks | 0) }, (_, i) => addDays(today, -7 * (i + 1)));

  let readable = true;
  try {
    if (typeof store?.totals !== 'function') throw Object.assign(new Error('the store has no totals(day)'), { name: 'Unsupported' });
    await visitsDoc(today);
  } catch (err) {
    readable = false;
    if (err?.name === 'Unsupported') notes.push('totals rules: the store has no totals(day) (Analytics Engine: use analyticsEngineReader)');
    else fail('store', 'store', 'critical', `Cannot read the analytics store (${errorClass(err)}). The collector may be failing too.`);
  }
  evaluated.add('store');

  // Sum of visits over the n hours before `endHour` of `day` (crossing midnight
  // into earlier days as needed).
  const windowSum = async (day, endHour, n) => {
    let total = 0;
    for (let i = 1; i <= n; i++) {
      const h = endHour - i;
      const back = Math.floor(h / 24);
      total += hourCount(await visitsDoc(addDays(day, back)), h - back * 24);
    }
    return total;
  };
  let hourly = false;
  if (readable) {
    for (const d of weeks) if (hours(await visitsDoc(d))) hourly = true;
  }

  if (readable) {
    // (a) Silence: nothing in the last N hours (and the current one) while those hours are usually busy.
    if (R.silence) {
      if (!hourly) notes.push('silence: no hourly counts in the last weeks yet (hour.<HH> is counted from the first day the collector runs with hourly on; or hourly: false)');
      else {
        evaluated.add('silence');
        const n = Math.max(1, R.silence.hours | 0);
        const nowCount = (await windowSum(today, hour, n)) + hourCount(await visitsDoc(today), hour);
        const usual = median(await Promise.all(weeks.map((d) => windowSum(d, hour, n))));
        if (nowCount === 0 && usual >= R.silence.minExpected) {
          fail('silence', 'silence', 'critical', `No visit stored for ${n} hours. The same hours of the last ${weeks.length} ${weekdayOf(today)}s had ${round(usual)} (median). Is the tracker loading, and is the collector writing?`);
        }
      }
    }

    // (b) Low: visits so far today well below the same hours of earlier weeks.
    if (R.low) {
      if (!hourly) notes.push('low: no hourly counts in the last weeks yet');
      else if (hour > 0) {
        evaluated.add('low');
        const sofar = await windowSum(today, hour, hour);
        const usual = median(await Promise.all(weeks.map((d) => windowSum(d, hour, hour))));
        if (usual >= R.low.minBaseline && sofar < (R.low.percent / 100) * usual) {
          fail('low', 'low', 'warning', `Visits today by ${String(hour).padStart(2, '0')}:00: ${sofar}, usually ${round(usual)} (median of the last ${weeks.length} ${weekdayOf(today)}s), under ${R.low.percent}%.`);
        }
      } else evaluated.add('low');
    }

    // (b2) High: visits so far today well above the same hours of earlier weeks.
    if (R.high) {
      if (!hourly) notes.push('high: no hourly counts in the last weeks yet');
      else if (hour > 0) {
        evaluated.add('high');
        const sofar = await windowSum(today, hour, hour);
        const usual = median(await Promise.all(weeks.map((d) => windowSum(d, hour, hour))));
        if (sofar >= Math.max(R.high.min, R.high.factor * usual)) {
          fail('high', 'high', 'info', `Visits today by ${String(hour).padStart(2, '0')}:00: ${sofar}, usually ${round(usual)} (median of the last ${weeks.length} ${weekdayOf(today)}s). A link from somewhere big, or bots: check the sources.`);
        }
      } else evaluated.add('high');
    }

    // (c) Goals: a goal that stopped for N full days while it usually happens daily.
    if (R.goal) {
      evaluated.add('goal');
      const n = Math.max(1, R.goal.days | 0);
      const recent = [];
      for (let i = 1; i <= n; i++) recent.push(await visitsDoc(addDays(today, -i)));
      const before = [];
      for (let i = n + 1; i <= n + 28; i++) before.push(await visitsDoc(addDays(today, -i)));
      const names = new Set(before.flatMap((d) => Object.keys(d?.goal ?? {})));
      for (const g of [...names].sort()) {
        const usual = median(before.map((d) => num(d?.goal?.[g])));
        const lately = recent.reduce((s, d) => s + num(d?.goal?.[g]), 0);
        if (lately === 0 && usual >= R.goal.minPerDay) {
          fail(`goal:${g}`, 'goal', 'warning', `Goal "${g}": 0 in the last ${n} days, usually ${round(usual)} a day (median of the 28 days before). A broken form or button?`);
        }
      }
    }

    // (c2) Forms: submitted, but the goal the server confirms never comes.
    if (R.forms) {
      evaluated.add('forms');
      const n = Math.max(1, R.forms.days | 0);
      const recent = [];
      for (let i = 0; i < n; i++) recent.push(await visitsDoc(addDays(today, -i)));
      const before = [];
      for (let i = n; i < n + 28; i++) before.push(await visitsDoc(addDays(today, -i)));
      const names = new Set(recent.flatMap((d) => Object.keys(d?.form ?? {})));
      for (const f of [...names].sort()) {
        if (f === 'other' || !before.some((d) => num(d?.goal?.[f]) > 0)) continue;
        const sent = recent.reduce((s, d) => s + num(d?.form?.[f]), 0);
        const done = recent.reduce((s, d) => s + num(d?.goal?.[f]), 0);
        if (sent >= R.forms.minSubmits && done === 0) {
          fail(`forms:${f}`, 'forms', 'critical', `Form "${f}": ${sent} submits since ${addDays(today, -(n - 1))}, none confirmed (goal "${f}" at 0). Is the form's backend failing?`);
        }
      }
    }

    // (e) 404s: a spike today, and broken links of the site's own that are new.
    if (R.notFound) {
      evaluated.add('notFound');
      const t = await visitsDoc(today);
      const nfToday = sumOf(t?.nf);
      const usual = median(await Promise.all(weeks.map(async (d) => sumOf((await visitsDoc(d))?.nf))));
      if (nfToday >= Math.max(R.notFound.min, R.notFound.factor * usual)) {
        fail('notFound', 'notFound', 'warning', `404s today: ${nfToday}, a whole ${weekdayOf(today)} usually has ${round(usual)}. A removed page, a broken deploy, or a bot probing.`);
      }
      if (R.notFound.brokenLinks) {
        evaluated.add('brokenLinks');
        const seen = new Set();
        for (let i = 2; i <= 29; i++) for (const k of Object.keys((await visitsDoc(addDays(today, -i)))?.nfin ?? {})) seen.add(k);
        const fresh = new Set();
        for (const d of [today, addDays(today, -1)]) for (const k of Object.keys((await visitsDoc(d))?.nfin ?? {})) if (!seen.has(k)) fresh.add(k);
        if (fresh.size) {
          const paths = [...fresh].sort().slice(0, 5).map((k) => k.replace(/%2E/g, '.'));
          fail('brokenLinks', 'brokenLinks', 'warning', `New broken link${fresh.size > 1 ? 's' : ''} on the site (404s reached from its own pages): ${paths.join(', ')}${fresh.size > 5 ? ` and ${fresh.size - 5} more` : ''}.`);
        }
      }
    }
  }

  // (f) JavaScript errors: a new fingerprint, or one far above its usual day.
  if (readable && R.errors) {
    evaluated.add('errors');
    const today_ = await errsOf(today);
    const before = new Set();
    for (let i = 1; i <= 28; i++) for (const fp of Object.keys(await errsOf(addDays(today, -i)))) before.add(fp);
    const usual = new Map();
    const hits = [];
    for (const [fp, n] of Object.entries(today_)) {
      if (!usual.has(fp)) usual.set(fp, median(await Promise.all(weeks.map(async (d) => num((await errsOf(d))[fp])))));
      const u = usual.get(fp);
      // A first-ever err.(other) is a flood past the day's cap of distinct errors: flagged too.
      if (!before.has(fp) && n >= R.errors.newMin) hits.push({ fp, n, kind: 'new' });
      else if (before.has(fp) && n >= Math.max(R.errors.min, R.errors.factor * u)) hits.push({ fp, n, u, kind: 'spike' });
    }
    hits.sort((a, b) => b.n - a.n || (a.fp < b.fp ? -1 : 1));
    let samples = {};
    if (hits.length && typeof store.errSamples === 'function') {
      try {
        samples = { ...((await store.errSamples(addDays(today, -1))) ?? {}), ...((await store.errSamples(today)) ?? {}) };
      } catch {
        samples = {};
      }
    }
    for (const h of hits.slice(0, Math.max(1, R.errors.max | 0))) {
      const x = samples[h.fp];
      // The sample was scrubbed twice (k.js, collector); it holds no id.
      // The message only when the owner asked for it (showErrorText): it can quote a name.
      const what = h.fp === '(other)' ? 'errors past the daily cap of distinct errors' : x ? `${showErrorText ? `${String(x.m).slice(0, 120)} · ` : `error ${h.fp} · `}${String(x.f).slice(0, 60)}:${num(x.l)}${typeof x.path === 'string' ? ` · first on ${x.path.slice(0, 80)}` : ''}` : `error ${h.fp} (no sample kept)`;
      fail(`errors:${h.fp}`, 'errors', 'warning', h.kind === 'new'
        ? (h.fp === '(other)' ? `A flood of JavaScript errors: ${h.n} today past the daily cap of distinct errors (${DAILY_CAPS.err} a day per collector process), never seen before. Many different errors at once: a broken deploy, or junk sent to the collector.` : `New JavaScript error, ${h.n} today: ${what}`)
        : round(h.u) === 0
          ? `JavaScript error ${h.n} times today, unusual for a ${weekdayOf(today)} (seen in the 28 days before, but its ${weekdayOf(today)} median is 0): ${what}`
          : `JavaScript error ${h.n} times today, a whole ${weekdayOf(today)} usually has ${round(h.u)}: ${what}`);
    }
    if (hits.length > Math.max(1, R.errors.max | 0)) notes.push(`errors: ${hits.length - Math.max(1, R.errors.max | 0)} more errors over their thresholds, not listed`);
  }

  // (d) Writes: the collector's own record.
  let h = null;
  if (R.writes) {
    h = health ?? null;
    if (!h) {
      try {
        h = await readHealth(store, now.getTime());
      } catch {
        h = null;
      }
    }
    if (!h) notes.push('writes, deletions: no health record (this store keeps none, or the collector has not written one yet)');
    else {
      evaluated.add('writes');
      const stale = R.writes.staleMinutes * 60_000;
      const lastReport = Date.parse(h.lastReport ?? '');
      const lastWrite = Date.parse(h.lastWrite ?? '');
      if (num(h.writeErrors) > 0) {
        fail('writes', 'writes', 'critical', `${h.writeErrors} write${h.writeErrors > 1 ? 's' : ''} failed since the last success (${typeof h.lastError === 'string' ? h.lastError.slice(0, 60) : 'unknown error'}). Visitors still get 204.`);
      } else if (Number.isFinite(lastReport) && (!Number.isFinite(lastWrite) || lastReport - lastWrite > stale)) {
        fail('writes', 'writes', 'critical', `Reports arrive but nothing was written for over ${R.writes.staleMinutes} minutes.`);
      } else if (Number.isFinite(lastWrite) && now.getTime() - lastWrite > stale) {
        // No write for a while, whatever the record says about reports (a
        // failing store cannot store its own failure; a serverless collector
        // is gone): compare with the visits those hours usually bring.
        const n = Math.min(48, Math.max(1, Math.ceil((now.getTime() - lastWrite) / 3600_000)));
        const min = R.silence?.minExpected ?? DEFAULT_RULES.silence.minExpected;
        if (readable && hourly) {
          const usual = median(await Promise.all(weeks.map((d) => windowSum(d, hour, n))));
          if (usual >= min) {
            fail('writes', 'writes', 'critical', `No write stored since ${new Date(lastWrite).toISOString().slice(0, 16).replace('T', ' ')} UTC (${n} h); the same hours usually bring ${round(usual)} visits. The collector or its database may be down.`);
          }
        } else notes.push('writes: the last write is old, but without hourly counts there is no baseline to compare it with');
      }
    }
    // Deletion requests the collector had to drop (rate limit, store error).
    if (h && R.deletions) {
      evaluated.add('deletions');
      const last = Date.parse(h.lastDelDrop ?? '');
      if (Number.isFinite(last) && now.getTime() - last <= R.deletions.withinHours * 3600_000) {
        fail('deletions', 'deletions', 'warning', `Visitors' deletion requests were dropped (${num(h.delDropped) || 'some'}; the last at ${new Date(last).toISOString().slice(0, 16).replace('T', ' ')} UTC). Their rows are still stored: check the collector's limit (deletionsPerAddress) and the store.`);
      }
    }
  }

  // A deploy in the last 24 hours (collector.mjs markDeploy): every alert says so.
  if (readable && failing.size) {
    const recent = [];
    for (const d of [today, addDays(today, -1)]) {
      const list = (await visitsDoc(d).catch(() => null))?.deploys;
      if (Array.isArray(list)) for (const x of list) if (/^[0-9a-f]{7}$/.test(String(x?.sha)) && Date.parse(x.at) <= now.getTime() && now.getTime() - Date.parse(x.at) <= 86_400_000) recent.push(x);
    }
    const last = recent.sort((a, b) => Date.parse(a.at) - Date.parse(b.at)).pop();
    if (last) {
      // In the owner's time zone, as the alerts' days are.
      const t = new Date(Date.parse(last.at));
      const at = `${dayOf(t, timeZone)} ${new Intl.DateTimeFormat('en-GB', { timeZone, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(t)}`;
      const after = ` (after deploy ${last.sha} at ${at} ${timeZone})`;
      for (const a of failing.values()) a.text += after;
    }
  }

  // Once a day per rule, and a "recovered" line when it clears.
  const alerts = [];
  const recovered = [];
  const next = { active: {} };
  for (const [key, a] of failing) {
    const was = prior.active[key];
    next.active[key] = { since: was?.since ?? now.toISOString(), sent: today };
    if (!was) alerts.push(a);
    else if (was.sent !== today) alerts.push({ ...a, text: `Still: ${a.text}` });
    else next.active[key].sent = was.sent;
  }
  for (const [key, was] of Object.entries(prior.active)) {
    if (failing.has(key)) continue;
    const rule = key.split(':')[0];
    if (evaluated.has(rule)) recovered.push({ rule: key, text: `Recovered: ${labelOf(key)} (alerting since ${was.since?.slice(0, 16).replace('T', ' ')} UTC).` });
    else next.active[key] = was; // not checked this time: neither failing nor recovered
  }
  return { alerts, recovered, state: next, notes, quiet: false };
}

function labelOf(key) {
  const [rule, name] = key.split(/:(.*)/s);
  return { deletions: 'no deletion requests dropped recently', store: 'the store is readable', silence: 'visits are stored again', low: 'visits are back to usual', high: 'visits are back to usual', writes: 'writes succeed', notFound: '404s are back to usual', brokenLinks: 'no new broken links' }[rule] ?? (rule === 'goal' ? `goal "${name}" is being reached again` : rule === 'forms' ? `form "${name}" submits are confirmed again` : rule === 'errors' ? `JavaScript error ${name} is under its thresholds` : rule);
}

const ICON = { critical: '🔴', warning: '🟠', info: '🔵' };

/**
 * The alerts as one message. format 'slack' (mrkdwn, everything escaped) or
 * 'text' (e-mail). `site` names the site in the first line.
 */
export function alertText({ alerts = [], recovered = [] }, { site = 'site', format = 'slack' } = {}) {
  const e = format === 'slack' ? esc : String;
  const lines = [`${format === 'slack' ? '*' : ''}${e(`Analytics health · ${site}`)}${format === 'slack' ? '*' : ''}`];
  for (const a of alerts) lines.push(`${ICON[a.severity] ?? '🟠'} ${e(a.text)}`);
  for (const r of recovered) lines.push(`🟢 ${e(r.text)}`);
  return lines.join('\n');
}

/**
 * Posts the alerts to the ops channel: a bot token and `channel`
 * (SLACK_OPS_CHANNEL), or an incoming `webhook` of their own. Never the
 * visits channel: pass `visitsChannel` (and `visitsWebhook`) and a mix-up throws. Returns the
 * message ts (bot) or null; posts nothing when there is nothing to say.
 */
export async function postAlerts({ alerts = [], recovered = [], token, channel, webhook, visitsChannel, visitsWebhook, site, fetch = globalThis.fetch }) {
  if (!alerts.length && !recovered.length) return null;
  if (visitsChannel && channel && channel === visitsChannel) throw new Error('postAlerts: alerts go to the ops channel, not the visits channel');
  if (visitsWebhook && webhook && String(webhook).trim() === String(visitsWebhook).trim()) throw new Error('postAlerts: alerts go to the ops webhook, not the visits one');
  const text = alertText({ alerts, recovered }, { site, format: 'slack' });
  if (webhook) {
    await postToWebhook(webhook, text, { fetch });
    return null;
  }
  if (!token || !channel) throw new Error('postAlerts: needs a bot token and channel (SLACK_OPS_CHANNEL), or a webhook');
  return postToSlack({ token, channel, text, fetch });
}

/**
 * Totals and the last write from Cloudflare Workers Analytics Engine, over
 * its SQL API (POST the SQL text to /accounts/<id>/analytics_engine/sql with
 * an API token that can read Account Analytics; JSON answer { meta, data, rows }).
 * Use it as the `store` of checkHealth. Tested against a stand-in fetch only.
 * The last write is the newest data point, rounded to the minute; failed
 * writes are only in the Worker's own collect.health().
 */
export function analyticsEngineReader({ accountId, apiToken, dataset, fetch = globalThis.fetch }) {
  if (!/^[A-Za-z0-9_]+$/.test(String(dataset))) throw new Error('analyticsEngineReader: dataset must be a plain name');
  if (!/^[0-9a-f]{32}$/i.test(String(accountId))) throw new Error('analyticsEngineReader: accountId must be the 32-character account id');
  async function sql(text) {
    const res = await fetch(`https://api.cloudflare.com/client/v4/accounts/${accountId}/analytics_engine/sql`, {
      method: 'POST',
      headers: { authorization: `Bearer ${apiToken}` },
      body: text,
    });
    if (!res.ok) throw Object.assign(new Error(`Analytics Engine SQL API: ${res.status}`), { name: 'AnalyticsEngineError', code: res.status });
    return (await res.json()).data ?? [];
  }
  return {
    async totals(day) {
      if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) throw new Error('a day must be YYYY-MM-DD');
      // Counter points have three blobs; rows (blob4 = their data) are left out.
      const data = await sql(`SELECT blob2 AS path, blob3 AS key, SUM(_sample_interval * double1) AS n FROM ${dataset} WHERE blob1 = '${day}' AND blob4 = '' GROUP BY path, key`);
      const out = {};
      for (const r of data) {
        const id = `${day} ${r.path}`;
        const doc = (out[id] ??= { _id: id, day, path: r.path });
        let x = doc;
        const parts = String(r.key).split('.');
        if (parts.some((k) => k === '__proto__' || k === 'constructor' || k === 'prototype')) continue;
        for (const k of parts.slice(0, -1)) x = Object.hasOwn(x, k) && typeof x[k] === 'object' ? x[k] : (x[k] = {});
        x[parts[parts.length - 1]] = Number(r.n);
      }
      return out;
    },
    async health() {
      const [r] = await sql(`SELECT max(timestamp) AS last FROM ${dataset}`);
      const t = r?.last ? Date.parse(String(r.last).replace(' ', 'T') + (/[zZ]|[+-]\d\d:?\d\d$/.test(String(r.last)) ? '' : 'Z')) : NaN;
      if (!Number.isFinite(t)) return null;
      return { lastWrite: new Date(Math.floor(t / 60_000) * 60_000).toISOString(), writeErrors: 0, lastError: null };
    },
  };
}
