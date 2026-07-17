---
name: spec-writer
description: Create or refine spec-superflow planning artifacts. Invoke when the change is understood well enough to write proposal.md, specs/, design.md, and tasks.md.
---

# Spec Writer

Create or refine planning artifacts when the change has moved beyond exploration.

## Required Inputs

Read `.spec-superflow.yaml` (especially `dp_0_decisions`, `dp_0_confirmed`) and any existing planning artifacts. If `dp_0_confirmed` is not `true`, stop and route back to `workflow-start` for DP-0.

## Config Check

Run: `npx --yes --package spec-superflow@0.10.0 ssf runtime config --get artifacts.order` — generate in configured order (default: proposal → specs → design → tasks). Run with `artifacts.skip` — skip any listed artifacts.

## Artifact Roles

- `proposal.md`: why and scope
- `specs/`: required behavior (testable)
- `design.md`: architecture decisions and trade-offs (not line-by-line)
- `tasks.md`: dependency-aware implementation steps

## Working Rules

**Honor DP-0**: Read `dp_0_decisions`, respect confirmed constraints, don't silently expand scope. Pause on unconfirmed decisions.

### proposal.md
Must state: problem, what changes, capabilities affected, impact areas.

### specs/
Every requirement must be testable. Use SHALL or MUST. Every requirement must have at least one `#### Scenario:` with WHEN/THEN. Group under ADDED/MODIFIED/REMOVED Requirements headers.

### design.md
Must have: Context (current state, constraints, stakeholders), Goals, Decisions (Choice + Rationale + Alternatives considered), Risks And Trade-Offs.

### tasks.md
Must include:
- **File Structure**: all files with one-sentence responsibility (Create/Modify)
- **Interfaces**: cross-batch Consumes/Produces with exact types
- **Per-task**: exact file paths, expanded TDD phases (5 steps), Interfaces block
- **Granularity**: each step 2-5 min, atomic
- **Zero placeholders**: no TBD, TODO, "figure out", "add appropriate"
- **Dependency ordering**: depends only on prior tasks, explicit "Depends on: Batch N"

## Artifact Generation

Generate one at a time. Confirm each before next. This prevents scope drift — if proposal has errors, downstream artifacts are wrong.

1. `proposal.md` → present summary → wait for confirm
2. `specs/` → present requirement list → wait for confirm
3. `design.md` → present key decisions → wait for confirm
4. `tasks.md` → present batch breakdown → wait for confirm

## Validation Checklist

### proposal.md
- `## Why` > 50 chars, `## What Changes`, `## Scope` (In/Out), `## Impact`, `## Capabilities`, no TBD/TODO

### specs/
- SHALL/MUST for required behavior, `#### Scenario:` with WHEN/THEN per requirement, grouped under delta headers, no contradictions

### design.md
- `## Context`, `## Goals`, `## Decisions` (≥1, with Choice+Rationale+Alternatives), `## Risks And Trade-Offs`

### tasks.md
- `## File Structure`, `## Interfaces`, numbered tasks, exact file paths, TDD phases, ≤5 min steps, no placeholders, every requirement mapped, explicit dependencies

**If any artifact fails validation, fix before handing off to contract-builder.**

## DP-2: Artifact Review Gate

Present summary of all 4 artifacts (2-3 sentences each). Ask user for adjustments. After approval:
```bash
npx --yes --package spec-superflow@0.10.0 ssf state set <change-dir> dp_2_result "approved: <summary>"
npx --yes --package spec-superflow@0.10.0 ssf state set <change-dir> dp_2_timestamp $(date -u +%Y-%m-%dT%H:%M:%SZ)
```

## Handoff Rule

Do not start implementation after writing planning artifacts. Once stable, validated, and DP-2 is recorded, hand off to `contract-builder`.

## Exception Handling

- **Parse failures**: Report specific file/error; don't generate from corrupted templates
- **Missing templates**: Fall back to artifact structure defined in this skill
- **User interruption**: Artifacts on disk are the recovery checkpoint; resume from first missing/incomplete one
- **Validation failure**: Fix before handoff — do not hand off broken artifacts
