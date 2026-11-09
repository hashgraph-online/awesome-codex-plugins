# Graph Planning

Read this rule before defining any node, and again before every `amend`. A graph defined without it collapses into a few oversized nodes with no verification; every section here exists because that failure has a name.

Planning is not writing nodes. The leader writes the screen, the goal, the justification, and the topology in one pass, then executes that plan. When reality forces a change, the leader replans out loud and records an `amend` instead of drifting node by node.

## 1. Screen First

A graph is not the default form of delegation. Decide before planning.

| Condition | Verdict |
|---|---|
| Two or more tasks where some must finish before others start | graph |
| A fan-out whose results must join through one review or verification | graph |
| Tasks independent with no ordering | plain parallel subagents, no graph |
| One task, or one coherent judgment needing the whole problem in view | run it directly |
| Every worker needs the same broad context, or subtasks depend on each other heavily | one agent, no fan-out |
| Output is a written plan file executed checkbox by checkbox | out of scope |
| Output is a research report | out of scope |
| The job spans several phases or checkpoints | one run per phase, chained |

Name the ceiling the graph removes: context exhaustion, serialized latency, missing isolation, or self-grading. A graph that removes none of them is decoration, and the honest action is to run the work directly.

## 2. Goal Before Start

Every run is goal-bound.

- The objective names the deliverable the graph produces, in one sentence.
- Each success criterion names the evidence that proves it: the command and its expected result, the file and what must be in it, or the endpoint and its observable response.
- The run ends when the criteria pass with captured evidence, never when the last node reports.
- When an outer execution loop already owns the goal, register no second goal; the run inherits that goal and its evidence.
- A user-only decision is asked before the run that depends on it starts: irreversible or destructive change, spend, credentials or account access, or an external send or publish. A timed-out, dismissed, or assumed answer is not an answer. At most one question at a time, with a recommended option.

## 3. One Phase Per Run

A phase is the unit a loop checkpoints: one goal criterion, one worktree, one evidence gate, one plan wave. A harvest wave or a pipeline stage is a phase; "research it, implement it, and ship it" is three phases and three runs.

- The first run's verification output is the input to the decision to start the second run.
- Each run has its own key, goal, criteria, graph, and journal.
- Chaining runs is the leader's job between settlements; the graph itself has no branch construct.

## 4. Justification Record

Write the justification object inside `graph.json` before `run.created`. All six fields are required, and the self-check refuses to start while one is empty.

| Field | Content |
|---|---|
| `ceiling_removed` | Which ceiling the graph removes, or why the graph still pays for itself |
| `topology` | The 1-6 components and how the nodes trace to them |
| `state` | What the graph carries between nodes (handoff files, repository state) and what it deliberately does not |
| `bounds` | Caps in force, including any user-given cap that overrides the default |
| `approval` | Which nodes carry an irreversible or user-only action, and the answer or `not required` |
| `rollback` | How the run is undone if the result fails the criteria: revert paths, discard worktree, leave files untouched |

The record is the answer to "why is this a graph, and what makes it safe to run". It is not prose in chat; it is part of the definition.

## 5. Topology Lock

Before writing any node, enumerate the 1-6 top-level components that can each succeed or fail independently. Every node traces to exactly one component.

- Do not collapse a multi-component request into one blob node because it "looks small".
- Do not invent components the request does not have.
- If the request has more than six components, the phases are being mixed: split by phase first.

## 6. Split First, Route Second

The default question is not "which tier does this chunk need" but "how does this chunk become more `low` nodes".

Split when:

- the pieces are independent and safe to run at the same time
- their write scopes are disjoint
- each piece has a self-contained prompt and a check that decides pass or fail on its own

Do not split when:

- the pieces would share a write scope that cannot be untangled; serialize or merge instead
- the work is one coherent judgment that needs the whole problem in view; splitting yields confident partial answers
- the pieces are so small that briefing costs more than the work; fold them into a neighbor

