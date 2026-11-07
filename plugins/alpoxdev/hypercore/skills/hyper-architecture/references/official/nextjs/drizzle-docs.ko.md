# Official Drizzle Docs Summary

> Next.js 아키텍처 판단에 쓰는 버전 민감 Drizzle 사실입니다. 패키지별 import 경로나 마이그레이션 명령을 바꾸기 전에 공식 문서를 다시 확인합니다.

last_verified_at: 2026-11-04

## Installed-Version Baseline

| 패키지 | stable | 비고 |
|---|---|---|
| `drizzle-orm` | 0.45.4 (2026-10-08) | 0.45.2가 `sql.identifier()` / `sql.as()` 이스케이프를 수정했습니다(CWE-89) |
| `drizzle-kit` | 0.31.11 (2026-09-21) | `drizzle-orm` 0.45.x와 함께 나옵니다 |
| `drizzle-orm` / `drizzle-kit` 1.0.0-rc.5 | pre-release | 채택하지 않습니다. `latest` dist-tag은 여전히 0.45.4와 0.31.11입니다 |

`drizzle-orm >= 0.45.2`를 보안 하한으로 둡니다. 그 아래 버전은 `sql.identifier()`와 `sql.as()`로 escape되지 않은 식별자를 만들 수 있습니다.

## Source URLs

- `https://github.com/drizzle-team/drizzle-orm/releases`
- `https://github.com/drizzle-team/drizzle-orm/releases/tag/0.45.2`
- `https://github.com/drizzle-team/drizzle-orm/releases/tag/0.45.3`
- `https://orm.drizzle.team/docs/sql-schema-declaration`
- `https://orm.drizzle.team/docs/drizzle-config-file`
- `https://orm.drizzle.team/docs/migrations`
- `https://orm.drizzle.team/docs/kit-overview`
- `https://orm.drizzle.team/docs/drizzle-kit-generate`
- `https://orm.drizzle.team/docs/drizzle-kit-migrate`
- `https://orm.drizzle.team/docs/drizzle-kit-push`
- `https://orm.drizzle.team/docs/drizzle-kit-pull`
- `https://orm.drizzle.team/docs/drizzle-kit-check`
- `https://orm.drizzle.team/docs/drizzle-kit-up`
- `https://orm.drizzle.team/docs/drizzle-kit-export`
- `https://orm.drizzle.team/docs/relations`
- `https://orm.drizzle.team/docs/rqb`
- `https://orm.drizzle.team/docs/perf-serverless`
- `https://orm.drizzle.team/docs/zod`
- `https://orm.drizzle.team/docs/valibot`
- `https://orm.drizzle.team/docs/typebox`
- `https://orm.drizzle.team/docs/arktype`
- `https://orm.drizzle.team/docs/effect-schema`

## Official Facts

1. Drizzle schema는 TypeScript로 선언하고 queries와 migrations의 source of truth로 씁니다.
2. Schema는 single-file 또는 multi-file일 수 있습니다. Tables, enums, relations, 기타 모델은 Drizzle Kit이 import할 수 있게 export해야 합니다.
3. `drizzle.config.ts`는 `schema`로 schema file/folder/glob/array를, `out`으로 migration output folder를 지정합니다.
4. `out` 기본값은 `drizzle`입니다.
5. codebase-first committed SQL 흐름은 `drizzle-kit generate` 다음 `drizzle-kit migrate`입니다.
6. `drizzle-kit push`와 `drizzle-kit pull`은 schema push와 database-first/introspection workflow의 문서화된 대안입니다.
7. `drizzle-kit check`는 생성된 migration 이력을 훑어 충돌과 race condition을 찾습니다. 여러 브랜치가 schema를 바꿀 때 유용합니다.
8. `drizzle-kit up`은 이전에 생성한 migration snapshot을 올리고, `drizzle-kit export`는 schema를 raw SQL DDL로 출력합니다.
9. Drizzle serverless 성능 지침은 runtime이 module scope를 재사용할 수 있으면 connection과 prepared statement 객체를 handler scope 밖에 선언하라고 합니다.
10. 관계형 쿼리(RQB)를 쓰면 필요한 schema/tables/relations를 `drizzle()` 초기화 시점에 넘겨야 합니다.
11. Drizzle validation integrations에는 zod, valibot, typebox, arktype, typebox-legacy, effect-schema가 있습니다.
12. `drizzle-orm/netlify-db`(0.45.3)는 `NETLIFY_DB_URL`과 `NETLIFY_DB_DRIVER`를 읽고, 호출자가 driver를 소유할 때는 explicit client를 받습니다.
13. 0.45.2는 `sql.identifier()`와 `sql.as()`의 이스케이프를 고쳐 SQL injection 경로(CWE-89)를 막았습니다.
14. 0.45.4는 postgres-js가 explicit `.prepare(name)`에서 prepared query를 쓰지 않던 문제를 고쳤습니다.

