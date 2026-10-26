# Proof fidelity

Use this reference when a green result might prove something other than the
behavior it claims: a defect's proof sits in the wrong test or at a seam too
shallow to fail the way the report did, the change is itself a check standing
in for a real run, or correctness is a matter of meaning that no exact value
captures. It supplements [Test](../SKILL.md); it adds no mode, score or report.

## Place the proof of a defect

Before changing production code, decide which test carries the proof:

- A test already failing on the defect is the RED. Do not add a copy of it.
- A test that owns the contract but expects what accepted behavior contradicts
  is corrected and seen to fail. If the change would instead reverse an
  expectation that accepted behavior supports, that is an acceptance question
  for the caller, not a test edit.
- A test that should have caught the defect but mocks or skips the step that
  decides it is strengthened at that step, so the coverage that let the defect
  through is the coverage that now guards it.
- Otherwise add the smallest new case, named for the broken behavior. Put it in
  the test that owns that contract unless it reaches a risk the owner cannot.

The test must fail the way the report did: through the callers, sequence or
state that produced it, not only at the line that changed. A test that calls
the repaired function directly can go red on the local symptom while the
reported chain still breaks. When no reachable interface can trigger that
chain, do not write a shallower stand-in. Use the original reproduction as the
before/after check, list the missing regression test under `not_checked`, and
report the missing seam as a structural finding for
[Architecture](../../architecture/SKILL.md).

## A check that stands in for a real run

A CI step, gate, smoke test, harness or test double protects something it does
not itself run. When the change is such a check, compare what it runs against
with what it protects: working directory, prepared files and directories,
environment, inputs and command order. A gate that reads the working tree while
the protected thing is the commit, a smoke test that starts after the build step
users depend on, or a double that replaces the path that breaks can all stay
green while the real thing fails.

Name that green-while-red case, then show the check catches it: break the real
path in a disposable copy and confirm the check goes red through the same
invocation the protected run uses. A negative control that fails only in an
easier context proves only that context. When the contexts cannot be matched,
report the difference as a limit of the check under `not_checked`.

## Output judged for meaning

When correctness is a matter of meaning, as for a summary, a ranking or a
grouping, a count, length or coverage figure is a proxy that can improve while
the output gets worse. Use an exact value, property or credible reference for
any part of the contract they can express; a judged result is weaker evidence
than those.

1. Reject plainly broken output first with cheap hard checks: empty or
   truncated output, the wrong format, items invented, duplicated or dropped
   against the input.
2. Write the rubric before judging. Describe what the output concretely does at
   each level, and do not reward length or quantity for itself.
3. Judge a sample drawn the same way for every candidate: the same seed and
   strata, weighted toward inputs where failure is likely, and including items
   the output left out or left ungrouped.
4. Judge in a context that did not produce the output. Keep the judgment for
   each sampled item, the reason for each low one and a flag where the rubric
   was ambiguous.
5. Decide before judging what difference counts as a gain, wide enough to
   absorb a different mix of sampled items. Counts and other diagnostics can
   explain a result; they do not decide it.

Example: a change to ticket grouping cuts ungrouped tickets from 40 to 5, but
the judged sample shows several new groups merging unrelated issues. The count
improved while the grouping got worse, so the candidate misses the accepted
promise.

Return the rubric, sample, judgments and limits in the existing handoff; persist
them only for a requested destination or declared consumer.
