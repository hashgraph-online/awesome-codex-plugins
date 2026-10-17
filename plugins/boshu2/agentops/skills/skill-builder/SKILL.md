---
name: skill-builder
description: 'Create, repair, audit or consolidate agent skills (SKILL.md packages). Use when: writing or fixing a skill, its description or structure. Not for one-off lessons; use Memory.'
practices:
- pragmatic-programmer
- refactoring
hexagonal_role: supporting
consumes: []
produces:
- skill-source-package
- skill-hygiene-report
- converted-skill
- operationalization-proposal
context_rel: []
skill_api_version: 1
user-invocable: true
context:
  window: fork
  intent:
    mode: questions
  sections:
    exclude:
    - HISTORY
metadata:
  capabilities: [skill_builder, heal_skill, export_skill, distill_expertise]
  effects: [write_skill_source, write_build_report, regenerate_skill_projections, repair_skill_projections, write_converted_skill_projection, write_advisory_proposal]
  canonical_status: canonical
  disposition: keep_specialist
  tier: meta
  dependencies: []
  stability: experimental
output_contract: build-report.json for creation, audit-report.json for audit, target-valid exported files for conversion, or an advisory expertise proposal
---
# Skill Builder

Create, repair, audit or export one canonical skill package, or turn supported
expertise into a small authoring proposal.

## Decide whether to create anything

Apply these before any creation step, including when the request already names
the new skill or file it wants:

1. **Find the existing owner.** Search skills, references, checklists and
   instruction files for one that already handles the behavior. Extend that
   owner rather than adding a root.
2. **Count independent occurrences.** A new skill, gate, library or workflow
   needs three independently evidenced real occurrences and a successful
   reapplication to a source case without missing context. Fewer occurrences
   support only a narrow note in an existing owner; one incident is an
   observation, not a skill. An authoritative source supports only a faithful
   statement of that source.
3. **Name the consumer of every new artifact.** A proposed process artifact
   (a report, ledger, counter, dashboard or tracker) needs a concrete consumer,
   the decision it informs, the observed defect it answers and a retirement
   condition. If any is missing, leave it out; code written only to consume it
   is no consumer.
4. **No action is a valid result**, and so is a short addition to an existing
   owner. Say what the evidence supports before drafting, build only what the
   caller then authorizes, and return a proposal inline unless a durable one
   was requested.
5. **A built package proves no benefit.** Route behavioral benefit to
   [Skill Eval](../skill-eval/SKILL.md) and acceptance judgment to
   [Validate](../validate/SKILL.md).

## Choose the requested operation

| Need | Entry point |
|---|---|
| Create a source package | `scripts/build.sh` with `from-scratch`, `from-template` or `absorb-external` |
| Check package structure | `scripts/heal.sh --check [--strict] skills/<slug>` |
| Repair owned projections | `scripts/heal.sh --fix skills/<slug>` |
| Inspect audit evidence | `scripts/audit.sh [--profile canonical|portable|external-observation] [--json <path>] skills/<slug>` |
| Export to another platform | [Conversion](#conversion) |
| Make repeated expertise reusable | [Distill expertise](#distill-expertise) |

Run only the selected operation. Skills remain optional tools within the native
caller's authorized outcome; this skill does not add execution phases, own work,
operate Git, validate a software candidate, or decide delivery and retries.
Inputs, report destinations, exit codes and recovery from partial creation are
in [build and check mechanics](references/build-mechanics.md).

## Create and maintain

Treat external skills as structural signals only. Clean-room output must not
copy their names, prose, prompts, scripts or examples. `from-template` reuses
metadata defaults; `absorb-external <slug> --from <path>` verifies an input and
creates a blank source package. Neither imports another skill's content.

`scripts/build.sh` creates one incomplete source package containing only
`SKILL.md` with `metadata.authoring_state: scaffold`; helpers, references and
assets are conditional on the actual behavior. Replace the placeholders and
state applicability, inputs, authority, result, completion and failure in the
layout that makes them clear. Remove the scaffold state only after authoring
the behavior; strict source checks reject it. Removing it is an author
assertion, not proof of semantic completeness.

Edit `skills/<slug>/` as the source owner. Check the completed source with
`scripts/heal.sh --check --strict skills/<slug>`, then regenerate its owned
projections through the repository's owning commands. Inspect the generated
diff; hand-edit no projection.

Creation is staged, not atomic. If a later stage fails, keep the created source
and any report, capture the exit and diagnostic, and report source creation
separately from projection and check completion. Never call a partial result a
completed package or delete it to rerun creation. Missing required scripts,
references or runtime support block only their dependent operation; name that
resource and continue work that does not depend on it.

Check mode is read-only; fix mode regenerates owned projections for explicit
targets and invents no source behavior. The default audit reports static
conformance, located effects, behavioral evidence and non-gating authoring
suspicions separately, with no total, rating or aggregate verdict. Effects and
behavior stay `NOT_PROVEN` because the audit runs no skill or trial. Exact checks,
exit codes and the opt-in legacy schema live in [audit checks](references/audit-checks.md),
[authoring doctrine](references/authoring-doctrine.md) and
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
Every runtime, Codex included, loads `skills/` directly; this ad-hoc exporter
never produces a shipped tree.

## Distill expertise

When the caller wants a reusable rule, apply the decision rules above, then
begin with cited occurrences or a named authoritative source. State the trigger,
desired behavior, inputs, outputs, negative example and limits. Preserve short
source excerpts or command results with resolvable citations. Use Research's
[pattern mode](../research/SKILL.md#pattern-evidence) when the claim needs
exemplars and a holdout before packaging. Show a negative or holdout case and
how the proposed rule returns the right decision. Minimal recovery state needs
a named evidence-loss or corruption risk.

Respect [Memory's source and destination rules](../memory/SKILL.md) for mined
material. Evidence cannot publish itself as policy. A proposal-only request ends
with the proposal. Repair ordinary known defects within existing authority; tool
failures remain explicit facts for the native caller, not an automatic helper
chain.

For an actual package edit, use the [source template](references/skill-template.md)
for required fields and [context density guidance](references/context-density-checks.md)
when deciding which prose earns a place. Neither requires adding a new skill.
