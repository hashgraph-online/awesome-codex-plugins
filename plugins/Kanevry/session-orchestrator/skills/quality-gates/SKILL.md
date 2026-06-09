---
name: quality-gates
user-invocable: false
tags: [reference, quality, typecheck, test, lint]
model: haiku
model-preference: sonnet
model-preference-codex: gpt-5.4-mini
model-preference-cursor: claude-sonnet-4-6
description: >
  Use this skill when referencing canonical quality check commands for typecheck, test, and lint.
  Defines 4 variants (Baseline, Incremental, Full Gate, Per-File) used by
  session-start, wave-executor, session-end, and session-reviewer.
  Reference skill — not invoked directly.
---

# Quality Gates — Reference Skill

This skill defines the canonical quality check commands. Do NOT invoke this skill directly.
Consuming skills (session-start, wave-executor, session-end, session-reviewer) reference the
variant they need and execute the commands inline.

## Command Resolution (policy-file-first, #183)

Quality-gate commands are resolved in this priority order:

1. **`.orchestrator/policy/quality-gates.json`** — canonical policy file (preferred). Schema: `.orchestrator/policy/quality-gates.schema.json`. Bootstrap writes a package-manager-aware default; hand-edit to customize.
2. **Session Config** `test-command` / `typecheck-command` / `lint-command` in CLAUDE.md (Claude Code / Cursor) or AGENTS.md (Codex CLI) — fallback.
3. **Hardcoded defaults** — last resort: `pnpm test --run`, `tsgo --noEmit`, `pnpm lint`.

Loader: `scripts/lib/quality-gates-policy.mjs` exports `loadQualityGatesPolicy(repoRoot)` and `resolveCommand(policy, key, fallback)`. The Node runner `scripts/run-quality-gate.mjs` performs the same resolution inline.

If any resolved command is set to the literal string `skip`, skip that check entirely.

## Scope Policy (#320)

**Lint, typecheck, and test commands MUST run with the project's canonical, unscoped invocation** as resolved above (e.g., `pnpm lint`, `pnpm test --run`, `tsgo --noEmit`). The resolved command's own configuration (`eslint.config.*`, `tsconfig.json`, `vitest.config.*`, `package.json` scripts) is the single source of truth for which files are checked.

**Domain-split scoping is FORBIDDEN.** Do NOT replace the canonical command with narrower variants such as:

- `pnpm lint src/` or `pnpm lint src/ scripts/` — silently hides errors in `tests/`, `tests/e2e/`, `tests/integration/`, root-level config files (`vitest.config.mjs`, `eslint.config.js`, etc.), and any directory outside the chosen split.
- `pnpm exec eslint src/**/*.ts` — same blind-spot; bypasses the project's lint script.
- `pnpm test src/foo/` instead of `pnpm test --run` — masks regressions in untouched modules.

This rule applies to **every consumer** of this skill: session-start Baseline, wave-executor Incremental, session-end Full Gate, session-reviewer Per-File, discovery probes, and repo-audit. It applies whether the command is invoked by an agent, by `scripts/run-quality-gate.mjs`, or by a human running it inline during triage.

**Exception — Incremental Per-File (Variant 4) test runs:** `{test-command}` MAY be invoked with explicit changed-file arguments (e.g., `pnpm test -- auth.test.ts`) per the per-file contract. Lint and typecheck have NO per-file exception — they always run the canonical command.

**Why:** Domain-split scoping was empirically shown (consumer-repo Deep-10 retro, 2026-05-20) to hide 2 errors and 17 warnings in `tests/integration/` and `tests/e2e/` that the canonical `pnpm lint` (841-file glob) catches. Narrowing scope to `src/+scripts/` for "lint-triage" produced a green W1, but the W4 Full Gate then surfaced the hidden errors, forcing a W5 sweep. The narrow-scope variant is a foot-gun: it looks faster but leaks debt across waves.

## Session Config Fields (legacy fallback)

Read these from the project's `## Session Config` section when `.orchestrator/policy/quality-gates.json` is absent:

