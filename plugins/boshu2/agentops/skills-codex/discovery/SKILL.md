---
name: discovery
description: Create dense execution packets. Fold target
---
# $discovery - Dense Discovery Phase Adapter

## Codex Lifecycle Guard

When this skill runs in Codex hookless mode (`CODEX_THREAD_ID` is set or
`CODEX_INTERNAL_ORIGINATOR_OVERRIDE` is `Codex Desktop`), run:

```bash
ao codex ensure-start 2>/dev/null || true
```

The CLI records startup once per thread and skips duplicates automatically.

## Absorbed skills (ag-s43tg)

brainstorm (goal-vs-implementation clarification) + design (product-fit pressure test) — trigger detail in the Folded-In section below.

**YOU MUST EXECUTE THIS WORKFLOW. Do not just describe it.**

> **Loop position:** move 1 (shape intent as BDD) plus the seed for move 3
> (slice candidates) of the [operating loop](../../docs/architecture/operating-loop.md).
> Discovery turns a goal plus delegated child artifacts into one dense execution
> packet for `$crank` and `$validate`. It is also the **re-plan engine** for `$rpi`'s
> [Agile Re-Plan Loop](../rpi/references/agile-replan-loop.md): invoked again at each wave
> boundary to mutate the *remaining* waves from what the last wave taught — not only at the start. **Seed slice candidates small:** one Given/When/Then behavior each, refactor candidates kept separate from feature candidates — small batches + refactor-after-green are the load-bearing quality moves, not test-first ordering (Finster 2026, `skills/standards/references/agentic-workflow-evidence.md`); binding decomposition discipline is `$plan` (PR-010/PR-011).

## Folded-In Trigger Surface (brainstorm, design)

Discovery is the fold target for the retired standalone `brainstorm` and `design`
skills (skill-prune phase 2). Fire `$discovery` for their use-cases:

