Stack guide inside `hyper-architecture` for Axum. Read it when `rules/stack-detection.md` routes a target to Axum; from then on this file owns that target's work.

- Scope: Use this skill when building, reviewing, restructuring, or auditing an Axum (Rust) HTTP server architecture: project and module structure, Router composition, handlers and extractors, tower and tower-http middleware, request validation, SQLx persistence and migrations, error handling, OpenAPI/Swagger contracts, testing, and tokio server bootstrap. Do not use it for non-Axum Rust frameworks such as Actix Web, Rocket, Poem, or warp, for client-only Rust code, for copy-only edits that cross no architecture boundary, or for requests that want official crate defaults with no Hypercore conventions.
- Runtime needs: Requires an Axum project or an explicit request to create one. Version and API claims need the official axum, tower, tower-http, sqlx, utoipa, and validator documentation plus local Cargo.toml and Cargo.lock inspection. No bundled script; `cargo check`, `cargo clippy`, and the project test suite are the verification surface.

@architecture-rules.md
@../../rules/axum/project-structure.md
@../../rules/axum/routes.md
@../../rules/axum/handlers.md
@../../rules/axum/middleware.md
@../../rules/axum/validation.md
@../../rules/axum/database.md
@../../rules/axum/openapi.md
@../../rules/axum/errors.md
@../../rules/axum/testing.md
@../../rules/axum/platform.md
@../../rules/axum/conventions.md
@../../references/official/axum/axum-docs.md
@../../references/official/axum/tower-docs.md
@../../references/official/axum/sqlx-docs.md
@../../references/official/axum/utoipa-docs.md
@../../references/official/axum/ecosystem-docs.md

# Axum Architecture Enforcement

<output_language>

Default all user-facing deliverables, saved artifacts, reports, plans, generated docs, summaries, handoff notes, commit/message drafts, and validation notes to Korean, even when this canonical skill file is written in English.

Preserve source code identifiers, CLI commands, file paths, crate names, type names, JSON/YAML field names, API names, and quoted source excerpts in their required or original language.

Use a different language only when the user explicitly requests it, an existing target artifact must stay in another language for consistency, or a machine-readable contract requires exact English tokens.

</output_language>

<purpose>

- Enforce Hypercore Axum architecture rules/axum before code changes.
- Confirm the target is actually an Axum server before applying Axum-specific gates.
- Keep composition, handlers and extractors, tower middleware, validation, SQLx persistence, migrations, error handling, OpenAPI contracts, testing, and server bootstrap coherent.
- Apply the same architecture concerns this repository applies to its other server stacks, translated to Rust ownership and type rules/axum instead of copied syntax.
- Label stricter-than-axum requirements as Hypercore conventions when reporting findings.

</purpose>

<routing_rule>

Use this skill for Axum server implementation, review, remediation, or architecture enforcement.

Do not force this skill onto Actix Web, Rocket, Poem, warp, or other Rust web frameworks, onto client-only or embedded Rust, onto copy-only changes that do not cross an architecture boundary, or onto requests where the user explicitly wants official crate defaults without Hypercore conventions.

This skill is self-contained. Do not block on another skill's installation, path, or invocation to apply Axum rules.

</routing_rule>

<instruction_contract>

| Field | Contract |
|---|---|
| Intent | Keep Axum servers architecturally safe, typed, observable, documented, and aligned with official crate behavior plus labelled Hypercore conventions. |
| Trigger | Axum work involving structure, Router composition, handlers, extractors, middleware, validation, SQLx, migrations, OpenAPI, errors, tests, or bootstrap. |
| Scope | Review and guide touched Axum source, `Cargo.toml`, migrations, topic rule files, official references, and small reversible architecture fixes. |
| Authority | User and project instructions outrank this skill. Official crate documentation outranks Hypercore conventions for API facts. Safety, typing, validation, and data-boundary rules/axum block unsafe changes. |
| Evidence | Use repository indicators, `Cargo.toml`/`Cargo.lock`, touched paths, topic rules/axum, official references when drift matters, and compiler/test output. |
| Tools | Use local search, read, edit, `cargo check`, `cargo clippy`, `cargo test`, and a local HTTP smoke request. Gate migrations, credential access, production side effects, runtime swaps, and broad rewrites. |
| Loop | No optimization loop. After a remediation pass, allow at most two verify-repair iterations against the Step 3 gates and the touched checks; keep a change only when it stays inside the touched scope and passes those gates. |
| Output | Korean architecture finding or implementation summary with rule classification, changed files, validation evidence, remaining risks, and official-versus-Hypercore labels. |
| Verification | Run the relevant `cargo` checks and the final checklist for touched surfaces, plus one real request against a running server when the changed surface is reachable. |
| Stop condition | Stop after project mode is known, applicable gates pass or are reported as blockers, and validation evidence is recorded. |

