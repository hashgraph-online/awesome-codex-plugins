---
name: spec-writer
description: Create or refine spec-superflow planning artifacts. Invoke when the change is understood well enough to write proposal.md, specs/, design.md, and tasks.md.
---

# Spec Writer

## Bundled runtime

Before executing a CLI line below, replace its leading `SSF` with `node "<plugin-root>/scripts/spec-superflow.mjs"`; `<plugin-root>` is the absolute directory two levels above this file. Never run `SSF` literally or call an `ssf` from `PATH`.

Create or refine planning artifacts when the change has moved beyond exploration.

## New planned changes

For a new request (no state or workflow auto), or workflow_variant planned, write proposal.md and tasks.md together without pausing between individual artifacts. Proposal holds the goal, in/out scope, acceptance and risks; tasks holds ordered deliverables and proof commands. Add specs only for behavior needing durable scenarios and design only for unresolved architectural decisions. Do not create execution-contract.md or duplicate the task list in another plan.

Check shared interfaces against the real source once, then self-check the problem, scope, dependencies and proof. Present one approval request only if this concrete plan lacks approval. After approval run `SSF workflow start <dir> --path planned --confirm --reason "<user decision>"` and continue implementation. No intermediate planning/bridging transitions or independent reader agent. A semantic revision uses the same command after approval; a nonsemantic correction uses execution resync and retains failed-review history. The remaining sections apply only to existing legacy changes.

## Required Inputs

Read `.spec-superflow.yaml` (especially `dp_0_decisions`, `dp_0_confirmed`) and any existing planning artifacts. If `dp_0_confirmed` is not `true`, stop and route back to `workflow-start` for DP-0.

## Config Check

Run: `SSF runtime config --get artifacts.order` — generate in configured order (default: proposal → specs → design → tasks). Run with `artifacts.skip` — skip any listed artifacts.

## Artifact Roles

- `proposal.md`: why and scope
- `specs/`: required behavior (testable)
- `design.md`: architecture decisions and trade-offs (not line-by-line)
- `tasks.md`: dependency-aware implementation steps

## Working Rules

**Honor DP-0**: Read `dp_0_decisions`, respect confirmed constraints, don't silently expand scope. Pause on unconfirmed decisions.

### proposal.md
Must state: observed problem, what changes, in/out scope, impact areas, and proof of completion. Prefer concrete facts over empty adjectives such as “better”, “robust”, or “efficient”.

### specs/
Every requirement must be testable. Use SHALL or MUST. Every requirement must have at least one `#### Scenario:` with WHEN/THEN. Group under ADDED/MODIFIED/REMOVED Requirements headers.

### design.md
Must have: relevant facts and constraints, goals and non-goals, decisions (Choice + Rationale + Alternatives + Consequences), and risks with verification evidence. Do not invent stakeholders, migration steps, or open questions when they do not affect the decision.

### tasks.md
Must include a delivery/proof map and dependency-aware tasks. Each task names the affected path or bounded area, the observable outcome, and the evidence command. Keep RED/GREEN details, review receipts, and dispatch mechanics in the execution contract/task brief; do not inflate reader-facing tasks into five ritual substeps.

## Artifact Generation

Enter `specifying` before creating or editing planning artifacts: run `SSF state transition <change-dir> specifying` only if not already there. On resume, continue incomplete artifacts; do not self-transition. Full planning may omit specs only for explicitly unchanged behavior, and may omit design by configuration. Full cannot skip tasks: correct this configuration before generating the pack.

When DP-0 has made the scope clear, generate the configured planning pack (proposal, delta specs from `templates/spec.md`, design, and tasks) in order without pausing between individual artifacts. Validate the pack, then request one DP-2 review. Pause earlier only when the missing decision can change user-visible behavior, compatibility, security, delivery scope, or the selected design; or when artifacts state incompatible scope.

## Validation Checklist

### proposal.md
- `## Why` > 50 chars, `## What Changes`, `## Scope` (In/Out), `## Impact`, no TBD/TODO; claims name an observed problem and a completion proof

### specs/
- SHALL/MUST for required behavior, `#### Scenario:` with WHEN/THEN per requirement, grouped under delta headers, no contradictions

### design.md
- facts/constraints, goals/non-goals, `## Decisions` (≥1, with Choice+Rationale+Alternatives+Consequences), risks and verification

### tasks.md
- delivery/proof map, numbered tasks, affected paths or bounded areas, observable outcomes, no placeholders, every requirement mapped, explicit dependencies
- Must use the template checkbox format (one `- [ ]` per task on its own line); the guard enforces this format when entering execution

**If any artifact fails validation, fix before handing off to contract-builder.**

## DP-2: Artifact Review Gate

Present a concise summary of the configured artifacts. Self-check five questions once: problem, command boundary, invalidation boundary, continuation boundary, and document flow. Do not dispatch a blind-reader subagent unless the user explicitly requested delegation. Reuse approval already covering these artifacts; ask one consolidated question only for a new material decision or missing artifact approval. Do not add a separate continuation question. After approval:
```bash
SSF state set <change-dir> dp_2_result "approved: <summary>"
SSF state set <change-dir> dp_2_timestamp now
```

After DP-2 is recorded, remain in `specifying` and continue to contract-builder.

## Handoff Rule

Do not start implementation after writing planning artifacts. Once stable, validated, and DP-2 is recorded, hand off to `contract-builder`.

## Exception Handling

- **Parse failures**: Report specific file/error; don't generate from corrupted templates
- **Missing templates**: Fall back to artifact structure defined in this skill
- **User interruption**: Artifacts on disk are the recovery checkpoint; resume from first missing/incomplete one
- **Validation failure**: Fix before handoff — do not hand off broken artifacts
