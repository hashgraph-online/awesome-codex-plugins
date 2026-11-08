Stack guide inside `hyper-architecture` for Hono. Read it when `rules/stack-detection.md` routes a target to Hono; from then on this file owns that target's work.

- Scope: Use this skill when the user asks to build, audit, or restructure a Hono application, or to introduce Hono into an existing codebase, and the work touches app composition, route modules, middleware, validation, database or ORM boundaries, Drizzle, migrations, error handling, OpenAPI/Swagger, testing, or typed RPC. It enforces Hono architecture rules/hono before code changes. Do not use it for non-Hono frameworks, copy-only edits that cross no architecture boundary, or requests that want official Hono defaults with no Hypercore conventions.
- Runtime needs: Works best with repo inspection, official Hono docs verification, and direct code edits in Hono applications.

@architecture-rules.md
@../../rules/hono/project-structure.md
@../../rules/hono/routes.md
@../../rules/hono/handlers.md
@../../rules/hono/middleware.md
@../../rules/hono/validation.md
@../../rules/hono/database.md
@../../rules/hono/openapi.md
@../../rules/hono/errors.md
@../../rules/hono/testing-rpc.md
@../../rules/hono/platform.md
@../../rules/hono/conventions.md
@../../references/official/hono/hono-docs.md
@../../references/official/hono/drizzle-docs.md

# Hono Architecture Enforcement

<output_language>

Default all user-facing deliverables, saved artifacts, reports, plans, generated docs, summaries, handoff notes, commit/message drafts, and validation notes to Korean, even when this canonical skill file is written in English.

Preserve source code identifiers, CLI commands, file paths, schema keys, JSON/YAML field names, API names, package names, proper nouns, and quoted source excerpts in their required or original language.

Use a different language only when the user explicitly requests it, an existing target artifact must stay in another language for consistency, or a machine-readable contract requires exact English tokens. If a localized template or reference exists (for example `*.ko.md` or `*.ko.json`), prefer it for user-facing artifacts.

</output_language>

<purpose>

- Enforce Hypercore Hono architecture rules/hono before code changes.
- Confirm the target is actually a Hono project before applying Hono-specific gates.
- Keep route composition, handlers, middleware, validation, database/ORM, Drizzle, OpenAPI/Swagger, platform entrypoints, error handling, testing, and typed RPC boundaries coherent.
- Label stricter-than-Hono requirements as Hypercore conventions when reporting findings.

</purpose>

<routing_rule>

Use this skill for Hono app implementation, review, remediation, or architecture enforcement.

Do not force this skill onto non-Hono projects, generic Express/Fastify work, copy-only changes that do not cross an architecture boundary, or requests where the user explicitly wants official Hono defaults without Hypercore conventions.

This skill is self-contained. Do not block on global skills or external orchestration surfaces just to apply Hono rules.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Keep Hono projects architecturally safe, typed, documented, and aligned with official Hono behavior plus labelled Hypercore conventions. |
| Trigger | Hono work involving routes, handlers, middleware, validation, DB/ORM, Drizzle, OpenAPI, platform entrypoints, error handling, testing, or RPC. |
| Scope | Review and guide touched Hono source, topic rule files, official references, validation notes, and small reversible architecture fixes. |
| Authority | User/project instructions outrank this skill. Official Hono/Drizzle docs outrank Hypercore conventions for API facts. Safety, typing, validation, and data-boundary rules/hono block unsafe changes. |
| Evidence | Use project indicators, local package/source files, touched paths, topic rules/hono, official references when drift matters, and validation command output. |
| Tools | Use local search/read/edit/validation commands; gate migrations, credential access, production side effects, runtime adapter swaps, and broad rewrites. |
| Loop | Use no optimization loop. After a remediation pass, allow at most two verify-repair iterations against the Step 3 gates and the touched checks; keep a change only when it stays inside the touched scope and passes those gates, and stop when the verification checklist passes or a blocker is reported. |
| Output | Korean architecture finding or implementation summary with rule classification, changed files if any, validation evidence, remaining risks, and official-vs-Hypercore labels. |
| Verification | Run the relevant project checks and the final checklist for touched surfaces before declaring completion. |
| Stop condition | Stop after project mode is known, applicable gates pass or are reported as blockers, and validation evidence is recorded. |

</instruction_contract>

<activation_examples>

Positive examples:

