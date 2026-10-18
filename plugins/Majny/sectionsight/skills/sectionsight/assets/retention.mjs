/**
 * Retention that is actually enforced: old totals and rows deleted from
 * stores without a TTL, the oldest day still kept (so the owner can see the
 * privacy text's promise holds), and the bot's own Slack visit lines deleted
 * when their period ends. Reference implementation from the
 * sectionsight skill (MIT). Run it once a day.
 *
 *   import { enforceRetention, retentionStatus, deleteOldSlackLines } from './retention.mjs';
 *   await enforceRetention({ store, totalsDays: 730, rowsDays: 180 });
 *   const { state } = await deleteOldSlackLines({ state: visitsState, slackDays: 30, token });
 *
 * See references/collector.md ("Retention") and references/notifications.md.
 */

import { dayOf } from './collector.mjs';

const MS_DAY = 86_400_000;
/**
 * The first day kept: today in the collector's time zone, minus `days`. The
 * totals and rows are dated in that zone, so the cutoff must be too (a UTC
 * cutoff keeps one day too many east of UTC after midnight, and deletes one
 * too early west of it).
 */
export function cutoffDay(now, days, timeZone = 'UTC') {
  return new Date(Date.parse(`${dayOf(now, timeZone)}T00:00:00Z`) - days * MS_DAY).toISOString().slice(0, 10);
}

/**
 * Deletes totals older than `totalsDays`, rows older than `rowsDays` and
 * Search Console documents older than `gscDays` (by their day). Works for every store with deleteBefore: memory, files
 * (its purge), SQL (sqlStore) and Mongo (on top of its TTL indexes, for a
 * shorter period or a missing index). Analytics Engine cannot delete: it
 * keeps 3 months whatever is asked, and the result says so.
 *
 * `timeZone` is the collector's (default 'UTC', as the collector's).
 *
 * Returns { totals, rows, totalsBefore, rowsBefore } or { unsupported }.
 */
export async function enforceRetention({ store, totalsDays = 730, rowsDays = 180, gscDays = 490, now = new Date(), timeZone = 'UTC' }) {
  if (!(totalsDays > 0) || !(rowsDays > 0) || !(gscDays > 0)) throw new Error('enforceRetention: totalsDays, rowsDays and gscDays must be positive numbers of days');
  if (typeof store?.deleteBefore !== 'function') {
    return { unsupported: 'this store cannot delete by age (Analytics Engine keeps data 3 months, then drops it on its own)' };
  }
  const totalsBefore = cutoffDay(now, totalsDays, timeZone);
  const rowsBefore = cutoffDay(now, rowsDays, timeZone);
  // Search Console documents (gsc.mjs): 16 months by default, as Search Console keeps them.
  const removed = await store.deleteBefore({ totalsBefore, rowsBefore, gscBefore: cutoffDay(now, gscDays, timeZone) });
  return { totals: removed?.totals ?? 0, rows: removed?.rows ?? 0, totalsBefore, rowsBefore };
}

/**
 * The oldest day each kind of data still has, and whether that keeps the
 * promised periods: { oldestTotalsDay, oldestRowDay, totalsOk, rowsOk }.
 * `ok` is null when the period was not given or nothing is stored.
 */
export async function retentionStatus(store, { totalsDays, rowsDays, now = new Date(), timeZone = 'UTC' } = {}) {
  if (typeof store?.oldest !== 'function') return { unsupported: 'this store cannot report its oldest day' };
  const { totalsDay, rowsDay } = await store.oldest();
  const ok = (day, days) => (day && days ? day >= cutoffDay(now, days, timeZone) : null);
  return { oldestTotalsDay: totalsDay ?? null, oldestRowDay: rowsDay ?? null, totalsOk: ok(totalsDay, totalsDays), rowsOk: ok(rowsDay, rowsDays) };
}

/**
 * Deletes the bot's own messages older than `slackDays` (chat.delete; the
 * chat:write scope covers a bot's own messages) and drops them from the
 * state. It uses only the { channel, ts, at } entries visits.mjs keeps in
 * `state.posted` (rememberPosted): it never reads the channel's history.
 *
 * - A message already gone (message_not_found, channel_not_found) is dropped
 *   from the state.
 * - An entry without a date (`at`) counts as old enough and is deleted.
 * - Rate limited (HTTP 429, or an answer with error "ratelimited"): waits Retry-After seconds and tries again, up to
 *   `maxRetries` times, then stops and keeps the rest for the next run.
 * - A token problem (invalid_auth, not_authed, token_revoked, account_inactive,
 *   missing_scope) stops the run; nothing is dropped.
 * - Anything else (cant_delete_message…) keeps the entry and is counted in `failed`.
 *
 * Save the returned state. Returns { state, deleted, failed, stopped }.
 */
export async function deleteOldSlackLines({ state, slackDays = 30, token, now = new Date(), fetch = globalThis.fetch, sleep = (ms) => new Promise((r) => setTimeout(r, ms)), maxRetries = 3, max = 500 }) {
  if (!token) throw new Error('deleteOldSlackLines: a bot token is required');
  const before = now.getTime() - slackDays * MS_DAY;
  const posted = Array.isArray(state?.posted) ? state.posted : [];
  const keep = [];
  let deleted = 0;
  let failed = 0;
  let stopped = '';
  let done = 0;
  for (const p of posted) {
    // An entry without a usable date (an older runner) counts as old enough:
    // deleting a line early is the safe side of a retention promise.
    const at = Date.parse(p?.at);
    const old = !Number.isFinite(at) || at < before;
    if (stopped || !old || done >= max || typeof p.channel !== 'string' || !/^\d+\.\d+$/.test(String(p.ts))) {
      if (p && typeof p === 'object') keep.push(p);
      continue;
    }
    done++;
    let outcome = 'failed';
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      const res = await fetch('https://slack.com/api/chat.delete', {
        method: 'POST',
        headers: { 'content-type': 'application/json; charset=utf-8', authorization: `Bearer ${token}` },
        body: JSON.stringify({ channel: p.channel, ts: String(p.ts) }),
      });
      const body = res.status === 429 ? null : await res.json().catch(() => ({}));
      // Rate limited: HTTP 429, or (some proxies, older API paths) 200 with error "ratelimited".
      if (res.status === 429 || body?.error === 'ratelimited') {
        if (attempt === maxRetries) {
          outcome = 'ratelimited';
          break;
        }
        await sleep(Math.max(1, Number(res.headers.get('retry-after')) || 1) * 1000);
        continue;
      }
      if (body.ok || body.error === 'message_not_found' || body.error === 'channel_not_found') outcome = 'gone';
      else if (['invalid_auth', 'not_authed', 'token_revoked', 'token_expired', 'account_inactive', 'missing_scope'].includes(body.error)) outcome = `stop:${body.error}`;
      break;
    }
    if (outcome === 'gone') deleted++;
    else {
      keep.push(p);
      if (outcome === 'ratelimited') stopped = 'ratelimited';
      else if (outcome.startsWith('stop:')) stopped = outcome.slice(5);
      else failed++;
    }
  }
  return { state: { ...state, posted: keep }, deleted, failed, stopped: stopped || null };
}
