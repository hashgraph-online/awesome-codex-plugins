# Phase 2: Quality Gate — Verification Checklist

> Extracted from `SKILL.md` Phase 2 to reduce skill file size. This is the authoritative source for session-end quality gate checks.

Run ALL checks — do NOT skip any:

> **Quality Reference:** Run Full Gate quality checks per the quality-gates skill. Read `test-command`, `typecheck-command`, and `lint-command` from Session Config (defaults: `pnpm test --run`, `tsgo --noEmit`, `pnpm lint`).

1. **Full Gate checks**: TypeScript (0 errors), tests (must pass), lint (must pass, warnings OK)
   Alternatively, run `node "${CLAUDE_PLUGIN_ROOT:-${CODEX_PLUGIN_ROOT:-$PLUGIN_ROOT}}/scripts/run-quality-gate.mjs" --variant full-gate --config "$CONFIG"` for deterministic quality gate execution with structured JSON output.
   - **Stub detection:** if `result.stubbed` is non-empty, emit WARN per SKILL.md Phase 2.0a. Refer to `docs/recipes/quality-gate-container-pattern.md` for the container-PHPUnit pattern.
2. **Git status**: `git status` → understand all changes
3. **Uncommitted changes**: everything should be staged for commit
4. **No debug artifacts**: search for `console.log`, `debugger`, `TODO: remove` in changed files
5. **Vault validation** (opt-in via `vault-sync.enabled`): run the `vault-sync` validator per SKILL.md Phase 2.1. In `hard` mode, validation errors block the session close; in `warn` mode they are surfaced in the quality gate report but do not block; in `off` mode the gate is bypassed. Dangling wiki-links are always warnings only.

If any check fails:
- Fix it if quick (<2 min)
- Otherwise create a `priority:high` issue for immediate follow-up
- Do NOT commit broken code
