---
name: databuddy
description: Help external users integrate Databuddy into their own apps. Use for SDK setup, React/Vue/vanilla browser tracking, Node/server event tracking, custom event planning, attribution, feature flag evaluation, experiments, Databuddy DevTools, REST analytics queries, and event ingestion. Not for changing Databuddy's own source code.
---

# Databuddy

Use this skill for people adopting Databuddy in their own app or backend. Optimize for a working public integration or instrumentation plan: the right package, credential, endpoint, events, placement, and verification step.

Do not expose `DATABUDDY_API_KEY` in browser code. Browser integrations use a public website `clientId`; server/API integrations use an API key.

## Choose The Surface

- React or Next.js browser analytics: `@databuddy/sdk/react`; mount `<DatabuddyProvider />` near the app root, or wrap the app with it and pass `user` to sync identity and serve flags.
- Vue or Nuxt browser analytics: `@databuddy/sdk/vue`; mount the Vue `<Databuddy />` component once near `RouterView`/`NuxtPage` and translate props to kebab-case in templates.
- Vanilla HTML, CMS, or GTM: CDN script `https://cdn.databuddy.cc/databuddy.js` with `data-client-id`.
- Browser custom events: `track(...)` from `@databuddy/sdk` after the tracker is installed.
- Browser helper utilities: use `trackError`, `flush`, `reset`, `getIds`, `getTrackingParams`, `getRevenueMetadata`, `setGlobalProperties`, `optOut`, and `optIn` from `@databuddy/sdk` when users need manual errors, navigation safety, logout reset, attribution handoff, revenue attribution, or consent. Use `@databuddy/sdk/react` for the provider and flag hooks.
- Known users: in React pass `user={user ? { id, traits: { email, ... } } : null}` to `DatabuddyProvider` and it calls identify/reset for you; otherwise call `identify(profileId, traits?)` (again with new traits to update them) and `reset()` on logout from `@databuddy/sdk` (or `window.databuddy.*` with the script tag), and read the current profile with `getIds().profileId`; server-side use `client.identify({ profileId, anonymousId, traits })` or `profileId` on Node events. Identified users power the Users page, cross-device stitching, and profile retention. See `https://www.databuddy.cc/docs/sdk/identify-users`.
- Server-side events: `@databuddy/sdk/node`; call `flush()` before a serverless/short-lived runtime exits.
- Feature flags: React `defineFlag` + `useFlag` inside `DatabuddyProvider`, the Vue `createFlagsPlugin`, or `createServerFlagsManager` from `@databuddy/sdk/node`; use stable user context, pass `userPending` while auth loads, and call `waitForInit()` before first server read.
- DevTools: `@databuddy/devtools`; use for local/preview inspection of tracker status, IDs, queues, event calls, flags, overrides, diagnostics, and flag management.
- REST analytics: query API under `https://api.databuddy.cc/v1`.
- Custom SQL over analytics (when no query type fits): `POST https://api.databuddy.cc/sql/query`. Read the table notes at `https://www.databuddy.cc/docs/api/sql-tables` (or `GET https://api.databuddy.cc/sql/schema`) before counting; see `https://www.databuddy.cc/docs/api/sql`.
- Raw event ingestion: `POST https://basket.databuddy.cc/track`; prefer SDKs unless the user explicitly wants HTTP.
- Migrating from PostHog: swap `posthog-js`, `posthog-js/react`, and `posthog-node` imports for `@databuddy/sdk/posthog`, `@databuddy/sdk/posthog/react`, and `@databuddy/sdk/posthog/node`; the server adapter needs `websiteId`, and privacy options such as `before_send` must be replaced with Databuddy config. See `https://www.databuddy.cc/docs/sdk/posthog`.

Do not recommend `@databuddy/sdk/ai/vercel`; the public SDK exports only the core, `react`, `vue`, `node`, `agents`, `mcp`, and `posthog` entry points.

If the user says "API", determine whether they mean analytics queries, event ingestion, or feature flags before writing code.

Read [public-surfaces.md](./references/public-surfaces.md) when you need exact env vars, routes, scopes, snippets, or framework routing.
Read [frameworks.md](./references/frameworks.md) for React, Next.js, Vue, Nuxt, and vanilla browser setup.
Read [server-events.md](./references/server-events.md) for browser helpers, Node/server events, raw `/track`, and attribution handoff.
Read [feature-flags.md](./references/feature-flags.md) for client flags, server flags, rollouts, experiments, flag metrics, and flag debugging.
Read [devtools.md](./references/devtools.md) for `@databuddy/devtools` setup, capabilities, flag overrides, diagnostics, and flag management.
Read [event-design.md](./references/event-design.md) when the user asks what custom events to add, which properties matter, or how to avoid noisy/high-cardinality tracking.
Read [instrumentation-planning.md](./references/instrumentation-planning.md) when the user asks what to track, how to design metrics, how to wire attribution across client/server, or where to place tracking calls.
Read [troubleshooting.md](./references/troubleshooting.md) for CSP, blockers, wrong hosts, auth, missing events, and flag/debug failures.

