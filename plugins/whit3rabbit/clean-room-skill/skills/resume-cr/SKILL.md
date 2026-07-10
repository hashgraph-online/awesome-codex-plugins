---
name: resume-cr
description: Continues an existing Clean Room run from durable artifacts without relying on prior chat history.
argument-hint: [existing task-manifest.json or artifact roots]
disable-model-invocation: true
---

# Clean Room Resume

Resume an existing clean-room run from durable artifacts. Never use prior chat history as the source of truth.

Use the canonical `clean-room` skill workflow and references in this plugin. Read `skills/clean-room/references/CONTROLLER-LOOP.md` when the manifest records `loop_context` or unattended mode. Preserve the same clean-room boundary, role separation, artifact schemas, leakage rules, implementation-root rules, and hook expectations.

If `task-manifest.json` records `controller_policy.mode: "unattended"` in Claude Code, prefer launching `clean-room-skill run --task-manifest <path> --agent-runtime claude` only when `loop_context` exists and names approved pending or gap units. For ccsilo/OpenRouter sessions, use `clean-room-skill run --task-manifest <path> --ccsilo [variant]` instead of manual `--agent-runtime claude`, `--agent-config-dir`, or `CLEAN_ROOM_CLAUDE_EXECUTABLE` wiring. Never write `ANTHROPIC_AUTH_TOKEN` or API keys into ccsilo or Claude settings files. If an unattended manifest lacks `loop_context`, treat it as incomplete outer-loop state: finish decomposition or selected-slice approval first, or stop with the missing outer-loop fields instead of launching the runner. If `clean-room-skill` is not on `PATH`, immediately use `npx clean-room-skill@latest run --task-manifest <path> --agent-runtime claude` instead of searching for the installed package. Do not search plugin cache paths for schema files, and do not pass `--schema-dir /dev/null`. The runner uses bundled schemas by default; pass `--schema-dir` only when the user provides a real schema directory. The main conversation must not perform Agent 1, Agent 2, Agent 3, or Agent 4 work once runner-ready unattended state exists. Do not edit `task-manifest.json` unit statuses in the main conversation; unit completion must come from runner-managed role artifacts and contaminated-side coverage verification. Do not ask to continue while unattended policy, iteration budget, and approved pending or gap units still permit progress. If the runner or Claude role-agent dispatch is unavailable, stop with `BLOCKERS: Claude role-agent dispatch unavailable` rather than silently continuing in the main chat.

## Discovery Before Load

Before saying no clean-room run exists, perform the canonical `clean-room` "Run State Discovery Before Wizard" rules. Resolve explicit artifact paths first, then inspect the current working directory and ancestors for `.clean-room/local-state.json`, then configured clean-room roots, then bounded `~/Documents/CleanRoom/task-*` and `~/Documents/CleanRoom/*/tasks/task-*` candidates. If the repo-local pointer identifies an external project, scan that project's `tasks/` directory before any global fallback.

Treat target-repository `.clean-room/tasks/` as noncanonical unless the user explicitly provided that path or `.clean-room/local-state.json` identifies it as the external task root. Active artifacts belong under the external task root, not under the target repo stub.

If a candidate `task-manifest.json` is present but invalid, legacy-shaped, or schema-incompatible, report the exact path and validation errors. Do not say no artifacts exist. If no runnable task remains but a valid project is found, report the project root and make the next safe action "create a new task in this project" when the user wants to add more work.

## Load Order

Load these artifacts from the paths recorded in `task-manifest.json` and the configured root environment. Treat missing optional artifacts as blockers only when the current gate requires them. A task may live at `<base>/<project>/tasks/<task-id>/` with a shared project-level implementation root; trust the absolute paths recorded in `task-manifest.json` `artifact_paths` and never re-derive the layout from folder positions.

- `task-manifest.json`
- `preflight-goal.json`, when referenced by `task-manifest.json`, only on the contaminated/controller side
- `init-config.json`, when present, only for drift comparison against `task-manifest.json` `initialization_snapshot`
- `clean-run-context.json`, when present, only on the clean side
- `source-index.json`, only when referenced by the task manifest and only on the contaminated side
- `visual-index.json`, only when referenced by the task manifest and only on the contaminated side
- `coverage-ledger.json`
- `evidence-ledger.json`
- `handoff-package.json` and behavior specs when present
- `skeleton-manifest.json` when present
- `implementation-plan.json` when present
- `implementation-report.json` when present
- latest valid `qc-report.json`
- `clean-room-result.json`, when present
- `controller-status.json`, when present, only on the contaminated/controller side
- open abstract delta tickets

