/**
 * A same-origin proxy for PostHog (posthog-guard.mjs sets api_host '/ingest').
 * Reference implementation from the sectionsight skill (MIT).
 * Fetch API: Next.js route handlers (app/ingest/[...path]/route.js), Workers,
 * Deno, Bun.
 *
 * Why not a framework rewrite: a rewrite forwards every request header. The
 * visitor's cookies (a login session included) go to PostHog, and a CDN's
 * client-IP header (CF-Connecting-IP) can make PostHog's own CDN refuse the
 * request (Cloudflare error 1000), which silently breaks session replay.
 * Only the headers PostHog needs go out here.
 *
 *   const proxy = createPostHogProxy({ region: 'eu', prefix: '/ingest' });
 *   export const GET = proxy, POST = proxy;
 *
 * `clientIp(request)` says where the visitor's IP comes from; pass the same
 * function as the collector's. The default reads CF-Connecting-IP, else the
 * LAST X-Forwarded-For entry (the first is whatever the client sent), and
 * never X-Real-IP, which proxies often pass through from the client.
 * CF-Connecting-IP is trustworthy only when every request comes through
 * Cloudflare. `upstream: { api, assets }` replaces PostHog's hosts (a
 * self-hosted PostHog, or a local stand-in for staging and tests).
 * Runs on Node 18+ (AbortSignal.any is used where it exists).
 */
export function defaultClientIp(request) {
  const h = request.headers;
  const xff = h.get('x-forwarded-for');
  return h.get('cf-connecting-ip') ?? (xff ? xff.split(',').pop().trim() : '');
}

/** The request's own signal and a timeout, as one signal. */
function abortSignal(signal, timeoutMs) {
  const timeout = AbortSignal.timeout(timeoutMs);
  if (!signal) return timeout;
  if (typeof AbortSignal.any === 'function') return AbortSignal.any([signal, timeout]);
  // Node before 18.17 / 20.3: combine by hand.
  const c = new AbortController();
  const stop = (s) => () => c.abort(s.reason);
  if (signal.aborted) c.abort(signal.reason);
  else {
    signal.addEventListener('abort', stop(signal), { once: true });
    timeout.addEventListener('abort', stop(timeout), { once: true });
  }
  return c.signal;
}

export function createPostHogProxy({ region = 'eu', prefix = '/ingest', timeoutMs = 10_000, clientIp = defaultClientIp, upstream: hosts = {} } = {}) {
  const API = String(hosts.api ?? `https://${region}.i.posthog.com`).replace(/\/+$/, '');
  // Scripts (/static) and remote config (/array) come from the assets CDN.
  const ASSETS = String(hosts.assets ?? hosts.api ?? `https://${region}-assets.i.posthog.com`).replace(/\/+$/, '');
  // No Referer: on a same-origin request it is the full page URL, query included.
  const REQUEST_HEADERS = ['content-type', 'accept', 'accept-language', 'user-agent', 'origin'];
  const CONDITIONAL_HEADERS = ['if-none-match', 'if-modified-since'];
  // No content-encoding / content-length: fetch hands the body back decoded.
  const RESPONSE_HEADERS = ['content-type', 'cache-control', 'etag', 'last-modified', 'retry-after'];

  return async function proxy(request) {
    const url = new URL(request.url);
    if (!url.pathname.startsWith(prefix + '/')) return new Response(null, { status: 404 });
    const path = url.pathname.slice(prefix.length + 1).split('/');
    // PostHog's Logs product (console capture) and metrics: the project can
    // switch console capture on with no client veto. Accepted and dropped,
    // so the SDK does not retry.
    if (path[0] === 'i' && (path[2] === 'logs' || path[2] === 'metrics')) return new Response(null, { status: 204 });
    const assets = path[0] === 'static' || path[0] === 'array';
    // PostHog's endpoints end in a slash (/e/, /flags/); keep it. (Next.js:
    // set skipTrailingSlashRedirect, or the slash is redirected away.)
    const target = `${assets ? ASSETS : API}/${url.pathname.slice(prefix.length + 1)}${url.search}`;

    const read = request.method === 'GET' || request.method === 'HEAD';
    const headers = new Headers();
    for (const name of read ? [...REQUEST_HEADERS, ...CONDITIONAL_HEADERS] : REQUEST_HEADERS) {
      const v = request.headers.get(name);
      if (v) headers.set(name, v);
    }
    // The visitor's full IP, for PostHog's location lookup (turn on "Discard
    // client IP data" in the project settings so it is not stored).
    const ip = clientIp(request);
    if (ip && !assets) headers.set('x-forwarded-for', ip);

    let upstream;
    try {
      upstream = await fetch(target, {
        method: request.method,
        headers,
        body: read ? undefined : await request.arrayBuffer(),
        signal: abortSignal(request.signal, timeoutMs),
      });
    } catch (err) {
      return new Response(null, { status: err?.name === 'TimeoutError' ? 504 : 502 });
    }
    const out = new Headers();
    for (const name of RESPONSE_HEADERS) {
      const v = upstream.headers.get(name);
      if (v) out.set(name, v);
    }
    // A 304 or 204 must not carry a body, or Response() throws.
    const empty = [101, 204, 205, 304].includes(upstream.status);
    return new Response(empty ? null : upstream.body, { status: upstream.status, headers: out });
  };
}
