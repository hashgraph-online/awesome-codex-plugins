# Database와 ORM 경계

> Persistence는 repository와 runtime-aware database client 뒤에 둡니다

---

## Stable Drizzle 기준

2026-11-04 확인 기준 stable release는 `drizzle-orm` 0.45.4와 `drizzle-kit` 0.31.11입니다. `drizzle-orm` 1.0.0-rc.x는 release candidate이며 여기에서 채택하지 않습니다. Drizzle은 많은 optional driver를 지원하며 peer가 존재한다고 모든 Hono runtime에 적합한 것은 아닙니다.

- Persistence code 변경 전 `drizzle.config.ts`, installed driver, dialect, schema root, migration output, credential source, runtime을 조사합니다.
- `generate`는 SQL artifact 생성, `migrate`는 committed migration 적용, `push`는 direct schema synchronization, `pull`은 introspection, `check`는 migration 이력 검증으로 구분합니다. Workflow를 조용히 대체하지 않습니다.
- 둘 이상의 branch가 migration을 생성한 경우 merge 전에 `drizzle-kit check`를 실행합니다. 이 명령은 생성된 SQL 이력의 정합성을 검사하고, 0.31.11은 이전에 그냥 지나치던 silent migration skip을 경고합니다. `--ignore-conflicts`는 검토된 예외를 위한 탈출구이지 기본값이 아닙니다.
- Project가 해당 policy를 명시적으로 소유하지 않으면 `push`를 production migration strategy로 사용하지 않습니다.
- Schema와 migration history를 하나의 provenance chain으로 유지하고 local state를 통과시키려고 history를 재생성하거나 renumber하지 않습니다.
- 필요한 column만 select하고 public DTO를 mapping합니다. Pagination bound를 검증하고 ordering을 deterministic하게 만듭니다.
- Constraint, not-found/conflict mapping, rollback behavior, runtime-specific connection lifecycle을 test합니다.
- 최신 stable이 있다는 이유만으로 Drizzle package, driver, generated migration format을 upgrade하지 않습니다.
## 핵심 규칙

Route와 handler는 transport 관심사만 소유합니다: validation, service call, response shaping입니다. Service는 use-case orchestration을 소유합니다. Repository 또는 query module은 database access를 소유합니다. Database layer는 connection setup, ORM configuration, schema export, migration placement를 소유합니다.

Hypercore Hono 프로젝트에서 route가 `db`, `drizzle`, ORM table definition, driver client, migration helper를 직접 import하면 boundary violation입니다. 단, 사용자가 공식 Hono 기본값만 요청했거나 아주 작은 proof-of-concept라고 명시한 경우는 예외로 둘 수 있습니다.

## 승인된 배치

```text
src/
├── database/
│   ├── client.ts
│   ├── schema.ts
│   └── types.ts
├── repositories/
│   └── users/
│       └── users-repository.ts
├── services/
│   └── users/
│       └── users-service.ts
└── routes/
    └── users/
        ├── index.ts
        ├── handlers.ts
        └── schemas.ts

drizzle/
└── migrations/
```

- `database/client.ts`는 선택한 runtime에 맞는 ORM/database client를 만들거나 export합니다.
- `database/schema.ts` 또는 `database/schema/`는 Drizzle table declaration과 relation을 소유합니다.
- `drizzle/`, `migrations/`, `database/migrations/`는 generated SQL migration을 소유합니다. 이 경로는 `drizzle.config.ts`와 일치해야 합니다.
- `repositories/<domain>/`은 query function과 database row를 domain/DTO shape로 매핑하는 책임을 가집니다.
- `services/<domain>/`은 transaction, cross-repository workflow, business decision을 소유합니다.
- `routes/<domain>/`은 database client, ORM schema table, migration, driver package를 import하지 않아야 합니다.

## Drizzle 전용 가이드