- `Review this Hono app structure before I add more routes.`
- `Refactor a Hono API so routing, middleware, and validators follow one architecture.`
- `Add a new Hono route and make sure testClient and AppType inference still work.`
- `Wire Drizzle into this Hono API without routes talking to the database directly.`
- `Review database, migration, and OpenAPI boundaries before adding a new persisted endpoint.`
- `hyper-architecture 전체 수정`
- `Run the Hono architecture skill in full-remediation mode.`

Negative examples:

- `Create a generic Express middleware guide.`
- `Review a React SPA that does not use Hono.`

Boundary examples:

- `Make a tiny copy-only response text change in a Hono handler.`
  Direct editing can be enough if no architectural boundary is affected.
- `Use official Hono defaults only, not the extra hypercore conventions.`
  This skill still applies, but hypercore-only strictness that exceeds the official docs is relaxed.

</activation_examples>

<trigger_conditions>

Arguments change the remediation scope, not the core rules.

| Argument | Meaning |
|---|---|
| missing | Review and fix the requested or touched Hono scope. Untouched legacy drift may be reported as backlog when it is hypercore-only or risky to migrate. |
| `전체 수정` | Full-remediation mode. Scan the whole detected Hono application and fix every violation that is safe, local, reversible, and verifiable. Do not stop at touched files. |
| `full fix` / `fix all` | Same as `전체 수정`. |
| `공식 기본만` / `official defaults only` | Use official Hono behavior as the default surface and downgrade hypercore-only conventions to optional findings unless the user also asks for `전체 수정`. |

In `전체 수정` mode:

- Treat all Hono app files, route modules, handlers, middleware, validation schemas, OpenAPI files, database/repository boundaries, tests/RPC surfaces, and runtime entrypoints as in scope.
- Scan folder and file names across the detected Hono source tree. Folders and files must be kebab-case except framework or tool-required names such as `package.json`, `tsconfig.json`, `drizzle.config.ts`, lockfiles, generated declarations, and explicitly configured migration artifacts.
- Rename camelCase or PascalCase folders and files to kebab-case when imports, test paths, route references, and configuration references can be updated safely in the same change.
- Apply every low-risk auto-remediation in Step 3.5 across the app, not only touched files.
- For risky changes that cannot be completed safely in the same run, leave a precise blocker or backlog item with file paths and the failed rule. Do not silently ignore it.

</trigger_conditions>

<skill_architecture>

- Core (`stacks/hono/core.md`): trigger, contract, gate order, remediation policy, verification, stop condition.
- Rules: `stacks/hono/architecture-rules.md` plus the topic files mapped in `reference_routing`.
- References: `references/official/hono/hono-docs.md` and `references/official/hono/drizzle-docs.md` hold dated official facts.
- Assets: `assets/evals/hono-cases.jsonl` holds trigger and behavior cases.
- No bundled script: `testClient`, type checks, and the topic checklists are the verification surface.
- The skill is self-contained; it needs no other skill's path, document, or invocation.

</skill_architecture>

<loop_policy>

- No optimization loop. One review or remediation pass per request.
- After remediation, at most two verify-repair iterations run against the Step 3 gates and the touched checks. A change stays only when it is inside the touched scope and passes those gates.
- The loop ends at the first passing checklist or at a reported blocker; it never widens the touched scope to reach a green result.

</loop_policy>

<language_and_translation_default>

Write findings, remediation summaries, and validation notes in Korean. Keep identifiers, paths, folder names, API names, and the labels `official` and `hypercore-only` in their source form so a report maps one-to-one onto the rule files. `stacks/hono/core.ko.md` mirrors this file section by section; a rule changed here is changed there in the same edit.

</language_and_translation_default>

<reference_routing>

Read `stacks/hono/architecture-rules.md` before editing. Then open the one file that owns the touched surface:

