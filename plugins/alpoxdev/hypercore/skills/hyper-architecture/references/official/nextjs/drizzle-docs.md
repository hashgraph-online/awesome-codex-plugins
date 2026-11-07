# Official Drizzle Docs Summary

> Version-sensitive Drizzle facts for Next.js architecture decisions. Re-check official docs before changing package-specific import paths or migration commands.

last_verified_at: 2026-11-04

## Installed-Version Baseline

| Package | Stable | Notes |
|---|---|---|
| `drizzle-orm` | 0.45.4 (2026-10-08) | 0.45.2 fixed `sql.identifier()` / `sql.as()` escaping (CWE-89) |
| `drizzle-kit` | 0.31.11 (2026-09-21) | Ships alongside `drizzle-orm` 0.45.x |
| `drizzle-orm` / `drizzle-kit` 1.0.0-rc.5 | pre-release | Not adopted; `latest` dist-tags still point at 0.45.4 and 0.31.11 |

Treat `drizzle-orm >= 0.45.2` as the security floor. Anything below it can produce unescaped identifiers through `sql.identifier()` and `sql.as()`.

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

1. Drizzle schema is declared in TypeScript and acts as the source of truth for queries and migrations.
2. Schema can be single-file or multi-file. Tables, enums, relations, and other models must be exported so Drizzle Kit can import them.
3. `drizzle.config.ts` uses `schema` for the schema file/folder/glob/array and `out` for the migration output folder.
4. `out` defaults to `drizzle`.
5. The codebase-first committed SQL flow is `drizzle-kit generate` followed by `drizzle-kit migrate`.
6. `drizzle-kit push` and `drizzle-kit pull` are documented alternatives for schema push and database-first/introspection workflows.
7. `drizzle-kit check` walks the generated migration history for collisions and race conditions, useful when several branches alter the schema.
8. `drizzle-kit up` upgrades snapshots of previously generated migrations; `drizzle-kit export` prints the schema as raw SQL DDL.
9. Drizzle serverless performance guidance recommends declaring connection and prepared statement objects outside handler scope when the runtime can reuse module scope.
10. Drizzle relations and RQB require the relevant schema/tables/relations to be available at `drizzle()` initialization when using relational queries.
11. Drizzle validation integrations include zod, valibot, typebox, arktype, typebox-legacy, and effect-schema.
12. `drizzle-orm/netlify-db` (0.45.3) reads `NETLIFY_DB_URL` and `NETLIFY_DB_DRIVER`, and accepts an explicit client when the caller owns the driver.
13. 0.45.2 fixed escaping in `sql.identifier()` and `sql.as()`, closing a possible SQL injection path (CWE-89).
14. 0.45.4 fixed postgres-js not using prepared queries on an explicit `.prepare(name)`.

## Next.js Architecture Implications

- `src/db/schema`, `src/db/repositories`, and `src/db/client.server.ts` are Hypercore local conventions, not Drizzle or official Next.js requirements.
- The project should choose one discoverable schema path and make `drizzle.config.ts` point at it.
- DB client creation and repository helpers belong in server-only modules. Client Components and client hooks must not import them.
- Server Components may call server-only DAL/repository functions directly. Route Handlers should be reserved for HTTP-native endpoints, not internal data bridges.
- Server Actions must still validate input and re-check auth/authz before Drizzle writes, even when Drizzle validation integrations derive insert/update schemas.
- Record whether the repo uses `generate` + `migrate`, `push`, `pull`, or another migration policy before changing migration folders or scripts.
- Pin `drizzle-orm` at 0.45.2 or newer; older minors expose the identifier-escaping injection path.
- Check the installed version's column API before copying a docs example. The documentation site leads with the v1.0 API (`p.pgTable("users", { id: p.serial().primaryKey() })`) while stable 0.45 projects use `serial('id')` and friends.

## Drift Watchlist

- Re-check exact Drizzle Kit CLI command names and config properties against the installed `drizzle-kit` version.
- Re-check dialect-specific driver imports and runtime support before changing serverless, Edge, Neon, D1, Turso/libSQL, Netlify DB, or Postgres connection code.
- Re-check validation integration package names and generation APIs before adding new generated schemas.
- Watch the 1.0 release: the docs site is reorganizing around it, and adopting it changes the column-builder API.

## Sources

> Checked 2026-11-04. Release facts come from the GitHub releases feed and the 0.45.2 / 0.45.3 release notes; command and config facts come from the `orm.drizzle.team` documentation pages listed above; the stable version pin was confirmed against the npm `latest` dist-tags for `drizzle-orm` and `drizzle-kit`.

| Claim | Source |
|---|---|
| The stable versions and pre-release status in "Installed-Version Baseline" | `https://github.com/drizzle-team/drizzle-orm/releases` and the npm `latest` / `rc` dist-tags |
| The security and driver facts (13, 14, 12) | `https://github.com/drizzle-team/drizzle-orm/releases/tag/0.45.2` and `/releases/tag/0.45.3` |
| The Drizzle behavior recorded in "Official Facts" above | the `orm.drizzle.team` documentation pages listed under "Source URLs" |
| The placement and boundary guidance in "Next.js Architecture Implications" above | those same Drizzle pages plus `references/official/nextjs/nextjs-docs.md` for the Next.js server-boundary rules; the `src/db/...` naming is a Hypercore local convention, not an official requirement |
