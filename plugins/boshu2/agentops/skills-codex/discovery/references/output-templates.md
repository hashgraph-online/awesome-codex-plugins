# Discovery Output Templates

## Execution Packet

Write the current packet to:

- `.agents/rpi/execution-packet.json` as the latest alias
- `.agents/rpi/runs/<run-id>/execution-packet.json` as the per-run archive when `run_id` exists

When no `epic_id` exists, this execution packet becomes the file-backed discovery-to-implementation handoff; the next phase invokes `/crank .agents/rpi/execution-packet.json` instead of inventing an epic.

```json
{
  "schema_version": 1,
  "run_id": "<run-id or omitted>",
  "objective": "<goal>",
  "density": {
    "intent": "<behavior or capability>",
    "boundary": {
      "bounded_context": "<context>",
      "non_goals": ["<explicit non-goal>"],
      "write_scope": ["<path or surface>"]
    },
    "evidence": ["<acceptance example, test, gate, or verdict>"],
    "decision": "<why this slice/plan shape was chosen>",
    "constraint": ["<safety, runtime, token, or process limit>"],
    "next_action": "<exact /crank command or block reason>"
  },
  "artifacts": {
    "research_path": ".agents/research/<topic>.md",
    "plan_path": ".agents/plans/<plan>.md",
    "pre_mortem_path": ".agents/council/<pre-mortem>.md",
    "ranked_packet_path": ".agents/rpi/ranked-packet.json",
    "perspective_plan_paths": [
      ".agents/discovery/<run-id>/perspective-product.md",
      ".agents/discovery/<run-id>/perspective-architecture.md",
      ".agents/discovery/<run-id>/perspective-operations.md"
    ],
    "synthesis_packet_path": ".agents/discovery/<run-id>/synthesis-packet.yaml",
    "fable_approval_path": ".agents/council/<date>-fable-approval-<slug>.md",
    "approval_edge_path": ".agents/discovery/<run-id>/approval-edge.yaml"
  },
  "approval_edge": {
    "kind": "ApprovalEdge",
    "source_packet": ".agents/discovery/<run-id>/synthesis-packet.yaml",
    "capture_path": ".agents/council/ntm-captures/<target>_<stamp>.txt",
    "verdict_artifact": ".agents/council/<date>-fable-approval-<slug>.md",
    "verdict": "PASS|WARN",
    "accepted_risks": []
  },
  "epic_id": "<epic-id or omitted>",
  "plan_path": ".agents/plans/<plan-file>.md",
  "contract_surfaces": ["docs/contracts/repo-execution-profile.md"],
  "validation_commands": ["<from repo profile or defaults>"],
  "validation_lanes": [
    {
      "name": "<stable lane id>",
      "command": "<validation command>",
      "read_only": true,
      "writes_artifacts": false,
      "isolated_agents_home": true,
      "release_only": false,
      "mutation_escape_hatch": null,
      "cost_class": "standard",
      "auto_select": "default",
      "timeout_seconds": 180
    }
  ],
  "tracker_mode": "<beads|tasklist>",
  "tracker_health": {
    "healthy": true,
    "mode": "<beads|tasklist>",
    "reason": "<probe summary>"
  },
  "done_criteria": ["<from repo profile or defaults>"],
  "complexity": "<fast|standard|full>",
  "pre_mortem_verdict": "<PASS|WARN>",
  "test_levels": {
    "required": ["L0", "L1"],
    "recommended": ["L2"],
    "rationale": "<why these levels apply>"
  },
  "ranked_packet_path": ".agents/rpi/ranked-packet.json",
  "discovery_timestamp": "<ISO-8601>"
}
```

The `density` block is the phase boundary. Raw research, raw plan prose, and
raw council deliberation stay in the referenced artifacts.

## acceptance_criteria — per-epic + per-bead

The packet carries criteria at two slots — `epic_criteria` (array, one entry per epic-level acceptance statement) and `bead_criteria` (object keyed by bead ID, value is an array per bead). Both slots are typed by `#/$defs/Criterion` in [`schemas/execution-packet.schema.json`](../../../schemas/execution-packet.schema.json) — that schema is the canonical machine-readable form. Discovery STEP 6 lifts the YAML fences from the plan and serializes them into the packet; do not redefine the shape here.

Source YAML (lifted verbatim from epic + bead bodies emitted by `/plan`):

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
    agent_judge: "<council:name>"  # REQUIRED only when check_type == custom_rubric
```

Packet-side JSON shape (excerpt):

```json
{
  "epic_criteria": [
    { "id": "ac-e1.1", "description": "...", "check_type": "file_exists", "evidence_required": true, "weight": 1.0, "optional": false }
  ],
  "bead_criteria": {
    "soc-bcrn.1.2": [
      { "id": "ac-bcrn.1.2.1", "description": "...", "check_type": "grep_match", "evidence_required": true, "weight": 1.0, "optional": false }
    ]
  }
}
```

`/crank` and `/validate` read these slots; v1 packets without them fall back to the legacy `done_criteria` array.

## Phase Summary

Write to `.agents/rpi/phase-1-summary-YYYY-MM-DD-<goal-slug>.md`:

```markdown
# Phase 1 Summary: Discovery

- **Goal:** <goal>
- **Epic:** <epic-id>
- **Issues:** <count>
- **Complexity:** <fast|standard|full>
- **Pre-mortem:** <PASS|WARN> (attempt <N>/3)
- **Brainstorm:** <used|skipped>
- **History search:** <findings count or skipped>
- **Density:** intent, boundary, evidence, decision, constraint, next action
  all present
- **Status:** DONE
- **Timestamp:** <ISO-8601>
```

## Ratchet and Telemetry

```bash
ao ratchet record discovery 2>/dev/null || true
bash scripts/checkpoint-commit.sh rpi "phase-1" "discovery complete" 2>/dev/null || true
bash scripts/log-telemetry.sh rpi phase-complete phase=1 phase_name=discovery 2>/dev/null || true
```
