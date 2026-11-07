# Platform Setup

> Router, environment, alias, and operations-adjacent setup rules/tanstack-start

---

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| `src/router.tsx` exports fresh-instance `getRouter()` | Official | Block missing setup |
| Server/client env boundaries | Safety policy | Block secret leaks |
| Runtime env validation for non-trivial apps | Hypercore convention + Safety policy | Warn or add `src/config/env.ts` scaffold |
| Vite-version-aware path aliases | Hypercore convention | Fix when touched |
| Hosting via Nitro (`nitro/vite`) with Vite 8 and Node ≥22.12 | Official | Block removed-plugin or Vite 7 advice |
| Installed `@tanstack/*` versions checked against the official supply-chain advisory | Safety policy | Verify before install or upgrade |

---

## Dependency Safety

- **Safety policy.** Check the installed `@tanstack/*` versions against the official advisory's affected/patched ranges before installing or upgrading. Precedent: advisory [`GHSA-g7cv-rxg3-hmpx`](https://github.com/TanStack/router/security/advisories/GHSA-g7cv-rxg3-hmpx) (published 2026-05-11, critical) — malicious versions of `@tanstack/*` packages were published and harvested cloud credentials, GitHub tokens, and SSH keys at install time. Of the packages these snapshots pin, only `@tanstack/cli` was unaffected.
- **Official.** Affected → patched ranges recorded by that advisory. Treat this table as provenance and re-read the advisory for the authoritative range check.

| Package | Malicious versions | Patched |
|---|---|---|
| `@tanstack/react-router` | 1.169.5, 1.169.8 | 1.169.9 |
| `@tanstack/react-start` | 1.167.68, 1.167.71 | 1.167.72 |
| `@tanstack/router-cli` | 1.166.46, 1.166.49 | 1.166.50 |
| `@tanstack/router-plugin` | 1.167.38, 1.167.41 | 1.167.42 |
| `@tanstack/start-client-core` | 1.168.5, 1.168.8 | 1.168.9 |
| `@tanstack/start-plugin-core` | 1.169.23, 1.169.26 | 1.169.27 |
| `@tanstack/start-server-core` | 1.167.33, 1.167.36 | 1.167.37 |
| `@tanstack/zod-adapter` | 1.166.12, 1.166.15 | 1.166.16 |

- Do not record any specific version here as "known safe". The advisory's postmortem states every currently-available published version of every TanStack package is safe to install; the authoritative range check lives in the advisory and the npm advisory database, not in this file.
- If an affected version was installed on a host, treat that host as potentially compromised and rotate the credentials reachable from it (AWS, GCP, Kubernetes, Vault, GitHub, npm, SSH) — the payload ran as an install lifecycle script.

## Release Status

- **Official.** Start is stable at v1. `@tanstack/react-start` 1.169.0 (published 2026-10-12) is the first stable release: "TanStack Start is stable. If you're upgrading from a release candidate, follow `Migrate from the Release Candidate`." The stable line is 1.169.x; `@tanstack/react-router` moves independently on 1.170.x.
- **Official.** Upgrading a release-candidate project means removing three APIs and checking four behavior areas: `@tanstack/nitro-v2-vite-plugin` becomes `nitro()` from `nitro/vite`; `useSession` becomes a session library such as iron-session; `.inputValidator()` becomes `.validator()`; Vite 7 becomes Vite 8. The behavior areas are Errors, Responses, Requests and middleware, and each is recorded in `references/official/tanstack-start/tanstack-start-2026-11-04.md`.
- **Official.** Start requires Vite 8 when building with Vite (`peerDependencies.vite` is `>=8.0.0`; "Vite 7 is no longer supported") and `@tanstack/react-start@1.169.4` declares `engines.node` `>=22.12.0`. Check both before proposing a version bump or a fresh scaffold.
- Stability does not make behavior guesses safe. The Router and Start packages still absorb BREAKING changes in patch releases, so re-check the dated snapshot instead of assuming an API is settled.

---

## Router Setup

- `src/router.tsx` must export `getRouter()`
- `getRouter()` must create and return a fresh router instance each call
- Router-wide behavior such as `scrollRestoration`, preload defaults, and cache settings belong here

---

## Environment Rules

- Do not create `src/env/`, `src/env.ts`, or `src/env.d.ts` for new TanStack Start env scaffolds.
- Keep env code under `src/config/`; the canonical validation module is `src/config/env.ts`.
- Use `@t3-oss/env-core` with `zod` for TanStack Start/Vite projects; scaffold with `createEnv`.
- Configure client variables with `clientPrefix: "VITE_"` unless the project has explicitly changed Vite `envPrefix`.
- `VITE_*` variables are client-exposed and must not contain secrets, tokens, private API keys, passwords, or database URLs.
- Server-only env vars stay in `process.env`, are accessed behind server boundaries, and are listed in `server`.
- Client-safe env vars come from `import.meta.env`, are listed in `client`, and use the public prefix.
- Prefer `runtimeEnvStrict` for explicit build-time coverage; otherwise use `runtimeEnv` only when the framework/runtime reliably provides the whole env object.
- Include `isServer: typeof window === "undefined"` when a shared config file can be imported from both server and client code.
- Read env inside the request, not at module scope: `process.env` access belongs inside `.handler()`, middleware `.server()`, server-route handlers, or another per-request callback. On Cloudflare Workers and other edge SSR runtimes env is injected per request, so a module-scope read evaluates to `undefined` even on the server, and on the client it risks inlining secrets into the bundle.
- Set `emptyStringAsUndefined: true` for new validation modules unless the project has a documented reason not to.
- If sensitive server variable names must not ship to client bundles, split the schema under `src/config/` (for example `env.server.ts` and `env.client.ts`), not under `src/env/`.

