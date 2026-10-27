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
evidence for the caller's decision, never the test author's merge approval;
the binding verdict belongs to [Validate](../validate/SKILL.md).

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

- **Assert the promised effect.** Check the state change, outbound call or count
  the behavior promises at its boundary, reading a stored record back through
  the product's own read path unless the stored shape is the contract. Take
  exact expected values from a literal, worked example or the specification,
  never the implementation's own formula or a mock's answer: for a 20% discount
  on 50, assert 40. A status code, a returned object or the absence of an
  exception alone does not prove the behavior; would the test stay green if the
  code returned an empty or default result? A rejection test asserts the error
  its name claims, since another guard can reject the same input.
- **A regression test proves nothing until it fails on the defect.** Show that
  it fails on the pre-fix code (see Mutation-kill proof) through the callers,
  sequence or state that produced the report, not only at the changed line.
  Until then, report its proof as "not shown"; green alone is not yet proof.
- Derive cases from accepted observable behavior; reuse examples from the
  conversation, bead, specification or existing contract before inventing
  new ones. Keep established domain names; do not unify bounded-context terms
  by renaming tests.
- Use the repository's framework and real check recipe; keep tests free of
  accidental timing, ordering and shared-state dependencies.
- A test that starts green on existing correct behavior is legitimate; use such
  tests to pin untested code before changing it, marking an odd result as a
  suspected defect. Never manufacture a RED claim or alter acceptance to excuse
  a product defect.
- Repair a discovered defect when already authorized; otherwise report the reproducer and finding, never masking it by deleting or weakening a test ([fix the cause, not the oracle](../implement/SKILL.md#rules-that-decide-the-result)).

## Oracle-strength hierarchy

Prefer exact observable values or errors when known. Use properties or
invariants when they express the contract more faithfully than one example.
Differential agreement needs an independently credible reference. A smoke
check proves only what it observes; it cannot establish an exact behavior by
itself. When correctness is a matter of meaning, as for a summary or ranking, a
count is only a proxy; judge it as in [proof fidelity](references/proof-fidelity.md#output-judged-for-meaning).
Explain a material oracle limit in the native handoff, without creating a
worksheet or mandatory report.

## Mutation-kill proof

Establish that an important new behavioral check can catch the defect it claims
to guard. An authentic pre-fix RED or reproduction is usually sufficient. If a
regression test was written after the fix, run it against the pre-fix version
(revert the fix in an isolated copy) or use a safe, targeted negative control.
Mutate only when that would resolve real doubt about the oracle, then restore
and verify the candidate. Do not demand one mutation experiment per table row
or new test. Trust a revert or mutation result only from a copy confirmed to
hold this candidate's commit and uncommitted changes plus that one edit; a
worktree cut from HEAD can lack the fix or test. Never mutate a shared checkout.

## Harness health floors

Confirm the runner completed, the intended tests actually ran, and assertions
observe the promised behavior. Take the result from the runner's exit status,
not its printed output, and keep that status through pipes (`pipefail`):
`make test | tail` reports `tail`. A check that edits tracked files has changed
the subject; report the edit. Report crashes, truncation, unexpected skips or
exclusions as gaps. When runner discovery or failure reporting changed, use a
negative control through that same path before trusting green. When the change
is itself a check standing in for a real run, also match its context to what it
protects ([proof fidelity](references/proof-fidelity.md#a-check-that-stands-in-for-a-real-run)).
No need to re-prove an unchanged healthy runner on each edit.

## Workflow

1. Read the accepted examples and the relevant public interface. One
   discriminating example may suffice for a small change; add the error and
   boundary cases that could falsify acceptance. A `.feature` file is optional;
   if the repository already uses scenario-to-test annotations, maintain them
   and use its scenario coverage checker. When several record kinds support
   different actions, derive the meaningful kind/action pairs from accepted
   domain rules and check their promised end states. Do not invent impossible
   combinations or infer a kind's result from a sibling's passing test. A table
   test may cover many pairs; no separate artifact or test per cell is required.
   Report relevant uncovered pairs under `not_checked`. Shared removal code is
   valid when those kinds should both disappear; it is a defect when an observed
   end state contradicts the accepted meaning, such as deleting a record that
   withdrawal must retain as inactive.
2. Find the owning suite and a narrow baseline. For a defect, choose which test
   carries its proof before changing code; with no seam that reaches the
   reported chain, write no shallower stand-in
   ([proof fidelity](references/proof-fidelity.md#place-the-proof-of-a-defect)).
   Use [Domain's standards](../domain/references/standards/test-pyramid.md) only
   if they would change the test choice. Measure broad coverage only in
   `coverage` mode or under an existing repository requirement.
3. Write the smallest test that observes the promised result through a stable
   interface: the entry point callers use. Add no export, flag or hook only
   tests call (a time, randomness or external-boundary seam excepted), mock no
   collaborator inside the unit, and move to the interface any test you write
   here that a behavior-preserving rewrite would break; list existing ones under
   `not_checked` as rewrite candidates ([suite audit](references/suite-audit.md)).
   In `tdd` mode run it before implementation and require the expected
   missing-behavior failure, then implement and refactor under green, one test
   at a time, each next case chosen from what the last cycle showed.
4. Run focused checks while editing and the relevant integration recipe before
   handoff; broaden only for changed risk, a failure or repository policy.
5. Compare against the original accepted examples. New tests added after
   implementation may supplement but never replace them.

## Specialized references

Load only the guidance needed by the subject:

- Public compatibility contracts: [conformance-harnesses](references/conformance-harnesses.md)
- Parsers and hostile inputs: [fuzzing](references/fuzzing.md)
- Snapshots and golden-file updates: [golden artifacts](references/golden-artifacts.md)
- Invariants: [metamorphic testing](references/metamorphic-testing.md)
- Service integration: [real-service E2E](references/real-service-e2e.md)
- Selected user journeys: [exploratory QA](references/exploratory-qa.md)
- Authorized suite maintenance: [suite audit](references/suite-audit.md)
- Defect proof placement, stand-in checks and judged output: [proof fidelity](references/proof-fidelity.md)
- CLI/API failure signals and uncertain write outcomes: [error recovery](references/error-recovery.md)
- Timing, shared-state or concurrency failures: [difficult-failure experiments](../implement/references/difficult-failures.md)
- Workload baseline and candidate comparison: [subject performance](references/subject-performance.md)

## Output Specification

Tests belong in the repository's language-native locations. Check facts and
limits go in the existing handoff:

```text
tests:       <file::name> -> <behavior and exact values it asserts>
proof:       <each important new test> -> how it was shown to fail on its defect:
             pre-fix RED | reverted-fix run | negative control | not shown
commands:    <exact command> -> <result>
harness:     <runner completed; how many ran; skips or exclusions>
coverage:    <before -> after, command> (coverage mode only)
defects:     <discovered defect and reproducer, or none>
not_checked: <material behavior no test covers>
```

Persist coverage or other reports only when requested or required by a declared
consumer, at its selected destination; no automatic `.agents/` output.

Example: for a duplicate Job delivery, assert that the completed result is
returned and the external side effect is called only once. A coverage increase
without those assertions would not prove the behavior.

This guidance uses original examples informed by
[Matt Pocock's engineering skills](https://github.com/mattpocock/skills),
with AgentOps' existing acceptance and evidence boundaries.