- **`test-command`** — Custom test command.
- **`typecheck-command`** — Custom typecheck command.
- **`lint-command`** — Custom lint command.

If a field is missing, use the hardcoded default.

## Variant 1: Baseline

**Used by:** session-start (Phase 3)
**Purpose:** Quick health check at session start — non-blocking.

Commands:
1. Run `{typecheck-command} 2>&1 | tail -5`
2. Run `{test-command} 2>&1 | tail -5`

Behavior: Report results but do NOT block the session. Capture error counts and store them
as the session baseline for later comparison.

**Script output schema (Baseline):**
```json
{"variant": "baseline", "typecheck": {"status": "pass|fail|skip", "output": "string"}, "test": {"status": "pass|fail|skip", "output": "string"}}
```

## Variant 2: Incremental

**Used by:** wave-executor (after implementation waves)
**Purpose:** Verify implementation waves did not break anything.

Commands:
1. Run `{test-command}` on changed files only (e.g., `pnpm test -- <changed-test-files>`).
2. Run `{typecheck-command}`.

Behavior: Report failures. If issues are found, add fix tasks to the next wave automatically.
Do not block wave progression — let the next wave address regressions.

Metrics output (for consuming skills to capture):
```json
{
  "variant": "incremental",
  "duration_seconds": null,
  "typecheck": "pass|fail|skip",
  "test": "pass|fail|skip",
  "errors": []
}
```

## Variant 3: Full Gate

**Used by:** session-end (Phase 2)
**Purpose:** Final quality gate before commit — MUST pass.

Commands:
1. Run `{typecheck-command}` — must produce 0 errors.
2. Run `{test-command}` — must pass (exit code 0).
3. Run `{lint-command}` — must pass (warnings OK, errors NOT OK).
4. Check changed files for debug artifacts: `console.log`, `debugger`, `TODO: remove`.

Behavior: BLOCKING. Do not commit if any check fails. Fix quick issues (<2 min) inline.
For anything longer, create a `priority:high` issue and proceed without committing the
affected files.

Metrics output (for consuming skills to capture):
```json
{
  "variant": "full-gate",
  "duration_seconds": null,
  "typecheck": {"status": "pass|fail|skip", "error_count": 0},
  "test": {"status": "pass|fail|skip", "total": 0, "passed": 0},
  "lint": {"status": "pass|fail|skip", "warnings": 0},
  "debug_artifacts": []
}
```

## Variant 4: Per-File

**Used by:** session-reviewer agent
**Purpose:** Targeted quality check on specific changed files.

Commands:
1. Run `{test-command}` on specific file paths passed by the reviewer.
2. Run `{typecheck-command}`.

Behavior: Report per-file pass/fail status. The reviewer uses these results to annotate
its review output.

**Script output schema (Per-File):**
```json
{"variant": "per-file", "typecheck": {"status": "pass|fail|skip"}, "test": {"status": "pass|fail|skip"}, "files": ["string"]}
```

## Graceful Degradation

Handle missing tools without failing the session:

- If `{typecheck-command}` fails with "command not found" → skip TypeScript checks, note "No TypeScript configured".
- If `{test-command}` fails with "command not found" → skip tests, note "No test runner configured".
- If `{lint-command}` fails with "command not found" → skip lint, note "No linter configured".
- Non-TypeScript projects should set `typecheck-command: skip` in Session Config.

Always continue with the remaining checks — never abort a variant because one tool is missing.

## How Other Skills Reference This

When a consuming skill needs quality checks, include this directive:

> **Quality Reference:** Run [Baseline|Incremental|Full Gate|Per-File] quality checks
> per the quality-gates skill. Read `test-command`, `typecheck-command`, and `lint-command`
> from Session Config (defaults: `pnpm test --run`, `tsgo --noEmit`, `pnpm lint`).

Replace the bracketed variant name with the specific variant required by that phase.

## Script Alternative

