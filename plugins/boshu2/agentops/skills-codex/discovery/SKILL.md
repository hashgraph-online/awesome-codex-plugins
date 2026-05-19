---
name: discovery
description: 'Create dense execution packets.'
---
# $discovery - Dense Discovery Phase Adapter

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

Discovery turns a goal plus delegated child artifacts into one dense execution
packet for `$crank` and `$validation`.

## Strict Delegation Contract

Discovery delegates to `$brainstorm` (conditional), `$design` (conditional), `$research`, `$plan`, and `$pre-mortem` as **separate skill invocations**. Strict delegation is the default.

Reject these compression moves:

- inlining `$research` work;
- collapsing `$plan` into an inline decomposition;
- skipping `$pre-mortem`;
- replacing child skills with direct Codex sub-agent work.

See [`../shared/references/strict-delegation-contract.md`](../shared/references/strict-delegation-contract.md).

## Codex Lifecycle Guard

When this skill runs in Codex hookless mode (`CODEX_THREAD_ID` is set or
`CODEX_INTERNAL_ORIGINATOR_OVERRIDE` is `Codex Desktop`), ensure startup context
before entering the discovery DAG:

```bash
ao codex ensure-start 2>/dev/null || true
```

Leave `ao codex ensure-stop` to closeout skills; discovery owns startup only.

## Narrow Waist

Discovery does not carry raw child-skill output forward. It records artifact
paths, verdicts, and the six Context Density Rule fields:

| Field | Meaning |
|-------|---------|
| `intent` | Behavior or capability to produce |
| `boundary` | Bounded context, non-goals, write scope |
| `evidence` | Acceptance examples, tests, gates, verdicts |
| `decision` | Why this plan shape was chosen |
| `constraint` | Safety, runtime, token, and process limits |
| `next_action` | Exact `$crank` or follow-up command |

Everything else stays in child artifacts and is linked by path.

## Discovery To Plan Port

Use the [Skill Ports and Adapters](../../docs/contracts/skill-ports-and-adapters.md)
vocabulary for the boundary between Discovery and Plan:

| Boundary piece | Discovery contract |
|---|---|
| Inbound port | `shape_intent` from operator goal or BDD intent |
| Outbound port | `plan_slices` into `$plan` |
| Driving adapter | `$discovery` skill invocation |
| Driven adapter | `$plan` skill invocation plus bd/file persistence |
| Context packet | density block, artifact links, acceptance examples, non-goals, constraints |
| Guard adapter | `$pre-mortem` verdict before packet handoff |

```gherkin
Feature: Discovery hands dense intent to planning
  Scenario: Discovery delegates to Plan
    Given Discovery has a goal, research path, and design or brainstorm evidence
    When it crosses the `plan_slices` port
    Then it sends density fields and artifact links
    And it does not inline the Plan decomposition in Discovery prose
```

## Execution

Run the artifact-first DAG in [references/dag.md](references/dag.md). That
file owns the executable workflow, state shape, gate detail, per-step detail,
and the acceptance-criteria YAML contract.

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--auto` | on | Fully autonomous; inverse of `--interactive`. Passed through to `$research` and `$plan`. |
| `--interactive` | off | Human gates in research and plan. Does not affect pre-mortem. |
| `--skip-brainstorm` | auto | Skip brainstorm when the goal is already specific. |
| `--complexity=<level>` | auto | Force `fast`, `standard`, or `full`. |
| `--no-budget` | off | Disable phase time budgets. |
| `--no-scaffold` | off | Skip scaffold auto-invocation. |
| `--no-lifecycle` | off | Deprecated alias for `--no-scaffold`. |

## Output Specification

**Format:** compact markdown phase summary to stdout plus JSON execution packet
on disk.

**Files written:**

- `.agents/research/<topic-slug>.md` - research artifact path only
- `.agents/plans/YYYY-MM-DD-<goal-slug>.md` - plan document path only
- `.agents/council/YYYY-MM-DD-pre-mortem-<topic>.md` - pre-mortem verdict path only
- `.agents/rpi/execution-packet.json` - latest dense packet
- `.agents/rpi/runs/<run-id>/execution-packet.json` - per-run archive when `run_id` is set
- `.agents/rpi/phase-1-summary-YYYY-MM-DD-<goal-slug>.md` - compact discovery summary

## Completion Markers

```text
<promise>DONE</promise>      # Discovery complete, packet ready
<promise>BLOCKED</promise>   # Design or pre-mortem gate blocked
```

## References

- [references/dag.md](references/dag.md)
- [references/output-templates.md](references/output-templates.md)
- [references/phase-data-contracts.md](references/phase-data-contracts.md)
- [references/isolation-contract.md](references/isolation-contract.md)
- [references/complexity-auto-detect.md](references/complexity-auto-detect.md)
- [references/idempotency-and-resume.md](references/idempotency-and-resume.md)
- [references/phase-budgets.md](references/phase-budgets.md)
- [references/troubleshooting.md](references/troubleshooting.md)
