---
name: sdlc-build
description: Convert an accepted .sdlc/feature-slug/spec.md into a reviewed, engineer-approved plan.md and then implement it in the accepted order. Also the entry point for the fast path, when a person declares a change low-risk and it enters at Build with no intent.md or spec.md. Do NOT use for unapproved specifications, for a change the sensitive-path list covers, independent architecture review, test sign-off, PR review, merging, deployment, or production monitoring.
---

# SDLC Build

Run Stage 3 of 6 in the AI-Native SDLC playbook described in `docs/PLAYBOOK.md`.

## Purpose

Work in two distinct phases: create an approved engineering plan, then implement
the approved plan.

`plan.md` is the contract for implementation. Do not treat it as optional notes.

## Entry gate

Locate `.sdlc/<slug>/spec.md` and read it completely.

Proceed only when the spec exists and declares `Status: accepted`.

If the spec is absent, draft, or unapproved, route to `sdlc-design` and stop —
unless the change enters on the fast path below.

Do not begin code changes during Phase A.

## Fast path

The playbook already allows a low-risk change to enter at Build. This is how.

A change takes the fast path only when a person declares it low-risk. The agent
never makes that call; it checks the declaration and can refuse it.

On a declaration, before writing anything:

1. Read the **Sensitive paths** list in `REVIEW.md`. If that file or that list is
   absent, there is no fast path: route to `sdlc-plan` and stop.
2. Compare every file the change will touch against that list.
3. If any file matches, refuse the fast path, name the matching path, and route to
   `sdlc-plan`. A declaration does not override the list.
4. If none matches, write `.sdlc/<slug>/plan.md` with a `## Fast path` section
   immediately above `## Files that change`:

   ```markdown
   ## Fast path
   Declared low-risk by: [person]. Reason: [why].
   Sensitive-path check: no file in `REVIEW.md` **Sensitive paths** is touched.
   ```

Add that heading only to a fast-path plan. The artifact gate reads it from the
committed plan, and while it is present every sensitive path is closed to this
change — an ordinary plan carrying it would block its own work. When a change is
re-routed to `sdlc-plan`, remove the section.

A fast-path change skips Stage 1 and Stage 2. It skips nothing else. It still gets
the Plan review below, the full Build and Test stages, the Stage 5 review passes,
and a human approval on the PR.

The declared file list is a claim, not a fact. `sdlc-deploy` checks the real diff
against the sensitive-path list again, and a diff that reaches one revokes the fast
path.

## Phase A: interview and plan

1. Read the accepted spec, including requirements, non-goals, concerns, and
   verification strategy. On the fast path there is no spec: read the `## Fast path`
   declaration instead, and treat its stated reason and scope as the requirement the
   plan must satisfy.
2. Interview the engineer about the proposed approach.
3. Ask which tools or libraries the engineer expects to use and why.
4. Ask for every file expected to change, be added, or be removed.
5. Ask for the implementation order and dependencies between steps.
6. Ask which risks, migrations, compatibility concerns, or rollback concerns exist.
7. Ask how the implementation will prove every requirement and non-goal boundary.
8. Write `.sdlc/<slug>/plan.md` using the required template.
9. Review the plan before the engineer sees it, as described below.
10. Show the full plan to the engineer, with the review findings beside it.
11. Stop for explicit approval before any coding begins.

## Plan review

Review the plan while changing direction still means editing Markdown. A defect
caught here costs a paragraph; the same defect caught at Stage 5 costs a commit and
a review round, and every round an agent author spends is a round nobody spends on
the next change.

1. Read the reviewer named for Stage 3 in `REVIEW.md`. The default is
   `codex-plan-review`.
2. If that reviewer is not installed, fall back to the `sdlc-reviewer` subagent
   running the `Plan` pass, and record the fallback. Never skip the review because
   the configured reviewer is missing.
3. Run the `Plan` pass only. Bugs, Security and Compliance need code and run at
   Stage 5.
4. State the budget in the invocation, because an external reviewer has its own
   loop and will not read this file: the `Plan` pass only, at most three rounds,
   only what changed since the previous round after round 1, no finding that
   `review-findings.md` already records, a repeated defect reported once as a
   class, and findings in the one-line `path:line — Severity — failure — fix` form.
5. Record each round in `.sdlc/<slug>/review-findings.md` under stage `Plan`.
6. At the cap, stop reviewing and tell the engineer the approach itself needs
   rethinking. Three rounds on a Markdown plan means the plan is not the problem.
7. If the reviewer returns having run more rounds than the budget, record the real
   number. The count is evidence about the review, and quietly writing down the
   budget instead of what happened makes the round metrics worthless.

An external reviewer may debate to its own conclusion rather than to this budget —
`codex-plan-review`, for one, is documented to run until it approves or deadlocks,
with no round cap of its own. Passing the budget in the invocation is then a request,
not a limit. Where the cost of that matters more than the extra depth, name
`sdlc-reviewer` for Stage 3 in `REVIEW.md`: it honours the cap because this skill
drives its rounds.

Fix what the review finds before showing the plan, or record why a finding was not
acted on. The engineer approves the plan and its findings together.

Pay particular attention to `Files that change`. The artifact gate admits source
writes from that list: a missing entry blocks the implementation mid-flight, and an
over-broad entry widens what the gate will admit.

## Required artifact

Write this plan structure verbatim. Replace only bracketed content with the
engineer's confirmed approach.

```markdown
# Plan: [feature name] (from spec.md [date])

## Files that change
[list of affected files]

## Order of work
[numbered steps]

## Risks
[potential issues]

## Proof
[test coverage description]
```

In **Proof**, describe verification coverage rather than writing test code. For
example, name the unit tests and integration tests that will establish correctness.

List expected files precisely enough that reviewers can compare plan to changes.

## Phase A exit gate

After showing the plan, stop and ask exactly:

> Engineer, does this plan match your approach?

Accept only explicit engineer approval. Do not treat a request to continue as
approval, and do not implement while approval is pending.

If the engineer corrects the plan, revise it and repeat the gate.

## Phase B: implement

Begin Phase B only after explicit approval of `plan.md`.

1. Read and follow the project's `CLAUDE.md` before touching implementation.
2. Use `CLAUDE.md` as project memory and instructions.
3. Apply available skills as policy rather than bypassing them.
4. Respect hooks as guardrails; do not evade or disable them.
5. Use parallel sessions only for genuinely independent work when available and
   permitted by project instructions.
6. Implement the plan in its accepted order.
7. Preserve the spec's non-goals and unresolved concerns.
8. Record each actual deviation in `plan.md` as it happens, including why it was
   necessary and how it affects proof or risk.
9. Do not silently change the chosen approach, file set, order, or verification.

If a deviation invalidates the plan's contract, pause and seek engineer direction
before continuing.

Do not claim that tests pass in this stage unless tests have actually been run;
formal verification is Stage 4.

## Phase B exit gate

When the code exists and deviations are recorded, stop and ask exactly:

> Is the implementation complete per the plan?

Move to testing only after confirmation.

If the engineer says no or identifies incomplete work, return to the accepted plan
and complete or revise the recorded work before asking again.

## Handoff

Hand off `plan.md` and the implemented code to `sdlc-test`.

Include actual deviations and their recorded locations in `plan.md`.

Do not hand off a plan without code or code without its plan.
