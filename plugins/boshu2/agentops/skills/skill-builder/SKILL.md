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

`<skill-dir>` is the directory that contains this SKILL.md. Claude Code shows it
as "Base directory for this skill"; Codex lists this skill's SKILL.md path; in
an AgentOps source checkout it is `skills/skill-builder`. Replace `<skill-dir>`
with that absolute path before running a command. The working directory stays
the user's repository. If the host did not show where this skill is installed,
use the directory of the SKILL.md you read. If you cannot determine it, do not
guess a path or run a same-named script from the current repository; say the
bundled script is unavailable and apply the rules and doctrine here to the
package by hand and use its repository's own checks.

| Need | Entry point |
|---|---|
| Create a source package | `bash "<skill-dir>/scripts/build.sh" from-scratch <slug>`, `from-template <slug> --like <existing-slug>` or `absorb-external <slug> --from <path>` |
| Check package structure | `bash "<skill-dir>/scripts/heal.sh" --check [--strict] skills/<slug>` |
| Repair the skill mesh | `bash "<skill-dir>/scripts/heal.sh" --fix skills/<slug>` |
| Inspect audit evidence | `bash "<skill-dir>/scripts/audit.sh" [--profile canonical\|portable\|external-observation] [--json <path>] skills/<slug>` |
| Merge overlapping skills | [Consolidate](#consolidate) |
| Export to another platform | [Conversion](#conversion) |
| Make repeated expertise reusable | [Distill expertise](#distill-expertise) |

Run only the selected operation. `build.sh` and `heal.sh --fix` work on
`skills/` of an AgentOps source checkout and refuse with exit 2 elsewhere, such
as from a plugin install, instead of writing into its cache; `heal.sh --fix`
checks the source first, so a target with findings exits 1 before that refusal.
For a skill in another repository or a user's skills directory, apply the rules
and doctrine here to that directory and use its own checks; `audit.sh` resolves
targets from the current directory and has `portable` and
`external-observation` profiles.
Roots, inputs, report destinations, exit codes and recovery from partial
creation are in [build and check mechanics](references/build-mechanics.md).

## Create and maintain

Treat external skills as structural signals only. Clean-room output must not
copy their names, prose, prompts, scripts or examples. Every creation mode
writes the same blank scaffold: `from-template` only checks the named skill and
records it as `source_hint`, and `absorb-external` only verifies its input.
Neither imports another skill's content or metadata.

`build.sh` creates one incomplete source package containing only
`SKILL.md` with `metadata.authoring_state: scaffold`; helpers, references and
assets are conditional on the actual behavior. Replace the placeholders and
state applicability, inputs, authority, result, completion and failure in the
layout that makes them clear. An ending such as "hand off" or "then stop" can
end the caller's turn when the skill runs inline; read
[endings](references/authoring-doctrine.md#state-authority-and-a-usable-failure-path)
before writing one. Remove the scaffold state only after authoring the
behavior; strict source checks reject it. Removing it is an author assertion,
not proof of semantic completeness.

Before editing a skill after a miss or a review finding, read
[changing existing text](references/authoring-doctrine.md#change-existing-text-at-its-owning-layer);
it decides when text stays unchanged, when a list stays explicit, and what to
check before cutting a line.

Edit `skills/<slug>/` as the source owner. Check the completed source with
`bash "<skill-dir>/scripts/heal.sh" --check --strict skills/<slug>`. In an
AgentOps source checkout only, run `bash scripts/regen-all.sh` from the
repository root to regenerate every owned projection, including
`plugin/skills/`; `bash "<skill-dir>/scripts/heal.sh" --fix skills/<slug>`
regenerates only the skill mesh and leaves plugin copies unchanged. Inspect the
generated diff; hand-edit no projection. A clean check says nothing about
behavior: when an edit changes
when the skill routes, what it asks, when it stops, what it commits or
publishes or how it degrades, or cuts a line that recorded provenance protects,
report that behavior as unmeasured unless a [Skill Eval](../skill-eval/SKILL.md)
result measured that behavior, and name what was missing (a runner, a host or
the caller's authorization). Typo, path and formatting edits need no such note.

Creation is staged, not atomic. If a later stage fails, keep the created source
and any report and follow [recovery](references/build-mechanics.md#staged-creation-and-recovery);
never call a partial result a completed package or delete it to rerun creation.
A missing script, reference or runtime blocks only the operation that needs it;
name it and continue the rest.

The default audit reports conformance, effects, behavior and authoring
suspicions separately, with no total or verdict; effects and behavior stay
`NOT_PROVEN` because it runs no skill. Checks, exit codes and the opt-in legacy
schema are in [audit checks](references/audit-checks.md); what Codex reads is in
[Codex parity](references/codex-parity.md).

## Consolidate

Merge only when two skills own the same behavior; a shared passage or two is a
cross-link, not a merge. Apply the decision rules above, then pick one owner:
keep the skill with the stronger contract (clearer applicability, authority,
result and failure path) and move into it only the rules the other has and it
lacks. Before retiring the other name, search the skills, references,
instruction files, goal prompts, workflows and docs for callers that invoke it
by name, point each at the owner, and keep the old name until every caller does.
In the AgentOps repository, also record the retired name and its new owner in
`docs/MIGRATION.md` and add the slug to `REMOVED_SKILLS` in
`scripts/check-cathedral-cut-conformance.py`, which fails if the skill comes
back; never delete a skill there without that tombstone. A merge can move
routing, so report as unmeasured whether the requests the retired skill caught
now reach the owner unless a routing or [Skill Eval](../skill-eval/SKILL.md)
result measured it.

## Conversion

Run `bash "<skill-dir>/scripts/converter/convert.sh" <source-skill-dir> <target>
[output-dir]` to export one package, or `--all`, to `codex`, `cursor` or `test`
outside the shipped tree. Before an export, read
[running the converter](references/converter/skill-bundle-schema.md#run-the-converter)
for path resolution, the default output and its refusals. Preserve the source;
fix the source or adapter, never the exported output.

## Distill expertise

When the caller wants a reusable rule, apply the decision rules above and begin
with cited occurrences or a named authoritative source. State the trigger,
desired behavior, inputs, outputs, limits and a negative or holdout case the
rule decides correctly, with short source excerpts and resolvable citations.
Use Research's [pattern mode](../research/SKILL.md#pattern-evidence) when the
claim needs exemplars and a holdout, and
[Memory's source and destination rules](../memory/SKILL.md) for mined material.
A proposal-only request ends with the proposal. For an actual package edit, use
the [source template](references/skill-template.md) for required fields and the
admission test in [changing existing text](references/authoring-doctrine.md#change-existing-text-at-its-owning-layer)
to decide which prose earns a place.
