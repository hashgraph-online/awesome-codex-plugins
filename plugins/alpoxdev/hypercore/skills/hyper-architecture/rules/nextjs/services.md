# Services, DAL, and Provider Boundaries

> Next.js service-layer guidance for Server Components, Server Actions, Route Handlers, DAL/service/provider boundaries, provider adapters, DTOs, and server-only helper splits.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Server Components may query data sources directly | Official Next.js fact | Allowed when the module stays server-only and returns safe UI data |
| Server Actions are reachable mutation entry points | Official + safety policy | Validate input, authenticate, authorize, and return minimal DTOs |
| Route Handlers are public HTTP endpoints | Official + safety policy | Do not use as the default internal UI or Server Component data bridge |
| DAL/service/provider layering | Hypercore local convention | Apply to touched non-trivial shared code |
| Server-only helper split | Safety policy + Hypercore local convention | Keep DB, secret, filesystem, and privileged SDK code out of client graphs |

## Layer Taxonomy

Use the smallest layer that preserves the boundary:

```text
Server Component or Server Action
  -> src/modules/<domain>/<feature>/ or src/services/<domain>/
  -> server-only DAL/repository/helper
  -> src/db/<area>/client.server.ts or repository
  -> src/integrations/<provider>/client.server.ts
```

Official Next.js docs allow Server Components to fetch from an ORM or database directly. Hypercore local convention still prefers a server-only DAL or service boundary once the logic has authorization, DTO shaping, provider orchestration, reusable queries, cache tags, or transaction concerns.

## Service Roles

| Layer | Use for | Avoid |
|---|---|---|
| `src/modules/<domain>/<feature>/` | Feature-owned queries, mutations, DTOs, schemas, cache keys, and reusable orchestration | Provider-specific SDK ownership |
| `src/services/<domain>/` | Domain service entrypoints in repos that already use service naming | Generic dumping ground for hooks, DB clients, and UI |
| `src/lib/<domain>/` | Small cross-feature helpers, permissions, formatters, cache tag helpers | Secret-bearing clients or DB access from client-reachable files |
| `src/db/<area>/` | Drizzle client, schema, repositories, transaction helpers | UI state, React hooks, provider API clients |
| `src/integrations/<provider>/` | External SDK clients, webhook schemas, provider mapping | Domain authorization or business workflow ownership |
| `src/server/<area>/` | Request/session/server runtime utilities | Browser-callable helpers |

`src/modules`, `src/services`, `src/db`, `src/server`, `src/integrations`, and `src/config` are Hypercore local folder conventions, not official Next.js law.

## Server-only Helper Split

Split client-safe and privileged code explicitly:

```text
src/modules/billing/invoices/
├── invoices.actions.ts       # Server Actions; validates input and delegates
├── invoices.queries.ts       # server-side read entrypoints for Server Components
├── invoices.server.ts        # authz, DAL orchestration, transactions
├── invoices.schemas.ts       # validation schemas and serializable DTO types
└── invoices-dto.ts           # client-safe return models when useful
```

Rules:

- Add `import 'server-only'` to privileged service, DAL, DB, authz, and provider modules.
- Do not export DB rows directly to Client Components or Server Action callers. Shape minimal DTOs.
- Keep authorization close to the Server Action or delegated server-only service. Page-level checks are not enough for mutations.
- Keep provider SDK clients in `src/integrations/<provider>/` or another server-only provider module; domain services orchestrate them.
- Avoid mixed `index.ts` barrels that re-export client-safe schemas beside `.server.ts`, DB, or provider clients.
- Do not use Route Handlers as internal RPC for Server Components or UI-only mutations when a Server Component read or Server Action fits.

## DTO, Validation, and Authorization

For touched service code:

1. Validate untrusted `FormData`, params, headers, search params, and JSON before use.
2. Authenticate and authorize in the Server Action or delegated server-only service.
3. Convert Drizzle rows, provider payloads, or internal records into minimal DTOs before crossing into client-visible output.
4. Revalidate or refresh after writes with `updateTag`, `revalidateTag(tag, 'max')`, `revalidatePath`, `refresh`, or a documented alternative, and state whether the action response should include a same-roundtrip re-render.

## Review Checklist

- [ ] Server Components, Server Actions, and Route Handlers use the right surface for the job.
- [ ] Non-trivial shared logic is behind a domain/module/service boundary, not duplicated in route files.
- [ ] DB, secrets, filesystem, and privileged SDK imports stay in server-only modules.
- [ ] Server Actions validate input and re-check auth/authz directly or through a delegated server-only layer.
- [ ] Client-visible outputs are minimal DTOs, not raw DB rows or broad provider objects.
- [ ] Provider adapters live under `src/integrations/<provider>/` or an equivalent server-only provider module.
- [ ] Folder placement is reported as Hypercore local convention, not official Next.js requirement.

## Sources

> Checked 2026-11-04 against `https://nextjs.org/docs/app/guides/data-security`, `https://nextjs.org/docs/app/getting-started/server-and-client-components`, `https://nextjs.org/docs/app/guides/server-actions`, and `https://nextjs.org/docs/app/api-reference/functions/revalidateTag`. The dated snapshot is `references/official/nextjs/current-docs-2026-11-04.md`.
