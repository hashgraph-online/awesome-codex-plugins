---
name: writing-plans
description: "Use when you have an approved spec or written requirements for a multi-step task that needs a durable plan document before touching code. Small, single-owner, or fast-path tasks do not need this skill."
---

<EXPLICIT-MODE-GATE>
If activation mode is explicit (`~/.config/aegis/config.toml` has
`activation_mode = "explicit"`, or `AEGIS_ACTIVATION_MODE=explicit` is visible
in the environment) and the current user request did not explicitly invoke
Aegis or this skill by name, exit back to the fast path: answer concisely
without this workflow's checklist, ceremony, or document requirements. If the
user explicitly named Aegis or this skill, proceed normally.
</EXPLICIT-MODE-GATE>

# Execute

→ Existing parent plan/spec and a tiny execution slice? → **Use Planless Slice Lane.**
→ Mechanical or bounded change with no durable boundary (no new owner,
  contract, schema, public API, migration, or compat surface)? → **Use
  Planless Slice Lane without a parent document.**
→ Approved spec/requirements for a new workstream or an escalation trigger? →
  **Write an implementation plan for an engineer with no prior task context.**

For a durable plan: confirm scope and acceptance, map current owners/files,
record the TDD route, decompose into executable tasks, define verification and
retirement, self-review, save, then select the execution route. Proceed unless
a real authorization or safety boundary requires the user.

Escalate from Planless Slice Lane when the work adds a new owner, contract,
schema, public API, architecture boundary, migration, persistence,
security/permission, distribution/release surface, or an unclear verification
boundary.

# Writing Plans

This skill turns approved requirements into a bounded, executable plan. The
plan must answer: what changes, why code is necessary, which existing owner and
files change, what stays compatible, what verifies the result, what risk
remains, and what old path is retired or deliberately retained. A plan is
method-pack guidance; it cannot grant authoritative completion.

## TDD Route Guard

Before task decomposition, record `TDD Route` with mode (`off | auto`), decision
(`strict | light | skipped`), authority, test posture, reason, and verification.

Strict RED / GREEN steps belong only to an explicit user/project TDD request or
`TDD Route: strict`. In `off`, use `skipped` unless explicit strict authority
overrides it. An approved plan or a risk label alone is not strict authority.

In `auto`, select `strict` for behavior, bugfix, shared/core, contract,
persistence, permission, migration, producer/consumer, or meaningful
regression signals. Select `light` only when the work is tiny, low-risk,
single-owner, has no behavior change or strict signal, and has an obvious
focused check. Absence of an explicit user TDD request is never evidence for
`light`; the auto decision itself must be recorded.

If risk remains unknown, return to requirements, debugging, or plan review
before task decomposition; do not infer a TDD route from uncertainty.

Only a `strict` decision with stated authority may prescribe failing-test,
RED, GREEN, and REFACTOR steps. Otherwise plan the minimum change plus
diagnostic reproduction or post-change regression. A missing auto decision
returns to route selection before implementation tasks.

## Entry And Artifact Choice

**Announce at start:** on the plan-writing route, say that this skill is
creating the implementation plan. On `Planless Slice Lane`, announce the lane instead and do not claim a plan is being created.

**Execution context:** Reuse the current branch/workspace by default. A branch
needs independent history; a worktree needs concurrent checkout, blocking
unrelated dirty state, or explicit user/repository authority.

**Input:** approved requirements, a Spec Brief, or a Design Spec.

**Default plan path:** `docs/aegis/plans/YYYY-MM-DD-<feature-name>.md`. Plans do
not go in `work/`; user and repository authority override the default.

Exception: use `Planless Slice Lane` when an existing parent plan/spec already
owns the current tiny execution slice, or when the change is mechanical or
bounded and needs no parent document. Do not save a new plan. Emit a compact
`Slice Card`:

```text
Slice Card:
- Goal:
- Parent plan/spec:
- Files:
- Boundary:
- Verification:
- Stop:
```

On the no-parent branch, `Parent plan/spec:` is `none — direct bounded request`.

## Aegis Project Workspace

Workspace creation is lazy and follows project authority. The Aegis Method
Pack repository must not create or ship a live `docs/aegis/` workspace. When a
durable plan must initialize or update another project's workspace, read the
workspace section of `expanded-planning-guidance.md`. It owns the
`<aegis-workspace-helper>` and `INDEX.md` command detail, not the decision to
create a plan.

## Default Plan Surface

Compact output contract: express these as natural plan content, not a stack of
cards: `Aegis Visibility`, approved scope and plan basis, required baseline
refs, files/owners, compatibility boundary, `Change Necessity`, TDD route,
tasks, verification, risks, and retirement. Keep conditional structures silent unless their trigger below fires.

`Aegis Visibility` is normally one sentence explaining which owner, contract,
retirement, compatibility, or verification pressure makes a durable plan
useful. Structured trace belongs only to audit, debug, release, long-task
review, or explicit request.

Before tasks, perform a `Requirement Ready Check`: identify the approved source,
scope, scenarios, and acceptance evidence. If any decision-changing item is
missing, do not create implementation tasks; return the smallest gap to the
requirement/spec owner.

Perform `Change Necessity` before any non-trivial source edit or any new source-code path. This is behavior-triggered, not prompt-triggered. State
naturally why no-change/docs/config is insufficient and name the minimum code
boundary. A tiny helper, guard, branch, fallback, adapter, or owner is not
exempt. A `no-change`, `docs/config-only`, or `needs-clarification` result
narrows or stops the code plan.

