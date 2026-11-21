# Drizzle 공식 문서 요약

last_verified_at: 2026-11-04

## Stable package snapshot

2026-11-04 npm registry metadata와 release note를 확인한 기준입니다.

| Package | Stable |
|---|---:|
| `drizzle-orm` | 0.45.4 |
| `drizzle-kit` | 0.31.11 |

출처: [npm registry: drizzle-orm](https://registry.npmjs.org/drizzle-orm), [npm registry: drizzle-kit](https://registry.npmjs.org/drizzle-kit), [Drizzle releases](https://github.com/drizzle-team/drizzle-orm/releases)

이 version은 유지보수 근거이지 upgrade 권한이 아닙니다. Installed dialect driver, peer dependency, config format, generated migration format을 함께 확인해야 합니다.

Hono 아키텍처 결정이 Drizzle ORM, `drizzle-kit`, runtime-specific database driver, schema file, migration, transaction에 의존할 때 이 참조를 사용합니다.

## 공식 문서로 확인한 핵심 포인트

1. Drizzle은 PostgreSQL, Neon, Cloudflare D1, Turso/libSQL, SQLite, PGLite, Bun SQL 등 runtime/dialect별 connection 문서를 제공합니다. 배포 runtime과 맞는 driver를 선택해야 합니다.
출처: [Database connection](https://orm.drizzle.team/docs/connect-overview)

2. Drizzle schema는 TypeScript 파일로 선언합니다. Drizzle Kit은 schema file 또는 folder를 읽으므로 schema declaration은 안정적으로 export되는 위치에 있어야 합니다.
출처: [Schema declaration](https://orm.drizzle.team/docs/sql-schema-declaration), [Drizzle config file](https://orm.drizzle.team/docs/drizzle-config-file)

3. `drizzle.config.ts`의 `schema`는 schema file/folder path이고, `out`은 migration output folder입니다. 기본 migration output folder는 `./drizzle`입니다.
출처: [Drizzle config file](https://orm.drizzle.team/docs/drizzle-config-file), [`drizzle-kit generate`](https://orm.drizzle.team/docs/drizzle-kit-generate)

4. `drizzle-kit generate`는 Drizzle schema 변경에서 SQL migration을 생성합니다. 생성된 migration은 `drizzle-kit migrate`, Drizzle ORM migration API, 외부 도구, 직접 SQL 실행으로 적용할 수 있습니다.
출처: [`drizzle-kit generate`](https://orm.drizzle.team/docs/drizzle-kit-generate), [Migrations](https://orm.drizzle.team/docs/migrations)

5. `drizzle-kit migrate`는 `drizzle-kit generate`가 만든 SQL migration을 적용합니다. Migration folder를 읽고, migrations log table을 확인하고, 아직 적용되지 않은 SQL을 실행한 뒤 적용 기록을 남깁니다.
출처: [`drizzle-kit migrate`](https://orm.drizzle.team/docs/drizzle-kit-migrate)

6. Drizzle migration 문서는 database-first와 codebase-first workflow를 구분합니다. `pull`, `generate`, `push`, `migrate`, `export`, `check`는 서로 다른 workflow를 위한 명령이므로, 저장소 표준이 없는 한 스킬이 하나의 workflow를 강제하면 안 됩니다. `drizzle-kit check`는 생성된 SQL migration 이력의 정합성을 검사하며, 여러 branch가 각각 migration을 만드는 상황에서 필요합니다.
출처: [Migrations](https://orm.drizzle.team/docs/migrations), [`drizzle-kit check`](https://orm.drizzle.team/docs/drizzle-kit-check)

7. Drizzle serverless performance 문서는 runtime이 process를 재사용할 수 있을 때 database connection과 prepared statement를 handler scope 밖에 선언하라고 권장합니다.
출처: [Serverless performance](https://orm.drizzle.team/docs/perf-serverless)

8. Cloudflare D1 지원은 `drizzle-orm/d1`과 D1 Worker binding을 사용합니다. D1 문서는 `drizzle(env.<BINDING_NAME>)`와 Wrangler의 `migrations_dir` 설정을 보여줍니다.
출처: [Cloudflare D1](https://orm.drizzle.team/docs/connect-cloudflare-d1)

9. Neon 지원은 HTTP, WebSocket, serverless driver 경로가 나뉩니다. 문서는 single, non-interactive transaction에는 HTTP가 빠르고, session 또는 interactive transaction support가 필요하면 WebSocket이 필요하다고 설명합니다.
출처: [Neon](https://orm.drizzle.team/docs/connect-neon)

10. Drizzle transaction은 `db.transaction(async (tx) => ...)` 형태를 사용합니다. 문서는 값 반환, rollback, savepoint 기반 nested transaction, transaction 안의 relational query, dialect-specific transaction config도 보여줍니다.
출처: [Transactions](https://orm.drizzle.team/docs/transactions)

11. Relational query는 두 세대가 있습니다. 안정판 0.x는 `drizzle-orm`에서 가져온 `relations()`로 relation을 선언하고, `defineRelations()`와 Relational Queries v2는 `drizzle-orm@rc`와 그 migration guide에 속합니다. 현재 relations page는 release candidate 기준으로 쓰여 있어, 0.45.x 설치에서 그대로 따르면 존재하지 않는 API를 요구하게 됩니다.
출처: [Relations v1 to v2](https://orm.drizzle.team/docs/relations-v1-v2), [Relations](https://orm.drizzle.team/docs/relations)

## 이 스킬에 미치는 영향

- Hypercore Hono 규칙은 Drizzle setup을 하나의 universal import path가 아니라 runtime-specific 결정으로 취급해야 합니다.
- Database client 생성은 각 route handler가 아니라 database/platform boundary에 둡니다.
- Drizzle schema와 migration folder는 `drizzle.config.ts`에서 찾을 수 있어야 합니다.
- Migration 생성/적용은 운영 동작입니다. 일반 route edit 과정에서 조용히 수행하면 안 됩니다.
- Transaction boundary는 service/use-case layer에 둡니다. Transaction에 참여하는 repository helper는 `tx` 또는 database dependency를 받아야 합니다.
- Public API DTO, OpenAPI schema, typed RPC response shape가 Drizzle row shape와 자동으로 같다고 가정하면 안 됩니다.

## Version과 docs caveat

- Drizzle 문서는 live 문서이고 version-sensitive합니다. 코드 변경 전에는 설치된 `drizzle-orm` / `drizzle-kit` release에 맞는 정확한 package version과 import path를 다시 확인합니다.
- Repository helper가 `tx`를 받아야 한다는 규칙은 Drizzle transaction API 형태에서 나온 아키텍처 추론이지, 공식 문서의 문장을 그대로 옮긴 요구사항은 아닙니다.
- Neon, D1, Turso/libSQL 등 provider runtime 문서는 provider SDK 변화에 따라 바뀔 수 있습니다.
- `drizzle-orm` 1.0.0-rc.x는 release candidate입니다. `defineRelations` / Relational Queries v2 API, `EmptyFilter`, `undefined` filter 오류는 안정 동작이 아니며, 이 스킬은 이를 예정 사항으로만 적고 채택하지 않습니다.
- `drizzle-kit` 0.31.11은 `check` 중 silent migration skip을 경고합니다. 이 경고는 잡음이 아니라 migration 이력 결함으로 다룹니다.


## Sources

> Checked 2026-11-04.

| 주장 | 출처 |
|---|---|
| 위 snapshot 표의 `drizzle-orm`, `drizzle-kit` version | 그 표 옆에 적은 registry·release URL |
| 위 1-11번 항목에 기록한 Drizzle 동작 | 각 번호 항목에 붙은 inline `Source:` 링크 |
| 마지막 caveat 절. 그 절이 공식 요구사항이 아니라 이 package의 추론이라고 표시한 `tx` 설명 포함 | 1-11번 항목에서 링크한 같은 Drizzle 문서 page. 추론 부분은 그 절에서 이 package의 것으로 밝힘 |
