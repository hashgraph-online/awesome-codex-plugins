# Run-instructions extraction catalog

Reference data for `/archcore:init` Step A.2 (Detect sub-phase). Edit this file to tune extraction.

## What it detects

The RUN GUIDE: the canonical install / run / test commands needed to work on THIS checkout, read verbatim from the repo and never invented. It is the shortest path from a fresh clone to a running, testable build in whatever language, ecosystem, or domain the repo uses (web, ML, embedded, games, data/IaC, mobile, in-house tooling). It captures what a maintainer of this repo actually types, not what a published package's consumers type. The keep-lists, monorepo markers, and prereq sources below are common examples, not the universe.

## How to find it (any codebase)

Fallback ladder — stop at the first step that yields usable, verbatim commands:

1. **README / setup docs.** First section whose heading signals setup (getting started, quick start, install, installation, setup, development, running locally, build, usage, compile, toolchain — match non-English headings too). Extract fenced shell blocks; read commands verbatim, strip `$`/`>`/`#` prompt markers.
2. **Manifest scripts / task definitions.** Whatever the matched manifest declares: `package.json` `scripts`, pyproject `[tool.poetry.scripts]`, `Cargo.toml [[bin]]`, `composer.json` `scripts`, `Rakefile`, `mix` aliases, etc.
3. **Build-system evidence (try this BEFORE asking).** Makefile/Justfile/Taskfile targets; Dockerfile `CMD`/`ENTRYPOINT` and `.devcontainer` postCreate; the first CI job's steps (`.github/workflows`, `.gitlab-ci.yml`, …); and the canonical CLI implied by whichever manifest matched — e.g. `*.csproj`/`*.sln` → dotnet, `Package.swift`/`*.xcodeproj` → swift build / xcodebuild, `go.work` / Cargo `[workspace]` → that toolchain, `flake.nix` → nix develop, `build.gradle` → ./gradlew, `mix.exs` → mix, `pubspec.yaml` → flutter, `deps.edn` → clojure/clj, `dune-project`/`*.opam` → dune, `*.cabal`/`stack.yaml` → cabal/stack, `CMakeLists.txt` → cmake, `MODULE.bazel`/`WORKSPACE` → bazel, `*.tf` → terraform, `Chart.yaml` → helm. **Engine-managed exception:** for game engines that GENERATE the project files (Unity/Unreal/Godot `*.csproj`), the build/run is the engine itself — do NOT emit `dotnet build`; state that the project is built/run from the engine editor (or its batch-mode CLI) and omit a terminal command when none is canonical.
4. **Only then** ask the user a single open question.

Workspace & prereq signals: treat workspace/version files of ANY ecosystem (pnpm-workspace.yaml, turbo.json, nx.json, lerna.json, go.work, Cargo `[workspace]`, settings.gradle, multi-module pom, MODULE.bazel, .tool-versions/mise.toml) as monorepo and/or prerequisite sources; read declared runtime versions straight from the manifest, never guess them. Read every command verbatim — never invent flags.

False-positive guard: do NOT emit a README consumer snippet (`npm install my-lib`, `pip install my-lib`, `cargo install <tool>`, `docker run <published-image>`) as the project's own setup. Do NOT let a tiny JS docs/site under `apps/` trip the JS-monorepo path for a Rust/Go/Python repo.

Emit a signal only on positive evidence; when no candidate is unambiguous, prefer omission over a guess — never invent.

## Common signals (non-exhaustive examples)

These are non-exhaustive examples to orient pattern-matching — absence from this list is NOT absence of signal; fall back to the method above for anything not shown.

### Monorepo markers

A repo is a monorepo if any holds: a root `pnpm-workspace.yaml` / `turbo.json` / `nx.json` / `lerna.json`; **≥ 2 package/project manifests of ANY ecosystem** under `apps/` / `packages/` / `services/` (`package.json`, `mix.exs` for an Elixir umbrella, `Cargo.toml`, `go.mod`, `*.csproj`, …); or a cross-ecosystem workspace declaration (`go.work`, Cargo `[workspace]`, `settings.gradle`, multi-module `pom.xml`, `MODULE.bazel`, Mix umbrella `apps_path`). When detected, the guide needs a top-level **Prerequisites**, a top-level **Workspace install** (the single command that primes all apps), and one subsection per detected app (named after its dir) with that app's own dev/build/test commands.

### README setup-heading regex (case-insensitive)

```
^#{1,3}\s+(getting\s+started|quick\s*start|installation|install|development|dev\s+setup|setup|local\s+development|running\s+locally|running\s+the\s+app|run|build|usage|compile)\b
```

