---
name: produce-feedback
description: Use when user wants to produce a factual chronicle of development-skills plugin interactions in the current conversation for later ingestion, or runs /produce-feedback. Pure record, no judgment.
disable-model-invocation: true
---

Produce a factual chronicle of development-skills plugin interactions in this conversation. Pure record, no judgment.

Write to `docs/reports/development-skills-feedback-YYYY-MM-DD.md`. Self-contained.

## Section 1: Project Context (short)

Language, size, test count, framework. Task performed. Why plugin was involved.

## Section 2: Full Chain-of-Thought Dump

EXHAUSTIVE chronological dump of every plugin interaction. Every skill trigger, phase read, gate evaluation, routing decision, agent spawn, tool call, verification run, deviation, problem.

Each step:
1. **Plugin instruction:** Quote the specific instruction from the specific file
2. **Agent action:** Tool called, parameters, result
3. **Agent reasoning:** Why it followed or deviated
4. **Outcome:** What happened

```
Step 3: core-dev/SKILL.md Step 1: "Run: bash scripts/find-plan.sh active"
  - Action: Glob("**/find-plan.sh") → no results. grep fallback → found plan.
  - Reasoning: Script not found. Used fallback.
  - Outcome: Active plan found. 3 tool calls.
```

## Section 3: Friction Point Summary

| # | Step | Plugin file + instruction | What happened | Tool calls |
|---|------|--------------------------|---------------|------------|

## Section 4: Proposed Behavioral Evals

One eval per friction point:

```json
{
  "name": "kebab-case-name",
  "category": "category",
  "tests_change": "which friction point",
  "prompt": "user prompt",
  "expected_output": "what model should do",
  "assertions": [{"name": "x", "type": "behavioral", "check": "what", "pass_criteria": "criteria"}]
}
```

Verify Section 2 covers every interaction, then report location.