## Credential And Endpoint Rules

| Use | Host/path | Credential | Scope |
| --- | --- | --- | --- |
| Browser analytics | `https://basket.databuddy.cc` via SDK/CDN | `clientId` | none |
| Server events | `POST https://basket.databuddy.cc/track` | `DATABUDDY_API_KEY` | `track:events` |
| REST analytics | `https://api.databuddy.cc/v1/query...` | `DATABUDDY_API_KEY` | `read:data` |
| SQL analytics | `POST https://api.databuddy.cc/sql/query` | `DATABUDDY_API_KEY` | `read:data` |
| Feature flag evaluation | `https://api.databuddy.cc/public/v1/flags...` | `clientId` | none |

- API auth accepts `x-api-key: dbdy_...` or `Authorization: Bearer dbdy_...`; prefer `x-api-key` for examples unless docs for that endpoint use Bearer.
- `websiteId` in event tracking means the public website client id, the same kind of value used by `data-client-id`; it is not necessarily an internal UUID.
- For server-side attribution, collect `{ anonymousId, sessionId }` in the browser with `getIds()`, pass them to your backend, and send them as the Node SDK fields `anonymousId` and `sessionId`.
- Visitor ID privacy is configured with `anonymizeVisitorIds` (`true`/omitted = anonymized, `false` = keeps raw IDs, `"auto"` = raw only in Databuddy's conservative country allowlist); avoid internal wording like storage or hashing in public examples.
- `profileId` is an opaque, stable id from the customer's own database (1-128 characters), never an email. Ingestion trims it, removes control characters, HTML tags, and `<>'"&`, and collapses whitespace runs, so use plain ids such as UUIDs or database keys that this leaves unchanged. Emails and names belong in traits, which are flat scalars (50 keys, 2KB) and process personal data, so the customer needs a lawful basis such as consent.
- Feature flag evaluation uses the main API host, not basket. It needs a website `clientId`, not API-key-only auth.
- Feature flag management uses `manage:flags` with `x-api-key`; do not expose that key in browser source. DevTools accepts it at runtime for local/preview flag management.
- `DATABUDDY_API_URL` is endpoint-specific. Do not reuse a basket root for query API or flags.
- Strict CSP sites need `script-src` for `https://cdn.databuddy.cc` and `connect-src` for `https://basket.databuddy.cc`; add `https://api.databuddy.cc` when using flags.

## Workflow

1. Identify the user's runtime and target surface.
2. Prefer the highest-level supported SDK over raw HTTP.
3. Infer the minimum credential, or ask for only the missing one.
4. Give a short install/env/code path plus one verification step.
5. For custom instrumentation, define `question -> metric -> event -> properties -> source -> placement -> verification` before adding code.

## Custom Event Rules

- Track user intent, product milestones, and operational outcomes, not every click.
- Use stable `snake_case` names and low-cardinality property keys.
- Do not track PII, secrets, raw tokens, full exception stacks, or large payloads.
- Prefer one event with useful properties over many near-duplicate event names.
- Use backend tracking for authoritative outcomes such as account creation, imports, webhooks, and jobs.
- Start with the fewest events that answer the user's question; add more only for funnel steps, important variants, or failure states.
- Do not track the same outcome in both browser and backend. Use browser events for intent and backend events for completed or failed outcomes.

## Verification

- Browser SDK:
  - confirm the script loads and requests reach `basket.databuddy.cc`
  - confirm the expected `clientId` is configured
  - check CSP, ad-blockers, and registered/allowed domain settings if requests never leave the browser
- Node SDK:
  - send one test event
  - call `flush()` before exit
  - confirm no auth or queue errors
- REST API:
  - start with `GET /v1/query/websites`
  - then run the scoped query or event send
- Feature flags:
  - wait for initialization
  - test with a known flag key and user context
  - use DevTools to inspect readiness, evaluated values, variants, and overrides
- Custom instrumentation:
  - verify the event appears under the intended website
  - confirm attribution IDs are present when a server event belongs to a browser session
  - confirm the event can power the intended funnel, goal, segment, or reliability metric

## Response Style

- Default to practical integration guidance and working examples
- Avoid internal monorepo details unless the user is debugging Databuddy itself.
- Keep answers short unless the user asks for a migration or full instrumentation plan.