Run `Ripple Signal Triage` before tasks when the change touches shared/core or
cross-module behavior; a public API, schema, contract, compatibility,
persistence, cache, export/readback, fallback, adapter, duplicate/legacy owner,
retirement path, or both producer and consumer. If no signal fires, add no
output. If one fires, identify the canonical owner and affected downstream consumers,
state source-of-truth/contract/fallback/retirement risk, and carry expanded verification
into the relevant task. A required owner/public-contract/source-of-truth change,
retaining two owners, or adding a fallback, adapter, or compatibility branch
returns to design or requires explicit prior alignment before implementation.

Run a compact `Plan Pressure Test` before task decomposition: test owner / contract / retirement fit, higher-level architecture path, verification scope,
and task executability. It may proceed, revise the plan, or return to design;
it is not an approval authority.

## Conditional Detailed Guidance

Read only the trigger-matched section of `expanded-planning-guidance.md`:

- `## Baseline And Requirement Detail` when specific baseline acknowledgement
  needs structure or requirement readiness is incomplete/disputed;
- `## New-Surface And Architecture Detail` when a new surface or new owner needs
  `Existence Check`, `AEGIS_MINIMALITY_REFERENCE`, `Architecture Integrity Lens`,
  or `first-principles-review` detail before task decomposition;
- `## Complexity Detail` when material file-size, mixed-owner, add-in-place,
  adapter, fallback, or shared-core pressure appears;
- `## Execution Readiness Detail` for a long-running, handoff-prone,
  subagent-driven, high-risk architecture/contract/compatibility/retirement handoff;
- `## Workspace Save Detail` only when saving requires workspace initialization
  or `INDEX.md` updates;
- `## Execution Route Detail` only when route evidence needs a structured
  handoff; and
- `## Expanded Plan Review` only for an independent high-risk or handoff-heavy
  review.

The direct triggers cover baseline readiness, new surface or new owner,
complexity pressure, workspace persistence, and execution handoff. The
reference supplies detail only. This main file owns routing, plan versus
Planless selection, task blocking, and execution handoff.

For a new surface, use `Existence Check` and
`docs/current/AEGIS_MINIMALITY_REFERENCE.md` before tasks. Reuse an existing
owner when it is sufficient. If owner, contract, responsibility overlap,
higher-level simplification, fallback, or retirement remains risky, use the
`Architecture Integrity Lens` and `first-principles-review` before task
decomposition.

For maintained source, screen file shape, owner fit, add-in-place risk, and a
better boundary. With no pressure signal, a compact edit-in-place decision is
enough. When pressure exists, load the expanded `Plan-Time Complexity Check`
and `Complexity Budget`. An over-budget result must change the task boundary,
add governance work, or stop for follow-up.

For an ordinary medium/high handoff, state Intent Lock, Scope Fence, Baseline Lock, tests, and drift stop naturally. Load the expanded `Execution Readiness View` only for the auditable handoff triggers above. Neither form is a
`GateDecision`, `PolicySnapshot`, approval gate, or completion authority.

If the plan must choose among deleting an old internal path, retaining a proven
external compatibility boundary, or stopping for persistent-state
confirmation, compose `anti-entropy-governance`. It does not authorize
destructive execution.

Preserve approved ADR signal preservation, source refs, alternatives,
compatibility, and baseline-sync questions for completion; do not create
accepted architecture memory from an unexecuted plan.

## Planless Slice Lane

Use `Planless Slice Lane` before writing or saving a plan when one of these
entry conditions holds:

- a parent spec or parent plan already defines the workstream, and the current
  request is executing or refining one bounded task from that parent
- the change is mechanical or bounded and needs no parent document (the
  no-parent branch under `# Execute`)

and both of these are true:

- no new owner, contract, schema, public API, architecture boundary, migration,
  persistence, security/permission, distribution/release surface, or unclear
  verification boundary appears
- the slice can be described by a `Slice Card`

The lane preserves long-task continuity without turning execution bookkeeping
into durable planning artifacts. A parent scope or acceptance mismatch returns
to the parent plan/spec instead of spawning a micro-plan.

## Plan And Task Quality

Map files before tasks. Follow existing ownership and naming. For non-trivial
plans, passively use relevant current terms from `CONTEXT-MAP.md` or `CONTEXT.md`;
route a real semantic conflict to `establishing-project-context`.

Every durable plan starts with Goal, Architecture, Tech Stack,
Baseline/Authority Refs, Compatibility Boundary, TDD Route, and Verification.
Then define small, ordered tasks with exact files, purpose, minimum necessary
change, compatibility impact, and commands/outcomes that prove the task.
Include code excerpts only when a signature, contract, or transformation would
otherwise remain ambiguous; do not duplicate the implementation inside the
plan.

For bug fixes, refactors, contract changes, or governance cleanup, keep Repair
Track and Retirement Track explicit in the affected task. A retained old owner
or fallback needs a reason and retirement trigger.

Self-review once for approved-scope coverage, placeholders, owner/type
consistency, minimum change boundary, compatibility, exact verification,
conditional trigger handling, and retirement. Fix defects inline. Tasks are
execution units, not Git history units: the coordinator captures
`TaskStartSnapshot` and creates one scoped commit only after the whole Task is
reviewed and freshly verified.

## Execution Handoff

The agent owns the execution-route decision. Select `subagent-driven` only for
genuinely independent tasks with bounded ownership when coordination pays for
it; otherwise select `inline`. Unavailable subagents falls back to inline execution. A dirty workspace alone does not select either route.

Ask the user only for unresolved authorization, privacy, paid-resource,
external-action, irreversible-action, scope, acceptance, or workspace-ownership
boundaries. Otherwise proceed immediately. State the decision, evidence,
fallback, and `User confirmation required: no | yes — <boundary>` compactly;
load the reference only when the full `Execution Route` schema is useful.

For `subagent-driven`, use `aegis:subagent-driven-development`. For `inline`,
use `aegis:executing-plans`.
