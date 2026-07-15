---
name: heal-skill
description: Check or repair structural hygiene in
---
# Heal Skill — Check one or more skill packages

`heal-skill` is a specialist hygiene tool. It reports structural defects in
canonical source skills and generated Codex twins. With `--fix`, it repairs only
owned projections through their generators. It does not schedule work, operate
Git, validate a software candidate, or decide what happens after a failure.

## Inputs

```bash
bash skills/heal-skill/scripts/heal.sh --check [skills/<slug> ...]
bash skills/heal-skill/scripts/heal.sh --check --strict [skills/<slug> ...]
bash skills/heal-skill/scripts/heal.sh --fix [skills/<slug> ...]
```

Every explicit target must be a real, direct child of `skills/` or
`skills-codex/`. Missing paths, traversal, and symlink spellings are rejected.

## Procedure

1. Resolve and contain all requested target directories.
2. Parse each `SKILL.md` frontmatter.
3. Check the path/name match, description, API version, disposition metadata,
   and linked local references.
4. Print every finding once.
5. In `--fix` mode only, regenerate metadata-owned projections and scoped Codex
   twins, then stop.

`--check` is read-only. `--strict` makes any finding produce exit 1. A failed
fix is returned to the caller; the skill does not retry or select another
action.

## Deep content audit

The optional read-only content audit is:

```bash
bash skills/heal-skill/scripts/audit.sh [--strict] [--json <path>] skills/<slug>
```

It combines the structural result with deterministic authoring checks and an
advisory quality score. It is not the core `Validate` phase, does not write a
`verdict.v2`, and has no delivery authority. Check definitions live in
[audit-checks.md](references/audit-checks.md); density scoring is described in
[context-density-checks.md](references/context-density-checks.md).

## Output

Structural findings are printed as:

```text
[FINDING_CODE] skills/example: concrete explanation
```

Deep audit JSON conforms to [audit-report.json](schemas/audit-report.json).
The caller owns any subsequent edit or invocation.

## Checks

- Check mode never mutates files.
- Fix mode changes only an explicit source target and its owned projections.
- A second identical fix is idempotent.
- Generated Codex parity follows [codex-parity.md](references/codex-parity.md).
- Remaining non-fixable findings stay explicit.

## Related executable specifications

- [heal-skill.feature](references/heal-skill.feature)
- [skill-auditor.feature](references/skill-auditor.feature)