Stop extracting when the next heading at the same or higher level appears.

### Command keep-list (first token after an optional `$`/`>`)

- **Install / build / run:** `npm`, `pnpm`, `yarn`, `bun`, `deno`, `pip`, `pipx`, `poetry`, `uv`, `conda`, `mamba`, `pdm`, `hatch`, `bundle`, `gem`, `composer`, `cargo`, `go`, `mix`, `rebar3`, `sbt`, `mvn`, `gradle`, `./gradlew`, `dotnet`, `swift`, `xcodebuild`, `pod`, `flutter`, `dart`, `dune`, `opam`, `clojure`, `clj`, `lein`, `bb`, `stack`, `cabal`, `cmake`, `ninja`, `meson`, `bazel`, `bazelisk`, `nix`, `zig`, `nimble`, `shards`, `terraform`, `pulumi`, `ansible-playbook`, `kubectl`, `helm`, `dvc`, `snakemake`, `nextflow`, `pio`, `idf.py`, `west`, `arduino-cli`, `mise`, `asdf` — and, generally, **the canonical build/run/test CLI of whatever toolchain the repo uses** (this list only illustrates; do not gate on it).
- **Run / test / lint:** the same prefixes with second tokens like `install`, `add`, `dev`, `start`, `run`, `exec`, `test`, `build`, `lint`, `format`, `check`, `watch`, `serve`, `flash`, `deploy`, `repro`
- **Env / setup:** `cp`/`mv` (only if target is `.env`-like), `docker`, `docker-compose`, `make`, `just`, `task`

Consider bash/sh/shell/zsh/console/terminal/cmd blocks, plus bare fenced blocks that contain a keep-list command or a `$` prompt. Drop environment-level lines that don't belong in a project run guide: `git clone`, `curl`, `wget`, `rm`, `rmdir`, `sudo apt`, `brew install`.

### Prerequisite sources (read declared versions verbatim; never guess)

| Source | Field | Example emitted line |
|--------|-------|----------------------|
| `package.json` | `engines.node` / `engines.pnpm` / `engines.bun` | `Node.js <spec>` / `pnpm <spec>` / `Bun <spec>` |
| `package.json` | `packageManager` | `<tool>@<version>` |
| `pyproject.toml` | `project.requires-python` | `Python <spec>` |
| `Cargo.toml` | `package.rust-version` | `Rust <version>` |
| `go.mod` | `go <version>` directive | `Go <version>` |
| `Gemfile` | `ruby '<version>'` | `Ruby <version>` |
| `composer.json` | `config.platform.php` / `require.php` | `PHP <spec>` |

If nothing is declared, omit the Prerequisites section entirely — do not pad it.

## Templates

### Single-app template

```markdown
## Prerequisites

- {runtime 1}
- {runtime 2}

## Install

```sh
{install command}
```

## Run locally

```sh
{dev command}
```

## Test

```sh
{test command}
```
```

Rules:
- Drop any section whose content is empty (no test command detected → omit Test).
- `Prerequisites` as a bullet list; commands as fenced `sh` blocks.
- No interleaved prose — the guide is a minimal command reference, not an explainer.
- Total body ≤ 15 lines (excluding the illustrative outer backticks above).

### Monorepo template

```markdown
## Prerequisites

- {runtime 1}
- {package manager and its version from packageManager, if present}

## Workspace install

```sh
{root install command, e.g., pnpm install}
```

## Apps

### {app-1-name}

```sh
{cd apps/{app-1-name} && {app-1 dev command}}
```

### {app-2-name}

```sh
{cd apps/{app-2-name} && {app-2 dev command}}
```

## Test

```sh
{workspace-wide test command, if present}
```
```

Rules:
- Each app subsection ≤ 6 lines.
- If an app has no detectable dev command from its own manifest `scripts`, fall back to `{package manager} dev` at that path, not at repo root.
- Prefer workspace-aware commands when supported (e.g., `pnpm --filter <name> dev` instead of `cd`).

## Output

`SKILL.md` Phase E fires the `create_document`; this catalog supplies the body per the templates above.

| Field | Value |
|---|---|
| `type` | `guide` |
| `directory` | `onboarding` |
| `filename` | `running-the-project` |
| `title` | `Running the project locally` |
| `status` | `accepted` |
| `tags` | `['onboarding']` |

Body cap: single-app ≤ 15 lines; monorepo per-app subsection ≤ 6 lines.
