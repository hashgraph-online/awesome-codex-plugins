# Architecture Rules Reference

> Complete rule set for Astro projects under `hyper-architecture`, plus the gate table this stack guide judges changes against.

Some rules below are stricter than Astro defaults. They are labelled `hypercore-default` team conventions, not framework requirements. Rules that an opened official page states are labelled `official`.

Brownfield adoption rule: untouched legacy code may be tracked as migration work instead of failing immediately when the issue is stylistic or Hypercore-specific. Rendering-mode errors, missing adapters, authorization gaps, secret exposure, and non-serializable island props still block immediately, especially in touched code.

---

## Forbidden

| Category | Forbidden |
|---|---|
| Detection | Applying Astro rules to a project with no `astro` dependency and no `astro.config.*` |
| Precedence | Routing an Astro target to the Vite guide because `vite` is in its manifest |
| Routes | A hand-written route table, or routes outside `src/pages/` |
| Dynamic routes | `getStaticPaths()` on an on-demand route, or expecting its `props` there |
| Endpoints | A page file that returns a `Response` instead of an endpoint exporting `GET`/`POST` |
| Rendering | Adding Actions, sessions, server islands, live collections, or route caching while `output: 'static'` has no adapter |
| Rendering | Switching the whole site to `output: 'server'` to make one route dynamic |
| Headers | Setting response headers inside a child component instead of at page level |
| Islands | Framework JavaScript with no `client:*` directive and no stated reason |
| Islands | Passing functions, class instances, or circular structures to a hydrated or server island |
| Content | `src/content/config.ts` (removed legacy location) instead of `src/content.config.ts` |
| Content | Unsorted `getCollection()` results presented as a stable order |
| Actions | An Action without Zod validation on non-trivial input |
| Actions | An Action that relies on page-level auth instead of authorizing in the handler or middleware |
| Middleware | A default export instead of a named `onRequest`, or reassigning `context.locals` |
| Env | Secrets read through `import.meta.env` in shared code, or `context: 'client'` with `access: 'secret'` |
| Advanced routing | Authorization by `url.pathname` prefix inside `src/fetch.ts` |
| Build output | Hand-written files under `dist/` or `.astro/` |
| Performance | Claiming a performance gain without a before and after number on a production build |
| Reporting | Presenting a Hypercore convention as official Astro behavior |

---

## Gate Table

Gates run in order. A failure in an earlier gate stops the target.

### Gate 1: Detection and Rendering Mode

| Check | Rule |
|---|---|
| No `astro` dependency and no `astro.config.*` in the target | Not an Astro target; stop and route elsewhere |
| `astro` dependency present but `src/pages/` missing | BLOCKED. Without it the site has no routes |
| `output` not recorded before a server feature is recommended | BLOCKED |
| Server feature requested while `output: 'static'` and no `adapter` is configured | BLOCKED |
| Route needs request data but has no `export const prerender = false` | BLOCKED |
| `prerender` value is computed at runtime instead of being statically analyzable | BLOCKED |
| Whole-site `output: 'server'` proposed for a single dynamic route | WARNING, BLOCKED when most routes stay static |

### Gate 2: Routing and Structure

| Check | Rule |
|---|---|
| Route file outside `src/pages/` | BLOCKED |
| Dynamic route uses `[param]` where `[...rest]` is required, or the reverse | BLOCKED |
| `getStaticPaths()` used on an on-demand route, or `props` expected from it | BLOCKED |
| Endpoint missing a method export or `satisfies APIRoute` | BLOCKED |
| Route relies on the priority table without checking it (static over dynamic, endpoints over pages) | WARNING |
| File name collides with a reserved route prefix (`_astro`, `_server_islands`, `_actions`) | BLOCKED |
| Reusable UI, layout, or helper code placed in `src/pages/` | WARNING. Only routes belong there |
| Redirect implemented as a page when `redirects` config covers it | WARNING |
| `src/pages/500.astro` added to a static-only site | BLOCKED. It only works with on-demand rendering |

### Gate 3: Islands and Framework Boundaries

| Check | Rule |
|---|---|
| Framework component expected to be interactive but no `client:*` directive | BLOCKED |
| `client:load` used where `client:visible` or `client:idle` would do | WARNING |
| `client:only` used for a component that could render on the server | WARNING |
| Non-serializable prop passed to a hydrated component or a server island | BLOCKED |
| Server island used for a fragment that does not need request data | WARNING |
| Server island props large enough to exceed the query-string limit and fall back to POST | WARNING. It breaks caching |
| Only `.astro` files mix frameworks; a framework component importing another framework's component | BLOCKED |

### Gate 4: Content Layer

