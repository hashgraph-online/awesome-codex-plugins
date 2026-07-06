---
name: claude-md-drift-check
description: Use when detecting drift between CLAUDE.md (or AGENTS.md, the Codex CLI alias) / _meta narrative and live repository state. Nine checks: absolute-path resolution, 01-projects/ count claims, issue-reference freshness (closed refs in forward-looking sections), session-file existence, command-count sync (claimed "N commands" vs actual commands/*.md), session-config-parity (top-level keys diffed against docs/session-config-template.md), vault-dir-parity (CLAUDE.md vs AGENTS.md agreement on vault-integration.vault-dir), generated-rule-staleness (WARN-only: auto-generated rules whose learning-key is absent or expired in learnings.jsonl), and rule-scoping (paths: vs globs: frontmatter defects, cited-but-missing rule citations in CLAUDE.md/AGENTS.md/See-Also footers, zero-match globs, and foreign PascalCase glob tokens in .claude/rules/*.md). Invoked as an opt-in session-end phase; mirrors vault-sync's lean JSON+exit-code contract.
model: haiku
---

# CLAUDE.md Drift-Check Skill

> The instruction file is alias-resolved per
> [`skills/_shared/instruction-file-resolution.md`](../_shared/instruction-file-resolution.md):
> `CLAUDE.md` (Claude Code / Cursor IDE) wins ties; `AGENTS.md` (Codex CLI) is
> picked up as a transparent alias when `CLAUDE.md` is absent. The resolved
> path and kind are surfaced in the JSON output (`resolved_path`,
> `resolved_kind`).

## Status

PHASE 1 IMPLEMENTED (2026-04-19). Session-end opt-in quality gate. Upstream of `/close` commit preparation, downstream of `vault-sync`.

## Why this exists

`CLAUDE.md` is narrative SSOT for a repo's Session Config and project context. It decays quickly when surrounding state changes — paths get renamed, project counts shift, issues close, session files get pruned in digests. The drift-cluster closed by agents/vault#57 (3 items in one sweep) was the 4th incidence of the `issue-description-drift-stale-filecount` learning. Manual curation does not scale; this skill turns drift detection into a repeatable gate.

## Checks

| # | Check | What it scans | How |
|---|-------|---------------|-----|
| 1 | `path-resolver` | Every absolute path `/Users/…` in scope files | `existsSync(path)` |
| 2 | `project-count-sync` | Hardcoded "N registered" / "N projects" claims next to `01-projects/` | compare to `ls -d 01-projects/*/` |
| 3 | `issue-reference-freshness` | `#NN` in forward-looking sections (What's Next, Backlog, Open Issues, Offene Themen, Todo, Next Steps) | `glab issue view NN --repo <origin>` |
| 4 | `session-file-existence` | `50-sessions/YYYY-MM-DD-*.md` references anywhere in scope | `existsSync(vault/50-sessions/<file>)` |
| 5 | `command-count` | "N commands" / "N /commands" claims in prose | compare to `ls commands/*.md \| wc -l`; skipped if no `commands/` dir |
| 6 | `session-config-parity` | Top-level keys under `## Session Config` in `CLAUDE.md` / `AGENTS.md` | diff against `docs/session-config-template.md`; missing keys flagged as errors |
| 7 | `vault-dir-parity` | `vault-integration.vault-dir` in BOTH `CLAUDE.md` AND `AGENTS.md` | reuse `_parseVaultIntegration`; flag when the two files disagree |
| 8 | `generated-rule-staleness` *(WARN only)* | `.claude/rules/*.md` with `auto-generated: true` frontmatter | extract `learning-key`; WARN when the key is absent from `.orchestrator/metrics/learnings.jsonl` or its learning's `expires_at` is in the past; skipped silently when no auto-generated rules exist |
| 9 | `rule-scoping` | `.claude/rules/*.md` frontmatter + `## See Also` footers + `.claude/rules/<name>.md` citations in `CLAUDE.md`/`AGENTS.md` | five probes: `paths:` frontmatter (error), cited-but-missing rule citations (error), zero-match `globs:` patterns (warn), foreign PascalCase glob tokens (warn), unreadable rule files (warn — surfaced instead of silently skipped); skipped silently when `.claude/rules/` is absent |

Check 3 deliberately scopes to forward-looking sections. Mentions inside "Recently Closed", "Decisions", "Archive", etc. describe history and must not be flagged.

Check 5 counts `*.md` files directly inside `commands/` (non-recursive, non-hidden). The `commands/` directory is resolved relative to `VAULT_DIR` by default; use `--commands-dir <path>` to override.

Check 6 (issue #30) extracts the YAML block under `## Session Config` from both the canonical template (`docs/session-config-template.md` by default, override with `--config-template`) and the resolved local instruction file. Top-level keys present in the template but missing locally surface as `session-config-parity` errors. Both fenced YAML (```` ```yaml ... ``` ````) and raw YAML body (up to next `## ` heading) are accepted. The check skips gracefully when the template file is absent, when no instruction file is detected, or when explicitly disabled via `--skip-session-config-parity`.

The parity set is **template-driven**: every column-0 YAML key under `## Session Config` in the template is checked. As of the gsd Pattern Adoption Quick-Wins bundle (PRD 2026-05-22, issues #517–#521), the template-side keys include the four new top-level blocks:

- `state-md-lock` (Pattern 1 / #518) — mechanical STATE.md write lock
- `slopcheck` (Pattern 2 / #520) — opt-in package legitimacy gate
- `templates-first` (Pattern 3 / #519) — gh/glab template-read enforcement hook
- `verification-auto-fix` (Pattern 4 / #521) — opt-in auto-fix retry loop after Quality-Gate fail

A local CLAUDE.md / AGENTS.md that omits any of these now fails `session-config-parity` in `mode: hard`. The bundle ships all four keys in CLAUDE.md and `docs/session-config-template.md` together (Wave 1 of the adoption plan) so the check stays green at adoption time.

Check 7 (issue #600) is the **only** check that intentionally reads BOTH instruction files rather than the single alias-resolved one. The alias rule (CLAUDE.md wins ties, AGENTS.md is the Codex alias) means `resolveInstructionFile()` picks exactly one — so a repo carrying both files can silently let `AGENTS.md` drift out of sync with `CLAUDE.md`. A sibling project ran for weeks with a correct `vault-integration.vault-dir` in `CLAUDE.md` and a dead path in `AGENTS.md`. Check 7 reads `vault-integration.vault-dir` from each file (reusing the `_parseVaultIntegration` parser from `scripts/lib/config/vault-integration.mjs` — no hand-rolled YAML) and flags a `vault-dir-parity` error when the two values diverge (the error is attributed to `AGENTS.md`, the secondary alias, and names both values). The check skips gracefully when only one instruction file is present (nothing to compare), when neither file declares a `vault-integration:` block, or when explicitly disabled via `--skip-vault-dir-parity`. Two files that both omit `vault-dir` (both unset) agree and pass.

Check 9 (`rule-scoping`) validates `.claude/rules/*.md` frontmatter against the `scripts/lib/rule-loader.mjs` contract, catching the class of defect where a rule silently drifts out of the activation pipeline the loader actually implements. Four probes: **(1) paths-presence** — a top-level `paths:` frontmatter key is not a key `rule-loader.mjs` recognises (it only reads `globs:`), so a rule with `paths:` silently loads ALWAYS-ON regardless of intended file scope; flagged as an error. **(2) cited-but-missing** — `(a)` `.claude/rules/<name>.md` citations inside `CLAUDE.md`/`AGENTS.md` that don't resolve to a file on disk, and `(b)` bare `<name>.md` tokens in a rule's own `## See Also` footer that don't exist as sibling rule files (tokens carrying a path separator, e.g. `../../skills/_shared/state-ownership.md`, are cross-directory references and explicitly out of scope); both flagged as errors. **(3) zero-match-globs** — a `globs:` pattern matching zero files in `git ls-files` (falls back to a manual directory walk when git is unavailable); flagged as a WARNING, not an error, because library/exemplar repos legitimately carry dead stack rules (this repo alone carries ~37 by design — Swift/Next.js/Supabase rules with no matching files in a pure-Node-ESM codebase). **(4) foreign-glob** — a glob pattern containing a PascalCase product-like token (regex `[A-Z][a-z]+[A-Z]`, e.g. `WalkAITalkieTests`) — a likely copy-paste leftover from another project's rule scope; flagged as a WARNING. Glob matching reuses the same picomatch-with-inline-fallback resolution `scripts/lib/rule-loader.mjs` uses (`parseGlobsFrontmatter` is imported directly; the picomatch resolution itself is duplicated locally since `rule-loader.mjs` does not export a public matcher function). The check is skipped silently (no `checks_run` entry, no `checks_skipped` entry) when `.claude/rules/` is absent, or explicitly via `--skip-rule-scoping`.

## Files

- `checker.mjs` — pure Node ESM, no runtime deps. Reads scope files, runs enabled checks, emits JSON on stdout.
- `checker.sh` — POSIX shim. Resolves `VAULT_DIR`, execs Node. No `pnpm install` needed (zero deps).
- `package.json` — declares Node engine; no dependencies.
- `tests/` — vitest suite added in Quality wave.

## Invocation

```bash
VAULT_DIR=/path/to/vault bash checker.sh --mode warn
```

CLI flags (all optional):

| Flag | Default | Effect |
|------|---------|--------|
| `--mode <hard\|warn\|off>` | `warn` | `hard` → exit 1 on errors; `warn` → exit 0, errors in JSON; `off` → short-circuit to `status: skipped-mode-off` |
| `--repo <owner/name>` | derived from `git remote get-url origin` | Override for Check 3's `glab issue view --repo` |
| `--include-path <glob>` | resolved instruction file (`CLAUDE.md` or `AGENTS.md` per alias rule), `_meta/**/*.md` | Repeatable. Scope files, relative to `VAULT_DIR`. Defaults are seeded post-resolution so Codex-only repos (`AGENTS.md`) are scanned out of the box. |
| `--skip-path-resolver` | off | Disable Check 1 |
| `--skip-project-count` | off | Disable Check 2 |
| `--skip-issue-refs` | off | Disable Check 3 (also auto-skipped if `glab` not on PATH) |
| `--skip-session-files` | off | Disable Check 4 |
| `--skip-command-count` | off | Disable Check 5 |
| `--skip-session-config-parity` | off | Disable Check 6 |
| `--skip-vault-dir-parity` | off | Disable Check 7 |
| `--skip-generated-rule-staleness` | off | Disable Check 8 |
| `--skip-rule-scoping` | off | Disable Check 9 |
| `--commands-dir <path>` | `<VAULT_DIR>/commands` | Override path to `commands/` directory for Check 5 |
| `--config-template <path>` | `<VAULT_DIR>/docs/session-config-template.md` | Override path to the canonical Session Config template for Check 6 |

Environment:

- `VAULT_DIR` — project root to scan. Defaults to `$PWD`. Can also be passed as positional arg 1.

## JSON output

```json
{
  "status": "ok|invalid|skipped|skipped-mode-off",
  "mode": "hard|warn|off",
  "vault_dir": "<absolute path>",
  "resolved_path": "<absolute path to CLAUDE.md or AGENTS.md, or null>",
  "resolved_kind": "claude|agents|null",
  "files_scanned": N,
  "checks_run": ["path-resolver", "project-count-sync", "issue-reference-freshness", "session-file-existence", "command-count", "session-config-parity", "vault-dir-parity", "generated-rule-staleness", "rule-scoping"],
  "checks_skipped": ["<name>: <reason>"],
  "errors": [
    { "check": "<name>", "file": "<relative path>", "line": N, "message": "<human>", "extracted": "<raw text>" }
  ],
  "warnings": [
    { "check": "<name>", "file": "<relative path>", "line": N, "message": "<human>", "extracted": "<raw text>" }
  ],
  "command_count": { "actual": N }
}
```

The `resolved_path` / `resolved_kind` pair surfaces the alias resolution outcome (issue #33 AC2) so users on either platform can audit which instruction file the checker scanned. `kind: 'claude'` for `CLAUDE.md`, `kind: 'agents'` for `AGENTS.md`, `null` when neither was found.

When `command-count` fires a drift error, the error object also carries `"command_count": { "actual": N, "claimed": M }` for easy programmatic diffing.

Exit codes:

- `0` — no errors, or errors present but `mode=warn`, or short-circuit (mode=off / no scope files)
- `1` — errors present and `mode=hard`
- `2` — invocation or infra error (missing `VAULT_DIR`, unreadable file, malformed glob)

## Session Config block (opt-in)

In repo-level `CLAUDE.md` under `## Session Config`:

```yaml
drift-check:
  enabled: true
  mode: warn          # hard | warn | off
  include-paths:
    - CLAUDE.md
    - AGENTS.md
    - _meta/**/*.md
  check-path-resolver: true
  check-project-count-sync: true
  check-issue-reference-freshness: true
  check-session-file-existence: true
  check-command-count: true
  check-session-config-parity: true
  check-vault-dir-parity: true
  check-generated-rule-staleness: true
  check-rule-scoping: true
```

When `drift-check.enabled` is `false` or the block is absent, the session-end phase is a no-op.

## Invocation points

### Session-End Phase 2.2 — opt-in quality gate

- Trigger: after Phase 2.1 `vault-sync`, before commit prep
- Behavior: full scan of the configured `include-paths`
- Error handling: `mode=hard` exits non-zero and session-end converts errors into carryover + continue; `mode=warn` surfaces in quality-gate report; `mode=off` skipped silently
- Rationale: drift is narrative-level; vault-sync catches frontmatter-level. The two gates are complementary.

### Future: wave-executor (not implemented)

A lightweight variant could run after Impl-Polish when `CLAUDE.md` is edited mid-session. Out of scope for Phase 1.

## Design notes

- **No zod.** Output is emission-only, input is plain text. Pure stdlib keeps dep footprint zero.
- **No frontmatter parsing.** Scope files are scanned as Markdown prose; `vault-sync` owns frontmatter validation.
- **Code-fence aware.** Path extraction skips triple-backtick blocks to avoid flagging example paths. Issue-ref extraction does NOT skip fences (configs and snippets often cite real live issues).
- **Section-aware Check 3.** A `#NN` mention in "Recently Closed" is context; the same mention in "What's Next" is drift. The checker tracks the current `##` heading to decide.
- **`glab` optional.** If `glab` is missing or not authenticated, Check 3 degrades to `checks_skipped` with a clear reason — never blocks.

## Relationship to vault-sync

| Aspect | vault-sync | drift-check |
|--------|-----------|-------------|
| Target | Frontmatter + wiki-links in vault/*.md | Narrative drift in CLAUDE.md / _meta/*.md |
| Schema source | Vendored Zod from baseline | None — regex + filesystem checks |
| Deps | `zod`, `yaml` | None (stdlib only) |
| Session-end phase | 2.1 | 2.2 |
| Default mode | `warn` | `warn` |

They are siblings, not overlapping. vault-sync is the structural gate; drift-check is the narrative gate.
