/**
 * The weekly "what changed" digest, from the totals only (no rows, no ids):
 * one message for Slack or e-mail. Reference implementation from the
 * sectionsight skill (MIT).
 *
 *   import { weeklyDigest } from './digest.mjs';
 *   import { postToSlack } from './visits.mjs';
 *   const { text } = await weeklyDigest({ store, timeZone: 'Europe/Berlin', site: 'example.com' });
 *   await postToSlack({ token, channel: process.env.SLACK_DIGEST_CHANNEL, text });
 *
 * It compares a week (Monday to Sunday, in the collector's time zone) with
 * the week before and with the average of the 4 weeks before, always with
 * the counts beside the percentages. Small counts are rounded (see
 * roundCount): by default a count under 10 is "<10" and larger ones are
 * rounded to tens, and every percentage is computed from the rounded counts,
 * so the percentages do not undo the rounding. Sections:
 *   visits, sources (AI assistants grouped), sections whose read rate moved,
 *   goals by source, consent answers, new sources / outbound hosts / 404 paths /
 *   JavaScript errors, Core Web Vitals p75, AI crawlers, Search Console, deploys.
 * A section with nothing to say is left out. See references/notifications.md.
 */
import { esc } from './visits.mjs';
import { dayOf, p75FromBuckets, CWV_BUCKETS, AI_SOURCES, SOURCE_CLASSES } from './collector.mjs';
import { addDays } from './health.mjs';
import { crawlerTotals, PURPOSES } from './crawlers.mjs';

const num = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : 0);
const SKIP_KEYS = new Set(['_id', 'day', 'path', 'at', 'deploys']);

/** Adds the counters of `doc` into `into` (nested objects summed key by key). */
export function addCounters(into, doc) {
  for (const [k, v] of Object.entries(doc ?? {})) {
    if (SKIP_KEYS.has(k) || k === '__proto__' || k === 'constructor' || k === 'prototype') continue;
    if (typeof v === 'number' && Number.isFinite(v)) into[k] = num(into[k]) + v;
    else if (v && typeof v === 'object' && !Array.isArray(v)) addCounters((into[k] = into[k] && typeof into[k] === 'object' ? into[k] : {}), v);
  }
  return into;
}

/** The Monday (YYYY-MM-DD) of the week that holds `day`. */
export function mondayOf(day) {
  const dow = new Date(`${day}T12:00:00Z`).getUTCDay();
  return addDays(day, -((dow + 6) % 7));
}

/**
 * A count as it may be shown. mode 'tens' (default): 0 stays 0, 1–9 is
 * "<10", from 10 on it is rounded to the nearest ten. 'none': exact. CNIL's
 * self-assessment tool for audience measurement suggests rounding small
 * counts to tens; the owner may choose exact counts for their own eyes
 * (references/decisions.md).
 */
export function roundCount(n, mode = 'tens') {
  const x = Math.max(0, Math.round(num(n)));
  if (mode === 'none') return x;
  if (x === 0) return 0;
  if (x < 10) return null; // "<10"
  return Math.round(x / 10) * 10;
}
const fmt = (r) => (r === null ? '<10' : r.toLocaleString('en-US'));

/** Reads one week (7 days from `monday`): { pages: Map(path → counters), visits, deploys, days }. */
export async function weekTotals(store, monday) {
  const pages = new Map();
  const visits = {};
  const deploys = [];
  for (let i = 0; i < 7; i++) {
    const day = addDays(monday, i);
    const docs = (await store.totals(day)) ?? {};
    for (const [id, doc] of Object.entries(docs)) {
      const path = typeof doc?.path === 'string' ? doc.path : id.slice(11);
      if (path === '*') {
        addCounters(visits, doc);
        if (Array.isArray(doc.deploys)) for (const x of doc.deploys) if (x && /^[0-9a-f]{7}$/.test(String(x.sha))) deploys.push({ sha: x.sha, at: String(x.at ?? ''), note: typeof x.note === 'string' ? x.note : '' });
      } else addCounters(pages.get(path) ?? pages.set(path, {}).get(path), doc);
    }
  }
  return { monday, pages, visits, deploys, hasData: pages.size > 0 || Object.keys(visits).length > 0 };
}

