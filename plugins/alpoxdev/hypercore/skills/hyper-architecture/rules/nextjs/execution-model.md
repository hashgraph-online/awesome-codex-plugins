# Execution Model

> Next.js Server and Client Component boundary rules.

---

## Core Rule

Do not guess where code runs.

- Server Components are the default in App Router.
- Client Components need `'use client'` at entry-point files that are rendered from Server Components.
- Once a file is marked `'use client'`, its imports and child components become part of the client module graph.
- Client Components can be prerendered, so they must still avoid server secrets and server-only APIs.
- Server-only code must stay out of the client environment.

## Default Strategy

1. Start with a Server Component.
2. Add `'use client'` only for state, event handlers, effects, browser APIs, or client-only hooks.
3. Keep the client boundary as low as possible in the tree.
4. Pass only serializable, minimal props from server to client.
5. Keep privileged reads in server-only modules or a DAL.

## Hard Rules

| Check | Rule |
|---|---|
| Interactive code without `'use client'` | BLOCKED |
| High-level layout or root marked `'use client'` without real need | BLOCKED |
| Client Component imports DB clients, secret env, `cookies()`, `headers()`, or server-only helpers | BLOCKED |
| Non-serializable or broad raw records passed from Server Components to Client Components | BLOCKED |
| Server-only helper lacks `import 'server-only'` or equivalent boundary clarity | WARNING |
| Provider rendered broader than needed | WARNING. Render providers as deep as possible |

## Serializable Props Rule

Props passed from Server Components to Client Components must be serializable and intentionally small.

Prefer:

- DTOs
- small view models
- explicit primitive props
- IDs that let a Client Component call an approved action or route when client refresh is truly needed

Avoid:

- whole ORM records
- class instances, functions, symbols, or non-serializable values
- secrets
- internal fields the UI does not need

## Provider Placement

Context providers should wrap only the subtree that needs them. This preserves more of the tree for static optimization and keeps client bundles smaller.

React 19.3 relaxes one part of that rule: a Server Component can import and render a Context object from a `'use client'` module directly, as `<Context value={...}>`, without an intermediate provider component. Use the direct form when the wrapper only forwards a value, because it removes a component from the tree without widening the client boundary. The boundary is still the `'use client'` module that defines the Context, so keep the value it receives serializable and minimal.

## Navigation and State Preservation

With Cache Components enabled, Next.js wraps visited routes in React `<Activity mode="hidden">` instead of unmounting them. Client state survives a navigation and reappears when the user returns.

- Effects are cleaned up while a route is hidden and recreated when it becomes visible again. A hook that assumes a single mount lifetime across navigation is wrong under this model.
- Assertions that depend on unmount cleanup, such as dropdown or dialog dismissal, must be written against the hide/visible transition instead.
- Next.js keeps a few recently visited routes hidden and removes older ones from the DOM, so do not rely on hidden routes staying mounted indefinitely.

## Server-Only and Client-Only Protection

Use `import 'server-only'` for modules that must never run in the client environment:

- DAL modules
- DB access
- secret-bearing SDK wrappers
- authorization helpers that must stay server-side

Use client-only wrappers for browser-dependent third-party components that do not expose a compatible client entry point.

## Review Checklist

- `'use client'` appears only where needed
- Client Components do not reach server-only modules
- Props crossing the server/client boundary are narrow and serializable
- Providers are placed as deep as practical, and value-only wrappers use direct `<Context value>` rendering where the React 19.3 form applies
- Effects and cleanup logic account for hidden routes instead of assuming unmount
- Third-party browser-only UI is wrapped behind a clear Client Component boundary

## Sources

> Checked 2026-11-04 against `https://nextjs.org/docs/app/getting-started/server-and-client-components`, `https://nextjs.org/docs/app/guides/server-and-client-boundary`, `https://nextjs.org/docs/app/api-reference/config/next-config-js/cacheComponents`, `https://nextjs.org/docs/app/guides/preserving-ui-state`, and `https://react.dev/blog/2026/09/09/react-19-3`. The dated snapshot is `references/official/nextjs/current-docs-2026-11-04.md`.
