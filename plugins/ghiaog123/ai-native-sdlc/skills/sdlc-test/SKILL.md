---
name: sdlc-test
description: Execute project verification for an implemented, planned change and report real test and applicable eval output before it can be reviewed. Do NOT use for drafting plans, implementing features, speculative test advice, PR review, merging, deployment, or monitoring.
---

# SDLC Test

Run Stage 4 of 6 in the AI-Native SDLC playbook described in `docs/PLAYBOOK.md`.

## Purpose

Prove the implementation against `plan.md` and `spec.md` before review.

The agent must execute verification. Never claim that tests pass based on source
inspection, an earlier run, or an assumption.

## Entry gate

Locate `.sdlc/<slug>/plan.md`, `.sdlc/<slug>/spec.md`, and the implemented code.

Verify that `plan.md` contains **Proof** and that `spec.md` contains
**Verification strategy**.

Verify that the spec was accepted and that implementation is available to test.

If any artifact, required section, or implementation is missing, return to
`sdlc-build` and stop.

A change whose `plan.md` has a `## Fast path` section has no `spec.md` by design. For
it, require `plan.md`, its **Proof** section, and the implemented code, and read the
fast-path declaration in place of the spec. Everything else in this stage is unchanged:
the fast path skips Stage 1 and Stage 2, never verification.

## Procedure

1. Read `plan.md` **Proof** in full.
2. Read `spec.md` **Verification strategy** in full, or, on the fast path, the
   `## Fast path` declaration and the plan's stated scope.
3. Map the planned proof to the spec's requirements and verification strategy, or on
   the fast path to the declared scope and reason.
4. Discover the project's documented test commands and test suites.
5. Execute all tests in the project, including the tests named by the plan where
   applicable.
6. Capture actual command output, exit status, skipped tests, and failures.
7. Quote the real relevant output in the verification report.
8. Determine whether this change modified `CLAUDE.md`, any skill, any hook,
   `REVIEW.md`, or the reviewer subagent definition. The review policy and the
   reviewer are configuration like any other: a change that weakens either is a
   change nothing else in the loop will catch.
9. If it did, discover the project's existing eval suite for that configuration.
10. Run the applicable eval suite and quote its actual output and exit status.
11. If no eval suite exists, state that none was found; do not invent an eval.
12. Compare evidence with every planned and specified verification claim.

Do not omit a suite because it is slow, inconvenient, or unrelated at first glance.

If the project documents a required environment that is unavailable, report the
specific blocker and do not mark verification green.

## Evals

An eval is a fixed prompt set with expected-behaviour assertions, versioned beside
the configuration it protects.

When `CLAUDE.md`, a skill, a hook, `REVIEW.md`, or the reviewer definition changes,
find and run the project evals that guard that configuration.

## The reviewer's own eval set

`.sdlc/evals/reviewer/` holds the cases that protect the reviewer itself. Each case
is one past change that escaped review, with the defect that escaped:

```text
.sdlc/evals/reviewer/
├── proposed/     written by sdlc-maintain, not yet confirmed by a person
├── confirmed/    a person agreed the defect is real; these are the eval set
└── clean/        changes known to contain no defect
```

A case names the change, the commit that introduced the defect, the file and line,
the bug class, and the fix. A case passes when the reviewer, run against that
change, reports that file and that bug class at `Important`. Reporting something
else at that location is not a pass.

Run `confirmed/` when `REVIEW.md` or the reviewer definition changes, and keep the
result only if it does not fall. Run `clean/` the same way: a finding there is a
false alarm, and the rate is the noise signal in `docs/METRICS.md`.

Only a person moves a case from `proposed/` to `confirmed/`. An agent never
promotes its own case, and an unconfirmed case never gates anything.

Do not invent an eval suite, expected results, or passing result. Note plainly when
no project eval suite can be found.

## Failure loop

If any test, required check, or applicable eval is red, return to code.

Report the real failure output and identify the failed proof or verification claim.

Do not ask for review, produce a deployment handoff, or call verification green
while any required evidence is red or missing.

After code is corrected, rerun the affected verification and all project tests.

## Required report

Show a concise evidence report containing:

- The tests and commands actually executed.
- Quoted real output for pass or failure.
- The result of each relevant `Proof` and verification-strategy item.
- Whether configuration changed.
- Applicable eval commands and quoted results, or the fact that none was found.

Do not replace quoted output with “tests pass.” The output is the evidence.

## Exit gate

Proceed only when all of the following are true:

1. All project tests pass, with quoted output.
2. If protected configuration changed, all applicable evals pass, with quoted output.
3. The agent explicitly states: `Verification is green`.

Stop and show the test output before handing off.

If any condition is false, loop back to code and do not request review.

## Handoff

Hand off to `sdlc-deploy` only with the complete test evidence.

Include commands, quoted results, relevant eval status, and any limitations that
were resolved before the final green result.