- 선택한 dialect와 runtime에 맞는 공식 Drizzle driver/import를 사용합니다. Edge route module에 Node 전용 driver를 섞지 않습니다.
- Drizzle client 생성은 `database/client.ts`, platform factory, app initialization boundary에 둡니다.
- Cloudflare D1은 `c.env.DB` 같은 typed `Bindings` surface를 통해 흐르게 합니다. `process.env`로 흉내내지 않습니다.
- Neon, serverless Postgres, D1, SQLite, Node Postgres는 client lifecycle이 다릅니다. Repository를 쓰기 전에 runtime-specific Drizzle connection path를 먼저 정합니다.
- `drizzle.config.ts`는 실제 schema file/folder와 실제 migration output folder를 가리켜야 합니다.
- 안정판 0.45.x에서는 `drizzle-orm`의 `relations()`로 relation을 선언합니다. `defineRelations()`와 Relational Queries v2는 `drizzle-orm@rc`에 속하며, 현재 relations page가 그 release candidate 기준으로 쓰여 있어 0.45.x에서 따르면 설치된 version에 없는 API를 요구하게 됩니다.
- Drizzle table object는 persistence schema입니다. DTO mapping 결정 없이 route response contract나 OpenAPI schema로 노출하지 않습니다.
- Repository function이 transaction 안팎에서 모두 동작해야 한다면 각 함수 안에서 global client를 import하지 말고 `db`/`tx` dependency를 받습니다.

## Connection Lifecycle

| Runtime 형태 | 규칙 |
|------|------|
| Long-lived Node server | Pool/client는 module 또는 app bootstrap scope에서 만듭니다. Request마다 새 pool을 만들지 않습니다. |
| 재사용 가능한 module scope가 있는 serverless function | Provider가 process 재사용을 지원하면 client와 prepared statement를 handler scope 밖에 둡니다. |
| Edge 또는 binding-backed runtime | Runtime binding 또는 공식 edge driver를 사용합니다. Cross-request connection reuse를 가정하지 않습니다. |
| Tests | Test database, transaction rollback strategy, repository fake를 사용합니다. Automated test가 production data를 바라보면 안 됩니다. |

Connection과 config 코드는 `database/`, `lib/env.ts`, `lib/create-app.ts`, runtime edge에 둡니다. Feature route handler에 두지 않습니다.

## Repositories와 Services

```text
route handler -> service/use-case -> repository/query module -> database client
```

- Handler는 validated input과 auth context를 service에 넘길 수 있습니다.
- Service는 하나 이상의 repository를 호출하고 transaction 필요 여부를 결정합니다.
- Repository는 Drizzle query builder, SQL helper, selected columns, joins, row mapping을 사용할 수 있습니다.
- Repository는 `Context`, `c.env`, headers, cookies, request body를 읽지 않습니다.
- API contract가 안정적인 DTO를 요구한다면 service는 raw ORM row를 public response code로 그대로 반환하지 않습니다.
- Cross-feature data access는 다른 feature route module을 import하지 말고 service/repository API를 거칩니다.

## Transactions

- 하나의 논리 단위로 commit/rollback되어야 하는 multi-step write에는 명시적 transaction을 사용합니다.
- Transaction boundary는 route handler가 아니라 service/use-case layer에 둡니다.
- 같은 transaction에 참여하는 repository에는 `tx`를 넘깁니다.
- 숨은 nested transaction은 피합니다. Drizzle은 savepoint 기반 nested transaction API를 지원하지만, nested 사용은 의도적이고 리뷰되어야 합니다.
- Transaction boundary 변경은 동작 변경일 수 있습니다. 영향을 받는 workflow를 repository, service, request-level test로 덮습니다.

## Schema와 Migrations

- Drizzle schema declaration은 안정적인 database schema module 또는 folder에 둡니다.
- Generated migration SQL은 `drizzle.config.ts`와 일치하는 committed migration folder에 둡니다.
- Generated SQL은 merge 전에 리뷰합니다. Migration file은 build artifact가 아니라 production behavior입니다.
- 일반 request handler에서 database migration을 generate, push, run하지 않습니다.
- Route 변경의 일부로 table, column, index, migration file을 자동 rename하지 않습니다.
- Schema 변경이 public response에 영향을 주면 validation schema, DTO mapping, OpenAPI response, typed RPC test를 같은 변경에서 맞춥니다.

