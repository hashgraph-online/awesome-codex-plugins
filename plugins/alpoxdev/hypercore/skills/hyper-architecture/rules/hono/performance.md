# Performance

> Measure on the deployed runtime, prefer the default SmartRouter, and cut wire bytes with `compress()`/`etag()`/`cache()` only where the platform does not already do it.

Read this when the request names latency, throughput, bundle size, cold start, caching, or "최적화" on a Hono app. This file owns the router choice, the response-byte middleware, and the shared-cache contract; `rules/hono/platform.md` owns which runtime you are measuring on.

## Measure first

The runtime decides what a number means, so name it before measuring. A local Node server, a Cloudflare Worker invocation, and a Deno Deploy isolate have different cold-start and CPU budgets.

```bash
# local Node/Bun/Docker target
node dist/index.js &            # or bun run start, or the repo's start script
wrk -t4 -c50 -d20s http://127.0.0.1:3000/<route>
curl -s -o /dev/null -w 'ttfb=%{time_starttransfer}s size=%{size_download}B\n' http://127.0.0.1:3000/<route>
```

- Record p50/p95 latency and requests per second for one read and one write route, at the concurrency the app actually serves.
- Record the response bytes before and after any compression or ETag change, and confirm the runtime is not already encoding the body.
- On a worker platform, measure the deployed target (`wrangler dev --remote` / `deploy` then a load run), not only `wrangler dev` locally, because the platform adds its own compression, cache, and CPU limits.
- As of 2026-11-07 the registry `latest` for `hono` is 4.13.17; 4.13.16 remains the security floor that fixes router and form-validation defects [L-70]. Record the installed version from `package.json` and do not measure a drift you have not identified.

A lever you cannot measure here is reported as not measured, never as a gain.

## Rules

Ordered by typical impact.

1. **`official` — Keep the default `SmartRouter` unless a measurement justifies a change.** `SmartRouter` composes routers and its source shows `new SmartRouter({ routers: [new RegExpRouter(), new TrieRouter()] })`; `RegExpRouter` compiles patterns into a single regex and is described as "the fastest router in the JavaScript world" [L-51]. Switching is one constructor option, `new Hono({ router: new RegExpRouter() })` [L-52]. Do not pin `RegExpRouter` globally before the route set is known, because it rejects patterns `TrieRouter` accepts [L-51].
2. **`official` — Choose a router for the runtime's actual cost model.** `LinearRouter` is for runtimes that initialize per request because registration is much faster there; `TrieRouter` supports all patterns and is slower than `RegExpRouter` but far faster than Express; `PatternRouter` is the smallest, and "an application using only PatternRouter is under 15KB in size" [L-51]. `hono/tiny` is the `PatternRouter` preset, so it buys size, not route throughput [L-56].
3. **`official` — Register middleware and routes in the order they must run.** "Handlers or middleware will be executed in registration order" [L-51]. Moving a broad middleware later changes both behavior and cost for every preceding route, so keep the mount table explicit and measure after any reorder.
4. **`official` — Do not compress on a platform that already compresses.** `compress()` responds to `Accept-Encoding`, supports only `'gzip'` and `'deflate'`, and defaults to a 1024-byte threshold; on Cloudflare Workers and Deno Deploy "the response body will be compressed automatically, so there is no need to use this middleware" [L-53]. On Node and other bare runtimes, add it with a `contentTypeFilter` (the exported `COMPRESSIBLE_CONTENT_TYPE_REGEX` is the default) so images and archives are skipped [L-53].
5. **`hypercore-default` — Return 304s on GET-heavy JSON routes.** The middleware behavior is official; adding it as a default is our policy. `etag()` adds the ETag header and answers matching conditional requests with `304`; extend `retainedHeaders` beyond the default retained set (`Cache-Control`, `Content-Location`, `Date`, `ETag`, `Expires`, `Vary`) when a custom header must survive a 304 [L-54].
6. **`official` — Register `cache()` after authentication and set the per-user cache headers.** The middleware uses the Web Cache API on Cloudflare custom domains and Deno 1.26+/Deno Deploy, and "the cache is shared by all clients… The middleware does not look at the `Cookie` header" [L-55]. Send `Cache-Control: private` or `no-store`, or `vary: 'Cookie'`, on any per-user response, and note that QUERY requests above `maxQueryBodySize` (64 KiB default) bypass the cache [L-55].
7. **`hypercore-default` — Gate HTML responses on Core Web Vitals when the Hono app serves pages.** LCP ≤ 2.5 s, INP ≤ 200 ms, CLS ≤ 0.1 at p75, reported for mobile and desktop separately [L-67]. For an API-only app this rule does not apply; measure latency instead.

