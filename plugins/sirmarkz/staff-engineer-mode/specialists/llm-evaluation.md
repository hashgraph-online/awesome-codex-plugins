---
name: llm-evaluation
description: "Use when designing or changing LLM, retrieval-grounded, prompt, or agent evals needing datasets, traces, graders, thresholds, slices, or triage"
---

# LLM And Agent Evaluation Harness Engineering

## Iron Law

```
NO MODEL-BACKED CHANGE WITHOUT EVAL CASES, SCORING RULES, THRESHOLDS, REGRESSION HISTORY, AND FAILURE TRIAGE
```

If you cannot say what got better, what got worse, and which failures block release, the eval is not a release check.

## Overview

LLM and agent behavior is production behavior when prompts, tools, retrieval, actions, or model outputs affect users or workflows.

**Core principle:** infer the eval unit from the requested workflow, then build the matching harness with representative cases, stable scoring, slice coverage, regression history, and release thresholds before trusting model-backed changes.

## When To Use

- The user is designing, building, changing, or operating LLM, retrieval-grounded, prompt, agent, grader, regression, acceptance-threshold, or model-backed workflow evals.
- A prompt, model, retrieval source, tool policy, task-run workflow, or agent loop changes and needs release checks.
- Existing evals are flaky, too small, too easy, judge-biased, or disconnected from production failures.
- You need repeatable checks for quality, refusal, formatting, task completion, trace correctness, final-state correctness, or user-impact slices.

## When Not To Use

- The main risk is prompt injection, tool misuse, data leakage, or unsafe actions; use `llm-application-security` instead.
- The main work is classical ML drift, training-serving skew, or model-serving readiness; use `ml-reliability-and-evaluation` instead.
- The request is broad AI coding-agent controls; use `ai-coding-governance` instead.
- The request is product strategy for which model to choose with no engineering check.

## Eval Unit Boundary

| Mode | Eval Unit | Primary Evidence |
| --- | --- | --- |
| LLM output | One generated output from prompt and context inputs | Expected answer, format, refusal, grounding, and versioned inputs. |
| Retrieval-grounded | One generated output from retrieved evidence | Retrieval fit, cited-context use, answer correctness, and versioned corpus inputs. |
| Agent | One end-to-end task run | Behavior trace, tool calls, observations, state updates, final state, and final artifact. |

Classical ML prediction evals belong to `ml-reliability-and-evaluation`; keep this specialist focused on LLM output, retrieval-grounded, and agentic task-run evals.

## Info To Gather

- Current work phase, next decision, what is known, and assumptions where details are missing.
- Intended use, affected user groups, workflow, user tasks, expected outputs, unacceptable failures, misuse context, human escalation or override path, and release decision to support.
- Eval cases, production examples, synthetic cases, edge cases, slices, and known regressions.
- Scoring method, graders, rubrics, deterministic checks, human judgment, and tie-break rules.
- For agentic workflows: task context, allowed tools, environment assumptions, trace expectations, tool-call assertions, state updates, final-state assertions, and repeat-run policy.
- For agentic adversarial evals: the white-box risk architect, black-box or gray-box case author, white-box reviewer, context each role saw, and whether expected traces, reference solutions, implementation notes, happy-path examples, and route rationales were withheld from the case author.
- Thresholds, confidence needs, flake rate, baseline result, and comparison target.
- Versioned prompts, models, retrieval inputs, tools, datasets, and harness code.
- Failure triage workflow, severity, waiver rules, and re-run policy.

## Workflow

1. **Name the decision.** State whether the eval checks merge, release, prompt change, model change, or rollback.
2. **Frame the risk context.** State intended use, affected user groups, unacceptable harms or workflow failures, misuse context, and human escalation or override expectations where impact warrants it.
3. **Choose the eval unit dynamically.** Use the user's requested artifact to decide whether each case checks one generated response, one retrieval-grounded response, or one agentic task run; do not force agent trace fields onto non-agent evals.
4. **Build representative cases.** Include production-like tasks, edge cases, regressions, adversarial examples, and important user slices. For agentic adversarial evals, split access by role: a white-box eval architect defines risk slices, interfaces, mitigations, and coverage goals; a black-box or gray-box case author receives only the target boundary, allowed interface/tools, risk intent, and failure class; a white-box reviewer validates coverage and measurability after cases exist. Withhold expected traces, reference solutions, implementation notes, happy-path examples, and route rationales from the case author. Prefer a separate adversarial subagent or independent reviewer for case writing, then curate duplicates and invalid cases before adding them.
5. **Separate scoring types.** Use exact checks for structured requirements, trace and final-state checks for agent runs, rubric scoring for judgment, and human judgment for ambiguous high-impact cases. For retrieval-grounded evals, score retrieval quality separately from grounding and answer correctness so failures are attributable. For agent runs, fix task environment, tool fixtures, run isolation, seeds, and repeat-run policy so traces are reproducible and variance is measured.
6. **Control grader risk.** Define rubrics, blind comparisons where useful, calibration cases, and checks for scoring drift.
7. **Set thresholds first.** Declare pass, warn, and block criteria before looking at the new result. Report sample size and statistical uncertainty on eval deltas before gating.
8. **Guard against contamination.** Use held-out sets and canary strings so cases cannot leak into training or few-shot context.
9. **Version inputs.** Link prompts, model, retrieval corpus, tool policy, eval cases, graders, harness code, and task environment to the result.
10. **Triage failures.** Classify blockers, acceptable regressions, flaky cases, data issues, trace issues, and missing coverage.
11. **Keep history.** Track baseline, deltas, regressions, waived failures, repeated-run variance, and production incidents that should become future cases.

