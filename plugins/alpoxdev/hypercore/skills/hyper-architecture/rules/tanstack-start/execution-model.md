# Execution Model

> TanStack Start runtime boundary rules/tanstack-start for server, client, and isomorphic code

---

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Loaders are isomorphic, not server-only | Official | Block privileged direct access |
| Secrets stay behind server-only boundaries | Safety policy | Block leaks |
| Prefer environment functions over ad-hoc branching | Hypercore convention | Warn/fix in touched code |

---

## Core Rule

Do not guess where code runs. In TanStack Start:

- route `loader` is isomorphic by default
- `beforeLoad` and component rendering may run on server, client, or both depending on SSR mode
- browser APIs are not automatically safe in route code
- secrets are never safe in client-reachable code

---

## Non-Negotiable Rules

| Check | Rule |
|------|------|
| `loader` directly reads secrets, DB, filesystem, or privileged SDKs? | BLOCKED. Move to `createServerFn` or `createServerOnlyFn` |
| Client-reachable code reads secret values directly from `process.env`? | BLOCKED |
| Module-scope `process.env` read in server code? | BLOCKED on edge SSR runtimes. Env is injected per request, so the read evaluates to `undefined` before the env exists |
| Browser-only APIs (`window`, `localStorage`, `document`) used in server-capable code without guard or boundary? | BLOCKED |
| Manual `typeof window` branching used where `createClientOnlyFn` / `createServerOnlyFn` / `createIsomorphicFn` is clearer? | WARNING. Prefer framework primitives |
| Shared utility mixes server-only and client-only logic in one unbounded function? | BLOCKED. Split or use explicit environment function |

---

## Pick The Right Primitive

| Need | Use |
|------|-----|
| Server RPC callable from routes/components | `createServerFn` |
| Server-only helper that must crash on client | `createServerOnlyFn` |
| Client-only helper that must crash on server | `createClientOnlyFn` |
| Same API with different server/client implementations | `createIsomorphicFn` |

---

## Loader Rule

`loader` is not a safe place for secrets by itself.

Wrong:

```ts
export const Route = createFileRoute('/users')({
  loader: () => {
    return fetch(`/api/users?key=${process.env.SECRET_KEY}`)
  },
})
```

Right:

```ts
const getUsersSecurely = createServerFn().handler(async () => {
  return fetch(`/api/users?key=${process.env.SECRET_KEY}`)
})

export const Route = createFileRoute('/users')({
  loader: () => getUsersSecurely(),
})
```

---

## Security Rules

- Secrets, DB clients, filesystem access, and privileged SDKs stay behind `createServerFn` or `createServerOnlyFn`
- Read env per request: `process.env` belongs inside `.handler()`, middleware `.server()`, server-route handlers, or another per-request callback. This is a correctness rule as well as a leak rule — on Cloudflare Workers and other edge SSR runtimes a module-scope read is `undefined` even on the server, because env is injected at request time
- Browser APIs stay behind `createClientOnlyFn`, `ClientOnly`, or client-only components/hooks
- If code can be imported by the client, assume it is public unless import protection and execution boundaries prove otherwise

---

## Review Checklist

- No `loader` contains secret or privileged access directly
- Environment-specific helpers use TanStack Start primitives
- Server-only code is not reachable from client code
- Browser-only code is not reachable during server render

## Sources

> Sources checked 2026-11-04: <https://tanstack.com/start/latest/docs/framework/react/guide/execution-model.md> (isomorphic-by-default, loaders are isomorphic), <https://tanstack.com/start/latest/docs/framework/react/guide/environment-variables.md> (read env per request, not at module scope). Official TanStack behavior is otherwise delegated to this package's own snapshots: `references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, and `references/official/tanstack-start/current-docs-2026-11-04.md` (official facts verified 2026-11-04). Repository-local links checked 2026-11-04.
