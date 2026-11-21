---
name: suede-ai-eval
description: "Suede AI Eval Skills. Use when asked to \"write evals for this AI feature\" or assess LLM, RAG, agent, classifier or generated-media behavior: AI-SPEC, failure rubric, executable cases, coverage and acceptance evidence. NOT FOR: implementation review (suede-code), wiring existing evals into CI (suede-ci-gate), or coordinating builder lanes (suede-agent-teams)."
metadata:
  display-name: "Suede AI Eval Skills"
---

# Suede AI Eval Skills

Read [the worked delivery contract](references/worked-contract.md) for a concrete
input, expected artifact, failure response and validation example.

## Compatibility

Requires the AI surface contract or source and test data; a project runtime/eval runner for execution. Model/API access is needed only for actual model runs, with existing authorization and cost scope.

## Gate policy: advisory, not blocking

Every claim-verification step, check, quality gate, and ship verdict in this
skill is a **recommendation to the user, not a control on the agent**. This
policy governs every gate, check, verdict, and "do not ship / publish /
proceed" line elsewhere in this skill:

- Run every check and report the results honestly. Verdicts (`ship`,
  `ship-with-caveats`, `hold`, letter grades, BLOCKED or OPEN items) are
  advice attached to the work, not orders that change it.
- Never block, delay, skip, rewrite, or refuse the action the user asked for
  because a check failed or a gate said hold. Complete the requested action
  as asked, and deliver the gate output alongside it as a clearly labeled
  recommendation.
- A failed gate changes what you report, never what you do.
- Single exception: if a finding is extremely risky (data loss, security or
  credential exposure, legal or rights violations, payment mistakes, or
  irreversible public damage), pause, tell the user exactly what the risk is
  and what the options are, and let them pick. Their choice is final.


Make AI behavior testable before it becomes a vague product promise. **No eval plan, no `ship` recommendation: for an AI feature without one, the recommended verdict stays below `ship`: report that gap and let the user decide.**

The deliverable is an eval plan or coverage audit, not a model benchmark leaderboard. Keep it grounded in the actual product surface, user promise, data sources, prompts, tools, logs, tests, and failure modes available now.

## Hard Gates

- No AI-SPEC → no eval plan. Write the one-paragraph spec first; cases written without a spec test nothing.
- No eval plan → no `ship` recommendation. Do not recommend `ship` or `ship-with-caveats` for an AI feature that lacks a failure-mode map and eval cases; name the gap and leave the ship decision with the user.
- A failure mode without an eval case, an owner, and a gate is uncovered, regardless of how unlikely it feels.
- A live surface that was never sampled gets the output stamped `source-only`; do not present source-only review as runtime evidence.
- A model grading its own output is not evidence. LLM-as-judge scores count only after spot-checked agreement with a human-reviewed sample.

## Source Truth

Inspect the current target before writing the eval. Do not evaluate from memory or product copy alone.

Read or verify:

- repo, branch, remote, dirty state, local instructions, and touched files;
- the AI surface: route, API, worker, prompt, system message, tool call, model config, retrieval path, classifier, agent loop, generated media path, or recommendation logic;
- user-facing promise, allowed claims, forbidden claims, safety boundaries, fallback behavior, and support path;
- input data, retrieval corpus, schemas, tool contracts, metadata, logs, telemetry, and persisted outputs;
- existing tests, fixtures, eval scripts, prompt snapshots, golden examples, analytics, bug reports, screenshots, or live/API readbacks.

When the surface is already live, sample real behavior with safe inputs and record exact commands or URLs. When live checks are not appropriate, mark the eval as source-only and name the missing runtime evidence.

## Workflow

