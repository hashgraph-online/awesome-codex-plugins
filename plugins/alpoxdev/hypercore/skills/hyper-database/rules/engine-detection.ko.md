# 엔진 감지

엔진을 지정하거나 엔진 가이드를 읽기 전에 모든 실행의 시작에서 이 규칙을 사용합니다. 대상이 어떤 엔진을 쓰는지, 각 엔진을 어느 가이드가 맡는지, 언제 추측 대신 멈출지를 정합니다.

## 1. 감지기 실행

대상 저장소 루트에서 함께 제공되는 감지기를 실행합니다.

```bash
bash <skill-dir>/scripts/detect-engines.sh --root <repo-root>
```

`engines`, `orms`, `migrations`를 담은 JSON 객체 하나를 출력하고, 각 엔진에는 이를 드러낸 파일과 신호가 붙습니다. 매니페스트, compose 파일, ORM 설정, `*.example` 환경 파일만 읽습니다. 실제 `.env`는 열지 않고 연결 문자열 값도 출력하지 않습니다.

셸, `bash`, `jq`를 쓸 수 없으면 §2의 순서대로 같은 파일을 직접 읽고, 라우팅 줄에 감지를 수동으로 했다고 밝힙니다.

## 2. 신호와 가중치

| Weight | Signal | Example |
|---|---|---|
| Decisive | 다이얼렉트를 지정하는 ORM 또는 마이그레이션 설정 | `schema.prisma`의 `provider = "postgresql"`, `drizzle.config.ts`의 `dialect: 'mysql'`, `wrangler.toml`의 `d1_databases` |
| Decisive | compose 파일의 데이터베이스 컨테이너 이미지 | `image: valkey/valkey:8`, `image: postgres:18` |
| Strong | 매니페스트의 드라이버 의존성 | `pg`, `mysql2`, `ioredis`, `iovalkey`, `mongodb`, `@aws-sdk/client-dynamodb`, `cassandra-driver`, `jackc/pgx`, 다이얼렉트 기능을 켠 `sqlx` |
| Strong | 예시 환경 파일의 URL 스킴 | `postgres://`, `rediss://`, `mongodb+srv://` |
| Supporting | 마이그레이션 폴더와 SQL 파일 | `prisma/migrations/`, `supabase/migrations/`, `db/migrate/`, `alembic/versions/` |
| Weak | 요청에만 있는 단어 | 저장소 근거 없이 "우리 Redis가 느려" |

- 라우팅한 엔진마다 파일과 신호를 인용합니다. "Postgres 같습니다"는 근거가 아닙니다. 엔진마다 한국어 라우팅 줄 하나를 이 형식으로 출력합니다. `라우팅: <engine> / 근거: <file> <signal> / 가이드: engines/<engine>.md`. 저장소가 없으면 근거는 `사용자 지정`(사용자가 엔진을 말함) 또는 `엔진 없음 -> choose`입니다.
- 약한 신호만으로는 저장소가 없거나(새 설계) 사용자가 엔진을 지정했고 이를 반박하는 파일이 없을 때만 라우팅합니다.
- Redis 클라이언트 라이브러리는 Valkey와도 통신합니다. `redis`/`ioredis`가 `valkey/valkey` 이미지, 매니지드 Valkey 엔드포인트, 사용자 본인의 "Valkey" 발언과 함께 있으면 Valkey로, 아니면 Redis로 다룹니다. 둘 다 [engines/redis-valkey.md](../engines/redis-valkey.md)를 사용합니다.
- `@supabase/supabase-js`, `@neondatabase/serverless`, Prisma `cockroachdb`는 PostgreSQL 와이어 프로토콜에 플랫폼이 더해진 것입니다. PostgreSQL 가이드를 먼저 읽고, 그다음 분산 가이드의 플랫폼 절을 읽습니다.
- `@planetscale/database` 또는 Vitess 키스페이스 설정은 MySQL에 Vitess가 더해진 것입니다. MySQL 가이드를 먼저 읽고, 그다음 분산 가이드를 읽습니다.
- `@libsql/client`, Turso URL, `d1_databases`는 SQLite에 플랫폼이 더해진 것입니다. SQLite 가이드를 먼저 읽고, 그다음 분산 가이드를 읽습니다.

## 3. 라우팅 표

