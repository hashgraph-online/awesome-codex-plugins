# Database and ORM Boundary

> Keep persistence behind repositories and runtime-aware database clients

---
## Stable Drizzle Baseline

As verified on 2026-11-04, stable releases are `drizzle-orm` 0.45.4 and `drizzle-kit` 0.31.11. `drizzle-orm` 1.0.0-rc.x is a release candidate and is not adopted here. Drizzle supports many optional drivers; the presence of a peer does not make it valid for every Hono runtime.

- Inspect `drizzle.config.ts`, installed driver, dialect, schema roots, migration output, credentials source, and runtime before changing persistence code.
- Treat `generate` as SQL artifact creation, `migrate` as applying committed migrations, `push` as direct schema synchronization, `pull` as introspection, and `check` as migration-history validation. Never substitute one workflow silently.
- Run `drizzle-kit check` before merging when more than one branch generated migrations; it verifies that the generated SQL history is consistent, and 0.31.11 warns about silent migration skips it previously passed over. `--ignore-conflicts` is an escape hatch for a reviewed exception, not a default.
- Do not use `push` as a production migration strategy unless the project explicitly owns that policy.
- Keep schema and migration history as one provenance chain; never recreate or renumber history to make local state pass.
- Select only required columns and map public DTOs. Validate pagination bounds and make ordering deterministic.
- Test constraints, not-found/conflict mapping, rollback behavior, and runtime-specific connection lifecycle.
- Do not upgrade Drizzle packages, drivers, or generated migration format merely because newer stable versions exist.

## Core Rule

Routes and handlers own transport concerns only: validation, service calls, and response shaping. Services own use-case orchestration. Repositories or query modules own database access. The database layer owns connection setup, ORM configuration, schema exports, and migration placement.

For hypercore Hono projects, a route importing `db`, `drizzle`, ORM table definitions, driver clients, or migration helpers directly is a boundary violation unless the user explicitly asked for official Hono defaults or a tiny proof-of-concept.

## Approved Placement

```text
src/
├── database/
│   ├── client.ts
│   ├── schema.ts
│   └── types.ts
├── repositories/
│   └── users/
│       └── users-repository.ts
├── services/
│   └── users/
│       └── users-service.ts
└── routes/
    └── users/
        ├── index.ts
        ├── handlers.ts
        └── schemas.ts

drizzle/
└── migrations/
```

- `database/client.ts` creates or exports the ORM/database client for the selected runtime.
- `database/schema.ts` or `database/schema/` owns Drizzle table declarations and relations.
- `drizzle/`, `migrations/`, or `database/migrations/` owns generated SQL migrations; the path must match `drizzle.config.ts`.
- `repositories/<domain>/` owns query functions and maps database rows into domain or DTO shapes.
- `services/<domain>/` owns transactions, cross-repository workflows, and business decisions.
- `routes/<domain>/` should not import database clients, ORM schema tables, migrations, or driver packages.

## Drizzle-Specific Guidance

- Use the official Drizzle driver/import for the selected dialect and runtime. Do not mix a Node-only driver into an edge route module.
- Keep Drizzle client construction in `database/client.ts`, a platform factory, or an app initialization boundary.
- Cloudflare D1 should flow through a typed `Bindings` surface such as `c.env.DB`; do not fake it with `process.env`.
- Neon, serverless Postgres, D1, SQLite, and Node Postgres have different client lifecycles. Choose the runtime-specific Drizzle connection path before writing repositories.
- `drizzle.config.ts` should point to the real schema file or schema folder and the real migration output folder.
- Declare relations with `relations()` from `drizzle-orm` on the stable 0.45.x line. `defineRelations()` and Relational Queries v2 belong to `drizzle-orm@rc`; the live relations page is written for that release candidate, so following it on 0.45.x asks for APIs the installed version does not have.
- Drizzle table objects are persistence schema. Do not expose them as route response contracts or OpenAPI schemas without a DTO mapping decision.
- If repository functions need to work inside and outside transactions, accept a `db`/`tx` dependency instead of importing the global client inside every function.

## Connection Lifecycle

| Runtime shape | Rule |
|------|------|
| Long-lived Node server | Create pools/clients at module or app bootstrap scope. Do not instantiate a new pool per request. |
| Serverless function with reusable module scope | Keep the client and prepared statements outside handler scope when the provider can reuse the process. |
| Edge or binding-backed runtime | Use the runtime binding or official edge driver. Avoid assuming cross-request connection reuse. |
| Tests | Use a test database, transaction rollback strategy, or repository fake. Never point automated tests at production data. |

Connection and config code belongs in `database/`, `lib/env.ts`, `lib/create-app.ts`, or the runtime edge. It does not belong in feature route handlers.

## Repositories and Services

```text
route handler -> service/use-case -> repository/query module -> database client
```

