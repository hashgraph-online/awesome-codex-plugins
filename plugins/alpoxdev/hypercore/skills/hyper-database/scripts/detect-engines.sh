#!/usr/bin/env bash
# detect-engines.sh - list the database engines, ORMs, and migration folders a
# repository declares, with the file and the signal that showed each one.
#
# Usage: bash detect-engines.sh [--root <dir>] [--json]
#   --root  repository root to scan (default: current directory)
#   --json  print one JSON object (default); kept for symmetry with other tools
#
# Output (stdout, JSON):
#   {"root": "<the --root value as given>",
#    "engines":    [{"engine": "postgres", "evidence": [{"file": "...", "signal": "..."}]}],
#    "orms":       [{"orm": "prisma", "evidence": [...]}],
#    "migrations": ["prisma/migrations", ...]}
#
# It reads manifests, compose files, ORM configs, and *.example env files only.
# It never reads real .env files and never prints a connection-string value:
# only the URL scheme is reported. Exit codes: 0 scanned (even with no engine),
# 2 bad arguments, 3 missing dependency (jq).
# Requires bash 3.2+, POSIX find/grep/sed, and jq 1.6+.
set -euo pipefail

ROOT="."
while [ "$#" -gt 0 ]; do
  case "$1" in
    --root)
      [ "$#" -ge 2 ] || { echo "detect-engines: --root needs a directory" >&2; exit 2; }
      ROOT="$2"; shift 2 ;;
    --json) shift ;;
    -h|--help) sed -n '2,19p' "$0"; exit 0 ;;
    *) echo "detect-engines: unknown argument: $1" >&2; exit 2 ;;
  esac
done

command -v jq >/dev/null 2>&1 || { echo "detect-engines: jq is required" >&2; exit 3; }
[ -d "$ROOT" ] || { echo "detect-engines: not a directory: $ROOT" >&2; exit 2; }
ROOT_LABEL=$ROOT
ROOT=$(CDPATH='' cd -- "$ROOT" && pwd)

HITS=$(mktemp "${TMPDIR:-/tmp}/detect-engines.XXXXXX")
trap 'rm -f "$HITS"' EXIT

# hit <kind> <name> <file> <signal>
hit() { printf '%s\t%s\t%s\t%s\n' "$1" "$2" "${3#"$ROOT"/}" "$4" >>"$HITS"; }

# Files to scan, skipping dependency and build folders.
list_files() {
  find "$ROOT" \( -name node_modules -o -name .git -o -name .hyper -o -name dist \
    -o -name build -o -name target -o -name .next -o -name .venv -o -name venv \
    -o -name vendor -o -name .dart_tool \) -prune -o -type f \( "$@" \) -print 2>/dev/null
}

# scan_tokens <file> <kind> then pairs of <regex> <name>
scan_tokens() {
  local file=$1 kind=$2
  shift 2
  while [ "$#" -ge 2 ]; do
    if grep -Eq -- "$1" "$file" 2>/dev/null; then
      hit "$kind" "$2" "$file" "$(grep -Eo -m1 -- "$1" "$file" | head -n1)"
    fi
    shift 2
  done
}

# JavaScript / TypeScript manifests: dependency names in quotes.
while IFS= read -r f; do
  scan_tokens "$f" engine \
    '"(pg|postgres|@neondatabase/serverless|@vercel/postgres|pg-promise|slonik)"[[:space:]]*:' postgres \
    '"@supabase/supabase-js"[[:space:]]*:' postgres \
    '"(mysql2|mysql|mariadb|@planetscale/database)"[[:space:]]*:' mysql \
    '"(better-sqlite3|sqlite3|sqlite|@libsql/client|@electric-sql/pglite)"[[:space:]]*:' sqlite \
    '"(redis|ioredis|@redis/client|@upstash/redis)"[[:space:]]*:' redis \
    '"(iovalkey|@valkey/valkey-glide)"[[:space:]]*:' valkey \
    '"(mongodb|mongoose)"[[:space:]]*:' mongodb \
    '"(@aws-sdk/client-dynamodb|@aws-sdk/lib-dynamodb|dynamoose|electrodb|dynamodb-toolbox)"[[:space:]]*:' dynamodb \
    '"cassandra-driver"[[:space:]]*:' cassandra \
    '"@clickhouse/client(-web)?"[[:space:]]*:' clickhouse
  scan_tokens "$f" orm \
    '"(@prisma/client|prisma)"[[:space:]]*:' prisma \
    '"(drizzle-orm|drizzle-kit)"[[:space:]]*:' drizzle \
    '"typeorm"[[:space:]]*:' typeorm \
    '"(sequelize)"[[:space:]]*:' sequelize \
    '"(kysely)"[[:space:]]*:' kysely \
    '"(knex)"[[:space:]]*:' knex \
    '"@mikro-orm/core"[[:space:]]*:' mikro-orm