## Synthesized Default

Use a versioned eval harness whose evidence matches the requested workflow: output checks for LLM responses, retrieval and grounding checks for retrieval-backed answers, and trace plus final-state checks for agent runs. Keep representative cases, slice coverage, deterministic checks where possible, calibrated rubric graders where needed, predefined thresholds, regression history, and explicit failure triage. For a new harness with no history, the first run establishes the baseline that regression history accrues from. Treat aggregate score improvements as insufficient when critical slices or known failure modes regress.

## Phase Behavior

- Ideation: identify risks, defaults, unknowns, options, and the next decision before code exists.
- Design: shape the target artifact, tradeoffs, checks, and details to gather.
- Development: guide sequencing, code boundaries, checks, and acceptance criteria.
- Testing: define release-blocking tests, evals, fixtures, and failure probes.
- Release: define rollout, observability, abort, rollback, and readiness details.
- Maintenance: define owners, drift checks, cleanup triggers, and refresh cadence.
- Existing artifact: use current code, docs, telemetry, incidents, or diffs as context for the next engineering decision; do not wait for a finished artifact before guiding design, build, release, or operation.
- Missing details: state assumptions and say what to check next instead of blocking lifecycle guidance.

## Exceptions

- Early prototypes may use exploratory evals if they are not release checks.
- Human judgment can supplement automated scoring for high-impact or ambiguous tasks, but should use a written rubric.
- Low-risk copy changes may use a narrow regression set if output constraints and affected journeys are limited.

## Response Quality Bar

- Lead with the eval harness design, release check, failure triage, or threshold decision requested.
- Cover decision, eval unit, cases, slices, scoring, thresholds, versioning, regression history, and failure handling before optional model discussion.
- Select mode-specific evidence from the prompt: response evidence for LLM output evals, retrieval evidence for retrieval-grounded evals, and trace/final-state evidence for agentic evals.
- Make recommendations actionable with dataset changes, grader rules, pass/fail criteria, and rerun policy where relevant.
- Name the details to inspect, such as eval cases, baseline runs, grader rubric, flake rate, slice results, trace logs, final-state checks, versioned inputs, and failure log; do not state details you have not seen.
- Stay technology-agnostic by default: do not introduce provider, product, framework, database, protocol, or command names unless the user supplied them or explicitly requested tool-specific guidance.
- Stay inside model-backed evaluation checks. Route security, ML serving, or AI coding controls only when those risks dominate.
- Be concise: prefer eval matrices and release checks over generic eval theory.

## Required Outputs

- Output shape: render the matching shared template headings or tables in the reply, or use the same shape.
- Eval harness specification.
- Intended-use, affected-user, unacceptable-failure, misuse, and escalation context.
- Eval-unit and pipeline boundary, scoped to the requested LLM, retrieval-grounded, or agentic workflow.
- Case inventory with production, synthetic, edge, regression, and slice coverage.
- Adversarial-case access record for agentic adversarial evals: white-box architect, black-box or gray-box case author, white-box reviewer, context withheld from the author, failure intent, and curation result.
- Scoring and grader rubric.
- Trace, tool-call, state, and final-artifact checks for agentic workflows.
- Thresholds for pass, warn, block, and rollback.
- Versioned-input record.
- Failure triage table with disposition and next action.
- Regression history and case-promotion policy.

## Checks Before Moving On

- `decision_named`: eval result maps to a merge, release, rollback, or investigation decision.
- `risk_context`: intended use, affected user groups, unacceptable failures, misuse context, and escalation or override expectations are stated where relevant.
- `case_coverage`: representative cases include critical tasks, slices, and known regressions.
- `adversarial_independence`: for agentic adversarial evals, white-box risk design is recorded, the case author used black-box or gray-box context without expected traces, reference solutions, implementation notes, happy-path examples, or route rationales, and white-box review happened after case generation.
- `scoring_defined`: checks, graders, rubrics, and tie-break rules are explicit.
- `mode_evidence`: retrieval evals separate retrieval quality from answer correctness; agent evals fix a reproducible environment and repeat-run policy.
- `trace_and_state_checks`: agentic evals check required tool calls, observations, state updates, final state, and final artifact where relevant.
- `thresholds_predeclared`: pass, warn, and block criteria are set before judging the change.
- `version_lineage`: prompts, model, data inputs, tools, eval cases, graders, and result are linked.
- `contamination_guard`: eval sets are held out or canary-marked to detect contamination.
- `delta_significance`: eval-gate decisions report sample size and uncertainty, not point deltas.

## Red Flags - Stop And Rework

- A single aggregate score hides critical slice regressions.
- The grader rubric changes between baseline and candidate.
- Eval cases are generated from the same prompt being tested with no independent check.
- Agentic adversarial cases are written from expected traces, reference solutions, implementation notes, happy-path examples, or route rationales.
- The same agent writes the happy path and final adversarial cases without a separate black-box author or white-box review.
- Failures are waived without a reason or an expiry.
- Production incidents do not become regression cases.

## Common Mistakes

| Mistake | Correction |
| --- | --- |
| Score first, threshold later | Set pass and block criteria before running. |
| Only happy-path cases | Add edge, adversarial, and regression cases with black-box or gray-box case authorship. |
| Unversioned prompts | Link every input to every result. |
| Treating judge output as truth | Calibrate rubrics and inspect failures. |
