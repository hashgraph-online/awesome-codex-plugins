# Harness Patterns Reference

This reference keeps shared vocabulary out of individual skills. Use it when a skill needs neutral names for common harness concepts without copying product-specific workflow. Roles describe what a harness surface does; artifact names are defaults, not requirements.

## Core Layers

- Entrypoint: the first surface an agent reads, often `AGENTS.md` or an equivalent mirror.
- Source of truth: the versioned document or script that owns a decision.
- Contract: a rule that can be checked by script or review, usually with diff and audit modes.
- Validation surface: the commands that prove a change is safe enough for review.
- Runtime evidence: artifacts that connect observed behavior to logs, traces, external dependencies, or other runtime signals.
- Work-state surface: the current tasks, statuses, acceptance criteria, and task-to-change traceability.
- Ledger: a durable delivery-evidence record of agent intent, changes, validation, risks, and linked tasks or commits.
- Quality garden: a small set of generated metrics and baselines used to freeze new degradation and reduce old debt.

## Role Mapping

Before recommending new files, map existing repository surfaces to harness roles:

- `entrypoint`: agent-facing first-read instructions.
- `work-state`: authoritative task state and acceptance criteria.
- `ledger`: durable delivery or review evidence.
- `validation`: command surface and CI gates.
- `runtime-evidence`: run artifacts, reports, traces, or equivalent observed-behavior proof.
- `quality`: generated metrics, thresholds, and baseline movement.

If a repository already has an equivalent artifact, use that artifact and record it in `Detected Mapping`. Only create the default artifact when the role is absent.

## Recommended Defaults

These names are lightweight repo-local defaults, not required forms. If a project already has a reliable Jira, Linear, GitHub Issues, internal board, review template, test runner, generated report, or equivalent system, map that system to the relevant role.

- `AGENTS.md` for agent entrypoint rules.
- `docs/design/` for longer design decisions.
- `docs/exec-plans/` for multi-step implementation plans.
- `tasks.md` or `docs/tasks.md` for current work state, acceptance criteria, and task-to-change traceability when no reliable external tracker exists.
- `artifacts/runs/<run_id>/` for runtime evidence bundles.
- `agent_chats/` or `agents_chat/` for delivery ledgers that summarize evidence; they may reference tasks and commits but do not replace task state.
- `scripts/check_*` or `scripts/doctor*` for local repository checks.

## Repository Profiles

Use `references/harness-profiles.json` to choose the minimum useful role set for a repository archetype. A small library or docs-only repository should not inherit runtime-evidence or heavy quality governance by default. A service or high-audit repository may need stronger runtime evidence or ledger roles.

Use its `skillRouting` map to load the owner of a required role. Several roles may intentionally share one skill; do not recreate one skill per artifact or keyword.

Use `templates/` only after mapping existing equivalents. Templates are starting points for missing roles, not a prescribed repository shape.

## Standalone Skill Rule

Keep guidance as a standalone skill only when it adds a stable schema, executable or mechanically checkable procedure, repository or organization context, a high-risk guardrail, or measured improvement in `docs/model-evaluation.md`. Put generic model knowledge and routine execution rules in shared references, templates, or the target repository entrypoint.

## Task And Commit Coupling

- When a change completes, changes, or invalidates a tracked task, stage the task-state update in the same logical commit as that change.
- This does not mean every commit needs a task entry; use the repository's task policy for small maintenance work.
- If an external tracker is authoritative, update that tracker and reference the task ID from the commit or review record; mirror to `tasks.md` only when the repository explicitly wants a repo-local surface.

## Pattern Shape Matrix

These shapes are distilled from private authoring inputs. Do not name or copy source repositories in committed skill guidance.

| Shape | Useful signals | Bootstrap bias |
| --- | --- | --- |
| Comprehensive harness | root entrypoint, architecture docs, validation scripts, runtime artifacts, ledgers, quality reports, CI gates | Add only the missing layer; avoid re-scaffolding the whole repo. |
| Incremental harness | docs split by decisions, runbooks, quality, generated reports, validation pipelines, baselines | Normalize indexes and commands before adding new layers. |
| Thin bootstrap | root entrypoint, task board, basic docs, partial scripts or helper commands | Create the smallest discoverable artifact and link it from the entrypoint. |
| Delivery-ledger app | collaboration ledger, release/package notes, commit hooks, task state, user-facing documentation | Couple task-state updates with the related commit before introducing heavier governance. |

## Source Material Policy

- Source repositories may be inspected privately during authoring.
- Committed references must express only reusable roles, artifacts, checks, and failure modes.
- Do not include source project names, copied workflows, concrete URLs, accounts, hosts, or local paths.

## Missing-File Construction Rule

If a skill asks an agent to search for a harness surface and that surface is absent, the agent must not stop at "missing." It must propose or create the minimum artifact described by the skill-local `references/build-when-missing.md`.

## Design Bias

- Start with the smallest useful slice.
- Freeze new drift before paying down historical debt.
- Prefer a clear script over a platform until the script stops being enough.
- Prefer a shared reference over another skill when multiple capabilities use the same mechanism.
- Keep private URLs, credentials, account names, and environment assumptions out of reusable skills.
