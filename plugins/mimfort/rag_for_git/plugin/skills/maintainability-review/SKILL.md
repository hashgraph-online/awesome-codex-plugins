---
name: reviewer_maintainability-review
description: "Review code changes only for maintainability risks: unnecessary complexity, poor readability, duplication, weak separation of concerns, and misalignment with repository conventions. Use when the user explicitly asks for maintainability review, code quality review, clean code review, complexity review, readability review, simplification review, or how to simplify changed code without changing behavior."
---

# Maintainability Review

<!-- include: _common/dimension-scope.md -->

<!-- include: _common/tool-usage.md -->
<!-- include: _common/reviewer-grounding.md -->
In `/reviewer_review-pr` use the PR-session tools above. Standalone (no PR session): use
the session-less tools per the reviewer-grounding block when reviewer is connected and the
index is fresh; otherwise fall back to grep/Read.

## Goal

Look only for maintainability risks in the selected changes. Ignore performance,
security, and general correctness unless they directly explain a maintainability
concern.

Prioritize findings such as:

- unnecessary branching, flag combinations, and deep nesting that increase cognitive
  load;
- large or mixed-responsibility functions that became harder to understand;
- duplication or near-duplication that should likely be consolidated;
- abstractions, wrappers, or indirection layers that hide a simple flow without a
  clear payoff;
- hidden side effects, implicit contracts, or unclear data flow;
- naming or structure that materially harms readability or makes intent harder to
  recover;
- changes that drift away from established repository patterns or documented
  contributor rules;
- behavior changes that should likely carry nearby tests according to project
  practice;
- edits to generated artifacts when the repository expects source changes plus
  regeneration.

## Repository Context

Before raising project-practice findings, read the repository-local guidance that
governs the current workspace.

Prefer this order:

1. In `/reviewer_review-pr`, read `CLAUDE.md` or `AGENTS.md` via `read_file`; in standalone,
   read them from disk.
2. Read the nearby implementation to understand existing patterns.
3. Compare the change against the established local style before flagging it.

Do not treat personal preference as a project convention.

## Method

1. Read the diff first.
2. Open only the nearby code needed to understand the changed path.
3. Prefer concrete maintainability costs over vague "clean code" opinions.
4. State assumptions explicitly when a finding depends on local context.
5. Suggest a simpler alternative that preserves behavior and better fits local
   patterns; put this in the `suggestion` field.
6. Avoid review spam. Do not invent nits.

## Simplification Heuristics

Prefer suggestions such as:

- split a mixed-responsibility function into a small orchestration layer plus focused
  helpers;
- replace deeply nested conditionals with guard clauses or flatter control flow;
- collapse pass-through wrappers that add little or no meaning;
- replace duplicated branches with a shared helper or data-driven mapping;
- move side-effect-free transformation logic closer together and isolate I/O
  boundaries;
- reuse established project helpers, managers, or patterns instead of introducing
  ad-hoc flow;
- keep changes local when a broader abstraction is not justified by the diff.

Do not suggest refactors that increase indirection without a clear readability win.

## What Not To Flag

Do not raise findings for:

- purely stylistic preferences when the code is already clear;
- unchanged legacy code outside the requested review scope;
- hypothetical future abstractions with no present need;
- formatter or linter nits that are already handled automatically;
- rename suggestions unless the current naming materially impairs understanding.

## Severity

- `critical` / `high`: the change introduces major complexity, unclear control flow,
  or strong convention drift that is likely to cause future bugs or make the code
  meaningfully harder to modify safely.
- `medium`: the change adds noticeable complexity or weakens readability or
  consistency enough that it should probably be simplified before merge.
- `low`: the change is acceptable but has a worthwhile simplification or cleanup
  opportunity.

## Output

Return only actionable findings.

Return ONLY the findings JSON used by the review pipeline, with
`"category": "maintainability"`:

<!-- include: _common/findings-schema.md -->
- Calibrate `confidence` against concrete, grounded evidence: a duplicated block you can quote
  or a real complexity hotspot → 0.8+; a subjective readability concern → 0.5–0.7; pure taste
  → ≤ 0.4 (drop).
Set "category" to "maintainability"; "side" is always "RIGHT".

The `suggestion` field replaces what in the original Codex format appeared after
`Simplification:` — put the concrete simplifying alternative there.

<!-- include: _common/dimension-output-tail.md -->
