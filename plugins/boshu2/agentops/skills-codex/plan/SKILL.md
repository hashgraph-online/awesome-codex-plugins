---
name: plan
description: "Run plan."
---

# $plan - Issue-Ready Decomposition

> Quick ref: turn a goal or research artifact into `.agents/plans/*.md`,
optional bd issues, dependency waves, file ownership, and validation checks.

**Execute this workflow. Do not only describe it.** Keep planning separate from
implementation. A finished plan should let `$crank`, `$implement`, or a future
Codex session execute without chat-only context.

## Inputs And Flags

Given `$plan <goal> [--auto]`:

| Flag | Purpose |
|------|---------|
| `--auto` | Skip the human approval gate for `$rpi` and other autonomous chains |
| `--fast-path` | Force the minimal 1-2 issue plan shape |
| `--deep` | Force symbol-level/deep plan detail |
| `--skip-symbol-check` | Skip symbol verification for greenfield plans |
| `--skip-audit-gate` | Skip baseline audit gate for docs-only plans |

If bd is unavailable, still write the markdown plan in `.agents/plans/`.

## Discovery Boundary

Use the [Skill Ports and Adapters](../../docs/contracts/skill-ports-and-adapters.md)
vocabulary for the boundary from Discovery into Plan:

| Boundary piece | Plan contract |
|---|---|
| Inbound port | `plan_slices` from BDD intent, bead, research artifact, or execution packet |
| Outbound ports | `persist_issue`, `verify_symbols`, `retrieve_context`, `seed_execution_packet` |
| Driving adapter | `$plan` skill invocation |
| Driven adapters | bd, `rg`, `.agents/findings`, `.agents/plans`, execution-packet writer |
| Context packet | slice plan, file dependency matrix, acceptance criteria, test levels |
| Guard adapter | stale-scope verification, symbol verification, wave-validity check |

```gherkin
Feature: Plan converts dense intent into executable slices
  Scenario: Plan consumes Discovery output
    Given Discovery provides density fields and artifact links
    When Plan receives the `plan_slices` port request
    Then each slice has acceptance criteria, write scope, test levels, and ownership
    And no slice depends on raw Discovery chat context
```

## Workflow

1. **Pre-flight stale bead scope.** If the input is a bead ID and the work is
   full-complexity, older than 7 days, or inherited from another session, run
   `ao beads verify <bead-id>` before decomposition. Do not plan against stale
   citations without revalidation.
2. **Set up artifacts.** Create `.agents/plans/` and locate prior research,
   handoffs, findings, planning rules, and relevant `.agents/` history.
3. **Load prevention context.** Prefer `.agents/planning-rules/*.md`; fall back
   to `.agents/findings/registry.jsonl`. Treat active findings as hard
   planning context. Record applied finding IDs in the plan with an
   `Applied findings:` line, even when the value is `none`.
4. **Recommend a strategic duel when warranted.** If the plan spans more than
   one execution session and has at least one contested operator-default
   decision, recommend the dueling-idea-wizards route
   (`$council --mode=debate --focus=ideas`) before decomposition. Keep it
   advisory, not mandatory. Skip it for single-session or non-contested plans.
   Evidence from the 2026-05-17 Mt Olympus run: roughly 22 min wall-clock,
   3/5 operator defaults flipped, and one already-shipped adapter bug surfaced.
5. **Explore only as needed.** If prior research does not provide enough file
   and symbol detail, inspect the codebase or dispatch a bounded explorer.
   Demand file inventory, symbol names, reuse points with `file:line`, test
   locations, and package/import relationships.
6. **Baseline audit.** Mechanically count the current state before making
   quantitative claims: files, sections, LOC, tests, fixtures, schemas, and
   any SKILL.md files near size limits. Record commands and results.
7. **Choose detail level.** Minimal for 1-2 simple issues, Standard for 3-6
   issues, Deep for 7+ issues, broad refactors, or `--deep`.