const sumOf = (o) => (o && typeof o === 'object' ? Object.values(o).reduce((s, v) => s + (typeof v === 'number' ? v : sumOf(v)), 0) : 0);
/** One counter family (e.g. "out") summed over every page of a week. */
function overPages(week, family) {
  const out = {};
  for (const doc of week.pages.values()) for (const [k, v] of Object.entries(doc[family] ?? {})) out[k] = num(out[k]) + num(v);
  return out;
}
const unescapeKey = (k) => String(k).replace(/%2E/g, '.');

/**
 * Builds the digest. Options:
 *   store      a collector store with totals(day) (and errSamples(day), gsc(day) where it has them)
 *   week       any day of the week to report (default: the last complete week)
 *   now, timeZone  for the default week (the collector's time zone)
 *   site       the site's name in the first line
 *   rounding   'tens' (default) or 'none'
 *   minSample  default 30: percentages and movers only on counts at least this big
 *   format     'slack' (mrkdwn, everything escaped) or 'text'
 *   top        how many entries a list shows (default 5)
 *   showErrorText  default false: a new error is named by fingerprint, file and line;
 *              true adds its scrubbed message (it can still quote a name)
 *   gscQueries default true: list Search Console's top movers; false shows its totals only
 * Returns { text, from, to, data } (data: the numbers behind the text, for tests and other formats).
 */
