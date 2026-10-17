---
title: Experiment Skill — Deep Reference
date: 2026-05-28
source: extracted from skills/experiment/SKILL.md
---

## Lifecycle diagram

```
UNPROVEN (0.0) --> TESTING (0.1-0.7) --> SUPPORTED (0.8+) or REFUTED (<0.2)
                                            |                    |
                                        GRADUATED              KILLED
                                       (proven rule)       (remove from rules)
```

## Confidence scoring — full worked example

Bayesian-style updates after each experiment run.

Formulas:
- supports:     `confidence += (1 - confidence) * 0.25`
- refutes:      `confidence -= confidence * 0.3`
- inconclusive: no change (but recorded in evidence log)

Graduation threshold: confidence ≥ 0.8 AND evidence_for ≥ 3 AND for:against ≥ 3:1
Kill threshold: confidence < 0.2 AND evidence_against ≥ 2

Step-by-step example for H001 starting at 0.0:
```
experiment 1: supports  --> 0.0 + (1.0 - 0.0) * 0.25    = 0.25
experiment 2: supports  --> 0.25 + (1.0 - 0.25) * 0.25  = 0.4375
experiment 3: refutes   --> 0.4375 - 0.4375 * 0.3        = 0.306
experiment 4: supports  --> 0.306 + (1.0 - 0.306) * 0.25 = 0.480
experiment 5: supports  --> 0.480 + (1.0 - 0.480) * 0.25 = 0.610
experiment 6: supports  --> 0.610 + (1.0 - 0.610) * 0.25 = 0.708
experiment 7: supports  --> 0.708 + (1.0 - 0.708) * 0.25 = 0.781
experiment 8: supports  --> 0.781 + (1.0 - 0.781) * 0.25 = 0.836  --> GRADUATED
```

## AgentDB schema

```sql
CREATE TABLE IF NOT EXISTS hypotheses (
  id TEXT PRIMARY KEY,
  statement TEXT NOT NULL,
  source TEXT NOT NULL,
  domain TEXT NOT NULL,
  status TEXT DEFAULT 'unproven',
  confidence REAL DEFAULT 0.0,
  evidence_for INTEGER DEFAULT 0,
  evidence_against INTEGER DEFAULT 0,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS experiments (
  id TEXT PRIMARY KEY,
  hypothesis_id TEXT NOT NULL,
  method TEXT NOT NULL,
  measurement TEXT NOT NULL,
  pass_criteria TEXT NOT NULL,
  fail_criteria TEXT NOT NULL,
  result TEXT CHECK(result IN ('supports', 'refutes', 'inconclusive')),
  evidence TEXT,
  executed_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (hypothesis_id) REFERENCES hypotheses(id)
);
```

## Domains

Rules cluster into testable domains. Classification guides experiment design.

| Domain | Description |
|---|---|
| methodology | Research-first, anti-patterns-before-solutions, slow-down-to-speed-up |
| coordination | Parallel-first, tier system, agent spawning patterns |
| testing | Tests-before-code, edge-cases-first, mock boundaries |
| git | Atomic commits, conventional messages, feature branches |
| security | No hardcoded secrets, input validation boundaries |
| performance | Measure before optimizing, bottleneck identification |
| quality | Big 5 checks, code review protocols, R-factor thresholds |

## Seeding — parsing rules from CLAUDE.md

Bootstrap hypotheses from existing CLAUDE.md rules.

Parse rule-like patterns:
- Imperative statements: "Never X", "Always Y", "Must Z"
- Convention definitions: "Format: X", "Style: Y"
- Assertions: "X is better than Y", "X before Y"
- Quantitative claims: "reduces by X%", "takes N minutes"

Each becomes a hypothesis record:
- id: auto-generated (H001, H002, ...)
- statement: the rule as stated
- source: file path + line number
- domain: auto-classified from domains list
- status: unproven
- confidence: 0.0

## Experiment design principles

Six principles. Violating any one invalidates the experiment.

1. **Falsifiability** — Every experiment must be able to disprove the hypothesis. If no possible outcome would refute the rule, the experiment is useless.

2. **Minimum viable test** — Smallest possible scope that produces signal. One task comparison, not a week-long study.

3. **Quantitative preferred** — Numbers over opinions. Time, error count, recall percentage, rework frequency. Qualitative evidence is acceptable only when quantitative is impossible.

4. **Control condition** — Compare against baseline. What happens WITHOUT the rule? No control = no experiment. Just an observation.

5. **Reproducibility** — Another session should be able to repeat the experiment with the same method. Record: exact steps, inputs, environment, measurement approach.

6. **Independence** — Test one rule at a time. Control for confounds. If two rules interact, test each independently first.

## Experiment patterns by domain

### methodology (example: research before coding)
- method: A/B comparison across similar tasks
- measure: time to completion, error rate, rework count
- control: task executed WITHOUT the rule applied
- sample_size: minimum 3 comparisons for signal

### coordination (example: parallel beats serial)
- method: timed execution of same-scope work
- measure: wall-clock time, merge conflict rate, quality score
- control: serial execution of identical scope
- sample_size: minimum 3 comparisons for signal

### testing (example: tests before code)
- method: track tasks with test-first vs test-after
- measure: bug escape rate, rework frequency, coverage delta
- control: tasks where tests were written after implementation
- sample_size: minimum 5 tasks per condition

### quality (example: Big 5 checks prevent bugs)
- method: compare code reviewed with Big 5 vs without
- measure: post-merge bug reports, review round-trips
- control: code merged without Big 5 review
- sample_size: minimum 5 reviews per condition

### git (example: atomic commits reduce revert pain)
- method: track revert complexity for atomic vs bundled commits
- measure: time to revert, collateral damage (unrelated changes reverted)
- control: multi-concern commits
- sample_size: minimum 3 revert events per condition

### security (example: Zod validation prevents injection)
- method: fuzz endpoints with and without schema validation
- measure: injection success rate, malformed input acceptance rate
- control: endpoint without Zod/Pydantic layer
- sample_size: minimum 50 fuzz inputs per endpoint

### performance (example: measure before optimizing saves time)
- method: compare optimizations guided by profiling vs intuition
- measure: actual speedup achieved, time spent optimizing
- control: intuition-guided optimization
- sample_size: minimum 3 optimization tasks per condition