done < <(list_files -name package.json)

# Python manifests.
while IFS= read -r f; do
  scan_tokens "$f" engine \
    '(^|[^a-z_-])(psycopg2?(-binary)?|asyncpg|pg8000)([^a-z_-]|$)' postgres \
    '(^|[^a-z_-])(pymysql|mysqlclient|aiomysql|mysql-connector-python)([^a-z_-]|$)' mysql \
    '(^|[^a-z_-])(aiosqlite)([^a-z_-]|$)' sqlite \
    '(^|[^a-z_-])redis([^a-z_-]|$)' redis \
    '(^|[^a-z_-])(valkey|valkey-glide)([^a-z_-]|$)' valkey \
    '(^|[^a-z_-])(pymongo|motor|beanie|mongoengine)([^a-z_-]|$)' mongodb \
    '(^|[^a-z_-])(pynamodb)([^a-z_-]|$)' dynamodb \
    '(^|[^a-z_-])(cassandra-driver|scylla-driver)([^a-z_-]|$)' cassandra \
    '(^|[^a-z_-])(clickhouse-connect|clickhouse-driver)([^a-z_-]|$)' clickhouse
  scan_tokens "$f" orm \
    '(^|[^a-z_-])(sqlalchemy|SQLAlchemy)([^a-z_-]|$)' sqlalchemy \
    '(^|[^a-z_-])alembic([^a-z_-]|$)' alembic \
    '(^|[^a-z_-])(django|Django)([^a-z_-]|$)' django \
    '(^|[^a-z_-])(sqlmodel)([^a-z_-]|$)' sqlmodel
done < <(list_files -name pyproject.toml -o -name 'requirements*.txt' -o -name Pipfile)

# Rust manifests.
while IFS= read -r f; do
  scan_tokens "$f" engine \
    '(tokio-postgres|deadpool-postgres|"postgres"|features *=.*"postgres")' postgres \
    '(mysql_async|features *=.*"mysql")' mysql \
    '(rusqlite|libsql|features *=.*"sqlite")' sqlite \
    '^redis *=|^\[dependencies\.redis\]|fred *=' redis \
    '^mongodb *=' mongodb \
    'aws-sdk-dynamodb' dynamodb \
    '^(scylla|cdrs-tokio) *=' cassandra \
    '^clickhouse *=' clickhouse
  scan_tokens "$f" orm \
    '^sqlx *=|^\[dependencies\.sqlx\]' sqlx \
    '^(diesel) *=' diesel \
    '^(sea-orm) *=' sea-orm
done < <(list_files -name Cargo.toml)

# Go modules.
while IFS= read -r f; do
  scan_tokens "$f" engine \
    '(jackc/pgx|lib/pq)' postgres \
    'go-sql-driver/mysql' mysql \
    '(mattn/go-sqlite3|modernc.org/sqlite|tursodatabase)' sqlite \
    '(redis/go-redis|gomodule/redigo|redis/rueidis)' redis \
    'valkey-io/valkey-go' valkey \
    'go.mongodb.org/mongo-driver' mongodb \
    'aws-sdk-go-v2/service/dynamodb' dynamodb \
    '(gocql/gocql|scylladb/gocqlx)' cassandra \
    'ClickHouse/clickhouse-go' clickhouse
  scan_tokens "$f" orm \
    'gorm.io/gorm' gorm \
    'entgo.io/ent' ent \
    'sqlc-dev/sqlc' sqlc
done < <(list_files -name go.mod)

# Ruby, JVM, and Dart manifests (engine names only).
while IFS= read -r f; do
  scan_tokens "$f" engine \
    "(gem ['\"]pg['\"]|org.postgresql|postgresql:postgresql)" postgres \
    "(gem ['\"](mysql2|trilogy)['\"]|mysql-connector-j|mariadb-java-client)" mysql \
    "(gem ['\"]sqlite3['\"]|sqlite-jdbc|sqflite|drift:)" sqlite \
    "(gem ['\"]redis['\"]|jedis|lettuce-core|spring-boot-starter-data-redis)" redis \
    "(gem ['\"]mongoid['\"]|mongodb-driver|spring-boot-starter-data-mongodb)" mongodb \
    "(software.amazon.awssdk:dynamodb|dynamodb-enhanced)" dynamodb \
    "(java-driver-core|cassandra-driver-core|spring-boot-starter-data-cassandra)" cassandra
  scan_tokens "$f" orm \
    "gem ['\"]rails['\"]" rails-active-record \
    "(hibernate-core|spring-boot-starter-data-jpa)" jpa-hibernate \
    "(flyway-core|org.flywaydb)" flyway \
    "(liquibase-core)" liquibase
done < <(list_files -name Gemfile -o -name pom.xml -o -name 'build.gradle*' -o -name pubspec.yaml)

