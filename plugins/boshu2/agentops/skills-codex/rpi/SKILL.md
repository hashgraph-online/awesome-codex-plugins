---
name: rpi
description: 'Coordinate one RPI traversal: one bounded Triggers: "run rpi", "run one traversal", "execute this plan", orchestration or worker delegation that implements changes.'
---
# RPI

Run one experiment from the caller's existing intent source through three
responsibilities and stop:

```text
anti-ceremony guard -> Plan -> Implement -> fresh Validate -> report
```

On `CONTINUE`, the core path remains Plan -> Implement -> fresh Validate ->
report. RPI invokes the guard exactly once before Plan. It preserves the
original intent and dispatches each core phase at most once.
It does not own retries, budgets, queues, claims, leases, Git, delivery, release,
closure, or the caller's next decision.

The pure [`scripts/run_once.py`](scripts/run_once.py) reference behavior makes
the dispatch and stop semantics executable without Git, `ao`, or a tracker.

## Admission and phase lock

RPI activates for any request shaped as plan-execute-verify work —
orchestration, worker delegation, "execute this plan", or an explicit
Plan -> Implement -> Validate ask — whenever the goal includes changing the
subject. The caller does not have to name RPI. Research-, audit-, and
review-only delegation is not RPI admission: it produces evidence for a
caller, has no implementation candidate, and never earns a verdict.

Once the caller has accepted a plan — including a duel or design synthesis —
Plan is closed for that intent. Every subsequent lane must return
implementation evidence: diffs, commits, test results, or factual receipts.
Dispatching another planning, audit, or review lane over the same intent
requires new explicit caller authorization; a review comment is never that
authorization by itself.

## Contract

1. Invoke anti-ceremony's artifact-free quick guard once with the caller
   outcome, proposed process work, remaining proof, and stop condition. On
   `STOP`, dispatch no core phase, report `NOT_PLANNED` with the guard's
   one-sentence reason, and stop. On `CONTINUE`, proceed without adding an
   artifact, retry, repair, delivery, tracker, or Git action.
2. Resolve the existing bead or caller intent. Invoke Plan once only if that
   source needs shaping; Plan updates the same source or proposes an amendment.
   It creates no AgentOps packet. Preserve a durable caller-owned source by
   reference and digest; only when no durable source exists does the runtime
   snapshot the exact resolved source bytes under their digest before
   dispatching Implement or a fresh Validate context. If usable intent cannot
   be established, report `NOT_PLANNED` and stop.
3. Invoke Implement once with the resolved intent. It performs one bounded
   experiment; the runtime derives subject identity and check receipts. If no
   subject is built, report `NOT_BUILT` and stop.
4. Invoke Validate once in a context distinct from the author's context. Pass
   the intent reference and digest, exact subject manifest, factual receipts,
   validator identity, and freshness attestation.
5. Return the fresh validation result and a short report. Persist and link
   `verdict.v2` only when the caller requests machine-readable evidence or a
   declared downstream consumer requires it. Stop regardless of `PASS`, `FAIL`,
   or `NOT_PROVEN`.

`NOT_PLANNED` and `NOT_BUILT` are report statuses, never semantic verdicts.
A caller may revise the bead or caller intent and start a new invocation. RPI
never creates a parallel revision artifact or selects the next work itself.

## Anti-ceremony boundary

The hard [`anti-ceremony`](../anti-ceremony/SKILL.md) dependency owns the quick
guard and its explicit-only full honesty audit. RPI does not duplicate that
judgment or turn each component, gate failure, or specialist comment into a new
planning artifact. A terminal caller goal may remain one bounded experiment
across several source owners when they serve one outcome and one acceptance
boundary.

If control artifacts or fresh-validation cycles are multiplying faster than
implementation evidence, stop dispatching more lanes. Return to one
outcome-level intent and continue with targeted deterministic checks, reserving
the full integration check and fresh validation for the frozen subject. This
changes orchestration cost, never acceptance, exact identity, fail-closed
scope, or validation authority.