A two-node graph with a real dependency is legitimate. A graph with fewer than three nodes and no real dependency is not a graph; use plain parallel or a direct run.

## 7. Tiers and Specialty Kinds

Tier is difficulty, not importance.

| Tier | Use |
|---|---|
| `low` | The default: mechanical, single-file, or pattern-following work |
| `medium` | A standard multi-file change with real integration surface |
| `high` | One cohesive hard problem that cannot be split without losing the whole-problem context |

- Every non-`low` tier carries a one-line reason that could be said out loud ("touches six files across three packages").
- At most one `high` node per graph, and only when the rest of the graph depends on that judgment.
- A graph whose every node is `high` is a routing failure: it pays the most expensive worker for mechanical lanes.

`kind` is chosen by the kind of work, never by difficulty: `writing` for docs and prose, `visual` for UI and styling, `git` for repository operations. A node that needs no specialty omits `kind`.

## 8. Implementation and Its Proof Stay Together

One node owns one deliverable end to end: the change and the check that proves it. A node that only writes and a node that only tests serialize on the same files and double the coordination cost.

The exception is the terminal verification node, which is separate because it grades the whole graph, not its own work.

## 9. Fan-Out, Then Fan-In Through One Review

The default shape is N producers in parallel, then one node that depends on all of them and produces the join.

- When every node of the next wave would depend on every node of the previous, never draw the full edge grid. Insert one review node between the waves.
- A node that consumes only part of a wave gets its own review on that branch and starts when that branch clears, not when the whole wave does.
- The join declares its output shape: the file it writes, the table it returns, or the verdict it records. "Merge everything" is not a shape.
- Mass harvests shard items into batch nodes sized by the report contract; each node collects a bounded batch and writes ONE bounded file report. The node count is `ceil(total_items / items_per_batch)`, and synthesis reads the per-batch reports, never raw node outputs. Past one run's cap, split into concurrent runs each with its own aggregator.

## 9.1 Digest Reduction Over Batch Nodes

Any reducer that joins more than one batch emits a digest file, and the final reducer reads digests only, never raw node output.

