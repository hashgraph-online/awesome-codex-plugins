# Service operations

Use the relevant procedure for an authorized operational change or investigation.
Start from the caller's service promises, affected users, environment, accepted
outcomes and action authority. Existing SLOs, observation windows, rollout rules
and recovery limits remain caller-owned. If a missing promise or permission
blocks a decision, report that gap; do not invent a target or authorize an action.
Safe read-only investigation can continue within scope. Read-only describes
the effect, not the intent: prefer a read-only identity or replica when one
exists. A read still loads a live system, so run production queries one at a
time against bounded, indexed selections, never scan a large table, and list a
query whose cost you cannot bound as not run.

Return observations, actions, failures and limits in the existing handoff.
Persist additional evidence only for a request or declared consumer at the
explicitly selected destination. Preserve necessary evidence before cleanup or
replacement, including unsuccessful attempts. These procedures create no
automatic knowledge capture, report, controller or required skill sequence.

## Reliability: observe the user outcome

Translate the service promise into a result observable through its public
interface: completion, correctness, freshness or latency as relevant. Reproduce
the reported harm with representative inputs and compare with the caller's
accepted outcome. Healthy processes, low CPU or backend success counters are
diagnostic signals; they cannot establish that the user received the right
result. Trace the failing boundary after observing the discrepancy.

When logs, traces or error events already exist, follow one concrete failing
request by its request, trace or event ID through every source in time order
before building a reproduction. Allow for clock skew across hosts, read each
instance an error tracker groups together, and treat an ID that stops
propagating as a finding. Preserve the identifiers and excerpts you need before
retention removes them.

State which users or request classes were exercised, the observation window,
eligible attempts and failures. Preserve partial or unknown coverage. A sampled
success cannot establish an unmeasured SLO or health of unexercised paths. When
new tests are needed, [Test](../../test/SKILL.md) owns test design; its
[real-service reference](../../test/references/real-service-e2e.md) covers checks
whose failure crosses a service boundary.

## A latency or freshness alert may have the wrong boundary

Before changing a timeout, monitor or pipeline, measure the named operation or
resource from the alert under relevant conditions. An aggregate run can hide
which member is late. Inspect the effective setting at the failing call site,
including overrides; a helper default may never govern that request.

Compare the observation with the caller's actual service threshold and the
monitor's notification rule. A maintenance action may legitimately start before
user harm warrants notification. Establish both policies before calling their
difference a defect; neither a monitor nor a health command automatically owns
the service promise. Preserve an agreed early-warning requirement.

Distinguish elapsed time from progress. A slow operation still advancing, a
blocked operation and a healthy operation reported late by a stale monitor need
different repairs. For example, if a refresh completes within its effective
budget while the page fires below the accepted freshness limit, investigate the
notification condition before extending the budget. If the resource actually
exceeds that limit, quieting the alert does not repair the service.

Carry the measured target, duration or freshness, effective setting location,
progress evidence and policy comparison in the existing handoff. Missing access
leaves the causal claim unproven; it does not justify a speculative rewrite.

## Delivery: use representative evidence before expanding

Confirm the candidate, target environment and permitted rollout extent against
the caller's delivery policy. Exercise the relevant user journeys and failure
paths against baseline and candidate under comparable conditions, using the
same accepted criteria. An idle canary with no eligible requests provides no
delivery evidence. Missing representative traffic, required checks or an
observation window leaves delivery unestablished; do not call absence of errors
a successful rollout.

Expand only when both the evidence and existing authority permit it. If a check
fails, stop expansion and use only authorized containment or recovery actions.
Before proposing rollback as recovery, inspect data, schema, configuration and
dependency compatibility and available restore evidence. A prior version alone
does not prove rollback is safe or that lost data can be restored.

If the change alters exposure, identities, permissions, data access or a trust
boundary, use the existing [Security](../../security/SKILL.md) owner for the
authorized assessment. Carry findings and gaps into the delivery decision;
a clean scan neither accepts risk nor grants deployment permission.

## Incident: mitigate, then verify recovery

Establish the user impact and capture the current symptom and relevant state
without delaying authorized urgent containment. Choose mitigation within the
caller's incident authority and available evidence; if the required action is
outside that authority, hand it to the responsible operator. Observe whether
mitigation actually reduces harm. Reduced harm or a healthy backend alone is
not verified recovery.

Test recovery through the affected user interface against the original service
promise and permitted observation window. Check residual work or state, such
as pending requests or incomplete writes, when relevant to that promise. Keep
each failed recovery attempt with its action, observed result and remaining
impact before making another change. Report partial recovery explicitly. Declare
user-visible recovery only for the outcomes actually verified, preserving the
failed attempts and any unresolved data or coverage limits.

## Resilience: bound the fault and prove restoration

Select one failure hypothesis and an authorized, isolated target. Before fault
injection, establish affected resources, maximum duration or attempts, stop
conditions and a restoration approach within the same authority. Unknown blast
radius or missing restoration authority blocks injection. Do not extend the
fault merely to obtain a passing result.

Observe the promised user behavior during the fault and stop at the agreed
bound or earlier stop condition. Remove the fault and verify both resource
restoration and the affected user outcomes, including deferred work when it
matters. A successful fault command or cleanup exit does not prove restoration.
If restoration fails, preserve the fault and recovery evidence, report the
remaining impact and use the incident procedure within existing authority.
One bounded experiment supports only the failure conditions it exercised.

## Toil: compare the full cost with leaving the process alone

Measure the existing process for the same workload and decision horizon as the
proposed change. Include human effort and machine cost where they matter, plus
the consequence of errors. Compare leaving it alone, a simpler change and the
proposed automation against that baseline.

Count creation and validation, ongoing operation and maintenance, failed runs,
repair and recovery work, including the effort of this trial. Separate shared
work from costs attributable to each option. Report measured units and workload
counts; label unavailable costs and assumptions instead of treating them as
zero. Faster subprocess time is not demonstrated labor or net cost savings.
Retain, revise or decline the change according to the caller's accepted outcome
and this comparison. A useful helper can be retained without claiming a saving
that the evidence does not establish.
