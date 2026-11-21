# Project Discovery

**Purpose**: Read the project carefully and detect what shape of README it needs before drafting.

## 1. Shape detection signals

Detect the project type before choosing sections:

| Project type | Strong signals |
|---|---|
| **CLI** | `bin` field in `package.json`, `src/cli/*`, single executable script, `Cargo.toml` `[[bin]]`, Python `entry_points`/`console_scripts` |
| **Library** | `main`/`module`/`exports` in `package.json`, `lib/`, `src/index.*`, `Cargo.toml` `[lib]`, Python package without CLI entry |
| **Web app** | `next.config.*`, `vite.config.*`, `nuxt.config.*`, `app/` or `pages/`, framework deps in manifest |
| **Monorepo** | `packages/`, `apps/`, `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`, root `workspaces` field |
| **Plugin** | `.claude-plugin/`, `agents/`, `skills/`, plugin/marketplace manifest for an editor or platform |
| **Framework** | exposes templates, generators, or a `create-*` command |
| **Docs site** | `docusaurus.config.*`, `astro.config.*`, `mkdocs.yml`, `vitepress`, large `docs/` tree |
| **Service / API** | `Dockerfile`, `serve` script, server entry, route folder, no published library exports |

When signals overlap, prefer the dominant deliverable: a published package without an app entry is a library; a server with a published SDK may be both — document the primary use first and link to the secondary surface.

## 2. Files to inspect first

Read in this order before drafting:

1. Existing `README.md` (root and package-level if monorepo).
2. `AGENTS.md`, `CLAUDE.md`, `GEMINI.md` for language and convention hints.
3. `LICENSE` or `LICENSE.*`.
4. Manifest: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `deno.json`, `pubspec.yaml`.
5. Lockfile to confirm package manager: `pnpm-lock.yaml`, `package-lock.json`, `yarn.lock`, `bun.lockb`, `Cargo.lock`, `poetry.lock`, `uv.lock`.
6. Workspace manifests: `pnpm-workspace.yaml`, `turbo.json`, `nx.json`, `lerna.json`.
7. Entry points: `bin`, `main`, `module`, `exports`, `src/index.*`, `src/cli/*`, framework config files.
8. Scripts: `scripts` field in `package.json`, `Makefile`, `justfile`, `Taskfile.yml`.
9. Plugin manifest: `.claude-plugin/*.json`, `agents/`, `skills/`, marketplace metadata.
10. Top-level folders to map structure: `src/`, `packages/`, `apps/`, `cli/`, `instructions/`, `scripts/`, `docs/`.

Stop reading once shape and primary commands are clear. Do not exhaustively read source files.

## 3. Install command derivation

Choose the install snippet from the actual manifest, never from convention:

- Node: pick the package manager from the lockfile (`pnpm install`, `npm install`, `yarn install`, `bun install`).
- Published library: show consumer install from the manifest `name` field (`npm install <name>`, `pnpm add <name>`).
- CLI bin: show the run path (`npx <name>`, `pnpm dlx <name>`, `cargo install <name>`, `pipx install <name>`).
- Plugin/marketplace: derive from the project's own existing README or plugin manifest. Do not invent marketplace URLs.
- Local-only project (private or unnamed): write the from-source install (`git clone`, then run dev/build).

If the manifest has no `name` or it is private, do not invent one. Use the local install path instead.

## 4. Usage and example derivation

Look for the smallest authentic example:

- **Library**: read the public exports and pick a 3-10 line snippet that uses the most documented function.
- **CLI**: list the top-level commands from the actual command-handler file or captured `--help` output; quote one realistic command.
- **Web app / service**: show the dev command, the URL it serves, and the production build command.
- **Plugin**: show how the plugin is installed and invoked in the host environment, derived from existing project docs.

Mark fabricated or hypothetical examples with `<!-- TODO -->` rather than ship them as real.

## 5. Project map only when needed

Add a "Project structure" section only if:

- the repo has 4+ top-level folders that a new contributor needs to navigate, or
- it is a monorepo with multiple packages worth listing.

Otherwise omit it. The README should orient, not mirror the file tree.

## 6. Language and convention hints

Use these signals to decide whether the README can use the Korean default or must preserve another target language:

- Default to Korean for new README prose.
- If an existing target `README.md` is predominantly non-Korean and the task is a surgical refactor/update, preserve that language for consistency unless the user asked to translate.
- If the user explicitly requests a language, use it. If preservation signals conflict and would materially change the artifact language, ask once; do not silently choose English.

## 7. Discovery output

Before drafting, record a short profile in working notes:

```text
Type: [cli | library | web-app | monorepo | plugin | framework | docs-site | service]
Package manager: [npm | pnpm | yarn | bun | cargo | uv | poetry | go | deno | other]
Entry: [path or command]
Primary scripts: [dev/build/test/lint/release]
README language: [ko default | user-requested | preserve-existing]
Existing README state: [missing | present-accurate | present-stale]
License: [SPDX or "missing"]
```

This profile drives section selection in `rules/readme/section-design.md` and the validation summary in `rules/readme/validation.md`.

## Sources

> No external sources; content checked 2026-09-21.

This rule states the repository-local discovery procedure for README authoring. It makes no external claim, so no external source is cited.
