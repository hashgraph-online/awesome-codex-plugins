# Recipes: putting the pieces together per stack

How the parts fit, in the order a page uses them:

```
consent.js   ── window.analyticsConsent, the banner, "Privacy settings"   (model B)
k.js         ── reports ──► POST /api/k ──► collector.mjs ──► a store       (all models)
posthog-guard.mjs ── after Accept only ──► /ingest/* ──► posthog-proxy.mjs ──► PostHog EU
visits.mjs   ── on a schedule: rows ──► Slack lines / e-mail                (B, C)
```

**Rules for every stack:**

- **Copy the assets you need** from this skill's `assets/` folder into the
  project: public files for the browser, server files next to the routes.
  Keep their comments.
- **One private-path rule, in four places:** k.js `data-skip`, the
  collector's `skip`, consent.js `skip`, and posthog-guard's `private`.
  Write it once as a regex, for example `^/(account|reset|invite|pay)(/|$)`.
  A string is one regex: never a comma-separated list, because a regex may
  contain `{1,3}`. For a case-insensitive rule write the string as
  `/^\/(account|reset)(\/|$)/i`; k.js, consent.js and the collector read the
  flags, and posthog-guard takes a RegExp (`/…/i`) or that string.
- **Content Security Policy.** Inline `<script>` config (as below) needs a
  nonce or hash in `script-src`, or move the config into a small external
  file (`/analytics-config.js`). consent.js injects a `<style>` by default:
  on a static host serve `assets/consent.css` with `stylesheet:
  '/consent.css'` (or its rules in the site's CSS and `styles: false`), so
  `style-src 'self'` is enough; with a per-request nonce, give consent.js's
  `<script>` tag the nonce (the style inherits it).
- **Load consent.js before anything that reads it.** In the `<head>`, with
  `defer` and before k.js and the PostHog module (deferred and module
  scripts run in document order, after parsing), or `beforeInteractive` in
  Next.js. Without `defer` it blocks rendering (about +150 ms FCP on a
  mobile Lighthouse run); drop `defer` only when an inline script reads
  `window.analyticsConsent` while the page is still parsing.
- **No same-origin server?** The collector needs a route that takes a POST
  on the site's own origin (a function, an API route, a small Node server).
  If the site is purely static with no functions, stop and ask the owner.
  Other origins mean CORS and a second host to describe in the policy.
- **Linters:** the copied assets are vendored code, ES5 in the browser
  files; add them to the linter's ignore list (e.g. `public/k.js`,
  `public/consent.js`, `lib/analytics/*.mjs` in eslint's `ignores`) rather
  than editing them to satisfy the site's rules.
- **TypeScript:** the assets are plain JS. Import `.mjs` with `allowJs`, or
  add a one-line `declare module '*/collector.mjs';` shim. Do not rewrite
  them in TS by hand; the tests cover the JS.

## Plain HTML with a Node server (Express or `http`)

```html
<!-- in every page's <head>, private pages included (consent.js hides itself there) -->
<script>window.consentConfig = { skip: '^/(account|reset)(/|$)', detailsHref: '/privacy',
  texts: { title: '…', body: '…' } };</script>
<script src="/consent.js" defer></script>
<script src="/k.js" defer data-ids="consent" data-skip="^/(account|reset)(/|$)"
        data-hosts="example.com,www.example.com,localhost,127.0.0.1"></script>
<!-- only if PostHog is used: -->
<script type="module">
  import { startPostHog, stopPostHog, purgePostHog } from '/posthog-guard.mjs';
  const site = { token: 'phc_…', hosts: [location.hostname], origin: location.origin, apiHost: '/ingest',
    private: [/^\/(account|reset)(\/|$)/], consented: () => window.analyticsConsent?.get() === 'granted' };
  const load = () => import('/vendor/posthog.mjs');   // a copy of node_modules/posthog-js/dist/module.mjs
  if (site.consented()) startPostHog(site, load); else purgePostHog();
  window.addEventListener('consent:changed', (e) => { if (e.detail === 'granted') startPostHog(site, load); });
  Object.assign(window.consentConfig, { onWithdraw: () => stopPostHog(), onDecline: () => purgePostHog() });
</script>
```

Footer of every page, 404 included:
`<button type="button" class="ph-no-capture" data-consent-open>Privacy settings</button>`.

The server (Express):

```js
import { createCollector, fileStore, toNodeHandler } from './analytics/collector.mjs';
import { createPostHogProxy } from './analytics/posthog-proxy.mjs';
const store = fileStore('./data/analytics', { dailyDays: 730, rowsDays: 180 });
await store.purge();
setInterval(() => store.purge(), 6 * 3600_000).unref();
const collect = createCollector({ hosts: ['example.com', 'www.example.com', 'localhost', '127.0.0.1'],
  store, ids: 'consent', skip: [/^\/(account|reset)(\/|$)/], timeZone: 'Europe/Berlin' });
// Before any body parser: express.json()/text() would consume the body.
app.post('/api/k', toNodeHandler(collect, { trustProxy: false }));
```

- **`trustProxy`.** `true` when a proxy you run sets `X-Forwarded-For`;
  `'cloudflare'` only when the origin cannot be reached except through
  Cloudflare.
- **The PostHog proxy.** `app.all('/ingest/*splat', …)` (Express 5; in
  Express 4 it is `'/ingest/*'`) converts the request to a
  Fetch `Request` (or use `@hono/node-server`), then `createPostHogProxy({ region: 'eu' })`.
- **`fileStore`.** It needs a single Node process.

## Next.js (App Router)

Files (this layout is tested by the skill's end-to-end run):

| File | Content |
|---|---|
| `public/consent.js`, `public/k.js` | copied from `assets/` |
| `src/lib/analytics/collector.mjs`, `visits.mjs`, `posthog-guard.mjs`, `posthog-proxy.mjs` | copied from `assets/` |
| `src/lib/analytics/config.ts` | hosts, the skip regex source, the time zone, the retention days, read by everything |
| `src/app/layout.tsx` | the config script, consent.js and k.js, and the "Privacy settings" button in the footer |
| `src/app/api/k/route.ts` | the collector |
| `src/app/ingest/[...path]/route.ts` | the PostHog proxy, if used |
| `next.config.ts` | `skipTrailingSlashRedirect: true` if the proxy is used; the headers |

The layout, with consent.js and k.js before hydration:

```tsx
import Script from 'next/script';
import { headers } from 'next/headers';
// With a nonce-based CSP (below); without one, drop the two lines about it.
const nonce = (await headers()).get('x-nonce') ?? undefined;
// in <head> or at the top of <body>. mount: 'end' is required: React hydrates
// <body>, and a banner inserted before its children breaks hydration (#418).
<Script id="consent-config" strategy="beforeInteractive" nonce={nonce}>{`window.consentConfig = { skip: ${JSON.stringify(SKIP)}, detailsHref: '/privacy', mount: 'end' };`}</Script>
<Script src="/consent.js" strategy="beforeInteractive" nonce={nonce} />
<Script src="/k.js" strategy="afterInteractive" nonce={nonce} data-ids="consent" data-skip={SKIP} data-hosts={HOSTS.join(',')} />
// in the footer:
<button type="button" className="ph-no-capture" data-consent-open>Privacy settings</button>
```

**CSP on the App Router.** It needs inline scripts, so a strict policy is
the nonce one from Next's CSP guide: a `proxy.ts` (`middleware.ts` before
Next 16) that sets `script-src 'self' 'nonce-…' 'strict-dynamic'` and
`style-src 'self' 'nonce-…'` and passes the nonce in `x-nonce`. With
`'strict-dynamic'`, scripts loaded by a nonced script (PostHog's lazy
recorder) are allowed and `'self'` is ignored. Nonces need dynamic
rendering: pages cannot be static or use partial prerendering, so turn
`cacheComponents` off. consent.js's `<style>` takes the nonce of its own
tag.

**Scheduled jobs on `next start`** (Slack visit lines, digest, retention,
health): Next bundles the route handler and `instrumentation.ts` into
separate module instances, so share one store through `globalThis`:

```ts
// lib/analytics/store.ts
export const store = () => (globalThis.__kStore ??= fileStore('./data/analytics'));
// instrumentation.ts
export async function register() {
  if (process.env.NEXT_RUNTIME !== 'nodejs') return;
  const { startJobs } = await import('./lib/analytics/jobs');   // setInterval loops calling the assets
  startJobs();
}
```

On serverless hosts (Vercel), use the host's cron calling a route instead.

**Collector.** If the store's `init()` fails, the collector must still
answer 204 and try again on the next report (the same wrapper as in
`collector.md`):

```ts
import { createCollector, mongoStore } from '@/lib/analytics/collector.mjs';
export const runtime = 'nodejs';
let ready: Promise<ReturnType<typeof mongoStore>> | null = null;
const store = () => (ready ??= db().then(async (d) => { const s = mongoStore(d); await s.init(); return s; })
  .catch((e) => { ready = null; throw e; }));
const collect = createCollector({ hosts: HOSTS, ids: 'consent', skip: SKIP, timeZone: TZ,
  store: { write: async (x) => (await store()).write(x) } });
export const POST = (req: Request) => collect(req);
```

**PostHog.** Use a small client component mounted in the layout, or
`instrumentation-client.ts`. Start it after the page is idle, with
`import('posthog-js')` (bundled). consent.js is already loaded
(`beforeInteractive`), so `window.analyticsConsent` exists.

**Next.js details:**

- Internal links must use `next/link`. With smooth scrolling, add
  `<html data-scroll-behavior="smooth">`.
- `next dev` blocks LAN-IP origins unless `allowedDevOrigins` is set. Test
  with `next build && next start`, or with verify's `--resolve <host>`.
- Route files may export only route fields: put helpers in `lib/`.

## Astro on Cloudflare Pages

- **Static output with Pages Functions.** Put the collector in
  `functions/api/k.js`. Build it once per isolate, with `env` from the
  context:

  ```js
  import { createCollector, analyticsEngineStore } from '../../src/analytics/collector.mjs';
  let collect;
  export async function onRequestPost({ request, env }) {
    collect ??= createCollector({ hosts: ['example.com', 'www.example.com'], ids: 'never',
      skip: '/^\\/(account|reset)(\\/|$)/i',   // the same rule as k.js data-skip
      timeZone: 'Europe/Berlin', store: analyticsEngineStore(env.EVENTS) });
    return collect(request);
  }
  ```

  `request.cf.country` gives the country with no header.

  collector.mjs also holds `fileStore`, which imports `node:fs/promises`
  lazily. It is never called on Workers, but the bundler sees the import:
  set `compatibility_flags = ["nodejs_compat"]` in `wrangler.toml` (or
  the Pages project's settings), or wrangler warns or fails to build.
  Alternatively delete `fileStore` from your copy.
- **With the SSR adapter** (`_worker.js`), Cloudflare ignores `/functions`.
  Use an API route instead: `src/pages/api/k.ts` with
  `export const prerender = false`, and `env` from
  `Astro.locals.runtime.env`.
- **A store on Cloudflare.** Two options:
  - **Workers Analytics Engine:** `analyticsEngineStore(env.EVENTS)` in
    `collector.mjs`. Every counter increment is a data point; its comment
    has the SQL that sums a day. It was tested against a stand-in binding
    only, so compare one day's numbers with the browser's reports after
    deploying. Analytics Engine keeps data for **3 months** and **samples**
    at volume (`SUM(double1 * _sample_interval)`). Write the 3 months into
    the privacy text instead of 2 years. One data point per report, with
    columns of your own, works too. It **cannot delete**: with model B set
    `deleteButton: false` in `consentConfig` and `data-delete="off"` on
    k.js, so no "Delete my visit data" button promises what the store
    cannot do, and say in the privacy text that records go after 3 months.
  - **D1 (SQLite):** `sqlStore({ dialect: 'sqlite', query: async (sql, p) =>
    (await env.DB.prepare(sql).bind(...p).all()).results })` from
    `collector.md`; it can delete, so the button can stay. Run
    `enforceRetention` from a cron Worker.
- **Cron.** Pages has no cron. Notifications need a separate Worker with
  a cron trigger, which reads Analytics Engine over its SQL API.
- **Astro's `<ClientRouter />`.** It swaps `<body>`. consent.js re-mounts
  its banner and follows routes; k.js follows `history`.
- **`astro dev`** does not run Pages Functions. Test with
  `wrangler pages dev ./dist`.

## A Vite SPA (React, Vue, Svelte) with a Node server

k.js and consent.js go in `index.html` (`defer`, consent.js first). The
history patch follows the router. The server serves `dist/`, the collector
and, for unknown paths, **a real 404**: an SPA fallback that answers 200 for
every path is a "soft 404" (verify fails it). Keep one list of routes that
the router and the server both import, so a new page cannot be served as a
404 by mistake:

```js
// src/routes.js: the only list of pages
export const ROUTES = ['/', '/product', '/about', '/privacy', '/blog/:slug'];
export const known = (path) => ROUTES.some((r) => new RegExp('^' + r.replace(/:[^/]+/g, '[^/]+') + '/?$').test(path));

// server.mjs
import { known } from './src/routes.js';
app.post('/api/k', toNodeHandler(collect));
app.use(express.static('dist', { index: false }));
app.use((req, res) => res.status(known(req.path) ? 200 : 404).type('html').send(known(req.path) ? shell : shell404));
// shell404: dist/index.html with data-k404 on <html>, so k.js reports the
// broken link; the router's catch-all route renders the 404 page.
```

In the router's catch-all route, set the marker for client-side 404s
before k.js sees the route (`useLayoutEffect` adding `data-k404` to
`<html>`, removed on unmount).

## When something does not fit

- **No server code at all** (a pure static host): model A with a
  collector on a functions platform you add (Cloudflare Pages Functions,
  Netlify Functions, Vercel). Or ask the owner whether a hosted tool fits
  better.
- **Multi-page site without client-side routing, model B:** with the
  default `memory` visit id, every page load is its own visit row.
  Use `data-visit-store="session"` if visits should span pages, and list
  `k-visit` in the privacy text.
- **No owner to ask** (an unattended agent): stop after Discover, and write
  the questions from `decisions.md` into the report.