</instruction_contract>

<activation_examples>

Positive examples:

- `Review this Axum service structure before I add more routes.`
- `Refactor an Axum API so routing, state, middleware, and error handling follow one architecture.`
- `Add a new Axum route and keep extractor ordering and typed rejections correct.`
- `Wire SQLx into this Axum API without handlers touching the pool directly.`
- `Review the SQLx migration and OpenAPI boundaries before adding a persisted endpoint.`
- `hyper-architecture 전체 수정`

Negative examples:

- `Create a generic Actix Web middleware guide.`
- `Review a React SPA that has no Rust server.`

Boundary examples:

- `Make a tiny copy-only change to an Axum health response string.` Direct editing can be enough when no architectural boundary is affected.
- `Use official Axum defaults only, without the extra Hypercore conventions.` This skill still applies, but Hypercore-only strictness that exceeds the official docs is relaxed.
- `This repository has a Hono API and a Rust Axum worker.` This skill owns only the Axum worker; the other server keeps its own architecture rules.

</activation_examples>

<trigger_conditions>

Arguments change the remediation scope, not the core rules.

| Argument | Meaning |
|---|---|
| missing | Review and fix the requested or touched Axum scope. Untouched legacy drift may be reported as backlog when it is Hypercore-only or risky to migrate. |
| `전체 수정` | Full-remediation mode. Scan the whole detected Axum server and fix every violation that is safe, local, reversible, and verifiable. Do not stop at touched files. |
| `full fix` / `fix all` | Same as `전체 수정`. |
| `공식 기본만` / `official defaults only` | Use official crate behavior as the default surface and downgrade Hypercore-only conventions to optional findings unless the user also asks for `전체 수정`. |

In `전체 수정` mode:

- Treat all Rust sources, `Cargo.toml` files, route modules, handlers, extractors, middleware, SQLx queries and migrations, OpenAPI definitions, tests, and the bootstrap entrypoint as in scope.
- Scan module and file names across the detected Axum crate. Rust source modules must be `snake_case`; do not rename them to kebab-case.
- Apply every low-risk auto-remediation in Step 3.5 across the whole crate, not only touched files.
- For risky changes that cannot be completed safely in the same run, leave a precise blocker or backlog item with file paths and the failed rule. Do not silently ignore it.

</trigger_conditions>

<skill_architecture>

- Core (`stacks/axum/core.md`): trigger, contract, gate order, remediation policy, verification, stop condition.
- Rules: `stacks/axum/architecture-rules.md` plus the topic files mapped in `reference_routing`.
- References: `references/official/axum/axum-docs.md`, `tower-docs.md`, `sqlx-docs.md`, `utoipa-docs.md`, and `ecosystem-docs.md` hold dated official facts.
- Assets: `assets/evals/axum-cases.jsonl` holds trigger and behavior cases.
- No bundled script: `cargo check`, `cargo clippy`, `cargo test`, and one live request are the verification surface.

</skill_architecture>

<loop_policy>

- No optimization loop. One review or remediation pass per request.
- After remediation, at most two verify-repair iterations run against the Step 3 gates and the touched checks. A change stays only when it is inside the touched scope and passes those gates.
- The loop ends at the first passing checklist or at a reported blocker; it never widens the touched scope to reach a green result.

</loop_policy>

<language_and_translation_default>

