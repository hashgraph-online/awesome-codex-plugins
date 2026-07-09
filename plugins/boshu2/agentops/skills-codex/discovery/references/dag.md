# Discovery Artifact-First DAG

Discovery is the densest RPI phase. Its job is not to keep research,
planning, and pre-mortem prose resident in the caller. Its job is to run the
declared child skill contracts and compile their artifacts into one execution
packet.

## Phase Rule

Every child step returns:

- artifact path
- verdict or status
- one-line extraction for the six density fields
- next action or block reason

Do not paste raw child output into discovery state. Link it.

## State

```text
discovery_state = {
  goal: "<goal string>",
  objective: "<bounded behavior objective>",
  complexity: "<fast|standard|full>",
  tracking_mode: "<beads|tasklist>",
  artifacts: {
    brainstorm_path: null,
    design_path: null,
    ranked_packet_path: null,
    research_path: null,
    perspective_plan_paths: [],
    synthesis_packet_path: null,
    duel_verdict_dir: null,
    duel_decision: null,
    fable_approval_path: null,
    approval_edge_path: null,
    plan_path: null,
    pre_mortem_path: null
  },
  density: {
    intent: null,
    boundary: null,
    evidence: [],
    decision: null,
    constraint: [],
    next_action: null
  },
  verdict: null
}
```

## DAG

Run every step in order. Stop only on an explicit BLOCKED verdict.

### STEP 0 - Initialize

```bash
mkdir -p .agents/rpi
# Tracker detection (tracker-agnostic): prefer br (beads_rust), else bd (legacy beads), else tasklist.
# Users may run EITHER beads CLI; the operationalize step (STEP 4) and the DONE gate use whichever is active.
if command -v br >/dev/null 2>&1; then TRACKING_MODE=beads; BEADS_CLI=br
elif command -v bd >/dev/null 2>&1; then TRACKING_MODE=beads; BEADS_CLI=bd
else TRACKING_MODE=tasklist; BEADS_CLI=; fi
if command -v ao >/dev/null 2>&1; then AO_AVAILABLE=true; else AO_AVAILABLE=false; fi
```

Classify complexity from explicit flag first, then goal shape:

- `fast`: short, specific, one-surface goal or `--fast-path`
- `standard`: medium goal or one scope keyword
- `full`: `--deep`, architecture keywords, cross-catalog changes, or >120 chars

### STEP 1 - Intent Clarification

If the goal is vague and `--skip-brainstorm` is not set:

```text
Skill(skill="brainstorm", args="<goal>")
```

Record only `brainstorm_path` and the refined objective. Do not carry the full
brainstorm transcript.

Skip when the goal is already specific (>50 chars, no vague keywords) or a
recent matching brainstorm artifact exists.

### STEP 1.5 - Product Design Gate

When `PRODUCT.md` exists and the goal is a feature/capability rather than a
bug, docs task, chore, dependency bump, lint, or format task:

```text
Skill(skill="design", args="<objective> --quick")
```

Design FAIL blocks discovery. PASS/WARN records `design_path` and one
decision line.

### STEP 2 - Bounded Prior Art

If `ao` is available, retrieve pointers, not full context:

```bash
ao search "<objective keywords>" 2>/dev/null || true
# Decision-point pull: GOLD wiki, compact pointers (no bodies), hard top-K cap
# (ADR-0002 bookend-bound). WARN — never silently — if the gold wiki is absent.
if [ -d .ao/wiki ]; then
    ao lookup --query "<objective keywords>" --gold --pointers --limit 3 2>/dev/null || true
else
    echo "WARN: gold wiki (.ao/wiki) absent — run 'ao wiki gold'; falling back to raw .agents/ corpus" >&2
    ao lookup --query "<objective keywords>" --limit 3 2>/dev/null || true
fi
```

Apply each returned item explicitly:

- applicable? yes/no
- density field affected: intent, boundary, evidence, decision, constraint, or next action
- citation path

Write the ranked result path to `ranked_packet_path`. If no artifact exists,
record a short inline list of citation paths only.

### STEP 3 - Research Contract

Invoke research as its own skill contract:

```text
Skill(skill="research", args="<objective> [--auto]")
```

The research artifact is the source of detail. Discovery extracts only:

- `research_path`
- impacted bounded contexts
- relevant files or symbols
- applicable test levels
- constraints that must affect the plan