## Spiral breaker

The spiral breaker fires when two consecutive control artifacts (plans, audits,
reviews, prompts, reports) contain no new implementation evidence. Terminate the
run and report `NOT_BUILT` when no implementation subject exists; when a subject
exists, stop and report its current status without dispatching another lane or
repair revision. RPI owns no lane budget, repair budget, or retry policy.

## Delegation boundaries

Delegate with minimal context: a lane receives the frozen intent reference and
the established facts it needs, never the orchestrator's full conversation
history. If a lane cannot proceed from the intent alone, report that the plan
failed the fresh-context test and stop; do not pad it with chat transcript or
start another planning lane without explicit caller authorization.

Lanes whose write scopes share a regen surface (the same generated outputs,
mirrors, or manifests) serialize; only lanes with disjoint source scopes and
disjoint regen surfaces may run in parallel.

## Invariants

- Acceptance and its runtime-derived digest do not change between phases.
- The anti-ceremony guard runs once before Plan; `STOP` dispatches none of Plan,
  Implement, or Validate, while `CONTINUE` preserves their order.
- The runtime derives complete changed-path coverage or Validate returns
  `NOT_PROVEN`.
- A proven change outside `write_scope` makes the verdict `FAIL`.
- PASS requires nonempty distinct author and validator context IDs plus an
  explicit freshness attestation.
- Optional Premortem, Postmortem, Council, genie, factory, tracker, and runtime
  adapters are caller-selected. They do not alter phase order or core outcomes.
  When a factory adapter is selected, work enters it through that factory's
  coordinator (for Gas City, the Mayor — see
  [using-gc](../using-gc/SKILL.md)); RPI hands over intent and never dispatches
  factory runs itself.
- Learn is an optional later consumer of verdict collections and is not part of
  this invocation.

## Report

RPI has one required report surface and one optional representation:

1. **Interactive response:** return the result to the caller in natural
   language. This is the default assistant response.
2. **Machine artifact:** return or persist the exact `rpi-report.v1` object
   only when the caller requests machine-readable evidence or a declared
   adapter consumes it. The schema ships in a repo checkout at
   `schemas/rpi-report.v1.schema.json`; the minimal required shape is:

   ```json
   {
     "schema_version": "rpi-report.v1",
     "status": "PASS",
     "intent_ref": "<durable-source-ref-or-fallback-snapshot-ref>",
     "acceptance_digest": "<64-hex-char-sha256-or-null>",
     "subject_manifest_digest": "<64-hex-char-sha256-or-null>",
     "verdict_ref": "<verdict-location-or-null>",
     "verdict_digest": "<64-hex-char-sha256-or-null>",
     "checked": ["<criterion satisfied by evidence>"],
     "not_checked": ["<criterion not covered>"]
   }
   ```

   `intent_ref` remains required: it names the durable caller-owned source when
   one exists, otherwise the content-addressed fallback snapshot. `status` is
   one of `PASS | FAIL | NOT_PROVEN | NOT_PLANNED | NOT_BUILT`; the three digest
   fields, when present, are 64-character lowercase hex SHA-256 strings;
   `checked` and `not_checked` are arrays of strings. All nine keys are required
   (use `null` for an inapplicable ref or digest), and no
   additional properties are allowed.

Lead the interactive response with the status and one sentence stating the
caller-visible outcome. Lead with the subject, not the process: production
paths changed, commits, test results, and acceptance criteria satisfied or
remaining. A rising artifact count over an unchanged subject is a stop
signal, not progress. Follow with only the strongest proof, any material
unchecked scope, and a clickable verdict reference when one exists. Name why
no subject exists for `NOT_PLANNED` or `NOT_BUILT`; for a guard `STOP`, use its
one-sentence reason. Keep the response to one short paragraph or at most four
bullets.

When no machine artifact was requested, do not create a hidden one. Raw digests,
schema fields, and exhaustive check lists stay out of the interactive response
unless an integrity failure makes one necessary to explain the result.

Do not append a next action. The caller owns continuation.