| Touched surface | File |
|---|---|
| Project profiles, folder ownership, dependency direction, monorepos, structural migration | `rules/hono/project-structure.md` |
| Route composition, mount order, fallback placement, sub-app structure | `rules/hono/routes.md` |
| Handler extraction, `createFactory()`, `createHandlers()`, typed context flow | `rules/hono/handlers.md` |
| Shared request boundaries, auth/logging/request-id flow, `c.set()` / `c.get()` | `rules/hono/middleware.md` |
| Params/query/json/form validation choices | `rules/hono/validation.md` |
| Database clients, repositories, ORM boundaries, Drizzle schema, migrations, transactions, D1, Neon, Turso/libSQL, `DATABASE_URL` | `rules/hono/database.md` |
| OpenAPI generation, Swagger UI, operation metadata, schema drift, docs endpoints | `rules/hono/openapi.md` |
| `HTTPException`, `app.onError()`, response shaping | `rules/hono/errors.md` |
| `testClient()`, `hc<AppType>`, `AppType`, larger-app inference | `rules/hono/testing-rpc.md` |
| Adapters, entrypoints, bindings, env/config typing, `basePath()` boundaries | `rules/hono/platform.md` |
| Naming, TypeScript style, imports, comments for any touched file | `rules/hono/conventions.md` |
| Latency, throughput, router choice, response compression, ETag, shared cache, bundle size | `rules/hono/performance.md` |
| Lint, format, type-check, tsconfig, package manager, CI check order | `rules/setup/typescript.md` |
| Official Hono behavior behind a rule, or an explicit official-defaults request | `references/official/hono/hono-docs.md` |
| Drizzle behavior behind `rules/hono/database.md` claims | `references/official/hono/drizzle-docs.md` |

When the user asks for official defaults, start from `references/official/hono/hono-docs.md`, treat hypercore-only rules/hono as optional overlays, and label which findings are which.

</reference_routing>

<support_file_read_order>

1. `stacks/hono/architecture-rules.md` for the rule taxonomy and gate summary.
2. The topic file for the touched surface, in `reference_routing` order.
3. `rules/hono/conventions.md` before editing any file's naming or style.
4. `references/official/hono/hono-docs.md` when official behavior or an official-defaults request is in play.
5. `references/official/hono/drizzle-docs.md` when database behavior is in scope.

</support_file_read_order>

<workflow>

| Step | Task | Output |
|---|---|---|
| 1 | Prove the target is a Hono project | Scope decision |
| 2 | Load the rule files for the touched surface | Minimal evidence set |
| 3 | Judge planned changes against the critical gates | Findings with file paths |
| 3.5 | Apply low-risk auto-remediations inside the touched scope | Edits or backlog items |
| 4 | Implement in the file order below, then verify | Changed files and evidence |

Step 1 — project validation:

```bash
rg -n '"hono"|@hono/' package.json
rg -n "from 'hono'|from \"hono\"" src app .
rg -n "new Hono\\(|createFactory\\(|testClient\\(|hc<|OpenAPIHono|swaggerUI|hono/mount|methodNotAllowed|from '@hono/" src app .
```

If none of those indicators exist, stop and route back to the normal implementation or review path instead of forcing Hono rules.

When database work is in scope, also inspect database indicators:

```bash
rg -n '"drizzle-orm"|drizzle-kit|DATABASE_URL|D1Database|@neondatabase|@libsql|pg|postgres' package.json drizzle.config.ts src app .
rg -n "from 'drizzle-orm|from \"drizzle-orm|db\\.|transaction\\(|migrate\\(|schema|repositories?" src app .
```

When `전체 수정` mode is active, run broad discovery before editing:

```bash
rg --files src app routes 2>/dev/null
rg -n "new Hono\\(|app\\.route\\(|app\\.mount\\(|hono/mount|methodNotAllowed|basePath\\(|validator\\(|zValidator\\(|standardValidator\\(|OpenAPIHono|swaggerUI|testClient\\(|hc<|drizzle-orm|DATABASE_URL|D1Database|@neondatabase|@libsql" src app .
```

Step 3 — critical gates. Brownfield rule: untouched legacy style drift can become backlog; safety, typing, validation, persistence, OpenAPI, and runtime boundary issues still block touched work; in `전체 수정` mode the whole detected Hono app is the touched scope.

- One runtime-neutral Hono app and one obvious mount table; select the smallest justified structure profile and preserve dependency direction.
- Touched route modules do not bypass services to import DB/ORM/schema/SDK/runtime adapter details directly.
- Non-trivial params/query/json/form data uses validator middleware before domain logic; form/multipart validation requires Hono 4.13.16 or later.
- Extracted handlers preserve typing with inline chaining or `createFactory()` / `createHandlers()`.
- Middleware order and typed `Bindings`/`Variables` are explicit when shared context is used.
- Touched code avoids APIs deprecated in 4.x (`app.mount()`, `hono/<adapter>` imports, `@hono/node-ws`) and does not change the 404 contract implicitly by enabling `methodNotAllowed()`.
- Drizzle schemas, migrations, clients, and transactions stay behind database/service boundaries.
- Public documented routes keep runtime validation, DTOs, OpenAPI/Swagger, and RPC response shapes aligned.
- Runtime adapter and bootstrap code stays at the platform edge.
- Source folders and files use kebab-case unless a tool or external contract requires otherwise.

