# Database and Drizzle Boundaries

> Drizzle schema, config, migrations, connection lifecycle, relations, validation integrations, and Next.js server-boundary placement.

## Rule Classifications

| Rule | Classification | Enforcement |
|---|---|---|
| Drizzle schema is TypeScript source of truth | Official Drizzle fact | Keep schema exported and discoverable by `drizzle.config.ts` |
| `drizzle.config.ts` owns `schema` and `out` | Official Drizzle fact | Verify config points at the chosen schema and migration folder |
| `generate` + `migrate` committed SQL flow | Official Drizzle workflow | Prefer unless the repo explicitly uses `push`, `pull`, or another workflow |
| Connections/prepared statements outside handler scope | Official Drizzle serverless guidance | Apply where runtime can reuse module scope |
| `drizzle-orm >= 0.45.2` | Official Drizzle security fix | Block adding or keeping a lower minor |
| Migration history collisions checked | Official Drizzle Kit command | Run `drizzle-kit check` when several branches alter the schema |
| DB folder placement under `src/db` | Hypercore local convention | Label as local convention, not official Next.js or Drizzle law |
| DB access from client hooks/components | Safety policy | Block |

## Default Next.js + Drizzle Shape

This is a Hypercore local convention:

```text
src/
├── db/
│   ├── client.server.ts
│   ├── schema/
│   │   ├── users.ts
│   │   ├── invoices.ts
│   │   └── relations.ts
│   ├── repositories/
│   │   └── users.server.ts
│   └── migrations/             # only if the repo chooses src-local output
├── modules/
├── services/
└── integrations/
drizzle.config.ts
drizzle/                        # default Drizzle Kit migration out
```

Next.js does not mandate `src/db`, and Drizzle does not mandate a Next.js folder shape. The invariant is that schema files are exported and reachable by Drizzle Kit, runtime DB access is server-only, and migration output matches local policy.

## Schema and Config

- Drizzle schema is the TypeScript source of truth for queries and migrations.
- Schema may be single-file or multi-file. Multi-file schemas must export tables, enums, relations, and other models needed by Drizzle Kit.
- `drizzle.config.ts` must point `schema` at the chosen schema file, folder, glob, or array.
- `out` controls migration output and defaults to `drizzle`.
- If the repo uses multiple databases or dialects, use explicit config names and do not hide cross-database assumptions in one generic `db.ts`.

## Migrations

Default committed SQL flow:

```bash
drizzle-kit generate
drizzle-kit migrate
```

Rules:

- Commit generated SQL migrations when the repo follows codebase-first migrations.
- Treat `drizzle-kit push` as a schema-push alternative for explicit local/dev or project-approved workflows, not as a silent replacement for reviewed migrations.
- Treat `drizzle-kit pull` as a database-first/introspection workflow and record when it is the project standard.
- Run `drizzle-kit check` when several branches alter the schema, so generated migration history collisions surface before merge.
- `drizzle-kit up` upgrades snapshots of previously generated migrations, and `drizzle-kit export` prints the schema as raw SQL DDL for review or external tooling.
- Do not run production migrations from a Route Handler, Server Action, hook, or request lifecycle path.

## Runtime and Connection Lifecycle

- Put Drizzle client creation in a server-only module such as `src/db/client.server.ts`.
- Add `import 'server-only'` or an equivalent boundary to DB client and repository modules.
- Declare connection objects and prepared statements outside request handler scope when the runtime can reuse module scope.
- Assume the Node.js runtime. The Edge Runtime is deprecated, and Cache Components rejects the `runtime` export entirely, so pick a driver that works on Node.js or a provider-specific serverless driver rather than targeting an edge surface.
- Server Components may call server-only DAL/repository functions. Client Components and hooks must not import DB modules.

## Relations, RQB, and Repositories

- If using Drizzle relational queries, initialize `drizzle()` with the schema/tables/relations required by RQB.
- Keep relation definitions near schema exports or in a clearly named schema relation file.
- Repository helpers should hide query details and return DTO-ready data, not raw broad rows for client output.
- Transaction-capable helpers should accept a transaction/client parameter when shared by multi-step writes.

## Version and Security Floor

- Pin `drizzle-orm` at 0.45.2 or newer. `0.45.2` fixed `sql.identifier()` and `sql.as()` escaping, closing a possible SQL injection path (CWE-89); earlier minors can emit unescaped identifiers.
- `0.45.3` added the `drizzle-orm/netlify-db` driver, and `0.45.4` fixed postgres-js not using prepared queries on an explicit `.prepare(name)`.
- The stable pair as of 2026-11-04 is `drizzle-orm@0.45.4` with `drizzle-kit@0.31.11`. The 1.0 line is still a release candidate and is not adopted here.
- The documentation site leads with the v1.0 API (`p.pgTable("users", { id: p.serial().primaryKey() })`). Follow the installed version's column builders, which on 0.45 are `pgTable("users", { id: serial("id").primaryKey() })`.

## Validation Integrations

Drizzle validation integrations include zod, valibot, typebox, arktype, typebox-legacy, and effect-schema. Use them to derive or align request validation, insert/update validation, and DTO schemas when that reduces drift.

Do not treat Drizzle table definitions as sufficient user-input validation by themselves. Server Actions and Route Handlers still validate untrusted input at their boundary.

## Review Checklist

- [ ] `drizzle.config.ts` points to exported schema files and the intended migration `out` folder.
- [ ] Schema source of truth is clear, whether single-file or multi-file.
- [ ] Migration workflow is explicit: `generate` + `migrate`, `push`, `pull`, or documented project alternative.
- [ ] DB client, repositories, schema-sensitive helpers, and prepared statements stay server-only.
- [ ] Connections/prepared statements are not recreated inside request handlers when module reuse is available.
- [ ] RQB usage registers the required schema/tables/relations at `drizzle()` initialization.
- [ ] Validation integrations are used deliberately and do not replace boundary validation.
- [ ] `drizzle-orm` is pinned at 0.45.2 or newer, and `drizzle-kit` matches the installed minor line.
- [ ] Migration history is checked with `drizzle-kit check` when multiple branches change the schema.
- [ ] Folder placement is labelled Hypercore local convention, not official Next.js law.

## Sources

> Checked 2026-11-04 against `https://orm.drizzle.team/docs/migrations`, `https://orm.drizzle.team/docs/kit-overview`, `https://orm.drizzle.team/docs/drizzle-kit-check`, `https://orm.drizzle.team/docs/drizzle-kit-up`, `https://github.com/drizzle-team/drizzle-orm/releases/tag/0.45.2`, `https://github.com/drizzle-team/drizzle-orm/releases/tag/0.45.3`, and `https://nextjs.org/docs/app/api-reference/file-conventions/route-segment-config/runtime`. Drizzle facts also live in `references/official/nextjs/drizzle-docs.md`, and Next.js server-boundary rules/nextjs in `references/official/nextjs/nextjs-docs.md`.
