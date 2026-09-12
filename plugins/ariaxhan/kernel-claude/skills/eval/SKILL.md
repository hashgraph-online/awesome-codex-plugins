---
name: eval
description: "Eval-Driven Development (EDD) for AI workflows. pass@k metrics, capability evals, regression evals. Triggers: eval, edd, pass@k, capability, regression, benchmark."
allowed-tools: Read, Bash, Write, Edit, Grep, Glob
kernel:
  kind: methodology
  version: 1
  side_effects: none
  confirmation: none
---

<skill id="eval">

<prerequisite>
AgentDB read-start has run. Check for existing eval definitions in _meta/research/.
Understand what behavior you're evaluating before writing evals.
</prerequisite>

<reference>
Skill-specific: skills/eval/reference/eval-research.md
</reference>

<core_principles>
1. DEFINE BEFORE CODE: Evals written first force clear thinking about success criteria.
2. CODE GRADERS > MODEL GRADERS: Deterministic checks beat probabilistic judgments.
3. STRUCTURAL SEPARATION FOR HIGH-STAKES: When stakes are real (security, payments, eval-of-evals, agent quality scoring), use the blind-evaluator agent — never self-score. Self-scoring inflates results ~36% structurally; procedural separation ("I won't peek") does not fix it.
4. TRACK PASS@K: pass@1 (first attempt), pass@3 (within 3 attempts). Target pass@3 > 90%.
5. REGRESSION BEFORE SHIP: Every change must pass existing evals before merge.
6. FAST EVALS GET RUN: Slow evals get skipped. Keep evaluation fast.
</core_principles>

<workflow>
1. DEFINE: Write eval criteria before implementation. (gate: criteria exist in writing before any code)
2. IMPLEMENT: Code to pass defined evals.
3. EVALUATE: Run evals, record pass@k. (gate: pass@3 > 90% for capability; pass^3 = 100% for regression)
4. REPORT: Document results in eval report format. See reference for template.
</workflow>

<blind_evaluation_protocol>
Use when implementing agent would otherwise score its own output (high-stakes: security, payments, agent quality):

1. Spawn `agents/blind-evaluator.md` as a fresh agent.
2. Pass ONLY: problem statement, rubric (3-7 criteria with PASS conditions + weights), artifact path.
3. Do NOT pass: implementer's checkpoint, summary, commit message, prompt, or expected solution.
4. (gate: blind evaluator runs contamination check — if forbidden inputs detected, returns INVALID; clean inputs and retry)
5. (gate: confidence < 0.7 from blind evaluator → escalate to human grader)

Two-phase eval protocol:
- Run 1: implementing agent solves cold, no eval feedback. Blind evaluator scores. This is the externally-reportable number.
- Run 2: implementing agent gets Run 1 score + rubric breakdown, then optimizes. For iteration only.
</blind_evaluation_protocol>

<metrics>
pass@k: "At least one success in k attempts"
- pass@1: First attempt success rate
- pass@3: Success within 3 attempts (typical target: > 90%)

pass^k: "All k trials succeed"
- pass^3: 3 consecutive successes
- Use for critical paths (auth, payments)

See reference for calculation formula and worked examples.
</metrics>

<grader_selection>
1. Code-based (preferred): grep, test suite, build, type-check — deterministic, fast.
2. Model-based: for open-ended outputs that can't be checked deterministically. Run multiple times, take majority.
3. Human: required for security-sensitive changes, UX evaluation, legal/compliance.

See reference for full grader templates and examples.
</grader_selection>

<anti_patterns>
<block id="eval_after_code">Writing evals after implementation tests existing bugs, not requirements.</block>
<block id="model_grader_overuse">Model-based grading is slow and probabilistic. Prefer code graders.</block>
<block id="skip_regression">Every change must pass regression evals. No exceptions.</block>
<block id="slow_evals">Evals that take > 30s get skipped. Keep them fast.</block>
<block id="no_tracking">Track pass@k over time. Declining reliability is a signal.</block>
<block id="self_score">For any user-facing or high-stakes eval, the implementing agent scoring its own work inflates results ~36%. Spawn blind-evaluator instead.</block>
<block id="post_merge_eval">Evaluating against a codebase that already contains the canonical solution = answer key in the eval set. Use pre-merge snapshots or a separate fixture.</block>
<block id="greenfield_in_golden_dataset">Greenfield tickets in the golden eval set collapse to self=10, blind=3. Greenfields are not evaluable as solved tasks — exclude them from the dataset.</block>
<block id="context_breadth_before_baseline">Optimizing how much context the evaluator gets before establishing a baseline score = can't distinguish signal from noise. Run minimal-context baseline first, then test additions one at a time.</block>
</anti_patterns>

<on_complete>
agentdb write-end '{"skill":"eval","eval_type":"capability|regression","pass_at_1":"<X%>","pass_at_3":"<Y%>","failures":["<list>"]}'

Record eval type, pass rates, and any failures for future reference.
</on_complete>

</skill>