8. **Decompose into issues.** Each issue needs title, file ownership,
   dependencies, acceptance criteria, test levels, and at least one mechanical
   conformance check (`files_exist`, `content_check`, `command`, `tests`, or
   `lint`). **Every bead MUST also carry an embedded `## Scenarios` Gherkin
   block (Given/When/Then) — by default, without being asked.** Free-text-only
   acceptance is invalid (AGENTS.md); promote any free text to scenarios before
   creating the bead. The `## Scenarios` block is the behavior layer and sits
   above the `acceptance_criteria` YAML (the machine-checkable layer); they are
   complementary, never substitutes. One scenario per distinct Given/When/Then
   behavior. Non-trivial plans and bead bodies should include the `hexagon:`
   boundary block: inbound port, bounded context, adapters, context packet, and
   done state.
9. **Compute waves.** Group independent issues by dependency. Serialize or
   merge same-file writes. Include generated artifacts, docs, schemas, fixtures,
   Codex companions, manifests, and hash markers in ownership.
   Generated Artifact Companion Scope is mandatory: list every touched file,
   including tests, docs, schemas, fixtures, runtime copies, parity manifests, hash markers,
   and generated Codex artifacts. If skill behavior or runtime UX
   changes, include `bash scripts/refresh-codex-artifacts.sh --scope worktree`
   in verification.
10. **Write the plan.** Use `.agents/plans/YYYY-MM-DD-<goal-slug>.md` and the
   template in [references/plan-document-template.md](references/plan-document-template.md).
11. **Create tracking tasks.** Prefer bd issues with validation blocks and
    dependency edges. If bd is missing, leave the markdown plan as the durable
    handoff.
12. **Approval gate.** Skip only with `--auto`; otherwise ask whether to
    proceed, revise, or return to research.

## Required Plan Sections

Every non-trivial plan must include:

- context and applied findings
- files to modify
- boundaries and non-goals
- baseline audit evidence
- issue list with acceptance criteria and validation
- execution order/waves
- file dependency matrix
- file-conflict matrix
- cross-wave shared file registry when applicable
- planning rules compliance
- verification commands
- next steps

Read [references/plan-document-template.md](references/plan-document-template.md)
for the canonical shape.

## Codex Guardrails

- Keep WHAT and HOW distinct; do not implement while planning.
- Prefer concrete file paths, symbol names, and validation commands over long
  narrative.
- Treat Codex companion files as part of the same issue when skill behavior or
  runtime UX changes.
- If a plan changes a schema with `additionalProperties: false`, put schema work
  before consumers in an earlier wave.
- If an acceptance criterion cannot be checked mechanically, mark it
  underspecified before handing it to execution.

## Examples

**User says:** `$plan "add rate limiting"`
Produce a plan with file inventory, issues, validation, and wave order.

**User says:** `$plan --auto ".agents/research/auth.md"`
Use the research as input, write the plan, create tracking tasks when possible,
and skip the approval gate.

Read [references/examples.md](references/examples.md) for full examples.

## Troubleshooting

| Problem | Response |
|---------|----------|
| bd is missing | Write the markdown plan and note that issue creation was skipped |
| Prior research is thin | Explore enough to produce file and symbol evidence |
| Same file appears in parallel issues | Serialize or merge those issues before handoff |
| Baseline audit is missing | Mark the plan incomplete unless `--skip-audit-gate` is justified |

## Reference Documents

- [references/complexity-estimation.md](references/complexity-estimation.md)
- [references/decomposition.md](references/decomposition.md)
- [references/detail-templates.md](references/detail-templates.md)
- [references/examples.md](references/examples.md)
- [references/implementation-detail.md](references/implementation-detail.md)
- [references/plan-document-template.md](references/plan-document-template.md)
- [references/plan-mutations.md](references/plan-mutations.md)
- [references/plan-to-beads-workflow.md](references/plan-to-beads-workflow.md)
- [references/planning-rules.md](references/planning-rules.md)
- [references/pre-decomposition.md](references/pre-decomposition.md)
- [references/sdd-patterns.md](references/sdd-patterns.md)
- [references/task-creation.md](references/task-creation.md)
- [references/templates.md](references/templates.md)
- [references/wave-matrices.md](references/wave-matrices.md)