Use the detailed checklists in the linked support files for remediation detail; this core does not restate them.

Step 3.5 — auto-remediation. Auto-fix directly when the issue is local, reversible, and low-risk:

- Rename touched camelCase/PascalCase source folders or files to kebab-case and update imports and references.
- Add missing validator middleware to a touched route.
- Add a typed `AppType` export when a shared RPC or client contract depends on it.
- Move route mounting into a single composition file.
- Convert extracted untyped handlers to `createFactory()` / `factory.createHandlers()`.
- Add `app.onError()` or improve HTTP exception translation.
- Move runtime adapter imports out of handlers and route modules.
- Move touched direct database calls into existing services or repositories, and add the missing repository wrapper for a touched query.
- Centralize repeated database client imports into the existing database client boundary.
- Add missing OpenAPI metadata for touched public routes when the repo already publishes a spec.
- Move Swagger UI exposure behind the existing docs/admin/dev boundary.

Do not auto-apply broad or potentially breaking migrations without explicit justification: mass route or module renames (except kebab-case-only renames in `전체 수정` mode with every reference updated and verified), whole-app layer rewrites, repository-wide validation library swaps, RPC shape changes that break existing clients, runtime adapter swaps, database provider or ORM or dialect swaps, generating or applying or deleting production migrations, schema table/column/index renames, transaction boundary rewrites without tests, and switching OpenAPI generators across a whole app.

Step 4 — implementation order:

1. Validate current structure and rule breaches. In `전체 수정` mode, inventory the whole detected Hono app before editing.
2. Fix folder and file naming to kebab-case when safe, because later imports and tests depend on stable paths.
3. Fix route composition and typing boundaries.
4. Fix database, repository, and connection boundaries for touched persistence behavior, or for the full app in `전체 수정` mode.
5. Fix validation and middleware ordering.
6. Fix OpenAPI/Swagger contract drift for touched public routes, or for every documented route in `전체 수정` mode.
7. Fix error handling and response shaping.
8. Fix testing and RPC inference regressions.
9. Run verification.

</workflow>

<required>

- A proven Hono project before any Hono rule is applied, and a named reason when the request lands outside a Hono scope.
- One runtime-neutral app composition with an obvious mount table, and a structure profile justified by repository evidence.
- The repo's existing layering preserved: routes do not reach DB/ORM clients, schema tables, or migration helpers directly.
- Runtime validation on non-trivial request input, and typed `Bindings`/`Variables` wherever shared context is used.
- A report that labels each finding `official` or `hypercore-only`.
- Verification evidence from `testClient` / `hc` / type checks where those surfaces exist.

</required>

<forbidden>

- Forcing Hono rules/hono on Express, Fastify, or another framework because the request sounds similar.
- Renaming production migrations, applying migrations, or changing schema table/column/index names without explicit authority.
- Swapping runtime adapters, database providers, ORMs, dialects, or drivers inside an architecture review.
- Breaking existing RPC clients by changing response shapes without a recorded decision.
- Presenting a Hypercore convention as official Hono behavior.
- Silencing a blocking gate because untouched legacy code shows the same pattern.
- Claiming a check ran when it did not, or reporting a gate as passed without its output.

</forbidden>

<validation>

- [ ] Hono project detection confirmed.
- [ ] The touched surface's rule file was read, and official override mode applied when requested.
- [ ] Touched files and folders follow kebab-case naming; in `전체 수정` mode the whole source tree was scanned for violations.
- [ ] Route composition is obvious and mountable, and dependency direction is justified by repository evidence.
- [ ] Middleware order verified and typed context bindings are explicit.
- [ ] Validation is enforced on non-trivial inputs.
- [ ] Touched routes do not import DB/ORM clients, Drizzle schema tables, or migration helpers directly.
- [ ] Database client lifecycle is centralized and runtime-appropriate; schema and migration paths match the configured setup.
- [ ] Transactions are explicit for affected multi-step writes.
- [ ] OpenAPI/Swagger docs and Swagger UI exposure are updated and environment-appropriate for touched documented routes.
- [ ] Error handling policy is explicit and `testClient` / `hc` / `AppType` inference still works where applicable.
- [ ] API DTOs, OpenAPI schemas, and RPC response shapes do not expose raw ORM rows.
- [ ] Runtime adapter code stays at the edge.
- [ ] Final findings distinguish official Hono rules/hono from hypercore-only conventions.

</validation>
