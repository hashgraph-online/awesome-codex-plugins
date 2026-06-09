---
name: sealos-database
description: Provision, connect, and operate Sealos Cloud databases through sealos-cli for local development, Devbox development, and app setup. Use when the user needs a cloud database for a project, asks to create or connect PostgreSQL/MySQL/MongoDB/Redis or another Sealos database, wants DATABASE_URL or similar env vars wired into a dev environment, needs database connection details, backups, logs, public access, or wants to replace local Docker Compose databases with a managed Sealos database.
---

# Sealos Database

Use this skill to give a project a real Sealos Cloud database during development. The default outcome is: identify the app's database need, create or reuse a Sealos database with `sealos-cli`, fetch connection details, wire only the needed local env vars, and verify the app can connect.

## Safety Rules

1. Never print database passwords or full connection strings in the final answer.
2. Do not overwrite an existing env value without confirming or preserving the old value.
3. Do not commit `.env`, `.env.local`, connection strings, passwords, kubeconfig, or Sealos auth files.
4. Ask before enabling public database access. Prefer private connections when the app runs inside Sealos/Devbox.
5. Ask before destructive operations: `database delete`, `backup-delete`, restoring over a name that may collide, or disabling access that an active app depends on.
6. Use JSON output from `sealos-cli` by default and parse it instead of scraping table output.

## Workflow

### 1. Resolve the target project

Confirm the working directory with `pwd` or `git rev-parse --show-toplevel`.

Run the analyzer when a project directory is available:

```bash
node <SKILL_DIR>/scripts/analyze-project-database.mjs <project-dir>
```

Use the analyzer result as a starting point, then inspect the real files it cites before editing anything. It intentionally avoids printing secret values.

### 2. Check `sealos-cli`

Prefer an existing `sealos-cli` binary:

```bash
sealos-cli --version
sealos-cli database --help
sealos-cli whoami
```

If it is not installed, use `npx -y sealos-cli@latest ...` for one-off commands. Ask before installing it globally.

If auth is missing or expired, run:

```bash
sealos-cli login <region>
sealos-cli workspace list
sealos-cli workspace current
```

Use the workspace the user expects. If multiple workspaces exist and the target is ambiguous, ask before provisioning.

### 3. Choose create or reuse

List existing databases first:

```bash
sealos-cli database list -o json
```

Reuse an existing database when the name, type, and purpose match. Create a new one when the project has no suitable database or the user asks for a fresh dev database.

Use conservative development defaults unless the project clearly needs more:

```bash
sealos-cli database create postgresql --name <app-dev-db> --cpu 1 --memory 1 --storage 3 --replicas 1 -o json
```

Before creating, check supported versions if version choice matters:

```bash
sealos-cli database versions --type postgresql -o json
```

Supported CLI database types include `postgresql`, `mongodb`, `mysql`, `apecloud-mysql`, `redis`, `kafka`, `qdrant`, `nebula`, `weaviate`, `milvus`, `pulsar`, and `clickhouse`. Use the type detected from the project; default to `postgresql` only when the project has no database-specific signals.

### 4. Wait for readiness and fetch connection data

Poll details until the database is running or connection data is present:

```bash
sealos-cli database get <name> -o json
sealos-cli database connection <name> -o json
```

Read `references/sealos-cli-database.md` for the current command contract and response handling.

### 5. Wire the development environment

Map the connection into the env var the project already uses:

| Project signal | Preferred env key |
| --- | --- |
| Prisma, Drizzle, TypeORM, generic Postgres | `DATABASE_URL` |
| MySQL app with existing MySQL-specific config | `DATABASE_URL` or existing `MYSQL_URL` |
| MongoDB app | `MONGODB_URI` |
| Redis cache/queue | `REDIS_URL` |

Use the existing local env convention:

1. Prefer `.env.local` for Next.js and frontend-adjacent projects.
2. Prefer `.env` only when the repo already uses it for local development and it is gitignored.
3. Treat `.env.example` as documentation only; never write real secrets there.
4. Preserve comments and unrelated keys.

If a connection string is not directly returned in the desired form, compose it from `host`, `port`, `username`, and `password` fields from `sealos-cli database connection`.

### 6. Verify application connectivity

Run the project's normal verification path, not just the CLI command:

1. Run migrations or introspection if the project has a clear command (`prisma migrate`, `drizzle-kit migrate`, `db:migrate`, `db:push`).
2. Start the app or run the smallest test that opens a DB connection.
3. If the app runs outside Sealos and cannot reach the private endpoint, ask before enabling public access:

```bash
sealos-cli database enable-public <name> -o json
sealos-cli database connection <name> -o json
```

Disable public access after testing if it is no longer needed:

```bash
sealos-cli database disable-public <name> -o json
```

### 7. Report the result

Summarize:

1. Database name, type, region/workspace, and status.
2. Env file and key updated, without revealing the secret value.
3. Verification command and outcome.
4. Any public access state and follow-up action.

## Common Tasks

### Connect an existing project to a Sealos database

1. Run the analyzer.
2. Inspect the env/config files it cites.
3. List existing Sealos databases.
4. Create or reuse the matching database.
5. Fetch connection details.
6. Write the expected env key.
7. Run the app's DB verification.

### Replace a local Compose database for development

1. Identify the app service env vars that point at `postgres`, `mysql`, `mongo`, or `redis` compose services.
2. Provision the equivalent Sealos database.
3. Update only the app's local env file, not the compose file, unless the user asks to remove the local service.
4. Keep local Compose rollback simple: the original compose service remains available.

### Add a database to a Devbox workflow

1. Use private database connection details when the Devbox runs in the same Sealos workspace.
2. Write env vars into the Devbox/app environment expected by the repo.
3. Restart or reload the Devbox process only after env vars are in place.

## References

- `scripts/analyze-project-database.mjs` - read-only project database intent analyzer.
- `references/sealos-cli-database.md` - `sealos-cli database` command contract.
- `references/env-integration.md` - safe env-file editing and connection-string mapping.
