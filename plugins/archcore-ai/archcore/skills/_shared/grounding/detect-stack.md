# Stack detection catalog

Reference data for `/archcore:init` Step A.1 (Detect sub-phase). Edit this file to extend detection; the skill reads it at runtime.

## What it detects

The stack = the load-bearing technologies a contributor must respect: the language(s); the primary framework/runtime/engine that owns the entry point; the persistence mechanism; and any dominant domain library that defines how code is written here. "Framework" is whatever plays that role in the ecosystem at hand — a web framework, an ML library (PyTorch), a game engine (Unity/Unreal/Godot), an IaC tool (Terraform), a data tool (dbt), or an in-house framework — not only the web frameworks in the examples below. The target is the small set of technologies whose choice a newcomer cannot silently override, in any language, domain, or stack.

## How to find it (any codebase)

1. **Find the manifest(s)** of WHATEVER ecosystem is present (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `composer.json`, `*.csproj`, `pom.xml`/`build.gradle`, `mix.exs`, `Package.swift`, `deps.edn`, `pubspec.yaml`, `*.opam`, `build.sbt`, `CMakeLists.txt`, etc.). Polyglot repos may have several — collect from each.
2. **Read the direct dependencies** (top-level only — never transitive) and rank by fan-in: which packages are imported across the most files. The highest fan-in direct deps are stack candidates; one-off utilities are not.
3. **Open the entry file(s)** (see `detect-entrypoints`) and read their imports — the framework/primary lib is whatever the entry point pulls in and hands control to (the server, the app object, the engine init, the pipeline runner).
4. **Cross-check the evidence**: the dominant source file types, the build/config files (lockfiles, CI, container/IaC manifests), and what the code actually does at runtime should converge on the same candidate.
5. **Fill each stack slot** (framework/primary lib, persistence, UI, state, test runner) with the candidate carrying the strongest converging evidence — highest fan-in, imported by the entry file, present across the codebase. A dominant domain library names the stack even when it is not a web framework (emit "Build with PyTorch", "Build with Terraform", "Build with Unity", or an in-house framework's own name).
6. **Reject incidental signals**: a `fastapi`/`express` present only for a `/health` endpoint, a docs site folded in via polyglot scanning, a peerDependency on a component library, or an example/tooling package must NOT set the repo's primary framework. Re-derive the slot from evidence rather than dropping it.
7. **No recognized manifest** → fall back to file-extension majority vote on top-level source dirs (`src/`, `lib/`, `app/`, or repo root); max 2 languages; then read the dominant files' imports for the framework slot.
8. **Multiple equally load-bearing candidates** in one slot (e.g. both `react` and `vue` in a monorepo) → pick the one in the most top-level manifests, or ask the user to disambiguate on a tie.

Emit a signal only on positive evidence; when no candidate is unambiguous, prefer omission over a guess — never invent.

## Common signals (non-exhaustive examples)

These are non-exhaustive examples to orient pattern-matching — absence from this list is NOT absence of signal; fall back to the method above for anything not shown.

**Manifests → ecosystem:** `package.json` (JS/TS), `pyproject.toml`/`Pipfile`/`requirements.txt` (Python), `Cargo.toml` (Rust), `go.mod` (Go), `Gemfile` (Ruby), `composer.json` (PHP), `*.csproj`/`*.fsproj` (.NET), `pom.xml`/`build.gradle[.kts]` (Java/Kotlin), `mix.exs` (Elixir), `Package.swift` (Swift).

| Slot | Example signals (illustrative, not a checklist) |
|------|--------------------------------------------------|
| Framework (web/app) | `next`, `nuxt`, `remix`, `astro`, `sveltekit`, `@nestjs/core`, `express`, `fastify`, `hono`; `django`, `flask`, `fastapi`, `starlette`; `rails`, `sinatra`; `gin`, `echo`, `fiber`, `chi`; `actix-web`, `axum`, `rocket`; `spring-boot-starter`, `ktor-server-core`; `laravel/framework`, `symfony/symfony` |
| Framework (other domains) | `torch`/`tensorflow`/`jax` (ML); Unity/Unreal/Godot (games); `terraform`/`pulumi`/`cdktf` (IaC); `dbt` (data); an agent/LLM plugin (Claude Code / agent host: skills + commands in Markdown, a `marketplace.json`/`plugin.json`); any in-house framework that owns the entry point |
| Runtime | `node` (engines), `bun`, `deno` |
| Persistence (lib + store) | `prisma`, `drizzle-orm`, `typeorm`, `sequelize`, `mongoose`, `kysely`; `sqlalchemy`, Django ORM, `tortoise-orm`, `psycopg`, `asyncpg`, `pymongo`; `activerecord`, `sequel`; `gorm`, `ent`, `pgx`; `diesel`, `sqlx`, `sea-orm`; Spring Data. Infer the store (postgres/mysql/sqlite/mongodb) from driver names. |
| UI | `react`, `vue`, `svelte`, `solid-js`, `preact`, `@angular/core`, `lit`, `htmx.org`, `qwik` |
| Styling | `tailwindcss`, `styled-components`, `@emotion/*`, `sass`, `vanilla-extract`, `@mui/material`, `@mantine/core`, `@chakra-ui/react` |
| State | `redux`/`@reduxjs/toolkit`, `zustand`, `jotai`, `valtio`, `mobx`, `xstate`, `effector`, `pinia` |
| Test runner (primary only) | `vitest`, `jest`, `playwright`, `cypress`; `pytest`; `rspec`, `minitest`; `phpunit`; `cargo test`, `go test`; `junit` |

**Do NOT count as stack signal** (tooling/plumbing, even when in direct deps): `@types/*`, `eslint*`, `prettier*`, `typescript` (infer TS from `.ts` files), `@babel/*`, build tools (`webpack`, `vite`, `rollup`, `esbuild`, `swc`, `turbopack`), `husky`, `lint-staged`, `dotenv*`, and generic utilities (`chalk`, `commander`, `yargs`, `fs-extra`, `chokidar`).

## Rule template

Start from this skeleton. Drop any line whose placeholder has no detected signal. Never leave `{…}` unfilled. The body must be ≤ 6 lines total.

```
Code in {language(s)}.
Build with {framework} (do not introduce alternative frameworks without an ADR).
Persist via {persistence-lib} when adding storage; default to {primary-store}.
Style with {styling-lib} classes/components; do not introduce alternative styling.
Manage state with {state-lib}.
Test with {test-runner} as the primary runner.
```

Examples of valid composed outputs:

```
Code in TypeScript.
Build with Next.js (do not introduce alternative frameworks without an ADR).
Persist via Prisma when adding storage; default to PostgreSQL.
Style with Tailwind classes; do not introduce alternative styling.
Manage state with Zustand.
```

```
Code in Python.
Build with PyTorch (do not introduce alternative frameworks without an ADR).
Test with pytest as the primary runner.
```

## Output

`SKILL.md` Phase E fires the `create_document`; this catalog supplies the rule body per the template above.

| Field | Value |
|---|---|
| `type` | `rule` |
| `directory` | `conventions` |
| `filename` | `project-stack` |
| `title` | `Project stack` |
| `status` | `accepted` |
| `tags` | `['stack', 'conventions']` |

Body cap: ≤ 6 lines.
