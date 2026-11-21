# Database and Drizzle Boundaries

> Drizzle schema, config, migrations, connection lifecycle, relations, validation integrations, Next.js server-boundary placement 지침입니다.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Drizzle schema는 TypeScript source of truth | Official Drizzle fact | schema를 export하고 `drizzle.config.ts`에서 찾을 수 있게 유지 |
| `drizzle.config.ts`가 `schema`와 `out`을 소유 | Official Drizzle fact | config가 선택한 schema와 migration folder를 가리키는지 확인 |
| `generate` + `migrate` committed SQL flow | Official Drizzle workflow | repo가 `push`, `pull`, 다른 workflow를 명시하지 않으면 우선 |
| connection/prepared statements는 handler scope 밖 | Official Drizzle serverless guidance | runtime이 module scope를 재사용할 수 있으면 적용 |
| `drizzle-orm >= 0.45.2` | Official Drizzle security fix | 그보다 낮은 minor를 추가하거나 유지하지 않음 |
| migration 이력 충돌 확인 | Official Drizzle Kit command | 여러 브랜치가 schema를 바꾸면 `drizzle-kit check` 실행 |
| DB folder placement under `src/db` | Hypercore local convention | official Next.js 또는 Drizzle law가 아니라 local convention으로 label |
| client hooks/components에서 DB access | Safety policy | 차단 |

## Default Next.js + Drizzle Shape

이 구조는 Hypercore local convention입니다:

```text
src/
├── db/
│   ├── client.server.ts
│   ├── schema/
│   │   ├── users.ts
│   │   ├── invoices.ts
│   │   └── relations.ts
│   ├── repositories/
│   │   └── users.server.ts
│   └── migrations/             # only if the repo chooses src-local output
├── modules/
├── services/
└── integrations/
drizzle.config.ts
drizzle/                        # default Drizzle Kit migration out
```

Next.js는 `src/db`를 강제하지 않고 Drizzle도 Next.js folder shape를 강제하지 않습니다. invariant는 schema files가 export되어 Drizzle Kit에서 reachable하고, runtime DB access가 server-only이며, migration output이 local policy와 일치하는 것입니다.

## Schema and Config

- Drizzle schema는 queries와 migrations의 TypeScript source of truth입니다.
- Schema는 single-file 또는 multi-file일 수 있습니다. Multi-file schemas는 Drizzle Kit에 필요한 tables, enums, relations, models를 export해야 합니다.
- `drizzle.config.ts`는 `schema`가 선택한 schema file, folder, glob, array를 가리키게 해야 합니다.
- `out`은 migration output을 제어하며 기본값은 `drizzle`입니다.
- repo가 multiple databases 또는 dialects를 쓰면 explicit config names를 사용하고 하나의 generic `db.ts`에 cross-database assumptions를 숨기지 않습니다.

## Migrations

기본 committed SQL flow:

```bash
drizzle-kit generate
drizzle-kit migrate
```

Rules:

- repo가 codebase-first migrations를 따른다면 generated SQL migrations를 commit합니다.
- `drizzle-kit push`는 explicit local/dev 또는 project-approved workflow의 schema-push alternative로 취급하고 reviewed migrations의 silent replacement로 쓰지 않습니다.
- `drizzle-kit pull`은 database-first/introspection workflow로 취급하고 project standard일 때 기록합니다.
- 여러 브랜치가 schema를 바꾸면 `drizzle-kit check`를 돌려 생성된 migration 이력 충돌을 merge 전에 드러냅니다.
- `drizzle-kit up`은 이전에 생성한 migration snapshot을 올리고, `drizzle-kit export`는 schema를 raw SQL DDL로 출력해 리뷰나 외부 도구에 씁니다.
- production migrations를 Route Handler, Server Action, hook, request lifecycle path에서 실행하지 않습니다.

## Runtime and Connection Lifecycle

- Drizzle client creation은 `src/db/client.server.ts` 같은 server-only module에 둡니다.
- DB client와 repository modules에는 `import 'server-only'` 또는 동등한 boundary를 추가합니다.
- runtime이 module scope를 재사용할 수 있으면 connection objects와 prepared statements를 request handler scope 밖에 선언합니다.
- Node.js runtime을 전제합니다. Edge Runtime은 deprecated이고 Cache Components는 `runtime` export 자체를 거부하므로, edge 표면을 겨냥하지 말고 Node.js나 provider-specific serverless driver에서 동작하는 driver를 고릅니다.
- Server Components는 server-only DAL/repository functions를 호출할 수 있습니다. Client Components와 hooks는 DB modules를 import하면 안 됩니다.

