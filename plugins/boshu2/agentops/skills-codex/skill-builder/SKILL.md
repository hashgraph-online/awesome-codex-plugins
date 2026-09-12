---
name: skill-builder
description: 'Create, adapt, consolidate or repair skill packages and projections. Use when: authoring guidance, descriptions or structure; Skill Eval measures behavioral benefit.'
---
# Skill Builder

Create, repair, audit or export one canonical skill package, or turn supported
expertise into a small authoring proposal. Search existing owners before adding
a root. Extend the owner that already handles the behavior.

## Choose the requested operation

| Need | Entry point |
|---|---|
| Create a source package | `scripts/build.sh` with `from-scratch`, `from-template` or `absorb-external` |
| Check package structure | `scripts/heal.sh --check [--strict] skills/<slug>` |
| Repair owned projections | `scripts/heal.sh --fix skills/<slug>` |
| Audit authoring quality | `scripts/audit.sh [--strict] [--json <path>] skills/<slug>` |
| Export to another platform | [Conversion](#conversion) |
| Make repeated expertise reusable | [Distill expertise](#distill-expertise) |

Run only the selected operation. Skills remain optional tools within the native
caller's authorized outcome; this skill does not add execution phases, own work,
operate Git, validate a software candidate, or decide delivery and retries.

## Create and maintain

Treat external skills as structural signals only. Clean-room output must not
copy their names, prose, prompts, scripts or examples. `from-template` reuses
metadata defaults; `absorb-external <slug> --from <path>` verifies an input and
creates a blank source package. Neither imports another skill's content.

For creation, supply one input to `scripts/build.sh`, then replace placeholders
with the actual behavior. The caller can supply `SKILL_TIER`,
`SKILL_DEPENDENCIES`, `SKILL_CAPABILITIES` and `SKILL_EFFECTS`; lists are JSON
arrays. The result is one source package with `SKILL.md` and
`scripts/validate.sh`. The builder's report is
`.agents/scratch/skill-builder/<slug>-build.json` under
[build-report.json](schemas/build-report.json).

Edit `skills/<slug>/` as the source owner. Check the completed source with
`scripts/heal.sh --check --strict skills/<slug>`, then regenerate its owned
projections through the repository's owning commands. `scripts/regen-all.sh`
is the integrated projection recipe; `scripts/generate-skill-mesh.py`,
`scripts/codex-sync.sh --only <slug>` and
`scripts/regen-codex-hashes.sh --only <slug>` are the existing scoped surfaces.
Do not repeat work already performed by `build.sh` unless source changes
require it. Inspect the generated diff; hand-edit no projection.

Check/heal targets must be real direct children of `skills/`; reject missing
paths, traversal and symlink spellings. Check mode is read-only. Fix mode
regenerates owned projections for explicit targets and does not invent source
behavior. Findings name their code, target and concrete issue; `--strict`
returns nonzero for findings. Check the slug/name match, description, API
version, metadata, live dependencies and linked resources.

Deep audit reports structural and advisory authoring findings; it is not a
candidate verdict. Its optional JSON follows
[audit-report.json](schemas/audit-report.json). Interpret static scores as
structure and authoring signals, not proof that a skill works. Exact checks live
in [audit checks](references/audit-checks.md),
[authoring doctrine](references/authoring-doctrine.md), and
[Codex parity](references/codex-parity.md).

## Conversion

Use `bash skills/skill-builder/scripts/converter/convert.sh <skill-dir> <target>
[output-dir]` for an explicit out-of-tree export. Targets are `codex`, `cursor`
and `test`; `--all` selects all source packages, and `--codex-layout inline`
selects the legacy inline Codex layout. Read
[SkillBundle](references/converter/skill-bundle-schema.md) when format details
matter. Parse the source once, render the target, then validate resource parity
and target format. Report layout and any omitted Cursor references.

The default export is `.agents/projections/converter/<target>/<skill-name>/`.
The exporter clean-writes its output directory, so use only the explicit derived
target: refuse a source package, its ancestor, or the repository root. Preserve
the source unchanged and fix the source or adapter instead of editing output.
A parse, write, format or required-resource failure leaves an incomplete export.
The shipped `skills-codex/**` remains owned by `scripts/codex-sync.sh` through
`scripts/regen-all.sh`; this ad-hoc exporter never replaces that authority.

## Distill expertise

When the caller wants a reusable rule, begin with cited occurrences or a named
authoritative source. State the trigger, desired behavior, inputs, outputs,
negative example and limits. Prefer an addition to an existing reference or
skill over a new root, library, gate or workflow; no action is a valid result.

An abstraction needs three independently evidenced real occurrences and a
successful reapplication to a source case without missing context. Preserve
short source excerpts or command results with resolvable citations. Fewer
occurrences support a narrow reference note; an authoritative source substitutes
only for a faithful statement of that source, not a wider generalization.
Use Research's [pattern mode](../research/SKILL.md#pattern-evidence) when the
claim needs exemplars and a holdout before packaging.

A proposed process artifact must have a concrete consumer, a subject or release
decision it informs, an observed defect and a retirement condition. If any is
missing, omit the artifact. Code written only to consume it supplies no consumer.
Minimal recovery state needs a named evidence-loss or corruption risk. Show a
negative/holdout case and how the proposed rule returns the right decision.

Return the proposal inline unless a durable proposal was requested. Respect
[Memory's source and destination rules](../memory/SKILL.md) for mined material.
Evidence cannot publish itself as policy. Build an artifact only when the
caller's authorization includes adoption; a proposal-only request ends with the
proposal. Repair ordinary known defects within existing authority; tool failures
remain explicit facts for the native caller, not an automatic helper chain.

For an actual package edit, use the [source template](references/skill-template.md)
for required fields and [context density guidance](references/context-density-checks.md)
when deciding which prose earns a place. Neither requires adding a new skill.
