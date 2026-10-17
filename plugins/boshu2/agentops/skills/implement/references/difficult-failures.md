# Difficult failures

Use the matching experiment only when an unexplained symptom suggests varying
conditions, leaked state or concurrent access. These experiments support
Implement's existing cause, prediction, discriminating check and original
scenario loop; they add no phase or obligation to an ordinary known repair.

## Preserve the reported failure

Keep the observed trigger, wrong result and relevant conditions available.
Reduce inputs or setup safely, retaining the same symptom and accepted behavior.
A smaller case that fails for a different reason does not reproduce the report.
Use isolated test data; reproduction does not authorize destructive operations
or instrumentation in a live service.

Identify the baseline and candidate content and inputs before comparing them.
Keep comparable setup, execution order and environment. A failure on the baseline
can establish that it predates the candidate; it does not make that failure
irrelevant to the requested outcome or authorize ignoring a required check.
If the symptom cannot be reproduced, report the observed evidence and missing
condition; a plausible explanation is still an untested prediction.

## Intermittent verdicts

Name the variable the causal prediction depends on: for example, random seed,
test order, clock state, dependency availability or a resource constraint.
Observe that variable and compare baseline and candidate under controlled,
comparable conditions. Where supported, pin it or vary it deliberately while
holding the other relevant conditions steady. Use a probe that exercises the
suspected dependency and asserts the original promised result.

When repetition is useful, state the conditions, sample count and observed
failures for each comparison. Choose the observation effort for the uncertainty
and actual remaining bounds, without imposing a universal repetition count.
Preserve adverse observations rather than discarding them until a run passes.

Example: a reservation sometimes remains active after its deadline. Control the
clock on either side of that deadline, observe the state, and check both expiry
and a still-valid reservation after repairing the cause. Merely waiting longer
does not establish which dependency caused the wrong state.

Retries, longer sleeps and wider timeouts do not prove a cause or a fix. Repeated
green within a bounded sample is an observation under those conditions, not
proof that every intermittent failure has been eliminated.

## A predecessor changes a later test

Compare the affected test alone with that test after the actual ordered prefix
from the failing run, preserving relevant process and shared-state boundaries.
If the difference survives, reduce the prefix while retaining its order and the
failure. Keep the smallest sufficient predecessor condition you can establish;
several predecessors may interact, so do not assume there is one guilty file.

Inspect the state that survives its legitimate lifetime, such as configuration,
a cache, a replacement dependency, a timer or a shared temporary path. State
which owner creates it, when it should end and how it reaches the affected test.
Repair that owner or its isolation within authorized scope. Resetting the later
test solely to conceal an earlier leak leaves other consumers exposed.

Example: a test replaces a formatter for one output mode, then a later test
receives that formatter unexpectedly. Restore the replacement at its owner;
recheck the later test alone, the sufficient prefix and the original suite, plus
the first test's legitimate formatting behavior.

## Concurrent access breaks an invariant

Name the exact invariant and actors, then the suspected read/write ordering that
could violate it. If the host and existing harness support it, use a scoped
synchronization hook or barrier to select that ordering and observe the relevant
state. Assert the invariant on the baseline and candidate, not only successful
returns or the absence of exceptions. Keep temporary controls out of live use.

Example: two writers add different tags to one document; both tags must survive.
Arrange for both to read the initial document before either stores its change.
Check the final tags, repair the actual shared-state access, then recheck that
ordering, legitimate single-writer behavior and the original reported scenario.

A smaller timing window or a passing stress run does not prove synchronization.
Without a supported way to exercise the suspected ordering, report the causal
claim or repair as unproven and name the missing facility. Invent no host
capability and add no scheduling machinery merely to complete this experiment.

Carry the tested prediction, exact conditions, commands, observations, original
scenario result and remaining uncertainty in the existing handoff. Once the
cause is supported and repaired, finish the relevant checks; do not open a new
hypothesis round or acquire a retry or delivery controller.
