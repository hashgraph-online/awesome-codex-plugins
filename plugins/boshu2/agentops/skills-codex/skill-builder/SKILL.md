---
name: skill-builder
description: Create a metadata-complete AgentOps skill
---
# Skill Builder — Create one skill source package

Create one `skills/<slug>/` package, verify its structure, regenerate the
metadata-owned projections, and stop. The builder does not schedule work,
allocate writers, operate Git, promote learnings, or decide whether the new
skill should be invoked.

Before creating a new root, search `skills/*/SKILL.md` for an existing owner.
Extend an existing skill when it already owns the requested behavior.

## Constraints

- Create exactly one source package because metadata must have one canonical
  owner.
- Treat external skills as structural signals only because clean-room output
  must not copy names, prose, prompts, scripts, or examples.
- Regenerate projections once and stop because validation, revision, Git, and
  delivery remain caller-owned.

## Inputs

Choose exactly one mode:

- `from-scratch <slug>` creates a blank source package.
- `from-template <slug> --like <existing-slug>` uses the existing skill only
  for metadata defaults; it does not copy its prose.
- `absorb-external <slug> --from <path>` verifies the source exists, then
  creates a clean-room blank package without copying names, prose, prompts,
  scripts, or examples.

The caller may set `SKILL_TIER`, `SKILL_DEPENDENCIES`,
`SKILL_CAPABILITIES`, and `SKILL_EFFECTS`. Values that represent lists must be
JSON arrays.

## Procedure

1. Run `scripts/build.sh` with one mode and one new slug.
2. Fill the generated placeholders with the skill's actual behavior.
3. Run `skills/heal-skill/scripts/heal.sh --check --strict skills/<slug>`.
4. Run `scripts/generate-skill-mesh.py` to derive the catalog, registry,
   router, graph, maps, counts, and runtime image manifests from `SKILL.md`
   metadata.
5. Run `scripts/codex-sync.sh --only <slug>` and
   `scripts/regen-codex-hashes.sh --only <slug>` to derive the Codex twin.
6. Inspect the generated diff. Validation and delivery remain caller-owned.

`build.sh` performs steps 1, 3, 4, and 5 once. It never retries or chooses a
next action.

## Output

The source package contains:

```text
skills/<slug>/
├── SKILL.md
└── scripts/validate.sh
```

The build report is `.agents/audits/<slug>-build.json` and conforms to
`schemas/build-report.json`. Generated inventories and runtime projections are
not additional sources of truth.

## Checks

- The slug and frontmatter `name` match.
- Metadata declares `tier`, `dependencies`, `capabilities`, `effects`,
  `canonical_status`, and `disposition`.
- Every hard dependency names a live skill.
- The generated package contains no Git, tracker, queue, retry, release, or
  delivery behavior.
- External material is treated only as a signal that a clean-room skill may be
  useful; its content is not copied.

## Failure behavior

Any invalid input, structural failure, projection failure, or Codex sync
failure exits nonzero after one attempt. The caller decides whether to revise
or invoke the builder again.

## References

- [skill template](references/skill-template.md)
- [heal-skill](../heal-skill/SKILL.md)