export async function weeklyDigest({ store, week, now = new Date(), timeZone = 'UTC', site = 'site', rounding = 'tens', minSample = 30, format = 'slack', top = 5, showErrorText = false, gscQueries = true } = {}) {
  if (typeof store?.totals !== 'function') throw new Error('weeklyDigest: the store has no totals(day) (Analytics Engine: health.mjs analyticsEngineReader)');
  const monday = mondayOf(week ?? addDays(mondayOf(dayOf(now, timeZone)), -7));
  const weeks = [];
  for (let i = 0; i <= 4; i++) weeks.push(await weekTotals(store, addDays(monday, -7 * i)));
  const [cur, prev] = weeks;
  // The 4 weeks before, those with any data (a new site has fewer).
  const before = weeks.slice(1).filter((w) => w.hasData);
  const e = format === 'slack' ? esc : String;
  const b = (s) => (format === 'slack' ? `*${s}*` : `\n${s}`);
  const R = (x) => roundCount(x, rounding);
  const C = (x) => fmt(R(x));
  // A change from b to a, from the rounded counts, when b is big enough.
  const pct = (a, base) => {
    const ra = R(a);
    const rb = R(base);
    if (ra === null || rb === null || rb < minSample || !rb) return '';
    const p = Math.round(((ra - rb) / rb) * 100);
    return ` (${p > 0 ? '+' : ''}${p}%)`;
  };
  const avg = (f) => before.reduce((s, w) => s + f(w), 0) / Math.max(1, before.length);
  const lines = [];
  const data = {};
  const to = addDays(monday, 6);
  const span = `${new Date(`${monday}T12:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' })} – ${new Date(`${to}T12:00:00Z`).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })}`;
  lines.push(format === 'slack' ? b(e(`Weekly · ${site} · ${span}`)) : `Weekly · ${site} · ${span}`);
  const vs = (f) => {
    const a = f(cur);
    const l = f(prev);
    const m = avg(f);
    const avgPart = before.length ? ` · ${before.length === 4 ? '4-week' : `${before.length}-week`} average ${C(m)}${pct(a, m)}` : '';
    return `${C(a)} · last week ${C(l)}${pct(a, l)}${avgPart}`;
  };

  // Visits and views.
  const views = (w) => [...w.pages.values()].reduce((s, d) => s + num(d.views), 0);
  data.visits = { cur: num(cur.visits.visits), prev: num(prev.visits.visits) };
  lines.push(`Visits ${vs((w) => num(w.visits.visits))}`);
  lines.push(`Page views ${vs(views)}`);

  // Sources, the AI assistants as one group.
  const src = (w) => w.visits.src ?? {};
  const ai = (w) => AI_SOURCES.reduce((s, k) => s + num(src(w)[k]), 0);
  const srcRows = Object.entries(src(cur)).filter(([k]) => !AI_SOURCES.includes(k)).sort((x, y) => y[1] - x[1]).slice(0, top);
  if (srcRows.length || ai(cur)) {
    const parts = srcRows.map(([k, v]) => `${e(k)} ${C(v)}${pct(v, num(src(prev)[k]))}`);
    if (ai(cur) || ai(prev)) {
      const each = AI_SOURCES.filter((k) => num(src(cur)[k])).map((k) => `${e(k)} ${C(src(cur)[k])}`);
      parts.push(`AI assistants ${C(ai(cur))}${pct(ai(cur), ai(prev))}${each.length ? ` (${each.join(', ')})` : ''}`);
    }
    lines.push(`Sources: ${parts.join(' · ')}`);
  }
  data.aiVisits = { cur: ai(cur), prev: ai(prev) };

  // Sections whose read rate moved most (pages with enough views both weeks).
  const movers = [];
  for (const [path, doc] of cur.pages) {
    const old = prev.pages.get(path);
    const vNow = R(doc.views);
    const vOld = R(old?.views);
    if (!old || vNow === null || vOld === null || vNow < minSample || vOld < minSample) continue;
    for (const s of new Set([...Object.keys(doc.sec ?? {}), ...Object.keys(old.sec ?? {})])) {
      if (s === '_') continue;
      const rNow = R(doc.sec?.[s]?.r);
      const rOld = R(old.sec?.[s]?.r);
      // Both read counts big enough too: a "<10" is never taken as 0.
      if (rNow === null || rOld === null || rNow < minSample || rOld < minSample) continue;
      const a = Math.round((rNow / vNow) * 100);
      const z = Math.round((rOld / vOld) * 100);
      if (a !== z) movers.push({ path, s, a, z, d: a - z, rNow, rOld, vNow, vOld });
    }
  }
  movers.sort((x, y) => Math.abs(y.d) - Math.abs(x.d) || (x.path + x.s < y.path + y.s ? -1 : 1));
  data.readMovers = movers.slice(0, top);
  if (movers.length) {
    lines.push(b('Read-rate changes'));
    for (const m of movers.slice(0, top)) lines.push(`${e(m.path)} · ${e(m.s)}: ${m.a}% read (${fmt(m.rNow)} of ${fmt(m.vNow)}), last week ${m.z}% (${fmt(m.rOld)} of ${fmt(m.vOld)}), ${m.d > 0 ? '+' : ''}${m.d} pts`);
  }

  // Goals, by the source class of the visit's entry.
  const goals = cur.visits.goal ?? {};
  const gnames = Object.keys({ ...goals, ...(prev.visits.goal ?? {}) }).sort();
  if (gnames.length) {
    lines.push(b('Goals'));
    for (const g of gnames) {
      const total = num(goals[g]);
      const by = cur.visits.goalsrc?.[g] ?? {};
      const known = SOURCE_CLASSES.filter((c) => num(by[c])).map((c) => `${c} ${C(by[c])}`);
      const rest = total - SOURCE_CLASSES.reduce((s, c) => s + num(by[c]), 0);
      if (rest > 0 && known.length) known.push(`entry unknown ${C(rest)}`);
      lines.push(`${e(g)} ${C(total)} · last week ${C(num(prev.visits.goal?.[g]))}${pct(total, num(prev.visits.goal?.[g]))}${known.length ? ` · ${known.join(', ')}` : ''}`);
    }
  }

  // Consent answers (only when the owner counts them).
  const cs = cur.visits.consent;
  if (cs && typeof cs === 'object') {
    const acc = num(cs.accept);
    const dec = num(cs.decline);
    const ra = R(acc);
    const rd = R(dec);
    const answered = (ra ?? 0) + (rd ?? 0);
    // No rate while either count is hidden as "<10".
    const rate = ra !== null && rd !== null && answered >= minSample ? Math.round((ra / answered) * 100) : null;
    data.consent = { accept: acc, decline: dec, shown: num(cs.shown), withdraw: num(cs.withdraw), rate };
    lines.push(b('Consent'));
    lines.push(`Banner shown on ${C(cs.shown)} page views · accepted ${C(acc)} · declined ${C(dec)} · withdrawn ${C(cs.withdraw)}${rate !== null ? ` · accept rate ${rate}% of answers` : ''}`);
    lines.push(rate !== null
      ? `Per-visit rows and visit lines cover only the people who accepted (about ${rate}% of those who answered): read them as a sample of people who said yes, not of all visitors. The totals above count everyone.`
      : 'Per-visit rows and visit lines cover only the people who accepted; too few answers this week to say what share that is.');
  }

  // New things: sources, outbound hosts, 404 paths, JavaScript errors.
  const seenBefore = (f) => new Set(before.flatMap((w) => Object.keys(f(w))));
  const fresh = (f) => {
    const old = seenBefore(f);
    return Object.entries(f(cur)).filter(([k, v]) => num(v) > 0 && !old.has(k) && k !== 'other' && k !== '(other)').sort((x, y) => y[1] - x[1] || (x[0] < y[0] ? -1 : 1));
  };
  const news = [];
  const list = (rows, label) => rows.slice(0, top).map(([k, v]) => `${e(label(k))} ${C(v)}`).join(', ') + (rows.length > top ? ` and ${rows.length - top} more` : '');
  const newSrc = fresh(src);
  if (newSrc.length) news.push(`New sources: ${list(newSrc, String)}`);
  const newOut = fresh((w) => overPages(w, 'out'));
  if (newOut.length) news.push(`New outbound hosts: ${list(newOut, String)}`);
  const newNf = fresh((w) => w.visits.nf ?? {});
  if (newNf.length) news.push(`New 404 paths: ${list(newNf, unescapeKey)}`);
  const newIn = fresh((w) => w.visits.nfin ?? {});
  if (newIn.length) news.push(`New broken links on the site (404s from its own pages): ${list(newIn, unescapeKey)}`);
  const errs = (w) => overPages(w, 'err');
  const newErr = fresh(errs);
  if (newErr.length) {
    let samples = {};
    if (typeof store.errSamples === 'function') {
      for (let i = 6; i >= 0; i--) {
        try {
          samples = { ...((await store.errSamples(addDays(monday, i))) ?? {}), ...samples };
        } catch {}
      }
    }
    // The message only with showErrorText: scrubbing cannot see a name written without quotes.
    const what = (fp) => (samples[fp] ? `${showErrorText ? String(samples[fp].m).slice(0, 100) : `error ${fp}`} · ${String(samples[fp].f).slice(0, 40)}:${num(samples[fp].l)}` : `error ${fp}`);
    news.push(`New JavaScript errors: ${newErr.slice(0, top).map(([fp, v]) => `${e(what(fp))} (${C(v)})`).join('; ')}${newErr.length > top ? ` and ${newErr.length - top} more` : ''}`);
  }
  data.fresh = { sources: newSrc.map(([k]) => k), outbound: newOut.map(([k]) => k), notFound: newNf.map(([k]) => unescapeKey(k)), brokenLinks: newIn.map(([k]) => unescapeKey(k)), errors: newErr.map(([k]) => k) };
  if (news.length) {
    lines.push(b('New this week'));
    lines.push(...news);
  }

  // Core Web Vitals: p75 per page and device, the worst first, with the slow section.
  const vit = [];
  const RANK = { poor: 2, 'needs-improvement': 1, good: 0 };
  for (const [path, doc] of cur.pages) {
    for (const [device, metrics] of Object.entries(doc.cwv ?? {})) {
      for (const m of ['lcp', 'inp', 'cls']) {
        const counts = metrics?.[m];
        const p = counts ? p75FromBuckets(counts, m) : null;
        if (!p || p.n < minSample || p.rating === 'good') continue;
        const slow = Object.entries(doc.cwvs?.[m] ?? {}).sort((x, y) => y[1] - x[1])[0];
        vit.push({ path, device, m, p, slow });
      }
    }
  }
  vit.sort((x, y) => RANK[y.p.rating] - RANK[x.p.rating] || y.p.bucket / CWV_BUCKETS[y.m].edges.length - x.p.bucket / CWV_BUCKETS[x.m].edges.length || (x.path < y.path ? -1 : 1));
  data.vitals = vit.slice(0, top).map((v) => ({ path: v.path, device: v.device, metric: v.m, rating: v.p.rating }));
  if (vit.length) {
    lines.push(b('Slow pages (Core Web Vitals, 75th percentile)'));
    const unit = (m, x) => (m === 'cls' ? String(x) : `${x / 1000} s`);
    const range = (m, p) => (p.to === Infinity ? `over ${unit(m, p.from)}` : m === 'cls' ? `${p.from}–${p.to}` : `${p.from / 1000}–${p.to / 1000} s`);
    for (const v of vit.slice(0, top)) {
      lines.push(`${e(v.path)} · ${e(v.device)} ${v.m.toUpperCase()} ${range(v.m, v.p)} (${v.p.rating}, ${C(v.p.n)} views)${v.slow ? ` · poor mostly in ${e(v.slow[0] === '_' ? 'no section' : v.slow[0])} (${C(v.slow[1])})` : ''}`);
    }
  }

  // AI crawlers (crawlers.mjs).
  const crawl = crawlerTotals(cur.visits);
  if (crawl.length) {
    const all = crawl.reduce((s, c) => s + c.total, 0);
    const live = crawl.filter((c) => c.purpose === 'live').reduce((s, c) => s + c.total, 0);
    const failed = crawl.reduce((s, c) => s + num(c.byStatus['4xx']) + num(c.byStatus['5xx']), 0);
    data.crawlers = { total: all, live, failed };
    lines.push(b('AI crawlers'));
    lines.push(`${C(all)} requests · last week ${C(crawlerTotals(prev.visits).reduce((s, c) => s + c.total, 0))} · ${PURPOSES.live}: ${C(live)} · answered 4xx/5xx: ${C(failed)}`);
    lines.push(crawl.slice(0, top).map((c) => `${e(c.name)} ${C(c.total)} (${PURPOSES[c.purpose] ?? c.purpose})${c.paths[0] ? `, most on ${e(c.paths[0][0])}` : ''}`).join(' · '));
  }

  // Google Search (gsc.mjs), where the store keeps it.
  if (typeof store.gsc === 'function') {
    const read = async (m) => {
      const q = {};
      let clicks = 0;
      let impressions = 0;
      let days = 0;
      for (let i = 0; i < 7; i++) {
        const doc = await store.gsc(addDays(m, i)).catch(() => null);
        if (!doc) continue;
        days++;
        clicks += num(doc.totals?.clicks);
        impressions += num(doc.totals?.impressions);
        for (const r of Array.isArray(doc.queries) ? doc.queries : []) if (typeof r?.q === 'string') q[r.q] = num(q[r.q]) + num(r.clicks);
      }
      return { q, clicks, impressions, days };
    };
    const g = await read(monday);
    const gp = await read(addDays(monday, -7));
    if (g.days) {
      data.gsc = { clicks: g.clicks, prevClicks: gp.clicks };
      lines.push(b(`Google Search (data for ${g.days} of 7 days so far; Search Console lags 2–3 days)`));
      lines.push(`Clicks ${C(g.clicks)} · last week ${C(gp.clicks)}${pct(g.clicks, gp.clicks)} · impressions ${C(g.impressions)}`);
      const moved = Object.keys({ ...g.q, ...gp.q }).map((k) => ({ k, a: num(g.q[k]), z: num(gp.q[k]) })).filter((x) => R(x.a) !== R(x.z)).sort((x, y) => Math.abs(y.a - y.z) - Math.abs(x.a - x.z) || (x.k < y.k ? -1 : 1));
      if (gscQueries && moved.length) lines.push(`Top movers: ${moved.slice(0, top).map((x) => `"${e(x.k)}" ${C(x.a)} (was ${C(x.z)})`).join(' · ')}`);
    }
  }

  // Deploys in the week (collector.mjs markDeploy).
  if (cur.deploys.length) {
    const when = (at) => (Number.isFinite(Date.parse(at)) ? new Intl.DateTimeFormat('en-GB', { timeZone, weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }).format(new Date(at)) : '');
    lines.push(b('Deploys'));
    lines.push(cur.deploys.sort((x, y) => (x.at < y.at ? -1 : 1)).map((d) => `${e(d.sha)} ${e(when(d.at))}${d.note ? ` (${e(d.note)})` : ''}`).join(' · '));
  }
  data.deploys = cur.deploys.map((d) => d.sha);

  if (rounding !== 'none') lines.push(format === 'slack' ? '_Counts under 10 show as <10, others are rounded to tens; percentages use the rounded counts._' : 'Counts under 10 show as <10, others are rounded to tens; percentages use the rounded counts.');
  return { text: lines.join('\n'), from: monday, to, data };
}
