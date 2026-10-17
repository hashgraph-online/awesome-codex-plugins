# context-pack

A first-pass repository briefing for coding agents.

Point it at a repository and it answers the questions an agent otherwise spends its first dozen tool calls on: which instructions to follow, how to build and test, where execution starts, which files carry the logic, how the tree is organised, and what is changing right now. The output is a few kilobytes of markdown (or JSON), deterministic, and needs no index or API key.

```sh
context-pack --cwd path/to/repo
```

Abridged output for [ripgrep](https://github.com/BurntSushi/ripgrep):

```md
# ripgrep — context pack

> ripgrep is a line-oriented search tool that recursively searches the current directory for a regex pattern while respecting gitignore rules.

- Languages: rust (83)
- Stack: cargo
- Git: branch `master`, tracks `origin/master`, default branch, working tree clean

## Commands
- test: `cargo test --workspace` — cargo default
- lint: `cargo clippy --workspace --all-targets -- -D warnings` — cargo default
- ci: `ci/test-complete` — .github/workflows/ci.yml

## Entry points
- `crates/core/main.rs` — cargo bin `rg` (Cargo.toml) · 489 lines
- `crates/ignore/src/lib.rs` — cargo library root (crates/ignore/Cargo.toml) · 549 lines

## Key files
- `crates/printer/src/standard.rs` — large module (3987 lines), used by an entry point
- `crates/core/flags/defs.rs` — large module (8161 lines)
- `crates/core/search.rs` — large module (449 lines), used by the main entry point

## Workspace (10 packages)
- `crates/*` — 10 package(s): `crates/ignore`, `crates/printer (grep-printer)`, ...

## Layout
- `crates/` — 147 file(s), rust
  - `crates/core/` — 30 file(s), rust
- `tests/` — 22 file(s), rust [tests]
```

## What it finds

- **Agent instructions**: `AGENTS.md` (including nested, scoped ones), `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/`, `.cursorrules`, `.github/copilot-instructions.md`, `.windsurfrules`, `.clinerules`, `CONVENTIONS.md`, and agent skills (`SKILL.md`).
- **Commands**: Makefile, justfile and Taskfile targets, package scripts (npm/pnpm/yarn/bun, deno, composer), ecosystem defaults (cargo, go, uv/poetry/pytest/ruff, maven/gradle, dotnet, swift, mix, ...), and what CI actually runs on pull requests.
- **Entry points**: declared ones first (`[[bin]]`, `bin`/`main`/`exports`, `[project.scripts]`, `cmd/*/main.go`, Spring `*Application`, `Program.cs`, Dockerfile `CMD`), then conventions.
- **Key files**: the modules that carry the logic, ranked by size, how often they change in git history, and whether an entry point uses them. Examples, fixtures, docs sites, vendored and generated code are kept out.
- **Workspace**: monorepo packages grouped by pattern (`packages/*`), with test fixtures excluded.
- **Layout**: top-level directories with file counts, languages, and role, expanded where the code lives.
- **Active work**: uncommitted changes, commits on the current branch versus its base branch, and recent commits.
- **Docs, config, dependencies**: architecture and contributor docs, env templates, compose services, pinned toolchains.
- **Repo memory**: durable notes from `.context-pack/memory.md` (see below).

Leftover budget is spent on excerpts: the root instruction file, and declaration outlines (with line numbers) of the entry point and top key files. Secrets are redacted and files such as `.env` are never excerpted.

## Install

```sh
brew tap Rothschildiuk/context-pack https://github.com/Rothschildiuk/context-pack.git
brew install Rothschildiuk/context-pack/context-pack
```

Or `npm install -g @oleh12/context-pack`, or `cargo install --git https://github.com/Rothschildiuk/context-pack.git`, or a prebuilt archive from [Releases](https://github.com/Rothschildiuk/context-pack/releases).

## Usage

```sh
context-pack                         # briefing for the current directory
context-pack --cwd ../service        # another repository (or a subdirectory of one)
context-pack review                  # changed files and branch diff, for code review
context-pack compact                 # ~2 KB, for tight prompts
context-pack deep                    # ~16 KB, more files and excerpts
context-pack json                    # machine-readable, same content
context-pack --max-bytes 3000 --max-files 5 --include 'src/auth/**' --exclude legacy
```

`--no-git`, `--no-layout`, `--no-excerpts`, `--quiet`, and `--output <file>` do what they say. `context-pack --help` lists everything.

### With an agent

As an MCP server (Claude Code, Codex, Cursor, and other MCP clients):

```json
{ "mcpServers": { "context-pack": { "command": "context-pack", "args": ["--mcp-server"] } } }
```

Tools: `get_context`, `get_changed_context`, `get_file_excerpt` (confined to the repository), `add_memory_note`, `init_memory`, `refresh_memory`.

Without MCP, add one line to your repo's `AGENTS.md`/`CLAUDE.md`: *"Run `context-pack` before exploring this repository."* The skill in `skills/context-pack/` packages the same workflow for Codex.

### Repo memory

Some knowledge is not in the code: "integration tests need Docker running", "never edit `generated/` by hand", "the admin sync path bypasses retries". `.context-pack/memory.md` holds it, and every briefing shows it.

```sh
context-pack memory init                      # create the file
context-pack memory add "Run make db before the integration tests."
context-pack memory refresh                   # mark the notes as reviewed
```

The tool only ever rewrites the metadata block; notes are preserved exactly. If the notes were last reviewed more than a week ago and commits landed since, the briefing says so.

### Context artifacts

For agents that start from files rather than commands:

```sh
context-pack context refresh   # writes .context-pack/PROJECT_CONTEXT.md and .json
context-pack context check     # fails if they are missing or were generated from another HEAD
```

### JSON

`--format json` serializes the same briefing (`schema_version: "2.0"`): `repo` (name, description, languages, stack, dependencies), `instructions`, `commands`, `entry_points`, `key_files`, `workspace`, `layout`, `docs`, `config`, `git`, `memory`, `excerpts`, `notes`, `stats`.

## Limits

- Heuristics, not understanding: rankings can be wrong on unusual layouts. `--include` pins files you know matter.
- Shallow clones have no history, so change frequency is unavailable there.
- It is a starting map, not a search engine. Use `rg` and your agent's own tools for everything after the first minute.

## Development

See [CONTRIBUTING.md](./CONTRIBUTING.md). The short version: `cargo test`, `cargo clippy --all-targets -- -D warnings`, `cargo fmt --check`.

MIT licensed.