| Detected engine | Guide |
|---|---|
| PostgreSQL(자체 호스팅 또는 매니지드, pgvector, PostGIS, TimescaleDB 포함) | [engines/postgres.md](../engines/postgres.md) |
| MySQL, MariaDB, Percona Server | [engines/mysql.md](../engines/mysql.md) |
| SQLite, libSQL, Cloudflare D1 | [engines/sqlite.md](../engines/sqlite.md) |
| Redis, Valkey, 그 밖의 RESP 서버 | [engines/redis-valkey.md](../engines/redis-valkey.md) |
| MongoDB | [engines/mongodb.md](../engines/mongodb.md) |
| Amazon DynamoDB | [engines/dynamodb.md](../engines/dynamodb.md) |
| Apache Cassandra, ScyllaDB | [engines/cassandra-scylla.md](../engines/cassandra-scylla.md) |
| Vitess, PlanetScale, CockroachDB, TiDB, YugabyteDB, Neon, Supabase, Turso, D1의 플랫폼 동작 | 와이어 프로토콜 가이드 다음에 [engines/distributed-sql.md](../engines/distributed-sql.md) |
| ClickHouse, 시계열, 벡터, 검색 엔진 | [engines/analytical-and-special.md](../engines/analytical-and-special.md) |

## 4. 여러 엔진을 쓰는 대상

- 요청이 건드리는 엔진만 라우팅하고, 건드리지 않는 엔진은 읽지 않습니다. Postgres + Redis 저장소에서 "캐시 키 설계 봐줘"는 Redis 가이드만 읽습니다.
- 한 요청이 엔진을 넘나들면(테이블 앞의 캐시, 스트림으로 흘려보내는 아웃박스), 원본 저장소의 가이드를 먼저 읽고 파생 저장소의 가이드를 읽은 뒤 [rules/data-modeling.md](data-modeling.md) §6의 일관성 규칙을 확인합니다.
- 모노레포에서는 요청이 건드리는 패키지 루트마다 감지기를 실행하고, 패키지마다 자체 근거로 라우팅합니다.

## 5. 충돌과 정지

| Situation | Action |
|---|---|
| 사용자가 지정한 엔진과 파일이 어긋남("Postgres로"인데 `mysql2`와 `image: mysql:8.4`만 있음) | 멈추고 근거 두 개를 인용해 한 번 묻습니다 |
| 같은 데이터에 다이얼렉트 두 개가 설정됨(개발은 `provider = "sqlite"`, 운영은 `postgresql`) | 운영 다이얼렉트로 라우팅하고, 개발·운영 불일치를 발견 사항으로 표시합니다 |
| 저장소도 지정된 엔진도 없고 작업이 엔진 선택이 아님 | 엔진을 묻는 질문을 한 번 하거나, 사용자가 권고를 원하면 choose 모드로 라우팅합니다 |
| 라우팅 표 밖의 엔진(Oracle, SQL Server, Neo4j, Couchbase, Db2) | 엔진 중립 규칙만 적용하고, 이를 다루는 엔진 가이드가 없다고 밝히며, 엔진별 점검을 `not covered`로 표시합니다 |
| 요청이 가리키는 객체(테이블, 컬렉션, 키 계열)가 스키마나 코드에 없음 | 비슷한 객체를 추측하지 않습니다. 가장 가까운 후보를 파일과 함께 나열하고 한 번 묻습니다 |
| 저장소 경로가 아예 없음 | 감지 스크립트를 건너뛰고 라우팅 줄에 그렇게 적은 뒤, 사용자가 지정한 엔진이나 choose 모드로 이어 갑니다 |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Prisma `datasource.provider` 값과 Drizzle Kit의 `dialect` 필드 | <https://www.prisma.io/docs/orm/v7/reference/prisma-schema-reference>, <https://orm.drizzle.team/docs/drizzle-config-file> |
| Wrangler 설정에 `d1_databases`로 선언하는 Cloudflare D1 바인딩 | <https://developers.cloudflare.com/d1/get-started/> |
| Valkey가 RESP 프로토콜을 유지하고 Redis 클라이언트가 연결된다는 점 | <https://valkey.io/topics/protocol/> |
| 신호 가중치, 우선순위, 정지 규칙 | 이 패키지가 고른 설계이며 검증된 최적값이 아님 |
