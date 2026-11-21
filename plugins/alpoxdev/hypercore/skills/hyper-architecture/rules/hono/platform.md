# Platform Setup

> Keep adapter and runtime concerns at the edge

---
## Stable Runtime Baseline

As verified on 2026-11-07, Hono is 4.13.17 (4.13.16 remains the security floor that fixes the router and form-validation defects) and `@hono/node-server` is 2.1.6. The adapter requires Node `>=20` and accepts Hono `^4 || ^5.0.0-0`; this package manifest is stricter than the Node.js guide page, which still lists 18.x minimums. Installed package metadata and the selected runtime's current official guide win.

- Cloudflare/Deno/Bun runtimes commonly expose a Fetch-compatible app entry; Node uses the official adapter.
- Import adapters from their own packages (`@hono/bun`, `@hono/deno`, `@hono/cloudflare-workers`, `@hono/aws-lambda`, `@hono/lambda-edge`, `@hono/netlify`, `@hono/vercel`, `@hono/service-worker`). `hono/<adapter>` still works in v4 but is deprecated and is removed in v5, so new code must not add it. `hono/cloudflare-pages` has no replacement package.
- Node WebSocket support is built into `@hono/node-server`: install `ws`, create a `WebSocketServer` with `{ noServer: true }`, pass it to `serve()` as `websocket: { server: wss }`, and use `upgradeWebSocket` from `@hono/node-server`. `@hono/node-ws` is deprecated.
- Keep `app.fetch` or the reusable Hono app separate from process startup, listeners, WebSocket servers, static-file roots, and shutdown hooks.
- Treat Node raw request/response APIs, Cloudflare `executionCtx`/bindings, and provider-specific wait-until behavior as adapter capabilities.
- `serveStatic` serves only `GET` and `HEAD`, rejects paths that still contain `%` after decoding, and needs `allowPercentInPath: true` to serve file names with a literal `%`. That option can bypass path-scoped middleware, so access control must sit on the same pattern the static handler serves.
- Validate environment configuration at startup where possible. Never put secrets in client-visible config, logs, or generated OpenAPI examples.
- Test the runtime adapter when code uses streaming, WebSockets, static files, raw APIs, execution context, or provider bindings; `app.request()` alone is insufficient.
- Do not change adapters, deployment manifests, compatibility dates, or runtime versions without explicit scope and provider-specific verification.

## Rules

- Runtime adapter code belongs in entry files such as `src/index.ts`, `src/server.ts`, or `src/worker.ts`
- Route modules should stay portable across adapters where possible
- Adapter imports come from `@hono/*` packages, never from deprecated `hono/<adapter>` subpaths
- Environment bindings/config should be typed explicitly
- Database bindings and connection strings should be read through the platform/config boundary, not directly from feature handlers
- Use runtime-appropriate database clients: Hono `Bindings` / `c.env` for Workers bindings such as D1, and validated config for Node/Bun server runtimes
- `showRoutes()` and similar helpers stay dev-only
- `basePath()` or API version prefixes should be defined intentionally at composition boundaries
- Static-file access control is applied on the same path pattern the static handler serves, and `allowPercentInPath` is not a workaround for authorization

## Review Checklist

- Adapter imports are not mixed into route modules
- Adapter imports come from `@hono/*` packages, not deprecated `hono/<adapter>` subpaths
- Node WebSocket bootstrap uses `@hono/node-server` with `ws`, not `@hono/node-ws`
- Runtime-specific concerns are isolated
- Config and bindings are typed
- Database client setup matches the runtime and stays outside route modules
- Static file routes are protected on their served pattern and do not rely on `allowPercentInPath`
- Debug helpers are not left enabled accidentally

## Sources

> Checked 2026-11-07. The adapter split, deprecations, and static-file behavior come from the linked release notes and guides; package versions come from the npm registry.

| Claim | Source |
|---|---|
| Hono 4.13.17 as registry `latest`, `@hono/node-server` 2.1.6, and their peer and engine ranges | [npm registry: hono](https://registry.npmjs.org/hono), [npm registry: `@hono/node-server`](https://registry.npmjs.org/@hono/node-server) |
| Adapter packages and `hono/<adapter>` deprecation | [`hono` v4.13.10 release](https://github.com/honojs/hono/releases/tag/v4.13.10) |
| Node WebSocket bootstrap and `@hono/node-ws` deprecation | [Node.js Guide](https://hono.dev/docs/getting-started/nodejs), [`@hono/node-server` README](https://github.com/honojs/node-server) |
| `serveStatic` `%` rejection, `allowPercentInPath`, GET/HEAD only | [`hono` v4.13.11 release](https://github.com/honojs/hono/releases/tag/v4.13.11), [`hono` v4.13.14 release](https://github.com/honojs/hono/releases/tag/v4.13.14) |
