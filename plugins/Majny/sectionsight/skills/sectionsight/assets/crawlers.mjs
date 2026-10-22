/**
 * AI crawlers and fetchers in the totals: which ones read the site, how often,
 * with which answers, and which pages. Server side only (k.js never sees a
 * crawler: they run no JavaScript, or are dropped as bots). Reference
 * implementation from the sectionsight skill (MIT).
 *
 *   import { countCrawler } from './crawlers.mjs';
 *   // Cloudflare Worker: after the response is made, off the response's path
 *   ctx.waitUntil(countCrawler(request, store, { status: response.status, timeZone: 'Europe/Berlin' }));
 *
 * It matches the User-Agent against a vendored snapshot of the ai.robots.txt
 * list (crawlers-list.mjs, refreshed by scripts/update-crawlers.mjs) with one
 * precompiled regex. It stores, on the day's "<day> *" totals document:
 *   crawl.<bot>.<2xx|3xx|4xx|5xx|unknown>   requests by answer class
 *   crawlp.<bot>.<path>                     requests per page (capped; then (other))
 * Never the IP address, never the user agent, never a query string; a path
 * that is private (`skip`) or looks personal counts as (other).
 *
 * A user agent is a claim: anyone can send "GPTBot". The counts say what
 * requests called themselves, not who sent them (operators publish IP ranges
 * to verify against; this file does not look at IPs). On Cloudflare, AI Crawl
 * Control already shows requests per AI crawler: prefer it there.
 * See references/ai-visibility.md.
 */
import { CRAWLERS, CRAWLERS_SNAPSHOT } from './crawlers-list.mjs';
import { dayOf, field, pagePath, toRegExps, nfKey } from './collector.mjs';

export { CRAWLERS, CRAWLERS_SNAPSHOT };

/** What each purpose class means, for the digest and the docs. */
export const PURPOSES = {
  live: 'fetched live for an answer',
  agent: 'an agent acting for a user',
  search: 'indexing for AI search',
  training: 'collecting training data',
  other: 'other or unclear',
};

/**
 * Local overrides, applied after the vendored list (it is regenerated; these
 * are not). NOT_IN_USER_AGENTS: names the list carries that must not be
 * matched in a User-Agent, each with the reason. Edit here, not in
 * crawlers-list.mjs (references/ai-visibility.md, "Local overrides").
 */
export const NOT_IN_USER_AGENTS = {
  Code: 'VS Code and other Electron apps send "Code/1.95" in ordinary browsing',
  Cursor: 'the Cursor editor sends "Cursor/0.42" in ordinary browsing',
  Operator: 'a common word: any user agent containing it would count',
  Trae: 'the Trae editor (ByteDance) sends "Trae/1.x" with Electron in ordinary browsing',
  'Google-Extended': 'a robots.txt token only; Google never sends it as a user agent',
  'Applebot-Extended': 'a robots.txt token only; Apple never sends it as a user agent',
};
/** Crawlers to add or reclassify locally: { name, operator, purpose } (empty by default). */
export const LOCAL_CRAWLERS = [];

const BY_NAME = new Map([...CRAWLERS, ...LOCAL_CRAWLERS].filter((c) => !Object.hasOwn(NOT_IN_USER_AGENTS, c.name)).map((c) => [c.name, c]));
const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\/]/g, '\\$&');
// One regex, longest names first (so "Claude-Code" wins over "Code" at the
// same place), a name only as a whole token: not inside another word
// ("NotGPTBot"), not followed by more of a name ("GPTBotX", "Code-Server").
// Case-sensitive, as the list spells them (it lists both spellings where two
// are in use): "Spider" must not match "Sogou web spider".
const UA_RE = new RegExp(`(?<![A-Za-z0-9_-])(${[...BY_NAME.keys()].sort((a, b) => b.length - a.length).map(escapeRe).join('|')})(?![A-Za-z0-9_-])`);

/**
 * The crawler a user agent names, or null: { name, key, operator, purpose,
 * live } where key is its counter name and live is true for a fetch made
 * while answering a user ("fetched live for an answer").
 */
export function crawlerOf(ua) {
  if (typeof ua !== 'string' || !ua || ua.length > 1024) return null;
  // A desktop app built on Electron (an editor, a chat app) is a person's
  // browser, never a crawler, whatever names its user agent carries.
  if (/\bElectron\/\d/.test(ua)) return null;
  const m = UA_RE.exec(ua);
  if (!m) return null;
  const c = BY_NAME.get(m[1]);
  return { name: c.name, key: field(c.name), operator: c.operator, purpose: c.purpose, live: c.purpose === 'live' };
}

