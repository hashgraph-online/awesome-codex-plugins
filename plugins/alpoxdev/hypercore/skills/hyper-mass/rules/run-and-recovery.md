# Run and Recovery

Read this rule before the first dispatch, before any resume, and before any recovery verb. The leader owns the run: it dispatches, journals, supervises, recovers, and decides when the goal is met. A node never decides that its own work ends the run.

## 1. Execution Modes

Pick the mode from what the runtime actually exposes, and record the choice in `run.created`.

| Mode | When | Behaviour |
|---|---|---|
| `native` | The runtime exposes a workflow or DAG capability | Submit this definition to it, subscribe to its events, and mirror every transition into `run.jsonl`. The graph file and journal stay the record of intent. |
| `waves` | Subagents or background agents exist, no native engine | The leader computes ready nodes and dispatches each wave itself. |
| `sequential` | Neither exists | The leader runs each node itself in topological order and records `parallelism: none`. The verification node records `verifier: self (no subagent capability)` and may return only deterministic verdicts; the settlement states `maker-checker not available`. |

- Native mode does not transfer ownership of the caps, the write scopes, or the verification contract. Check its state against `graph.json` rather than assuming the engine honoured the definition.
- When the native engine lacks a recovery verb, do not fake it. Use the closest supported action, journal the substitution, and name the gap in the settlement.
- In `sequential` mode the producer and the judge are the same worker. The verification node's handoff and its `node.completed` payload carry `verifier: self (no subagent capability)`, and its verdict is limited to deterministic checks: commands with captured output, file existence, and diffs. Never present a self-assessment as independent review.
- No mode may dispatch a node whose dependency has not completed and whose handoff has not been observed.

## 2. Topological Waves

For `waves` mode:

1. Read the journal and compute the ready set: pending nodes whose dependencies are all `completed` with an existing handoff.
2. Dispatch every ready node in one burst, up to the concurrency cap (8, or the runtime's lower limit).
3. Wait for the burst to settle. Do not poll node by node, and do independent leader work while it runs.
4. For each settled node, open its handoff, check the specific facts downstream depends on, then journal `node.completed` or `node.failed`.
5. Recompute the ready set and open the next wave.
6. Stop when the goal's criteria pass, the caps end the run, or a user-only decision blocks the next node.

Rules:

- A dependent node never dispatches before its ancestor's handoff exists on disk.
- Nodes past the concurrency cap are queued, not failed. Width costs queue time, never correctness.
- A wave that becomes empty while pending nodes remain is a stall, not completion: some dependency is unmet or a handoff is missing. Re-read the journal and fix the cause.
- The leader does not edit product files while acting as the orchestrator; it dispatches, verifies, and records.

## 3. The Journal

`run.jsonl` is append-only, one JSON object per line, in event order.

| Event | Written when | Payload |
|---|---|---|
| `run.created` | Before the first dispatch | `mode`, `nodes`, `definition_digest`, `justification` present |
| `run.resumed` | When an existing run is resumed | `from_event`, `reused_nodes` |
| `node.started` | Immediately before a dispatch | `node`, `attempt` |
| `node.completed` | After the handoff is opened and checked | `node`, `handoff`, `evidence` |
| `node.failed` | After the failure is observed | `node`, `attempt`, `error` |
| `node.retried` | When a retry is issued | `node`, `attempt`, `reason` |
| `node.sent` | When a steering message is delivered | `node`, `boundary` |
| `node.cancelled` | After a node's child is stopped during a run cancel | `node`, `reason` |
| `run.amended` | When a definition change is accepted | `changed` (node ids), `reason` |
| `run.settled` | When the run ends | `status`, `reason`, `criteria` |

Rules:

- Every line carries `ts` in ISO 8601 UTC and `event`.
- Write `node.started` before the dispatch; write `node.completed` and `node.failed` after observing the result, never from the node's own message alone.
- Never rewrite history. A correction is a new event.
- A node counts as completed only when its handoff exists and the leader has opened it. A reply that reports being blocked is a failure, not a completion.
- The journal is the resume source of truth. The native engine's status is a second opinion.

## 4. Resume

When a run directory already exists:

1. Read `graph.json` and every line of `run.jsonl` before touching any node.
2. Rebuild node state from the journal: completed nodes with an existing handoff stay completed and are never re-run; completed nodes whose handoff is missing are downgraded to `failed`; started-but-unsettled nodes return to pending; failed nodes keep their attempt count.
3. Journal `run.resumed` with the reused node ids.
4. Recompute the ready set and continue from the first incomplete wave.

| Situation | Action |
|---|---|
| Same key, same definition, interrupted | Resume; do not re-run completed nodes |
| Same key, changed definition | `amend`; only changed and added nodes plus their transitive dependents re-run |
| Same key, completed run, no changes | Return it untouched; nothing is scheduled |
| New key for the same work | A different run, not a retry; do not use it to recover a failure |
| Handoff missing for a completed node | Treat as failed and retry within the cap |

Do not resume by re-dispatching the whole graph. That repeats finished work and can double side effects.

## 5. Recovery Verbs

| Verb | Acts on | Rules |
|---|---|---|
| `retry` | Failed or cancelled nodes, or a named subset | Fresh attempt with the failure attached to the prompt. Dependents that were skipped re-enter only when their failed ancestor is in the retry set. Completed nodes are refused; `amend` is that path. Refused while the run is still active; wait for the wave to settle. Two retries per node. |
| `amend` | The definition | Fingerprint each node. Unchanged completed nodes keep their handoffs; only changed or added nodes plus their transitive dependents re-run. Amending a running node is refused. Three amends per run. Journal `run.amended` with the changed ids and the reason. |
| `send` | One running or resident node | Steer the node back inside its own `SCOPE`, or revive a finished resident child to continue with its context. It never changes the definition; a permanent change is an `amend`. A node that cannot be continued is refused, and `retry` is the remedy. |
| `cancel` | The whole run | Only to abandon the goal, with a reason. Elapsed time alone never justifies it. First stop and terminate every active node's child and journal `node.cancelled` for each one; only when no node is active write `run.settled` with `status: cancelled` and the reason. No node may keep writing after the settlement. |

- A retry is a fresh attempt, not a new key.
- An amend is a definition change, not a retry. Do not mix them to avoid the caps.
- A send is steering, not a new instruction set. If the node must work differently, amend its prompt.
- Every verb produces a journal line. Recovery without a record did not happen.

## 6. Supervision

Supervision is reading the work while it runs, not watching status.

On every wake, check each active node against its own `SCOPE`:

- writes outside its declared `writes`
- gold-plating past the `DELIVERABLE`
- circling one sub-problem instead of finishing
- reading the whole repository when its scope is one package
- taking on a neighboring node's job

On drift, `send` the exact boundary it crossed. A node that stays off course gets a tightened prompt through `retry` or `amend` once the wave settles. Drift corrected in wave 1 costs one message; drift found at synthesis costs the run.

## 7. Failure Playbook

| Symptom | Read it as | Action |
|---|---|---|
| One node failed | Its dependents are blocked; the rest of the graph is fine | Read the error, `retry` that node with the error in the prompt |
| Many nodes fail at start within seconds, never producing a handoff | Provider or route storm, not bad prompts | Stop launching, fix the route, then `retry`; completed nodes keep their results |
| Zero nodes running mid-wave | Queue backlog at the concurrency cap, not a stall | Check node states and wait; do not cancel or re-dispatch |
| A node says completed but the handoff is missing or empty | False completion | Mark it failed and retry; never pass an empty handoff downstream |
| A downstream node finds its input handoff missing | The edge did not carry data | FAIL that node and the run's criteria; do not let it proceed on assumptions |
| The same failure signature twice on the same node | The cause is not transient | Stop that node, report the signature, and amend or escalate |
| A retry or amend cap is reached | The run cannot converge within its bounds | Settle as `exhausted`, name the unmet criteria, and propose a split or a user decision |
| The native engine and the journal disagree | The engine is not the record | Re-read the handoffs, reconcile, and journal the resolution; never silently trust the engine |
| A node reports "confirmed" about its own work | An unverified claim | The verification node re-runs the real check |
| An irreversible action is about to dispatch | Approval is a node, not a sentence | Stop before the dispatch and ask the one user-only question |

## 8. Settle and Report

Settle only when one of these holds:

- every success criterion passes with captured evidence, and the verification node confirms it (`completed`)
- the caps or twice-repeated failure end the run (`exhausted` or `failed`)
- the user cancels the goal (`cancelled`)
- a user-only decision blocks the next node (`blocked`, waiting on one question)

The closing report carries: run key and directory, node outcomes, handoff paths, the verification command and its captured result, every retry and amend, the bounds reached, and residual risk. In `sequential` mode it also states `maker-checker not available`. Never report a run as complete because the last node returned.

## Sources

> Checked 2026-11-03.

| Claim | Source |
|---|---|
| Native workflow execution versus leader-run waves, the journal event set, resume from the journal, and the retry/amend/send/cancel semantics, adapted from the `mass-ulw` skill | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| Fan-out caps, the missing-branch rule, checkpoint resume, and the anti-pattern of a producer grading itself | `instructions/graph-engineering/GRAPH_ENGINEERING.md` |
| Numeric caps on stop conditions and budget exhaustion as `exhausted` rather than done | `instructions/loop-engineering/LOOP_ENGINEERING.md` |
| Evidence file or it did not happen, `SKIP` is not a pass, and a judge separate from the actor | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| The parent integrates and verifies, and receives artifacts rather than summaries | `instructions/context-engineering/references/parallel-workflows.md` |

### Evidence grade

`LOCAL` - this file states this package's run contract. Event names and verb rules are adapted from the upstream skill; the caps and the resume matrix are this package's choices, aligned with the family contract.
