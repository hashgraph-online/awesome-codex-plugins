---
name: skill-builder
description: Create a metadata-complete AgentOps skill
---
# Skill Builder — Create, heal, and audit skill packages

`skill-builder` owns the full structural lifecycle of one `skills/<slug>/`
source package: create it, verify its structure, repair owned projections, and
audit its content discipline. It does not schedule work, allocate writers,
operate Git, validate a software candidate, promote learnings, or decide what
happens after a failure.

Before creating a new root, search `skills/*/SKILL.md` for an existing owner.
Extend an existing skill when it already owns the requested behavior.

## Modes

| Trigger phrases | Mode | Entry point |
|---|---|---|
| "create a skill", "scaffold skill", "new skill" | create (build) | `scripts/build.sh` |
| "absorb external skill" | create (absorb-external) | `scripts/build.sh` |
| "check skill package" | check | `scripts/heal.sh --check [--strict]` |
| "heal skill", "repair skill hygiene" | heal | `scripts/heal.sh --fix` |
| "audit skill structure" | audit | `scripts/audit.sh` |

## Constraints

- Create exactly one source package because metadata must have one canonical
  owner.
- Treat external skills as structural signals only because clean-room output
  must not copy names, prose, prompts, scripts, or examples.
- Regenerate projections once and stop because validation, revision, Git, and
  delivery remain caller-owned.
- Check and audit modes never mutate files; fix mode changes only an explicit
  source target and its owned projections, because source behavior remains
  human-authored.

## Create mode

Choose exactly one build input:

- `from-scratch <slug>` creates a blank source package.
- `from-template <slug> --like <existing-slug>` uses the existing skill only
  for metadata defaults; it does not copy its prose.
- `absorb-external <slug> --from <path>` verifies the source exists, then
  creates a clean-room blank package without copying names, prose, prompts,
  scripts, or examples.

The caller may set `SKILL_TIER`, `SKILL_DEPENDENCIES`,
`SKILL_CAPABILITIES`, and `SKILL_EFFECTS`. Values that represent lists must be
JSON arrays.

### Procedure

1. Run `scripts/build.sh` with one mode and one new slug.
2. Fill the generated placeholders with the skill's actual behavior.
3. Run `scripts/heal.sh --check --strict skills/<slug>`.
4. Run `scripts/generate-skill-mesh.py` to derive the catalog, registry,
   router, graph, maps, counts, and runtime image manifests from `SKILL.md`
   metadata.
5. Run `scripts/codex-sync.sh --only <slug>` and
   `scripts/regen-codex-hashes.sh --only <slug>` to derive the Codex twin.
6. Inspect the generated diff. Validation and delivery remain caller-owned.

`build.sh` performs steps 1, 3, 4, and 5 once. It never retries or chooses a
next action.

## Heal and check modes

```bash
bash skills/skill-builder/scripts/heal.sh --check [skills/<slug> ...]
bash skills/skill-builder/scripts/heal.sh --check --strict [skills/<slug> ...]
bash skills/skill-builder/scripts/heal.sh --fix [skills/<slug> ...]
```

Every explicit target must be a real, direct child of `skills/` or
`skills-codex/`. Missing paths, traversal, and symlink spellings are rejected.

### Procedure

1. Resolve and contain all requested target directories.
2. Parse each `SKILL.md` frontmatter.
3. Check the path/name match, description, API version, disposition metadata,
   and linked local references.
4. Print every finding once.
5. In `--fix` mode only, regenerate metadata-owned projections and scoped Codex
   twins, then stop.

`--check` is read-only. `--strict` makes any finding produce exit 1. A failed
fix is returned to the caller; the skill does not retry or select another
action. Structural findings are printed as:

```text
[FINDING_CODE] skills/example: concrete explanation
```

Generated Codex parity follows [codex-parity.md](references/codex-parity.md).
A second identical fix is idempotent, and remaining non-fixable findings stay
explicit.

## Audit mode

The optional read-only deep content audit is:

```bash
bash skills/skill-builder/scripts/audit.sh [--strict] [--json <path>] skills/<slug>
```

It combines the structural result with deterministic authoring checks and an
advisory quality score. It is not the core `Validate` phase, does not write a
`verdict.v2`, and has no delivery authority. Check definitions live in
[audit-checks.md](references/audit-checks.md); density scoring is described in
[context-density-checks.md](references/context-density-checks.md).

## Output

A created source package contains:

```text
skills/<slug>/
├── SKILL.md
└── scripts/validate.sh
```

The build report is `.agents/audits/<slug>-build.json` and conforms to
`schemas/build-report.json`. Deep audit JSON conforms to
`schemas/audit-report.json`. Generated inventories and runtime projections are
not additional sources of truth. The caller owns any subsequent edit or
invocation.

## Checks

- The slug and frontmatter `name` match.
- Metadata declares `tier`, `dependencies`, `capabilities`, `effects`,
  `canonical_status`, and `disposition`.
- Every hard dependency names a live skill.
- The generated package contains no Git, tracker, queue, retry, release, or
  delivery behavior.
- External material is treated only as a signal that a clean-room skill may be
  useful; its content is not copied.
- Check mode never mutates files; fix mode changes only an explicit source
  target and its owned projections.

## Failure behavior

Any invalid input, structural failure, projection failure, or Codex sync
failure exits nonzero after one attempt. The caller decides whether to revise
or invoke the builder again.

## References

- [skill template](references/skill-template.md)
- [authoring doctrine](references/authoring-doctrine.md) — prose-quality
  principles behind the advisory `authoring` audit block
- [heal.feature](references/heal.feature)
- [skill-auditor.feature](references/skill-auditor.feature)
