---
name: codex-quota-optimizer
description: Optimize Codex Plus/Pro usage before and during coding tasks. Use when the user wants to save Codex quota/credits, reduce token or context waste, choose a cheaper model/reasoning level, avoid unnecessary repo scans/tests/subagents, or plan an implementation with the smallest reliable execution footprint. Do not use when the user explicitly prioritizes maximum quality regardless of usage.
---

# Codex Quota Optimizer

Optimize for **useful work per unit of Codex allowance**, not for the shortest answer.

## 0. Operating principle

Use the cheapest execution path that can still meet the acceptance criteria. Escalate only when evidence shows the cheaper path is insufficient.

Never claim an exact remaining quota unless the current Codex client/account exposes it. If quota state matters, tell the user to check `/status` or the usage dashboard, then continue with the best available strategy.

### Zero-friction invariant

The optimizer must not become the overhead.

- Do not make an additional model call just to classify or budget a task.
- Do not add network requests for CQO classification, journaling, or auditing.
- Do not put a blocking budget gate in front of normal Codex execution.
- Do not ask the user for confirmation merely because a soft budget was exceeded.
- Do not spawn subagents on CQO's behalf.
- The Skill must remain fully useful when the optional `cqo` CLI is never installed or run.

See `references/zero-friction.md`.

## 1. Read only what you need

Before broad exploration:

1. Inspect the task request, current diff, and repository instructions (`AGENTS.md`).
2. Prefer targeted search (`rg`, file-specific reads, manifests, changed files) over recursive reading.
3. If the repository is unfamiliar, run `scripts/repo_snapshot.py --compact` once before opening many files.
4. Do not re-read unchanged files already understood in the current task unless a contradiction appears.
5. Read generated/vendor/build directories only when directly relevant.

See `references/context-policy.md` for detailed rules.

## 2. Classify the task before execution

Assign one class internally as part of the existing reasoning turn. Do not call another model solely to perform classification.

- **XS** — one-file, mechanical, obvious acceptance criteria.
- **S** — narrow feature/fix, 1–3 files, known pattern.
- **M** — several files, modest design judgment or integration.
- **L** — cross-cutting change, unclear architecture, migration, complex debugging.
- **XL** — high-risk redesign, multi-system work, security-critical or ambiguous end-to-end task.

Then choose the lowest adequate model/reasoning path:

- **XS/S:** prefer Luna or the fastest/cheapest available setting, low reasoning.
- **M:** prefer Terra, low/medium reasoning.
- **L:** Terra medium first; escalate to Sol only for unresolved design/debugging complexity.
- **XL:** Sol medium/high; Astra only when the task truly needs strongest multi-step/tool reasoning and the account exposes it.

Availability varies by plan/client. If a named model is unavailable, choose the nearest cheaper/faster model with the same role.

Do not use Max/Ultra by default. Do not spawn subagents merely because they are available.

See `references/model-routing.md`.

## 3. Use an execution budget

For every non-trivial task, maintain this internal budget:

- **Discovery budget:** enough reads/searches to locate the change surface.
- **Edit budget:** minimum files required to satisfy acceptance criteria.
- **Verification budget:** targeted checks first; broad checks only at the final gate or when evidence demands them.

These are **soft budgets**, never execution gates:

- Stop discovery once the relevant dependency path is understood.
- Stop editing once acceptance criteria are met; avoid opportunistic refactors.
- Stop verification after relevant tests/type/lint checks pass unless the change is high risk.
- If another file, test, or reasoning step is required for correctness, continue without interrupting the user.
- If scope expands, reclassify internally and keep moving; do not request permission just because the initial budget was too small.

## 4. Plan economically

For S/M/L/XL tasks, state or maintain a compact plan with:

1. target behavior,
2. likely files,
3. minimal verification,
4. escalation trigger.

Do not create a long speculative plan before reading the minimum repository evidence.

Prefer one coherent implementation turn over repeated micro-turns that each reload context.

## 5. Edit minimally

