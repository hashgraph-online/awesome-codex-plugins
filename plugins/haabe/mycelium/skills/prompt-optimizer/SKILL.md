---
name: prompt-optimizer
description: "A/B test CLAUDE.md instruction changes against eval benchmarks. Capture baselines, test variants, compare results."
metadata:
  instruction_budget: "17"
  framework_dependency: "mycelium"
  framework_dependency_note: "This skill is designed to run within the Mycelium framework (https://github.com/haabe/mycelium). Standalone use will skip the canvas state, theory gates, and harness behavior the skill assumes. Install: /plugin install mycelium@haabe-mycelium."
---

# Prompt Optimizer

Systematically improve Mycelium instructions through measurement. Adapted from n-trax.

## Commands

### `baseline` -- Capture current performance
1. Run `/mycelium:eval-runner run-split optimization` — record as optimization scores
2. Run `/mycelium:eval-runner run-split holdout` — record as holdout scores
3. Record both to `.claude/optimization/baseline.json`: timestamp, CLAUDE.md hash, optimization metrics, holdout metrics, overall and per-category metrics

### `test <variant>` -- Test a variant
1. Read variant from `.claude/optimization/variants/<variant>.md`
2. Apply the CLAUDE.md changes described
3. Run `/mycelium:eval-runner run-split optimization` — this is the hill-climbing signal
4. Run `/mycelium:eval-runner run-split holdout` — this validates generalization
5. Store results in `.claude/optimization/results/<variant>.json`
6. Compare against baseline. Flag **overfitting** if optimization improves but holdout degrades.
7. Do NOT auto-revert -- let user decide

### `report` -- Compare all variants
Generate comparison table with split-aware columns:
```
| Variant | Opt Pass Rate | Holdout Pass Rate | Delta Opt | Delta Holdout | Overfit? | Decision |
```
Flag `Overfit? = YES` when optimization delta is positive but holdout delta is negative.

### `exemplar <eval-name>` -- Capture winning trajectory
After a clean eval win (1 iteration, fast), save the approach to `.claude/optimization/exemplars/`.

## Workflow
1. Capture baseline
2. Hypothesize an instruction improvement
3. Document in variants/ directory
4. Test the variant
5. Compare via report
6. Keep or revert based on data
7. Capture exemplars from clean wins