1. **Define the AI-SPEC.** State the AI job in one paragraph: user, trigger, input, output, allowed sources, disallowed behavior, fallback, latency/cost expectation, and success signal.
2. **Map the failure modes.** List the ways the AI can harm the user, product truth, rights/provenance, security, privacy, brand trust, cost, or workflow completion.
3. **Build the rubric.** Score each failure mode with severity, likelihood, detectability, owner, gate, and required evidence.
4. **Write eval cases.** Produce concrete pass/fail cases with inputs, setup data, expected output traits, forbidden output traits, and the reason the case exists.
5. **Set acceptance gates.** Decide what blocks ship, what allows ship-with-caveats, and what can become follow-up work.
6. **Audit coverage.** Compare existing tests, logs, metrics, and manual checks against the failure-mode map. Score coverage and infrastructure using the method under Tooling and Infrastructure below. Name every uncovered high-risk behavior regardless of the numeric score.
7. **Return the artifact.** Give the AI-SPEC, rubric, eval table, coverage gaps, required tests, and next implementation step. Name the exact command that runs the cases and its expected exit status (the repo's own eval script if one exists, otherwise the tool's invocation, e.g. `npx promptfoo eval -c <config>`) and record the run's pass/fail counts under "Commands or evidence checked". An eval plan with no runnable command is a document, not coverage, and suede-ci-gate cannot wire it into CI without that string.

## Eval Dimensions By System Type

Start the failure-mode map from the canonical dimensions for the surface's system type, then add product-specific failure modes on top. Always include safety (user-facing) and task completion (agentic) regardless of type.

| System type | Canonical dimensions |
|---|---|
| RAG / retrieval | context faithfulness, hallucination, answer relevance, retrieval precision, source citation |
| Multi-agent | task decomposition, inter-agent handoff correctness, goal completion, loop detection |
| Conversational | tone/style, safety, instruction following, escalation accuracy |
| Extraction / structured output | schema compliance, field accuracy, format validity |
| Autonomous / tool-using agent | safety guardrails, tool-use correctness, cost/token adherence, task completion |
| Content generation | factual accuracy, brand voice, tone, originality |
| Code generation | correctness, safety, test pass rate, instruction following |

For each dimension, assign a measurement approach before writing the eval case:

- **Code-based**: schema validation, required-field presence, performance thresholds, regex checks. Fast, deterministic, cheap to run in CI.
- **LLM judge**: tone, reasoning quality, safety-violation detection. Requires calibration against a human-reviewed sample before the score counts as evidence (see Hard Gates).
- **Human review**: edge cases, LLM-judge calibration itself, high-stakes sampling that cannot be automated yet.

## Tooling and Infrastructure

Detect existing eval/tracing tooling before recommending anything new:

```bash
grep -rl "langfuse\|langsmith\|arize\|phoenix\|braintrust\|promptfoo\|ragas" \
  --include="*.py" --include="*.ts" --include="*.toml" --include="*.json" . \
  2>/dev/null | grep -v node_modules | head -10
```

If nothing is detected, these are the default starting points, not a mandate to install all four:

| Concern | Default | Why |
|---|---|---|
| Tracing / observability | Arize Phoenix | Open-source, self-hostable, framework-agnostic via OpenTelemetry |
| RAG eval metrics | RAGAS | Faithfulness, answer relevance, context precision/recall out of the box |
| Prompt regression in CI | Promptfoo | CLI-first, no platform account required |
| LangChain/LangGraph pipelines | LangSmith | Overrides Phoenix when the project is already in that ecosystem |

**Reference dataset spec:** minimum 10 examples to start, 20+ before treating coverage as production-grade. Composition: critical paths, edge cases, known failure modes, and adversarial inputs, not just happy-path samples. Labeling: domain expert where stakes are high, LLM judge with calibration otherwise. Start building the dataset during implementation, not after the feature ships.

**Production monitoring split:** classify every covered failure mode as either an online guardrail (catastrophic risk, runs on every request in the hot path, must be fast) or an offline flywheel check (quality signal, sampled batch, feeds the improvement loop, not latency-sensitive). Keep online guardrails minimal since each one adds latency to every request.