### STEP 3.5 - Plan-Pawl Duel Gate (fanout class)

**Risk-class router.** Run the **plan-pawl duel** for **fanout-class** discovery —
architecture forks, one-way doors, contract/coordination changes (the `plan-pawl`
row in [`docs/contracts/pawls.md`](../../../docs/contracts/pawls.md)). For an **MVP
vertical slice** (cheap, reversible work), SKIP this step — gating it is the
waterfall `pawls.md` forbids; the slice gets only the inline `--quick` pre-mortem
at STEP 5.

The plan-pawl is the `multi-model` pawl applied to the PLAN artifact instead of a
code diff. It SUBSUMES the two redundant cross-family-review gates discovery used to
run — the single-judge Codex fanout approval and the STEP 5 pre-mortem council —
into ONE gate. For fanout class this duel verdict IS the pre-mortem verdict; STEP 5
is already satisfied.

Generate, then duel:

1. Write independent `PerspectivePlan` artifacts under
   `.agents/discovery/<run-id>/`, normally using these lenses:
   - product/user value
   - architecture and gate integrity
   - operations, migration, and failure recovery
   **Lens count scales with risk class (2026-07-02, showcase kernel R3):** reserve
   the full three-lens fan-out for genuine architecture forks and one-way doors.
   For content/marketing-class epics, run operations (always load-bearing — file
   ownership, waves, cut order) plus at most one domain lens, folding the rest
   into the synthesis directly (measured: product + gate-integrity lenses
   overlapped the research synthesis ~40% on a content epic, ~343k tokens for the
   trio). The DUEL below never scales down — two distinct families at the pawl is
   the floor regardless of lens count.
   Then write one `SynthesisPacket` that selects or merges the winning plan,
   records rejected alternatives, and carries open questions.
2. Run the cross-family DUEL over the `SynthesisPacket`: two judge panes from
   DISTINCT model families (e.g. Claude + Codex via
   [`using-atm`](../../using-atm/SKILL.md), `--no-user`, fresh-context by
   construction). Each pane writes one judge verdict
   (`{family,disposition,warn_class,judgment_flag}`) to `.agents/duel/<run-id>/`.
3. Decide deterministically — never by reading the panes yourself:

   ```bash
   ao plan-pawl decide --dir .agents/duel/<run-id> --round <N> --max-rounds 3
   ```

Gate semantics (the exit code IS the decision):

- exit 0 `PASS` (quorum: no FAIL AND >= 2 distinct roster families) -> continue to
  `/plan`.
- exit 3 `REDO` (auto-redo, no human) -> a FAIL re-runs fanout/synthesis with the
  findings; a mechanical WARN is auto-applied then re-judged; re-run with `--round`
  incremented. A judgment WARN is surfaced but does not block PASS.
- exit 4 `BLOCKED` -> a circuit breaker tripped (round > max, an explicit judgment
  flag, or oscillation): write BLOCKED and stop (the andon — rare and earned).

Discovery records only:

- `perspective_plan_paths`
- `synthesis_packet_path`
- `duel_verdict_dir` and the `ao plan-pawl decide` decision (PASS/REDO/BLOCKED)
- `approval_edge_path` (the `ApprovalEdge` records BOTH judge panes for the duel
  form; the single-Fable form remains valid under `--no-duel`)
- one decision line explaining the selected plan

The artifact shapes are defined in
[`docs/contracts/codex-fanout-approval-packet.md`](../../../docs/contracts/codex-fanout-approval-packet.md).

### STEP 4 - Plan Contract

Invoke plan as its own skill contract:

```text
Skill(skill="plan", args="<objective or approved synthesis_packet_path> [--auto]")
```

The plan artifact is the source of slice detail. Discovery extracts only:

- `plan_path`
- `epic_id` when one exists
- issue count and wave count
- the `## Scenarios` Gherkin block per bead
- acceptance criteria YAML fences
- next `/crank` target

Every bead `/plan` emits MUST carry an embedded `## Scenarios` Gherkin block
(Given/When/Then) by default — this is the behavior layer and is non-optional.
Free-text-only acceptance is invalid (AGENTS.md). The plan output MUST also
include `acceptance_criteria` fenced YAML at two levels (the machine-checkable
layer): the parent epic body and each child bead body. Criterion shape is
canonical in `schemas/execution-packet.schema.json` (`#/$defs/Criterion`).
Discovery does NOT relax this requirement; run the admission gate per
returned bead:

