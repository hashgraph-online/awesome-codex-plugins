---
name: dev-plan
description: 'Create a concrete implementation plan from a spec or clearly scoped request before coding. Use for implementation-planning requests such as 出个 plan, 技术实施方案, plan this, or consensus plan. Ground steps in the repository and scale tradeoff analysis and independent review to risk. Clarify material requirement gaps when needed; do not force an intake workflow for already clear scope. Supports --quick and --deliberate.'
---

# Dev Plan

Produce an implementable, verifiable plan within the user's stated scope. Planning does not authorize implementation. Read [references/dev-baseline.md](references/dev-baseline.md).

## Establish the contract

Read the supplied spec or related `.claude/artifacts/designs/<feature>.md`, relevant code, existing tests, and any accepted ADR. Preserve source links, acceptance criterion identifiers, scope exclusions, assumptions, and open questions. A clear request is sufficient without a separate spec artifact; summarize its requirements in the plan.

If a missing requirement materially changes the solution, ask for that decision or explain the blocked portion. Use `dev-grill-docs` when the task actually requires broader requirement alignment and that skill is available. Continue planning independent parts. Do not require a new intake invocation merely because a spec file is absent. A `STUCK` source must have its blocking questions resolved before planning dependent implementation.

Inspect actual definitions and call paths before naming modification targets. New paths must be labeled proposed. Cite existing paths and symbols; use line numbers only when verified and helpful. Do not manufacture precision or require a percentage of steps to contain line numbers.

## Scale planning to risk

| Mode | Depth |
|---|---|
| `--quick` | Compact requirements, steps, meaningful risks, and validation for a well-understood change |
| Default | Repository-grounded steps, real design decisions, dependencies, and review proportional to impact |
| `--deliberate` | Add concrete failure scenarios, rollout and recovery considerations, and validation across relevant system boundaries |

Honor the requested depth while still surfacing material risks. A small diff involving destructive operations, authorization, payments, migration, sensitive data, or public compatibility may need deeper treatment. Explain a necessary depth increase in one sentence; do not impose every test layer or a fixed number of scenarios on every task.

## Draft the plan

- Choose the smallest coherent approach consistent with existing architecture and accepted requirements.
- Compare alternatives only when there is a real choice. One established approach is sufficient; briefly explain any important rejected option without inventing a second candidate.
- Organize implementation steps by dependencies, observable behavior, and ownership. Include affected modules, data or API contracts, failure handling, and integration points where relevant.
- Map acceptance criteria to concrete checks. Distinguish automated proof from staging, device, browser, or production evidence that needs a separate environment.
- For consequential design decisions, record a concise ADR within the plan: decision, drivers, alternatives, rationale, and consequences. Follow existing project conventions; trivial plans need no ceremonial ADR.
- For risky changes, describe credible failures, prevention or detection, rollout ordering, rollback or recovery limits, and relevant compatibility windows. Do not assume a destructive migration can be rolled back without data loss.
- Note workspace constraints when they affect implementation: Git root, branch, dirty work, or concurrent ownership. Preserve the selected checkout; isolation is an engineering choice, not a mandatory approval stop.

For `--deliberate` or explicit RALPLAN-DR/consensus requests, retain recognizable principles, decision drivers, alternatives, architecture challenge, review outcome, and decision record. Apply them to real tradeoffs. Do not fabricate disagreement or reservations to fill the format.

## Review and revise

Separate authoring from review. For substantial, risky, or explicitly consensus plans, use an independent reviewer when delegation is available and authorized. Give them the source contract, draft, relevant code access, and a bounded review question. An architecture reviewer may challenge a consequential design; a second critic is useful only when it adds a distinct check.

Review for requirement coverage, correctness of repository assumptions, sequencing, compatibility, credible mitigations, and executable verification. Findings need evidence and a concrete implication. No findings is a valid outcome; a quota of objections creates noise.

In-context role switching is a self-check, not independent review or consensus. When independent review is unavailable, disclose that limitation and leave the plan `DRAFT` unless the user has explicitly accepted it. Do not pretend separate Planner / Architect / Critic labels establish approval.

Revise concrete findings, then review the affected changes. Stop when concerns are resolved or further progress needs unavailable evidence or a user decision. For an explicit consensus workflow, use at most three review rounds unless the user sets a different budget; preserve unresolved issues as `BELOW_CONSENSUS_THRESHOLD` at that limit. Do not escalate to new architecture solely because a round limit was reached.

## Artifact and status

Default path: `.claude/artifacts/plans/<feature>.md` in the user's project. Use the user's specified path or chat-only output when requested. Reuse the source feature slug and preserve unrelated artifact content.

```markdown
# <feature> Implementation Plan

> Status: DRAFT | APPROVED | REVISE | REJECT | BELOW_CONSENSUS_THRESHOLD
> Source: <spec path or user request>
> Mode: --quick | default | --deliberate
> Last updated: <YYYY-MM-DD>

## Requirements summary
<Scope and constraints>

## Acceptance criteria
<Preserved AC identifiers and observable outcomes>

## Implementation steps
<Ordered changes with concrete repository targets and dependencies>

## Risks & mitigations
<Material risks only>

## Verification steps
<Checks mapped to behavior, plus environment prerequisites>

## Open questions
<Only unresolved decisions, with affected steps; omit if none>

## Review trail
<Reviewer or user acceptance, actual findings and resolution, or self-check limitation>
```

Add ADR, workspace setup, pre-mortem, expanded test plan, and ownership sections only when relevant or requested. `APPROVED` means an independent reviewer found no blocking issue or the user explicitly accepted the current plan; record which. It does not mean code is implemented, tests passed, or implementation is authorized. A changed substantive plan needs its approval reassessed. A quick self-checked draft must not claim Critic approval.

## Handoff

Return the plan path or requested inline plan, chosen approach, material unresolved issues, and review status. Respect plan-only requests. If a broader instruction already authorizes implementation, continue after the plan is usable within that authorization; do not require the user to invoke another skill as a procedural checkpoint. See [examples.md](examples.md) for depth and approval examples.

## SDD Contract

The plan links accepted intent to implementation targets, decisions, risks, ownership, and verification. Downstream work should preserve AC identifiers and report material drift. Update the affected contract when a behavior or decision changes; do not treat all implementation details as immutable or silently implement unresolved product choices.

## Multi-Agent Profile

Recommended agent_type: default

When supported and authorized, delegate bounded exploration or an independent plan review. Keep one owner for the final artifact and user-facing questions; reviewers stay read-only. Workers need source artifact, scope, exclusions, relevant code, and expected evidence. In the source repository, `docs/multi-agent-policy.md` provides optional team guidance; it is not required by standalone installations.
