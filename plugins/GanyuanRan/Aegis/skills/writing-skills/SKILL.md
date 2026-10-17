---
name: writing-skills
description: "Use when creating new skills, editing existing skills, or verifying skills work before deployment"
---

# Writing Skills

## Purpose

Create the smallest reusable skill that changes decisions or improves task
execution without constraining unrelated work. Skill changes use behavior
validation, not a code TDD route. This validation does not require loading `aegis:test-driven-development`.

## Default Path

### 1. Establish Need And Ownership

- Name the reusable behavior gap, intended users/hosts, and non-goals.
- Check whether an existing skill, project rule, host adapter, or automated
  check already owns it. Prefer the smallest existing owner.
- For an existing skill, inspect its references, manifests or generated copies,
  discovery tests, and bundled resources before changing or retiring them.
- Create a skill only for reusable, non-obvious guidance. Keep one-off project
  conventions in the project owner and automate mechanical constraints when
  practical.

### 2. Record Behavior Before Editing

Use representative tasks, not questions that merely ask the agent to recite
instructions.

- New skill: run a no-skill control.
- For an existing skill, run the current version first; add a no-skill ablation
  only when testing whether the skill itself needs to exist.
- Cover positive triggers, negative near-misses, and a pressure or application
  case appropriate to the skill type.
- Record decisions, missed or extra invocations, unsafe workarounds, evidence
  references, and unknowns. Do not treat line or byte counts as behavior proof.

If meaningful behavior cannot be evaluated, stop at `needs-verification`; do
not claim that the skill is deployment-ready or capability-preserving.

### 3. Design The Minimum Instruction Surface

- Assume the agent is capable. Include only non-obvious context, decision
  criteria, safety boundaries, and steps whose omission caused an observed gap.
- Match specificity to risk: allow judgment for open work; use exact sequences
  only for fragile, permission-sensitive, or safety-critical operations.
- Keep the description concise, third-person, and discriminating. State the
  capability and when it applies; add an exclusion only when it prevents likely
  misrouting. Do not turn the description into a procedural shortcut.
- Keep the executable default path and non-omittable constraints in `SKILL.md`.
  Move substantial conditional detail to a direct reference and state the
  evidence trigger for reading it.
- Keep references one level deep where practical. Do not load every reference
  by default or duplicate its content in the main body.
- Add an example only when it materially stabilizes a decision or output. One
  representative example is normally enough.
- Keep portable method instructions host-neutral. Put host tool names, install
  paths, and UI choreography in their host-owned documentation.

The canonical repository shape is `skills/<skill-name>/SKILL.md` with only the
supporting references, scripts, or assets the workflow actually uses. Use the
repository's host docs or the target host's live specification for optional
metadata instead of copying a vendor manual into the skill.

### 4. Make The Smallest Change

Address observed gaps and remove superseded duplication in the same slice.
Preserve public attribution and any externally supported contract. When
retiring an internal owner, fallback, or resource, compose
`aegis:anti-entropy-governance`; do not leave a compatibility copy without
dependency evidence.

Do not convert one model's phrasing, one historical incident, or a hypothetical
edge case into a universal rule.

### 5. Validate The Candidate

Re-run the same positive, negative, and pressure/application scenarios under a
comparable model, tool, and host configuration. Compare outcomes, not wording.

Also verify:

- frontmatter, name, and description parse on supported hosts;
- intended requests still discover the skill and near-misses do not;
- every conditional reference is reachable from an explicit trigger;
- changed scripts run successfully;
- retired files and instructions have no live references;
- repository workflow, boundary, packaging, and host checks relevant to the
  touched surface pass.

If behavior regresses, restore the missing obligation or narrow the change;
do not add a second owner or fallback to mask it.

## Scenario Selection

| Skill type | Representative evidence |
| --- | --- |
| Discipline or safety | realistic pressure and authorization boundaries |
| Technique | application, variation, and missing-information cases |
| Pattern | recognition, application, and counter-example cases |
| Reference | retrieval, correct use, and common-gap cases |

For a complex or high-risk skill where an independent evaluator adds confidence,
read `testing-skills-with-subagents.md`.

## Completion Record

Keep the result compact and auditable in natural prose or equivalent fields:

- behavior gap and canonical owner;
- baseline and candidate scenario results;
- retained and retired obligations/resources;
- trigger and reference checks;
- verification commands and uncovered hosts/models;
- status: `verified`, `needs-verification`, or `blocked`.

This is method-pack evidence, not authoritative completion or deployment
approval.