Write findings, remediation summaries, and validation notes in Korean. Keep identifiers, paths, crate names, type names, and the labels `official` and `hypercore-only` in their source form so a report maps one-to-one onto the rule files. `stacks/axum/core.ko.md` mirrors this file section by section; a rule changed here is changed there in the same edit.

</language_and_translation_default>

<reference_routing>

Read `stacks/axum/architecture-rules.md` before editing. Then open the one file that owns the touched surface:

| Touched surface | File |
|---|---|
| Project profiles, crate/module ownership, dependency direction, workspaces, structural migration | `rules/axum/project-structure.md` |
| Router composition, nesting and merging, path syntax, fallbacks, version prefixes | `rules/axum/routes.md` |
| Handler signatures, extractor order, `State`, `Path`/`Query`/`Json`, typed rejections | `rules/axum/handlers.md` |
| tower layers, `from_fn`, `route_layer`, layer order, tower-http stack, `HandleErrorLayer` | `rules/axum/middleware.md` |
| serde and `validator` boundaries, custom validating extractors, error mapping | `rules/axum/validation.md` |
| SQLx pool, queries, offline mode, migrations, transactions, repository boundaries | `rules/axum/database.md` |
| utoipa and utoipa-axum definitions, spec endpoints, Swagger UI gating, contract drift | `rules/axum/openapi.md` |
| `AppError`, `IntoResponse`, error envelopes, 404/405 behavior | `rules/axum/errors.md` |
| `tower::ServiceExt::oneshot`, `axum-test`, integration and database tests | `rules/axum/testing.md` |
| `main.rs` bootstrap, configuration, `axum::serve`, graceful shutdown, tracing | `rules/axum/platform.md` |
| Rust naming, modules, imports, clippy and style for any touched file | `rules/axum/conventions.md` |
| Latency, throughput, release profile, SQLx pool sizing, compression, timeout layers, memory, binary size | `rules/axum/performance.md` |
| Lint, format, clippy, rustfmt, toolchain pinning, workspace lints, CI check order | `rules/setup/rust.md` |
| Official axum behavior behind a rule, or an explicit official-defaults request | `references/official/axum/axum-docs.md` |
| tower and tower-http behavior behind `rules/axum/middleware.md` claims | `references/official/axum/tower-docs.md` |
| SQLx behavior behind `rules/axum/database.md` claims | `references/official/axum/sqlx-docs.md` |
| utoipa behavior behind `rules/axum/openapi.md` claims | `references/official/axum/utoipa-docs.md` |
| `validator`, `axum-test`, `thiserror`, and `tracing` behavior behind validation, testing, error, and platform claims | `references/official/axum/ecosystem-docs.md` |

When the user asks for official defaults, start from the official references, treat Hypercore-only rules/axum as optional overlays, and label which findings are which.

</reference_routing>

<support_file_read_order>

1. `stacks/axum/architecture-rules.md` for the rule taxonomy and gate summary.
2. The topic file for the touched surface, in `reference_routing` order.
3. `rules/axum/conventions.md` before editing any file's naming or style.
4. `references/official/axum/axum-docs.md` when official behavior or an official-defaults request is in play.
5. The reference that backs the claim: `tower-docs.md` for layers, `sqlx-docs.md` for database behavior, `utoipa-docs.md` for the API contract, `ecosystem-docs.md` for validation, testing, error, and logging crates.

</support_file_read_order>

<workflow>

| Step | Task | Output |
|---|---|---|
| 1 | Prove the target is an Axum server | Scope decision |
| 2 | Load the rule files for the touched surface | Minimal evidence set |
| 3 | Judge planned changes against the critical gates | Findings with file paths |
| 3.5 | Apply low-risk auto-remediations inside the touched scope | Edits or backlog items |
| 4 | Implement in the file order below, then verify | Changed files and evidence |

Step 1 — project validation: run the discovery commands in `rules/axum/project-structure.md` (Axum indicators, persistence indicators, and the full-crate inventory for `전체 수정` mode), plus the routing check in `rules/stack-detection.md`. If the Axum indicators are absent, stop and route back to the normal implementation or review path instead of forcing Axum rules.