- **Brainstorm — Separate goals from implementation.** Clarify goals before
  planning: separate WHAT from HOW, explore the problem space before committing
  to a solution, and capture Given/When/Then acceptance examples. The full
  intent → Gherkin → executed-red → bead-DAG contract is owned by
  [`behavior-first-planning`](../behavior-first-planning/SKILL.md) — cite it when the beads must carry runnable done-criteria. Open-ended ideation (generate-winnow, `--ideate`) is the [Open-Ended Path](#open-ended-path-generate-winnow--operationalize--refine) below.
- **Design — Validate product fit before discovery.** Use when framing a
  problem, checking product/market fit, or pressure-testing user value before
  writing a discovery packet or any code. The product-validation gate
  (PRODUCT.md alignment, council `--preset=product`) runs as discovery's
  conditional design delegation step.

## Strict Delegation Contract (default)

Discovery runs brainstorm and design as internal modes (absorbed, ag-s43tg) and delegates to `$research`, `$plan`, and `$pre-mortem` as **separate skill invocations**. Strict delegation is the **default**.

**Anti-pattern to reject:** inlining `$research` work (grep + read + synthesize), collapsing `$plan` into an inline decomposition, skipping `$pre-mortem`. See [`../shared/references/strict-delegation-contract.md`](../shared/references/strict-delegation-contract.md) for the full contract, supported compression escapes (`--quick`, `--skip-brainstorm`, `--interactive`/`--auto`, `--no-scaffold`), and the **Pre-Mortem Anti-Rationalization Clause** (what does NOT count as a pre-mortem: an inline risk section you wrote, a prior adversarial pass on an input/premise rather than this plan, or "a related council already ran").

**Re-baseline before you scope** (mandatory for "improve X" / "build the missing Y"): `$research` MUST confirm a capability doesn't already exist before scoping *new construction*. The `--auto` trap is author-as-researcher scoping "what's unbuilt" from memory without grepping — existing machinery gets re-estimated as net-new. Every "X is missing" claim carries the search that proved it; no search → `$pre-mortem`'s re-baseline check (2.4–2.8) WARN/FAILs it. Run that existence search as `ms search "<capability phrase>"` first (fast path when `ms` is available — `command -v ms`, or the `mcp__ms__search` tool is attached; else grep `skills/**/SKILL.md` + `docs/SKILLS.md`) and cite the hits in the packet's overlap/prior-art section.

See [`docs/learnings/orchestrator-compression-anti-pattern.md`](../../docs/learnings/orchestrator-compression-anti-pattern.md) for the live compression signature.
See [`references/isolation-contract.md`](references/isolation-contract.md) for the mechanical four-lever model and the compression patterns flagged by `scripts/check-skill-isolation.sh`. See [`references/best-practices.md`](references/best-practices.md) for the lifecycle principle + anti-pattern citation table.

## Narrow Waist

Discovery does not carry raw child-skill output forward. It records artifact
paths, verdicts, the `hexagon:` boundary block from
[`docs/architecture/intent-to-loop-hexagon.md`](../../docs/architecture/intent-to-loop-hexagon.md),
and the six Context Density Rule fields:

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
vocabulary and the [Intent-to-Loop Hexagon](../../docs/architecture/intent-to-loop-hexagon.md)
for the boundary between Discovery and Plan:

| Boundary piece | Discovery contract |
|---|---|
| Inbound port | `shape_intent` from operator goal or BDD intent |
| Outbound port | `plan_slices` into `$plan` |
| Driving adapter | `$discovery` skill invocation |
| Driven adapter | `$plan` skill invocation plus br/file persistence |
| Context packet | density block, artifact links, acceptance examples, non-goals, constraints |
| Guard adapter | plan-pawl duel verdict (fanout) or `$pre-mortem` verdict (MVP-slice) before packet handoff |

Executable acceptance: [references/discovery.feature](references/discovery.feature) — Discovery hands dense intent across the `plan_slices` port (promoted from inline; soc-qk4b.2).

Goal-design packet inputs (`intent.md` + `driver.md`) use [references/goal-design-packet-input.md](references/goal-design-packet-input.md): run the checker before research; failure blocks; checked packets feed density fields and candidate slice seeds, not a `$plan` replacement.

## Plan-Pawl Duel Gate
### Risk-class routing: MVP vertical slice vs fanout (decide FIRST)
The duel is for one-way doors, not every slice. Route first:

- **Fanout class** (architecture forks, one-way-door decisions, cross-agent
  coordination contracts, product decisions): run the **plan-pawl duel** below — the
  `multi-model` pawl over the PLAN artifact ([`docs/contracts/pawls.md`](../../docs/contracts/pawls.md)).
  It SUBSUMES the old single-judge Codex fanout approval AND the `$pre-mortem`
  council into one cross-family gate (`--duel`, auto-on for fanout/`--complexity=full`).
- **MVP vertical slice** (default for routine runtime/CLI work): skip the duel
  (`--no-duel`). Run the discovery DAG under a hard time-box — **~15 min discovery,
  ~90 min slice** — then stop; the slice gets only the inline `--quick` pre-mortem.
  Work surfaced mid-slice becomes follow-up beads, never absorbed into the active bead.

The plan-pawl gates plan SHAPE, never behavior: the 2026-06-12 runtime review found a
coherent fanout+approval set that still missed an auth bypass one adversarial test
would have caught ([learning](../../docs/learnings/2026-06-12-codex-runtime-review-auth-and-scope.md)).

### The gate (fanout-class work only)

Insert the duel before `$plan` creates beads. The two-judge `ApprovalEdge` shape is
[`docs/contracts/codex-fanout-approval-packet.md`](../../docs/contracts/codex-fanout-approval-packet.md);
the DAG step is STEP 3.5 in [`references/dag.md`](references/dag.md).

1. Write at least three independent `PerspectivePlan` artifacts with different
   lenses (product/user value, architecture/gate integrity, operations/migration).
2. Winnow those into one `SynthesisPacket` (selected plan, rejected alternatives,
   rationale, open questions, risks).
3. Run the cross-family DUEL: two distinct-family judge panes (e.g. Claude + Codex
   via [`using-atm`](../using-atm/SKILL.md), `--no-user`, fresh-context by
   construction) each write one judge verdict to `.agents/duel/<run-id>/`.
4. Decide deterministically — never read the panes yourself:
   `ao plan-pawl decide --dir .agents/duel/<run-id> --round <N> --max-rounds <duel-rounds>`.
   exit 0 `PASS` (quorum: no FAIL, >=2 distinct families) -> `$plan`; exit 3 `REDO`
   -> auto-redo (a FAIL re-synthesizes; a mechanical WARN auto-applies + re-judges;
   a judgment WARN is surfaced, non-blocking); exit 4 `BLOCKED` -> breaker tripped
   (round > max / judgment flag / oscillation), stop (the andon).
5. Persist a duel `ApprovalEdge` (both judge panes, the `duel_verdict_dir`, the
   decision). For fanout this verdict IS the pre-mortem verdict — do not run a
   second council.

Approval evidence must survive the worktree: before the gated bead/epic closes, mirror
the council/duel artifacts (or a compact proof packet) to a tracked durable surface
(see [`codex-exec`](../codex-exec/SKILL.md)) — `.agents/` in a temp worktree is ignored.

## Open-Ended Path (generate-winnow → operationalize → refine)

> **Additive to the default flow — it does not replace the strict-delegation contract or the artifact-first DAG.** This path activates for open-ended "improve the project"-style goals (`"improve the project"`, `"what should we build next"`, `"make X more robust"`) OR when `--ideate` is passed. For a specific goal, the default flow (brainstorm-clarify → research → plan → pre-mortem) is unchanged.

On the open-ended path, Discovery prepends the generate-winnow methodology before research/plan and adds two steps after planning. Full detail lives in [`references/bead-operationalization.md`](references/bead-operationalization.md) and [`references/ideation-mode.md`](references/ideation-mode.md).

1. **Ideate (delegate to `brainstorm --ideate`).** Invoke `brainstorm` in **ideation mode** (a real skill invocation — strict delegation still applies; do NOT inline the 30-idea generation). It returns a ranked portfolio of **15** ideas (top 5 + next 10) with how/perceive/implement notes, rubric scores, and red-team findings.
2. **Research + plan-pawl duel + Plan.** Run research over the selected portfolio. Open-ended/high-risk work is fanout class: produce `PerspectivePlan` artifacts and a `SynthesisPacket`, then run the STEP 3.5 plan-pawl **duel** (two distinct families, `ao plan-pawl decide`) before `$plan` creates tracker rows — that duel verdict subsumes the pre-mortem. Then run the normal artifact-first DAG over the approved packet rather than a single goal.
3. **Operationalize.** Turn the ranked portfolio into a comprehensive, granular set of **self-documenting beads** — tasks, subtasks, dependency structure (`ao beads exec dep add`), and **explicit test tasks** (unit + e2e with detailed logging). Each bead carries what/why/how/risks/success so the original plan markdown never needs to be consulted again. Overlap-check against existing beads (`ao beads exec list --json`) before creating — merge, don't duplicate.
4. **Refine in plan space (4-5 passes).** Before handing the packet to `$crank`, run **4-5 refinement passes** over the bead set. Each pass: **re-read AGENTS.md** (especially after compaction), check every bead for sense and optimality, and **DO NOT OVERSIMPLIFY / DO NOT LOSE FEATURES OR FUNCTIONALITY**. Validate between passes (no dependency cycles; every leaf actionable via `ao beads exec ready`).

> Tracking is **`br`** with `bv` triage — this is AgentOps. The operationalize and refine steps consume `brainstorm`'s ideation output; see [`references/bead-operationalization.md`](references/bead-operationalization.md).

Executable acceptance for this path: [references/discovery.feature](references/discovery.feature) (ideation/operationalize/refine scenarios, ag-yw0).

## Execution

Run the artifact-first DAG in [references/dag.md](references/dag.md). That
file owns the executable workflow, state shape, gate detail, per-step detail,
and the acceptance-criteria YAML contract.

## Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--auto` | on | Fully autonomous (no human gates). Inverse of `--interactive`. Passed through to `$research` and `$plan`. |
| `--interactive` | off | Human gates in research and plan (STEP 3, STEP 4). Does NOT affect pre-mortem gate. |
| `--skip-brainstorm` | auto | Skip STEP 1 brainstorm when goal is already specific |
| `--ideate` | auto | Force the open-ended generate-winnow path: delegate to `brainstorm --ideate` (30→5→15), then operationalize into self-documenting `br` beads and refine 4-5x in plan space. Auto-on for open-ended goals. See [Open-Ended Path](#open-ended-path-generate-winnow--operationalize--refine). |
| `--complexity=<level>` | auto | Force complexity level (`fast` / `standard` / `full`) |
| `--no-budget` | off | Disable phase time budgets |
| `--no-scaffold` | off | Skip scaffold auto-invocation in STEP 4.5 |
| `--duel` | auto | Run the plan-pawl cross-family duel at STEP 3.5. Auto-on for fanout class and `--complexity=full`; opt-in elsewhere. Subsumes the single-judge fanout approval + pre-mortem council. |
| `--no-duel` | off | Skip the duel (MVP-slice class): single-Fable `ApprovalEdge` if approval is needed, plus the inline `--quick` pre-mortem at STEP 5. |
| `--duel-rounds=<N>` | 3 | Max duel rounds before the max-attempts breaker trips (`ao plan-pawl decide --max-rounds`). |

## Quick Start

```bash
$discovery "add user authentication"              # full discovery
$discovery --interactive "refactor payment module" # human gates in research + plan
$discovery --skip-brainstorm "fix login bug"       # skip brainstorm for specific goals
$discovery --complexity=full "migrate to v2 API"   # force full council ceremony
```

## Output Specification

**Format:** compact markdown phase summary to stdout plus JSON execution packet
on disk.

**Files written** (the shaping; the LOAD-BEARING output is the persisted tracker beads — see Completion Markers):

- `.agents/research/<topic-slug>.md` - research artifact path only
- `.agents/plans/YYYY-MM-DD-<goal-slug>.md` - plan document path only
- `.agents/council/YYYY-MM-DD-pre-mortem-<topic>.md` - pre-mortem verdict path only
- `.agents/rpi/execution-packet.json` - latest dense packet
- `.agents/rpi/runs/<run-id>/execution-packet.json` - per-run archive when `run_id` is set
- `.agents/rpi/phase-1-summary-YYYY-MM-DD-<goal-slug>.md` - compact discovery summary

**Exit signal:** completion marker (`<promise>DONE</promise>` or `<promise>BLOCKED</promise>`) — see Completion Markers below.

## Completion Markers

```
<promise>DONE</promise>      # Discovery complete AND the plan PERSISTED in the active tracker (br/bd, else tasklist): `ao beads exec show <epic_id>` (the packet's epic_id is a STRING — it must resolve) lists the epic + Gherkin-bearing slice children. A plan packet + passing pre-mortem with NO persisted beads is NOT DONE — operationalize (dag STEP 4 / $plan), verify, then signal.
<promise>BLOCKED</promise>   # Pre-mortem failed 3x, manual intervention needed
```

## Troubleshooting

Read `references/troubleshooting.md` for common problems and solutions.

## Reference Documents

- [references/goal-clarification-brainstorm.md](references/goal-clarification-brainstorm.md) — absorbed brainstorm body (four-phase clarification + ideation funnel)
- [references/idea-rubric.md](references/idea-rubric.md) — absorbed brainstorm idea rubric
- [references/brainstorm.feature](references/brainstorm.feature) — absorbed brainstorm executable spec
- [references/red-team-checklist.md](references/red-team-checklist.md) — absorbed brainstorm red-team checklist
- [references/dag.md](references/dag.md) — executable workflow, state shape, gate detail, per-step detail, acceptance-criteria YAML contract
- [references/complexity-auto-detect.md](references/complexity-auto-detect.md) — precedence contract for keyword vs issue-count classification
- [references/idempotency-and-resume.md](references/idempotency-and-resume.md) — re-run safety and resume behavior
- [references/phase-budgets.md](references/phase-budgets.md) — time budgets per complexity level
- [references/troubleshooting.md](references/troubleshooting.md) — common problems and solutions
- [references/output-templates.md](references/output-templates.md) — execution packet and phase summary formats
- [references/phase-data-contracts.md](references/phase-data-contracts.md) — phase artifact data contracts (cited from references/isolation-contract.md)
**See also:** [research](../research/SKILL.md), [plan](../plan/SKILL.md), [pre-mortem](../pre-mortem/SKILL.md), [crank](../crank/SKILL.md), [rpi](../rpi/SKILL.md), [scaffold](../scaffold/SKILL.md)
