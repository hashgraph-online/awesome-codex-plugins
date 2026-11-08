# Architecture Rules Reference

> Rule taxonomy and blocking gate summary for hypercore TanStack Start projects.

Some rules/tanstack-start are stricter than official TanStack defaults. Every rule should be understood as one of:

- **Official** — required or documented by TanStack.
- **Safety policy** — local blocking rule for security/runtime correctness.
- **Hypercore convention** — local/team preference that may exceed official defaults.

Brownfield adoption: touched files must satisfy applicable safety rules/tanstack-start and current hypercore conventions. Untouched legacy style drift can be logged as migration backlog unless it creates a safety boundary issue.

## Source Priority

1. `references/official/tanstack-start/current-docs-2026-11-04.md`
2. `references/official/tanstack-start/tanstack-start-2026-11-04.md`
3. `references/official/tanstack-start/tanstack-router-2026-11-04.md`
4. Topic rules/tanstack-start under `rules/tanstack-start/`
5. Project-local package types and tests when installed versions differ

## Blocking Safety Gates

| Surface | Classification | Block or fix when |
|---|---|---|
| Loader boundaries | Official + Safety policy | A loader assumes server-only execution or reads secrets/DB/filesystem directly |
| Server functions | Official + Safety policy | Mutation input is not validated at runtime, handler is missing, installed package/API version is not respected, or auth-required RPC lacks its own auth boundary |
| Import protection | Official + Safety policy | Import protection is disabled, config is overwritten, or server/client-only imports leak outside compiler-recognized boundaries |
| Middleware | Official + Safety policy | Client `sendContext` is trusted server-side without runtime validation; a `sendContext` value selects which rows are read or written without a separate authorization check (Official: "shape validation is not authorization"; derive the session from a server-trusted source, never from `sendContext`); or a route guard is treated as the data authorization boundary (Official: "A route guard is not a data authorization boundary") |
| SSR/hydration | Official + Safety policy | First render includes unstable values without a stabilization/fallback strategy |
| Server routes | Official + Hypercore convention | Internal app RPC is implemented as server routes instead of server functions without explicit justification |
| Route export | Official | File routes do not export the route instance as `Route` |
| Route organization | Hypercore convention | Touched app pages use flat files, omit needed route-local hooks/components, or treat route-local `-functions/` as the default server-function home |
| Project structure | Official + Hypercore convention + Safety policy | Review ignores custom route roots, hand-edits `routeTree.gen.ts`, treats shared folder conventions as official law, exposes server-only shared code to clients, or mixes server function wrappers/helpers |
| Hooks | Hypercore convention | Touched interactive page/component logic remains inline instead of moving to `-hooks/` |
| Code style | Hypercore convention | Touched files use camelCase filenames, `any`, function declarations, missing return types, or omit required Korean block comments. Exemption (Official): a framework-mandated entrypoint whose official example is a declaration keeps that declaration — `src/router.tsx` must `export function getRouter()`; the ban applies to every other file |

## Layer Architecture

```text
Route/Page UI
  -> route-local hooks / TanStack Query
  -> optional route-local -functions/<resource>.functions.ts
     or modules/<domain>/<feature>/<resource>.functions.ts
  -> modules/<domain>/<feature>/<resource>.server.ts
  -> lib/<domain>, db/<domain> repositories,
     or integrations/<provider> server-only clients
  -> database/ or external SDK
```

Rules:

- **Safety policy:** Routes must not import ORM/database clients directly.
- **Hypercore convention:** Server functions should call domain module/lib layer code for non-trivial business logic.
- **Hypercore convention:** Simple CRUD may remain in a server function only when extracting a module/lib layer would add noise.
- **Safety policy:** Auth-required server functions must not rely only on route `beforeLoad`; use middleware or handler-level auth checks.
- **Hypercore convention + Safety policy:** Split `*.functions.ts` `createServerFn` wrapper entrypoints from `*.server.ts` privileged helpers and avoid mixed barrels.

## Official-vs-Hypercore Clarifications

- TanStack Router officially supports flat, directory, and mixed route structures. Hypercore prefers route directories for app pages.
- TanStack Start docs show `src/routes`, `src/router.tsx`, generated `src/routeTree.gen.ts`, `public/`, and root `vite.config.ts` as the typical project shape; nested `src/modules`, `src/lib`, `src/integrations`, and similar shared folders are Hypercore/repo-local conventions.
- TanStack Start is stable at 1.169 and requires Vite 8 with Node ≥22.12 when it builds with Vite; the 1.168 release-candidate line and Vite 7 are not supported targets.
- TanStack Start import protection is enabled by default and its option surface is documented by the guide. Hypercore requires explicit extension when project-specific deny rules/tanstack-start are needed.
- TanStack Start server function wrappers are static-importable RPC entrypoints. Hypercore applies the official larger-app split between `.functions.ts` wrappers and `.server.ts` server-only helpers inside the `src/modules/<domain>/<feature>/` convention.
- TanStack Router with Zod v4 passes schemas directly to `validateSearch`; `@tanstack/zod-adapter` is Zod v3 only and its peer range (`zod: ^3.23.8`) conflicts with Zod 4, so a Zod 4 project must not install it.
- Server routes are an official Start feature; hypercore reserves them for HTTP semantics, not internal app RPC.
- Publishing-only static pages do not require `-hooks/`, `-components/`, or `-functions/`. Add `-hooks/` or `-components/` when interactive UI grows; add `-functions/` only for route-only server actions.

