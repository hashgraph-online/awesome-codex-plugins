---
name: rpi
description: Run one bounded Plan, Implement, and fresh
---
# RPI

Run one experiment through three responsibilities and stop:

```text
Plan -> Implement -> fresh Validate -> report
```

RPI preserves the original intent and dispatches each core phase at most once.
It does not own retries, budgets, queues, claims, leases, Git, delivery, release,
closure, or the caller's next decision.

The pure [`scripts/run_once.py`](scripts/run_once.py) reference behavior makes
the dispatch and stop semantics executable without Git, `ao`, or a tracker.

## Contract

1. Invoke Plan once with the caller's intent. Preserve its exact
   `PlanPacket` and digest. If planning cannot produce a complete packet, report
   `NOT_PLANNED` and stop.
2. Invoke Implement once with that packet. It performs one bounded experiment
   and returns a `CandidatePacket`. If no candidate is built, report `NOT_BUILT`
   and stop.
3. Invoke Validate once in a context distinct from the candidate's
   `author_context_id`. Pass only the PlanPacket, CandidatePacket, factual
   evidence, validator identity, and freshness attestation.
4. Return the durable `verdict.v2` reference and a short report. Stop regardless
   of `PASS`, `FAIL`, or `NOT_PROVEN`.

`NOT_PLANNED` and `NOT_BUILT` are report statuses, never semantic verdicts.
A caller may later create a `revision-packet.v1` and start a new invocation;
RPI never creates, selects, or consumes a revision automatically.

## Invariants

- Acceptance and its digest do not change between phases.
- The candidate reports complete changed-path coverage or Validate returns
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
plan_packet_digest: <sha256 or null>
subject_manifest_digest: <sha256 or null>
verdict_ref: <path or null>
verdict_digest: <sha256 or null>
checked: []
not_checked: []
```

Do not append a next action. The caller owns continuation.