```bash
# Validate the structured BODY (--json | .description), not the human `ao beads exec show` render — the render also
# includes COMMENTS, so a Gherkin block in a comment would fool a bead whose body has no `## Scenarios`.
# `ao beads exec show --json` emits the canonical shape (a JSON array) for either tracker (age-f07z).
ao beads exec show "$BEAD_ID" --json 2>/dev/null \
  | jq -r '.[0].description // ""' \
  | bash scripts/check-bead-scenario-coverage.sh --admission -
```

Exit 1 sends the bead back to `/plan` to be promoted before compiling the
packet. Exit 2 is a tracker failure — stop and surface it; do not reject the
bead.

**Tracker-agnostic persistence (STEP 0 `$TRACKING_MODE`):** in `beads` mode `/plan` writes the epic + slice
children to `br`/`bd` (the STEP 6 DONE gate verifies the epic resolves AND has ≥1 parent-child child). In
`tasklist` mode (no `br`/`bd` on `PATH`) there is no bead DB, so `/plan` MUST persist the same operationalized
plan — the epic + its vertical slices with their acceptance — to **`.agents/rpi/tasklist.md`**, which the DONE
gate checks instead. Either way, an epic with no slices is not an operationalized plan.

### STEP 4.5 - Optional Scaffold

If the plan creates a new project, package, module, service, or bootstrap
surface, and `--no-scaffold` is not set:

```text
Skill(skill="scaffold", args="<detected-language> <project-name>")
```

Record only the scaffold artifact path and constraints that affect
pre-mortem.

### STEP 5 - Pre-Mortem Contract (MVP-slice class)

**Fanout class:** the pre-mortem is SUBSUMED by the STEP 3.5 plan-pawl duel — that
cross-family verdict IS the pre-mortem verdict. Do not run a second council; skip
to STEP 6.

**MVP-slice class** (the STEP 3.5 duel was skipped): invoke the inline `--quick`
pre-mortem against the exact plan artifact:

```text
Skill(skill="pre-mortem", args="<plan_path> --quick")
```

PASS/WARN continues. FAIL triggers re-plan with the pre-mortem findings, up to 3
total attempts. After 3 FAIL verdicts, write BLOCKED and stop.

Before STEP 6, propagate required hardening — from the STEP 3.5 duel verdict
(fanout) or this pre-mortem (MVP-slice) — into the plan issues or file-backed task
specs. Workers read issues and specs, not the report.

### STEP 6 - Compile Execution Packet

Write:

- `.agents/rpi/execution-packet.json`
- `.agents/rpi/runs/<run-id>/execution-packet.json` when `run_id` exists
- `.agents/rpi/phase-1-summary-YYYY-MM-DD-<slug>.md`

The packet is the narrow waist. It contains the six density fields, artifact
paths, criteria, validation lanes, tracker state, test levels, complexity, and
next action. It does not contain raw research, raw plan prose, or raw council
deliberation.

After the packet is written, stamp the orchestration-shape decision onto it. The
live (skill-driven) packet write does NOT route through the Go seed-writer, so
this is the live wire that makes `orchestration_decision` carry a validated
shape: `ao orchestrate shape` reads the packet, gathers observable ground truth
(Agent Mail live-writer count + per-lane reservation write-sets via
`orchestration.ValidateShape`), and overrides any confabulated proposal. Add
`--unattended` when the work must outlive the session (durability axis → ATM):

```bash
ao orchestrate shape 2>/dev/null || true # add --unattended for out-of-session/durable runs
ao ratchet record discovery 2>/dev/null || true
```

**DONE gate (the load-bearing completion check — EVERY path, specific-goal included).** Before emitting
DONE, the plan MUST be PERSISTED in the active tracker (STEP 4's output), not merely named by the packet's
`epic_id` STRING. Verify the epic + its slice children actually resolve — tracker-agnostically (`br` or `bd`,
or the tasklist equivalent):

```bash
EPIC_ID="$(jq -r '.epic_id // empty' .agents/rpi/execution-packet.json 2>/dev/null)"
BD_DIR="$(ao beads dir 2>/dev/null)"
if [ "$TRACKING_MODE" = beads ]; then
  # $BEADS_CLI is br or bd (STEP 0). The packet MUST name an epic that RESOLVES, carries >=1 SLICE child, and
  # EACH child must carry Gherkin acceptance — an epic alone OR an empty child is not an operationalized plan
  # (else the bug recurs one level down). The check matches the contract: existence AND Gherkin, not just existence.
  [ -n "$EPIC_ID" ] || { echo "discovery: packet carries no epic_id — not operationalized; run STEP 4 / /plan before DONE" >&2; exit 1; }
  epic_json="$(BEADS_DIR="$BD_DIR" "$BEADS_CLI" show "$EPIC_ID" --json 2>/dev/null)"
  [ -n "$epic_json" ] || { echo "discovery: epic $EPIC_ID not in the tracker ($BEADS_CLI) — operationalize before DONE" >&2; exit 1; }
  child_ids="$(printf '%s' "$epic_json" | jq -r '(if type=="array" then .[0] else . end).dependents[]? | select(.dependency_type=="parent-child") | .id' 2>/dev/null)"
  [ -n "$child_ids" ] || { echo "discovery: epic $EPIC_ID has NO vertical-slice children — operationalize the SLICES (STEP 4 / /plan), not just the epic, before DONE" >&2; exit 1; }
  # Each slice's BODY must pass the canonical Gherkin admission check. Feed the STRUCTURED description field
  # (--json | .description), NOT the human `br show` render — the render also includes COMMENTS, so a Gherkin
  # block in a comment would fool a child with an empty body (deterministic + comment-immune).
  for c in $child_ids; do
    BEADS_DIR="$BD_DIR" "$BEADS_CLI" show "$c" --json 2>/dev/null \
      | jq -r '(if type=="array" then .[0] else . end).description // ""' \
      | bash scripts/check-bead-scenario-coverage.sh --admission - >/dev/null 2>&1 \
      || { echo "discovery: slice $c lacks Gherkin (## Scenarios) acceptance in its BODY — promote it (STEP 4 / /plan) before DONE" >&2; exit 1; }
  done
