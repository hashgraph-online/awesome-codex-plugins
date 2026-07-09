# Generic scaffolding templates (project · component · CI)

> **Provenance:** This content was **moved verbatim** out of `skills/scaffold/SKILL.md`
> (bead `age-skills-audit-fable-l6ic.10`, generic-craft trim). A frontier model produces
> standard project trees, best-practice config, and GitHub-Actions / GitLab-CI YAML
> correctly **with no template** — so this file is a fallback reference, not the skill's
> durable value. The durable binding (the domain-slice manifest → operating-loop scope)
> stays in `SKILL.md`. Reach for this file only when you want the canonical shapes the
> skill historically stamped; otherwise ask the model directly.

The three generic modes share a four-step spine: **gather requirements → generate
structure → verify → initial commit**. Every generated file must have real, functional
content — not placeholder comments.

## Step 1: Gather Requirements

Collect these inputs (use defaults when not specified):

| Input | Default | Notes |
|-------|---------|-------|
| Language/framework | (required) | go, python, node, rust, react |
| Project type | CLI (Go), package (Python), app (Node) | CLI, library, web-service, API, package |
| Testing framework | Language default | go test, pytest, vitest, cargo test |
| CI platform | GitHub Actions | github, gitlab |
| Project name | (required) | kebab-case, validated |

Validate the project name is kebab-case. Reject names with spaces, uppercase, or special characters.

## Step 2: Generate Project Structure

Create the directory tree and all files.

### Go CLI

```
<name>/
  cmd/<name>/main.go        # cobra or bare main with version flag
  internal/config/config.go  # configuration loading
  internal/config/config_test.go
  go.mod
  go.sum
  Makefile                   # build, test, lint, clean targets
  .goreleaser.yml            # cross-compile config
  .gitignore
  .editorconfig
  CLAUDE.md
```

### Go Library

```
<name>/
  pkg/<name>.go              # primary exported API
  pkg/<name>_test.go
  examples/basic/main.go     # runnable example
  go.mod
  go.sum
  Makefile
  .gitignore
  .editorconfig
  CLAUDE.md
```

### Python Package

```
<name>/
  src/<name>/__init__.py     # version and public API
  src/<name>/core.py         # primary module
  tests/__init__.py
  tests/test_core.py         # real behavioral test
  pyproject.toml             # black, ruff, mypy config included
  .github/workflows/ci.yml
  .gitignore
  .editorconfig
  CLAUDE.md
```

### Node/TypeScript

```
<name>/
  src/index.ts               # entry point with exports
  src/core.ts                # primary module
  test/core.test.ts          # vitest test
  package.json               # scripts: build, test, lint, format
  tsconfig.json
  .gitignore
  .editorconfig
  CLAUDE.md
```

### Rust

```
<name>/
  src/lib.rs                 # library root (or main.rs for CLI)
  src/core.rs                # primary module
  benches/benchmark.rs       # criterion bench stub
  Cargo.toml                 # with clippy, rustfmt config
  .gitignore
  .editorconfig
  CLAUDE.md
```

## Step 3: Apply Best Practices

After generating the structure, layer on cross-cutting concerns:

For installer scripts, agent-facing tool servers, MCP surfaces, or Rust CLI storage scaffolds, apply [agent-facing-tool-scaffolds.md](agent-facing-tool-scaffolds.md) before writing files.

### .gitignore

Use the language-appropriate template. Include IDE files (`.vscode/`, `.idea/`), OS files (`.DS_Store`, `Thumbs.db`), and build artifacts.

### .editorconfig

```ini
root = true

[*]
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
charset = utf-8

[*.{go,rs}]
indent_style = tab
indent_size = 4

[*.{py,ts,js,json,yml,yaml,toml}]
indent_style = space
indent_size = 4

[Makefile]
indent_style = tab
```

### Pre-commit Hooks

Generate a `.pre-commit-config.yaml` with language-appropriate hooks:

- **Go:** gofmt, go vet, golangci-lint
- **Python:** black, ruff, mypy
- **Node/TS:** eslint, prettier
- **Rust:** rustfmt, clippy

### Testing Setup

Every scaffold includes at least one real test that:
- Tests actual behavior (not just `!= nil`)
- Uses the language's idiomatic test patterns
- Passes on first run

### CI Pipeline

Generate CI config unless the user explicitly opts out. Default: GitHub Actions.

