# Prompt Pack Schema

**Purpose**: Define the pack fields a parser consumes. **Read when**: a full pack or a parser-consumed schema is requested.

Use this schema for reusable prompt artifacts. Keep keys stable when an eval harness or downstream script reads them.

```yaml
identity:
  name: ""
  role: ""
  responsibility: ""
intent:
  user_goal: ""
  success_criteria: []
  failure_criteria: []
trigger:
  use_when: []
  do_not_use_when: []
scope:
  in_scope: []
  out_of_scope: []
  side_effect_limits: []
authority:
  priority_order: []
  conflict_rule: ""
  binding_rules: []       # developer-level: valid on every run
  advisory_rules: []      # defaults a user may override
  untrusted_data_shaping: "yaml | json | xml | labeled-block"
evidence:
  required_sources: []
  source_ledger: ""
tools:
  allowed: []
  gated: []
variables:
  required: []
  optional: []
context_packet:
  documents: []
  material_order: "documents first, question and output format last"
  assumptions: []
  missing_information: []
  volatile_tail: []       # date, current task, per-turn values appended last
examples:
  positive: []
  negative: []
constraints:
  style: []
  safety: []
  reasoning_visibility: "Do not request hidden chain-of-thought; ask for public rationale and verification evidence."
  output_shape: "instructions | example | schema"   # never a prefilled assistant turn
output_schema:
  format: "markdown | json | yaml"
  fields: []
  forbidden: []
eval_cases:
  fixture: ""
  categories: [positive, negative, boundary, workflow, source, safety, regression, adversarial]
  runs: 0
  aggregation: ""
  grader_version: ""
version_note:
  version: ""
  changed: []
  rationale: ""
  remaining_risk: ""
```

## Required Sections

Every prompt pack should include identity, variables, context packet, examples, constraints, output schema, eval cases, and version note even when some values are intentionally empty with a reason.

## Field Rules

- `authority.binding_rules` and `authority.advisory_rules` are separated so a lower layer cannot silently override a higher one. A rule listed as advisory must not read like a prohibition.
- `context_packet.material_order` and `context_packet.volatile_tail` keep the stable prefix stable. Anything that must outlive a compaction belongs in a file, not in this block.
- `constraints.output_shape` names how the shape is expressed. A prefilled assistant turn is not an option: current Claude models reject a prefilled last assistant message with a 400 error.
- `eval_cases.runs` and `eval_cases.aggregation` are per case. `eval_cases.grader_version` changes whenever the judge changes, and a grader change makes earlier scores incomparable.

When `format` is `json` or `yaml`, define exact key names and types, reject malformed required inputs, and include a schema eval that parses the output. Do not accept prose that merely mentions the required fields.

## Sources

> Checked 2026-11-03 against the repository instruction base.

| Claim | Source | Checked |
|---|---|---|
| Authority levels and untrusted-data framing | `instructions/context-engineering/references/prompt-authoring.md` | 2026-11-03 |
| Stable prefix and volatile tail | `instructions/cache/CACHE.md` | 2026-11-03 |
| Per-case runs, aggregation, and the grader version in the record | `instructions/harness-engineering/HARNESS_ENGINEERING.md` | 2026-11-03 |
| Prefilled responses rejected on current Claude models | <https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices> | 2026-11-03 |

No other external URL is cited; the schema rules restate the repository base above.