Step 3 — critical gates. Brownfield rule: untouched legacy style drift can become backlog; safety, typing, validation, persistence, OpenAPI, and runtime boundary issues still block touched work; in `전체 수정` mode the whole detected Axum crate is the touched scope. Use the detailed checklists in the linked support files for remediation detail; this core does not restate them.

- One composition root returns `Router`, and `main.rs` only bootstraps it; state is provided once with `with_state`.
- Handlers do not hold SQL, pool creation, or migration logic; persistence stays behind repositories.
- Body-consuming extractors are last, shared state is extracted before the body, and user input is never `unwrap()`ed.
- Layers are composed with an explicit order, fallible layers have a `HandleErrorLayer` or equivalent, and `route_layer` is used where a layer must not run on unmatched routes.
- Request DTOs use serde plus a `validator` boundary when rules/axum exceed type shape, and validation failures map to one stable error envelope.
- SQLx queries, transactions, and migrations stay behind the database/service boundary; migrations are committed and never applied by a request handler.
- Public documented routes keep runtime schemas, response types, and the utoipa spec aligned; Swagger UI exposure matches the environment policy.
- One `AppError` implements `IntoResponse`; internal error text, SQL, and secrets never reach the response body.
- Bootstrap code owns `axum::serve`, signal handling, tracing initialization, and configuration validation; route modules never bind ports.
- Rust modules and files use `snake_case`, and `cargo clippy` has no newly introduced warnings on touched code.

Step 3.5 — auto-remediation. Auto-fix directly when the issue is local, reversible, and low-risk:

- Reorder extractor parameters so the body-consuming extractor is last.
- Move a direct `sqlx` query from a handler into the existing repository or service for that domain.
- Replace `pool.clone()`-per-request or `PgPool::connect` inside a handler with the shared `AppState` pool.
- Add a missing repository wrapper for a touched query, or a missing service call for touched orchestration.
- Add `FromRef` substates instead of passing the whole `AppState` into unrelated handlers.
- Convert a direct `sqlx::Error` response into the existing `AppError` translation.
- Add missing `utoipa` annotations to a touched public route when the repository already publishes a spec.
- Move `axum::serve` or listener binding out of a route module into the binary entrypoint.
- Rename touched `camelCase` or `kebab-case` Rust modules to `snake_case` and update `mod` declarations and imports in the same change.

Do not auto-apply broad or potentially breaking migrations without explicit justification: whole-app layer rewrites, ORM or driver swaps, schema table/column/index renames, applying or deleting production migrations, transaction-boundary rewrites without tests, RPC or response-shape changes that break clients, runtime or async-runtime swaps, and adding a new architecture layer across the crate.

Step 4 — implementation order:

1. Validate current structure and rule breaches. In `전체 수정` mode, inventory the whole detected Axum crate before editing.
2. Fix module and file naming where safe, because later imports and tests depend on stable paths.
3. Fix Router composition, state wiring, and routing order.
4. Fix handler and extractor typing, then validation boundaries.
5. Fix database, repository, transaction, and migration boundaries for touched persistence behavior.
6. Fix middleware composition and error translation.
7. Fix OpenAPI metadata and response contracts for touched public routes.
8. Fix bootstrap, configuration, and observability at the edge.
9. Run verification.

</workflow>

<required>

- A proven Axum server before any Axum rule is applied, and a named reason when the request lands outside an Axum scope.
- One `Router` composition function separate from `main.rs`, with state applied once and routing order stated.
- The repo's existing layering preserved: handlers never reach the SQLx pool, schema, or migration runner directly.
- Correct extractor ordering, typed state, and request validation on non-trivial input.
- A report that labels each finding `official` or `hypercore-only`.
- Verification evidence from `cargo check`, `cargo clippy`, `cargo test`, and one live request where the changed surface is reachable.

</required>

<forbidden>

- Forcing Axum rules/axum on Actix Web, Rocket, Poem, warp, or another framework because the request sounds similar.
- Renaming or applying production migrations, or changing schema table/column/index names, without explicit authority.
- Swapping the async runtime, database driver, ORM, or TLS backend inside an architecture review.
- Breaking existing clients by changing response shapes without a recorded decision.
- Presenting a Hypercore convention as official axum behavior.
- Silencing a blocking gate because untouched legacy code shows the same pattern.
- Claiming a check ran when it did not, or reporting a gate as passed without its output.

