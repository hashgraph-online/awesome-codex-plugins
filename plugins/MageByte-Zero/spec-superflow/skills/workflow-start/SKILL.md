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

`exploring` → `specifying` → `bridging` → `approved-for-build` → `executing` → `closing`, with `debugging` side-path from `executing`, and `abandoned` as terminal. If a transition is ambiguous, run `npx --yes --package spec-superflow@0.10.0 ssf runtime asset read docs/state-machine.md`.

## Terminal-State Short Circuit

Before update checks or recovery overlays, inspect the persisted state. If it is
`closing`, stop immediately: `closing` is a successful terminal state and the
next skill is `none`. Report the terminal state and its persisted evidence.
Do not run `handoff list`, `checkpoint list`, the execution-control recovery
scan, or `release-archivist`; do not resume, hand off, or route any more work.

## Initialization

1. **Update check**: Run `npx --yes --package spec-superflow@0.10.0 ssf runtime check-update`. Exit 0 → continue. Exit 1 → non-blocking upgrade reminder. Exit 2 → skip.
2. **Inspect change folder**: Check for `proposal.md`, `specs/`, `design.md`, `tasks.md`, `execution-contract.md`. Answer: Is the change fuzzy? Artifacts missing/unstable? Contract exist? User approved contract? Execution in progress or blocked? In verification/wrap-up?

## Overlay Recovery Scan

3. **Overlay recovery scan**: Run `npx --yes --package spec-superflow@0.10.0 ssf handoff list <change-dir> --json` and `npx --yes --package spec-superflow@0.10.0 ssf checkpoint list <change-dir> --json`. A `result-ready` handoff requires explicit review and `npx --yes --package spec-superflow@0.10.0 ssf handoff resolve` before resuming the affected work. An `active` handoff is non-blocking side work. Show a non-stale checkpoint as recovery context; show a stale checkpoint only as historical evidence.

## Execution-Control Recovery Scan

4. **Execution-control recovery scan**: For `approved-for-build`, `executing`, or `debugging`, run `npx --yes --package spec-superflow@0.10.0 ssf execution show <change-dir> --json`. Treat only `current: true` plus `waves[].eligible: true` as permission to start a wave; report plan revision, mode, next eligible wave, and every wave's receipt/blockers. A missing, invalid, or stale plan blocks implementation and routes to `build-executor`; do not infer progress from chat history.

## DP-0: User Confirmation Gate

Run DP-0 when: change folder doesn't exist, planning artifacts missing/empty, or `dp_0_confirmed` ≠ `true`. Skip if `dp_0_confirmed` is `true`.

Ask: change name + one-sentence intent, known constraints, related optimizations (include or stay focused?), communication preference (ask per decision or draft for review).

After confirmation:
```bash
npx --yes --package spec-superflow@0.10.0 ssf state set <change-dir> dp_0_decisions "<summary>"
npx --yes --package spec-superflow@0.10.0 ssf state set <change-dir> dp_0_result confirmed
npx --yes --package spec-superflow@0.10.0 ssf state set <change-dir> dp_0_confirmed true
npx --yes --package spec-superflow@0.10.0 ssf state set <change-dir> dp_0_timestamp $(date -u +%Y-%m-%dT%H:%M:%SZ)
```

Config-aware routing: check `artifacts.order` and `artifacts.skip` from project config.

## Mode Detection

If workflow is `auto`/`null`/unset: run `npx --yes --package spec-superflow@0.10.0 ssf runtime infer <change-dir>`. Inference: **hotfix** (≤2 tasks, ≤2 files, no schema/API/new modules), **tweak** (≤4 tasks, config/doc only), **full** (anything larger). Persist with `npx --yes --package spec-superflow@0.10.0 ssf state set <dir> workflow <mode>`.

Validate mode against artifact content. If hotfix/tweak criteria not met → upgrade to `full` and output reason. Don't overwrite explicit mode unless user asks.

## Routing Rules

### Route to need-explorer
Change is fuzzy, scope unclear, comparing options, no stable change name.

### Route to spec-writer
Guard: `npx --yes --package spec-superflow@0.10.0 ssf runtime guard check <dir> exploring specifying --json` → fail = BLOCK. User knows what they want, artifacts missing/incomplete.

### Route to contract-builder
Guard: `... check <dir> specifying bridging --json` → fail = BLOCK. Artifacts exist, implementation requested, contract missing/stale. Include `DP-3: 契约批准`.