### CLAUDE.md

Generate a project-specific `CLAUDE.md` containing:
- Build commands
- Test commands
- Lint commands
- Project structure overview
- Key conventions for the language (loaded from `/standards`)

## Step 4: Verify Scaffold Works

Run these checks in order. Stop and fix if any fail.

```
1. Build passes        →  language-specific build command
2. Tests pass          →  language-specific test command
3. Lint passes         →  language-specific lint command (warn-only if tools not installed)
```

### Verification Commands by Language

| Language | Build | Test | Lint |
|----------|-------|------|------|
| Go | `go build ./...` | `go test ./...` | `go vet ./...` |
| Python | `python -m py_compile src/**/*.py` | `python -m pytest` | `ruff check .` |
| Node/TS | `npx tsc --noEmit` | `npx vitest run` | `npx eslint .` |
| Rust | `cargo build` | `cargo test` | `cargo clippy` |

If a tool is not installed (e.g., `ruff`, `golangci-lint`), note it as a warning but do not fail the scaffold.

## Step 5: Initial Commit

After verification passes, create the initial commit:

```
bootstrap(<name>): scaffold <language> <type> project
```

Example: `bootstrap(my-cli): scaffold go cli project`

Do NOT push. The user decides when to push.

## Component Mode

When invoked as `/scaffold component <type> <name>`:

### Go Component

```
internal/<name>/<name>.go       # package with exported API
internal/<name>/<name>_test.go  # behavioral tests
```

Register the new package in relevant imports. Run `go build ./...` and `go test ./...` to verify.

### Python Component

```
src/<project>/modules/<name>/__init__.py
src/<project>/modules/<name>/core.py
tests/test_<name>.py
```

### Node/TS Component

```
src/<name>/index.ts
src/<name>/types.ts
test/<name>.test.ts
```

### React Component

```
src/components/<Name>/<Name>.tsx
src/components/<Name>/<Name>.test.tsx
src/components/<Name>/<Name>.stories.tsx  # Storybook story
src/components/<Name>/index.ts            # barrel export
```

After generating, run the project's test suite to verify the new component integrates cleanly.

## CI Mode

When invoked as `/scaffold ci <platform>`:

### GitHub Actions

Generate `.github/workflows/ci.yml`:

**This is a skeleton — expand steps using the detected language's actual commands.**

```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup # use actions/setup-go, setup-node, setup-python as detected
        uses: actions/setup-go@v5  # example for Go
        with:
          go-version-file: go.mod
      - name: Lint
        run: golangci-lint run  # replace with detected linter

  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4
      - name: Setup
        uses: actions/setup-go@v5
        with:
          go-version-file: go.mod
      - name: Test
        run: go test ./...  # replace with detected test command

  build:
    runs-on: ubuntu-latest
    needs: [lint, test]
    steps:
      - uses: actions/checkout@v4
      - name: Setup
        uses: actions/setup-go@v5
        with:
          go-version-file: go.mod
      - name: Build
        run: go build ./...  # replace with detected build command
```

Include language-appropriate caching (`actions/cache` for Go modules, pip, node_modules, cargo registry). Replace Go-specific steps with the detected language's toolchain.

### GitLab CI

Generate `.gitlab-ci.yml`:

```yaml
stages:
  - lint
  - test
  - build

variables:
  # language-specific cache paths

lint:
  stage: lint
  script: [lint command]

test:
  stage: test
  script: [test command]
  parallel:
    matrix:
      - IMAGE: [language versions]

build:
  stage: build
  script: [build command]
  needs: [lint, test]
```

Include caching directives and artifact definitions.

## Error Recovery

| Problem | Action |
|---------|--------|
| Directory already exists | Ask user: overwrite, merge, or abort |
| Build tool not installed | Note missing tool, generate files anyway, warn user |
| Test fails on generated code | Fix the generated code (this is a scaffold bug) |
| Git init fails | Verify not inside existing repo, handle accordingly |

## Output Summary

After completion, print a summary:

```
Scaffold complete: <name> (<language> <type>)
  Files created: <count>
  Build: PASS
  Tests: PASS (<count> tests)
  Lint:  PASS | WARN (tool not installed)
  Commit: bootstrap(<name>): scaffold <language> <type> project

Next steps:
  cd <name>
  <language-specific "run" command>
```
