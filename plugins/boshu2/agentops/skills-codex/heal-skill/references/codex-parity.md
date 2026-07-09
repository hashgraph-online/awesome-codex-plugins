# Codex Parity Repair

Use this workflow when `skills/<name>/SKILL.md` is canonically correct but
`skills-codex/<name>/SKILL.md` has drifted into bad Codex UX in the checked-in runtime artifact.

## Principles

1. `skills/<name>/SKILL.md` remains the canonical workflow contract.
2. `skills-codex/<name>/` is the checked-in Codex runtime artifact and may need direct maintenance.
3. Durable Codex-only body edits that should survive broader refactors belong in `skills-codex-overrides/<name>/SKILL.md`.
4. Codex operator-layer prompt edits belong in `skills-codex-overrides/<name>/prompt.md`.

## Audit First

Run:

```bash
bash scripts/audit-codex-parity.sh
```

Or target one skill:

```bash
bash scripts/audit-codex-parity.sh --skill swarm
```

The audit flags the failure classes that Codex maintenance keeps missing today:

- Claude-era task primitives
- Claude-only backend reference names and team terminology
- duplicated runtime phrases created by blind search/replace

## Repair Loop

For each flagged skill:

1. Read `skills/<name>/SKILL.md` to confirm whether the canonical contract is correct.
2. Read `skills-codex/<name>/SKILL.md` to see the broken checked-in Codex body.
3. Read `skills-codex-overrides/<name>/prompt.md` and `skills-codex-overrides/catalog.json`.
4. If the source contract is wrong, fix `skills/<name>/SKILL.md` first.
5. If the shipped Codex artifact is wrong, update `skills-codex/<name>/SKILL.md`.
6. If the source is correct but Codex needs a durable tailoring layer, create or update `skills-codex-overrides/<name>/SKILL.md`.
7. Re-run validation:
   - `bash scripts/audit-codex-parity.sh`
   - `bash scripts/validate-codex-generated-artifacts.sh --scope worktree`
   - `bash scripts/validate-codex-override-coverage.sh`

## LLM Repair Guidance

When doing the actual rewrite, the LLM should:

- preserve the behavior contract from `skills/<name>/SKILL.md`
- remove Claude-only primitive/tool names from the Codex body
- replace mechanical rewrites with real Codex-native instructions
- keep durable Codex-only delta in `skills-codex-overrides/<name>/SKILL.md` when it should remain distinct from the checked-in artifact

If a skill keeps needing Codex-only body surgery, update
`skills-codex-overrides/catalog.json` so the treatment matches reality instead
of pretending the skill is still parity-only.
