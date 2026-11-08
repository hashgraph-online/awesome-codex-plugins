# Execution Model

> Runtime-boundary rules/vite for Vite + TanStack Router route code

---

## Core Rule

Do not treat a route module or loader as a private server boundary.

In a typical SPA-only Vite app, loaders run in the browser during navigation. If the repo later adds SSR or manual server rendering, the same loader may also run during server render. Write loader code so it is safe in both cases.

---

## Non-Negotiable Rules

| Check | Rule |
|------|------|
| Loader or route module reads secrets, DB clients, filesystem, or privileged SDKs directly? | BLOCKED |
| Client-reachable code reads non-`VITE_` env values? | BLOCKED |
| Browser-only APIs used at module scope or in shared route utilities without a client boundary? | BLOCKED |
| Module-level side effects depend on browser globals? | BLOCKED |
| Loader performs direct networking that duplicates service-layer logic? | BLOCKED. Move networking to `services/` |

---

## Safe Patterns

- Route loaders call `queryClient.query({ ...options, staleTime: 'static' })` with service-owned query options
- Browser-only behavior lives inside components, hooks, effects, or explicit client-only wrappers
- Public runtime config uses `import.meta.env.VITE_*`
- Private secrets stay behind a real backend/API boundary

---

## Review Checklist

- No loader or route module reads secrets or private env values directly
- No route code imports DB clients or privileged SDKs
- Browser-only code does not execute at module scope
- Loader networking stays behind service/query-option helpers

---

## Sources

> The client-reachability of route modules and loaders and the `VITE_`-only client env rule stated here come from the dated snapshot recorded in `references/official/vite/current-docs-2026-11-04.md`, whose own verification date is 2026-11-04. The server-render caveat and the routing-loader-networking-through-service-helpers rule are this package's own guidance and Hypercore/repo-local conventions, not facts taken from the snapshot. No page was re-fetched for this file. Rule text and repository-local paths checked 2026-11-04.
