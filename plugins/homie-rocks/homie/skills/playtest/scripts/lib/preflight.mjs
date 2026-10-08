/**
 * Can THIS process reach the site, before any browser opens? Chrome and Node do not resolve names the same way (a
 * browser may use DNS over HTTPS, its own cache or a system resolver Node's does not consult), so a public studio can
 * load in Chrome while Node's fetch cannot even find the host. That says nothing about the game: it is a network
 * preflight failure of the instrument, reported BLOCKED with the way round it (test against the local site).
 *
 *   { ok: true }
 *   { ok: false, kind: 'dns' | 'refused' | 'timeout' | 'http' | 'network', verdict: 'BLOCKED' | 'FAIL', why }
 *
 * `dns`, `timeout` and `network` are BLOCKED: nothing was measured. `refused` (nothing listens there) and `http`
 * (the site answered, and not with the play page) are FAIL: the address itself is wrong or the site is down.
 */
import { lookup as dnsLookup } from 'node:dns/promises';
import { isIP } from 'node:net';

/*
 * ONE CLASSIFICATION, ONE SENTENCE. The studio's own commands (check, perf, shoot, port check, a deploy's read-back)
 * classify the same failure in @homie-rocks/studio's lib/net.mjs. This script cannot import that file (it runs against
 * whatever version the studio has installed), so the list of codes that mean "this computer could not look the name
 * up" and the words said for it are kept the same here by hand, and a test feeds both sides the same errors and
 * fails when either drifts.
 */
export const DNS_CODES = ['ENOTFOUND', 'EAI_AGAIN', 'EAI_NODATA', 'EAI_NONAME', 'ESERVFAIL'];
export const LOCAL_INSTEAD = 'To test without this computer\'s network in the way: run the site here (`npx --no-install homie-studio dev`, as a background task) and give the command --url http://127.0.0.1:8787 (or leave --url out where the command finds the dev site itself).';
const HEAD = 'network preflight failed, before any page or game was opened';

/** Every code on an error and its causes (Node's fetch wraps the real one: TypeError → cause → code). */
export function errorCodes(error) {
  const out = [];
  for (let e = error, i = 0; e && i < 6; e = e.cause, i++) { if (e.code) out.push(String(e.code)); if (Array.isArray(e.errors)) for (const x of e.errors) if (x?.code) out.push(String(x.code)); }
  return out;
}

/** One failed request, classified from its error (no network needed: the pure half, and what a test injects). */
export function classifyNetError(error, host) {
  const codes = errorCodes(error);
  const has = (...c) => c.some((x) => codes.includes(x));
  if (has(...DNS_CODES)) {
    return { kind: 'dns', verdict: 'BLOCKED', why: `${HEAD}: this computer's Node.js could not look up ${host} (${codes.find((c) => DNS_CODES.includes(c))}). A browser on the same computer may still open ${host} (browsers can use their own DNS), so this says nothing about the site or the game: it is this computer's name lookup. Nothing was measured. ${LOCAL_INSTEAD}` };
  }
  if (has('ECONNREFUSED')) return { kind: 'refused', verdict: 'FAIL', why: `${host} does not answer (nothing is listening there): start the site (npm run dev, as a background task that outlives this command) or check the address` };
  if (error?.name === 'TimeoutError' || error?.name === 'AbortError' || has('ETIMEDOUT', 'UND_ERR_CONNECT_TIMEOUT', 'UND_ERR_HEADERS_TIMEOUT')) {
    return { kind: 'timeout', verdict: 'BLOCKED', why: `${HEAD}: no answer from ${host} in time. That is the connection from this computer to ${host}, not a result about the game. Nothing was measured. ${LOCAL_INSTEAD}` };
  }
  return { kind: 'network', verdict: 'BLOCKED', why: `${HEAD}: the request to ${host} failed (${codes[0] ?? error?.message ?? 'no reason given'}). That is the connection from this computer to ${host}, not a result about the game. Nothing was measured. ${LOCAL_INSTEAD}` };
}

/**
 * Resolve the host, then fetch `url`. `lookup` and `fetcher` are injectable (a test injects a resolver that fails).
 * An IP address or localhost skips the lookup.
 */
export async function preflight(url, { lookup = dnsLookup, fetcher = fetch, timeoutMs = 10_000 } = {}) {
  let host;
  try { host = new URL(url).hostname; } catch { return { ok: false, kind: 'http', verdict: 'FAIL', why: `${url} is not an address` }; }
  const bare = host.replace(/^\[|\]$/g, '');
  if (!isIP(bare) && bare !== 'localhost' && !bare.endsWith('.localhost')) {
    try { await lookup(bare); } catch (error) { return { ok: false, host, ...classifyNetError(error, host) }; }
  }
  try {
    const r = await fetcher(url, { signal: AbortSignal.timeout(timeoutMs) });
    if (r.ok) return { ok: true, host };
    return { ok: false, host, kind: 'http', verdict: 'FAIL', why: `${url} answered ${r.status}: start the site (npm run dev, as a background task that outlives this command) or check the address and the game id` };
  } catch (error) {
    // This computer's own address has no name to resolve and no network in between: whatever went wrong, the local
    // site is not answering, and "try the local site instead" would be no help at all.
    if (/^(localhost|.*\.localhost|127\..*|::1|0\.0\.0\.0)$/.test(bare)) return { ok: false, host, kind: 'refused', verdict: 'FAIL', why: `${url} does not answer (${errorCodes(error)[0] ?? error?.cause?.message ?? error?.message ?? 'no reason given'}): start the site (npm run dev, as a background task that outlives this command) or check the address` };
    return { ok: false, host, ...classifyNetError(error, host) };
  }
}
