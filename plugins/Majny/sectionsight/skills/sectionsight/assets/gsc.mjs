/**
 * Google Search Console, once a day, into the analytics store: the top 50
 * queries and the top 50 pages of one day, for the weekly digest's "search"
 * section. Reference implementation from the sectionsight skill
 * (MIT). Node 18+ (node:crypto), no googleapis package.
 *
 *   import { gscDaily } from './gsc.mjs';
 *   await gscDaily({ serviceAccount: process.env.GSC_SERVICE_ACCOUNT, siteUrl: 'sc-domain:example.com', store });
 *
 * Setup (the owner, once): a Google Cloud service account with a JSON key
 * (no roles needed in the project), the Search Console API enabled in that
 * project, and the service account's e-mail added as a user (Restricted is
 * enough) of the property in Search Console. The key goes into an
 * environment variable; this file never logs or returns it.
 *
 * What it stores, one document per day (`store.saveGsc(day, doc)`, kept 16
 * months like Search Console itself):
 *   { day, totals: { clicks, impressions },
 *     queries: [{ q, clicks, impressions, position }], pages: [{ p, clicks, impressions, position }],
 *     hidden: { queries, pages } }
 * Google already leaves out rare ("anonymized") queries. A query that still
 * looks personal (an e-mail, a phone number, a token) and a page that is
 * private or carries a token are dropped here and counted in `hidden`.
 * See references/ai-visibility.md.
 */
import { createSign } from 'node:crypto';
import { looksPersonal, pagePath, toRegExps, dayOf } from './collector.mjs';

export const GSC_SCOPE = 'https://www.googleapis.com/auth/webmasters.readonly';
export const TOKEN_URL = 'https://oauth2.googleapis.com/token';
const MS_DAY = 86_400_000;
/** Search Console's days are Pacific Time days. */
export const GSC_TIME_ZONE = 'America/Los_Angeles';
const addDays = (day, n) => new Date(Date.parse(`${day}T00:00:00Z`) + n * MS_DAY).toISOString().slice(0, 10);

const b64url = (buf) => Buffer.from(buf).toString('base64').replace(/=+$/, '').replace(/\+/g, '-').replace(/\//g, '_');

/** The service account as an object: a parsed key file, or its JSON text. */
export function serviceAccountOf(sa) {
  let o = sa;
  if (typeof sa === 'string') {
    try {
      o = JSON.parse(sa);
    } catch {
      throw new Error('gsc: the service account is not valid JSON (the key file\'s content)');
    }
  }
  if (!o || typeof o.client_email !== 'string' || typeof o.private_key !== 'string') throw new Error('gsc: the service account needs client_email and private_key');
  return o;
}

/**
 * A signed JWT (RS256) for Google's OAuth token endpoint: the service
 * account's e-mail as issuer, the read-only Search Console scope, an hour.
 */
export function signJwt(serviceAccount, { now = Date.now(), scope = GSC_SCOPE, aud = TOKEN_URL } = {}) {
  const sa = serviceAccountOf(serviceAccount);
  const iat = Math.floor(now / 1000);
  const head = b64url(JSON.stringify({ alg: 'RS256', typ: 'JWT' }));
  const claims = b64url(JSON.stringify({ iss: sa.client_email, scope, aud, iat, exp: iat + 3600 }));
  const signer = createSign('RSA-SHA256');
  signer.update(`${head}.${claims}`);
  return `${head}.${claims}.${b64url(signer.sign(sa.private_key))}`;
}

/** An access token for the service account (one request; tokens last an hour). */
export async function accessToken(serviceAccount, { fetch = globalThis.fetch, now = Date.now() } = {}) {
  const body = new URLSearchParams({ grant_type: 'urn:ietf:params:oauth:grant-type:jwt-bearer', assertion: signJwt(serviceAccount, { now }) });
  const res = await fetch(TOKEN_URL, { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body: body.toString() });
  const json = await res.json().catch(() => ({}));
  // Only the status and Google's error code: never the request, which holds the signed assertion.
  if (!res.ok || typeof json.access_token !== 'string') throw new Error(`gsc: token request failed (${res.status}${typeof json.error === 'string' ? ` ${json.error.slice(0, 40)}` : ''})`);
  return json.access_token;
}

/** The searchAnalytics.query body for one day and one dimension ('query', 'page', or none for the totals). */
export function gscQuery(day, dimension, rowLimit = 50) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) throw new Error('gsc: a day must be YYYY-MM-DD');
  const q = { startDate: day, endDate: day, type: 'web', rowLimit: dimension ? rowLimit : 1 };
  if (dimension) q.dimensions = [dimension];
  return q;
}

/** The API URL for a property ("https://example.com/" or "sc-domain:example.com"). */
export function queryUrl(siteUrl) {
  return `https://www.googleapis.com/webmasters/v3/sites/${encodeURIComponent(siteUrl)}/searchAnalytics/query`;
}

