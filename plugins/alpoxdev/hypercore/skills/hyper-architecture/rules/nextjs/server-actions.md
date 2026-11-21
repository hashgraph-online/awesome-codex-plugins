# Server Actions

> `use server` rules/nextjs for mutations, validation, dispatch order, freshness, and security.

---

## Core Rule

Treat every Server Action as a reachable POST entry point.

For App Router mutations that originate from app UI, Server Actions are the default surface.

This means:

- validate input
- authenticate the caller
- authorize resource access
- return only what the UI needs
- refresh or revalidate affected data intentionally

Do not rely on page-level UI gating alone.

## Placement

- Use a dedicated top-level `'use server'` file for reusable actions, especially actions imported into Client Components.
- Inline actions inside a Server Component are acceptable when tightly bound to that route and the closure is intentional.
- Repeated DB/auth logic should move into a server-only DAL or helper.
- If the write comes from internal app UI and does not need an HTTP-native contract, prefer a Server Action over `route.ts`.

## Sequential Dispatch

Next.js dispatches Server Actions one at a time per client: a second action waits for the first, and a third waits for the second. This keeps the re-rendered server tree consistent with the action result that produced it.

- Do not use client-side `Promise.all` to run Server Actions in parallel; the client queues them anyway.
- When independent work must overlap, do it inside a single Server Action, fetch in parallel from a Server Component, or use a Route Handler for non-mutation requests.
- This is a client dispatcher property. The server does not queue actions; each runs in its own request as it arrives.

## Single-Response Data and UI

An action that triggers immediate revalidation completes the mutation and the re-render inside one HTTP request. The response carries both the action's return value and a newly rendered RSC payload for the current route.

A re-render is included in the same response when the action:

- calls `updateTag` or `revalidatePath`
- calls `refresh`
- mutates cookies through `cookies()`
- calls `redirect`

`revalidateTag` with a stale-while-revalidate profile is the exception: it marks the tag for background refresh and does not include a re-render, so the page picks up the change on a later read. An action that does none of the above carries only its return value.

## Forms and Client Calls

- Forms can invoke Server Actions with the `action` attribute and receive `FormData`.
- Use server-side validation for authoritative checks; client validation is only a UX aid.
- Use `useActionState`, pending state, optimistic updates, or transitions only in a narrow Client Component wrapper when the UI needs them.
- Because dispatch is sequential per client, design multi-step UI around explicit ordering or a single composite action rather than racing calls.

## Freshness APIs

- Use `updateTag` inside Server Actions for read-your-own-writes cache expiration. It is Server Action-only.
- Use `revalidateTag(tag, 'max')` when stale-while-revalidate behavior is acceptable. It also works in Route Handlers but not in Client Components or Proxy.
- Use `revalidatePath` for path-based invalidation.
- Use `refresh` from `next/cache` in a Server Action to refresh the current client router without tag invalidation. It is Server Action-only.
- Call required invalidation before `redirect()`.

## Hard Rules

| Check | Rule |
|---|---|
| Action trusts `FormData`, params, headers, or search params directly | BLOCKED |
| Action relies only on page-level auth redirect/gating | BLOCKED |
| Action returns raw DB records or internal objects | BLOCKED |
| Action mutates during render instead of through a form/event/transition path | BLOCKED |
| Action performs repeated domain authorization logic inline everywhere | WARNING. Move it into a DAL |
| `redirect()` used before required `updateTag`, `revalidatePath`, or `revalidateTag` | BLOCKED |
| Client code parallelizes Server Actions with `Promise.all` and expects concurrency | BLOCKED |
| Action assumes `revalidateTag(tag, 'max')` re-renders the current route in its response | BLOCKED |
| `updateTag` or `refresh` called outside a Server Action | BLOCKED |

## DAL Guidance

Prefer this split:

- Action: input edge, auth re-check, mutation orchestration, freshness, redirect
- DAL/server-only module: DB access, authorization logic, DTO shaping, sensitive business rules/nextjs

## Security Notes

- Read auth from cookies or headers, not from trusted client-supplied tokens passed into the action.
- Server Action return values are serialized back to the client, so keep them minimal.
- Constrain client input to a reference plus the change. Schema validation checks shape, not ownership; re-read the row through the session.
- For expensive actions, consider rate limiting and abuse controls.
- Next.js enforces a CSRF check on `Origin` versus `Host` or `X-Forwarded-Host`, a 1MB body limit by default, encrypted action IDs, and closure-variable encryption.
- Configure `experimental.serverActions.allowedOrigins` for proxy or CDN hosts; `*` matches one label, `**` matches one or more, and ports must be written out.

## Deployment

- Action IDs rotate at most every 14 days even when the source is unchanged, so a client on an older build can invoke an ID that no longer exists and see "Failed to find Server Action".
- Keep `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY` stable across instances so action references stay decryptable everywhere.
- Prefer rolling deployments over abrupt cutovers when users may be mid-mutation, and surface the failure as a retry path rather than a hard error.

## Review Checklist

- Input validation exists
- Auth and authz are re-checked inside the action or delegated server-only layer
- Return values are minimized
- Client call sites do not assume parallel dispatch
- Freshness happens before redirect when needed
- The freshness choice matches whether a same-response re-render is expected
- Encryption key and origin settings are deliberate in multi-instance or proxied deployments
- Repeated domain logic is not duplicated across many actions

## Sources

> Checked 2026-11-04 against `https://nextjs.org/docs/app/guides/server-actions`, `https://nextjs.org/docs/app/api-reference/config/next-config-js/serverActions`, `https://nextjs.org/docs/app/api-reference/functions/updateTag`, `https://nextjs.org/docs/app/api-reference/functions/revalidateTag`, `https://nextjs.org/docs/app/api-reference/functions/refresh`, and `https://nextjs.org/docs/app/guides/data-security`. The dated snapshot is `references/official/nextjs/current-docs-2026-11-04.md`.
