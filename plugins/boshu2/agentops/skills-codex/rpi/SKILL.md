---
name: rpi
description: "Run RPI."
---

# $rpi - Full Lifecycle Orchestrator

> Quick ref: `$discovery` -> `$crank` -> `$validate`, then report.

**Execute this workflow. Do not only describe it.** RPI is autonomous unless
`--interactive` is set. The user touchpoint is after validation, or after a
real blocked state exhausts retries. Read
[references/autonomous-execution.md](references/autonomous-execution.md) when
you need the full autonomy contract.

When an external executor fails but the code surface may still be valid, read
[references/codex-executor.md](references/codex-executor.md) and recover through
Codex direct checks before declaring a source-level regression.

## Codex Lifecycle Guard

When this skill runs in Codex hookless mode (`CODEX_THREAD_ID` is set or
`CODEX_INTERNAL_ORIGINATOR_OVERRIDE` is `Codex Desktop`), run:

```bash
ao codex ensure-start 2>/dev/null || true
```

Let `$validate`, `$post-mortem`, or `$handoff` own hookless closeout through
`ao codex ensure-stop`.

## Core Contract

RPI delegates via `$discovery`, `$crank`, `$validate` as **separate skill invocations**.
Keep strict delegation on by default; do not compress phases, replace phase
skills with direct agent spawns, or skip `$validate`. Read
[../shared/references/strict-delegation-contract.md](../shared/references/strict-delegation-contract.md)
for the full anti-compression contract.

When the runtime supports phase isolation, keep `$rpi` visible in the main
session and run each phase contract through isolated transport: phase skill
name in, bounded handoff artifact in, phase artifact/verdict/next action out.
The transport may be a daemon job, process runner, or subagent wrapper, but it
must execute the declared phase skill contract rather than doing phase work
directly. See [references/isolation-contract.md](references/isolation-contract.md).

## Context Density Rule

At every phase boundary, preserve only context that carries intent, boundary,
evidence, decision, constraint, or next action. Omit or link anything else.
The domain entry is `../domain/references/context-density-rule.md`.

RPI owns one lifecycle objective across all phases. Preserve the discovered
`epic_id` when present; otherwise preserve the original goal and execution
packet objective. A child bead or one ready slice is context, not a replacement
objective. `<promise>PARTIAL</promise>` from `$crank` means retry Phase 2 on the
same objective.

Preserve the [Intent-to-Loop Hexagon](../../docs/architecture/intent-to-loop-hexagon.md)
boundary as the objective crosses `shape_intent`, `persist_intent`,
`plan_slices`, `execute_wave`, `validate_acceptance`, and `record_evidence`.

## Route And Classify

1. Create `.agents/rpi/`.
2. Resolve `--from`:
   - default, `research`, `plan`, `pre-mortem`, `brainstorm` -> discovery
   - `implementation` or `crank` -> implementation
   - `validation`, `vibe`, or `post-mortem` -> validation
3. If the input is a bead and `--from` is absent, resolve it with `br show`:
   - epic -> implementation with that epic
   - child with parent -> implementation with the parent epic
4. Classify complexity:
   - `fast`: short/simple goal or `--fast-path`
   - `standard`: medium goal or one scope keyword
   - `full`: `--deep`, complex-operation keyword, 2+ scope keywords, or >120 chars
5. Log `RPI mode: rpi-phased (complexity: <level>)`.

Track state compactly:

```text
rpi_state = {
  goal: "<goal string>",
  epic_id: null,
  phase: "<discovery|implementation|validation>",
  complexity: "<fast|standard|full>",
  test_first: <true by default; false only when --no-test-first>,
  cycle: 1,
  verdicts: {}
}
```

## Phase DAG

Enter at the routed phase and run every phase after it.

1. **Discovery:** invoke `$discovery <goal> [--interactive] --complexity=<level>`
   directly or through phase-isolated skill transport.
   On DONE, read `.agents/rpi/execution-packet.json` or the run archive and
   preserve its objective spine. On BLOCKED, stop with the discovery verdict.
2. **Implementation:** invoke `$crank <epic-id>` when the packet has `epic_id`;
   otherwise invoke `$crank .agents/rpi/execution-packet.json`, directly or
   through phase-isolated skill transport. Pass `--test-first` or
   `--no-test-first` through. On DONE, record `ao ratchet record implement
   2>/dev/null || true` and continue. On PARTIAL or BLOCKED, retry the same
   objective up to 3 total attempts.