Canonical starter shape:

```ts
// src/config/env.ts
import { createEnv } from "@t3-oss/env-core"
import * as z from "zod"

export const env = createEnv({
  server: {
    DATABASE_URL: z.url(),
  },
  clientPrefix: "VITE_",
  client: {
    VITE_PUBLIC_APP_URL: z.url(),
  },
  runtimeEnvStrict: {
    DATABASE_URL: process.env.DATABASE_URL,
    VITE_PUBLIC_APP_URL: import.meta.env.VITE_PUBLIC_APP_URL,
  },
  isServer: typeof window === "undefined",
  emptyStringAsUndefined: true,
})
```

---

## Path Alias Rules

- Path aliases must be configured intentionally, not assumed
- Vite 8+: prefer `resolve.tsconfigPaths: true` (Vite's own option, default `false`)
- Vite 7 and earlier: use `vite-tsconfig-paths`
- A TanStack Start project is necessarily on the first branch: Start 1.169+ requires Vite 8, so the `vite-tsconfig-paths` branch only applies to non-Start Vite 7 projects
- Keep one canonical alias convention in the repo

---

## Operations-Adjacent Patterns

- Health/readiness endpoints are allowed as server routes
- Sitemap/robots generation may use prerender config or server routes
- Machine-readable endpoints for integrations/LLMO are allowed when explicitly required
- Observability hooks, metrics, and Sentry-style integrations belong in operations/platform docs, not page logic

---

## Server Entry

- `src/server.ts` is optional. Without it, Start uses its built-in entry, which renders requests and converts uncaught errors into HTTP responses. Do not add a custom entry just to get error handling.
- When a custom entry is needed, `createServerEntry` keeps the whole callback inside the request context, and `createStartHandler(...)` rethrows the original error so `handleStartError(error)` can build the response with helper state applied.
- Per-request values such as a request ID or a database handle belong in `handler.fetch(request, { context })`, typed by augmenting `server.requestContext` on `@tanstack/react-router`'s `Register` interface. The type registration provides no runtime value; the context reaches global middleware, request and function middleware, server routes, server functions, and the router.

## Hosting And Deployment

- **Official.** Deploy through Nitro with the `nitro/vite` plugin, not the removed `@tanstack/nitro-v2-vite-plugin`. Add `nitro()` from `nitro/vite` to `vite.config.ts` alongside `tanstackStart()`; Nitro integrates with Vite's Environments API as Start's underlying build tool.
- **Official.** Official hosting partners are Cloudflare (via `@cloudflare/vite-plugin` and `wrangler`), Netlify (via `@netlify/vite-plugin-tanstack-start`), and Railway (via Nitro). Treat other providers as supported but unpartnered.
- **Official.** On Node + Nitro, srvx `FastResponse` is the documented throughput option; it is a deployment-tuning choice, not an architecture requirement.
- Do not record hosting configuration in page or route code. Deployment settings belong in `vite.config.ts`, the provider config file, and operations docs.

## Review Checklist

- `getRouter()` exists and returns a new instance
- env usage is typed, boundary-safe, and read per request rather than at module scope
- alias setup matches the Vite version in use
- hosting advice names `nitro/vite` and never the removed plugin
- operational endpoints are not mixed with internal app RPC

## Sources

> Safety-policy facts come from the official advisory <https://github.com/TanStack/router/security/advisories/GHSA-g7cv-rxg3-hmpx> and its postmortem <https://tanstack.com/blog/npm-supply-chain-compromise-postmortem>; the stable-release status, the Vite 8 requirement, the removed APIs, and the hosting partners come from <https://tanstack.com/start/latest/docs/framework/react/overview.md>, <https://tanstack.com/start/latest/docs/framework/react/migrate-from-release-candidate.md>, <https://tanstack.com/start/latest/docs/framework/react/guide/hosting.md>, <https://tanstack.com/start/latest/docs/framework/react/guide/environment-variables.md>, <https://registry.npmjs.org/@tanstack/react-start/latest>, and <https://vite.dev/config/shared-options.md>. Official facts verified 2026-11-04. Everything else is delegated to this package's own snapshots: `references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, and `references/official/tanstack-start/current-docs-2026-11-04.md`. Repository-local links checked 2026-11-04.
