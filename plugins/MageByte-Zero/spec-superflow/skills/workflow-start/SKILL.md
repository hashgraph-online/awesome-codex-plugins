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

`exploring` → `specifying` → `bridging` → `approved-for-build` → `executing` → `closing`, with `debugging` side-path from `executing`, and `abandoned` as terminal. If a transition is ambiguous, run `ssf runtime asset read docs/state-machine.md`.

## Terminal-State Short Circuit

Before update checks or recovery overlays, inspect the persisted state. If it is
`closing`, stop immediately: `closing` is a successful terminal state and the
next skill is `none`. Report the terminal state and its persisted evidence.
Do not run `handoff list`, `checkpoint list`, the execution-control recovery
scan, or `release-archivist`; do not resume, hand off, or route any more work.

## Initialization

1. **Update check**: Run `ssf runtime check-update`. Exit 0 → continue. Exit 1 → non-blocking upgrade reminder. Exit 2 → skip.
2. **Inspect change folder**: Check for `proposal.md`, `specs/`, `design.md`, `tasks.md`, `execution-contract.md`. Answer: Is the change fuzzy? Artifacts missing/unstable? Contract exist? User approved contract? Execution in progress or blocked? In verification/wrap-up?

## Overlay Recovery Scan

3. **Overlay recovery scan**: Run `ssf handoff list <change-dir> --json` and `ssf checkpoint list <change-dir> --json`. A `result-ready` handoff requires explicit review and `ssf handoff resolve` before resuming the affected work. An `active` handoff is non-blocking side work. Show a non-stale checkpoint as recovery context; show a stale checkpoint only as historical evidence.

## Execution-Control Recovery Scan

4. **Execution-control recovery scan**: For Full or legacy Hotfix in `approved-for-build`, `executing`, or `debugging`, run `ssf execution show <change-dir> --json`. Treat only `current: true` plus `waves[].eligible: true` as permission to start a wave. Do not require this scan for Quick, Tweak, or a valid direct Hotfix receipt.

## Direct Short-Path Intake

For a clearly bounded Quick or incident Hotfix request, recommend and accept in the same turn. Do not collect the eight intake facts as a questionnaire: infer them from the request and repository, show the observed facts, recommendation, and qualification reason, then ask the user to choose `tdd`, `new-test`, or `bounded` verification before running:

```bash
ssf state init <change-dir>
ssf workflow recommend <change-dir> --task-count <n> --file-count <n> --config-doc-only no --schema-api-change no --new-module no --behavioral-constraint-change <yes|no> --cross-module-change <yes|no> --uncertainty low --request-kind <standard|incident>
ssf workflow accept <change-dir> --source direct-request --verification <tdd|new-test|bounded>
```

Quick is ≤3 tasks/files of low-risk code. Hotfix is an incident with a reproducible symptom and ≤2 tasks/files. Display `Observed`, `Recommended`, `Why`, and any risk reasons; acceptance is the user's direct request to proceed and their explicit verification choice. Do not create planning artifacts, a contract, an execution plan, wave receipts, or DP approvals. Transition through the receipt-aware guard, execute bounded work, and require `test_result: pass` before closing. A fourth code file, behavioral-constraint change (PRD/spec/design/API/data/permission), cross-module work, a new module, high uncertainty, or failed verification does not auto-escalate: show Quick and Full, then wait for the user's choice. A user selecting Quick must acknowledge the recommendation and choose `tdd`, `new-test`, or `bounded` verification in the receipt. Tweak is only ≤4 config/doc-only tasks/files with no risk signals; it cannot be selected as an override. A legacy Hotfix without a valid direct receipt remains on the Full contract/DP-3/plan/review path.

## DP-0: User Confirmation Gate

After Direct Short-Path Intake does not apply, run DP-0 when: change folder doesn't exist, planning artifacts are
missing/empty, `dp_0_confirmed` is not `true`, or a legacy change still has an
`auto`/empty workflow. Resolve the artifact language first, then complete the
workflow path intake. Do not set `dp_0_confirmed=true` while path facts or the
user's path choice are still missing.

### Artifact Language Resolution

Before the first planning artifact is generated, resolve one concrete artifact
language in this priority order:

1. explicit user language
2. the conversation's primary language
3. an explicit non-`auto` `execution.defaultLanguage`
4. the primary language of existing planning artifacts in the current change
5. the primary language of the project templates