- A handler may pass validated input and auth context to a service.
- A service may call one or more repositories and decide whether a transaction is needed.
- A repository may use Drizzle query builders, SQL helpers, selected columns, joins, and row mapping.
- A repository should not read `Context`, `c.env`, headers, cookies, or request bodies.
- A service should not return raw ORM rows to public response code when the API contract needs a stable DTO.
- Cross-feature data access should go through service or repository APIs, not by importing another feature route module.

## Transactions

- Use an explicit transaction for multi-step writes that must commit or roll back as one logical unit.
- Put the transaction boundary in the service/use-case layer, not in the route handler.
- Pass `tx` into repositories that participate in the same transaction.
- Avoid hidden nested transactions. Drizzle supports nested transaction APIs through savepoints, but nested usage should be intentional and reviewed.
- Changing transaction boundaries can change behavior. Cover the affected workflow with repository, service, or request-level tests.

## Schema and Migrations

- Keep Drizzle schema declarations in a stable database schema module or folder.
- Keep generated migration SQL under a committed migration folder that matches `drizzle.config.ts`.
- Review generated SQL before merging. Migration files are production behavior, not build artifacts.
- Do not generate, push, or run database migrations from a normal request handler.
- Do not auto-rename tables, columns, indexes, or migration files as part of a route change.
- If a schema change affects public responses, update validation schemas, DTO mapping, OpenAPI responses, and typed RPC tests in the same change.

## DTO / OpenAPI / RPC Boundary

- Database rows are not automatically API DTOs.
- Public response schemas should describe the API contract, not whatever columns the ORM currently selects.
- OpenAPI schemas, Hono validation schemas, and `AppType`/RPC response types should agree after persistence changes.
- Sensitive columns, internal IDs, soft-delete flags, and audit fields must be deliberately excluded or mapped before response shaping.
- Pagination, sorting, filtering, and partial selects should be reflected in validation and OpenAPI metadata when public clients depend on them.

## Non-Compliance Signatures

- A route or handler imports `drizzle-orm`, `db`, `schema`, `pool`, `client`, `DATABASE_URL`, or ORM table definitions.
- A handler creates a database connection or pool on every request.
- Repositories read Hono `Context` or `c.env` directly.
- Drizzle schema files live inside route folders.
- Migration files are generated but not committed, or the configured migration output folder does not exist.
- A service performs multiple dependent writes without a transaction or an explicit reason.
- Public responses serialize raw ORM rows with internal fields.
- A large app has repositories but no clear database client/config boundary.
- Relations are declared with `defineRelations()` on a stable 0.45.x install.
- Parallel branches generated migrations and nobody ran `drizzle-kit check`.

## Auto-Remediation Boundaries

Safe local fixes:

- Move direct route database calls into an existing service/repository.
- Add a missing repository wrapper for a touched query.
- Centralize a repeated database client import into the existing `database/client.ts`.
- Add DTO mapping for a touched public response when the required shape is already clear.

Do not auto-apply without explicit justification:

- Switching ORM, database provider, dialect, or Drizzle driver.
- Generating, editing, applying, or deleting production migrations.
- Renaming schema tables, columns, indexes, or migration folders.
- Rewriting transaction boundaries without tests for the affected workflow.
- Introducing a new database abstraction layer across the whole app.

## Review Checklist

- Touched routes do not import DB/ORM clients or Drizzle schema tables directly.
- Database client setup is centralized and matches the runtime.
- Environment access is typed through config or Hono `Bindings`.
- Repository functions hide query details and do not depend on Hono `Context`.
- Transactions are explicit for multi-step writes.
- Schema and migration paths match `drizzle.config.ts`.
- Migration history was checked with `drizzle-kit check` when branches could have diverged.
- Relations use the API of the installed generation (`relations()` on 0.45.x).
- API DTOs, validation schemas, OpenAPI responses, and typed RPC contracts still agree.
- Persistence behavior is covered by the smallest useful repository, service, or request-level test.


## Sources

> Checked 2026-11-04.

| Claim | Source |
|---|---|
| `drizzle-orm` 0.45.4 and `drizzle-kit` 0.31.11 as the stable pair | [npm registry: drizzle-orm](https://registry.npmjs.org/drizzle-orm), [npm registry: drizzle-kit](https://registry.npmjs.org/drizzle-kit), [Drizzle releases](https://github.com/drizzle-team/drizzle-orm/releases) |
| `drizzle-kit check` verifying migration-history consistency | [`drizzle-kit check`](https://orm.drizzle.team/docs/drizzle-kit-check) |
| `relations()` on 0.x versus `defineRelations()` on `drizzle-orm@rc` | [Relations v1 to v2](https://orm.drizzle.team/docs/relations-v1-v2) |
| Transaction, driver, and serverless connection behavior delegated to the Drizzle reference | [`references/official/hono/drizzle-docs.md`](../../references/official/hono/drizzle-docs.md) |
