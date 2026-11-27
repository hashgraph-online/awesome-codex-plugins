# Databuddy Public Surfaces

Use this as the routing map for exact package, env, endpoint, scope, or snippet details. Do not include these local file paths in customer-facing answers.

## Surface Matrix

| Surface | Prefer | Credential | Endpoint | Details |
| --- | --- | --- | --- | --- |
| React / Next.js browser tracking | `DatabuddyProvider` from `@databuddy/sdk/react` | `NEXT_PUBLIC_DATABUDDY_CLIENT_ID` or `clientId` prop | script from CDN, events to basket | [frameworks.md](./frameworks.md) |
| Vue / Nuxt browser tracking | `@databuddy/sdk/vue` | `VITE_DATABUDDY_CLIENT_ID`, `NUXT_PUBLIC_DATABUDDY_CLIENT_ID`, or prop | script from CDN, events to basket | [frameworks.md](./frameworks.md) |
| Vanilla / CMS / GTM | CDN script | `data-client-id` | `https://cdn.databuddy.cc/databuddy.js` then basket | [frameworks.md](./frameworks.md) |
| Browser helpers | `@databuddy/sdk` helpers | browser `clientId` from installed tracker | local/session storage, URL params, basket | [server-events.md](./server-events.md) |
| Server custom events | `@databuddy/sdk/node` | `DATABUDDY_API_KEY` plus optional `DATABUDDY_WEBSITE_ID` | `https://basket.databuddy.cc/track` | [server-events.md](./server-events.md) |
| Raw event ingestion | HTTP/fetch/curl | API key or website id | `POST https://basket.databuddy.cc/track` | [server-events.md](./server-events.md) |
| Feature flag evaluation | React `defineFlag` + `useFlag`, Vue `createFlagsPlugin`, or `createServerFlagsManager` | website `clientId` | `https://api.databuddy.cc/public/v1/flags/bulk` | [feature-flags.md](./feature-flags.md) |
| DevTools overlay | `@databuddy/devtools` | optional `manage:flags` API key for flag management | reads SDK globals; admin calls to API host | [devtools.md](./devtools.md) |
| REST analytics query | HTTP/fetch/curl | `DATABUDDY_API_KEY` | `https://api.databuddy.cc/v1/query...` | below |
| SQL analytics query | HTTP/fetch/curl | `DATABUDDY_API_KEY` | `POST https://api.databuddy.cc/sql/query` | [SQL docs](https://www.databuddy.cc/docs/api/sql), [tables](https://www.databuddy.cc/docs/api/sql-tables) |

## Scopes

- `read:data`: query analytics and list accessible websites.
- `track:events`: send server-side custom events to `/track`.
- `manage:flags`: manage flag definitions; not required for public flag evaluation with `clientId`.

## Install

```bash
bun add @databuddy/sdk
npm install @databuddy/sdk
pnpm add @databuddy/sdk
yarn add @databuddy/sdk
```

DevTools is a separate dev dependency:

```bash
bun add -d @databuddy/devtools
```

## REST Query

```bash
curl -H "x-api-key: dbdy_your_api_key" \
  https://api.databuddy.cc/v1/query/websites
```

Analytics queries are `POST https://api.databuddy.cc/v1/query?website_id=...` with a `parameters` array of query types and either `preset` or `startDate`/`endDate`.

Filters are `{ "field", "op", "value" }` objects. Operators: `eq`, `ne`, `contains`, `not_contains`, `starts_with`, `ends_with`, `in`, `not_in`, `regex` and `not_regex` (re2), the numeric `gt`, `gte`, `lt` and `lte` (values that can't be read as numbers don't match), and `is_set` and `is_not_set` (value ignored). Which fields a query type accepts varies, so check `GET /v1/query/types?include_meta=true`.

Profile retention counts only events that carry a profile id, set by `identify()` in the browser or `profileId` on server events. It takes its selectors as scalar `eq` filters. Send it in its own request, because `filters` apply to every parameter in the body. `startDate`/`endDate` is the cohort range, at most 90 days, and `observation_end` must be on or after `endDate`:

```bash
curl -X POST -H "x-api-key: dbdy_your_api_key" -H "Content-Type: application/json" \
  -d '{
    "parameters": ["identified_profile_retention"],
    "startDate": "2026-09-01",
    "endDate": "2026-09-30",
    "filters": [
      { "field": "activation_event", "op": "eq", "value": "onboarding_completed" },
      { "field": "return_event", "op": "eq", "value": "project_created" },
      { "field": "horizon_days", "op": "eq", "value": 7 },
      { "field": "observation_end", "op": "eq", "value": "2026-10-22" }
    ]
  }' \
  "https://api.databuddy.cc/v1/query?website_id=web_123"
```

The first row is the overall rate and the rest are daily cohorts, so never sum them together.

Query API uses the main API host. Event ingestion uses basket. Feature flag evaluation uses the main API host public flag routes.

## Read Next

- Framework setup: [frameworks.md](./frameworks.md)
- Server events and attribution: [server-events.md](./server-events.md)
- Feature flags and experiments: [feature-flags.md](./feature-flags.md)
- DevTools overlay: [devtools.md](./devtools.md)
- Event and metric planning: [instrumentation-planning.md](./instrumentation-planning.md)
- Troubleshooting and CSP: [troubleshooting.md](./troubleshooting.md)

## Source Docs

- React/Next: `apps/docs/content/docs/sdk/react.mdx`, `apps/docs/content/docs/Integrations/nextjs.mdx`
- Moving off deprecated SDK names: `apps/docs/content/docs/sdk/upgrade.mdx`
- Vue: `apps/docs/content/docs/sdk/vue.mdx`
- Vanilla/CDN: `apps/docs/content/docs/sdk/vanilla-js.mdx`
- Node: `apps/docs/content/docs/sdk/node.mdx`
- Feature flags: `apps/docs/content/docs/sdk/feature-flags.mdx`, `apps/docs/content/docs/sdk/server-flags.mdx`
- REST API: `apps/docs/content/docs/api/index.mdx`, `apps/docs/content/docs/api/authentication.mdx`, `apps/docs/content/docs/api/events.mdx`
