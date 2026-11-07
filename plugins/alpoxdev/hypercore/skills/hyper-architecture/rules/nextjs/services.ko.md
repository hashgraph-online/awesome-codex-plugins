# Services, DAL, Provider Boundaries

> Server Components, Server Actions, Route Handlers, provider adapters, DTO, server-only helper split을 위한 Next.js service-layer guidance입니다.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Server Components는 data source를 직접 query할 수 있음 | Official Next.js fact | module이 server-only이고 safe UI data를 반환하면 허용 |
| Server Actions는 reachable mutation entry point | Official + safety policy | input validation, authentication, authorization, minimal DTO 반환 필요 |
| Route Handlers는 public HTTP endpoints | Official + safety policy | internal UI 또는 Server Component data bridge 기본값으로 사용하지 않음 |
| DAL/service/provider layering | Hypercore local convention | touched non-trivial shared code에 적용 |
| Server-only helper split | Safety policy + Hypercore local convention | DB, secret, filesystem, privileged SDK code를 client graph 밖에 둠 |

## Layer Taxonomy

boundary를 보존하는 가장 작은 layer를 사용합니다:

```text
Server Component or Server Action
  -> src/modules/<domain>/<feature>/ or src/services/<domain>/
  -> server-only DAL/repository/helper
  -> src/db/<area>/client.server.ts or repository
  -> src/integrations/<provider>/client.server.ts
```

공식 Next.js docs는 Server Components가 ORM 또는 database에서 직접 fetch하는 것을 허용합니다. 그러나 authorization, DTO shaping, provider orchestration, reusable queries, cache tags, transaction concerns가 생기면 Hypercore local convention은 server-only DAL 또는 service boundary를 선호합니다.

## Service Roles

| Layer | Use for | Avoid |
|---|---|---|
| `src/modules/<domain>/<feature>/` | feature-owned queries, mutations, DTOs, schemas, cache keys, reusable orchestration | provider-specific SDK ownership |
| `src/services/<domain>/` | service naming을 이미 쓰는 repo의 domain service entrypoints | hooks, DB clients, UI를 넣는 generic dumping ground |
| `src/lib/<domain>/` | small cross-feature helpers, permissions, formatters, cache tag helpers | client-reachable files에서 secret-bearing clients 또는 DB access |
| `src/db/<area>/` | Drizzle client, schema, repositories, transaction helpers | UI state, React hooks, provider API clients |
| `src/integrations/<provider>/` | external SDK clients, webhook schemas, provider mapping | domain authorization 또는 business workflow ownership |
| `src/server/<area>/` | request/session/server runtime utilities | browser-callable helpers |

`src/modules`, `src/services`, `src/db`, `src/server`, `src/integrations`, `src/config`는 Hypercore local folder convention이며 official Next.js law가 아닙니다.

## Server-only Helper Split

client-safe code와 privileged code를 명시적으로 분리합니다:

```text
src/modules/billing/invoices/
├── invoices.actions.ts       # Server Actions; validates input and delegates
├── invoices.queries.ts       # server-side read entrypoints for Server Components
├── invoices.server.ts        # authz, DAL orchestration, transactions
├── invoices.schemas.ts       # validation schemas and serializable DTO types
└── invoices-dto.ts           # client-safe return models when useful
```

Rules:

- privileged service, DAL, DB, authz, provider module에는 `import 'server-only'`를 추가합니다.
- DB row를 Client Components 또는 Server Action callers에 직접 export하지 않습니다. minimal DTO로 shaping합니다.
- authorization은 Server Action 또는 delegated server-only service 가까이에 둡니다. mutation에는 page-level check만으로 부족합니다.
- provider SDK clients는 `src/integrations/<provider>/` 또는 동등한 server-only provider module에 둡니다. domain services가 orchestration을 맡습니다.
- client-safe schemas와 `.server.ts`, DB, provider clients를 함께 re-export하는 mixed `index.ts` barrel을 피합니다.
- Server Component read 또는 Server Action이 맞는 경우 Route Handlers를 internal RPC로 사용하지 않습니다.

## DTO, Validation, Authorization

touched service code에서는:

1. untrusted `FormData`, params, headers, search params, JSON을 사용 전에 validate합니다.
2. Server Action 또는 delegated server-only service에서 authenticate 및 authorize합니다.
3. client-visible output으로 넘어가기 전에 Drizzle rows, provider payloads, internal records를 minimal DTO로 변환합니다.
4. write 후에는 `updateTag`, `revalidateTag(tag, 'max')`, `revalidatePath`, `refresh`, 또는 문서화된 대안으로 revalidate/refresh하고, action 응답에 같은 라운드트립 재렌더가 포함되어야 하는지 밝힙니다.

## Review Checklist

- [ ] Server Components, Server Actions, Route Handlers가 작업에 맞는 surface를 사용함.
- [ ] non-trivial shared logic이 route files에 중복되지 않고 domain/module/service boundary 뒤에 있음.
- [ ] DB, secrets, filesystem, privileged SDK imports가 server-only modules 안에 머무름.
- [ ] Server Actions가 input을 validate하고 auth/authz를 직접 또는 delegated server-only layer에서 재확인함.
- [ ] client-visible outputs가 raw DB rows 또는 broad provider objects가 아니라 minimal DTO임.
- [ ] provider adapters가 `src/integrations/<provider>/` 또는 동등한 server-only provider module에 있음.
- [ ] folder placement를 official Next.js requirement가 아니라 Hypercore local convention으로 보고함.

## Sources

> 확인 2026-11-04. `https://nextjs.org/docs/app/guides/data-security`, `https://nextjs.org/docs/app/getting-started/server-and-client-components`, `https://nextjs.org/docs/app/guides/server-actions`, `https://nextjs.org/docs/app/api-reference/functions/revalidateTag`를 확인했습니다. 날짜가 붙은 스냅숏은 `references/official/nextjs/current-docs-2026-11-04.md`입니다.
