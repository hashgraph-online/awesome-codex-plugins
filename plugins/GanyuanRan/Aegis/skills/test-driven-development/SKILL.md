---
name: test-driven-development
description: "Use when the user explicitly requests strict or test-first TDD, or when the current conversation already contains an explicit `TDD Route: strict` decision from another Aegis workflow."
---

# Execute

- **False-positive entry on a native-direct-skill host?** Exit immediately unless
  the user explicitly requested TDD or the conversation records `TDD Route: strict`.
  Return to the selecting workflow or fast path with proportional verification.
- Under `strict`, validate preflight and Change Necessity before production
  edits. No production code without an observed failing behavior test first.
- RED (test and observe failure) -> GREEN (minimum owner repair and observe pass)
  -> REFACTOR (clean up while green). Apply Regression Scope before closeout.
- GREEN proves only the expressed behavior slice, not parent-task acceptance,
  business-value completion or final completion. Use `verification-before-completion`.

## Entry Boundary

Enter only for an explicit strict TDD/test-first/RED / GREEN / REFACTOR request
or a recorded `TDD Route: strict`. Native-direct-skill hosts must not infer
entry from generic risky-code wording. Consume the selected route; a missing
or invalid automatic decision returns to its selecting workflow.

Once strict entry is justified, it may cover features, bug fixes, refactoring,
behavior/logic, interface/data contracts, shared modules and core logic.
Exceptions (ask your human partner): throwaway prototypes, generated code,
config files, pure docs cleanup, read-only diagnosis and comment-only changes.

## TDD Mode and Route

TDD Mode defaults to `off`, disabling automatic TDD, not completion verification.
In `auto`, the selecting workflow chooses strict/light/skipped by task risk.

Before source edits, decide:

```text
Aegis Visibility:
- Why this TDD route is strict, light, or skipped:
- What RED/GREEN proves:
- What still needs verification:

TDD Route:
- Mode: auto | off
- Decision: strict | light | skipped
- Strict authority: explicit user/project request | recorded auto decision | not applicable
- Test posture: diagnostic reproduction | post-change regression | strict RED test
- Reason:
- Verification:
```

In `auto`, use `strict` for behavior, bugfix, contract, shared/core, producer /
consumer, persistence, permission, migration, or meaningful regression risk.
Use `light` for tiny low-risk edits with an obvious readback or command check.
Use `skipped` for read-only, docs-only, generated, throwaway, comment-only, or
environment-bound work where TDD does not fit.

In `off`, do not automatically require TDD, create a strict route, or infer one
from risk alone. Explicit user/project TDD requests still apply; risky work may
still need regression coverage and `verification-before-completion` before any
completion claim.
For plan or execution review, `Mode: off / Decision: skipped` is the normal
record unless an explicit user/project strict request overrides it. That record
does not load this skill or turn a diagnostic reproduction into RED. An
approved plan does not supply strict authority by itself.
If this skill was loaded anyway without an explicit TDD request or a visible
`TDD Route: strict` marker, exit instead of improvising an automatic strict
route from risk words alone.

Keep `Aegis Visibility` task-specific: explain the route decision and the
regression boundary, not a generic claim that TDD was used.

## Preflight Gate

TDD is the implementation discipline for an approved behavior or atomic task.
It is not a substitute for task routing, product clarification, or planning.

Before writing tests or production code, stop and route to brainstorming or
writing-plans if the current request has any medium- or high-complexity signal:

- multiple files, modules, pages, screens, services, or owners
- user-visible flows such as navigation, onboarding, checkout, lifecycle, or
  recovery paths
- state transitions, routing rules, API or data contracts, compatibility
  boundaries, migrations, permissions, or persistence
- more than one acceptance path or manual/visual verification requirement
- unclear product behavior, competing constraints, or long-running execution

For these tasks, require a baseline read-set, plan, and atomic tasks before TDD.
High-complexity or ambiguous tasks also need a spec/design review before
planning. Only proceed directly with TDD for low-complexity work whose intent,
owner, compatibility boundary, verification path, and slice goal / success
evidence are already clear.

## Change Necessity

Before strict RED/GREEN enters production edits, expose why code needs to
change: user-visible need, no-change/non-code alternative, why it is insufficient,
and the minimum owner/file boundary. This is behavior-triggered, not prompt-triggered:
any new source-code path, including a tiny helper, guard, branch, fallback,
adapter or owner, needs the decision before RED/GREEN normalizes it as work.
Keep this natural; it creates no new artifact or hot-path entry requirement.

