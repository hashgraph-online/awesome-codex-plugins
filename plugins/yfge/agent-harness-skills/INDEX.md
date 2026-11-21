# Skill Index

## Recommended Composition

The suite has four core skills and one optional governance skill:

1. `repo-harness-assessment` - start here for an existing repo; map roles, reconcile agent entrypoints, and choose the smallest useful next slice.
2. `repo-contracts-and-boundaries` - encode architecture boundaries, structural quality, baselines, and drift prevention.
3. `validation-harness-design` - define command surfaces, report formats, and CI gates.
4. `runtime-evidence-and-tracing` - connect runtime behavior and failures to evidence artifacts.
5. `work-state-and-delivery` - optionally govern design intent, tracked work, delivery evidence, and commit coupling when the repository needs those roles.

Do not load all five by default. Repository profiles in `references/harness-profiles.json` define the minimum roles for each archetype and map those roles to skill owners.

## Trigger Strength

- Hard trigger: load the matching skill before creating or refactoring repository harness entrypoints, contracts, validation surfaces, runtime-evidence systems, or governance policies.
- Soft route: use this index first for assessment, discussion, or deciding which skill applies; load only the relevant skill when the task turns into substantive harness work.
- No trigger: do not load a skill solely because a filename or keyword appears in a read-only question, status/diff inspection, casual comparison, or ordinary commit that already follows repository rules.

## Routing Notes

- Use `repo-harness-assessment` when the user asks what a repo is missing.
- Use `repo-harness-assessment` for `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, Cursor rules, GitHub instructions, source-of-truth navigation, mirrors, or entrypoint drift.
- Use `references/harness-profiles.json` to choose the lightest appropriate role set for the repository archetype.
- Include `Detected Mapping` in skill outputs so existing issue trackers, review templates, validation commands, reports, or artifact systems can stand in for default file names.
- Use `repo-contracts-and-boundaries` when the user asks to protect architecture, layering, dependency direction, ownership, schemas, baselines, allowlists, structural metrics, quality reports, or cleanup thresholds.
- Use `validation-harness-design` when the user asks for validation commands, doctor scripts, test matrices, CI gates, smoke checks, JSON, or JUnit outputs.
- Use `runtime-evidence-and-tracing` when the user asks to connect, diagnose, or design runtime evidence with request IDs, run IDs, logs, traces, screenshots, external dependency evidence, or artifacts.
- Use `work-state-and-delivery` when the user asks where requirements or tasks belong, or wants to design task, ledger, review, handoff, acceptance, delivery-artifact, or commit-coupling policy.
- For ordinary commits, follow the target repository's `AGENTS.md` or contributor rules directly; use `work-state-and-delivery` only when the policy itself is missing, conflicting, or being redesigned.

## Skill Value Rule

Keep a capability as a standalone skill only when it contributes at least one of these:

- a stable schema or output contract;
- an executable or mechanically checkable procedure;
- repository or organization context a general model cannot infer;
- a high-risk guardrail or evidence requirement;
- measured improvement in the model evaluation matrix.

Otherwise, place the guidance in a shared reference, template, or repository entrypoint instead of adding another skill.

## Version 0.1 Migration

- `agent-entrypoint-design` is now part of `repo-harness-assessment`.
- `quality-gardening` is now part of `repo-contracts-and-boundaries`.
- `design-doc-and-task-board`, `agent-ledger-and-delivery`, and repository-policy parts of `atomic-commit-discipline` are now `work-state-and-delivery`.
- Ordinary commit execution no longer has a standalone skill; follow the target repository entrypoint and contributor rules.