## Next.js Architecture Implications

- `src/db/schema`, `src/db/repositories`, `src/db/client.server.ts`는 Hypercore 로컬 관례이며 Drizzle이나 공식 Next.js 요구 사항이 아닙니다.
- 프로젝트는 schema 경로 하나를 정하고 `drizzle.config.ts`가 그것을 가리키게 합니다.
- DB client 생성과 repository 도우미는 server-only 모듈에 둡니다. Client Components와 client hooks는 import하면 안 됩니다.
- Server Components는 server-only DAL/repository 함수를 직접 호출할 수 있습니다. Route Handlers는 내부 데이터 통로가 아니라 HTTP-native endpoint에 씁니다.
- Drizzle validation integrations로 insert/update schema를 파생하더라도 Server Actions는 입력 검증과 auth/authz 재확인을 계속해야 합니다.
- migration folder나 script를 바꾸기 전에 저장소가 `generate` + `migrate`, `push`, `pull`, 다른 정책 중 무엇을 쓰는지 기록합니다.
- `drizzle-orm`을 0.45.2 이상으로 고정합니다. 그보다 낮은 minor는 식별자 이스케이프 injection 경로에 노출됩니다.
- 문서 예제를 복사하기 전에 설치된 버전의 컬럼 API를 확인합니다. 문서 사이트는 v1.0 API(`p.pgTable("users", { id: p.serial().primaryKey() })`)를 앞세우지만 stable 0.45 프로젝트는 `serial('id')` 계열을 씁니다.

## Drift Watchlist

- 설치된 `drizzle-kit` 버전과 정확한 CLI 명령 이름, config 속성을 다시 확인합니다.
- serverless, Edge, Neon, D1, Turso/libSQL, Netlify DB, Postgres 연결 코드를 바꾸기 전에 dialect별 driver import와 runtime 지원을 다시 확인합니다.
- 새 generated schema를 추가하기 전에 validation integration 패키지 이름과 생성 API를 다시 확인합니다.
- 1.0 릴리스를 지켜봅니다. 문서 사이트가 1.0 중심으로 재편되고 있고, 채택하면 column-builder API가 바뀝니다.

## Sources

> 확인 2026-11-04. 확인했습니다. 릴리스 사실은 GitHub releases 피드와 0.45.2 / 0.45.3 릴리스 노트에서, 명령과 config 사실은 위에 적은 `orm.drizzle.team` 문서 페이지에서 읽었고, stable 버전 고정은 `drizzle-orm`과 `drizzle-kit`의 npm `latest` dist-tag으로 확인했습니다.

| 주장 | 출처 |
|---|---|
| "Installed-Version Baseline"의 stable 버전과 pre-release 상태 | `https://github.com/drizzle-team/drizzle-orm/releases`와 npm `latest` / `rc` dist-tag |
| 보안과 driver 사실(13, 14, 12) | `https://github.com/drizzle-team/drizzle-orm/releases/tag/0.45.2`와 `/releases/tag/0.45.3` |
| 위 "Official Facts"의 Drizzle 동작 | "Source URLs"에 나열한 `orm.drizzle.team` 문서 페이지 |
| 위 "Next.js Architecture Implications"의 배치와 경계 지침 | 같은 Drizzle 페이지와 Next.js server-boundary 규칙을 위한 `references/official/nextjs/nextjs-docs.ko.md`. `src/db/...` 명명은 공식 요구 사항이 아니라 Hypercore 로컬 관례입니다 |
