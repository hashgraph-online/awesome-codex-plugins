# Client Hooks and Orchestration Boundaries

> Next.js hook guidance for client orchestration without crossing server, data, or privileged runtime layers.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Hooks only run in Client Components or client modules | React/Next.js fact | Add or narrow `'use client'` at the client entry point |
| Client hooks cannot import server-only code | Safety policy | Block DB, private env, `cookies()`, `headers()`, DAL, and provider secret imports |
| Hooks orchestrate UI state and client-side effects | Hypercore local convention | Apply to touched interactive UI |
| Server reads and writes use Server Components or Server Actions first | Official + safety policy | Do not tunnel privileged data through hooks |

## Boundary Rule

Hooks are client orchestration boundaries, not server/data layers. A hook may coordinate UI state, browser APIs, optimistic UI, transitions, client cache libraries, and calls to Server Actions. It must not own database access, Drizzle queries, private env, cookies/headers reads, provider SDK secrets, or authorization decisions.

Default flow:

```text
Client Component
  -> useFeatureHook()
  -> Server Action or client-safe query/cache call
  -> server-only service/DAL
  -> DB or integration
```

For initial page data, prefer Server Components and pass serializable, minimal props into the client leaf. Use client hooks for interaction after hydration or genuinely browser-only data.

## Placement

Use the repository's existing convention first. Common Hypercore local shapes:

```text
src/app/dashboard/_hooks/use-dashboard-filters.ts
src/modules/billing/invoices/hooks/use-invoice-selection.ts
src/components/data-table/use-column-visibility.ts
```

Segment-local hooks that only serve one App Router segment can live under `_hooks/` inside that segment. Cross-route hooks belong under a domain module or shared component folder.

## Hook Responsibilities

Good hook responsibilities:

- UI state, reducers, refs, and browser events
- form pending/error state and optimistic client state
- `useActionState`, transitions, and Server Action invocation state
- client cache invalidation wrappers when the project uses a client cache library
- derived view state from already-safe DTOs

Responsibilities that should stay server-side:

- Drizzle queries, repository calls, transactions, and schema migration concerns
- auth/authz decisions for protected data or mutations
- private env reads, `cookies()`, `headers()`, filesystem, and server-only provider clients
- raw DB row shaping for security-sensitive output
- Route Handler or Server Action replacement for public HTTP contracts

## Navigation and Effect Lifecycle

With Cache Components enabled, a route you navigate away from is hidden with React `<Activity mode="hidden">` rather than unmounted. Hooks must be written for that model:

- Effects and subscriptions are cleaned up when the route is hidden and recreated when it becomes visible again. A hook that registers a listener once per component lifetime loses it after a navigation and never restores it unless it is effect-based.
- Local state survives a round trip, so a hook that expects a closed dropdown or a cleared draft after navigation will not see that reset. Trigger the reset explicitly on the visibility transition when the UX needs it.
- Do not rely on hidden routes staying mounted forever; Next.js keeps only a few recently visited routes hidden.

## Server Action Invocation State

Server Actions are dispatched one at a time per client, so a client hook cannot assume two calls run concurrently. A hook that fires several actions from one handler gets queued execution, and `Promise.all` does not change that. Sequence dependent writes through one composite action, or accept that later calls wait.

## Internal Order

For touched non-trivial hooks, prefer a consistent order:

```typescript
export const useInvoices = (): UseInvoicesReturn => {
  // 1. Local state and refs
  // 2. Context/global client stores
  // 3. Server Action state or client cache bindings
  // 4. Handlers and callbacks
  // 5. Memoized derived view data
  // 6. Effects
  // 7. Return object
}
```

## Review Checklist

- [ ] Hook file is client-reachable only when needed and does not force broad root-level `'use client'`.
- [ ] Hook imports no DB client, Drizzle schema, private env, `server-only`, `cookies()`, `headers()`, or privileged provider client.
- [ ] Initial Server Component data is not refetched client-side without a browser-only reason.
- [ ] Server Action calls still validate and authorize server-side; hook-level checks are UX aids only.
- [ ] Hook does not assume parallel Server Action dispatch or a fresh mount after navigation.
- [ ] Effects re-register after a hidden route becomes visible again.
- [ ] Hook returns client-safe DTO/view state, not internal records.
- [ ] Segment-local hooks stay in `_hooks/`; cross-route hooks move to a shared domain/component folder.

## Sources

> Checked 2026-11-04 against `https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents`, `https://nextjs.org/docs/app/guides/preserving-ui-state`, `https://nextjs.org/docs/app/guides/server-actions`, and `https://nextjs.org/docs/app/getting-started/server-and-client-components`. The dated snapshot is `references/official/nextjs/current-docs-2026-11-04.md`.