### Route to build-executor
Contract exists and approved, contract matches artifacts. Include `DP-4: 执行模式选择`: propose waves, run `npx --yes --package spec-superflow@0.10.0 ssf execution recommend <change-dir> [--wave ...]`, show the user every available mode plus evidence and the recommendation, then obtain a clear selection. The command saves a current receipt; before the first implementation edit, `build-executor` must run `npx --yes --package spec-superflow@0.10.0 ssf execution plan <change-dir> --mode <selected> --confirm ...` (and `--acknowledge-recommendation` when the selected mode differs from the recommendation) using matching artifacts, contract, and waves, then `npx --yes --package spec-superflow@0.10.0 ssf execution show <change-dir> --json`; report the saved revision, selected mode, recommendation alignment, ordered waves, and actual concurrent-dispatch capability. A revision must repeat recommend and confirmation. Do not transition to `executing` until `show` reports `current: true`; then run `... check <dir> approved-for-build executing --json` → fail = BLOCK.

### Route to bug-investigator
Execution hit blockage: test failure, unexpected behavior, build error, task cannot proceed. After debugging, route back to build-executor.

### Route to code-reviewer
The current planned wave is implemented and ready for spec-compliance + code-quality verification. A reviewer must write an `npx --yes --package spec-superflow@0.10.0 ssf execution review <change-dir> --wave <id> --base <sha> --head <sha> --report <path> --verdict <pass|fail>` receipt before any dependent wave or closing transition.

### Route to release-archivist
Only while the current state is `executing`: implementation is complete and verification is ready. Run the guard `... check <dir> executing closing --json` → fail = BLOCK. `release-archivist` completes verification, audit, and any required delta merge before the final transition. Include `DP-7: 归档确认`.

### Route to spec-merger
Only while the current state is `executing`, before the final `executing → closing` transition: delta specs need merging with ADDED/MODIFIED/REMOVED/RENAMED specs. Never route a change already in `closing` to `spec-merger`.

### Route to abandoned
User explicitly requests, bug-investigator escalates after 3+ failures AND user chooses, scope change makes change no longer worthwhile AND user confirms. Block from `closing` or `abandoned`.

### Optional Prototype Handoff

When the user's brief explicitly contains UI, screen, interaction, layout, UX,
or product-experience uncertainty, ask once whether a prototype would reduce
uncertainty. Do not create a prototype handoff or enter a prototype worktree
until the user confirms. After confirmation:

```bash
npx --yes --package spec-superflow@0.10.0 ssf handoff create <change-dir> \
  --type prototype --objective "<confirmed objective>" \
  --expected-output "<expected evidence>" --acceptance "<completion criterion>"
npx --yes --package spec-superflow@0.10.0 ssf isolate <change-dir> prototype-<handoff-id>
```

Never suggest or enter this route automatically for backend, CLI, configuration,
or internal-refactor work. Never pass `--force` to `ssf isolate` for prototype
work.

### Fast-Path Routing
- **Hotfix**: Route to contract-builder (minimal), skip need-explorer + spec-writer, guard check `exploring bridging --workflow hotfix`, then `bridging -> approved-for-build`, after DP-3 → build-executor (recommend, show, and confirm an execution mode), after → release-archivist (lightweight). Hotfix may skip `proposal.md`, `design.md`, `tasks.md`, and `specs/`, but it still requires a fresh minimal `execution-contract.md`, DP-3 approval, and a current execution plan before build
- **Tweak**: Route to build-executor (direct edit), skip need-explorer + spec-writer + contract-builder, guard check `exploring approved-for-build --workflow tweak`, after → release-archivist (lightweight)

Post-transition: 💡 `npx --yes --package spec-superflow@0.10.0 ssf inject <change-dir>` to update phase-guard artifacts.

## Staleness Detection

Use content inspection, not timestamps.

**Stale contract**: proposal scope expanded beyond contract scope fence, or contract references capabilities no longer in proposal → route back to `contract-builder`.

**Stale planning artifacts**: capability in proposal has no spec file, or spec exists for capability not in proposal → drift detected.

**Stale tasks**: requirement in specs has no corresponding task → stale tasks.

## Guardrails

- No implementation before planning artifacts or contract exist
- No implementation for full/hotfix without a current `npx --yes --package spec-superflow@0.10.0 ssf execution plan`; no state transition based on an unverified DP-4 string
- No "continue" without state inspection
- No implementation past stale contract
- No implementation past bug without investigation
- No closure without all planned wave review receipts recorded as `pass`
- No closure with unsynced delta specs
- `closing` is a successful terminal state: next skill is none and recovery overlays do not run
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
