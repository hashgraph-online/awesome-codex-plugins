/**
 * Visits from the collector's rows, as one line each for Slack (or a few
 * lines of plain text for e-mail), plus the bookkeeping that posts each
 * visit once, after it has gone quiet. Reference implementation from the
 * sectionsight skill (MIT). Pure functions, except the two
 * posting helpers at the end.
 *
 * A line says where a visit came from and what it did, never who it was:
 * no IP, city, e-mail, phone, id or URL with a token. The rows are already
 * clean (collector.mjs); this file adds no identifier.
 *
 *   🇨🇿 · mobile · google · / 0:42 ↓75% (pricing 0:20 · faq 0:09) → /signup 1:10 → 🎯 signup · ▶ replay
 */

/** A new visit after this long without a report from the same visitor. */
export const VISIT_GAP_MS = 30 * 60_000;

function num(v) {
  return typeof v === 'number' && Number.isFinite(v) ? v : 0;
}
function ms(at) {
  return new Date(at).getTime();
}
export function mmss(seconds) {
  const s = Math.max(0, Math.round(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}
/** Slack mrkdwn escaping: everything a visitor's browser sent goes through it. */
export function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}
export function flag(cc) {
  if (!cc || !/^[a-z]{2}$/.test(cc) || cc === 'xx') return '🏳️';
  return String.fromCodePoint(...[...cc.toUpperCase()].map((c) => 0x1f1a5 + c.charCodeAt(0)));
}

/**
 * Groups rows into visits: per visit id, split after VISIT_GAP_MS without a
 * report. The reports of a page view already in a visit always join it (a
 * tab left open reports its time when it is finally hidden). In 'consent'
 * mode the id is the browser's visit id; in 'always' mode it is the
 * collector's daily visitor hash. Each visit:
 *   key     visit id + start time, stable across polls
 *   views   one per page view, in order: { path, active, depth, secs: {section: s}, after: [labels] }
 *   active  active seconds in all, ctas: link kinds clicked, goals: goals reached
 *   open    its last page view has sent no time report since its last event
 *           (the page may still be on screen)
 */
export function toVisits(rows, { gapMs = VISIT_GAP_MS } = {}) {
  const byId = new Map();
  for (const r of rows) {
    if (!r || typeof r.visit !== 'string') continue;
    const list = byId.get(r.visit) ?? [];
    list.push(r);
    byId.set(r.visit, list);
  }
  const visits = [];
  for (const list of byId.values()) {
    list.sort((a, b) => ms(a.at) - ms(b.at));
    const groups = [];
    const groupOfView = new Map();
    let cur = null;
    let lastAt = 0;
    for (const r of list) {
      const known = groupOfView.get(r.view);
      if (known) {
        known.push(r);
        // A late report joins its visit but does not keep the visit open: a
        // page opened right after it starts a new visit.
        if (known === cur && ms(r.at) - lastAt <= gapMs) lastAt = ms(r.at);
      } else {
        if (!cur || ms(r.at) - lastAt > gapMs) groups.push((cur = []));
        cur.push(r);
        groupOfView.set(r.view, cur);
        lastAt = ms(r.at);
      }
    }
    for (const g of groups) visits.push(build(g));
  }
  return visits.sort((a, b) => a.first - b.first);
}

const CTA_LABEL = { email: '✉️ e-mail', phone: '📞 phone', download: '⬇️ download' };

function build(rows) {
  const views = [];
  const byView = new Map();
  const ctas = [];
  const goals = [];
  let active = 0;
  let copies = 0;
  let prints = 0;
  for (const r of rows) {
    let v = byView.get(r.view);
    if (!v) {
      v = { view: r.view, path: r.path, active: 0, depth: 0, secs: {}, after: [], lastAt: 0, timedAt: 0 };
      byView.set(r.view, v);
      views.push(v);
    }
    v.lastAt = ms(r.at);
    const d = r.d ?? {};
    if (r.e === 'time') {
      v.timedAt = ms(r.at);
      v.active += num(d.sec);
      active += num(d.sec);
      for (const x of Array.isArray(d.dn) ? d.dn : []) v.depth = Math.max(v.depth, num(x));
      for (const pair of Array.isArray(d.secs) ? d.secs : []) {
        if (Array.isArray(pair) && typeof pair[0] === 'string') v.secs[pair[0]] = (v.secs[pair[0]] ?? 0) + num(pair[1]);
      }
    } else if (r.e === 'cta' && typeof d.k === 'string') {
      ctas.push(d.k);
      if (d.k === 'outbound' && typeof d.url === 'string') v.after.push(`↗️ ${d.url.split('/')[0]}`);
      else if (CTA_LABEL[d.k]) v.after.push(CTA_LABEL[d.k]);
      else if (d.k !== 'nav') v.after.push(`👉 ${d.k}`);
    } else if (r.e === 'goal' && typeof d.k === 'string') {
      goals.push(d.k);
      v.after.push(`🎯 ${d.k}`);
    } else if (r.e === 'copy') {
      copies++;
      if (d.kind === 'email') v.after.push('📋 copied the e-mail');
    } else if (r.e === 'print') {
      prints++;
      v.after.push('🖨️ printed');
    } else if (r.e === 'nf') {
      // A 404; from a link on the site itself, a broken link.
      v.after.push(d.r === 'internal' ? '🚫 404 (broken link)' : '🚫 404');
    }
  }
  const entry = rows.find((r) => r.entry)?.entry;
  const replay = rows.find((r) => typeof r.replay === 'string')?.replay;
  const last = views[views.length - 1];
  return {
    key: `${rows[0].visit}@${ms(rows[0].at)}`,
    visit: rows[0].visit,
    day: rows[0].day,
    first: ms(rows[0].at),
    last: ms(rows[rows.length - 1].at),
    entry,
    replay,
    views,
    active,
    ctas,
    goals,
    copies,
    prints,
    open: !!last && last.timedAt < last.lastAt,
  };
}

/** The default "worth a look": 10 s active, two pages, or anything clicked, reached, copied or printed. */
export function isNotable(v, { notableSeconds = 10 } = {}) {
  return (
    v.active >= notableSeconds ||
    v.views.length >= 2 ||
    v.goals.length > 0 ||
    v.ctas.some((k) => k !== 'nav') ||
    v.copies > 0 ||
    v.prints > 0
  );
}

function topSections(v, max = 3) {
  return Object.entries(v.secs)
    .filter(([, s]) => s >= 3)
    .sort((a, b) => b[1] - a[1])
    .slice(0, max);
}

/**
 * One Slack line (mrkdwn). `replayUrl` is the recording link's prefix, e.g.
 * 'https://eu.posthog.com/project/<id>/replay/'; a visit that carries a
 * recording id ends in a ▶ replay link.
 */
export function visitLine(v, { replayUrl } = {}) {
  const head = [
    flag(v.entry?.country),
    esc(v.entry?.device ?? '?'),
    // No entry row: a reload, a tab opened from the site, or consent given mid-page.
    v.entry?.source ? esc(v.entry.source) : 'continued visit',
  ].join(' · ');
  const pages = v.views
    .map((p) => {
      const depth = p.depth ? ` ↓${p.depth}%` : '';
      const secs = topSections(p);
      const inner = secs.length ? ` (${secs.map(([k, s]) => `${esc(k)} ${mmss(s)}`).join(' · ')})` : '';
      const after = p.after.length ? ` → ${[...new Set(p.after)].map(esc).join(' → ')}` : '';
      return `${esc(p.path)} ${mmss(p.active)}${depth}${inner}${after}`;
    })
    .join(' → ');
  const replay = replayUrl && v.replay && /^[A-Za-z0-9-]{8,64}$/.test(v.replay) ? ` · <${replayUrl}${v.replay}|▶ replay>` : '';
  return `${v.goals.length ? '🎯 ' : ''}${head} · ${pages}${replay}`;
}

/** The same visit as plain text, for an e-mail or a log: a headline and one block per page. */
export function visitText(v, { timeZone = 'UTC' } = {}) {
  const when = new Intl.DateTimeFormat('en-GB', { timeZone, weekday: 'short', day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }).format(new Date(v.first));
  const lines = [
    `${mmss(v.active)} on the site · ${v.views.length} ${v.views.length === 1 ? 'page' : 'pages'}`,
    `When: ${when} · From: ${v.entry?.source ?? 'continued visit'} · Where: ${(v.entry?.country ?? 'xx').toUpperCase()} · Device: ${v.entry?.device ?? '?'}`,
  ];
  v.views.forEach((p, i) => {
    lines.push(`${i + 1}. ${p.path}  ${mmss(p.active)}${p.depth ? `, scrolled ${p.depth}%` : ''}`);
    for (const [k, s] of topSections(p, 6)) lines.push(`     ${k} ${mmss(s)}`);
    for (const a of new Set(p.after)) lines.push(`     → ${a}`);
  });
  return lines.join('\n');
}

/**
 * What one poll posts. Evaluates each visit once, `settleMs` after it went
 * quiet (plus `openWaitMs` while its last page may still be on screen), so a
 * line carries the whole visit. At most `dayCap` lines a day; a visit that
 * reached a goal still gets one, up to `hardCap`. `state` remembers which
 * visits and page views were evaluated in the last `keepDays` days (a visit
 * that crosses midnight is read again the next day, partly, and must not be
 * posted twice) and each day's counts: save it BEFORE posting the lines, so
 * a failed save posts nothing rather than posting twice. A runner may keep
 * its own fields in `state.days[day]` (e.g. the Slack ts of the day's parent).
 * `state.posted` carries over the messages recorded with rememberPosted.
 *
 * Returns { state, lines: [{ day, line, text, visit }] }.
 */
export function planVisits(rows, prior, now, opts = {}) {
  const { settleMs = 30 * 60_000, openWaitMs = 25 * 60_000, dayCap = 25, hardCap = 100, keepDays = 3, replayUrl, timeZone = 'UTC', notable = isNotable } = opts;
  const t = now.getTime();
  const oldest = new Date(t - keepDays * 86_400_000).toISOString().slice(0, 10);
  const state = {
    seen: Object.fromEntries(Object.entries(prior?.seen ?? {}).filter(([, day]) => day >= oldest)),
    views: Object.fromEntries(Object.entries(prior?.views ?? {}).filter(([, day]) => day >= oldest)),
    days: Object.fromEntries(Object.entries(prior?.days ?? {}).filter(([day]) => day >= oldest).map(([day, c]) => [day, { ...c }])),
    // Every message posted, { channel, ts, at }, until deleteOldSlackLines
    // (retention.mjs) deletes it: kept past keepDays on purpose.
    posted: Array.isArray(prior?.posted) ? prior.posted.map((p) => ({ ...p })) : [],
  };
  const lines = [];
  for (const v of toVisits(rows)) {
    if (state.seen[v.key]) continue;
    // The tail of a visit already evaluated (read again after midnight with
    // its first rows out of the window): never a second line.
    if (v.views.some((p) => state.views[p.view])) {
      state.seen[v.key] = v.day;
      for (const p of v.views) state.views[p.view] ??= v.day;
      continue;
    }
    if (t - v.last < settleMs + (v.open ? openWaitMs : 0)) continue;
    state.seen[v.key] = v.day;
    for (const p of v.views) state.views[p.view] = v.day;
    if (!notable(v)) continue;
    const count = (state.days[v.day] ??= { lines: 0, skipped: 0 });
    if (count.lines >= hardCap || (count.lines >= dayCap && !v.goals.length)) {
      count.skipped += 1;
      continue;
    }
    count.lines += 1;
    lines.push({ day: v.day, line: visitLine(v, { replayUrl }), text: visitText(v, { timeZone }), visit: v.key });
  }
  return { state, lines };
}

/**
 * Records a posted message ({ channel, ts }, the ts postToSlack returns), so
 * deleteOldSlackLines (retention.mjs) can delete it when the retention ends.
 * Record the day's parent messages too. Save the state again after posting.
 */
export function rememberPosted(state, { channel, ts, at = new Date() }) {
  if (typeof channel !== 'string' || !/^\d+\.\d+$/.test(String(ts))) return state;
  (state.posted ??= []).push({ channel, ts: String(ts), at: new Date(at).toISOString() });
  return state;
}

// --- Posting -------------------------------------------------------------------

/**
 * Posts with a bot token (chat.postMessage). Returns the message ts, which a
 * caller can keep to post a day's visits as replies in one thread.
 * Needs the chat:write scope, and the bot invited to the channel.
 */
export async function postToSlack({ token, channel, text, threadTs, fetch = globalThis.fetch }) {
  const res = await fetch('https://slack.com/api/chat.postMessage', {
    method: 'POST',
    headers: { 'content-type': 'application/json; charset=utf-8', authorization: `Bearer ${token}` },
    body: JSON.stringify({ channel, text, unfurl_links: false, unfurl_media: false, ...(threadTs ? { thread_ts: threadTs } : {}) }),
  });
  const body = await res.json().catch(() => ({}));
  if (!body.ok) throw new Error(`Slack chat.postMessage: ${body.error ?? res.status}`);
  return body.ts;
}

/** Posts through an incoming webhook (no threads, no ts). */
export async function postToWebhook(url, text, { fetch = globalThis.fetch } = {}) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ text, unfurl_links: false, unfurl_media: false }),
  });
  if (!res.ok) throw new Error(`Slack webhook: ${res.status}`);
}
