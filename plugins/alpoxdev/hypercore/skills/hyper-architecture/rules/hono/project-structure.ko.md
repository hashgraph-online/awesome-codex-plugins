# 프로젝트 구조와 소유권

> 폴더 설계, 앱 조합 소유권, 기능 확장, 모노레포 또는 구조 리팩터링 시 이 규칙을 읽습니다. Hono 공식 사실은 [`../../references/official/hono/hono-docs.ko.md`](../../references/official/hono/hono-docs.ko.md)에 요약되어 있으며, 별도 표시가 없는 아래 레이아웃은 Hypercore 규칙입니다.

## 1. 저장소 근거로 프로필 선택

패키지/런타임, source root, entrypoint, route mount, alias, workspace 경계, generated file, database/migration 설정, OpenAPI 생성, test, 현재 import graph를 조사합니다. 건드린 경계가 안전하지 않거나 요청을 막지 않는 한 일관된 brownfield 구조를 보존합니다.

각 dependency에 명확한 owner를 부여하는 가장 작은 프로필을 사용합니다.

| 프로필 | 적용 조건 | 지금 추가할 것 |
|---|---|---|
| Compact | route가 적고 재사용 domain/persistence logic이 거의 없는 작은 API | runtime entry, `app.ts`, flat route, 근거가 있는 shared support만 |
| Product | 여러 domain/contributor/validator/persistence workflow, generated API docs 또는 typed client | domain route folder, service/repository boundary, shared middleware와 contract owner |
| Workspace | 여러 deployable 또는 별도 build되는 client가 server contract를 소비 | server package 안의 Product 구조와, 정당화될 때 compiled contract package |

모든 directory를 미리 만들지 않습니다. 고유한 owner, dependency rule 또는 build/runtime contract가 있을 때만 folder를 승격합니다. 빈 layer와 one-file pass-through abstraction은 scalability가 아닙니다.

## 2. 소유권과 의존 방향

```text
runtime entry -> app composition -> route module -> service/use case -> repository/client -> database/external system
```

| 관심사 | 기본 owner | 소유하면 안 되는 것 |
|---|---|---|
| Runtime startup과 adapter API | `runtime/`, `server.ts`, `worker.ts` 또는 configured entry | Domain route나 persistence policy |
| Root middleware/error/not-found/version prefix/route mount | `app.ts` 또는 하나의 `routes/index.ts` mount table | Feature business logic |
| HTTP method/path, validation, auth gate, response shaping | `routes/<domain>/` | ORM query, migration, provider SDK detail |
| Business decision과 multi-step transaction | `services/<domain>/` 또는 feature-local `service.ts` | Hono `Context`, cookie, header, raw request parsing |
| Query와 external SDK adaptation | `repositories/<domain>/`, `clients/<provider>/` | HTTP response shaping이나 route registration |
| Connection lifecycle, ORM schema, migration configuration | `database/`, configured schema/migration root | Request routing |
| Shared API component와 generated spec composition | `openapi/`와 app composition boundary | 중복된 feature operation definition |

Dependency는 오른쪽/아래 방향을 향합니다. 하위 layer는 Hono transport type을 import하지 않습니다. Feature route module은 다른 feature의 route module을 import하지 않으며, cross-feature workflow는 service/use case 또는 의도적으로 shared된 contract에서 만납니다.

## 3. Compact 레이아웃

```text
src/
├── app.ts                    # runtime-neutral Hono composition과 exported app type
├── server.ts                 # Node/Bun adapter; 설정에 따라 worker.ts 또는 index.ts
├── lib/
│   └── create-app.ts         # shared Env/factory typing이 필요할 때만
├── middleware/
│   └── request-id.ts         # 실제 cross-cutting middleware만
└── routes/
    ├── health.ts             # 작은 operational endpoint
    └── users.ts              # 작은 chained sub-app
```

Compact route는 작은 pure helper를 직접 호출할 수 있습니다. Business decision, reuse, persistence, transaction 또는 external SDK behavior가 경계를 정당화할 때만 service/repository를 추가합니다.

## 4. Product 레이아웃

```text
src/
├── app.ts                    # 유일한 root composition과 exported AppType surface
├── runtime/
│   ├── node.ts               # 지원하는 adapter만 생성
│   └── worker.ts
├── config/
│   └── env.ts                # 검증된 runtime configuration
├── middleware/
│   ├── auth.ts
│   └── request-id.ts
├── routes/
│   ├── index.ts              # 선택적 단일 mount table; app.ts와 소유권 중복 금지
│   ├── health.ts
│   └── users/
│       ├── index.ts          # chained usersApp export
│       ├── handlers.ts       # 필요하면 typed factory로 추출
│       ├── schemas.ts        # request/response schema
│       ├── routes.ts         # 선택적 OpenAPI route definition
│       ├── middleware.ts     # users 전용 middleware
│       └── users.test.ts
├── services/
│   └── users/
│       └── create-user.ts
├── repositories/
│   └── users/
│       └── users-repository.ts
├── clients/
│   └── mail/
│       └── mail-client.ts
├── database/
│   ├── client.ts
│   ├── schema.ts
│   └── types.ts
└── openapi/
    ├── components.ts
    └── registry.ts

drizzle/                     # drizzle.config.ts가 가리킬 때만 generated migration
└── migrations/
```

