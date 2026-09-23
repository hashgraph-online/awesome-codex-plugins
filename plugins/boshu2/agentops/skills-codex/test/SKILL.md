---
name: test
description: 'Write behavioral tests, practice TDD or inspect important coverage gaps. Use when: test design or missing proof needs work; running an existing suite needs no skill.'
---
# Test

Write or strengthen tests for a named behavior. Use existing tests directly when
the task is only to run a known suite; this skill is not a required wrapper.
A test is useful when it distinguishes an accepted outcome from a plausible
failure, not merely when it executes the implementation.

## Modes

| Mode | Use when | Result |
|---|---|---|
| `generate` | Existing behavior needs tests | Useful tests and focused/suite results |
| `coverage` | The caller asks to find or fill gaps | Before/after coverage, valuable tests and remaining risks |
| `tdd` | New behavior is being developed test first | Real expected RED, implementation, green and refactor |
| `strategy` | The caller wants test design only | Prioritized risks and proposed checks in the existing discussion |

Default to `generate`; mode and scope are skill prompt choices, not invented
CLI flags. Coverage thresholds come from the caller or repository.

## Critical Constraints

- Derive cases from accepted observable behavior. Reuse examples from the
  conversation, bead, specification or existing contract before inventing new ones.
- Preserve established domain names in test names and fixtures. Different
  bounded contexts may use different terms; do not unify them by renaming tests.
- Use the repository's framework and real check recipe. Keep tests isolated
  from accidental timing, ordering and mutable shared-state dependencies.
- A test that starts green on existing correct behavior is legitimate. Never
  manufacture a RED claim or alter acceptance to excuse a product defect.
- Repair a discovered defect when already authorized; otherwise report the
  reproducer and finding. Do not mask it by deleting or weakening a test.

## Oracle-strength hierarchy

Prefer exact observable values or errors when known. Use properties or
invariants when they express the contract more faithfully than one example.
Differential agreement needs an independently credible reference. A smoke
check proves only what it observes; it cannot establish an exact behavior by
itself. Explain a material oracle limit in the native handoff, without creating
a worksheet or mandatory report.

## Mutation-kill proof

Establish that an important new behavioral check can catch the defect it claims
to guard. An authentic pre-fix RED or reproduction is usually sufficient. If a
regression test was written after the fix, run it against the pre-fix version
or use a safe, targeted negative control in an isolated copy. Mutate only when
that would resolve real doubt about the oracle, then restore and verify the
candidate. Do not demand one mutation experiment per table row or new test.

## Harness health floors

Confirm the runner completed, the intended tests actually ran, and assertions
observe the promised behavior. Report crashes, truncation, unexpected skips or
exclusions as gaps. When runner discovery or failure reporting changed, use a
negative control through that same path before trusting green. No need to
re-prove an unchanged healthy runner on each edit.

## Workflow

1. Read the accepted examples and relevant public interface. For a small change,
   one discriminating example may suffice; add consequential error/boundary
   cases where they could falsify acceptance. A `.feature` file is optional.
   If the repository already uses scenario-to-test annotations, maintain them
   and use its scenario coverage checker. Do not add a feature file just to
   satisfy this skill.
2. Find the owning suite, applicable repository standards and a narrow baseline.
   Use [Domain's standards](../domain/references/standards/test-pyramid.md) only
   if additional guidance would affect the test choice. Measure broad coverage
   only for `coverage` mode or an existing repository requirement.
3. Write the smallest test that observes the promised result through a stable
   interface. In `tdd` mode run it before implementation and require the expected
   missing-behavior failure, then implement and refactor under green. In other
   modes use evidence appropriate to existing versus newly fixed behavior.
4. Run the focused checks during editing, then the relevant integration recipe
   before handoff. Broaden only for changed risk, a failure or repository policy;
   avoid replaying the full suite after every small edit.
5. Return test changes, literal commands and results, discovered defects and
   material unchecked behavior. Compare against the original accepted examples.
   New tests added after implementation may supplement but never replace them.

## Specialized references

Load only the guidance needed by the subject:

- Public compatibility contracts: [conformance-harnesses](references/conformance-harnesses.md)
- Parsers and hostile inputs: [fuzzing](references/fuzzing.md)
- Snapshots: [golden artifacts](references/golden-artifacts.md) and [update strategy](references/golden-artifact-strategy.md)
- Invariants: [metamorphic testing](references/metamorphic-testing.md)
- Service integration: [real-service E2E](references/real-service-e2e.md)

## Output Specification

Tests belong in the repository's language-native locations. Check facts and
limits belong in the existing handoff. Persist coverage or other reports only
when requested or required by a declared consumer, at its selected destination;
no automatic `.agents/` output. Factual green is input to fresh validation,
not the test author's binding PASS.

Example: for a duplicate Job delivery, assert that the completed result is
returned and the external side effect is called only once. Run the focused
case and owning suite. A coverage increase without those assertions would not
prove the behavior.

This guidance uses original examples informed by
[Matt Pocock's engineering skills](https://github.com/mattpocock/skills),
with AgentOps' existing acceptance and evidence boundaries.
