---
name: rpi
description: Run one bounded Plan, Implement, and fresh
---
# RPI

Run one experiment from the caller's existing intent source through three
responsibilities and stop:

```text
Plan -> Implement -> fresh Validate -> report
```

RPI preserves the original intent and dispatches each core phase at most once.
It does not own retries, budgets, queues, claims, leases, Git, delivery, release,
closure, or the caller's next decision.

The pure [`scripts/run_once.py`](scripts/run_once.py) reference behavior makes
the dispatch and stop semantics executable without Git, `ao`, or a tracker.

## Contract

1. Resolve the existing bead or caller intent. Invoke Plan once only if that
   source needs shaping; Plan updates the same source or proposes an amendment.
   It creates no AgentOps packet. The runtime snapshots the exact resolved
   source bytes under their digest, including when the conversation is the only
   source, before dispatching Implement or a fresh Validate context. If usable
   intent cannot be established, report `NOT_PLANNED` and stop.
2. Invoke Implement once with the resolved intent. It performs one bounded
   experiment; the runtime derives subject identity and check receipts. If no
   subject is built, report `NOT_BUILT` and stop.
3. Invoke Validate once in a context distinct from the author's context. Pass
   the intent reference and digest, exact subject manifest, factual receipts,
   validator identity, and freshness attestation.
4. Return the durable `verdict.v2` reference and a short report. Stop regardless
   of `PASS`, `FAIL`, or `NOT_PROVEN`.

`NOT_PLANNED` and `NOT_BUILT` are report statuses, never semantic verdicts.
A caller may revise the bead or caller intent and start a new invocation. RPI
never creates a parallel revision artifact or selects the next work itself.

## Proportionality guard

RPI does not turn each component, gate failure, or specialist comment into a
new planning artifact. A terminal caller goal
may remain one bounded experiment across several source owners when they serve
one outcome and one acceptance boundary.

If control artifacts or fresh-validation cycles are multiplying faster than
implementation evidence, stop dispatching more lanes. Return to one
outcome-level intent and continue with targeted deterministic checks, reserving
the full integration check and fresh verdict for the frozen subject. This
changes orchestration cost, never acceptance, exact identity, fail-closed
scope, or verdict authority.

## Continuation envelope

Before dispatching any lane, the orchestration declares its envelope: a budget
(maximum lanes per wave, maximum repair revisions per wave) and a checkpoint
rule — the second non-PASS outcome on one intent stops that lane and returns
to the caller instead of dispatching another attempt. An orchestration without
a declared envelope does not converge; it accretes lanes. The 2026-07-15
heal-skill fold ran three intent revisions
(`.agents/ao/intents/sha256/26a4f2be...eb48` lineage) and a `NOT_PROVEN` then
PASS verdict pair (`.agents/ao/verdicts/sha256/b6e759dd...cb6a`,
`e9b6cdb8...37b9`) before an enforced two-stop checkpoint ended the wave.

Delegate with minimal context: a lane receives the frozen intent reference and
the established facts it needs, never the orchestrator's full conversation
history. If a lane cannot proceed from the intent alone, the plan failed the
fresh-context test and should be repaired at the source, not padded with chat
transcript.

Lanes whose write scopes share a regen surface (the same generated outputs,
mirrors, or manifests) serialize; only lanes with disjoint source scopes and
disjoint regen surfaces may run in parallel.

## Invariants

- Acceptance and its runtime-derived digest do not change between phases.
- The runtime derives complete changed-path coverage or Validate returns
  `NOT_PROVEN`.
- A proven change outside `write_scope` makes the verdict `FAIL`.
- PASS requires nonempty distinct author and validator context IDs plus an
  explicit freshness attestation.
- Optional Premortem, Postmortem, Council, genie, factory, tracker, and runtime
  adapters are caller-selected. They do not alter phase order or core outcomes.
- Learn is an optional later consumer of verdict collections and is not part of
  this invocation.

## Report

Return exactly the useful boundary facts:

```yaml
schema_version: rpi-report.v1
status: PASS | FAIL | NOT_PROVEN | NOT_PLANNED | NOT_BUILT
intent_ref: <bead, issue, conversation, or null>
acceptance_digest: <sha256 or null>
subject_manifest_digest: <sha256 or null>
verdict_ref: <path or null>
verdict_digest: <sha256 or null>
checked: []
not_checked: []
```

Do not append a next action. The caller owns continuation.
