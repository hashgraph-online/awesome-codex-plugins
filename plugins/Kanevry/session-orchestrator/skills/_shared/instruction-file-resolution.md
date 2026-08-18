# Instruction File Resolution

> Single source of truth for how skills, scripts, hooks, and commands locate the per-repo project-instruction file.
> CLAUDE.md and AGENTS.md are transparent aliases — pick one, never both, never merged.

## Why this rule exists

The session-orchestrator plugin is consumed by four platforms (see `skills/_shared/platform-tools.md`):

- **Claude Code / Cursor IDE** — canonical instruction file is `CLAUDE.md`.
- **Codex CLI / Pi** — canonical instruction file is `AGENTS.md`.

Bootstrap accepts both as valid (`skills/bootstrap/_shared-template.md`). Without an explicit alias rule, downstream consumers that hardcode `CLAUDE.md` silently exclude every Codex CLI or Pi repo from their checks (see issue #33). The fix is purely additive: every site that resolves the project-instruction file must accept `AGENTS.md` as a fallback alias.

## Resolution rule (precedence)

Apply these steps in order against the repo root. Stop at the first hit. Never merge results from both files.

1. If `<repoRoot>/CLAUDE.md` exists **and is non-empty** (size > 0 bytes) → use it. `kind = 'claude'`.
2. Else if `<repoRoot>/AGENTS.md` exists **and is non-empty** → use it. `kind = 'agents'`.
3. Else → no instruction file detected. The caller decides how to handle this (gate-closed, warn, skip, etc.).

**Invariants:**

- `CLAUDE.md` always wins ties. A repo migrating from Claude Code to Codex CLI keeps the existing `CLAUDE.md` until it is intentionally renamed.
- Active platform config readers may prefer the native platform file when `SO_PLATFORM` is set (`AGENTS.md` for Codex CLI / Pi). Generic artifact resolution via `resolveInstructionFile()` keeps the `CLAUDE.md`-wins rule above.
- Empty files are treated as absent. A zero-byte placeholder must not block detection of the alias.
- Never read both files. Never concatenate, diff, or cross-validate them — the SSOT is whichever the rule selects.
- The resolved kind (`claude` | `agents`) is part of the contract. Consumers that report paths in JSON output (e.g., `skills/claude-md-drift-check/checker.mjs`) must surface the resolved path so users on either platform can audit the result.

## Reference implementations

### Bash one-liner (matches `skills/_shared/bootstrap-gate.md` style)

```bash
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if   [[ -s "$REPO_ROOT/CLAUDE.md" ]]; then CONFIG_FILE="$REPO_ROOT/CLAUDE.md";  CONFIG_KIND="claude"
elif [[ -s "$REPO_ROOT/AGENTS.md" ]]; then CONFIG_FILE="$REPO_ROOT/AGENTS.md";  CONFIG_KIND="agents"
else CONFIG_FILE=""; CONFIG_KIND=""
fi
```

`-s` (`size > 0 and exists`) collapses the existence + non-empty checks into a single test, matching the bootstrap gate convention.

### Node.js helper

Use `resolveInstructionFile(repoRoot)` from `scripts/lib/common.mjs`:

```js
import { resolveInstructionFile, findProjectRoot } from './scripts/lib/common.mjs';

const result = resolveInstructionFile(findProjectRoot());
// result is one of:
//   { path: '/abs/path/to/CLAUDE.md', kind: 'claude' }
//   { path: '/abs/path/to/AGENTS.md', kind: 'agents' }
//   null
```

Signature: `resolveInstructionFile(repoRoot?: string): { path: string, kind: 'claude' | 'agents' } | null`. When `repoRoot` is omitted, it falls back to `findProjectRoot()` from the same module.

## Out of scope

These patterns are **explicitly NOT supported** to keep the SSOT clean. Adopting them would dilute the alias contract without solving a documented user problem.

- **Hierarchical / subdir `CLAUDE.md` overrides** (Warp pattern). Verification: `0 / 14` `01-projects/*` repos in the meta-vault use a subdir `CLAUDE.md`. Revisit only if a monorepo consumer files concrete demand.
- **`.cursorrules`** — Cursor IDE reads `CLAUDE.md` natively (see `skills/_shared/platform-tools.md` § Config File). No separate file.
- **`.windsurfrules` / `.clinerules` / `WARP.md` / arbitrary editor-local rule files.** Adding more aliases multiplies the surface and creates ambiguous precedence. Stick to the two-file alias.

## Sites consuming this rule

Every site that reads or references the project-instruction file links here instead of restating the precedence. The current surface (issue #33 sweep) covers:

- `skills/` — `claude-md-drift-check/`, `wave-executor/wave-loop.md`, `vault-mirror/SKILL.md`, `vault-sync/SKILL.md` + `validator.mjs`, `plan/{mode-new,mode-feature,SKILL}.md`, `session-end/{SKILL,drift-operations,phase-3-2-docs-verification}.md`, `session-start/{SKILL,phase-8-5-express-path,phase-2-5-docs-planning}.md`, `docs-orchestrator/SKILL.md`, `discovery/probes-session.md`, `evolve/SKILL.md`, `_shared/{bootstrap-gate,config-reading}.md`.
- `scripts/` — `lib/common.mjs` (this helper), any future readers of repo-root instruction files.
- `commands/` — any user-facing command help that names the config file.
- `hooks/` — `pre-edit-scope.mjs` and similar handlers that gate edits against the config file.
- `tests/` — `tests/skills/instruction-file-alias-coverage.test.mjs` enforces that every site listing `CLAUDE.md` also names `AGENTS.md` (or is on its documented exception list).

When adding a new consumer, update the sweep test exception list **only** if the omission of `AGENTS.md` is intentional (e.g., a banner string that names a specific platform). Default to mentioning both.