3. **Validation:** invoke `$validate <epic-id> --complexity=<level>` when an
   epic exists; otherwise invoke `$validate --complexity=<level>`, directly
   or through phase-isolated skill transport. Add `--strict-surfaces` when
   `--quality` is set. On FAIL, extract findings, re-run `$crank` on the same
   objective, then re-run `$validate`, up to 3 total validation attempts. On
   DONE, record `ao ratchet record vibe 2>/dev/null || true`.
4. **Report:** summarize phase verdicts and epic status using
   [references/report-template.md](references/report-template.md). With
   `--loop`, restart from discovery on FAIL while `cycle < max_cycles`. With
   `--spawn-next`, read `.agents/rpi/next-work.jsonl` and suggest the next
   command without invoking it. Before emitting the report, apply the Context
   Density Rule: every line should carry intent, boundary, evidence, decision,
   constraint, or next action.

## Phase Data Contract

The execution packet carries the repo execution profile through
`contract_surfaces`, `done_criteria`, and queue claim/finalize metadata. Keep
the latest alias at `.agents/rpi/execution-packet.json` and read
[references/phase-data-contracts.md](references/phase-data-contracts.md) for
schemas and archive paths.

## Complexity-Scaled Gates

### Pre-mortem
- `complexity == "low"` or `"fast"`: inline review, no spawning (`--quick`)
- `complexity == "medium"` or `"standard"`: inline fast default (`--quick`)
- `complexity == "high"` or `"full"`: full council, 2-judge minimum; max 3 total attempts

### Final Vibe
- `complexity == "low"` or `"fast"`: inline review, no spawning (`--quick`)
- `complexity == "medium"` or `"standard"`: inline fast default (`--quick`)
- `complexity == "high"` or `"full"`: full council, 2-judge minimum; max 3 total attempts

### Post-mortem (STEP 2)
- `complexity == "low"` or `"fast"`: inline review, no spawning (`--quick`)
- `complexity == "medium"` or `"standard"`: inline fast default (`--quick`)
- `complexity == "high"` or `"full"`: full council, 2-judge minimum; max 3 total attempts

## Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `--from=<phase>` | discovery | Start at discovery, implementation, or validation |
| `--interactive` | off | Human gates in discovery/validate |
| `--auto` | on | Fully autonomous default |
| `--loop --max-cycles=<n>` | off / 3 | Iterate when validation fails |
| `--spawn-next` | off | Surface follow-up work after reporting |
| `--test-first` | on | Pass strict-quality preference to `$crank` |
| `--no-test-first` | off | Explicitly opt out of strict-quality |
| `--fast-path` / `--deep` | auto | Force fast or full complexity |
| `--quality` | off | Make validation strict surfaces blocking |
| `--dry-run` / `--no-budget` | off | Report only, or disable phase time budgets |

## Examples

**User says:** `$rpi "add user authentication"`
Run discovery, implementation, validation, then report.

**User says:** `$rpi --from=implementation ag-23k`
Resolve the bead scope, run implementation and validation, then report.

**User says:** `$rpi --deep "refactor payment module"`
Use full council gates across the lifecycle.

Read [references/examples.md](references/examples.md) for resume,
interactive, and loop examples.

## Troubleshooting

| Problem | Response |
|---------|----------|
| Discovery BLOCKED | Stop and report discovery's manual-intervention reason |
| `$crank` returns PARTIAL | Retry `$crank` on the same objective; do not narrow to a child slice |
| Validation FAIL | Re-crank with findings, then re-validate, up to 3 total attempts |
| Packet shape unclear | Read [references/phase-data-contracts.md](references/phase-data-contracts.md) |
| External executor fails | Read [references/codex-executor.md](references/codex-executor.md), run direct Codex validation, and only create follow-up work for reproducible source failures |

## Related skills

- $using-atm — out-of-session ATM substrate for running whole $rpi loops over a bead queue.

## Reference Documents

- [references/autonomous-execution.md](references/autonomous-execution.md)
- [references/complexity-scaling.md](references/complexity-scaling.md)
- [references/context-windowing.md](references/context-windowing.md)
- [references/codex-executor.md](references/codex-executor.md)
- [references/error-handling.md](references/error-handling.md)
- [references/examples.md](references/examples.md)
- [references/gate-retry-logic.md](references/gate-retry-logic.md)
- [references/gate4-loop-and-spawn.md](references/gate4-loop-and-spawn.md)
- [references/isolation-contract.md](references/isolation-contract.md)
- [references/phase-budgets.md](references/phase-budgets.md)
- [references/phase-data-contracts.md](references/phase-data-contracts.md)
- [references/report-template.md](references/report-template.md)
- [references/troubleshooting.md](references/troubleshooting.md)
