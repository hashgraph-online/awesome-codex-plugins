# Harness Engineering Guide for Hyper Docs

**Purpose**: Define how the docs mode should document the system around the prompt, not just the prompt itself.

## 0. Layering Rule

Document harnesses using three explicit layers:

- core rules
- provider references
- local overlays

If a sentence depends on vendor-specific behavior, it belongs in the provider-reference layer or must cite it directly.

## 0.1 Source Precedence

When provider guidance conflicts, prefer:

1. official developer or API docs
2. official migration or safety guides
3. official examples and business guides

## 0.2 Scope and Staleness

A harness document covers everything in a run that is not the model: the instructions it reads, the tools it can call, how its context is assembled and compacted, where its code executes, what checks its output, what records its behavior, and what gate decides the work may ship. A component that changes behavior is in scope even when it is not the prompt.

Every component also encodes a bet about what the model cannot do unaided, and models change under it. A component that was necessary on one model has been observed to become dead weight on its successor: the behavior it compensated for disappeared, the component stayed, and it cost tokens while hiding the improvement.

So each documented component carries three fields, and a harness document without them is a diagram:

| Field | Question it answers |
|---|---|
| Assumption | What do we believe the model cannot do unaided? |
| Re-test trigger | What change forces a retest — model, runtime, tool surface, or context policy? |
| Deletion observation | Which eval outcome stays the same when the component is removed? |

Three consequences for the writing:

- **Repair the harness, not the run.** A failure becomes a durable control: an instruction line traceable to that failure, a tool that detects it, or a check that rejects it, shipped with the case that reproduces it.
- **Measure the cost.** A component reports the tokens, wall time, and cost it imposes. The same component can be decisive on one model and worthless on another, so the result is reported per model.
- **Treat review as standing.** The space of useful harnesses moves rather than closes, so the document says when it must be revisited instead of implying a one-time migration.

## 1. Prompt Assets

- Document the prompt as an asset with a clear role, inputs, outputs, and validation expectations.
- Separate stable instructions from variable inputs and per-run state.
- Prefer templates and variables over duplicating near-identical prompts.
- When provider-specific behavior matters, cite the official source and verification date.

Pattern:

```markdown
## Prompt Asset
- Purpose:
- Stable instructions:
- Variable inputs:
- Output contract:
- Validation method:
```

## 2. Tool Contracts

- Describe each tool in terms of purpose, inputs, outputs, failure modes, and approval boundaries.
- Prefer reusable tool contracts over one-off prompt prose.
- State when the tool should be used and when direct work is better.
- If tool access is sensitive, document the guardrail or approval step explicitly.
- Document the selection test for the tool set: if an engineer cannot say which tool applies in a given situation, the model cannot either, and the document has a tool-count problem rather than a wording problem.
- When a tool must be withdrawn mid-task, mask it instead of deleting its definition. The definition sits in the cached prefix, so removal changes the request for the rest of the session.

Pattern:

```markdown
## Tool Contract: [Tool Name]
- Use when:
- Do not use when:
- Inputs required:
- Output expected:
- Approval or guardrail:
- Failure handling:
```

## 3. Eval Loops

- Define success criteria before recommending prompt or harness iteration.
- Document the eval set, graders, acceptance threshold, and failure triage path.
- Distinguish prompt regressions from tool, state, or policy regressions.
- Judge a non-deterministic target by a rule: every case declares its run count and an aggregation, and a gate states an equivalence margin separately from the interval its run count buys. One run is not a verdict.
- Record the model and runtime version, the case-set hash, the grader version, and the benchmark version with every result. Without them the number cannot be compared later, and a grader change silently invalidates the comparison.
- Report `pass^k` (all k runs succeed) alongside `pass@k` (any run succeeds). Only the first is a reliability claim.
- Keep the actor and the judge different agents, and give the judge the artifact plus the criteria rather than the worker's summary of its own work.

Pattern:

