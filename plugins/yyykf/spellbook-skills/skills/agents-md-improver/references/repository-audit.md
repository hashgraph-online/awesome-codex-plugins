# Repository Audit Mode

Use this mode when the user asks whether AGENTS.md-style project instructions are stale, incomplete, inaccurate, outdated, or should be refreshed against the current repository.

## Scan Scope

Scan only as deeply as needed to compare instruction files with repository truth. Prefer targeted reads over broad file dumps.

- Instruction files: `AGENTS.md`, nested `AGENTS.md`, `CLAUDE.md`, `.claude.local.md`, and any file imported by an instruction wrapper.
- Repository manifests: `package.json`, `pyproject.toml`, `pom.xml`, `build.gradle`, `go.mod`, `Cargo.toml`, `.version-bump.json`, and similar files when present.
- Build, test, and release entrypoints: `Makefile`, `justfile`, `scripts/`, CI workflows, package scripts, and documented release scripts.
- Agent/plugin manifests: `.codex-plugin/`, `.claude-plugin/`, `.agents/plugins/`, root `agents/`, and plugin marketplace metadata.
- User-facing docs: `README.md`, localized README files, and docs that describe install, usage, architecture, release, or workflow.
- Git state: `git status -sb` and current diffs for instruction-relevant files.

Respect user-provided exclusions. If the user says to ignore a path, prune it from scans and do not infer from it.

## Quality Criteria

### Commands And Workflows

- Essential build, test, lint, release, or local run commands are documented when they are not obvious.
- Commands use real paths and flags from the repository.
- Workflow notes explain when to run a command, not just that the command exists.

### Architecture And Ownership

- Key directories, modules, or ownership boundaries are documented when filenames alone are insufficient.
- Important cross-module relationships are explained only when they affect future edits.
- Generated files, vendored code, or read-only specs are clearly marked if touching them would be harmful.

### Non-Obvious Patterns

- Repository-specific gotchas, known failure modes, and environment quirks are captured.
- Unusual design choices include the short reason they exist.
- Tooling limitations are framed as actionable guidance.

### Currency

- Referenced files and directories exist.
- Documented commands still match current scripts, wrappers, or manifests.
- Version, platform, or toolchain notes reflect the current repository state.

### Conciseness

- Each line would help a future agent act better in this repository.
- Generic engineering advice is omitted.
- Long explanations are moved to project docs or `.project_context/` unless they must steer every session.

### Placement

- Project-wide behavior belongs in root `AGENTS.md` or its intentional shared source.
- Module-local behavior belongs in a nested `AGENTS.md`.
- Historical notes, task summaries, and exploration results belong in `.project_context/`.
- Tool-specific behavior belongs in that tool's instruction file unless it also applies to AGENTS.md-compatible tools.

## Red Flags

- The file repeats obvious facts from filenames or README content.
- The file contains stale paths, broken commands, or old tool names.
- A wrapper `AGENTS.md` points to another file, but the target was not read.
- Personal preferences or local machine details are written into shared project instructions without being reusable.
- Secrets, tokens, private URLs, or raw logs are included.

## Output Template

For audit-only requests, output a report before proposing edits:

````markdown
## AGENTS.md Quality Report

### Summary
- Effective instruction source: <path and import relationship>
- Files found: <count and paths>
- Current risk: <low|medium|high>
- Recommended updates: <count>

### Findings
- <finding grounded in repository evidence>

### Proposed Updates

### Update: <target file>

Why: <one-line reason this helps future agent sessions>

```diff
+ <concise durable instruction>
```
````

If no durable update is warranted, say so clearly and include the evidence that supports that conclusion.
