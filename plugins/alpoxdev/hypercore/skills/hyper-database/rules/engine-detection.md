# Engine Detection

Use this rule at the start of every run, before naming an engine or reading an engine guide. It decides which engines a target uses, which guide owns each one, and when to stop instead of guessing.

## 1. Run the Detector

Run the bundled detector from the target repository root:

```bash
bash <skill-dir>/scripts/detect-engines.sh --root <repo-root>
```

It prints one JSON object with `engines`, `orms`, and `migrations`, each engine carrying the file and the signal that showed it. It reads manifests, compose files, ORM configs, and `*.example` env files only; it never opens a real `.env` and never prints a connection-string value.

When the shell, `bash`, or `jq` is unavailable, read the same files by hand in the order of §2 and say in the routing line that detection was manual.

## 2. Signals and Their Weight

| Weight | Signal | Example |
|---|---|---|
| Decisive | An ORM or migration config that names the dialect | `provider = "postgresql"` in `schema.prisma`, `dialect: 'mysql'` in `drizzle.config.ts`, `d1_databases` in `wrangler.toml` |
| Decisive | A database container image in a compose file | `image: valkey/valkey:8`, `image: postgres:18` |
| Strong | A driver dependency in a manifest | `pg`, `mysql2`, `ioredis`, `iovalkey`, `mongodb`, `@aws-sdk/client-dynamodb`, `cassandra-driver`, `jackc/pgx`, `sqlx` with a dialect feature |
| Strong | A URL scheme in an example env file | `postgres://`, `rediss://`, `mongodb+srv://` |
| Supporting | Migration folders and SQL files | `prisma/migrations/`, `supabase/migrations/`, `db/migrate/`, `alembic/versions/` |
| Weak | Words in the request alone | "우리 Redis가 느려" with no repository evidence |

- Quote the file and the signal for every engine you route. "Looks like Postgres" is not evidence. Print one Korean routing line per engine in this shape: `라우팅: <engine> / 근거: <file> <signal> / 가이드: engines/<engine>.md`. With no repository, the evidence is `사용자 지정` (the user named the engine) or `엔진 없음 -> choose`.
- A weak signal alone routes only when the repository is absent (a new design) or the user names the engine and no file contradicts it.
- A Redis client library also speaks to Valkey. Treat `redis`/`ioredis` with a `valkey/valkey` image, a managed Valkey endpoint, or the user's own word "Valkey" as Valkey; otherwise as Redis. Both use [engines/redis-valkey.md](../engines/redis-valkey.md).
- `@supabase/supabase-js`, `@neondatabase/serverless`, and Prisma `cockroachdb` mean PostgreSQL wire protocol plus a platform; read the PostgreSQL guide first, then the platform section of the distributed guide.
- `@planetscale/database` or a Vitess keyspace config means MySQL plus Vitess; read the MySQL guide first, then the distributed guide.
- `@libsql/client`, Turso URLs, and `d1_databases` mean SQLite plus a platform; read the SQLite guide first, then the distributed guide.

## 3. Routing Table

| Detected engine | Guide |
|---|---|
| PostgreSQL (self-hosted or managed, including pgvector, PostGIS, TimescaleDB) | [engines/postgres.md](../engines/postgres.md) |
| MySQL, MariaDB, Percona Server | [engines/mysql.md](../engines/mysql.md) |
| SQLite, libSQL, Cloudflare D1 | [engines/sqlite.md](../engines/sqlite.md) |
| Redis, Valkey, other RESP servers | [engines/redis-valkey.md](../engines/redis-valkey.md) |
| MongoDB | [engines/mongodb.md](../engines/mongodb.md) |
| Amazon DynamoDB | [engines/dynamodb.md](../engines/dynamodb.md) |
| Apache Cassandra, ScyllaDB | [engines/cassandra-scylla.md](../engines/cassandra-scylla.md) |
| Vitess, PlanetScale, CockroachDB, TiDB, YugabyteDB, Neon, Supabase, Turso, D1 platform behavior | [engines/distributed-sql.md](../engines/distributed-sql.md) after the wire-protocol guide |
| ClickHouse, time-series, vector, and search engines | [engines/analytical-and-special.md](../engines/analytical-and-special.md) |

## 4. Multi-Engine Targets

- Route each engine the request touches; leave untouched engines unread. "캐시 키 설계 봐줘" in a Postgres + Redis repository reads only the Redis guide.
- When one request crosses engines (a cache in front of a table, an outbox feeding a stream), read the system of record's guide first, then the derived store's guide, and check the consistency rules in [rules/data-modeling.md](data-modeling.md) §6.
- In a monorepo, run the detector per package root the request touches and route each package on its own evidence.

## 5. Conflicts and Stops

| Situation | Action |
|---|---|
| The user names an engine the files contradict ("Postgres로" but only `mysql2` and `image: mysql:8.4`) | Stop and ask once, quoting both pieces of evidence |
| Two dialects are configured for the same data (`provider = "sqlite"` in dev, `postgresql` in prod) | Route by the production dialect; flag the dev/prod mismatch as a finding |
| No repository and no named engine, and the job is not engine choice | Ask one question for the engine, or route to choose mode when the user wants a recommendation |
| An engine outside the routing table (Oracle, SQL Server, Neo4j, Couchbase, Db2) | Apply only the engine-neutral rules, say no engine guide covers it, and mark engine-specific checks `not covered` |
| The object the request names (a table, collection, key family) does not exist in the schema or code | Do not guess a similar object; list the closest candidates with their files and ask once |
| No repository path at all | Skip the detector, say so in the routing line, and continue from the user's named engine or choose mode |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Prisma `datasource.provider` values and the Drizzle Kit `dialect` field | <https://www.prisma.io/docs/orm/v7/reference/prisma-schema-reference>, <https://orm.drizzle.team/docs/drizzle-config-file> |
| Cloudflare D1 bindings declared as `d1_databases` in the Wrangler configuration | <https://developers.cloudflare.com/d1/get-started/> |
| Valkey keeps the RESP protocol and Redis clients connect to it | <https://valkey.io/topics/protocol/> |
| The signal weights, the precedence, and the stop rules | this package's chosen design, not a validated optimum |