| Check | Rule |
|---|---|
| Collection without a `loader` | BLOCKED |
| Schema defined with a non-Zod validator or with `z` from `astro:content` | BLOCKED |
| `getCollection()` order treated as stable | BLOCKED |
| `reference()` used but never resolved through `getEntry()`/`getEntries()` | WARNING |
| Live collection added without an adapter | BLOCKED |
| Live collection used where a build-time collection plus a rebuild would do | WARNING |
| `deferRender: true` used without measuring build memory first | WARNING |

### Gate 5: Server Boundaries

| Check | Rule |
|---|---|
| Action input trusted without validation | BLOCKED |
| Action authorized only by a page-level check | BLOCKED |
| Action reachable at `/_actions/<name>` without the authorization an API endpoint would need | BLOCKED |
| `context.locals` reassigned instead of assigned fields | BLOCKED |
| Middleware exported as a default instead of a named `onRequest` | BLOCKED |
| Session read or written without a configured driver | BLOCKED |
| Environment variable read outside the schema in shared code | WARNING, BLOCKED for secrets |
| `security.checkOrigin` disabled without a recorded reason | BLOCKED |
| `security.csp` enabled together with `<ClientRouter />` | BLOCKED |
| `url.pathname` prefix used for authorization in `src/fetch.ts` | BLOCKED |

### Gate 6: Verification

| Check | Rule |
|---|---|
| `astro check` not run, or run without `@astrojs/check` and `typescript` installed | BLOCKED |
| TypeScript pinned to 7.x while `astro check` is the type gate | BLOCKED |
| `.astro` formatted by a JSX parser instead of `prettier-plugin-astro` | BLOCKED |
| Template or accessibility linting claimed for `.astro` from oxlint | BLOCKED |
| Component test written without the Container API when a component must be rendered | WARNING |
| Performance claim made without a production build measurement | BLOCKED |

---

## Layer Architecture

```text
Adapter / Worker Entrypoint
  astro.config.*  adapter: node | vercel | cloudflare | netlify
       |
       v
Routing Surface
  src/pages/**  (+ src/fetch.ts for a custom entrypoint)
       |
       v
Layouts and Pages
  src/layouts/*.astro  ->  src/pages/*.astro
       |
       v
Islands and Components
  src/components/**  client:* only where interaction is required
       |
       v
Server Boundaries
  src/actions/**, src/middleware.ts, src/lib/server/**
       |
       v
Data
  src/content.config.ts (build time), src/live.config.ts (request time)
```

**Data flow rules:**

- Only `src/pages/` is framework law; `components`, `layouts`, `styles`, and `lib` are a labelled team convention.
- Pages orchestrate rendering. They do not hold persistence logic or provider SDK calls.
- Server-only code lives outside anything a `client:*` island can import.
- Build-time data comes from content collections; request-time data comes from live collections, Actions, or middleware-populated `locals`.
- Build output (`dist/`, `.astro/`) is never edited by hand.

---

## Project Structure and Scalability

Read `rules/astro/project-structure.md` before adding folders, changing ownership, or moving routes.

Critical invariants remain here:

- `src/pages/` holds routes only.
- Nested folders appear when ownership or dependency pressure is observable, not pre-created as empty layers.
- `src/lib/server/` and `src/lib/client/` stay separate so a client island cannot import a secret-bearing module.
- Reserved file names (`src/middleware.ts`, `src/fetch.ts`, `src/content.config.ts`, `src/live.config.ts`, `src/actions/index.ts`, `src/env.d.ts`) keep their exact paths.
- Brownfield moves preserve public URLs, `prerender` values, and middleware order.

---

## Rendering Rules

- `output` is only `'static'` or `'server'`, and `'static'` is the default.
- `'server'` changes the default rendering behavior and nothing else.
- Per-route `prerender` is a static export, not a runtime value.
- Any on-demand route needs an adapter, and so do server islands and live collections.
- HTML streams by default on on-demand routes; response headers are set at page level.
- Prefer a server island over converting a whole page to on-demand rendering when only one fragment is personalized.

---

## Content Rules

- `src/content.config.ts` exports `collections`; each entry has a `loader` and an optional `schema`.
- `glob()` and `file()` come from `astro/loaders`; `z` comes from `astro/zod`.
- Query results are non-deterministic in order and must be sorted.
- `reference()` relations are validated when resolved.
- Live collections live in a separate `src/live.config.ts`, need a custom loader, and need an adapter.

---

## Server Boundary Rules

- Actions are public POST endpoints at `/_actions/<name>` and need the same authorization as an API route.
- Middleware exports a named `onRequest`, composes with `sequence()`, and shares request state through typed `locals`.
- Sessions need a driver; adapter defaults exist for Node, Cloudflare, and Netlify, and Vercel needs explicit configuration.
- Every environment variable is declared in `env.schema` and imported from `astro:env/client` or `astro:env/server`.
- A `context: 'client'` field can never be `access: 'secret'`.

---

## Performance Rules