# Container images.
while IFS= read -r f; do
  scan_tokens "$f" engine \
    'image:[[:space:]]*["'\'']?([a-z0-9./-]*/)?(postgres|postgis/postgis|pgvector/pgvector|timescale/timescaledb[a-z-]*|supabase/postgres)(:|["'\''[:space:]]|$)' postgres \
    'image:[[:space:]]*["'\'']?([a-z0-9./-]*/)?(mysql|mariadb|percona[a-z-]*)(:|["'\''[:space:]]|$)' mysql \
    'image:[[:space:]]*["'\'']?([a-z0-9./-]*/)?(redis|redis-stack[a-z-]*|redis/redis-stack[a-z-]*)(:|["'\''[:space:]]|$)' redis \
    'image:[[:space:]]*["'\'']?([a-z0-9./-]*/)?(valkey/valkey|valkey)(:|["'\''[:space:]]|$)' valkey \
    'image:[[:space:]]*["'\'']?([a-z0-9./-]*/)?(mongo|mongodb/mongodb-community-server)(:|["'\''[:space:]]|$)' mongodb \
    'image:[[:space:]]*["'\'']?([a-z0-9./-]*/)?(amazon/dynamodb-local)(:|["'\''[:space:]]|$)' dynamodb \
    'image:[[:space:]]*["'\'']?([a-z0-9./-]*/)?(cassandra|scylladb/scylla)(:|["'\''[:space:]]|$)' cassandra \
    'image:[[:space:]]*["'\'']?([a-z0-9./-]*/)?(clickhouse/clickhouse-server|clickhouse)(:|["'\''[:space:]]|$)' clickhouse
done < <(list_files -name 'docker-compose*.yml' -o -name 'docker-compose*.yaml' -o -name 'compose*.yml' -o -name 'compose*.yaml')

# ORM configuration files that name the dialect.
while IFS= read -r f; do
  case "$f" in
    *.prisma)
      hit orm prisma "$f" "schema.prisma"
      scan_tokens "$f" engine \
        'provider[[:space:]]*=[[:space:]]*"(postgresql|postgres|cockroachdb)"' postgres \
        'provider[[:space:]]*=[[:space:]]*"mysql"' mysql \
        'provider[[:space:]]*=[[:space:]]*"sqlite"' sqlite \
        'provider[[:space:]]*=[[:space:]]*"mongodb"' mongodb ;;
    *drizzle.config.*)
      hit orm drizzle "$f" "drizzle config"
      scan_tokens "$f" engine \
        "dialect:[[:space:]]*['\"]postgresql['\"]" postgres \
        "dialect:[[:space:]]*['\"](mysql|singlestore)['\"]" mysql \
        "dialect:[[:space:]]*['\"](sqlite|turso)['\"]" sqlite ;;
    *wrangler.toml|*wrangler.json|*wrangler.jsonc)
      scan_tokens "$f" engine 'd1_databases' sqlite ;;
    *alembic.ini)
      hit orm alembic "$f" "alembic.ini" ;;
  esac
done < <(list_files -name '*.prisma' -o -name 'drizzle.config.*' -o -name 'wrangler.toml' \
  -o -name 'wrangler.json' -o -name 'wrangler.jsonc' -o -name alembic.ini)

# Example env files: report the URL scheme only, never the value.
while IFS= read -r f; do
  scan_tokens "$f" engine \
    '(postgres|postgresql)(\+[a-z0-9]+)?://' postgres \
    '(mysql|mariadb)(\+[a-z0-9]+)?://' mysql \
    '(file:|libsql://|sqlite:)' sqlite \
    'rediss?://' redis \
    'valkeys?://' valkey \
    'mongodb(\+srv)?://' mongodb
done < <(list_files -name '.env.example' -o -name '.env.sample' -o -name '.env.template' -o -name 'env.example')

# Migration folders.
MIGRATIONS=$(find "$ROOT" \( -name node_modules -o -name .git -o -name .hyper \) -prune -o -type d \
  \( -path '*/prisma/migrations' -o -path '*/supabase/migrations' -o -path '*/drizzle' \
  -o -path '*/db/migrate' -o -path '*/alembic/versions' -o -name migrations \) -print 2>/dev/null \
  | sed "s#^$ROOT/##" | sort -u)

jq -n --arg root "$ROOT_LABEL" --rawfile hits "$HITS" --arg migrations "$MIGRATIONS" '
  def rows: $hits | split("\n") | map(select(length > 0) | split("\t")
    | {kind: .[0], name: .[1], file: .[2], signal: .[3]});
  def group(kind; key): [rows[] | select(.kind == kind)]
    | group_by(.name)
    | map({(key): .[0].name, evidence: (map({file, signal}) | unique)});
  {root: $root,
   engines: group("engine"; "engine"),
   orms: group("orm"; "orm"),
   migrations: ($migrations | split("\n") | map(select(length > 0)))}'
