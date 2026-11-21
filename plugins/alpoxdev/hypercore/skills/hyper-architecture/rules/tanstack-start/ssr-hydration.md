# SSR And Hydration

> Route SSR mode and hydration-safety rules/tanstack-start

---

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Route SSR options and `ClientOnly` are official Start concepts | Official | Use deliberately |
| Deterministic first render | Safety policy | Block hydration-unsafe output |
| Prefer stabilization before disabling SSR | Hypercore convention | Apply to touched routes |

---

## Core Rule

If server HTML and client render can differ, treat it as a design problem, not a harmless warning.

---

## Non-Negotiable Rules

| Check | Rule |
|------|------|
| Component renders unstable values on first render (`Date.now()`, random IDs, locale-dependent text, viewport-only branching)? | BLOCKED unless stabilized |
| Browser-only widget rendered during SSR without `ClientOnly` or SSR restriction? | BLOCKED |
| Route uses `ssr: false` or `ssr: 'data-only'` without a deliberate fallback strategy? | BLOCKED |
| Root disables SSR without understanding `shellComponent` behavior? | BLOCKED |

---

## Preferred Fix Order

1. Make server and client output deterministic
2. Compute once on the server and hydrate from loader data
3. Use `ClientOnly` for genuinely browser-only UI
4. Use route `ssr: 'data-only'` or `ssr: false` only when needed

---

## Approved Patterns

- Locale/timezone-sensitive UI should use a deterministic server value, typically cookie-backed
- Client environment discovery may set cookies after hydration for future SSR requests
- Unstable widgets may be wrapped in `ClientOnly`
- For a single value that must differ before hydration, prefer `useHydrated()` from `@tanstack/react-router`. It is `false` during SSR and the first client render and `true` after hydration, which is narrower than wrapping a whole subtree in `ClientOnly`
- `ssr` also takes a function: `ssr: ({ params, search }) => false | 'data-only' | true`. It runs only on the server for the initial request and is stripped from the client bundle; `params` and `search` arrive as either `{ status: 'success', value }` or `{ status: 'error', error }`, so the callback must handle the error branch
- A child route can only make the inherited `ssr` mode more restrictive: `true` may become `'data-only'` or `false`, and `'data-only'` may become `false`, never the reverse
- The first route with `ssr: false` or `ssr: 'data-only'` renders `pendingComponent` (or `defaultPendingComponent`) for at least `minPendingMs`
- Use `pendingComponent` when SSR mode changes route rendering behavior
- If the root route limits SSR, understand that `shellComponent` still renders the HTML shell

---

## Review Checklist

- No hydration-unsafe first render output
- `ClientOnly` is used intentionally, not as a blanket escape hatch
- `ssr` mode is explicit for unstable routes, and a functional `ssr` handles the `{ status: 'error' }` branch
- Hydration-sensitive single values use `useHydrated()` rather than a subtree-wide `ClientOnly`
- Fallback and shell behavior are understood for reduced SSR routes

## Sources

> Sources checked 2026-11-04: <https://tanstack.com/start/latest/docs/framework/react/guide/selective-ssr.md> (`ssr` modes, functional form, inheritance restrictiveness, `pendingComponent`/`minPendingMs`), <https://tanstack.com/start/latest/docs/framework/react/guide/execution-model.md> (`useHydrated`), <https://tanstack.com/start/latest/docs/framework/react/guide/hydration-errors.md> (mismatch sources and the cookie-backed fix). Official TanStack behavior is otherwise delegated to this package's own snapshots: `references/official/tanstack-start/tanstack-start-2026-11-04.md`, `references/official/tanstack-start/tanstack-router-2026-11-04.md`, and `references/official/tanstack-start/current-docs-2026-11-04.md` (official facts verified 2026-11-04). Repository-local links checked 2026-11-04.