</forbidden>

<validation>

- [ ] Axum project detection confirmed from a read manifest or source file.
- [ ] The touched surface's rule file was read, and official-defaults mode applied when requested.
- [ ] Touched Rust modules and files use `snake_case`; in `전체 수정` mode the whole crate was scanned.
- [ ] A single `Router` composition function exists and `main.rs` only bootstraps it.
- [ ] State is provided once with `with_state`, and substates use `FromRef` where justified.
- [ ] Extractor order is valid and the body-consuming extractor is last.
- [ ] Non-trivial request DTOs are validated before service logic.
- [ ] Touched handlers do not import SQLx query macros or create pools directly.
- [ ] SQLx query mode (compile-time checked or offline) and migration provenance are consistent with the repository setup.
- [ ] Transactions are explicit for affected multi-step writes.
- [ ] OpenAPI definitions and Swagger UI exposure are updated and environment-appropriate for touched documented routes.
- [ ] One `AppError`/`IntoResponse` policy exists and does not leak internals.
- [ ] API DTOs, OpenAPI schemas, and response types do not expose raw database rows or internal fields.
- [ ] Bootstrap code owns serve, shutdown, tracing, and config validation.
- [ ] `cargo check`, `cargo clippy`, and touched tests were run, and one live request was exercised where reachable.
- [ ] Final findings distinguish official axum rules/axum from Hypercore conventions.

</validation>

## Sources

> Checked 2026-11-05.

| Claim | Source |
|---|---|
| Axum 0.8 route path syntax, extractor order, `State`, `Router` state generics, layer ordering, `route_layer`, and middleware behavior | [axum docs](https://docs.rs/axum/latest/axum/), [Router](https://docs.rs/axum/latest/axum/struct.Router.html), [extract](https://docs.rs/axum/latest/axum/extract/index.html), [middleware](https://docs.rs/axum/latest/axum/middleware/index.html), [State](https://docs.rs/axum/latest/axum/extract/struct.State.html) |
| Axum 0.8.0 breaking changes and 0.8.9 MSRV 1.80 | [axum CHANGELOG](https://github.com/tokio-rs/axum/blob/main/axum/CHANGELOG.md) |
| `FromRequestParts` no longer requires `#[async_trait]` in the 0.8 line | [axum-core CHANGELOG](https://github.com/tokio-rs/axum/blob/main/axum-core/CHANGELOG.md) |
| `validator`, `axum-test`, `tower::ServiceExt` capabilities | [validator](https://docs.rs/validator/latest/validator/), [axum-test](https://docs.rs/axum-test/latest/axum_test/), [ServiceExt](https://docs.rs/tower/latest/tower/util/trait.ServiceExt.html) |
| SQLx 0.9 feature names, query macros, offline mode, migrations, transactions | [sqlx README](https://github.com/launchbadge/sqlx/blob/main/README.md), [sqlx CHANGELOG](https://github.com/launchbadge/sqlx/blob/main/CHANGELOG.md), [SQLx docs](https://docs.rs/sqlx/latest/sqlx/) |
| utoipa 6, utoipa-axum 0.3, utoipa-swagger-ui 10 behavior and MSRV | [utoipa CHANGELOG](https://github.com/juhaku/utoipa/blob/master/utoipa/CHANGELOG.md), [utoipa-axum](https://docs.rs/utoipa-axum/latest/utoipa_axum/) |
| The `[Hyper]`-style trigger-first description, the bilingual package shape, and the one-level reference rule | `instructions/skill/SKILL_AUTHORING.md` |
| Keeping the loaded head stable when names and descriptions change | `instructions/cache/CACHE.md` |

### Evidence grade

The Axum, tower, SQLx, and utoipa statements are `VENDOR` facts taken from each project's own documentation and changelog at the dated snapshot. The layering and naming rules/axum are this repository's conventions, marked `hypercore-only` where they exceed official crate guidance.