## Do not

- Switch to `RegExpRouter` as a reflex. It is the fastest single router but rejects patterns the default composition falls back to `TrieRouter` for, so an unmeasured switch can turn a working route into a startup error [L-51][L-52].
- Adopt `hono/tiny` to make an existing API pass a latency budget. It trades route throughput for size [L-56].
- Add `compress()` on Cloudflare Workers or Deno Deploy and claim a byte reduction the platform already delivered [L-53].
- Enable `cache()` before auth, or leave the default `Cache-Control` on a per-user response. The cache ignores `Cookie` and will serve one user's payload to another [L-55].
- Put `cache()` in front of an endpoint whose QUERY bodies exceed `maxQueryBodySize` and expect a cache hit [L-55].
- Present `etag()` or `cache()` as free. ETag costs a body read or hash on every miss, and the shared cache needs correct private/no-store headers before it is safe [L-54][L-55].
- Quote a local `wrangler dev` number as the deploy result. The platform adds compression, caching, and CPU limits [L-53][L-55].

## Checklist

- [ ] The runtime was named and the measurement ran against that runtime, not only a local dev server.
- [ ] Before and after numbers exist for every claimed gain.
- [ ] The router choice is the default, or a measured reason names the route-set constraint that forced it.
- [ ] Middleware and route registration order is explicit and was not shuffled without re-measuring.
- [ ] `compress()` is absent on a compressing platform, or configured with a content-type filter elsewhere.
- [ ] `etag()` is applied where conditional GETs matter, with `retainedHeaders` covering custom headers.
- [ ] `cache()` sits after auth, and per-user responses carry `private`/`no-store` or `vary: 'Cookie'`.
- [ ] QUERY endpoints above `maxQueryBodySize` are known to bypass the cache.
- [ ] HTML responses meet the CWV thresholds at p75, or the app is API-only and the point is explicitly out of scope.
- [ ] The change keeps the gates in `stacks/hono/architecture-rules.md` and the checks from `rules/setup/typescript.md` passing.

## Sources

> Checked 2026-11-07. Router, middleware, and cache statements come from the Hono documentation and the `hono/tiny` preset source; current version comes from the npm registry.

| Claim | Source |
|---|---|
| Router inventory, `SmartRouter` composition, registration order, `RegExpRouter` speed claim | [Routers – Hono](https://hono.dev/docs/concepts/routers) |
| `new Hono({ router })` constructor option and default | [Hono API](https://hono.dev/docs/api/hono) |
| `hono/tiny` preset importing `PatternRouter` | [hono/tiny preset source](https://raw.githubusercontent.com/honojs/hono/main/src/preset/tiny.ts) |
| `compress()` codecs, default threshold, content-type filter, platform note | [Compress Middleware – Hono](https://hono.dev/docs/middleware/builtin/compress) |
| `etag()` 304 behavior and retained headers | [ETag Middleware – Hono](https://hono.dev/docs/middleware/builtin/etag) |
| `cache()` platform support, shared cache, `Cookie` caveat, `maxQueryBodySize` | [Cache Middleware – Hono](https://hono.dev/docs/middleware/builtin/cache) |
| Core Web Vitals thresholds at p75 | [Web Vitals](https://web.dev/articles/vitals) |
| `hono` 4.13.17 as registry `latest` | [npm registry: hono](https://registry.npmjs.org/hono) |
