---
name: workflow-start
description: Primary entry point for the spec-superflow state-machine workflow. Invoke when the user is inside an active spec-superflow change directory (look for .spec-superflow.yaml, changes/<name>/, proposal.md, specs/, design.md, tasks.md, or execution-contract.md) and asks to start, continue, resume, implement, plan, or figure out the next workflow step. Also invoke when the user explicitly asks to start a new spec-superflow change or route through the spec-superflow workflow. Do not invoke for unrelated coding tasks that happen to use words like start, continue, implement, or plan.
---

# Workflow Start

Primary entry point for `spec-superflow`. Jobs: inspect change context, check for updates, confirm DP-0, determine state, route to correct skill, block invalid transitions.

## Use This Skill When

Only invoke when spec-superflow context is present: `.spec-superflow.yaml` exists, artifacts like `proposal.md`/`specs/`/`design.md`/`tasks.md`/`execution-contract.md` are present, or user explicitly invokes spec-superflow by name. When in doubt, check for `.spec-superflow.yaml` first.

Do NOT invoke for: general coding tasks outside spec-superflow changes, casual questions, unrelated work.

## States

`exploring` → `specifying` → `bridging` → `approved-for-build` → `executing` → `closing`, with `debugging` side-path from `executing`, and `abandoned` as terminal. Read `docs/state-machine.md` if transition is ambiguous.

## Initialization

1. **Update check**: Run `node "${CLAUDE_PLUGIN_ROOT}/scripts/check-update.mjs"`. Exit 0 → continue. Exit 1 → non-blocking upgrade reminder. Exit 2 → skip.
2. **Inspect change folder**: Check for `proposal.md`, `specs/`, `design.md`, `tasks.md`, `execution-contract.md`. Answer: Is the change fuzzy? Artifacts missing/unstable? Contract exist? User approved contract? Execution in progress or blocked? In verification/wrap-up?

## DP-0: User Confirmation Gate

Run DP-0 when: change folder doesn't exist, planning artifacts missing/empty, or `dp_0_confirmed` ≠ `true`. Skip if `dp_0_confirmed` is `true`.

Ask: change name + one-sentence intent, known constraints, related optimizations (include or stay focused?), communication preference (ask per decision or draft for review).

After confirmation:
```bash
node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" state set <change-dir> dp_0_decisions "<summary>"
node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" state set <change-dir> dp_0_result confirmed
node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" state set <change-dir> dp_0_confirmed true
node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" state set <change-dir> dp_0_timestamp $(date -u +%Y-%m-%dT%H:%M:%SZ)
```

Config-aware routing: check `artifacts.order` and `artifacts.skip` from project config.

## Mode Detection

If workflow is `auto`/`null`/unset: run `node "${CLAUDE_PLUGIN_ROOT}/scripts/infer-workflow.mjs" <change-dir>`. Inference: **hotfix** (≤2 tasks, ≤2 files, no schema/API/new modules), **tweak** (≤4 tasks, config/doc only), **full** (anything larger). Persist with `node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" state set <dir> workflow <mode>`.

Validate mode against artifact content. If hotfix/tweak criteria not met → upgrade to `full` and output reason. Don't overwrite explicit mode unless user asks.

## Routing Rules

### Route to need-explorer
Change is fuzzy, scope unclear, comparing options, no stable change name.

### Route to spec-writer
Guard: `node "${CLAUDE_PLUGIN_ROOT}/scripts/guard/guard.mjs" check <dir> exploring specifying --json` → fail = BLOCK. User knows what they want, artifacts missing/incomplete.

### Route to contract-builder
Guard: `... check <dir> specifying bridging --json` → fail = BLOCK. Artifacts exist, implementation requested, contract missing/stale. Include `DP-3: 契约批准`.

### Route to build-executor
Guard: `... check <dir> approved-for-build executing --json` → fail = BLOCK. Contract exists and approved, contract matches artifacts. Include `DP-4: 执行模式选择`.

### Route to bug-investigator
Execution hit blockage: test failure, unexpected behavior, build error, task cannot proceed. After debugging, route back to build-executor.

### Route to code-reviewer
Batch completed, batch ready for spec-compliance + code-quality verification.

### Route to release-archivist
Guard: `... check <dir> executing closing --json` → fail = BLOCK. Implementation complete, verification complete/nearly complete. Include `DP-7: 归档确认`.

### Route to spec-merger
Delta specs exist that need merging, change closing with ADDED/MODIFIED/REMOVED/RENAMED specs.

### Route to abandoned
User explicitly requests, bug-investigator escalates after 3+ failures AND user chooses, scope change makes change no longer worthwhile AND user confirms. Block from `closing` or `abandoned`.

### Fast-Path Routing
- **Hotfix**: Route to contract-builder (minimal), skip need-explorer + spec-writer, guard check `exploring bridging --workflow hotfix`, after DP-3 → build-executor (inline), after → release-archivist (lightweight)
- **Tweak**: Route to build-executor (direct edit), skip need-explorer + spec-writer + contract-builder, guard check `exploring approved-for-build --workflow tweak`, after → release-archivist (lightweight)

Post-transition: 💡 `node "${CLAUDE_PLUGIN_ROOT}/scripts/spec-superflow.mjs" inject <change-dir>` to update phase-guard artifacts.

## Staleness Detection

Use content inspection, not timestamps.

**Stale contract**: proposal scope expanded beyond contract scope fence, or contract references capabilities no longer in proposal → route back to `contract-builder`.

**Stale planning artifacts**: capability in proposal has no spec file, or spec exists for capability not in proposal → drift detected.

**Stale tasks**: requirement in specs has no corresponding task → stale tasks.

## Guardrails

- No implementation before planning artifacts or contract exist
- No "continue" without state inspection
- No implementation past stale contract
- No implementation past bug without investigation
- No closure without code review
- No closure with unsynced delta specs
- No transitions from `abandoned` (terminal)
- No transition to `abandoned` from `closing` or `abandoned`
- No auto-abandon without user confirmation
- No merging delta specs from abandoned change

## Output Standard

Always state: (1) current detected state, (2) why (cite file/content/condition), (3) which skill should run next. If blocking, explain missing artifact/approval.

Decision point references when routing:
- contract-builder → DP-3, build-executor → DP-4, bug-investigator (escalation) → DP-5, release-archivist (verification failure) → DP-6, release-archivist → DP-7

## Exception Handling

- **Parse failures**: Fall back to content-level detection if `.spec-superflow.yaml` is malformed
- **Missing files**: Route to the skill that generates the missing files
- **User interruption**: Re-inspect change directory content (not cached state) on resume
