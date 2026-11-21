# 마이그레이션 도구

ORM이나 마이그레이션 도구가 변경을 생성하거나 적용할 때 이 참조를 사용합니다. 먼저 잠금 파일이나 매니페스트에서 도구 버전을 읽습니다. 여러 도구가 주 버전 사이에 명령을 바꿨으므로 한 주 버전의 규칙이 다음 주 버전에는 틀립니다. 아래 모든 도구는 마이그레이션의 순서를 정하고 기록합니다. 어느 것도 잠금을 잡는 문장을 안전하게 만들지 않으므로, 각 도구가 만드는 SQL에는 `rules/schema-changes.md`가 여전히 적용됩니다.

## 1. 공통 규칙

- 생성한 마이그레이션은 초안입니다. 공유 데이터베이스에 닿기 전에 SQL(또는 도구의 작업 목록)을 읽고, 안전하지 않은 문장을 다시 씁니다(`rules/schema-changes.md` §2).
- 운영에는 검토하고 커밋한 마이그레이션만, 배포 파이프라인의 비대화형 명령으로 적용합니다. 라이브 데이터베이스를 비교해 즉시 적용하는 명령(`push`, `synchronize`, `db update`)은 다시 만들 수 없는 데이터베이스에는 절대 쓰지 않습니다. 이런 명령은 이름 변경을 삭제와 추가로 읽습니다.
- 한 번에 한 배포만 마이그레이션을 적용합니다. 파이프라인 작업을 직렬화하거나 도구의 잠금에 기대며 두 번째 작업이 기다리거나 실패할 것을 예상합니다.
- 린터는 데이터 규모가 아니라 문장 형태를 따집니다. 린트 통과를 테이블의 행 수, 세션의 `lock_timeout`과 함께 봅니다(`rules/validation.md` §3).
- 대부분의 도구는 운영에서 정방향만 지원합니다. 롤백은 한 번도 실행하지 않은 `down` 스크립트가 아니라 새 정방향 마이그레이션이나 expand/contract(확장/축소)의 축소 단계로 계획합니다.

## 2. 도구별 참고

| Tool | Version scope | Apply in production | Never in production | Gotchas |
|---|---|---|---|---|
| Prisma ORM | 7 이하 | `prisma migrate deploy` | `prisma migrate dev`(섀도 데이터베이스를 쓰고 리셋을 요청할 수 있음), `prisma db push` | `migrate deploy`는 드리프트를 감지하지도 리셋하지도 않습니다. 섀도 데이터베이스는 버려도 되는 데이터베이스여야 합니다 |
| Prisma ORM | 8 | `prisma migration check`, 이어서 `prisma db migrate --show`, 이어서 `prisma db migrate`(CI에서는 `--to <ref>`) | 이력 보존이 필요한 데이터베이스에 `prisma db update`(`db push`의 대체) | `db migrate`는 묻지 않고 파괴적 작업을 적용합니다. `prisma migration show <dir>`로 검토합니다. ORM 8 마이그레이션 문서는 PostgreSQL과 MongoDB를 지원, SQLite를 실험적으로 밝힙니다. PostgreSQL에서 실패한 실행은 롤백되는 트랜잭션 하나이므로 비트랜잭션 문장(`CREATE INDEX CONCURRENTLY`)은 별도 처리가 필요합니다 |
| Drizzle Kit | current | `drizzle-kit generate`(SQL 검토), 이어서 `drizzle-kit migrate` 또는 런타임 마이그레이터 | 다시 만들 수 없는 데이터에 `drizzle-kit push` | `push`는 TypeScript 스키마를 라이브 데이터베이스와 비교해 SQL 파일 없이 적용합니다. 설치된 `drizzle-orm` 마이그레이터를 확인합니다. PostgreSQL에서는 대기 중 마이그레이션을 트랜잭션 하나로 적용하므로 `CREATE INDEX CONCURRENTLY` 같은 비트랜잭션 구문은 마이그레이터 밖의 별도 스크립트로 실행하고, 각 마이그레이션 파일 맨 위에 `SET lock_timeout`을 둡니다 |
| TypeORM | current | 파이프라인에서 `typeorm migration:run` | `synchronize: true` | 이름을 바꾼 엔티티가 두 번 로드되지 않도록 컴파일 출력 디렉터리를 정리합니다 |
| Sequelize, Knex, Kysely | current | 그 도구의 `migrate`/`latest` 명령 | 자동 동기화 헬퍼(`sequelize.sync({ alter: true })`) | 그 다이얼렉트에서 도구가 마이그레이션마다 트랜잭션으로 감싸는지 확인합니다. 동시 인덱스 빌드는 트랜잭션 밖에서 실행해야 하므로 그 마이그레이션을 예외로 뺍니다(Knex: `exports.config = { transaction: false }`) |
| SQLAlchemy + Alembic | current | `alembic upgrade head` | 읽지 않은 채 적용하는 autogenerate 출력 | 순서는 파일 이름이 아니라 각 스크립트 안의 `down_revision`에서 나옵니다. autogenerate는 이름 변경과 데이터 이동을 놓칩니다 |
| Django | current | `manage.py migrate` | 큰 테이블에서 `manage.py sqlmigrate` 검토 없이 적용 | 마이그레이션은 PostgreSQL과 SQLite에서 트랜잭션이지만 MySQL에서는 아닙니다. 실패한 MySQL 마이그레이션은 일부 DDL을 남기므로, 무중단 패턴에는 `atomic = False`와 `SeparateDatabaseAndState`를 씁니다 |
| Rails Active Record | current | `strong_migrations`가 빌드를 실패하게 한 상태의 `rails db:migrate` | `ignored_columns` 없이 `remove_column` | 컬럼 제거는 다섯 단계입니다. 컬럼을 무시하고, 배포하고, `safety_assured`로 제거하고, 배포하고, 무시 줄을 지웁니다. 동시 인덱스에는 `disable_ddl_transaction!`을 씁니다 |
| sqlx (Rust) | current | `sqlx migrate run` | - | 첫 마이그레이션을 `-r`로 되돌릴 수 있게 만들지 않았으면 정방향만입니다. `cargo sqlx prepare`가 만든 `.sqlx/`를 커밋하고 `SQLX_OFFLINE=true`를 설정해 빌드가 데이터베이스에 닿지 않게 합니다 |
| Flyway, Liquibase, sqitch | current | 그 도구의 `migrate`/`update`/`deploy` | 공유 데이터베이스의 `clean`(모든 것을 삭제) | SQL에 버전을 부여할 뿐, DDL을 무중단으로 만들지 않습니다 |
| Atlas | current | `atlas migrate apply`, 또는 검토한 계획으로 선언적 `schema apply` | CI에서 린트 없이 `--auto-approve` | 버려도 되는 `--dev-url` 데이터베이스가 필요합니다. `migrate lint`가 안전 게이트입니다 |
| gh-ost, pt-online-schema-change | current | `INSTANT`도 무중단 `INPLACE`도 아닌 큰 MySQL `ALTER` | 기본 키나 유일 키가 없는 테이블 | gh-ost는 바이너리 로그를 읽습니다(트리거 없음). 둘 다 테이블 전체 복사용 디스크와 전환(cut-over) 구간이 필요합니다 |
| pgroll | current | 버전이 붙은 뷰를 쓰는 PostgreSQL expand/contract(확장/축소) | - | PostgreSQL 14 이상이 필요합니다 |
| Squawk | current | CI의 PostgreSQL 마이그레이션 린터 | - | 비동시 인덱스 생성, 자주 바뀌는 기본값 같은 차단 DDL을 표시합니다 |