- `no-change`: do not write tests or production code for a non-change.
- `docs/config-only`: route to that narrower surface and verify it.
- `needs-clarification`: pause before RED/GREEN.
- `code-change`: carry the minimum boundary into TDD Route, RED and regression.

## Complexity Budget

Before strict TDD on non-trivial work, record the planned complexity budget so
RED/GREEN does not silently normalize a wrong or overloaded owner.

For the Complexity Budget, state artifact class, current pressure, projected
post-change pressure and planned governance in the existing task record.

Use `using-aegis/references/complexity-governance.md` for shared artifact
classes, pressure signals, and the meaning of planned governance.

## Pre-Edit Complexity Check

Before production code edits, check whether the intended source edit would add
logic to an overloaded or wrong owner. Tiny edits can keep this to one line.

Use `using-aegis/references/complexity-governance.md` for shared pressure
signals and the meaning of `over-budget`.

Keep the Pre-Edit Complexity Check proportional: target file, pressure signal,
owner fit, safer boundary and decision. For a pressured owner, include the
Pre-Edit Owner-Fit Decision and classify intent as `wiring-only`,
`move-out / extract-first`, `local-fix-without-new-responsibility`,
`new-responsibility`, or `emergency / compatibility patch`.
The decision is `edit-in-place | extract helper | add owner file | split task |
pause for plan update`.

If the decision is `pause for plan update`, stop TDD and return to
`writing-plans` or `brainstorming` with the evidence.

If the predicted result is that this slice would push a maintained artifact
over budget and the slice does not also govern that overrun, do not continue
with RED/GREEN as if the task were safely scoped. Pause and update the plan.

When the target edit file is over-budget or mixed-purpose, classify edit intent
before production source edits. `new-responsibility` must not be added in place
by default. `wiring-only`, `move-out / extract-first`, and
`local-fix-without-new-responsibility` may proceed only when they do not add a
new responsibility and the verification boundary is clear. `emergency /
compatibility patch` requires residual risk and a retirement trigger.

## Conditional Reference Reads

The main skill is sufficient for an ordinary strict cycle. Do not load all
references by default. Select only the named section when its evidence trigger
applies; leave unrelated examples and workspace instructions unread.

| Trigger | Reference and exact section |
| --- | --- |
| Choosing observable assertions is unclear, or callback/mock counts can hide an incorrect result | `examples.md` — `## Behavior Assertions` |
| The minimum GREEN implementation is unclear or proposed options exceed tested behavior | `examples.md` — `## Minimal GREEN` |
| A concrete worked RED/GREEN/refactor sequence is requested or needed to understand the cycle | `examples.md` — `## Worked Bug Fix` |
| A medium/high task needs authorized project records and workspace initialization | `long-task-continuation/durable-work-guidance.md` — `## Create A Durable Work Record`; use its initialization command only when initializing, and its new-work command only for a needed work record |
| That task needs the work-record file layout | `long-task-continuation/durable-work-guidance.md` — `## Required Artifact Layout` |

Resolve the shared reference beside the host-discovered `long-task-continuation`
SKILL.md, preserving any installed directory prefix; do not assume an unprefixed
sibling directory. If that reference is unavailable, report the workspace-support
gap rather than inventing helper commands.

Use configured Aegis workspace support lazily through the installed
`<aegis-workspace-helper>`. Do not create records merely because TDD is active.
Do not promote reusable project facts, decisions, specs or plans into workspace
directories unless the workflow needs them and no existing project authority
already owns them. Helper commands and layout have one owner in long-task
continuation; TDD retains its preflight and production-edit boundaries.

## Red-Green-Refactor

### RED - Write Failing Test

State: input | output | boundary | acceptance criteria. Check existing test coverage first. Write one minimal test showing what should happen.
A minimal test anchors the next behavior slice; it does not by itself define
whole-task completeness unless the parent acceptance is already fully pinned.

**Requirements:**
- One behavior
- Clear name
- Real code (no mocks unless unavoidable)
- If a new feature changes user-observable behavior, prefer one minimal
  end-to-end or integration test for the main path before narrower unit tests
- For user-visible work, cover the main journey and the highest-risk experience
  or operational floor before treating unit tests as sufficient
- Add unit tests for core rules, boundary conditions, and error branches

### Verify RED - Watch It Fail

