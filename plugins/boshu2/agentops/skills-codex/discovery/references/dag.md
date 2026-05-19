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
if command -v bd >/dev/null 2>&1; then TRACKING_MODE=beads; else TRACKING_MODE=tasklist; fi
if command -v ao >/dev/null 2>&1; then AO_AVAILABLE=true; else AO_AVAILABLE=false; fi
```

Classify complexity from explicit flag first, then goal shape:

- `fast`: short, specific, one-surface goal or `--fast-path`
- `standard`: medium goal or one scope keyword
- `full`: `--deep`, architecture keywords, cross-catalog changes, or >120 chars

### STEP 1 - Intent Clarification

If the goal is vague and `--skip-brainstorm` is not set, run `$brainstorm`
with the current goal.

Record only `brainstorm_path` and the refined objective. Do not carry the full
brainstorm transcript.

Skip when the goal is already specific (>50 chars, no vague keywords) or a
recent matching brainstorm artifact exists.

### STEP 1.5 - Product Design Gate

When `PRODUCT.md` exists and the goal is a feature/capability rather than a
bug, docs task, chore, dependency bump, lint, or format task, run `$design`
with the bounded objective and quick mode.

Design FAIL blocks discovery. PASS/WARN records `design_path` and one
decision line.

### STEP 2 - Bounded Prior Art

If `ao` is available, retrieve pointers, not full context:

```bash
ao search "<objective keywords>" 2>/dev/null || true
ao lookup --query "<objective keywords>" --limit 5 2>/dev/null || true
```

Apply each returned item explicitly:

- applicable? yes/no
- density field affected: intent, boundary, evidence, decision, constraint, or
  next action
- citation path

Write the ranked result path to `ranked_packet_path`. If no artifact exists,
record a short inline list of citation paths only.

### STEP 3 - Research Contract

Run `$research` as its own skill contract with the bounded objective and
`--auto` when discovery is in auto mode.

The research artifact is the source of detail. Discovery extracts only:

- `research_path`
- impacted bounded contexts
- relevant files or symbols
- applicable test levels
- constraints that must affect the plan

### STEP 4 - Plan Contract

Run `$plan` as its own skill contract with the bounded objective and `--auto`
when discovery is in auto mode.

The plan artifact is the source of slice detail. Discovery extracts only:

- `plan_path`
- `epic_id` when one exists
- issue count and wave count
- acceptance criteria YAML fences
- next `$crank` target

The plan output MUST include `acceptance_criteria` fenced YAML at two levels:
the parent epic body and each child bead body. Criterion shape is canonical in
`schemas/execution-packet.schema.json` (`#/$defs/Criterion`).

### STEP 4.5 - Optional Scaffold

If the plan creates a new project, package, module, service, or bootstrap
surface, and `--no-scaffold` is not set, run `$scaffold` for the detected
language and project name.

Record only the scaffold artifact path and constraints that affect
pre-mortem.

### STEP 5 - Pre-Mortem Contract

Run `$pre-mortem` against the exact plan artifact.

Use quick mode for fast/standard and full council for full. PASS/WARN
continues. FAIL triggers re-plan with the pre-mortem findings, up to 3 total
attempts. After 3 FAIL verdicts, write BLOCKED and stop.

Before STEP 6, propagate required pre-mortem hardening into the plan issues or
file-backed task specs. Workers read issues and specs, not the pre-mortem
report.

### STEP 6 - Compile Execution Packet

Write:

- `.agents/rpi/execution-packet.json`
- `.agents/rpi/runs/<run-id>/execution-packet.json` when `run_id` exists
- `.agents/rpi/phase-1-summary-YYYY-MM-DD-<slug>.md`

The packet is the narrow waist. It contains the six density fields, artifact
paths, criteria, validation lanes, tracker state, test levels, complexity, and
next action. It does not contain raw research, raw plan prose, or raw council
deliberation.

```bash
ao ratchet record discovery 2>/dev/null || true
```

Emit:

```text
<promise>DONE</promise>
```

## Acceptance Criteria Contract

Both the epic and each child bead carry an `acceptance_criteria` fenced YAML
block. STEP 6 lifts these into the execution packet as `epic_criteria` and
`bead_criteria`.

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
