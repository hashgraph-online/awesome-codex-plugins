/**
 * A visitor's own data: export or delete the rows of one visit id, for a
 * request that reaches the owner (an e-mail with the id that consent.js or a
 * support page showed) or for the collector's { "del": … } requests.
 * Reference implementation from the sectionsight skill (MIT).
 *
 *   import { exportVisit, deleteVisit } from './dsar.mjs';
 *   const { rows, replays } = await exportVisit(store, '0123456789abcdef');
 *   await deleteVisit(store, '0123456789abcdef');
 *
 * Only rows carry a visit id. The totals are counters with no id in them and
 * stay as they are. A visitor rarely knows their id: k.js keeps it in memory
 * (one page load) or in the tab (data-visit-store="session"), and earlier
 * visits used other random ids nothing remembers. Those cannot be found, and
 * expire with the rows' retention. Model C's visitor id is a daily hash that
 * only the collector can compute again, from the same address and browser,
 * on the same day. Say this in the privacy text (references/privacy-policy.md).
 */

const VISIT = /^[0-9a-f]{16}$/;

function check(store, visit, method) {
  if (!VISIT.test(String(visit))) throw new Error('a visit id must be 16 hex characters');
  if (typeof store?.[method] !== 'function') return false;
  return true;
}

/**
 * Every row of the visit, oldest first, and the PostHog recording ids those
 * rows name (for deletePostHogRecordings). { rows, replays } or { unsupported }
 * (Analytics Engine cannot be read back per visit here).
 */
export async function exportVisit(store, visit) {
  if (!check(store, visit, 'visitRows')) return { unsupported: 'this store cannot read rows by visit (Analytics Engine: query the SQL API for index1 = the visit id)' };
  const rows = await store.visitRows(visit);
  const replays = [...new Set(rows.map((r) => r.replay).filter((x) => typeof x === 'string' && x))];
  return { rows, replays };
}

/**
 * Deletes every row of the visit. { deleted } or { unsupported } (Analytics
 * Engine cannot delete; its data goes after 3 months).
 */
export async function deleteVisit(store, visit) {
  if (!check(store, visit, 'deleteVisit')) return { unsupported: 'this store cannot delete rows (Analytics Engine keeps them 3 months)' };
  return { deleted: await store.deleteVisit(visit) };
}

/**
 * OPTIONAL, AND CHECK IT FIRST: deletes PostHog session recordings by id.
 *
 * It needs a PostHog *personal* API key with the session_recording:write
 * scope, on the server only (never the public project token, never in the
 * browser). PostHog's own source has a delete action on its session
 * recordings API (SessionRecordingViewSet.destroy, a DELETE on one
 * recording, and a POST bulk_delete; posthog/session_recordings/
 * session_recording_api.py, checked against PostHog's source in October
 * 2026), but the
 * URL it is mounted under (/api/projects/<id>/… or /api/environments/<id>/…)
 * depends on the PostHog version and could not be confirmed from the
 * published API reference when this was written. So the
 * owner passes the exact URL template from their own instance's API docs
 * (Settings → API, or /api/schema/), with {id} for the recording id:
 *
 *   endpoint: 'https://eu.posthog.com/api/environments/12345/session_recordings/{id}/'
 *
 * Try it on one test recording before relying on it. Returns
 * { deleted: [...ids], failed: [{ id, status }] }.
 */
export async function deletePostHogRecordings({ ids, endpoint, personalApiKey, fetch = globalThis.fetch }) {
  if (typeof endpoint !== 'string' || !/^https:\/\/[^/]+\/.*\{id\}/.test(endpoint)) {
    throw new Error('deletePostHogRecordings: endpoint must be the https URL template from your PostHog API docs, with {id}');
  }
  if (!personalApiKey) throw new Error('deletePostHogRecordings: a personal API key is required (server-side only)');
  const deleted = [];
  const failed = [];
  for (const id of ids ?? []) {
    if (!/^[A-Za-z0-9-]{8,64}$/.test(String(id))) {
      failed.push({ id, status: 'invalid id' });
      continue;
    }
    const res = await fetch(endpoint.replace('{id}', encodeURIComponent(id)), { method: 'DELETE', headers: { authorization: `Bearer ${personalApiKey}` } });
    if (res.ok || res.status === 404) deleted.push(id);
    else failed.push({ id, status: res.status });
  }
  return { deleted, failed };
}
