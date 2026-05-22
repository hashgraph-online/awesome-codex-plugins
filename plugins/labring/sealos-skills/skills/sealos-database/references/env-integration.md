# Environment Integration

Use this reference when wiring Sealos database connection data into a development project.

## File Choice

Prefer the project's existing convention:

1. `.env.local` for Next.js and similar local-only app config.
2. `.env` when the repo already uses it for local development and it is ignored by git.
3. Framework-specific files such as `.dev.vars`, `.env.development`, or `apps/*/.env.local` when the code already reads them.
4. `.env.example` only for placeholder documentation. Never write real secrets into example files.

Before writing secrets, verify the file is ignored:

```bash
git check-ignore .env .env.local .env.development
```

If the target file is tracked or not ignored, stop and choose an ignored local env file instead.

## Env Key Mapping

Prefer keys already used by the app.

| Database | Common keys |
| --- | --- |
| PostgreSQL | `DATABASE_URL`, `POSTGRES_URL`, `POSTGRES_PRISMA_URL` |
| MySQL | `DATABASE_URL`, `MYSQL_URL`, `MYSQL_DATABASE_URL` |
| MongoDB | `MONGODB_URI`, `MONGO_URL`, `DATABASE_URL` |
| Redis | `REDIS_URL`, `KV_URL`, `CACHE_URL`, `QUEUE_REDIS_URL` |
| Qdrant | `QDRANT_URL`, `QDRANT_API_KEY` |
| Weaviate | `WEAVIATE_URL`, `WEAVIATE_API_KEY` |
| ClickHouse | `CLICKHOUSE_URL` |

If multiple keys exist, update the one read by the runtime entry point or ORM config. Do not create extra aliases unless the app needs them.

## Connection String Shapes

Use a connection string returned by `sealos-cli database connection` when available. If only components are returned, compose the minimal expected form:

```text
postgresql://<username>:<password>@<host>:<port>/<database>
mysql://<username>:<password>@<host>:<port>/<database>
mongodb://<username>:<password>@<host>:<port>/<database>?authSource=admin
redis://:<password>@<host>:<port>/0
```

For PostgreSQL, default the database path to `postgres` unless the project explicitly expects another database name. If the app requires a non-default database, create it with the app's migration/bootstrap command or a safe one-time SQL command only after confirming the target.

## Editing Rules

1. Preserve comments, blank lines, and unrelated keys.
2. Replace only the selected key.
3. If the key exists and has a non-empty value, preserve the old value in chat as "replaced existing local value" without printing it.
4. Quote values only if the project's env files already use quotes or the value contains characters that the loader requires quoted.
5. Never print the full resulting connection string in the final answer.

## Verification

Use the project's own path:

- Prisma: `npx prisma db pull`, `npx prisma migrate status`, or the repo's migration script.
- Drizzle: `npx drizzle-kit check`, `npx drizzle-kit migrate`, or the repo's migration script.
- Rails: `bin/rails db:prepare` or `bin/rails db:migrate`.
- Django: `python manage.py migrate --check` or `python manage.py migrate`.
- Generic Node: run the app's smallest server/test script that opens a DB connection.

If the app runs from the user's laptop and private Sealos endpoints are unreachable, ask before enabling public access with `sealos-cli database enable-public <name> -o json`.
