# Route Structure

> Route organization, file-route lifecycle, search validation, and hypercore page folder conventions.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| File route instance exported as `Route` | Official | Block if missing |
| Search params validated when consumed | Official + Safety policy | Block if unvalidated user input affects behavior |
| Zod version matched to its validation path | Official | Block `@tanstack/zod-adapter` alongside Zod 4 |
| `beforeLoad` before `loader` lifecycle | Official | Use for auth/context/redirect decisions |
| Mixed flat/directory routes supported by Router | Official | Do not claim flat routes are invalid TanStack usage |
| Route-directory preference for app pages | Hypercore convention | Apply to touched app pages unless official defaults requested |
| `-hooks/` and `-components/` for pages with interactive logic or growing UI | Hypercore convention | Apply when route-local orchestration or UI extraction exists |
| `-functions/` only for route-local server function exceptions | Hypercore convention + Safety policy | Use domain modules by default; keep route-only actions local |

## Publishing-Only Exception

Publishing-only pages are static display pages with no interactive logic and no server integration.
Examples: terms, privacy, about, simple marketing content.

- They do **not** require `-components/`, `-hooks/`, or `-functions/`.
- If interactive logic is added, create `-hooks/` and route-local components as needed.
- When server integration is added, the default is to call server functions from `src/modules/<domain>/<feature>/` via route-local hooks. Use `-functions/` only for truly single-route actions.

## Hypercore Route Folder Shape

For global Start project structure, actual route-root discovery, generated `routeTree.gen.ts`, and shared nested folder policy, read `rules/tanstack-start/project-structure.md`.

```text
routes/<page>/
├── index.tsx          # page UI only
├── route.tsx          # layout/beforeLoad/loader when needed
├── -components/       # page-local components when UI grows or repeats
├── -hooks/            # page-local interactive/query orchestration
└── -sections/         # optional for large page sections
```

Route-local server function exception:

```text
routes/<page>/
└── -functions/
    ├── <resource>.functions.ts
    ├── <resource>.server.ts
    └── <resource>.schemas.ts
```

Official TanStack Router supports flat route files. The shapes above are hypercore maintainability conventions. `-`-prefixed folders such as `-components/`, `-hooks/`, and `-functions/` align with Router's default ignore prefix and are used as co-location folders that route generation does not treat as route files.

## File Route Export

```typescript
import { createFileRoute } from '@tanstack/react-router'

export const Route = createFileRoute('/users/')({
  component: UsersPage,
})
```

- The route instance must be exported as `Route`.
- `createFileRoute` path strings are generated/updated by the router plugin or CLI.

## Route Tokens and Code Splitting

- `routeToken` (default `route`) identifies the layout route file; `indexToken` (default `index`) identifies the index route file (Official).
- Both tokens accept a regex — `{ "regex": "...", "flags": "..." }` in `tsr.config.json`, or a native `RegExp` inline — and the regex is matched against the entire final segment of the route path (Official).
- A segment can be escaped with square brackets to keep it literal: with `indexToken: { "regex": "[a-z]+-page" }`, a literal `home-page` segment is named `[home-page].tsx` (Official).
- `autoCodeSplitting` is a TanStack Router bundler-plugin option, opt-in and defaulting to `false` (the next major release defaults it to `true`) (Official).
- It cannot be passed through `tanstackStart()`: the Start plugin omits `autoCodeSplitting` and `target` from the router config it accepts (Official).

## Route Lifecycle

| Step | Official behavior | Use for |
|---|---|---|
| `validateSearch` | Runs during matching/search validation | Parse and validate URL search state |
| `beforeLoad` | Runs serially before route loading | Auth, redirects, context extension |
| `loader` | Runs in route loading phase and can be cached/preloaded | Data loading; do not treat as server-only |
| `pendingComponent` | Optional threshold-based pending UI | Slow critical loader UX |
| `errorComponent` | Handles route lifecycle/render errors | Recoverable route errors |

## Search Transform

The current search-transform API is `search.middlewares` on route options: functions that transform search params when generating new links for that route or its descendants (Official).

```typescript
import { createFileRoute, retainSearchParams } from '@tanstack/react-router'

export const Route = createFileRoute('/')({
  search: {
    middlewares: [retainSearchParams(['rootValue'])],
  },
})
```

- Router ships `retainSearchParams` (keep a parent's params in descendant links) and `stripSearchParams` (drop params that hold their default value) for the two common cases (Official).
- `preSearchFilters` / `postSearchFilters` are deprecated and absent from the current search-params guide; the API reference still lists both as `⚠️ deprecated, use search.middlewares instead` (Official). Treat them as deprecated, not removed.

## Search Validation

When a route consumes search params, validate them.

`validateSearch` is a planning callback: it must be deterministic and side-effect-free for the same input, and it must not navigate or mutate application or router state (Official).

Zod v4 official path:

```typescript
import { z } from 'zod'

const searchSchema = z.object({
  page: z.number().default(1),
})

export const Route = createFileRoute('/products/')({
  validateSearch: searchSchema,
  component: ProductsPage,
})
```

Zod v3 official path:

```typescript
import { zodValidator, fallback } from '@tanstack/zod-adapter'
import { z } from 'zod'

const searchSchema = z.object({
  page: fallback(z.number(), 1).default(1),
})

export const Route = createFileRoute('/products/')({
  validateSearch: zodValidator(searchSchema),
  component: ProductsPage,
})
```

`@tanstack/zod-adapter` is Zod v3 only: its `peerDependencies` pin `zod: ^3.23.8`, which conflicts with Zod 4. On a Zod 4 project, do not install the adapter at all, even to keep a uniform import style. Pass the schema directly. On Zod 3 the adapter remains the official path. If a project standardizes on `zodValidator`, that only works while it stays on Zod 3 and must be labelled as a hypercore convention in the project notes.

## Loader Boundary Rule

- Loaders are isomorphic in TanStack Start.
- Do not access secrets, database clients, filesystem, or privileged SDKs directly in loader code.
- Move privileged work behind `createServerFn` in route-local exception `-functions/<resource>.functions.ts` or the default shared location `src/modules/<domain>/<feature>/<resource>.functions.ts`.
- Import `*.server.ts` helpers only inside `*.functions.ts` handlers; routes/components/hooks statically import the server function wrapper.

## Validation Checklist

- [ ] Touched file routes export `Route`.
- [ ] Search params are validated with a pattern appropriate to the installed Zod version.
- [ ] `beforeLoad` holds auth/context/redirect logic that must run serially.
- [ ] Loader code contains no direct secret/DB/filesystem access.
- [ ] Publishing-only pages were not forced into empty route-local folders.
- [ ] Pages with interactive logic have route-local hooks/components or a documented reason not to.
- [ ] Route-local server functions use `.functions.ts` / `.server.ts` / schema split or have been promoted to `src/modules/<domain>/<feature>/`.

## Sources

> Sources checked 2026-11-04: <https://tanstack.com/router/latest/docs/guide/search-params.md> (Zod v4 direct schema, `search.middlewares`), <https://tanstack.com/router/latest/docs/how-to/validate-search-params.md> (adapter unnecessary on Zod v4), <https://registry.npmjs.org/@tanstack/zod-adapter/latest> (Zod v3 peer range). Official TanStack behavior is otherwise delegated to this package's own snapshots: `references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, and `references/official/tanstack-start/current-docs-2026-11-04.md` (official facts verified 2026-11-04). Repository-local links checked 2026-11-04.
