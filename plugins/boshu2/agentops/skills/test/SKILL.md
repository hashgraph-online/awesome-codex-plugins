---
name: test
description: 'Write or assess tests that prove behavior and would fail without the fix. Use when: writing tests, TDD, or asked whether a green test is enough.'
practices:
- tdd
- property-based-testing
- bdd-gherkin
hexagonal_role: supporting
consumes:
- standards
- repo-context
produces:
- test-evidence
context_rel: []
skill_api_version: 1
user-invocable: true
context:
  window: fork
  intent:
    mode: task
  sections:
    exclude:
    - HISTORY
metadata:
  capabilities: [test]
  effects: [write_test_files, write_test_evidence, modify_source_files]
  canonical_status: canonical
  disposition: keep_specialist
  tier: execution
  dependencies: []
output_contract: behavioral tests and reproducible check facts; coverage results when requested
---
# Test

Write or strengthen tests for a named behavior. Use existing tests directly when
the task is only to run a known suite; this skill is not a required wrapper.
A test is useful when it distinguishes an accepted outcome from a plausible
failure, not merely when it executes the implementation. A green test is
evidence for the caller's decision, never the test author's merge approval.

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

- **Assert the promised effect.** Check the state change, stored record,
  outbound call or count the behavior promises, with exact expected values. A
  status code, a returned object or the absence of an exception alone does not
  prove the behavior.
- **A regression test proves nothing until it fails on the defect.** Show that
  it fails on the pre-fix code (see Mutation-kill proof). Until then, report its
  proof as "not shown"; green alone is not yet proof.
- Derive cases from accepted observable behavior; reuse examples from the
  conversation, bead, specification or existing contract before inventing
  new ones. Keep established domain names; do not unify bounded-context terms
  by renaming tests.
- Use the repository's framework and real check recipe; keep tests free of
  accidental timing, ordering and shared-state dependencies.
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
(revert the fix in an isolated copy) or use a safe, targeted negative control.
Mutate only when that would resolve real doubt about the oracle, then restore
and verify the candidate. Do not demand one mutation experiment per table row
or new test.

## Harness health floors

Confirm the runner completed, the intended tests actually ran, and assertions
observe the promised behavior. Report crashes, truncation, unexpected skips or
exclusions as gaps. When runner discovery or failure reporting changed, use a
negative control through that same path before trusting green. No need to
re-prove an unchanged healthy runner on each edit.

## Workflow

1. Read the accepted examples and the relevant public interface. One
   discriminating example may suffice for a small change; add the error and
   boundary cases that could falsify acceptance. A `.feature` file is optional;
   if the repository already uses scenario-to-test annotations, maintain them
   and use its scenario coverage checker.
2. Find the owning suite and a narrow baseline. Use
   [Domain's standards](../domain/references/standards/test-pyramid.md) only if
   they would change the test choice. Measure broad coverage only in `coverage`
   mode or under an existing repository requirement.
3. Write the smallest test that observes the promised result through a stable
   interface. In `tdd` mode run it before implementation and require the expected
   missing-behavior failure, then implement and refactor under green.
4. Run focused checks while editing and the relevant integration recipe before
   handoff; broaden only for changed risk, a failure or repository policy.
5. Compare against the original accepted examples. New tests added after
   implementation may supplement but never replace them.

## Specialized references

Load only the guidance needed by the subject:

- Public compatibility contracts: [conformance-harnesses](references/conformance-harnesses.md)
- Parsers and hostile inputs: [fuzzing](references/fuzzing.md)
- Snapshots: [golden artifacts](references/golden-artifacts.md) and [update strategy](references/golden-artifact-strategy.md)
- Invariants: [metamorphic testing](references/metamorphic-testing.md)
- Service integration: [real-service E2E](references/real-service-e2e.md)

## Output Specification

Tests belong in the repository's language-native locations. Check facts and
limits go in the existing handoff:

```text
tests:     <file::name> -> <behavior and exact values it asserts>
proof:     <each important new test> -> how it was shown to fail on its defect:
           pre-fix RED | reverted-fix run | negative control | not shown
commands:  <exact command> -> <result>
harness:   <runner completed; how many ran; skips or exclusions>
defects:   <discovered defect and reproducer, or none>
unchecked: <material behavior no test covers>
```

Persist coverage or other reports only when requested or required by a declared
consumer, at its selected destination; no automatic `.agents/` output. Factual
green is input to the caller's merge or review decision, not the test author's
binding PASS.

Example: for a duplicate Job delivery, assert that the completed result is
returned and the external side effect is called only once. A coverage increase
without those assertions would not prove the behavior.

This guidance uses original examples informed by
[Matt Pocock's engineering skills](https://github.com/mattpocock/skills),
with AgentOps' existing acceptance and evidence boundaries.
