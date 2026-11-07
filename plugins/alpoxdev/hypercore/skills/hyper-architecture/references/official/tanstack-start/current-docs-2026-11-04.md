# TanStack Start Current Docs Snapshot

- last_verified_at: 2026-11-04
- source: TanStack official Start docs pages fetched directly (the `guide/<page>.md` URLs below) plus published package types from `@tanstack/start-client-core@1.170.39` and `@tanstack/start-plugin-core@1.171.55`
- use_when: Start/Router API behavior, Start plugin config, import protection, execution boundaries, middleware, or server-function and server-route API shape affects an architecture decision
- authority: Official TanStack docs for API facts; Hypercore conventions remain in `rules/tanstack-start/`
- supersedes: the retired 2026-09-22 and 2026-06-02 snapshots (see "Corrected from earlier snapshots")

## Contents

- [Corrected from earlier snapshots](#corrected-from-earlier-snapshots)
- [Server functions](#server-functions)
- [Execution boundaries](#execution-boundaries)
- [Global Start configuration](#global-start-configuration)
- [CSRF protection](#csrf-protection)
- [Middleware](#middleware)
- [Import protection](#import-protection)
- [Server routes](#server-routes)
- [Drift handling](#drift-handling)
- [Sources](#sources)

## Corrected from earlier snapshots

- **`.inputValidator(...)` is removed, not deprecated.** Earlier snapshots recorded it as "deprecated but still resolving at runtime". `@tanstack/react-start@1.169.0` (2026-10-12) removed it from `createServerFn` and `createMiddleware`; the release note reads "Remove the deprecated `.inputValidator()` from `createServerFn` and `createMiddleware`. Use `.validator()`, which takes the same validator."
- Evidence, re-checked 2026-11-04:
  - Types: `start-client-core@1.170.39`'s declarations carry zero `inputValidator` occurrences.
  - Docs: `guide/server-functions.md` and `guide/middleware.md` use `.validator(...)` only, and `guide/middleware.md`'s comparison table lists `Input Validation | No | Yes (`.validator()`)`.
  - Migration page: the removed-API table maps `.inputValidator()` on server functions and middleware to `.validator()`.
- **The earlier "still resolves at runtime" record is now false.** It described `createServerFn.ts:921`'s `options.validator ?? options.inputValidator` fallback at commit `fe7f1fd0e6ef73c3f341dd2338b406749538a85d`; that fallback no longer exists. The earlier correction that `.validator(...)` was canonical was right; its claim that the alias kept working was a fact about that commit only.
- **Start is stable, not in Release Candidate.** The overview page now opens with "TanStack Start is stable."
- **Vite 8 is required, and Node ≥22.12.** `@tanstack/react-start@1.169.4` declares `peerDependencies.vite >=8.0.0` and `engines.node >=22.12.0`; the release note says "Vite 7 is no longer supported."
- The 2026-06-02 snapshot's deeper history, where an earlier pass recorded the inverse of the docs three days after the rename merged, is retained only as a caution: a dated snapshot is only as good as the pass that produced it.

## Server functions

- `createServerFn()` defines a server function. `method` defaults to `GET`; `createServerFn({ method: 'POST' })` is the other form. `Method` is exactly `'GET' | 'POST'` — `packages/start-client-core/src/createServerFn.ts:449` reads `export type Method = 'GET' | 'POST'`. No other verb is available.
- `.handler(...)` is the terminal builder call: it ends the chain and defines the implementation. `.validator(...)` attaches input validation and `.middleware([...])` attaches middleware before it. There is no `.inputValidator(...)`.
- The `strict` option exists and defaults to `strict: true`. It controls TypeScript-level serialization checks; `createServerFn({ strict: false })` and the granular `strict: { input: false }` / `strict: { output: false }` forms opt out. The docs warn that `strict: false` only relaxes the type checks — the runtime serialization layer still has to handle the values.
- File organization: the docs present the `*.functions.ts` (server function wrappers) / `*.server.ts` (server-only helpers) split as "one approach", not a mandate. Import protection does **not** enforce that naming — only `*.server.*` and `*.client.*` are enforced patterns.
- Static imports of server functions are safe; the docs warn against dynamic imports for them (`guide/server-functions.md:150`: "Avoid dynamic imports for server functions").
- Server functions are same-origin app RPC endpoints. They are callable from loaders, components, hooks, other server functions, and event handlers; `useServerFn()` is the React wrapper when hook ergonomics are needed.

## Execution boundaries

- `createServerFn`, `createServerOnlyFn`, `createClientOnlyFn`, and `createIsomorphicFn` are the official execution-control primitives.
- `createIsomorphicFn()` composes one function with per-environment implementations via `.server(...)` and `.client(...)`. A missing side is a no-op returning `undefined`, not an error.
- `createServerOnlyFn(...)` and `createClientOnlyFn(...)` enforce environment-bound execution and throw descriptive runtime errors when called in the wrong environment.
- Environment functions are tree-shaken per bundle: `.client()` bodies are excluded from the server bundle and vice versa.
- Loaders are isomorphic, not server-only — the docs' own "Common Problems" section calls out assuming otherwise as the classic secret-leak mistake.

## Global Start configuration

- `src/start.ts` is **not** part of the default Start template; it is created when global middleware or Start-level options are needed.
- The canonical shape is the callback form: `export const startInstance = createStart(() => ({ requestMiddleware: [...], functionMiddleware: [...] }))`. The source signature is `createStart(getOptions: () => StartInstanceOptions | Promise<StartInstanceOptions>)`.
- The real option surface is `serializationAdapters`, `defaultSsr`, `requestMiddleware`, `functionMiddleware`, and `serverFns: { fetch }` (`packages/start-client-core/src/createStart.ts:15-50`). `requestMiddleware` runs for every request handled by Start; `functionMiddleware` runs for every server function.
- These options are **not new**. They predate the retired 2026-06-02 snapshot — that file simply never listed them, so the omission was the skill's own, not upstream drift.

## CSRF protection

- `createCsrfMiddleware()` is the named API for protecting server functions from cross-site requests. The guide's recommended install carries a filter: `createCsrfMiddleware({ filter: (ctx) => ctx.handlerType === 'serverFn' })`, because "by default, `createCsrfMiddleware()` validates every request handled by the middleware". It verifies `Sec-Fetch-Site`, `Origin`, or `Referer` and rejects requests that cannot be proven same-origin; requests with none of the three are rejected unless `allowRequestsWithoutOriginCheck: true`. Options: `filter`, `origin`, `secFetchSite` (default `'same-origin'`), `referer` (default `true`), `allowRequestsWithoutOriginCheck` (default `false`), `failureResponse` (default `403 Forbidden`). The guide documents `filter`, `origin`, and `allowRequestsWithoutOriginCheck`; the rest are type-level facts.
- **Start installs this middleware automatically for server functions when the app does not define `src/start.ts`.** The trap: creating `src/start.ts` silently drops that automatic installation, so the file must add `requestMiddleware: [createCsrfMiddleware()]` explicitly. Start logs a development warning for server function requests when `src/start.ts` exists without it.

## Middleware

- Two middleware types. Request middleware uses `createMiddleware()`; `createMiddleware({ type: 'request' })` is allowed but the request type is the default. Server function middleware uses `createMiddleware({ type: 'function' })` and can define `.client(...)` and `.server(...)` phases.
- Server function middleware validation uses `.validator(...)` as well, and `inputValidator` was removed from `createMiddleware` in the same 1.169.0 release. Do not confuse middleware `.validator(...)` with server-function `.validator(...)`: they belong to different chain objects and different data contexts.
- A route guard is not a data authorization boundary. Middleware and `beforeLoad` can deny access to a page, but data returned by a server function or server route still needs its own check against the session principal.
- `sendContext` is explicit and one-directional per hop. Client context is **not** sent to the server by default; it must be passed through `next({ sendContext: {...} })`. Anything the client can send, the client can lie about, so values arriving via `sendContext` are client-provided data.
- **"Shape validation is not authorization."** (`guide/middleware.md:348`.) A parsed UUID or number is a well-formed identifier, not an authorized one. When the value selects which rows get read or written — a query key, filter, or path parameter — the session principal's access to it must be verified separately, otherwise a logged-in user can rewrite the value in their own request and reach other tenants' data.
- The docs' required pattern (`guide/middleware.md:377`): "Always derive the session itself from a server-trusted source (a cookie + DB lookup in `authMiddleware`), never from `sendContext`. Anything the client can send, the client can lie about."

## Import protection

- **Status: documented, no Experimental banner.** The page opens with "Import protection prevents server-only code from leaking into client bundles and client-only code from leaking into server bundles. It runs inside TanStack Start and is enabled by default." Documented options: `enabled`, `behavior`, `log`, `include`, `exclude`, `maxTraceDepth`, environment `files`/`specifiers`/`excludeFiles`, `ignoreImporters`, `onViolation`.
- Enabled out of the box. Documented defaults: `enabled: true`; `behavior: { dev: 'mock', build: 'error' }` (`'mock'` warns and substitutes a mock module, `'error'` fails the build); `log: 'once'` (deduplicates repeated violations); scope `include` = Start's `srcDirectory`; `maxTraceDepth: 20`.
- Default deny rules: `client.files` = `['**/*.server.*']`, `server.files` = `['**/*.client.*']`, `client.specifiers` = the framework server specifiers, `server.specifiers` = `[]`, and both `excludeFiles` = `['**/node_modules/**']`.
- **Replace vs additive is the trap.** Per the option table (`guide/import-protection.md:561-567`):
  - `client.specifiers` is **additive with defaults** — providing it extends the built-in list.
  - `client.files`, `client.excludeFiles`, `server.files`, `server.specifiers`, and `server.excludeFiles` **replace** the defaults. (`server.specifiers` is listed as "replaces defaults", but its default is `[]`, so it is not additive in practice.)
  - `excludeFiles` **fully replaces** `['**/node_modules/**']`. To exclude extra paths while still skipping `node_modules`, pass both: `excludeFiles: ['**/node_modules/**', '**/vendor/**']`.
  - Setting `client.files` without carrying `'**/*.server.*'` therefore silently drops the default deny rule.
- `excludeFiles: []` re-enables resolved-target checking in locations the defaults skip, such as `node_modules`. It is a deliberate opt-in, not a recommendation.
- Type-only imports and re-exports are ignored because they are erased at runtime; mixed imports still count when they carry at least one runtime value.
- Side-effect marker imports remain available for explicit boundaries: `@tanstack/react-start/server-only` and `@tanstack/react-start/client-only`.
- `mockAccess` (`'error' | 'warn' | 'off'`, optional) exists in `@tanstack/start-plugin-core@1.171.55`'s `schema.d.ts` but is **absent from the import-protection guide**. It is a real schema option that the docs do not document, so it must be labeled as such whenever it is cited and never presented as a documented option.
- Dev-mode violations can be false positives because build mode defers the check until after tree-shaking; confirm with a production build before changing a boundary.

## Server routes

- Server routes are declared by adding `server` to a `createFileRoute(...)(...)` call in a route file, and follow Router's file-based routing conventions.
- The `server` property contains `handlers` — either an object mapping HTTP methods to handler functions, or a function that receives `createHandlers` for handlers that need middleware composition — and an optional `middleware` array that applies route-level middleware to all handlers.
- Pathless layout routes and break-out routes are supported for grouping server route middleware: a pathless layout adds middleware to a group of routes, and a break-out route escapes parent middleware.
- Duplicate route paths with duplicate HTTP methods are invalid; wildcard/splat routes use the trailing `$` file-route convention.

## Drift handling

- This is a dated official-doc snapshot, not a permanent rulebook. Its filename date and `last_verified_at` agree by construction; if either changes, both change together.
- Refresh trigger: re-verify when the official doc pages listed below change, or on an advisory check. Do **not** key it on local package versions moving beyond a pinned set — router/start absorb breaking changes in PATCH releases, so a version-based trigger both over- and under-fires.
- If local installed package types disagree with this file, run typecheck and record the project-specific exception rather than editing this snapshot.
- `src/modules`, `src/lib`, `src/db`, `src/server`, `src/integrations`, and `src/config` grouping remain Hypercore conventions, not official TanStack requirements. The `.functions.ts` / `.server.ts` split is official guidance, but enforcing it inside `src/modules/<domain>/<feature>/` nested folders is a Hypercore convention.

## Sources

> Sources checked 2026-11-04. Every page and source below was fetched directly on 2026-11-04 for this snapshot. The `guide/` path segment is required; the same pages without it return 404. Line numbers cited are positions in an older fetched copy, so they will drift as the pages change — the quoted text is the stable anchor.

- <https://tanstack.com/start/latest/docs/framework/react/guide/server-functions.md>
- <https://tanstack.com/start/latest/docs/framework/react/guide/middleware.md>
- <https://tanstack.com/start/latest/docs/framework/react/guide/authentication-server-primitives.md>
- <https://tanstack.com/start/latest/docs/framework/react/migrate-from-release-candidate.md>
- <https://tanstack.com/start/latest/docs/framework/react/guide/import-protection.md>
- <https://tanstack.com/start/latest/docs/framework/react/guide/server-routes.md>
- <https://tanstack.com/start/latest/docs/framework/react/guide/code-execution-patterns.md>
- <https://tanstack.com/start/latest/docs/framework/react/guide/environment-functions.md>
- <https://registry.npmjs.org/@tanstack/start-client-core/-/start-client-core-1.170.39.tgz>
- <https://registry.npmjs.org/@tanstack/start-plugin-core/-/start-plugin-core-1.171.55.tgz>
- <https://registry.npmjs.org/@tanstack/react-start/latest>
