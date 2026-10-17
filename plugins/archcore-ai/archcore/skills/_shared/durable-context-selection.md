# Durable Context Selection — Which Claims of a Change Get a Document Owner

Plugin runtime asset. Loaded by the `review` skill on a branch review: inside
`closeout.capture` when a `plan` matched (`skills/_shared/tracks/closeout.md`),
and in step 3 of `skills/review/SKILL.md` when no plan matched. One procedure
serves both paths. Interview mechanics and the question ceiling:
`skills/_shared/elicitation-contract.md`.

The procedure decides which claims of a reviewed change a later reader needs
from `.archcore/`, which document owns each claim, and which claims stay in code.
The origin of the code — a plan, another agent, a branch with no documents —
changes neither the evidence rules nor the selection rules.

## Terms

- **Unit**: one claim, or one related claim group, that answers a named future
  reader task. A changed file or a diff hunk is not a unit.
- **Signal**: complexity, implicitness, or uncertainty in the change. A signal
  marks where to inspect. A signal alone never selects or drops a unit.
- **Owner**: the existing document, or the document type, that holds exactly
  that kind of claim per its content contract.

## Inputs

- The branch boundary and scoped diff from `skills/_shared/branch-state.md`.
- The working tree, the relevant code and tests, and available git history.
- The scoped `.archcore/` documents and the bidirectional-check findings.
- With a matched plan: the `closeout.verify` report, including unplanned Δ, and
  the `closeout.merge` report.
- MR description or discussion only when the user supplied it. Local git
  establishes neither MR intent nor a test result.

## Procedure

1. Inspect the relevant code, tests, scoped documents, and history before naming any candidate.
2. With a matched plan, list the plan's claims that no other document holds yet.
3. With a plan covering part of the change, treat the rest as planless without attributing it.
4. For each changed subject with a relied-on contract, inspect its surface, invariants, and failure behavior beyond the changed lines.
5. Name candidates by claim and reader task, using the signal table below.
6. Apply the four tests below to each candidate.
7. Drop each candidate that fails test 1 or test 2; record it as omitted with the reason.
8. For each remaining candidate, prefer a focused update of the existing owner over a new document.
9. Split new documents only by independent surfaces, per `skills/_shared/spec-contract.md` "Over the cap".
10. Show the preview, then write only the units the user authorizes.

Zero units is a valid result. No count is a target or a limit.

## Signal → owner

| Signal in the change | What a later reader misses | Owner |
|---|---|---|
| External interface, state, rule priority, or failure behavior | A contract condition invisible on one success path | The covering `spec`; a new independent surface gets its own `spec` |
| A choice between options with directly evidenced reasons | Why the alternative lost and when the choice expires | `adr` |
| A repeatable operation where order matters | Prerequisites, the hazardous step, verification, recovery | `guide` for a human actor; `task-type` for an agent actor |
| A deliberately changed code practice with an evidenced reason, transferring beyond this edit | Before, after, scope, reason | `cpat` |
| An observable user flow with confirmed examples | Branches and the result for the actor | `scenario` beside the covering `spec` |
| A registry or reference data looked up on its own | Where the list lives and how to read it | `doc`, when an `@path` alone does not answer the task |
| One unexpected failure or limit | The condition under which the old picture was wrong | The owning Failure Behavior clause, `adr` consequence, or procedure Pitfalls |
| A local implementation that code and tests explain | Nothing durable | No document |

A simple public contract with no owner can warrant a `spec`. A complex internal
implementation that code and tests explain warrants none.

## Four tests

1. **Reader task.** Name the later task that needs this claim from a durable owner.
2. **Evidence.** Cite code, tests, history, supplied MR material, or the user's answer that confirms it.
3. **Durability.** Check that the claim survives an ordinary refactor; a claim that does not usually belongs in code or a test.
4. **Owner.** Name the existing document or the type that owns exactly this claim.

## Evidence limits

| Source | Establishes | Does not establish alone |
|---|---|---|
| Code and diff | The implemented path, interface, state, error handling | Intent, agreement, or verification in use |
| Tests and a run report | The checked examples and that run's result | Full contract coverage or the product goal |
| Plan and `Declared Delta` | The original intent and promised scope | Completion, or that undeclared code is wrong |
| Supplied MR material, commits | The stated motivation, when recorded | The truth of an unverified statement |
| Accepted documents | The current contract and constraints | That the changed code still satisfies them |
| The user's answer | Intent, status, and removal decisions | A test result that never ran |

- IF the evidence does not record the reasons and alternatives of a choice, THEN do not propose an `adr`; report the rationale as an open gap.
- IF the evidence does not record why a code practice changed, THEN do not propose a `cpat`; report the reason as an open gap.
- IF a new flow has no run report and no user confirmation, THEN label its examples unconfirmed.
- IF evidence conflicts with an accepted document, THEN report the conflict with its `skills/_shared/verdict-contract.md` label; do not treat the code as canon.
- IF no existing type owns a unit, THEN report the ownership gap; do not force a `cpat` or a `task-type`.
- Never select a `journey`. A discovered product goal is reported as an open question for `/archcore:plan`.

## Preview and authorization

1. Show every proposed write in one preview: per unit, the target path or type, the claims, the evidence, and the status `draft`.
2. Ask one question for the whole preview: write all, write a named subset, or write none. Recommend the evidenced set.
3. Count that question against the per-invocation ceiling.
4. IF the ceiling is exhausted before the preview, THEN report the selection unwritten and name the ceiling as the reason.
5. IF the user declines a unit, THEN record it as declined; a declined unit blocks no plan removal.

## Write routing

Each authorized unit runs through the instrument that owns its type, in callable
mode with the unit's scope and type pre-filled:

- `spec`, `doc`, `guide` for a module, `scenario` → `skills/_shared/tracks/describe.md`; the pre-filled type settles `describe.draft` without its type question.
- `adr` → `skills/_shared/tracks/decision.md` with the subject naming `adr` and the evidenced alternatives.
- `cpat`, `task-type`, a procedural `guide` → the produced-type rules of `skills/_shared/tracks/experience.md`; the preview replaces `experience.offer` for that unit.
- An update of an existing owner → `update_document` on that document; the preview authorization is its confirmation.

A created document starts at `draft`. The same invocation does not offer its
acceptance; the next review's accept gate does. Never copy source bodies,
generated schemas, or file inventories where an `@path` reference answers the
reader task.

## Report

Group the units as created, updated, omitted, deferred, and declined. Name the
claim and reason for each omitted and declined unit, and the missing check for
each deferred one.
