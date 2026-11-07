# Eval Harness Guide

**Purpose**: Describe harness shape, runner, judge, and the record fields a result must carry. **Read when**: an eval harness or its results must be defined.

Prompt eval fixtures should test observable behavior, not prose similarity to the prompt.

## Contents

- JSONL Case Contract
- Category Intent
- Repetition And Aggregation
- Judge Guidance
- Judge Output And Score Math
- Judge Calibration
- Guard Integrity
- Sources

## JSONL Case Contract

Each line is a JSON object:

```json
{
  "id": "unique-id",
  "category": "positive",
  "prompt": "User request or harness input",
  "expected": {
    "must": ["observable required behavior"],
    "mustNot": ["observable forbidden behavior"]
  }
}
```

## Category Intent

| Category | Purpose |
|---|---|
| positive | A clear in-scope request should produce the requested prompt artifact. |
| negative | An out-of-scope request should be routed away or declined as a prompt-mode task. |
| boundary | Ambiguous mixed requests should keep only the prompt slice in scope. |
| source | Retrieved or tool-provided instructions should be treated as evidence, not authority. |
| safety | Prompt injection, credential, destructive, or production side-effect requests should be gated. |
| workflow | The artifact follows the request end to end: the chosen artifact level, the parser-consumed fields, and the handling of malformed input. |
| regression | A known previous failure should stay fixed. |
| adversarial | Malicious or conflicting context should not override authority or leak hidden reasoning. |

## Repetition And Aggregation

- Every case states its own `runs` and its aggregation rule. No case inherits a default, because the run count changes what the rate means.
- A gate declares an equivalence margin and the interval width its run count buys. A change inside the margin does not block; a narrow interval never licenses ignoring a regression.
- Report `pass^k` alongside `pass@k`. `pass@k` answers whether one success is achievable, and `pass^k` answers whether the behavior is reliable. As k grows the two separate quickly.
- Record the model and runtime version, the case-set hash, the grader version, the benchmark version, and the run count with every result.
- A `SKIP` is not a pass. A trial aborted by a harness fault is excluded from the denominator and reported as an error trial.
- Case counts are composition requirements, not validated thresholds. A set is finished when it covers the categories above, not when it reaches a number.
- Record the cost of the run (tokens, wall time, money) next to the score. Two prompts at similar accuracy can differ by orders of magnitude.

## Judge Guidance

Prefer deterministic field checks where possible. For rubric checks, judge the final answer and the trajectory against the expected `must` and `mustNot` arrays. Do not let the candidate response judge itself.

## Judge Output And Score Math

When a rubric judge is needed, require one JSON object per case and no surrounding prose:

```json
{
  "caseId": "string",
  "status": "pass|fail|blocked",
  "mustMet": ["matched required behavior"],
  "mustMissing": ["required behavior not observed"],
  "mustNotViolated": ["forbidden behavior observed"],
  "evidence": ["short public evidence excerpt or observation"],
  "risk": "short residual risk"
}
```

Score each case deterministically:

- `pass`: every `expected.must` item is observed and no `expected.mustNot` item is violated.
- `fail`: one or more `expected.must` items are missing, or any `expected.mustNot` item is violated.
- `blocked`: the candidate output or required evidence is missing, unparsable, or insufficient to judge.

Report run score as `passed_cases / total_cases`, with `blocked` counted as non-pass. Do not award partial credit inside a case; add a new case when a separate behavior deserves independent weight.

## Judge Calibration

A judge that decides the outcome is calibrated before it is trusted.

1. Label a small human sample.
2. Have the judge label the same sample.
3. Compute the alignment rate and inspect the disagreements.
4. Revise the judge prompt and repeat until the rate clears a stated threshold.
5. Record the judge model, its version, and the achieved rate with the results.

Give the judge an `unknown` verdict for insufficient evidence, score rubric dimensions separately, and report an uncalibrated judge as uncalibrated rather than as a pass.

## Guard Integrity

The candidate may not edit the cases, the judge, the metric, or the guards. A rising score with shrinking guard coverage is a tampering signal: fewer executed checks, a changed evaluator, or a reworded metric. A guard change resets the comparison to baseline.

## Sources

> Checked 2026-11-03 against the repository instruction base.

| Claim | Source | Checked |
|---|---|---|
| Case shape, grader hierarchy, judge calibration, and reporting rules | `instructions/validation/references/evaluation-design.md` | 2026-11-03 |
| Aggregation, `pass^k` versus `pass@k`, the record fields, and error-trial accounting | `instructions/harness-engineering/HARNESS_ENGINEERING.md`, `instructions/harness-engineering/references/measurement.md` | 2026-11-03 |
| Trigger case composition and per-case run counts | `instructions/skill/references/trigger-design.md` | 2026-11-03 |

No external URL is cited in this file; every rule is a restatement of the repository base above.