/** A status code as its class. */
export function statusClass(status) {
  const n = Number(status);
  return Number.isInteger(n) && n >= 200 && n < 600 ? `${Math.floor(n / 100)}xx` : 'unknown';
}

// Distinct paths a bot may add a day, and bots a day, per process.
const CAPS = { paths: 30, bots: 200 };
let capDay = '';
let seen = new Map();
const NONE = Promise.resolve(null);
// The private-path rule, compiled once per value given (a rule that does not
// parse throws on the first crawler request, and is reported to onError).
const skipStrings = new Map();
const skipObjects = new WeakMap();
function skipOf(v) {
  if (v == null || v === '') return [];
  const cache = typeof v === 'object' ? skipObjects : skipStrings;
  let re = cache.get(v);
  if (!re) cache.set(v, (re = toRegExps(v)));
  return re;
}

/**
 * Counts one request if its user agent is a known AI crawler. Returns a
 * promise that never rejects (pass it to waitUntil, or ignore it): null for
 * any other request, without touching the store. Options:
 *   status    the response's status code (unknown when not given: Next.js middleware cannot see it)
 *   timeZone  the collector's, so the day is the same (default 'UTC')
 *   skip      the private paths (the collector's rule); they count as (other)
 *   now       default new Date()
 *   onError   (err) => void; a store failure is otherwise silent
 * `request` is a Fetch Request, or anything with `url` and `headers` (a
 * Node/Express request: headers as an object).
 */
export function countCrawler(request, store, opts = {}) {
  const h = request?.headers;
  const ua = typeof h?.get === 'function' ? h.get('user-agent') : h?.['user-agent'];
  const c = crawlerOf(ua);
  if (!c) return NONE;
  return (async () => {
    try {
      const day = dayOf(opts.now ?? new Date(), opts.timeZone ?? 'UTC');
      if (day !== capDay) {
        capDay = day;
        seen = new Map();
      }
      let paths = seen.get(c.key);
      const known = paths || seen.size < CAPS.bots;
      if (!paths && known) seen.set(c.key, (paths = new Set()));
      const bot = known ? c.key : '(other)';
      let path = null;
      try {
        path = pagePath(new URL(String(request.url ?? '/'), 'http://localhost').pathname, skipOf(opts.skip));
      } catch {}
      let p = '(other)';
      if (path && paths && (paths.has(path) || paths.size < CAPS.paths)) {
        paths.add(path);
        p = nfKey(path);
      }
      const inc = { [`crawl.${bot}.${statusClass(opts.status)}`]: 1, [`crawlp.${bot}.${p}`]: 1 };
      await store.write({ incs: [{ _id: `${day} *`, day, path: '*', inc }] });
      return { day, bot: c.name, purpose: c.purpose };
    } catch (err) {
      try {
        opts.onError?.(err);
      } catch {}
      return null;
    }
  })();
}

/**
 * A day's (or a week's, summed) crawler counts from a "<day> *" document:
 * [{ key, name, operator, purpose, total, byStatus, paths: [[path, n]…] }],
 * busiest first.
 */
export function crawlerTotals(doc) {
  const byKey = new Map([...CRAWLERS, ...LOCAL_CRAWLERS].map((c) => [field(c.name), c]));
  const out = [];
  for (const [key, st] of Object.entries(doc?.crawl ?? {})) {
    if (!st || typeof st !== 'object') continue;
    const byStatus = Object.fromEntries(Object.entries(st).map(([k, n]) => [k, Number(n) || 0]));
    const total = Object.values(byStatus).reduce((a, b) => a + b, 0);
    const c = byKey.get(key);
    const paths = Object.entries(doc?.crawlp?.[key] ?? {}).map(([p, n]) => [p.replace(/%2E/g, '.'), Number(n) || 0]).sort((a, b) => b[1] - a[1]);
    out.push({ key, name: c?.name ?? key, operator: c?.operator ?? '', purpose: c?.purpose ?? 'other', total, byStatus, paths });
  }
  return out.sort((a, b) => b.total - a.total || (a.key < b.key ? -1 : 1));
}