- The digest file states its size bound: the package default is 5,000 tokens; a run MAY state a different bound in its `graph.json` justification, and the digest then obeys that stated bound.
- Every claim in the digest cites the handoff path it came from. A digest claim without a handoff citation fails the self-check.
- Cluster reducers write one digest per cluster; the final reducer consumes only those digests. A synthesis node that reads raw node output directly (or a batch node's full handoff) instead of the digests fails the self-check.

Prefer `solutionSpace` on a node when the work has a list of approaches the worker may pick from but **MUST** stay inside: the node prompt lists it and an approach outside the list fails the self-check rather than passing silently. `resolvedModel` is an observation, not a plan: write it only from the observed result, never predicted from the tier.

## 10. Write Scopes and the Handoff Channel

`dependsOn` orders; files carry the data.

- `writes` lists the exact paths or globs a node may change, including its handoff file.
- No two nodes that can run in parallel may share a write path. Chain them with a dependency or merge them.
- Every node writes its handoff to `.hyper/mass/<run-key>/nodes/<node-id>.md` as its last act.
- A downstream node names that exact path in `reads` and its prompt, and its prompt treats a missing file as FAIL, not as an empty result.
- Add an edge only when the downstream node consumes what the upstream node writes. A fact the leader already knows goes into the prompt with no edge.
- Every prompt still stands alone: no "as discussed above", no variable the node cannot resolve.

## 11. Node Prompt Contract

Each `prompt` carries these markers, in this order:

```text
TASK: one imperative sentence naming the deliverable.
DELIVERABLE: the concrete artifact returned: files changed, report shape, evidence produced.
SCOPE: what the node may read and write, with exact paths, stated as a hard boundary. Name what is out of scope when a neighboring node owns it.
VERIFY: the check the node runs on its own work: the literal command and its expected result.
STOP WHEN: the single observable condition that ends the node's run.
```

Rules that make prompts obeyed:

- Self-contained: paste exact paths, facts, and constraints into the prompt.
- Minimum sufficient context: every pasted fact must change what the node does.
- Binary observables: "exit code 0 and `dist/index.js` exists", never "check it works".
- Positive framing: say what to do; reserve NEVER and ONLY for true invariants.
- One role per node: a producer does not grade its own work.
- The handoff path appears in `DELIVERABLE` and in `SCOPE`.

## 12. Verification Node

Every graph that changes code ends with at least one verification node that depends on all producer nodes.

- It runs the real check: the test command, the build, the endpoint call, the rendered page.
- Its prompt names the exact invocation and the binary observable that decides pass or fail.
- It reports captured output, not a summary of what it believes happened.
- It checks that every handoff its dependencies promised exists and is non-empty.
- A downstream node that builds on an upstream result re-checks the specific facts it depends on before trusting them.
- The producer and the judge are different nodes; the judge receives the artifact and the criteria, not the producer's summary.
- When no separate worker exists (`sequential` mode), the verification node records `verifier: self (no subagent capability)` in its handoff, returns only deterministic verdicts (a command with captured output, file existence, a diff), and never presents self-assessment as independent review. The settlement says `maker-checker not available`.

## 13. Self-Check Before Start

Refuse to write `run.created` until every line passes:

- [ ] One phase, one objective, and success criteria with evidence.
- [ ] Justification has all six fields.
- [ ] 1-6 components, and every node traces to one.
- [ ] Unique ids, every `dependsOn` id exists, no cycle.
- [ ] At least one runnable node in every wave.
- [ ] Parallel-capable nodes have disjoint `writes`.
- [ ] Every node has a `handoff` under the run directory.
- [ ] A terminal verification or review node depends on every producer.
- [ ] At most one `high` node, and every non-`low` tier has a reason.
- [ ] Caps respected; otherwise the work is split under a new key.
- [ ] No synthesis node consumes unbounded raw node output: every reducer over more than one batch emits a digest with a stated size bound and handoff citations, and the final reducer reads only digests.
- [ ] Every node that declares `solutionSpace` lists it in the prompt, and the approach it reports using is checked against the list; every `resolvedModel` value came from an observed result.

The same key with the same definition is a resume. A changed definition under an old key is a conflict and goes through `amend`. A different key is a different run, never a retry.

## Sources

> Checked 2026-11-09.

| Claim | Source |
|---|---|
| The decomposition doctrine, category routing ladder, write-scope rules, node prompt contract, verification wave, and mass-harvest sharding, adapted from the planning reference of the `mass-ulw` skill | <https://github.com/code-yeongyu/oh-my-openagent/tree/0d80470e4201925727e88afbafcdf24d7801a588> |
| The screen before graphing, the ceiling a graph removes, approval as a structural node, a verifier separate from the producer, and fan-out caps | `instructions/graph-engineering/GRAPH_ENGINEERING.md` |
| The delegation prompt fields and the parent that integrates and verifies | `instructions/context-engineering/references/parallel-workflows.md` |
| Evidence file or it did not happen, and the judge receiving the artifact and criteria rather than the worker's summary | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| The tier ladder and the 32-node, 8-concurrent, 2-retry, 3-amend bounds | family contract, 2026-11-03, and `instructions/loop-engineering/LOOP_ENGINEERING.md` |
| Digest reduction after batch fan-out: one digest file per reducer over more than one batch, a stated token bound (default 5,000), handoff citations on every claim, and the final reducer reading digests only; node `solutionSpace` bounds and approach-outside-list self-check failure; `resolvedModel` recorded from observed results only | `dbc-hbin/omp-ulw @ 74df40f` (2026-11-09), re-authored; the source repository has no license file and nothing was copied |

### Evidence grade

`LOCAL` - this file states this package's planning contract. The doctrine is adapted from the upstream skill; the tiers, the caps, and the justification record are this package's choices, aligned with the family contract.