If more than one `qc-report.json` is present, select the valid report with the newest `reviewed_at`. If reports tie, cannot be validated, or disagree about artifact hashes, stop and report a blocker.

## Required Checks

Before choosing work:

- Validate all loaded JSON artifacts against the bundled schemas.
- Validate handoff package paths and SHA-256 values before trusting clean artifacts.
- Confirm source roots, contaminated artifact roots, clean roots, implementation roots, and clean allowed-read roots remain separated.
- Confirm authorization still covers the recorded source scope and allowed actions.
- Report `run_state` when present; do not infer generation from chat history when it is missing.
- Trust `initialization_snapshot` before any reusable `init-config.json`. If they differ, report drift and stop before changing roots, model policy, schema profile, or rule classification.
- When `initialization_snapshot` records `project_id` or `project_root`, confirm the on-disk `clean-room-project.json` at the project root still agrees with them and with the shared implementation root. Report drift and stop on mismatch.
- Preserve the existing `controller_policy`; missing policy means `attended`.
- Stop if new-run artifacts lack `preflight_goal_ref`, `preflight_goal_sha256`, or the required `handoff_sequence`. Treat this as legacy or incomplete preflight state and ask for a reviewed preflight goal before resuming.
- Validate referenced `preflight-goal.json` before using goal, stack, dependency, license, exactness, output, or hygiene decisions.
- Preserve `loop_context` when present. In unattended inner-loop mode, selected work must remain inside `loop_context.approved_scope_refs`.
- Stop if clean roles appear to require source, screenshots, contaminated ledgers, contaminated chat history, raw diffs, source excerpts, `source-index.json`, `visual-index.json`, or the full `task-manifest.json`.
- Stop if Agent 3 appears to require writing code outside `CLEAN_ROOM_IMPLEMENTATION_ROOTS` or running shell outside the bounded Agent 3 shell policy.
- Stop if Agent 4 appears to require reading source/contaminated material, writing outside `CLEAN_ROOM_IMPLEMENTATION_ROOTS` and `CLEAN_ROOM_CLEAN_ROOTS`, or running shell outside the bounded Agent 4 polish runner policy.
- Stop if `clean-run-context.json` exposes source roots, visual roots, contaminated roots, source index refs, visual index refs, coverage ledgers, or evidence ledgers.
- Stop if Agent 0 appears to have steered Agent 2, Agent 3, or Agent 4 through direct chat, progress feedback, implementation hints, priority changes, or partial implementation reports instead of durable sanitized artifacts.
- Treat non-terminal Agent 3 `implementation-report.json` states as internal clean-side state, not Agent 0 feedback.
- Stop if Agent 1.5 appears to require source roots, visual roots, `source-index.json` contents, `visual-index.json` contents, raw screenshots, contaminated evidence ledgers, private identifier denylist contents, raw diffs, source excerpts, or Agent 1 source-reading chat history.
- If `context_management.mode` is `role-session-briefs`, verify the next role can be launched from a fresh context using `role-session-brief.json` and the recorded budgets. Do not use resume chat history as the brief.

## Selection Rules

Pick exactly one next safe action:

- One pending, gap, or blocked unit from `task-manifest.json` and `coverage-ledger.json`, limited to `loop_context.approved_scope_refs` when present.
- One blocked gate when a required artifact, schema validation, handoff hash, leakage review, authorization check, or root-separation check is missing or invalid.
- A final package closeout when implementation is complete, coverage is complete, QC passed, any configured polish review passed, and `clean-room-result.json` records a terminal inner-loop return when `loop_context` is present.

Do not batch units. Do not advance state from memory. Do not reinterpret the source scope.

Before launching another role, Agent 0 may refresh contaminated-side `controller-status.json` with the current gate, selected unit, coverage state, implementation/QC state, blockers, latest artifact refs, and next safe action. Then create a role-specific `role-session-brief.json`. Clean roles receive the brief and clean artifact refs only, never full resume state.

## Output

Return only this structure:

```text
STATE: attended/unattended, current unit, latest implementation and QC status.
NEXT: one safe action.
BLOCKERS: missing artifacts or invalid checks.
DO NOT: no source text crossing wall, no code writes outside implementation roots.
```

If no safe next action can be proven, set `NEXT` to `blocked` and explain the first blocking gate.