이 tree는 예시이며 configured source/schema/migration root가 우선합니다.

## 5. Feature 성장 기준

| 압력 | 구조 대응 |
|---|---|
| 작은 operational endpoint 하나 | route file 하나 유지 |
| Validation 또는 여러 handler 발생 | `routes/<domain>/`으로 승격하고 route-only schema/handler colocation |
| Business behavior가 재사용되거나 독립 test 대상 | 기존 저장소 패턴에 맞춰 feature-local 또는 root `services/<domain>/` owner 추가 |
| Persistence/provider 호출 발생 | repository/client boundary 추가; route는 DB table/driver/provider SDK import 금지 |
| 두 domain이 transport-independent contract 재사용 | 목적이 명확한 shared owner로 승격; generic dumping-ground `utils/` 금지 |
| 여러 domain이 middleware/OpenAPI component 재사용 | 재사용되는 primitive만 `middleware/` 또는 `openapi/`로 승격 |
| 두 번째 deployable이 server RPC type 소비 | compiled contract package 검토; package 경계 너머 server source deep import 금지 |

파일 수만으로 분리하지 않습니다. 응집된 feature는 colocate할 수 있지만 transport/business/persistence ownership이 섞인 큰 파일은 한 번만 사용되어도 분리합니다.

## 6. Composition과 type surface

Hono 공식 지침은 큰 앱에서 `app.route()`를 지원하며 RPC inference를 위해 chaining에 주의하도록 요구합니다. 명확한 root composition path를 하나만 유지합니다.

```ts
const routes = app
  .route('/users', usersApp)
  .route('/billing', billingApp)

export type AppType = typeof routes
export default app
```

- `/api`와 version prefix는 root mount 또는 `basePath()` boundary에 둡니다.
- Root middleware는 영향받는 route보다 먼저, fallback은 마지막에 등록합니다.
- Runtime startup은 reusable app과 분리하여 `app.request()` test가 server를 boot하지 않게 합니다.
- 저장소가 사용한다면 RPC client, `testClient`, generated OpenAPI를 같은 composed surface에서 파생합니다.
- 매우 큰 RPC surface는 type-check/IDE 부담을 측정한 뒤 compiled declaration 또는 의도적으로 분할한 client를 사용합니다. Canonical server contract를 조용히 희생하지 않습니다.

## 7. Workspace 레이아웃

```text
apps/
├── api/                     # Product profile; runtime과 implementation 소유
└── web/                     # 안정적인 client/contract package 소비
packages/
└── api-contract/            # 별도 build/소비될 때만 emitted type/client
```

Producer/consumer의 `hono` version compatibility를 유지하고 TypeScript `strict`를 활성화하며 기존 build system에 따라 project reference 또는 emitted declaration을 사용합니다. Client package는 database schema, secret, runtime binding, server-only implementation module을 export하면 안 됩니다.

## 8. Brownfield migration

1. 실제 entrypoint, mount, import, generated file, configured root를 매핑합니다.
2. 파일을 옮기기 전에 ownership violation과 cycle을 찾습니다.
3. Public path, middleware order, error behavior, `AppType`, OpenAPI output, migration provenance를 보존합니다.
4. 한 번에 하나의 vertical slice를 옮기고 import/configuration을 원자적으로 갱신합니다.
5. 각 slice 후 focused route/request test와 type check를 실행합니다. Behavior와 guard가 통과할 때만 candidate를 유지합니다.
6. 넓은 이동이 요청 범위를 넘으면 untouched Hypercore-only drift를 backlog로 기록합니다. Touched code의 safety/validation/typing/persistence/runtime-boundary 위반은 계속 차단합니다.

이는 bounded migration loop입니다. Feedback은 focused test/type check와 import-boundary inspection, guard는 public behavior와 contract 불변, 최대 iteration은 계획한 slice 수입니다. Guard에 실패한 slice는 계속하기 전에 폐기하거나 되돌립니다.

## 9. 구조 검증

- Runtime-neutral app 하나와 명확한 mount table 하나를 확인합니다.
- 모든 route의 owner가 명확하고 fallback order가 보존되는지 확인합니다.
- Route/handler에서 DB client, ORM table, migration, driver, provider SDK import를 검색합니다.
- Service/repository에서 Hono `Context`와 raw request/response dependency를 검색합니다.
- Alias, package export, generated-file ownership, schema/migration path를 configuration과 대조합니다.
- 옮긴 route에 type check와 focused `app.request()` 또는 `testClient()` test를 실행합니다.
- RPC/OpenAPI가 있으면 exported composed type/spec에 대표 route와 error shape가 남아 있는지 확인합니다.
- 검증하지 못한 runtime/client/migration/generated artifact를 명시합니다. 파일 레이아웃만으로 성공을 추론하지 않습니다.

## Sources

> Checked 2026-11-04. 이 파일은 이 package 자체 참조 밖의 외부 출처를 쓰지 않았습니다. 공식 Hono 동작은 [`references/official/hono/hono-docs.ko.md`](../../references/official/hono/hono-docs.ko.md)에 위임하며, 그 문서는 2026-11-04에 확인했습니다.