- Change the smallest coherent surface.
- Reuse existing helpers, patterns, components, and tests.
- Avoid formatting unrelated files.
- Avoid dependency upgrades unless required.
- Avoid generated-file churn unless generation is part of the task.
- Batch logically related edits rather than repeatedly opening/editing the same file.

When a task can be solved by configuration or a small local patch, do not introduce a framework or abstraction layer.

## 6. Verify in layers

Run checks in this order:

1. syntax/format check for touched files,
2. focused unit/component test for touched behavior,
3. focused type/lint check,
4. broader package/app test only if needed,
5. full suite only for cross-cutting/high-risk changes or before a release gate.

Do not repeatedly run the same expensive full suite after tiny edits. If a broad test fails for an unrelated pre-existing reason, record it and continue with focused verification.

See `references/test-policy.md`.

## 7. Control context growth

At natural checkpoints, compress working state into a short handoff note:

- goal,
- decisions,
- files changed,
- tests run/results,
- remaining issue.

Use the checkpoint instead of restating the entire conversation or repository history.

For long tasks, create/update a small local scratch note only if it prevents repeated exploration. Remove it before finalizing unless the project wants it committed.

## 8. Avoid expensive anti-patterns

Never do these by default:

- scan the entire repository when a targeted search can locate the feature,
- open large lockfiles, minified bundles, generated output, or vendor trees without need,
- run full test suites before identifying the change surface,
- use high/xhigh/max/ultra reasoning for routine edits,
- use multiple subagents for a task one agent can do cheaply,
- ask Codex to rewrite whole files when a patch is sufficient,
- repeatedly summarize information already present in the current context,
- refactor adjacent code “while here” without user value,
- browse the web when repository/local docs are enough,
- perform duplicate searches with equivalent queries.

See `references/anti-patterns.md`.

## 9. Escalate deliberately

Escalate model/reasoning/tool breadth only when at least one trigger is present:

- two focused attempts fail for reasons not explained by local evidence,
- architecture is ambiguous and wrong choice would cause broad rework,
- failure spans multiple subsystems,
- security/data-loss/migration risk is meaningful,
- acceptance criteria conflict,
- targeted verification exposes hidden coupling.

Before escalation, summarize what is known so the stronger model does not need to rediscover it.

## 10. Plus vs Pro behavior

Do not hardcode plan quotas into decisions. Use the same efficiency policy for both plans, with different default aggressiveness:

- **Plus:** default to `economy` behavior — Luna/Terra first, focused checks, strict scope control.
- **Pro:** default to `balanced` behavior — Terra first, Sol when complexity justifies it; still avoid waste because Pro allowance is finite and may be shared with other agentic features.

If the user says quota is nearly exhausted, enter **emergency mode**:

- no broad exploration,
- no optional refactors,
- no subagents,
- cheapest adequate model,
- one implementation path,
- focused verification only,
- produce a concise continuation note if completion is impossible in the current turn.

## 11. User-facing output

When useful, end with a compact **Usage choices** note containing only actionable items such as:

- “This is an S task; Luna/low is sufficient.”
- “Use Terra/medium for implementation; reserve Sol for the migration edge case.”
- “Run the focused test now; defer the full suite until final review.”

Do not clutter every answer with quota commentary if the skill is operating successfully in the background.

## 12. Optional local observability

The `cqo` CLI is optional. It provides task-level classification, soft budgets, a local journal, and a local audit:

- `cqo start <task>`
- `cqo status`
- `cqo audit`
- `cqo history`

The journal is local-only under `~/.cqo` (or `CQO_HOME`). It does not inspect private account pages or estimate hidden quota.

**Never run `cqo` automatically just to collect analytics.** The CLI is an inspection layer, not a runtime dependency. If the user did not opt into a CQO session, normal Skill behavior continues with zero CLI overhead.

## 13. Optional helper scripts

- `scripts/repo_snapshot.py --compact` — compact project map without reading the whole repo.
- `scripts/change_scope.py` — summarize current Git change surface and suggest verification scope.
- `scripts/cqo.py` — optional zero-network local CLI for task-level budgeting and auditing.

Use scripts only when they save model context/tool calls or the user explicitly wants observability; do not run them ritualistically.