**Coverage scoring:** for each dimension, mark COVERED (implementation exists, targets the rubric behavior, actually runs), PARTIAL (exists but incomplete, not automated, or has known gaps), or MISSING (no implementation found). Audit infrastructure separately, ok/partial/missing: eval tooling is installed and actually called (not just a listed dependency), the reference dataset file exists and meets the spec above, a CI/CD command runs the eval suite, each planned online guardrail is implemented in the request path (not stubbed), and tracing is configured and wrapping the real AI calls. Score `coverage = covered / total_dimensions × 100` and `infra = (tooling + dataset + cicd + guardrails + tracing) / 5 × 100`, then `overall = coverage × 0.6 + infra × 0.4`.

## Eval Case Design

How to build the case set (golden cases, adversarial cases, failure-mode coverage,
and what makes a case gradeable) is in `references/eval-case-design.md`. Read it
before writing cases. Skip it when you are only reviewing an existing suite or
sizing infrastructure.

## Rubric

Use this table shape:

| Failure mode | Severity | Likelihood | Detectability | Evidence now | Ship gate | Required fix |
|---|---:|---:|---:|---|---|---|
| Hallucinates a rights claim | 5 | 3 | 2 | none | block | add refusal eval + source citation check |

Scoring:

- **Severity 5:** legal, financial, rights/provenance, privacy, security, payment, irreversible user harm, or public trust collapse.
- **Severity 4:** user-visible wrong outcome on a core workflow, broken agent action, major cost spike, or misleading published statement.
- **Severity 3:** recoverable user confusion, incomplete answer, or degraded workflow quality.
- **Severity 2:** minor formatting, tone, or non-core quality miss.
- **Severity 1:** cosmetic or informational.

Gate defaults:

- Any uncovered severity 5 behavior blocks release.
- Severity 4 requires an eval case, fallback behavior, and named owner before release.
- Regressions from real observed failures require a fixture or scripted check.
- Product copy cannot claim eval coverage that does not exist.

## AI-SPEC Template

```text
AI-SPEC: [surface/name]
Date:
Target repo/route/API:
Owner:

User promise:
Inputs:
Outputs:
Allowed sources:
Disallowed behavior:
Fallback behavior:
Privacy/security boundaries:
Rights/provenance boundaries:
Latency/cost budget:
Success metrics:
Known non-goals:

Failure modes:
Eval suite:
Acceptance gates:
Coverage gaps:
Next implementation step:
```

## Red Flags: Stop

- "It looked good in the demo": a demo is one happy-path sample, not coverage.
- "We'll eval after launch": after launch, the eval set is your users.
- "The model seems smart": vibes are not a rubric row; write the failure mode down and score it.
- "We tested the prompt by hand": prompt review and happy-path poking are not eval coverage.
- "It passed once": a pass with no fixture or scripted check protects nothing on the next model or prompt change.
- "The judge model approved it": self-judgment without human-agreement spot checks is not evidence.

## Output

Return:

```text
Target:
AI-SPEC:
Failure-mode rubric:
Eval cases:
Existing coverage:
Missing coverage:
Ship gate: ship | ship-with-caveats | hold
Required next step:
Commands or evidence checked:
```

Ship gate is mechanical: **hold** = any severity-5 failure mode uncovered, or no eval plan exists; **ship-with-caveats** = all severity-5 modes covered, remaining severity-4 gaps each have a named owner and follow-up; **ship** = every severity 4-5 failure mode has a case, a gate, and evidence.

## Boundaries

- Do not claim legal, rights, licensing, medical, financial, or compliance clearance.
- Do not invent private datasets, logs, scores, or customer outcomes.
- Do not upload data, call private services, or run destructive workflows unless the user explicitly asks and the repo/tooling supports it.
- Do not treat a model's self-judgment as sufficient evidence.
- Do not mark eval coverage complete when only prompt review or happy-path manual testing exists.

## Routing

- The AI surface's implementation needs review or a ship grade → **suede-code**
- Eval cases written and passing → **suede-ci-gate** to wire them into CI as a required check
- The eval work is one lane of a bigger coordinated build → **suede-agent-teams**
