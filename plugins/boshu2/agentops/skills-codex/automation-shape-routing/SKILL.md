---
name: automation-shape-routing
description: 'Front door for agent automation: choose'
---
# Automation Shape Routing

Choose the smallest execution shape that preserves the required evidence and
control. This skill routes; it does not build or start a substrate.

Ordered routing works because each rung is strictly cheaper to operate than the
next: if the smallest shape truly preserves the evidence and control the task
needs, every larger shape can only add coordination cost, never correctness.

Named failure mode — **substrate romance**: routing to persistent workers
because the topology is interesting, not because any deciding axis demands it.

Anti-pattern: starting the chosen substrate as part of routing "to save a
step". Corrective: return the one-line verdict and let the owner start under
its own authority.

## Critical Constraints

- **Route only; do not start a substrate. Why:** choosing an execution shape is
  a judgment step, while launching NTM, Agent Mail, or Gas City changes runtime
  state and requires separate operator authority.
- **Prefer the smallest shape that preserves evidence. Why:** persistence and
  coordination add recovery and ownership costs that one-shot work cannot repay.
- **Partition write scopes before choosing concurrency. Why:** a larger worker
  topology cannot make overlapping production writes safe.

## Route in order

1. **One deliverable?** Do it inline. Use a small in-session fresh-context
   fanout only when independent perspectives are the product. Do not create a
   reusable artifact for a one-off task.
2. **Reusable sequential procedure?** Use `skill-builder`.
3. **Must-never-regress constraint?** Route through `operationalize` to a gate.
4. **Fixed typed DAG, headless, no attach/steer?** Use `workflow-builder` only
   where that runtime is explicitly selected and available.
5. **Persistent, attachable roles over caller-supplied packets?** Use
   `agent-native`. NTM is the pane adapter; Agent Mail coordinates only
   explicitly selected live actors.
6. **Durable city of quests with GC-native supervision/store?** Route to
   `using-gc` only when the operator explicitly selects Gas City. GC is not an
   automatic fallback or an `ao` runtime enum.

## Deciding axes

| Axis | Lightweight choice | Escalated choice |
|---|---|---|
| lifetime | current turn | persistent/attachable worker |
| topology | one writer or bounded fanout | durable role graph |
| control | no mid-run steering | observe/nudge/replace |
| output | one artifact | reusable skill/workflow/gate |
| store | caller-owned packet set | operator-selected GC quest store |
| contention | one writer | partition, then Agent Mail reservation |

Parallelism buys independence, not guaranteed speed. Refuse persistent
orchestration for one-shot work, colliding write scopes, or a sequential chain
that has no exploitable concurrency.

## Handoff

Return exactly one of:

- `inline` or `bounded-fanout`
- `skill-builder`
- `workflow-builder`
- `agent-native` with a named reason persistent panes help
- `using-gc` with explicit operator choice
- `operationalize:gate`

Name the deciding axis and invoke the owner. Do not copy the delegated workflow
into this router.

## Output Specification

- **Artifact directory:** stdout only; this routing decision creates no file.
- **Filename convention:** none. Emit exactly one routing-verdict line.
- **Serialization/schema format:** `shape=<allowed-shape>; axis=<deciding-axis>;
  owner=<owning-skill>` using one of the shapes listed under Handoff.
- **Owner mapping:** `inline` and `bounded-fanout` use `current-agent`;
  `skill-builder`, `workflow-builder`, `agent-native`, and `using-gc` use the
  same value for owner; `operationalize:gate` uses `operationalize`.
- **Validator command:** validate a captured `$verdict` as exactly one line
  with the declared shape/owner mapping:

  ```bash
  printf '%s\n' "$verdict" | awk '
    NR > 1 { extra = 1 }
    {
      valid = ($0 ~ /^shape=(inline|bounded-fanout); axis=[^;]+; owner=current-agent$/ ||
               $0 ~ /^shape=skill-builder; axis=[^;]+; owner=skill-builder$/ ||
               $0 ~ /^shape=workflow-builder; axis=[^;]+; owner=workflow-builder$/ ||
               $0 ~ /^shape=agent-native; axis=[^;]+; owner=agent-native$/ ||
               $0 ~ /^shape=using-gc; axis=[^;]+; owner=using-gc$/ ||
               $0 ~ /^shape=operationalize:gate; axis=[^;]+; owner=operationalize$/)
    }
    END { exit !(NR == 1 && !extra && valid) }
  '
  ```
- **Downstream handoff:** invoke the named owner only after returning the verdict;
  `inline` remains in the current agent and `bounded-fanout` remains in-session.

## Quality Rubric

- [ ] The verdict names exactly one allowed shape and one deciding axis.
- [ ] Persistent or city-shaped routes cite the operator's explicit selection.
- [ ] Concurrent routes state that production write scopes do not overlap.
- [ ] The router delegates to the owner without copying or starting its workflow.