else
  # tasklist mode (no br/bd) — the DEGRADED fallback. An arbitrary markdown tracker cannot be machine-verified as
  # robustly as a bead DB, so this is BEST-EFFORT + fail-closed (documented scope limit, not a hidden no-op):
  # .agents/rpi/tasklist.md must EXIST and carry the structural markers (an epic, >=1 slice, and Gherkin
  # Given/When/Then). For machine-verified completion, install br/bd.
  { [ -s .agents/rpi/tasklist.md ] \
      && grep -qiE 'epic' .agents/rpi/tasklist.md \
      && grep -qiE 'slice|^[-*] |^[0-9]+\.' .agents/rpi/tasklist.md \
      && grep -qiE 'given|when|then' .agents/rpi/tasklist.md ; } \
    || { echo "discovery: tasklist mode — .agents/rpi/tasklist.md must carry the epic + slices + Gherkin (Given/When/Then); operationalize before DONE (or install br/bd for machine-verified completion)" >&2; exit 1; }
fi
```

A plan packet + a passing pre-mortem with **no persisted beads is NOT DONE** — return to STEP 4 to
operationalize (epic + vertical slices with Gherkin acceptance + deps), then re-check. Only then emit:

```text
<promise>DONE</promise>
```

## Acceptance Criteria Contract

Both the epic and each child bead carry, by default:

1. An embedded `## Scenarios` Gherkin block (Given/When/Then) — the behavior
   layer, mandatory and non-optional for every bead.
2. An `acceptance_criteria` fenced YAML block — the machine-checkable layer.

STEP 6 lifts the criteria into the execution packet as `epic_criteria` and
`bead_criteria`. The `## Scenarios` block stays in the bead body and feeds the
`scenario-hash-stability` CI gate.

```yaml
acceptance_criteria:
  - id: ac-<scope>.<n>
    description: "<one-line measurable statement>"
    check_type: test_pass | command_exit_zero | file_exists | grep_match | manual | council_judge | custom_rubric
    check_command: "<shell command or script path>"
    evidence_path: "<glob>"
    evidence_required: true | false
    weight: 0.0-1.0
    optional: true | false
    agent_judge: "<council:name>"  # required only for custom_rubric
```

`agent_judge` is required when `check_type == "custom_rubric"`. Missing it is
a packet-write error, not a runtime warning.