**MANDATORY. Never skip.**

```bash
npm test path/to/test.test.ts
```

Confirm:
- Test fails (not errors)
- Failure message is expected
- Fails because feature missing (not typos)

**Test passes before production edits?** Inspect the reproduction and assertions.
If they miss the requested behavior, correct the test. If the behavior already
exists, reassess Change Necessity; keep useful regression evidence without
claiming a RED/GREEN cycle. Do not break or delete existing code to force RED.

**Test errors?** Fix error, re-run until it fails correctly.

### GREEN - Minimal Code

Write simplest code to pass the test.

Don't add features, refactor other code, or "improve" beyond the test.

Fix the real owner of the behavior. Do not add a new fallback, adapter, or
branch unless the debugging or design workflow identifies why it is necessary
and what old path retires.

### Verify GREEN - Watch It Pass

**MANDATORY.**

```bash
npm test path/to/test.test.ts
```

Confirm:
- Test passes
- Other tests still pass
- Output pristine (no errors, warnings)

**Test fails?** Fix code, not test.

**Other tests fail?** Fix now.

### REFACTOR - Clean Up

After green only:
- Remove duplication
- Improve names
- Extract helpers

Keep tests green. Don't add behavior.

### Repeat

Next failing test for next feature.

## Regression Scope

At minimum, run the target test you just changed or added. Broaden regression
based on impact:

- Shared module change -> related module tests
- Interface or data contract change -> producer and consumer tests
- Cross-module behavior change -> integration or end-to-end path
- Core logic refactor -> old behavior regression tests plus new behavior tests
- Ripple Signal Triage fired -> producer+consumer or real user path that proves
  the downstream effect remains bounded

If the current environment cannot run automated tests, state the blocker and provide reproducible manual verification steps.

## Strict-Route Red Flags - STOP and Diagnose

These red flags apply only after this skill has validly entered under
`TDD Route: strict`. Do not project them onto debugging or regression work
whose route is `light` or `skipped`.

- Code before test
- Test after implementation
- Test passes immediately without an explanation of existing behavior
- Can't explain why test failed
- Tests added "later"
- Rationalizing "just this once"
- "I already manually tested it"
- "Tests after achieve the same purpose"
- "It's about spirit not ritual"
- "Keep as reference" or "adapt existing code"
- "Already spent X hours, deleting is wasteful"
- "TDD is dogmatic, I'm being pragmatic"
- "This is different because..."

Stop and establish which case applies. If you wrote task-owned production code
before the required failing test, remove only that premature implementation
and restart from the behavior test. Preserve pre-existing code and user edits;
if changes are interleaved, isolate ownership before recovery. A test that
passes before any production edit needs the test/Change Necessity diagnosis
above, not code deletion. Missing evidence alone does not authorize a reset.

## Strict-Route Verification Checklist

- [ ] Defined input, output, boundaries, compatibility, acceptance criteria
- [ ] Each new behavior has a test observed failing before implementation;
      helpers extracted during GREEN refactoring may use that existing test
- [ ] All tests pass, output pristine
- [ ] Regression: shared/contract/core changes ran related tests
- [ ] Ripple signal hit: downstream or real user path covered
- [ ] If automation blocked → blocker + manual steps documented
- [ ] GREEN treated as local behavior proof only, not final completion
- [ ] If `TaskIntentDraft`, parent plan/spec, or `Slice Card` exists, covered and uncovered scope are explicit before any done claim

Can't check all applicable boxes? Diagnose the gap before claiming strict-route completion.

## Exploration and Emergency Exceptions

Exploratory spikes are allowed only as throwaway learning. When the spike ends,
convert confirmed behavior into tests before formal implementation.

Emergency hotfixes may prioritize the smallest safe repair when delay is more
dangerous than incomplete TDD. Record the reason, keep the change narrow, and
add the missing regression test in the same slice or the next nearest slice.

## When Stuck

Don't know how to test → write wished-for API first. Test too complicated → simplify design. Must mock everything → reduce coupling.

## Debugging Integration

Bug found? Start with `systematic-debugging`: reproduce, trace the owner, and
choose the smallest proof that supports the diagnosis. Under recorded
`TDD Route: strict`, the reproduction becomes the required failing test before
production edits. With `TDD Mode: off` and no strict route, use diagnostic
reproduction and targeted post-change regression as fit the repair; do not
start RED / GREEN by inference.