## Relations, RQB, Repositories

- Drizzle relational queries를 사용한다면 RQB에 필요한 schema/tables/relations를 `drizzle()` initialization에 등록합니다.
- relation definitions는 schema exports 근처 또는 명확한 schema relation file에 둡니다.
- Repository helpers는 query details를 숨기고 client output에 raw broad rows가 아니라 DTO-ready data를 반환해야 합니다.
- Transaction-capable helpers는 multi-step writes에서 공유될 수 있도록 transaction/client parameter를 받을 수 있게 설계합니다.

## Version and Security Floor

- `drizzle-orm`을 0.45.2 이상으로 고정합니다. `0.45.2`가 `sql.identifier()`와 `sql.as()` 이스케이프를 고쳐 가능한 SQL injection 경로(CWE-89)를 막았고, 그보다 낮은 minor는 escape되지 않은 식별자를 낼 수 있습니다.
- `0.45.3`은 `drizzle-orm/netlify-db` driver를 추가했고, `0.45.4`는 postgres-js가 explicit `.prepare(name)`에서 prepared query를 쓰지 않던 문제를 고쳤습니다.
- 2026-11-04 기준 stable 조합은 `drizzle-orm@0.45.4`와 `drizzle-kit@0.31.11`입니다. 1.0 계열은 아직 release candidate이며 여기서 채택하지 않습니다.
- 문서 사이트는 v1.0 API(`p.pgTable("users", { id: p.serial().primaryKey() })`)를 앞세웁니다. 설치된 버전의 column builder를 따르며, 0.45에서는 `pgTable("users", { id: serial("id").primaryKey() })` 형태입니다.

## Validation Integrations

Drizzle validation integrations에는 zod, valibot, typebox, arktype, typebox-legacy, effect-schema가 포함됩니다. Drift를 줄일 수 있으면 request validation, insert/update validation, DTO schemas를 derive하거나 align하는 데 사용합니다.

Drizzle table definitions만으로 user-input validation이 충분하다고 보지 않습니다. Server Actions와 Route Handlers는 boundary에서 untrusted input을 계속 validate해야 합니다.

## Review Checklist

- [ ] `drizzle.config.ts`가 exported schema files와 의도한 migration `out` folder를 가리킴.
- [ ] single-file 또는 multi-file 여부와 관계없이 schema source of truth가 명확함.
- [ ] migration workflow가 `generate` + `migrate`, `push`, `pull`, documented project alternative 중 하나로 명시됨.
- [ ] DB client, repositories, schema-sensitive helpers, prepared statements가 server-only로 유지됨.
- [ ] module reuse가 가능할 때 connections/prepared statements를 request handlers 안에서 매번 재생성하지 않음.
- [ ] RQB 사용 시 필요한 schema/tables/relations를 `drizzle()` initialization에 등록함.
- [ ] validation integrations를 의도적으로 사용하고 boundary validation을 대체하지 않음.
- [ ] `drizzle-orm`이 0.45.2 이상으로 고정되어 있고 `drizzle-kit`이 설치된 minor 계열과 맞음.
- [ ] 여러 브랜치가 schema를 바꿀 때 `drizzle-kit check`로 migration 이력을 확인함.
- [ ] folder placement를 official Next.js law가 아니라 Hypercore local convention으로 label함.

## Sources

> 확인 2026-11-04. `https://orm.drizzle.team/docs/migrations`, `https://orm.drizzle.team/docs/kit-overview`, `https://orm.drizzle.team/docs/drizzle-kit-check`, `https://orm.drizzle.team/docs/drizzle-kit-up`, `https://github.com/drizzle-team/drizzle-orm/releases/tag/0.45.2`, `https://github.com/drizzle-team/drizzle-orm/releases/tag/0.45.3`, `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/runtime`을 확인했습니다. Drizzle 사실은 `references/official/nextjs/drizzle-docs.md`에도 있고, Next.js server-boundary 규칙은 `references/official/nextjs/nextjs-docs.md`에 있습니다.