Treat `execution.defaultLanguage: auto` as a request to continue resolving, not
as a language. Append `artifact_language=<concrete-language>` to
`dp_0_decisions`, preserving its existing scope and constraint summary. Never
persist `auto` as the resolved artifact language. If DP-0 was already confirmed
but this field is absent, resolve and append it before routing to `spec-writer`.
All later planning skills reuse this field so one change does not switch
languages without an explicit user request.

### Workflow Path Intake (Mode Detection, Full/Legacy)

Workflow path selection is a DP-0 intake decision. It selects the planning path
(`full`, `hotfix`, `tweak`, or `quick`); it is separate from DP-4, which later selects
the execution mode (`Inline`, `Batch Inline`, or `SDD`). It does not add a
state or cause a phase transition.

1. Obtain the change name and one-sentence intent before any state-dependent
   command. Validate the change name as one non-empty relative path segment
   (not `.` or `..`, with no `/` or `\\`), resolve the change dir as `<project-root>/changes/<change-name>`, and reject any normalized path that
   escapes the project's `changes/` directory.
2. If the state file is absent or `dp_0_confirmed` is `false`/null, run `ssf state init <change-dir>` before `show`; initialization must leave DP-0 unconfirmed.
3. Read `state.workflow`. An explicit `full` workflow wins and skips automatic
   recommendation. For an explicit `hotfix`/`tweak`/`quick`, report the active
   path; if scope, risk, or verification now exceeds its boundary, refresh the
   recommendation with observed facts and route it to Full instead of continuing.
4. For `auto`/`null`/unset, run `ssf workflow show <change-dir> --json` before collecting or changing any facts. A missing receipt is represented as `needs-input` with all eight fixed facts in `missing_facts`.
5. If the response is `needs-input`, ask only for `missing_facts`; do not ask
   for any fact not listed by the receipt. Do not invent facts from missing
   artifacts and do not default the path to `full`.
6. Run `ssf workflow recommend <change-dir> ...` once with one complete fact snapshot.
7. Show the user `Observed`, `Available`, `Recommended`, and `Why`. A
   recommendation is advice only: never persist it as the workflow selection.
8. A recommended low-risk Quick or incident Hotfix is accepted only with
   `ssf workflow accept <change-dir> --source direct-request --verification <tdd|new-test|bounded>`.
   For Full, legacy Hotfix, or Tweak, obtain the user's explicit choice and run
   `ssf workflow select <change-dir> --mode <full|hotfix|tweak> --confirm --reason "<user choice>"`. For a risk-signalled Quick choice, run `workflow select --mode quick --confirm --acknowledge-recommendation --verification <tdd|new-test|bounded>`.
9. Add `--acknowledge-recommendation` only after the user chooses a
   non-recommended selectable path. Report the persisted receipt and DP-0 audit summary.
10. To escalate a selected Quick, direct Hotfix, or Tweak, refresh
   `workflow recommend` with observed risk facts, then select `full` with
   `--confirm` (and `--acknowledge-recommendation` only if required). Do not
   overwrite an explicit mode without this persisted recommendation.
11. Keep `ssf runtime infer <change-dir>` only for legacy artifact inference and validation compatibility; it cannot replace user selection at intake.

### Confirm DP-0

Only after an explicit workflow path is available, ask for the remaining DP-0
decisions: change name and one-sentence intent, known constraints, related
optimizations (include or stay focused?), and communication preference (ask per
decision or draft for review). Confirm one combined summary containing those
decisions, the resolved `artifact_language`, and the persisted workflow path
plus recommendation-alignment summary. Preserve existing scope, constraints,
and language entries; never replace them with the path summary alone.

After that combined confirmation:
```bash
ssf state set <change-dir> dp_0_decisions "<combined summary preserving scope, artifact_language, and workflow_path>"
ssf state set <change-dir> dp_0_result confirmed
ssf state set <change-dir> dp_0_confirmed true
ssf state set <change-dir> dp_0_timestamp $(date -u +%Y-%m-%dT%H:%M:%SZ)
```

Config-aware routing: check `artifacts.order`, `artifacts.skip`, and
`execution.defaultLanguage` from project config.

## Routing Rules

### Route to need-explorer
Change is fuzzy, scope unclear, comparing options, no stable change name.

### Route to spec-writer (Full only)
Guard: `ssf runtime guard check <dir> exploring specifying --json` → fail = BLOCK. User knows what they want, artifacts missing/incomplete.

### Route to contract-builder
Only for Full or legacy Hotfix. Guard: `... check <dir> specifying bridging --json` → fail = BLOCK. Artifacts exist, implementation requested, contract missing/stale. Include `DP-3: 契约批准`.

