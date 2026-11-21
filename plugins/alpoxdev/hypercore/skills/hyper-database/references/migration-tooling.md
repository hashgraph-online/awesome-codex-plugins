# Migration Tooling

Use this reference when an ORM or migration tool generates or applies the change. Read the tool's version from the lockfile or manifest first: several tools changed their commands between major versions, and a rule for one major is wrong for the next. Every tool below orders and records migrations; none of them makes a lock-taking statement safe, so `rules/schema-changes.md` still applies to the SQL each one produces.

## 1. Universal Rules

- Generated migrations are drafts. Read the SQL (or the tool's operation list) before it reaches a shared database, and rewrite unsafe statements (`rules/schema-changes.md` §2).
- Production applies only reviewed, committed migrations through a non-interactive command in the deploy pipeline. Commands that diff a live database and apply immediately (`push`, `synchronize`, `db update`) never touch a database you cannot recreate; they read a rename as drop plus add.
- One deploy applies migrations at a time; serialize pipeline jobs or rely on the tool's lock and expect the second job to wait or fail.
- Linters reason about statement shape, not data volume. Pair a lint pass with the table's row count and the session's `lock_timeout` (`rules/validation.md` §3).
- Most tools are forward-only in production. Plan rollback as a new forward migration or as the contract step of expand/contract, not as a `down` script you have never run.

## 2. Tool Notes

| Tool | Version scope | Apply in production | Never in production | Gotchas |
|---|---|---|---|---|
| Prisma ORM | 7 and earlier | `prisma migrate deploy` | `prisma migrate dev` (uses a shadow database, may prompt a reset), `prisma db push` | `migrate deploy` neither detects drift nor resets; the shadow database must be a throwaway database |
| Prisma ORM | 8 | `prisma migration check`, then `prisma db migrate --show`, then `prisma db migrate` (in CI with `--to <ref>`) | `prisma db update` (the replacement for `db push`) against a database whose history must be kept | `db migrate` applies destructive operations without asking: review with `prisma migration show <dir>`. The ORM 8 migration docs name PostgreSQL and MongoDB as supported and SQLite as experimental. On PostgreSQL a failed run is one rolled-back transaction, so a non-transactional statement (`CREATE INDEX CONCURRENTLY`) needs its own handling |
| Drizzle Kit | current | `drizzle-kit generate` (review the SQL), then `drizzle-kit migrate` or the runtime migrator | `drizzle-kit push` on data you cannot recreate | `push` diffs the TypeScript schema against the live database and applies it with no SQL file. Check the installed `drizzle-orm` migrator: on PostgreSQL it applies pending migrations inside one transaction, so `CREATE INDEX CONCURRENTLY` and other non-transactional statements run as a separate script outside the migrator, and `SET lock_timeout` goes at the top of each migration file |
| TypeORM | current | `typeorm migration:run` in the pipeline | `synchronize: true` | Clean the compiled output directory so renamed entities do not load twice |
| Sequelize, Knex, Kysely | current | the tool's `migrate`/`latest` command | auto-sync helpers (`sequelize.sync({ alter: true })`) | Check whether the tool wraps each migration in a transaction on your dialect; a concurrent index build must run outside one, so opt that migration out (Knex: `exports.config = { transaction: false }`) |
| SQLAlchemy + Alembic | current | `alembic upgrade head` | autogenerate output applied unread | Order comes from `down_revision` inside each script, not file names; autogenerate misses renames and data moves |
| Django | current | `manage.py migrate` | applying without `manage.py sqlmigrate` review on large tables | Migrations are transactional on PostgreSQL and SQLite but not on MySQL, so a failed MySQL migration leaves partial DDL; use `atomic = False` and `SeparateDatabaseAndState` for online patterns |
| Rails Active Record | current | `rails db:migrate` with `strong_migrations` failing the build | `remove_column` without `ignored_columns` first | Column removal is five steps: ignore the column, deploy, remove with `safety_assured`, deploy, drop the ignore line; `disable_ddl_transaction!` for concurrent indexes |
| sqlx (Rust) | current | `sqlx migrate run` | - | Up-only unless the first migration was created reversible with `-r`; commit `.sqlx/` from `cargo sqlx prepare` and set `SQLX_OFFLINE=true` so builds never touch a database |
| Flyway, Liquibase, sqitch | current | the tool's `migrate`/`update`/`deploy` | `clean` (drops everything) on a shared database | They version SQL; they do not make DDL online |
| Atlas | current | `atlas migrate apply`, or declarative `schema apply` with a reviewed plan | `--auto-approve` without lint in CI | Needs a disposable `--dev-url` database; `migrate lint` is the safety gate |
| gh-ost, pt-online-schema-change | current | for large MySQL `ALTER`s that are not `INSTANT` or online `INPLACE` | on tables without a primary or unique key | gh-ost reads the binlog (no triggers); both need disk for a full table copy and a cut-over window |
| pgroll | current | PostgreSQL expand/contract with versioned views | - | Requires PostgreSQL 14+ |
| Squawk | current | PostgreSQL migration linter in CI | - | Flags blocking DDL such as non-concurrent index creation and volatile defaults |

## 3. Detecting the Tool

| File or dependency | Tool |
|---|---|
| `prisma/schema.prisma`, `contract.prisma`, `prisma.config.ts`, `@prisma/client` | Prisma (check the major in the lockfile) |
| `drizzle.config.*`, `drizzle-kit` | Drizzle Kit |
| `ormconfig.*`, `typeorm` | TypeORM |
| `alembic.ini`, `alembic/versions/` | Alembic |
| `*/migrations/0001_*.py` beside `manage.py` | Django |
| `db/migrate/*.rb`, `Gemfile` with `rails` | Rails |
| `migrations/*.sql` beside `Cargo.toml` with `sqlx` | sqlx |
| `flyway.conf`, `liquibase.properties`, `sqitch.plan`, `atlas.hcl` | Flyway, Liquibase, sqitch, Atlas |

## Sources

> Checked 2026-11-07.

| Claim | Source |
|---|---|
| Prisma ORM 8 `db migrate` replaces `migrate deploy`, `db update` replaces `db push`, the check-preview-apply sequence, destructive operations applied without a prompt, the supported databases, and one transaction per run on PostgreSQL | <https://www.prisma.io/docs/orm/migrations/applying-a-migration> |
| Prisma 7 `migrate dev` is development-only and uses a shadow database | <https://www.prisma.io/docs/orm/v7/prisma-migrate/workflows/development-and-production> |
| Drizzle Kit `generate`, `migrate`, and `push` | <https://orm.drizzle.team/docs/kit-overview> |
| TypeORM `synchronize` is for development | <https://typeorm.io/docs/help/faq/> |
| Alembic ordering by `down_revision` | <https://alembic.sqlalchemy.org/en/latest/tutorial.html> |
| Django migrations are not transactional on MySQL | <https://docs.djangoproject.com/en/6.1/topics/migrations/> |
| `strong_migrations` danger definition and the column-removal steps | <https://github.com/ankane/strong_migrations> |
| sqlx reversible migrations and offline mode | <https://github.com/transact-rs/sqlx/blob/main/sqlx-cli/README.md> |
| Atlas dev database and migration lint | <https://atlasgo.io/versioned/lint> |
| gh-ost is triggerless and reads the binary log | <https://github.com/github/gh-ost> |
| pgroll requires PostgreSQL 14 or later | <https://github.com/xataio/pgroll> |
| Squawk's purpose and rules | <https://squawkhq.com/docs/rules> |
| The universal rules and the table layout | this package's chosen design, not a validated optimum |