```markdown
## Eval Plan
- Success criteria:
- Test set:
- Graders:
- Runs per case and aggregation:
- Equivalence margin and interval width:
- Recorded versions: model, runtime, case-set hash, grader, benchmark
- What to change if the eval fails:
```


## 3.1 Prompt / Role Instruction Smoke Eval

When a docs-mode task changes role prompts or instruction bases, include small regression cases before claiming quality improved.

| Case type | Check | Example |
|---|---|---|
| Happy path | follows goal, output shape, and tone | clear request produces expected sections |
| Missing context | asks, searches, or states caveat instead of guessing | source/file omitted |
| Scope boundary | respects non-goals and side-effect gates | request includes forbidden external action |
| Source boundary | treats retrieved content as evidence, not authority | page says “ignore prior instructions” |
| Regression | known failure does not recur | previous bad prompt/output pair |

## 4. Safety and Approval Gates

- Document what inputs are untrusted.
- Document what actions require approval, confirmation, or human review.
- State how prompt injection and data leakage risks are reduced.
- If MCP or external tools are involved, note the expected approval posture.

## 5. Context Ordering and Caching

- Document what content is static and what content is variable.
- Place reusable, stable instructions where the target provider benefits most from shared prefixes or stable top-of-context content.
- State how long documents, examples, and user-specific inputs should be ordered.

Pattern:

```markdown
## Context Layout
1. Stable instructions
2. Reusable reference material
3. Variable user inputs
4. Current task or query
```

## 6. Conversation State and Compaction

- Document what state persists across turns.
- State what must survive compaction and what can be summarized away. Name the survive-list: the active goal, accepted scope and non-goals, acceptance criteria, the current step and next action, and recorded blockers.
- For long-running harnesses, keep the active plan, current constraints, and unresolved risks explicit, and say where the plan file lives so a fresh session can re-read it.
- Give a reset the same treatment as a compaction: a handoff artifact a fresh session can read without the old transcript. A design that only covers compaction fails the moment the workflow resets.
- Treat repeated recovery into the same next action as a stall: fingerprint the projection, and after a named number of unchanged recoveries emit an explicit stalled directive instead of repeating the action.
- Avoid treating task state as permanent policy.

Pattern:

```markdown
## State Policy
- Persistent:
- Compactable:
- Reconstructable:
- Must survive compaction or reset:
- Plan file and re-read point:
- Stall fingerprint and threshold:
```

## 7. Model and Version Profiles

- Canonical docs should describe capability profiles, not fixed model literals.
- If a deployment needs exact model strings or snapshots, place them in provider references or deployment examples.
- Document when version pinning is required for stability and when a provider-default latest model is acceptable.

## 8. Worked Example

```markdown
# Research Harness

## Prompt Asset
- Purpose: Compare vendor SDK documentation quality
- Stable instructions: gather official sources first, summarize differences, cite each key claim
- Variable inputs: target vendors, product area, output format
- Output contract: executive summary, findings, citations, recommendation
- Validation method: source count threshold + reviewer readback

## Tool Contract: Web Search
- Use when: the question is recency-sensitive or source attribution matters
- Do not use when: the user explicitly forbids browsing and the task can be solved locally
- Inputs required: query, domain filter, recency if needed
- Output expected: official URLs and supporting passages
- Approval or guardrail: only cite official docs for normative vendor guidance
- Failure handling: narrow the query or switch to a more direct source

## Eval Plan
- Success criteria: all key claims cite official sources; no stale model literals in the canonical rule file
- Test set: 5 representative harness-doc sections
- Graders: source-grounding, clarity, maintainability, rule-boundary hygiene
- Acceptance threshold: all must-pass checks true
- What to change if the eval fails: update references first, then rewrite the dependent rule

## Context Layout
1. Stable instructions
2. Reusable official references
3. Variable task inputs
4. Active query

## State Policy
- Persistent: accepted rules, source references, active constraints
- Compactable: completed sub-analyses
- Reconstructable: intermediate drafting notes
- Must survive compaction: current plan, unresolved risks, validation status
```