- Measure the production build before changing anything, and change one lever per measurement.
- Island directives are performance decisions; each one needs a reason.
- Images go through `astro:assets`; `public/` images are never optimized.
- Fonts are self-hosted through the Fonts API.
- Keep `build.concurrency` at 1 unless a measurement justifies changing it.

See `rules/astro/performance.md` for the measured track.

---

## Verification Rules

- `astro check` is the type gate, and it needs both `@astrojs/check` and `typescript`.
- Pin TypeScript to 6.x while `astro check` is the type gate; 7.0 is rejected by the CLI.
- Format `.astro` with `prettier-plugin-astro`, and expect oxlint to lint only `<script>` blocks.
- Component tests use the Container API, and end-to-end tests use Playwright against `astro preview`.

---

## Checklist

- [ ] Astro detection confirmed, with the firing signal named.
- [ ] `output`, the adapter, and the framework integrations recorded.
- [ ] Every touched route has an explicit `prerender` decision, and dynamic routes match their mode.
- [ ] Islands carry the narrowest `client:*` directive with a stated reason, and no non-serializable prop crosses a boundary.
- [ ] Collections have a loader and a schema, and query results are sorted explicitly.
- [ ] Actions validate input and authorize; middleware results reach pages through typed `locals`; sessions have a driver.
- [ ] Environment variables are declared in `env.schema`, and no client-context field is secret.
- [ ] `astro check` passes with `@astrojs/check` and TypeScript 6.x installed.
- [ ] Each finding is labelled `official` or `hypercore-default`.

---

## Sources

> Checked 2026-11-07. Every rule above traces to the Astro research lane, which opened the official pages on 2026-11-07; the lane's source ids are kept in parentheses.

| Claim | Source |
|---|---|
| `output` accepts only `'static'` and `'server'`, `'static'` is the default, and `'server'` only switches the default (L-09, L-17) | https://docs.astro.build/en/reference/configuration-reference/ |
| Per-route `prerender` opt-in and opt-out, adapter requirement, page-level header limitation (L-09) | https://docs.astro.build/en/guides/on-demand-rendering/ |
| File-based routing, route priority order, reserved routes, `getStaticPaths()` rules, redirects and rewrites (L-06, L-07) | https://docs.astro.build/en/guides/routing/ |
| Endpoint method exports, `satisfies APIRoute`, extension-bearing URLs (L-08) | https://docs.astro.build/en/guides/endpoints/ |
| `404.astro` and on-demand-only `500.astro` (L-37) | https://docs.astro.build/en/basics/astro-pages/ |
| Only `src/pages/` is reserved; other folders are convention (L-05) | https://docs.astro.build/en/basics/project-structure/ |
| `client:*` directives, static-by-default framework components, serializable props, `.astro` as the only cross-framework surface (L-19, L-58) | https://docs.astro.build/en/guides/framework-components/ |
| Server islands, `server:defer`, fallback slots, encrypted props, the 2048-byte POST fallback (L-18) | https://docs.astro.build/en/guides/server-islands/ |
| Content layer loaders, `astro/zod` schemas, `getCollection()` order, `reference()`, live collections (L-10) | https://docs.astro.build/en/guides/content-collections/ |
| Actions as public `/_actions/<name>` endpoints and their authorization requirement (L-11, L-12) | https://docs.astro.build/en/guides/actions/ |
| Named `onRequest`, `sequence()`, `context.locals`, `App.Locals` typing (L-13) | https://docs.astro.build/en/guides/middleware/ |
| Session drivers and adapter defaults (L-14, L-17) | https://docs.astro.build/en/guides/sessions/ |
| `env.schema`, `astro:env` imports, the impossible client secret (L-15, L-16) | https://docs.astro.build/en/guides/environment-variables/ |
| `checkOrigin`, `allowedDomains`, CSP limits and unsupported combinations (L-17) | https://docs.astro.build/en/reference/configuration-reference/ |
| `src/fetch.ts` pipeline and the pathname-authorization caution (L-06, L-32) | https://docs.astro.build/en/reference/modules/astro-fetch/ |
| Route caching and `routeRules` (L-30, L-31) | https://docs.astro.build/en/guides/caching/ |
| `astro check` requirements, TypeScript 7.0 rejection, `prettier-plugin-astro` (L-51, L-40, L-28) | https://docs.astro.build/en/reference/cli-reference/ |
| oxlint lints only `<script>` blocks and has no `.astro` template linting (L-43, L-44) | https://oxc.rs/compatibility.html |
| Container API and Playwright setup (L-25, L-27) | https://docs.astro.build/en/guides/testing/ |
| Image optimization scope and `public/` exclusion (L-20, L-21) | https://docs.astro.build/en/guides/images/ |
| Fonts API self-hosting (L-24) | https://docs.astro.build/en/guides/fonts/ |
| `build.concurrency` default and caution (L-17) | https://docs.astro.build/en/reference/configuration-reference/ |