## Topic Files

- `rules/tanstack-start/project-structure.md` — Start project shape, route-root discovery, generated route tree, shared nested folder grouping, and route-local/shared server function placement.
- `rules/tanstack-start/conventions.md` — file naming, TypeScript style, import order, comment policy, and error-class rules/tanstack-start for touched files.
- `rules/tanstack-start/routes.md` — route organization, route lifecycle, search params, folder policy.
- `rules/tanstack-start/services.md` — server functions, validation, query/mutation layering.
- `rules/tanstack-start/hooks.md` — hook extraction and `useServerFn` wrapper policy.
- `rules/tanstack-start/import-protection.md` — marker files, deny rules/tanstack-start, compiler-boundary leaks.
- `rules/tanstack-start/middleware.md` — middleware types, context propagation, `sendContext` validation.
- `rules/tanstack-start/execution-model.md` — isomorphic/default execution model.
- `rules/tanstack-start/server-routes.md` — server route allowlist and justifications.
- `rules/tanstack-start/ssr-hydration.md` — SSR modes and hydration stability.
- `rules/tanstack-start/platform.md` — router/env/alias/operational setup.
- `rules/tanstack-start/validation.md` — final readback and trigger/resource checks.

## Auto-Remediation Policy

Auto-fix directly when the issue is local, reversible, and low-risk:

- Add missing route-local hooks/components for pages with interactive logic or extracted UI.
- Add or extend custom `importProtection` deny rules/tanstack-start without overwriting unrelated config.
- Add `getRouter()` fresh-instance router setup.
- Add marker imports or explicit `createServerOnlyFn` / `createClientOnlyFn` boundaries.
- Add runtime validation for untrusted server function input or `sendContext`.

Do not auto-apply broad or potentially breaking migrations without a clear user request:

- Mass route/file renames.
- Sweeping server route to server function migrations.
- SSR mode changes across many routes.
- Alias-wide import rewrites.
- Database schema edits or migration commands.

## Common Mistakes To Fix In Touched Files

| Mistake | Preferred fix |
|---|---|
| `const Route = createFileRoute(...)` | `export const Route = createFileRoute(...)` |
| Treating `loader` as server-only | Move privileged work behind `createServerFn` / `createServerOnlyFn` |
| Zod v4 search params forced through adapter | Use the direct schema; the adapter's peer range excludes Zod 4 |
| Zod v3 search params without adapter/fallback | Use `zodValidator` / `fallback` from `@tanstack/zod-adapter` |
| Server function mutation without runtime validation | Add `.validator(...)` before `.handler(...)` |
| Auth-required server function relies only on route `beforeLoad` | Add server function middleware or handler-level auth check |
| `*.functions.ts` references DB/secret helpers from a surviving export outside the handler | Split to `*.server.ts` and move usage inside handler boundary |
| `src/modules/<domain>/<feature>/index.ts` exports both `.functions.ts` and `.server.ts` | Remove barrel or split safe/server-only entrypoints |
| `createMiddleware()` with server-function-only middleware behavior | Use `createMiddleware({ type: 'function' })`; keep request middleware on `createMiddleware()` |
| Server/client imports leaking across environments | Split file, add marker, or wrap in environment function |
| Static publishing page forced into empty folders | Do not add route-local folders until interactive UI, extracted sections, or route-only server actions exist |
| Internal app RPC under server route | Prefer server function unless HTTP semantics are required |

## Completion Rule

A change is complete only when `rules/tanstack-start/validation.md` passes and any remaining official API ambiguity is recorded with exact date and source.

## Sources

> Sources checked 2026-11-04: <https://tanstack.com/start/latest/docs/framework/react/overview.md> (stable status), <https://tanstack.com/start/latest/docs/framework/react/migrate-from-release-candidate.md> (removed APIs, Vite 8), <https://tanstack.com/start/latest/docs/framework/react/guide/import-protection.md> (defaults), <https://tanstack.com/router/latest/docs/how-to/validate-search-params.md> (Zod v4 direct schema), <https://registry.npmjs.org/@tanstack/zod-adapter/latest> (Zod v3 peer range). Everything else is delegated to this package's own snapshots: `references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, and `references/official/tanstack-start/current-docs-2026-11-04.md`. Official facts verified 2026-11-04; repository-local links checked 2026-11-04.