### Route to build-executor
For Full or legacy Hotfix: contract exists and approved, contract matches artifacts. Include `DP-4: 执行模式选择`: propose waves, run `ssf execution recommend <change-dir> [--wave ...]`, then run `ssf execution plan <change-dir> --mode <selected> --confirm ...` and `execution show`. For Quick, Tweak, or direct Hotfix: use the receipt-aware guard and bounded verification; do not require DP-4, a contract, plan, or review receipt.

### Route to bug-investigator
Execution hit blockage: test failure, unexpected behavior, build error, task cannot proceed. After debugging, route back to build-executor.

### Route to code-reviewer (Full/legacy Hotfix only)
The current planned wave is implemented and ready for spec-compliance + code-quality verification. A reviewer must write an `ssf execution review <change-dir> --wave <id> --base <sha> --head <sha> --report <path> --verdict <pass|fail>` receipt before any dependent wave or closing transition. Quick, Tweak, and direct Hotfix use their verification summary instead.

### Route to release-archivist
Only while the current state is `executing`: implementation is complete and verification is ready. For Full/legacy Hotfix, run the guard and complete verification, audit, delta merge, and DP-7. For Quick, Tweak, and direct Hotfix, run the receipt-aware guard, persist `test_result: pass`, and produce the verification summary without audit or DP-7.

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
ssf handoff create <change-dir> \
  --type prototype --objective "<confirmed objective>" \
  --expected-output "<expected evidence>" --acceptance "<completion criterion>"
ssf isolate <change-dir> prototype-<handoff-id>
```

Never suggest or enter this route automatically for backend, CLI, configuration,
or internal-refactor work. Never pass `--force` to `ssf isolate` for prototype
work.

### Fast-Path Routing
- **Legacy Hotfix**: Route to contract-builder (minimal), skip need-explorer + spec-writer, guard check `exploring bridging --workflow hotfix`, then `bridging -> approved-for-build`, after DP-3 → build-executor (recommend, show, and confirm an execution mode), after → release-archivist (lightweight). It may skip planning artifacts but still requires a minimal contract, DP-3, and a current execution plan. A direct Hotfix instead follows Direct Short-Path Intake.
- **Tweak**: Route to build-executor (direct edit), skip need-explorer + spec-writer + contract-builder, guard check `exploring approved-for-build --workflow tweak`, after → release-archivist (lightweight)

Post-transition: 💡 `ssf inject <change-dir>` to update phase-guard artifacts.

## Staleness Detection

Use content inspection, not timestamps.

**Stale contract**: proposal scope expanded beyond contract scope fence, or contract references capabilities no longer in proposal → route back to `contract-builder`.

**Stale planning artifacts**: capability in proposal has no spec file, or spec exists for capability not in proposal → drift detected.

**Stale tasks**: requirement in specs has no corresponding task → stale tasks.

## Guardrails

- Full/legacy Hotfix: no implementation before planning artifacts or contract exist
- No implementation for Full or legacy Hotfix without a current `ssf execution plan`; no state transition based on an unverified DP-4 string
- No "continue" without state inspection
- Full/legacy Hotfix: no implementation past stale contract
- No implementation past bug without investigation
- Full/legacy Hotfix: no closure without all planned wave review receipts recorded as `pass` or with unsynced delta specs
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

## Standard User-Facing Handoff

End every user-facing phase report with this concise handoff. Only a successfully
persisted `closing` state and `abandoned` are terminal.

### Normal report

- Current stage: `<detected workflow stage>`.
- Completed / blocker: `<completed work>`.
- Next stage: `<next workflow stage or skill>`.
- Entry condition: `<what must be true to enter it>`.

### Blocked report

- Current stage: `<detected workflow stage>`.
- Completed / blocker: `<blocking fact or missing evidence>`.
- Next stage: `<stage that resumes after the blocker>`.
- Entry condition: `<the approval, artifact, validation, or fix required>`.

### Approval-wait report

- Current stage: `<detected workflow stage>`.
- Completed / blocker: `<work ready for the named decision>`.
- Next stage: `<stage that follows approval>`.
- Entry condition: `<explicit user approval or recorded decision>`.

### Successful terminal report

- Current stage: successfully persisted `closing` or `abandoned`.
- Completed / blocker: `<persisted terminal outcome>`.
- Next stage: `none`.
- Entry condition: no further transition exists.
