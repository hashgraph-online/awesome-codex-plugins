---
name: recording-architecture-decisions
description: Use when the user asks to create, write, update, amend, supersede, or evaluate an ADR, architecture decision record, durable architecture decision, decision log, or baseline sync after architecture-changing work.
---

# Recording Architecture Decisions

## Purpose

Record durable architecture decisions without losing the current-state baseline
closure. An ADR records why a decision was made; a baseline records what the
architecture is after that decision.

This skill is a lazy, task-specific workflow. It does not replace
`verification-before-completion`, does not grant completion authority, and does
not make authoritative `GateDecision` or `PolicySnapshot` outputs.

## Required Read Set

Before deciding or writing, read the smallest relevant excerpts from:

- `docs/adr/ADR-CREATION-GATE.md`
- `docs/current/AEGIS_ADR_AUTO_BACKFILL.md`
- the target project's current ADR, baseline, or authority docs that own the
  affected architecture surface

For Aegis repository changes, use this repository's `docs/adr/` and
`docs/current/` authority order. For target projects with their own ADR system,
respect that project owner instead of duplicating the same decision into
`docs/aegis/adr/`.

## When To Use

Use this skill when the user asks to:

- create, write, update, amend, supersede, or evaluate an ADR
- decide whether an architecture decision record is needed
- record a durable architecture decision or decision log entry
- close baseline sync after an ADR-relevant architecture change
- verify that an ADR action did not leave the architecture baseline stale

Do not use it for simple wording edits, ordinary README cleanup, tests-only
coverage improvements, low-risk single-file changes, or bug fixes that only
restore the existing baseline.

## Decision Flow

1. Identify the decision candidate and evidence source.
2. Run the ADR creation gate:
   - hard to reverse
   - surprising without context
   - real trade-off
3. Apply the Retro / Memory Filter:
   - executed durable decisions may become ADR or baseline memory
   - unexecuted ideas stay out of accepted architecture memory
   - process notes may use a lighter record when they do not change current
     architecture state
4. Choose exactly one ADR action: create, amend, supersede, or skip.
5. Choose the owner surface: project `docs/adr/`, `docs/aegis/adr/`, existing
   ADR, or lighter record.
6. Run Baseline Sync Closure.
7. If writing files, preserve local ADR conventions and verify structure.

## Baseline Sync Closure

If the ADR action is create, amend, or supersede, baseline sync must be checked.

Baseline sync is required when the decision changes or confirms any of:

- canonical owner or ownership map
- public API, schema, artifact shape, or behavior contract
- dependency direction or allowed cross-module relationship
- source-of-truth owner
- host compatibility strategy or install/discovery contract
- method-pack/runtime-core boundary
- runtime-ready artifact boundary or evidence model
- retained fallback, adapter, compatibility path, duplicate owner, or retirement
  schedule
- accepted architecture drift
- release or distribution strategy that future contributors would otherwise
  misread

If no baseline writeback is made, state why the existing baseline remains valid.
Never leave baseline sync implicit after create, amend, or supersede.

## Compact Output Contract

```text
Decision Candidate:
- Summary:
- Evidence source:

ADR Gate:
- Hard to reverse: yes | no | unknown
- Surprising without context: yes | no | unknown
- Real trade-off: yes | no | unknown

Retro / Memory Filter:
- Classification: executed durable decision | unexecuted idea | process note
- Memory action: record | skip | lighter record
- Reason:

ADR Action:
- create | amend | supersede | skip
- Reason:

Owner Surface:
- Target:
- Existing ADR / baseline checked:

Baseline Sync:
- Required: yes | no | unknown
- Target:
- Action: create snapshot | update baseline | cite unchanged | blocked
- Reason:

Boundary:
- Advisory method-pack signal only; not completion authority.
```

## Common Mistakes

- Writing an ADR because the topic feels important, even though the gate fails.
- Recording why in an ADR while leaving the baseline's current-state facts stale.
- Updating a baseline to match drift without first deciding whether the drift is
  intentional and ADR-worthy.
- Duplicating the same decision into both project `docs/adr/` and
  `docs/aegis/adr/` without an explicit mirror relationship.
- Treating an ADR or baseline sync as proof that the work is complete.