Prefer `scripts/run-quality-gate.mjs` for deterministic execution with structured JSON output. The inline command approach is supported but produces unstructured output that downstream consumers cannot reliably parse.

```bash
# Baseline (session-start)
node "${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$PLUGIN_ROOT}}/scripts/run-quality-gate.mjs" --variant baseline --config "$CONFIG"

# Incremental (wave-executor)
node "${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$PLUGIN_ROOT}}/scripts/run-quality-gate.mjs" --variant incremental --config "$CONFIG" --files changed-file1.ts,changed-file2.ts

# Full Gate (session-end)
node "${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$PLUGIN_ROOT}}/scripts/run-quality-gate.mjs" --variant full-gate --config "$CONFIG" --session-start-ref "$SESSION_START_REF"

# Per-File (session-reviewer)
node "${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$PLUGIN_ROOT}}/scripts/run-quality-gate.mjs" --variant per-file --config "$CONFIG" --files specific-file.ts
```

The script handles graceful degradation (missing tools → skip), structured JSON output matching the schemas above, and proper exit codes (0=pass, 1=error, 2=gate-failed).

## Baseline Cache (#258)

Quality gates historically ran 2–3× per session (session-start Baseline, per-wave Incremental, session-end Full Gate) even when nothing relevant to the gate had changed between waves. The Baseline Cache short-circuits **Incremental only** when the session-start Baseline result is still trustworthy.

**Storage:** `.orchestrator/metrics/baseline-results.jsonl` — append-only JSONL, one record per session baseline run (consistent with `sessions.jsonl`, `events.jsonl`, `learnings.jsonl` precedent at `.orchestrator/metrics/`).

**Record schema (version 1):**
```json
{"version":1,"session_id":"<id>","session_start_ref":"<git-sha>","captured_at":"<ISO 8601 UTC>","dependency_hash":"<sha256 of package.json + lockfile>","results":{"typecheck":{"status":"pass|fail","error_count":0},"test":{"status":"pass|fail"},"lint":{"status":"pass|fail"}}}
```

**Validity rules** — a cache record is valid iff ALL of:
- `session_start_ref` matches the current session's start ref.
- `dependency_hash` matches current sha256 of `package.json` + lockfile (`pnpm-lock.yaml` preferred, then `package-lock.json`, then `yarn.lock`).
- `captured_at` is within 7-day TTL.
- `results.typecheck.status`, `results.test.status`, `results.lint.status` all === `pass`.

Invalid reason codes: `no-record` | `session-ref-mismatch` | `dependency-changed` | `ttl-expired` | `baseline-had-failures`.

**Incremental-skip condition:** `shouldSkipIncremental()` returns `skip: true` when the cache is valid AND `git diff --name-only $SESSION_START_REF..HEAD | wc -l` returns <50. Otherwise `skip: false` and Incremental runs as before. The function never throws — on any error (git failure, unreadable cache, missing dependency_hash) it fails safe by returning `skip: false`.

**INVARIANT — Full Gate at session-end is NEVER skipped**, regardless of cache state. The cache only short-circuits Incremental in wave-executor. Full Gate remains the close-safety gate and always runs the complete typecheck + test + lint + debug-artifact scan. This is intentional and non-configurable.

**Implementation:** `scripts/lib/quality-gates-cache.mjs` exports `computeDependencyHash`, `saveBaselineResult`, `loadLatestBaselineResult`, `isCacheValid`, `shouldSkipIncremental`. Stdlib-only (`node:fs`, `node:path`, `node:crypto`, `node:child_process`).

**Validation (#266):** Effectiveness confirmed under the Claude Code subprocess-per-call hook model. The JSONL file-based design persists across subprocess boundaries — 100% hit-rate across 8 independent Node.js processes in benchmarks. Median call latency: 0.45 ms (subprocess) / 0.07 ms (in-process warm). The cache is NOT in-process memory; hooks do not call this module directly. See `docs/policy-cache-validation-2026-04-28.md` for full findings and `scripts/measure-policy-cache-effectiveness.mjs` for the instrumentation script.