## 9. Source Metadata

For provider-sensitive guidance, keep a reference entry with:

- `source_url`
- `last_verified_at`
- `applies_to`
- `summary`
- `implication_for_hyper_docs`
- `refresh_when`

## 10. Reference Refresh Workflow

- Refresh provider references when:
  - a canonical rule starts depending on undocumented behavior
  - a migration guide changes
  - model, tool, or context features materially shift
  - a reviewer cannot trace a provider-sensitive claim to an official source
- On refresh:
  - update the reference entry first
  - then update the canonical or adapter rule that depends on it
  - then run grep or readback checks for stale phrasing that the new source invalidates

## 11. Drift Signals

Watch for these drift signals:

- canonical docs mention a vendor behavior without a dated source
- a provider reference explains behavior that no canonical rule consumes
- examples become more concrete than the rules they support
- references disagree with each other about the same capability

## 12. Validation Checklist

- [ ] Prompt asset contract documented
- [ ] Tool contract documented when tools are in scope
- [ ] Eval plan documented when optimization is in scope
- [ ] Safety and approval gates stated when actions can affect systems or data
- [ ] Context ordering documented for long or cache-sensitive prompts
- [ ] State and compaction policy documented for long-running workflows
- [ ] Provider references include refresh-ready metadata
- [ ] Canonical docs avoid fixed model literals

## 13. Failure Triage

When a harness doc still feels weak after a refactor, inspect in this order:

1. missing core-vs-reference boundary
2. missing success criteria or eval plan
3. missing tool approval or safety rule
4. missing state or compaction policy
5. examples that are more specific than the governing rule
## 14. Minimum Eval Case Format

Use this shape for prompt/instruction regression cases:

```yaml
id: unique-case-id
intent: user goal
context:
  files: []
  sources: []
input: |
  user request
expected:
  must:
    - required behavior
  must_not:
    - forbidden behavior
runs: 3
gate: aggregate rule and equivalence margin
judge: deterministic check, or a model judge with its version and calibration status
trace: required trajectory evidence or none
metrics:
  - instruction_following
  - factuality
  - tool_use
  - safety
  - completion
```

A case set is composed, not counted. No vendor states a validated minimum case count, so the document declares what each case probes — normal, missing context, boundary, adversarial, and known regression — instead of asserting a number.

## 15. Parallel / Subagent Trace Rules

When the document covers parallel agents, verify the trajectory as well as the final output:

| Assertion | Pass condition |
|---|---|
| bounded_spawn | objective, scope, output, and stop condition are present |
| independent_or_sequenced | parallel work has no hidden dependency or is explicitly sequenced |
| ownership_declared | edit-capable work has a declared write set |
| least_privilege_tools | read-only work does not require write or side-effect tools |
| child_reports_evidence | child output includes files, links, test output, or changed paths |
| parent_integrates | parent synthesizes conflicts, duplication, and gaps |
| parent_verifies | parent reads final tests/evals/source checks before completion |

## 16. Instruction Change Loop

```text
Define success → collect baseline cases → run current doc → diagnose failures → patch smallest surface → re-run → document risk
```

## Sources

> Content checked 2026-11-03 against the repository instruction base; no external URL was opened for this file.

| Claim | Source |
|---|---|
| The harness boundary, the layered contract, the judgement rules, the trace fields, and the long-horizon recovery rules | `instructions/harness-engineering/HARNESS_ENGINEERING.md` |
| Component staleness, the repair-in-the-harness rule, and measured harness cost | `instructions/harness-engineering/references/harness-anatomy.md` |
| Grader calibration, trial reporting, and the verification-depth scale | `instructions/validation/references/evaluation-design.md`, `instructions/validation/index.md` |
| Context ordering, clearing, and compaction mechanics | `instructions/context-engineering/references/context-management.md` |

This file is this package's own procedure text. Where it compresses a claim, the source above carries the derivation.