## DTO / OpenAPI / RPC 경계

- Database row는 자동으로 API DTO가 아닙니다.
- Public response schema는 ORM이 현재 select한 column 목록이 아니라 API contract를 설명해야 합니다.
- Persistence 변경 뒤에도 OpenAPI schema, Hono validation schema, `AppType`/RPC response type이 서로 맞아야 합니다.
- Sensitive columns, internal IDs, soft-delete flags, audit fields는 response shaping 전에 의도적으로 제외하거나 매핑해야 합니다.
- Pagination, sorting, filtering, partial select가 public client 계약이면 validation과 OpenAPI metadata에도 반영합니다.

## 비준수 시그널

- Route 또는 handler가 `drizzle-orm`, `db`, `schema`, `pool`, `client`, `DATABASE_URL`, ORM table definition을 import함
- Handler가 request마다 database connection 또는 pool을 생성함
- Repository가 Hono `Context` 또는 `c.env`를 직접 읽음
- Drizzle schema file이 route folder 안에 있음
- Migration file이 생성됐지만 commit되지 않았거나 configured migration output folder가 없음
- Service가 여러 dependent write를 transaction 또는 명시적 이유 없이 수행함
- Public response가 내부 field를 포함한 raw ORM row를 그대로 serialize함
- 큰 app에 repository는 있지만 database client/config boundary가 불명확함
- 안정판 0.45.x 설치에서 `defineRelations()`로 relation을 선언함
- 여러 branch가 migration을 생성했는데 아무도 `drizzle-kit check`를 돌리지 않음

## Auto-Remediation 경계

안전한 local fix:

- Route의 직접 database call을 기존 service/repository로 이동
- Touched query에 누락된 repository wrapper 추가
- 반복된 database client import를 기존 `database/client.ts`로 중앙화
- 필요한 shape가 이미 명확한 touched public response에 DTO mapping 추가

명시적 근거 없이 자동 적용하지 않을 것:

- ORM, database provider, dialect, Drizzle driver 교체
- Production migration 생성, 편집, 적용, 삭제
- Schema table, column, index, migration folder rename
- 영향 workflow 테스트 없이 transaction boundary 재작성
- 앱 전체에 새로운 database abstraction layer 도입

## 리뷰 체크리스트

- Touched route가 DB/ORM client 또는 Drizzle schema table을 직접 import하지 않음
- Database client setup이 중앙화되어 있고 runtime과 일치함
- Environment access가 config 또는 Hono `Bindings`를 통해 type 지정됨
- Repository function이 query detail을 숨기고 Hono `Context`에 의존하지 않음
- Multi-step write의 transaction이 명시적임
- Schema/migration path가 `drizzle.config.ts`와 일치함
- Branch가 갈릴 수 있었으면 migration 이력을 `drizzle-kit check`로 확인함
- Relation이 설치된 세대의 API(`0.45.x`에서는 `relations()`)를 사용함
- API DTO, validation schema, OpenAPI response, typed RPC contract가 여전히 일치함
- Persistence behavior가 가장 작은 유용한 repository, service, request-level test로 커버됨


## Sources

> Checked 2026-11-04.

| 주장 | 출처 |
|---|---|
| 안정판 조합 `drizzle-orm` 0.45.4, `drizzle-kit` 0.31.11 | [npm registry: drizzle-orm](https://registry.npmjs.org/drizzle-orm), [npm registry: drizzle-kit](https://registry.npmjs.org/drizzle-kit), [Drizzle releases](https://github.com/drizzle-team/drizzle-orm/releases) |
| `drizzle-kit check`의 migration 이력 정합성 검사 | [`drizzle-kit check`](https://orm.drizzle.team/docs/drizzle-kit-check) |
| 0.x의 `relations()`와 `drizzle-orm@rc`의 `defineRelations()` | [Relations v1 to v2](https://orm.drizzle.team/docs/relations-v1-v2) |
| Transaction, driver, serverless connection 동작은 Drizzle 참조에 위임 | [`references/official/hono/drizzle-docs.ko.md`](../../references/official/hono/drizzle-docs.ko.md) |