const n = (v) => (typeof v === 'number' && Number.isFinite(v) ? v : 0);
const clean = (s) => String(s).replace(/[\u0000-\u001f\u007f\u2028\u2029]+/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 100);

/**
 * Turns the API's rows into the stored document: queries that look personal
 * and pages that are private (`skip`) or carry a token are dropped and counted.
 */
export function gscDoc(day, { totals = [], queries = [], pages = [] }, { skip = [] } = {}) {
  const re = toRegExps(skip);
  const hidden = { queries: 0, pages: 0 };
  const stat = (r) => ({ clicks: n(r.clicks), impressions: n(r.impressions), position: Math.round(n(r.position) * 10) / 10 });
  const qs = [];
  for (const r of queries) {
    const q = clean(r?.keys?.[0] ?? '');
    if (!q || looksPersonal(q)) hidden.queries++;
    else qs.push({ q, ...stat(r) });
  }
  const ps = [];
  for (const r of pages) {
    let p = null;
    try {
      p = pagePath(new URL(String(r?.keys?.[0] ?? '')).pathname, re);
    } catch {}
    if (!p) hidden.pages++;
    else ps.push({ p, ...stat(r) });
  }
  const t = totals[0] ?? {};
  return { day, totals: { clicks: n(t.clicks), impressions: n(t.impressions) }, queries: qs, pages: ps, hidden };
}

/**
 * The daily job: pulls the day `daysBack` days ago in Pacific Time (default
 * 3: Search Console's data is final after about 2 to 3 days) and saves it.
 * The `retryDays` days before it (default 3) are fetched again when they
 * are missing or were stored with no clicks and no impressions (fetched
 * before Google had them, or a missed run), each at most 3 times in all
 * (the document's `fetches`). Options:
 *   serviceAccount  the key file's JSON (text or object) (required)
 *   siteUrl         the property, "sc-domain:example.com" or "https://www.example.com/" (required)
 *   store           a collector store with saveGsc(day, doc) (required)
 *   skip            the private paths (the collector's rule): such pages are dropped
 *   rowLimit        default 50
 *   fetch, now      injectable for tests
 * Returns { day, queries, pages, hidden, refetched } (counts, and the earlier
 * days fetched again), never the key or the token.
 */
export async function gscDaily({ serviceAccount, siteUrl, store, skip = [], daysBack = 3, retryDays = 3, rowLimit = 50, fetch = globalThis.fetch, now = new Date() } = {}) {
  if (typeof store?.saveGsc !== 'function') throw new Error('gsc: the store has no saveGsc(day, doc) (Analytics Engine keeps none: use files, Mongo or SQL)');
  if (typeof siteUrl !== 'string' || !/^(sc-domain:[a-z0-9.-]+|https?:\/\/\S+\/)$/i.test(siteUrl)) throw new Error('gsc: siteUrl must be "sc-domain:example.com" or "https://www.example.com/"');
  const day = addDays(dayOf(now, GSC_TIME_ZONE), -daysBack);
  const token = await accessToken(serviceAccount, { fetch, now: now.getTime() });
  const ask = async (day, dimension) => {
    const res = await fetch(queryUrl(siteUrl), {
      method: 'POST',
      headers: { authorization: `Bearer ${token}`, 'content-type': 'application/json' },
      body: JSON.stringify(gscQuery(day, dimension, rowLimit)),
    });
    const json = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(`gsc: searchAnalytics.query failed (${res.status}${typeof json?.error?.status === 'string' ? ` ${json.error.status.slice(0, 40)}` : ''})`);
    return Array.isArray(json.rows) ? json.rows : [];
  };
  // `fetches`: how often a day was asked for; an empty day is asked at most 3 times.
  const pull = async (d, old) => {
    const doc = gscDoc(d, { totals: await ask(d, null), queries: await ask(d, 'query'), pages: await ask(d, 'page') }, { skip });
    doc.fetches = (Number(old?.fetches) || (old ? 1 : 0)) + 1;
    await store.saveGsc(d, doc);
    return doc;
  };
  const doc = await pull(day, typeof store.gsc === 'function' ? await store.gsc(day) : null);
  const refetched = [];
  if (typeof store.gsc === 'function') {
    for (let i = 1; i <= retryDays; i++) {
      const d = addDays(day, -i);
      const old = await store.gsc(d);
      if (old && (Number(old.totals?.clicks) > 0 || Number(old.totals?.impressions) > 0)) continue;
      if (old && (Number(old.fetches) || 1) >= 3) continue;
      await pull(d, old);
      refetched.push(d);
    }
  }
  return { day, queries: doc.queries.length, pages: doc.pages.length, hidden: doc.hidden, refetched };
}
