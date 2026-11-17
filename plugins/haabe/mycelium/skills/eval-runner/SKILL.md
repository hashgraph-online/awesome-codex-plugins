---
name: eval-runner
description: "Run eval scenarios to benchmark Mycelium effectiveness. Execute tasks using reflexion loop, validate against success criteria, record metrics."
metadata:
  instruction_budget: "41"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Eval Runner

Benchmark the agent's performance against defined scenarios. Adapted from n-trax eval system.

## Commands

### `run <category/name>`
1. Read YAML from `.claude/evals/scenarios/<category>/<name>.yml`
2. Parse fields (name, category, task_prompt, success_criteria, budget)
3. Execute setup steps if defined
4. Record start time
5. Execute task via reflexion workflow (read corrections first)
6. Record end time and iteration count
7. Validate ALL success criteria
8. Write result JSON to `.claude/evals/results/<timestamp>-<name>.json`
9. Report summary

### `run-all [category]`
1. Glob `.claude/evals/scenarios/**/*.yml`
2. Skip scenarios with `status: retired`
3. For each: run in isolation (git stash), record result, restore
4. Update `.claude/evals/pass-history.json` with each result
5. Aggregate and report

### `run-split <optimization|holdout>`
1. Glob `.claude/evals/scenarios/**/*.yml`
2. Read each YAML, filter by `split` field matching the requested set
3. Skip scenarios with `status: retired`
4. For each matching scenario: run in isolation, record result, restore
5. Update `.claude/evals/pass-history.json` with each result
6. Aggregate and report (label output clearly as "Optimization Set" or "Holdout Set")

### `report`
1. Read all results from `.claude/evals/results/`
2. Generate summary table:
```
| Category    | Pass Rate | Avg Iterations | Avg Time | Notes |
|-------------|-----------|----------------|----------|-------|
| discovery   | ...       | ...            | ...      |       |
| delivery    | ...       | ...            | ...      |       |
| integration | ...       | ...            | ...      |       |
| **Overall** | ...       | ...            | ...      |       |
```
3. List failure patterns and recommendations

### `prune`
1. Read `.claude/evals/pass-history.json`
2. Flag evals where `last_5` is all-pass (`saturated`) or all-fail (`broken`)
3. Flag evals with no runs in 30+ days (`stale`)
4. For saturated evals, suggest: retire or increase difficulty
5. For broken evals, suggest: fix criteria or retire
6. Present recommendations — do NOT auto-retire
7. On user confirmation: set `status: retired` in scenario YAML, update pass-history.json, log in .claude/harness/decision-log.md

### `mine`
Analyze audit logs to propose new eval scenarios from observed failure patterns.

1. Read `.claude/state/change-log.jsonl` (last 100 entries)
2. Read `.claude/state/diamond-state-audit.jsonl` (all entries)
3. Group change-log entries by `session_id`, identify:
   a. **Correction clusters**: 3+ edits to same file in one session (agent struggled)
   b. **Skill friction**: edits to `.claude/skills/*/SKILL.md` during a session (instructions unclear)
   c. **Missing test coverage**: 5+ files changed with no test file edits
4. Count diamond bypass entries from audit log
5. Cross-reference with existing scenarios in pass-history.json to avoid duplicates
6. For each pattern, output a proposed eval scenario as YAML template
7. Tag proposals with `source: trace-mining` and originating `session_id`
8. Do NOT auto-create files — present for human review

See `.claude/evals/schema.md` §Trace Mining Heuristics for pattern-to-eval mappings.

## Result Format
See `.claude/evals/schema.md` for YAML scenario and JSON result formats.

## Pass History
After writing each result JSON (step 8 of `run`), also update `.claude/evals/pass-history.json`:
- Increment `runs` and `passes` (if passed) for the eval
- Append `true`/`false` to `last_5` (trim to keep only last 5)
- Update `last_run` timestamp

## Creating Scenarios
Place YAML files in `.claude/evals/scenarios/<category>/`. Define task_prompt, success_criteria, and budget. Set `split`, `status`, and `source` fields per schema.