## 3. 도구 감지

| File or dependency | Tool |
|---|---|
| `prisma/schema.prisma`, `contract.prisma`, `prisma.config.ts`, `@prisma/client` | Prisma(잠금 파일에서 주 버전 확인) |
| `drizzle.config.*`, `drizzle-kit` | Drizzle Kit |
| `ormconfig.*`, `typeorm` | TypeORM |
| `alembic.ini`, `alembic/versions/` | Alembic |
| `manage.py` 옆의 `*/migrations/0001_*.py` | Django |
| `db/migrate/*.rb`, `rails`가 있는 `Gemfile` | Rails |
| `Cargo.toml`에 `sqlx`가 있는 상태의 `migrations/*.sql` | sqlx |
| `flyway.conf`, `liquibase.properties`, `sqitch.plan`, `atlas.hcl` | Flyway, Liquibase, sqitch, Atlas |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Prisma ORM 8에서 `db migrate`가 `migrate deploy`를, `db update`가 `db push`를 대체함, 확인-미리보기-적용 순서, 묻지 않고 적용하는 파괴적 작업, 지원 데이터베이스, PostgreSQL에서 실행당 트랜잭션 하나 | <https://www.prisma.io/docs/orm/migrations/applying-a-migration> |
| Prisma 7의 `migrate dev`는 개발 전용이며 섀도 데이터베이스를 사용함 | <https://www.prisma.io/docs/orm/v7/prisma-migrate/workflows/development-and-production> |
| Drizzle Kit의 `generate`, `migrate`, `push` | <https://orm.drizzle.team/docs/kit-overview> |
| TypeORM의 `synchronize`는 개발용 | <https://typeorm.io/docs/help/faq/> |
| Alembic의 `down_revision` 기준 순서 | <https://alembic.sqlalchemy.org/en/latest/tutorial.html> |
| Django 마이그레이션은 MySQL에서 트랜잭션이 아님 | <https://docs.djangoproject.com/en/6.1/topics/migrations/> |
| `strong_migrations`의 위험 정의와 컬럼 제거 단계 | <https://github.com/ankane/strong_migrations> |
| sqlx의 되돌릴 수 있는 마이그레이션과 오프라인 모드 | <https://github.com/transact-rs/sqlx/blob/main/sqlx-cli/README.md> |
| Atlas의 dev 데이터베이스와 마이그레이션 린트 | <https://atlasgo.io/versioned/lint> |
| gh-ost는 트리거를 쓰지 않고 바이너리 로그를 읽음 | <https://github.com/github/gh-ost> |
| pgroll은 PostgreSQL 14 이상이 필요함 | <https://github.com/xataio/pgroll> |
| Squawk의 목적과 규칙 | <https://squawkhq.com/docs/rules> |
| 공통 규칙과 표 배치 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
