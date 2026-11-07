# Evaluation And Iteration

**Purpose**: Define eval cases, judges, and bounded optimization rounds. **Read when**: building, scoring, or optimizing a reusable prompt.

## Minimum Categories

Include positive, negative, boundary, workflow, source, safety, regression, and adversarial cases when creating a JSONL prompt eval fixture. The set is composed, not counted: no number of cases is a validated threshold.

## Anti-Tautology Rule

An eval must be able to fail under a plausible bad prompt. Do not count checks that only assert file existence, keyword presence unrelated to behavior, or a restatement of the implementation text. A case whose expected output was written from the current implementation measures the implementation, not the behavior.

## Case Shape

Each medium-or-higher case should define:

- non-empty `id`, `category`, `language`, `invocation`, `risk`, and `prompt`
- observable `expected.must` and `expected.mustNot`
- runner and judge identity
- required trajectory evidence in `trace`
- a binary acceptance rule in `gate`

Cover the same intent across English, Korean, and mixed-language prompts. Include explicit, implicit, and contextual invocation so trigger tests do not pass from the skill name alone.

## Measurement

A non-deterministic behavior is not judged from one run.

- Every case declares its own `runs` and its aggregation rule. A case carrying neither is not a gate.
- A gate declares two numbers: the equivalence margin it will accept and the interval width its run count buys. A change inside the margin does not block, and a narrow interval alone never licenses ignoring a regression.
- Report `pass^k` (all k runs succeed) alongside `pass@k` (at least one run succeeds). Only the first is a reliability claim. At a 0.75 per-trial success rate, three consecutive successes occur about 42 percent of the time, so `pass@3` looks strong while `pass^3` is already weak.
- Record the model and runtime version, the case-set hash, the grader version, the benchmark version, and the run count with every result. A result without them cannot be compared later.
- A run that could not execute is `SKIP`, not a pass. A trial aborted by a harness fault is excluded from the denominator and reported as an error trial, never averaged in as a failure and never counted as a pass.
- 3 to 5 cases is a starting point for an instruction-only change and 8 to 15 for a standard prompt change; neither is a validated floor. State the target interval width and the run count together.
- Cost is a peer of quality. Two prompts at similar accuracy can differ by orders of magnitude in tokens and money, so a change that buys a point for ten times the tokens reports both numbers.
- A single-digit difference stays unresolved until the grader and the resource configuration are shown to be equivalent. Re-grading unchanged output has moved a published score by about nine points.
- A saturated case stops producing signal. When a case passes at the ceiling, move it to the regression suite and add a harder case in its place.

## Guard Integrity

- The candidate may not modify the metric procedure, the case set, the judge, the mandatory guards, or the evidence log.
- A rising metric with shrinking guard coverage is a tampering signal, not progress. Fewer executed checks, a changed evaluator, or a reworded metric all count as narrowing.
- When the artifact is allowed to modify its own harness, the evaluator, the guards, and the log stay outside the mutable set, and that change is reviewed as a separate change.

## Judge Calibration

- State the rubric with explicit prohibitions and a counterexample per dimension.
- Give the judge an `unknown` verdict so it does not have to guess.
- Label a small human sample, have the judge label the same set, compute the alignment rate, inspect the disagreements, and revise the judge prompt until the rate clears a stated threshold. Record the judge model, its version, and the achieved rate.
- A judge that looks good on style is not a judge for correctness. Score dimensions separately instead of averaging several judges.
- A judge that was not calibrated is reported as uncalibrated, not as a pass.

## Iteration Loop

Use no loop when direct deterministic checks prove the requested artifact. For optimization, run at most three candidate iterations:

1. Capture baseline output and score, with the run count and the guard set.
2. Declare the target metric or rubric and the improvement direction.
3. Freeze cases, runner, judge, and non-regression guards, and record their versions.
4. Diagnose failure as instruction gap, context gap, schema mismatch, source-boundary issue, safety issue, or model/runtime mismatch.
5. Patch the smallest prompt surface and rerun the same cases.
6. Keep the candidate only when the target improves and every guard still passes at its declared coverage; otherwise discard it.
7. Add a regression case for every new failure pattern, record the cost delta, and record the remaining risk.

## Stop

Stop optimizing when the target is met, three candidates have been evaluated, a guard failure would require broader scope, or remaining failures need missing context, capability, model/runtime, or user authority. Never change the baseline, cases, runner, judge, or guards to claim improvement; a widened guard or a narrowed case set resets the comparison to baseline instead of counting as progress.

## Sources

> Checked 2026-11-03 against the repository instruction base.

| Claim | Source | Checked |
|---|---|---|
| Judgement rules, the eval case shape, `pass^k` alongside `pass@k`, and the run-count record | `instructions/harness-engineering/HARNESS_ENGINEERING.md` | 2026-11-03 |
| The noise floor, re-grading movement, cost as an axis, and eval awareness | `instructions/harness-engineering/references/measurement.md` | 2026-11-03 |
| Grader hierarchy, judge calibration, partial credit, and the reporting rules | `instructions/validation/references/evaluation-design.md` | 2026-11-03 |
| A candidate may not edit the metric, guards, or log, and a narrower guard set is a stop rule | `instructions/autoresearch/AUTORESEARCH.md`, `instructions/autoresearch/references/core-loop.md` | 2026-11-03 |
| The with/without baseline and removing assertions that pass in both conditions | `instructions/skill/references/validation.md` | 2026-11-03 |

No external URL is cited in this file; every rule is a restatement of the repository base above.
