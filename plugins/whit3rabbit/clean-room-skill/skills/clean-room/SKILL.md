---
name: clean-room
description: Use for authorized clean-room, reverse-engineering, source-to-implementation, compatibility rewrite, or migration tasks. Produces clean behavioral specs, implementation plans, clean code changes, verification reports, QC reports, open questions, and test plans without moving source expression into the clean implementation.
compatibility: Designed for Claude Code, Codex, and Antigravity. Requires separate contaminated and clean workspaces or profiles for real clean-room use.
metadata:
  phase: clean-implementation
  legal_posture: risk_reduction_not_legal_advice
---

# Clean Room

## Overview

Produce clean behavioral specifications from authorized source analysis, then implement them in a separate clean destination code root. When no indexable source code exists and the user authorizes screenshots or images as evidence, produce clean behavioral specifications from contaminated visual observations instead. Keep contaminated source or visual evidence separate from clean planning, clean implementation, and verification.

This skill is not legal advice and does not create a legal safe harbor. Treat it as an engineering risk-reduction workflow for preserving a documented separation between source analysis, clean artifacts, and clean implementation code.

## Required Gates

1. Create or validate `preflight-goal.json` before source discovery, decomposition, attended execution, or unattended execution.
2. Confirm authorization, source scope, destination scope, allowed actions, prohibited actions, and evidence handling rules.
3. Separate contaminated artifacts, clean artifacts, and clean implementation code into different workspaces, worktrees, or repositories. Prefer separate agent profiles or homes when platform support exists.
4. Keep contaminated chat history, raw source, raw diffs, source excerpts, comments, distinctive identifiers, and implementation-shaped pseudocode out of clean artifacts.
5. Produce structured artifacts for the audit trail: preflight goal, init config, clean run context, role session briefs, controller status, source index or visual index, task manifest, evidence ledger references, coverage ledger summaries, behavioral spec, handoff package, skeleton manifest, implementation plan, implementation report, QC report, open questions, incident records, and test plan.
6. Write clean implementation code only under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, never in source or contaminated artifact roots.
7. Treat `allowed-tools` and skill frontmatter as convenience, not as a security boundary. Enforce separation with workspace paths, profiles, role agents, hooks, schema validation, and artifact quarantine.

## Role Model

Use these roles conceptually. If the host supports subagents, map each role to a separate agent or profile. If not, run the phases manually and keep artifacts separated.

- Agent 0 / contaminated manager/verifier: consumes the contaminated source index, or fallback visual index when no source code is available, decomposes scope into logical batches, tracks coverage, assigns source-reading or visual-evidence work, maintains compact controller status, creates low-context role session briefs, and checks final clean artifacts and terminal clean reports against source behavior, discovered source tests, equal-output requirements, and public contract compatibility. It may read source or visual evidence but must influence Agent 2, Agent 3, and Agent 4 only through durable sanitized artifacts, never direct chat, coaching, or in-progress feedback.
- Agent 1 / contaminated source analyst/spec writer: reads source in a read-only manner and writes neutral draft tasks and behavioral specs. It treats discovered source tests as behavioral evidence and converts them into clean `test_scenarios` for the same observable outputs. It must avoid code, copied comments, distinctive identifiers unless public API compatibility requires them, source test names or fixture structure, and source-shaped pseudocode. It does not approve its own drafts for handoff.
- Agent 1.5 / contaminated handoff sanitizer: works in a fresh source-denied contaminated context, reads only Agent 0's neutral brief plus assigned draft artifacts, scrubs identifying material, and approves or quarantines handoff candidates.
- Agent 2 / clean architect/planner: starts from the clean workspace, reads `clean-run-context.json`, approved clean handoff artifacts, the completed foundation spec, and the clean destination foundation under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`; then writes `CLEAN_ROOM_CLEAN_ROOTS/implementation-plan.json` with relative destination paths, tests, constraints, risks, and argv-array verification commands. It writes no code.
- Agent 3 / clean implementer/verifier: starts in the clean domain, reads `implementation-plan.json` and clean artifacts, writes code and tests only under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, writes reports under `CLEAN_ROOM_CLEAN_ROOTS`, records verification status, and emits exactly one terminal report for Agent 0 only after the assigned plan or task is complete, blocked, or quarantined. Run verification only through the installed Agent 3 verification runner; optional Docker or Podman verification must not mount source or contaminated artifact roots.
- Agent 4 / clean polish reviewer: starts in the clean domain after Agent 3 terminal reports, reviews final code for security, comments/docs, exception handling, resource leaks, race conditions, missing tests, and repo hygiene, writes `CLEAN_ROOM_CLEAN_ROOTS/polish-report.json`, may update implementation-root `AGENTS.md` and `.gitignore`, and may create one local implementation-root commit only through the installed Agent 4 polish runner. The commit path list must cover terminal Agent 3 changed paths plus Agent 4 polish changed paths.

## Workflow

Read `references/PREFLIGHT.md` before collecting the goal contract. Read `references/PROCESS.md` before running the workflow. Read `references/CONTROLLER-LOOP.md` before running attended, unattended, or resume controller work. Read `references/LEAKAGE-RULES.md` before writing or reviewing any artifact that crosses from contaminated to clean work. Read `references/SPEC-SCHEMA.md` when creating or validating artifact contents. Read `references/TARGET-LANGUAGE-GUIDE.md` when a destination language, framework, or public compatibility target is part of the request.

## Artifact CLI Discipline

The controller, durable runner, or main skill session owns artifact CLI execution. Role agents remain shell-free unless they are using the explicit Agent 3 or Agent 4 verification runners.

For every canonical clean-room JSON artifact:

- New artifact: run `clean-room-skill artifact template --kind <kind> --output <path>` or the artifact-specific generator first, then edit the generated file, then run `clean-room-skill artifact validate --path <path>` before the next gate.
- Existing artifact: run `clean-room-skill artifact validate --path <path>` before using or editing it, edit only after it validates or the controller accepts the repair target, then run validation again after edits.
- When a `task-manifest.json` exists, prefer `clean-room-skill artifact validate --task-manifest <path> --path <artifact>` so validation uses the same roots and hook checks as the runner.

Do not let shell-free role agents hand-write missing canonical artifacts from scratch. If an artifact is missing, invalid, or stale, the role must stop and require the controller, runner, or main skill session to create or validate it. `preflight-goal.json` still uses `clean-room-skill preflight --template` or `--input`; `source-index.json` and `visual-index.json` still use their dedicated indexer scripts before artifact validation.

Agent zero/controller must set and pass the clean-room environment block into every role session before tool use. Do not assume a new agent session inherits prior values. Required values are `CLEAN_ROOM_ROLE`, `CLEAN_ROOM_SOURCE_ROOTS`, `CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS`, `CLEAN_ROOM_CLEAN_ROOTS`, `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, `CLEAN_ROOM_SCHEMA_DIR`, and, for clean or source-denied roles, `CLEAN_ROOM_ALLOWED_READ_ROOTS`.

When `context_management.mode` is `role-session-briefs`, every role session starts from `CLEAN_ROOM_SESSION_BRIEF_PATH` plus the environment block. In `strict` enforcement, the controller must start a fresh model session, profile, or thread for each role, pass `CLEAN_ROOM_FRESH_CONTEXT_REQUIRED=1`, and keep the stage prompt, session brief, artifact ref count, and referenced artifact bytes inside the recorded budgets. Do not clear or delete durable artifacts to save tokens. Clear only model/chat context between roles.

`preflight-goal.json` is required before source indexing, visual indexing, or Agent 0 decomposition. It records the end goal, target stack, license policy, dependency policy, compatibility/exactness policy, feature policy, code hygiene limits, output policy, and controller mode. Completed preflight inputs and unattended contracts also record `intent_confirmation` with explicit user-confirmed end goal, target stack, and controller mode. It is controller/contaminated-side only; clean roles receive only the clean-safe `goal_contract` subset and `code_hygiene_policy` through `clean-run-context.json`.

When source scope is larger than a single obvious unit, run `scripts/build_source_index.py` as source-index preflight before starting clean-room role sessions. The resulting `source-index.json` is contaminated-only input for Agent 0. It may contain source paths, import/export names, dependency relationships, large-file segment spans, and optional local AST/indexing tool status, so do not place it in clean handoff packages or expose it to Agent 1.5, Agent 2, Agent 3, or Agent 4.

When no indexable source code is available and the user authorizes screenshots or image folders as the only evidence, run `scripts/build_visual_index.py` as visual-index preflight. Treat `visual-index.json` and all indexed images as contaminated-only source evidence. Do not OCR, copy visible words, extract exact palettes, duplicate distinctive layouts, or pass screenshots, visual paths, hashes, or visual-index contents to Agent 1.5 or clean roles. Visual roots must be included in `CLEAN_ROOM_SOURCE_ROOTS` for role sessions so clean and source-denied reads fail closed.

Optional AST/indexing helpers are detected before the controller loop through `scripts/clean_room_tool_manager.py --status` or through the dependency report embedded by `build_source_index.py`. No dependency is installed implicitly. Local installs require an explicit exact version, for example `scripts/clean_room_tool_manager.py --install-local ast-grep --version <exact-version>`, write under `~/.cache/re-skills/clean-room-tools/`, serialize npm prefix mutation with a cache-local lock, and return structured JSON error facts for setup failures. Target-project `.local/bin`, `.bin`, and `node_modules/.bin` are ignored unless `--allow-working-project-tools` or `RE_SKILLS_TRUST_PROJECT_TOOLS=1` is set.

Controller mode defaults to `attended` when `task-manifest.json` has no `controller_policy`. The outer loop evolves specs and selects one approved spec slice. Code-development runs start with exactly one `unit_kind: "foundation"` unit named by `loop_context.foundation_unit_ref`; non-foundation behavior slices wait until that unit is covered. The inner clean-room loop completes the approved slice through sanitized handoff, implementation, QC, optional final polish review, and contaminated-side coverage verification, then returns `clean-room-result.json` to the outer loop. In `attended` mode, agent zero pauses for human review at scope gate, handoff, QC deltas, polish deltas, blocked units, and final coverage. In `unattended` mode, agent zero may run a bounded inner loop: reload durable artifacts for each iteration, select at most one pending or gap unit inside `loop_context.approved_scope_refs`, start each role from fresh context with the required environment block, validate before advancing, and stop on any configured safety or ambiguity condition.

In Claude Code unattended mode, launch the durable runner with `clean-room-skill run --task-manifest <path> --agent-runtime claude` when possible and only after `task-manifest.json` has `loop_context` naming an approved pending or gap unit. For ccsilo/OpenRouter sessions, use `clean-room-skill run --task-manifest <path> --ccsilo [variant]` instead of manual `--agent-runtime claude`, `--agent-config-dir`, or `CLEAN_ROOM_CLAUDE_EXECUTABLE` wiring. If an unattended manifest lacks `loop_context`, treat it as incomplete outer-loop state and finish selected-slice approval before the runner is invoked. If `clean-room-skill` is not on `PATH`, immediately use `npx clean-room-skill@latest run --task-manifest <path> --agent-runtime claude`. Do not search plugin cache paths for schema files, and do not pass `--schema-dir /dev/null`; the runner uses bundled schemas by default. The main conversation must not do Agent 1, Agent 2, Agent 3, or Agent 4 work once runner-ready unattended state exists, and must not ask to continue while unattended policy still allows bounded progress. If role-agent dispatch is unavailable, fail closed with a blocker.

When installing, updating, checking status, running doctor, or launching the runner from a ccsilo Claude variant, prefer `clean-room-skill --ccsilo [variant]`, `clean-room-skill status --ccsilo [variant]`, `clean-room-skill update --ccsilo [variant]`, `clean-room-skill doctor --ccsilo [variant] --coverage`, and `clean-room-skill run --task-manifest <path> --ccsilo [variant]` instead of manually wiring `--config-dir` and `CLEAN_ROOM_CLAUDE_EXECUTABLE`. If the current session has `CLAUDE_CONFIG_DIR` under a ccsilo `variants/<name>/config` directory, omit the variant name and let the CLI read the sibling `variant.json`. Use manual `--config-dir` and executable environment overrides only when the ccsilo shortcut is unavailable. Never write `ANTHROPIC_AUTH_TOKEN` or API keys into ccsilo `settings.json`, `.claude.json`, or other settings files; credentials must stay in the wrapper/parent environment.

If a Claude runner stage reports `Not logged in · Please run /login`, first identify the configured agent harness. For ccsilo/OpenRouter, retry with `--ccsilo [variant]` before any manual wrapper debugging. For other wrapper/API-key harnesses, do not instruct the user to run `/login`; verify that the failing run launched the wrapper through `CLEAN_ROOM_CLAUDE_EXECUTABLE`, used the matching `--agent-config-dir`, and preserved the wrapper credentials. Claude `/login` applies only to OAuth-backed Claude sessions.

Do not grant shell-style tools to Agent 0, Agent 1, Agent 1.5, Agent 2, or the default Agent 3/4 role sessions. Agent 3 terminal verification may use shell-style tools only when `CLEAN_ROOM_ALLOW_AGENT3_SHELL=1`, the command cwd is under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, and the command invokes the installed `agent3-verification-runner.py`. Agent 4 polish verification and commit may use shell-style tools only when `CLEAN_ROOM_ALLOW_AGENT4_SHELL=1`, cwd is under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, and the command invokes the installed `agent4-polish-runner.py`. Use `--hooks=strict` for dedicated Codex, Claude, or OpenCode clean-room homes so hooks fail closed if required environment is missing or shell tools are invoked outside the allowed runner boundaries. Safe hook installs are compatibility-only between runs; during init/onboarding, prepare the role environment block and pass it into every clean-room role session so safe hooks enforce during active work.

Post-write hook failures are policy failures, not implementation guidance. If a clean or staged artifact cannot be read, scanned, schema-checked, or hashed because the filesystem changed, report the controlled redacted failure and ask the controller/user to restore readable artifact state before retrying.

## Recovery Entry Points

Use the recovery skills when a run already has durable artifacts:

- `resume-cr`: reload `task-manifest.json`, its `initialization_snapshot`, ledgers, `implementation-plan.json`, `implementation-report.json`, `qc-report.json`, and abstract delta tickets, then continue from the earliest incomplete gate using the recorded `controller_policy`. If `init-config.json` differs from the snapshot, report drift and wait for explicit confirmation.
- `start-over`: after explicit confirmation, non-destructively archive or quarantine existing artifacts and restart from the scope gate with a fresh `task_id`.
- `refocus`: audit declared scope against current artifacts and steer the workflow back to missed gates without expanding scope.

## Startup Wizard

Use the startup wizard when the user invokes this skill directly, such as `/clean-room`, `/clean-room:clean-room`, or Pi's `/skill:clean-room`, and does not provide an existing `task-manifest.json` or specific artifact review task.

### Run State Discovery Before Wizard

Before asking preflight questions, perform read-only run-state discovery. Do not rely on prior chat as state.

Discovery order:

1. Resolve explicit user-provided paths first. Accept a task root, `task-manifest.json`, `preflight-goal.json`, or `clean-room-bootstrap.json`.
2. Inspect the current working directory and its ancestors for `.clean-room/local-state.json`. If present, read it as a repo-local pointer to the external clean-room project; resolve `project_root`, `tasks_dir`, `implementation_root`, `latest_task_root`, and expected artifact names from that pointer before any global scan.
3. Inspect configured clean-room roots from the current request or environment, including `CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS`, `CLEAN_ROOM_CLEAN_ROOTS`, and `CLEAN_ROOM_IMPLEMENTATION_ROOTS` when present.
4. Scan `~/Documents/CleanRoom/task-*` (legacy single-task layout) and `~/Documents/CleanRoom/*/clean-room-project.json` plus `~/Documents/CleanRoom/*/tasks/task-*` (project layout) as a bounded fallback. Inspect only immediate project directories, their `tasks/` children, and expected artifact names.

Treat target-repository `.clean-room/tasks/` as noncanonical unless the user explicitly provides that path or the repo-local pointer identifies it as the external task root. Active artifacts belong under the external task root recorded by `clean-room-bootstrap.json`, `clean-room-project.json`, or `.clean-room/local-state.json`, not under the target repo stub.

If more than one candidate run is found without an explicit user path, list the candidate task roots grouped by project and stop for explicit selection. Do not choose the newest candidate automatically.

Classify the selected candidate before starting the wizard:

- Valid `task-manifest.json`: route to `resume-cr` and continue from the earliest incomplete gate.
- Invalid, legacy-shaped, or schema-incompatible `task-manifest.json`: stop, report the exact path and validation errors, and do not say no artifacts exist.
- Valid canonical `preflight-goal.json` without `task-manifest.json`: continue at source/destination discovery and manifest creation. Do not ask the preflight wizard again.
- `clean-room-bootstrap.json` only: run preflight using the bootstrap roots.
- `clean-room-project.json` with no task directories under `tasks/`: treat as an empty project and offer to create its first task inside that project.
- Project with only completed task directories: when the user asks to add more work, create the next task inside the same project and shared `implementation/` root by default.
- Invalid `preflight-goal.json`: stop, report canonical schema or required-field errors, and do not create a replacement preflight.
- No artifacts found: start the normal preflight wizard.

Load or create `preflight-goal.json` only after this discovery step. Do not start attended or unattended execution until the goal contract records the end goal, target stack, license policy, dependency policy, compatibility/exactness policy, feature add/remove policy, code hygiene limits, output policy, existing destination policy, and controller mode. Do not infer end goal, target language, runtime, framework, package manager, or test framework from source contents. If the user's end goal or target stack is unknown, record blocking `open_questions`, keep unattended disabled, and do not write runner-ready `task-manifest.json` or `clean-run-context.json`.

Gather only the setup facts needed to decide whether the workflow may start, or invoke `init` when the user wants a dedicated setup pass:

- Authorization statement, requester, allowed actions, prohibited actions, and evidence handling.
- Artifact base root. Default the task root to `~/Documents/CleanRoom/<project>/tasks/<task-id>/`. If the user does not provide an explicitly approved neutral task ID, generate one as `task-` plus 8 lowercase hex characters. Do not derive task IDs or output directory names from source folder names.
- Project grouping. Default to the clean-room project layout: `<base>/<project>/tasks/<task-id>/` with one shared `<base>/<project>/implementation/` root for every task in the project. If `.clean-room/local-state.json` points at a valid existing project, add new tasks to that project by default. When no existing project is detected and the user does not supply an approved neutral project name, generate `proj-` plus 8 lowercase hex characters; it must match `[a-z0-9][a-z0-9-]{0,63}`, must never be derived from source or destination folder basenames or meaningful source-name tokens, and appears in paths clean roles can see. Use the legacy flat `<base>/<task-id>/` layout only when the user explicitly chooses single-task compatibility. Only one task per project may run at a time because tasks share the implementation root; the durable runner enforces this with an advisory `.clean-room-implementation.lock` in each implementation root.
- Bootstrap creation. For new runs, call `clean-room-skill init` or `npx clean-room-skill@latest init`; pass `--project <name>` for a user-named project, pass `--new-project` when no valid local project pointer exists and no project name was supplied, and pass `--single-task` only for explicit legacy compatibility. Do not manually create task folders, project metadata, bootstrap metadata, or repo-local `.clean-room` pointer files.
- Source roots or fallback visual evidence roots, contaminated artifact root, clean artifact root, clean implementation root, quarantine root, and optional public or destination reference roots.
- Explicit user-confirmed end goal, target stack, and destination constraints from `preflight-goal.json`.
- Target schema profile: `openspec-delta`, `gsd-planning-package`, `speckit-feature-folder`, or `kiro-spec-folder`.
- Default model plus optional clean, contaminated, or per-role overrides.
- Additional user rules split into clean-safe and contaminated-only rules.
- Controller mode from `preflight-goal.json`. If unspecified, use `attended` only as a recorded preflight assumption.
- Run state. New runs use `generation: 1`, current `started_at`, and `restart_reason: user-requested`.
- Role hook environment block. Derive `CLEAN_ROOM_ROLE`, `CLEAN_ROOM_SOURCE_ROOTS`, `CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS`, `CLEAN_ROOM_CLEAN_ROOTS`, `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, `CLEAN_ROOM_ALLOWED_READ_ROOTS`, `CLEAN_ROOM_SCHEMA_DIR`, and optional hook-only denylist variables from the approved roots before launching any role session. Do not ask the user to export `CLEAN_ROOM_HOOK_ENFORCE` for normal safe-hook runs.

Before indexing or artifact generation, confirm that source roots, contaminated artifact roots, clean artifact roots, clean implementation roots, approved public reference roots, and schema directory are separate paths, and that clean/contaminated/implementation root path names are not source-derived. In project layout the implementation root is the shared project-level folder; per-task contaminated, clean, and quarantine roots stay under the task root, and the project name itself must pass the same source-derived-name checks. Stop if authorization is unclear, if clean and contaminated roots overlap, if implementation roots overlap any other trust-domain root, or if artifact/root paths contain source root basenames or meaningful non-generic source-name tokens. Agent 2, Agent 3, and Agent 4 must not receive source mounts or the full task manifest.

For `attended` mode, record a `controller_policy` that pauses for human review at scope gate, clean handoff, terminal implementation deltas, blocked units, and final coverage. Include stop conditions for `authorization-missing`, `scope-change`, `contamination-suspected`, `schema-validation-failed`, `leakage-scan-failed`, `unit-blocked`, `implementation-complete`, and `coverage-complete`; attended mode does not add an iteration-limit stop unless the user explicitly sets one.

For `unattended` mode, require explicit authorization, separated roots, finite bounds, `loop_context`, and a complete `preflight-goal.json` with no `open_questions`, `intent_confirmation` for explicit user-confirmed goal and target stack, and `unattended_allowed_after_preflight: true` before work starts. Record `controller_policy.mode` as `unattended`, `max_units_per_iteration` as `1`, `max_iterations` from preflight, and include these stop conditions: `authorization-missing`, `scope-change`, `contamination-suspected`, `schema-validation-failed`, `leakage-scan-failed`, `unit-blocked`, `implementation-complete`, `coverage-complete`, `iteration-limit-reached`, `spec-slice-complete`, `spec-slice-blocked`, `spec-delta-required`, `no-progress-detected`, `repeated-unit-selection`, and `clean-room-returned`.

Default sequence:

1. Preflight goal contract: create or validate `preflight-goal.json`.
2. Source and destination discovery: record reusable preferences in controller-side `init-config.json` when requested, choose a neutral task ID when needed, and run source-index preflight when needed. If no indexable source code exists and screenshots are explicitly authorized as the only evidence, run visual-index preflight instead.
3. Agent 0 decomposition: record authorization, boundaries, preflight goal hash, selected target profile, model policy, `run_state`, `handoff_sequence`, Agent 0-4 handoff contract, and required Agent 1.5 sanitizer role in `task-manifest.json`.
4. Clean context gate: create sanitized `clean-run-context.json` for Agent 2, Agent 3, and Agent 4. Include only clean artifact paths, implementation root environment references, target profile, clean-safe goal contract fields, code hygiene policy, approved public refs, clean-safe rules, clean-side model preferences, optional context-management budgets, and the artifact-only coordination boundary.
5. Contaminated spec writing: Agent 1 produces one or more draft `behavior-spec.json` artifacts from observed behavior, discovered source tests, public API contracts, error conditions, invariants, state transitions, and compatibility requirements. Source tests are behavioral evidence: convert them into clean `test_scenarios` that validate the same observable outputs without copying source test names, fixtures, private helpers, or source-shaped structure. For visual fallback, Agent 1 uses assigned `visual_index_refs` and `view_image` only in the contaminated role to describe UI intent, state, hierarchy, accessibility expectations, interaction purpose, and broad style goals without copying visible words or exact visual expression. For behavior-compatible ports, include compatibility-critical protocol, serialization, streaming, queueing, error-budget, async, and typed-data invariants when present.
6. Source-denied sanitization: Agent 1.5 receives only a neutral brief and assigned draft paths, removes identifying information, preserves the required artifact schema shape, records `leakage_review.reviewer_role` as `contaminated-handoff-sanitizer`, and quarantines failed artifacts.
7. Clean handoff: move only Agent 1.5-approved structured artifacts plus `clean-run-context.json` to the clean workspace. Do not hand off the full `task-manifest.json`. For each role launch, Agent 0 writes a compact `role-session-brief.json` for that role and phase; the brief carries status, next action, allowed artifact refs with hashes, and forbidden inputs. It is not a replacement for durable artifacts.
8. Clean planning: Agent 2 starts from the clean artifact root, reads `clean-run-context.json`, approved handoff artifacts, any existing `skeleton-manifest.json`, and the clean implementation foundation, then updates `skeleton-manifest.json` as the durable destination architecture map and produces `implementation-plan.json` with code hygiene policy. Use `implementation-plan.json` as the code-development work contract, and require every planned target/test path to be owned by a referenced architecture area.
9. Clean implementation and QC: Agent 3 reads `implementation-plan.json`, writes code and tests only under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, writes `implementation-report.json` under `CLEAN_ROOM_CLEAN_ROOTS`, maintains `CLEAN_ROOM_CLEAN_ROOTS/qc-report.json`, and loops without Agent 0 guidance until selected-slice work items are complete, blocked, or quarantined.
10. Clean polish review: when configured, Agent 4 reviews final code, updates only implementation-root polish files such as `AGENTS.md` or `.gitignore` when needed, writes `CLEAN_ROOM_CLEAN_ROOTS/polish-report.json`, and commits only through `agent4-polish-runner.py`. If the controller finalizes the commit, Agent 4 records `git.commit_status: "not-run"` and `final_status: "blocked"` until the bounded runner records the real commit hash.
11. Contaminated coverage verification: only after Agent 3 marks the report as terminal and any configured Agent 4 polish review passes may Agent 0 consume `implementation-report.json`, `qc-report.json`, `polish-report.json`, and `coverage-ledger.json`, compare against source coverage, and write `clean-room-result.json`. Exact-public-contract and behavior-compatible public-surface items must map item by item from behavior spec test coverage to implementation-plan `public_contract_refs`, terminal report completion, and coverage-ledger `public_surface_coverage`.
12. Repeat clean planning, implementation, and polish only from updated durable artifacts, never by steering an in-progress Agent 2, Agent 3, or Agent 4 session.

## Artifact Set

Use the JSON schemas in `assets/` as the contract for machine-readable artifacts:

- `task-manifest.schema.json`
- `preflight-goal.schema.json`
- `init-config.schema.json`
- `clean-run-context.schema.json`
- `source-index.schema.json`
- `visual-index.schema.json`
- `coverage-ledger.schema.json`
- `evidence-ledger.schema.json`
- `handoff-package.schema.json`
- `role-session-brief.schema.json`
- `controller-status.schema.json`
- `behavior-spec.schema.json`
- `skeleton-manifest.schema.json`
- `implementation-plan.schema.json`
- `implementation-report.schema.json`
- `clean-room-result.schema.json`
- `qc-report.schema.json`
- `polish-report.schema.json`
- `contamination-incident.schema.json`

Use `hooks/` as optional guardrail and audit scaffolding. Configure the host with explicit role and path environment variables before relying on the scripts:

- `CLEAN_ROOM_ROLE`
- `CLEAN_ROOM_SOURCE_ROOTS`
- `CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS`
- `CLEAN_ROOM_CLEAN_ROOTS`
- `CLEAN_ROOM_IMPLEMENTATION_ROOTS`
- `CLEAN_ROOM_ALLOWED_READ_ROOTS`
- `CLEAN_ROOM_SCHEMA_DIR`
- Optional `CLEAN_ROOM_ALLOW_AGENT3_SHELL=1` to allow isolated Agent 3 terminal verification through the installed verification runner only from implementation roots.
- Optional `CLEAN_ROOM_ALLOW_AGENT4_SHELL=1` to allow isolated Agent 4 polish verification and one local commit through the installed polish runner only from implementation roots.
- Optional `CLEAN_ROOM_PRIVATE_IDENTIFIER_DENYLIST` for hook-only scanning of private source identifiers.

For clean roles, read access is deny-by-default: allow only `CLEAN_ROOM_CLEAN_ROOTS`, `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, `CLEAN_ROOM_SCHEMA_DIR`, and explicit public or destination constraint roots in `CLEAN_ROOM_ALLOWED_READ_ROOTS`. Agent 1.5 is source-denied: allow only assigned contaminated artifacts, `CLEAN_ROOM_SCHEMA_DIR`, and explicit public or destination constraint roots. Write access is also deny-by-default: Agent 2 writes only clean artifacts, Agent 3 writes clean reports under `CLEAN_ROOM_CLEAN_ROOTS` and implementation files under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, Agent 4 writes polish reports under `CLEAN_ROOM_CLEAN_ROOTS` and final hygiene/commit state under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, clean-room artifact JSON files stay out of `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, and contaminated roles write only under `CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS`. Mark every behavioral claim as `observed`, `derived`, `inferred`, `unknown`, or `error`.

## Output Rules

Allowed clean-side artifact content:

- Neutral behavior descriptions.
- Public interface names only when needed for compatibility.
- Inputs, outputs, state transitions, invariants, errors, timing expectations, and test scenarios.
- Source-test-derived scenarios that validate equal output for public return values, serialized data, CLI or API responses, errors, state changes, ordering, and compatibility-relevant side effects.
- Abstract implementation constraints such as "must preserve stable sort order" or "must reject malformed input before persistence."
- Clean implementation plans and reports with relative destination paths, work items, argv-array verification commands, changed path summaries, and abstract blockers.

Blocked clean-side content:

- Source files, source excerpts, copied comments, raw diffs, stack traces containing source lines, and decompiled output.
- Raw screenshots, `visual-index.json`, visual paths, image hashes, copied visible text, exact palettes, exact iconography, exact spacing/layout reproduction, and distinctive visual expression.
- Pseudocode that mirrors source structure, function ordering, private helper names, or distinctive control flow.
- Nonessential package, module, class, function, method, variable, constant, field, internal identifiers, magic strings, log messages, UI copy, formatting, and naming schemes.
- Patent, trade-secret, or licensing conclusions presented as verified legal findings.

Identifier rule: package names, namespace/module paths, class names, function or method names, variable names, constants, fields, and internal event names are contaminated unless they are public compatibility surface. If retained, list the name in `public_surface` or `public_contracts` with `name`, `kind`, `visibility`, and a concrete compatibility reason; otherwise rewrite to neutral behavior.

## Completion Criteria

Finish the clean implementation loop when:

- `preflight-goal.json` records the user-approved goal contract before source discovery or decomposition.
- `task-manifest.json` defines source scope, clean scope, selected target profile, required preflight goal ref/hash, required handoff sequence, Agent 0-4 pipeline, Agent 1.5 sanitizer role, handoff rules, optional `initialization_snapshot`, optional `source_index_ref` or fallback `visual_index_ref`, `loop_context.foundation_unit_ref`, and `unit_kind`-typed units.
- `clean-run-context.json` exists for Agent 2, Agent 3, and Agent 4, records artifact-only coordination, clean-safe goal contract fields, code hygiene policy, and Agent 4 commit policy when configured, and does not contain source roots, visual roots, contaminated roots, source index refs, visual index refs, ledger paths, `preflight-goal.json`, or the full task manifest.
- Every in-scope unit has a behavior spec or an explicit out-of-scope record.
- Source tests and compatibility-critical invariants discovered in scope are represented as clean, leakage-safe `test_scenarios` or explicit coverage gaps.
- Approved behavior specs with non-empty `open_questions` must produce abstract delta tickets or block completion.
- `implementation-plan.json` maps clean specs to relative destination paths, tests, code hygiene policy, constraints, risks, and argv-array verification commands.
- Agent 3 has written implementation code only under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`.
- When context management is strict, every role was launched from a fresh context with a valid `role-session-brief.json` inside the recorded budgets.
- `implementation-report.json` records changed paths, verification results, completed and blocked work items, final implementation status, terminal Agent 0 reporting state, and abstract delta tickets.
- `skeleton-manifest.json` exists for code-development runs and records the current clean destination architecture map, including area-owned path prefixes and refactor triggers.
- `qc-report.json` records schema status, leakage review, unresolved gaps, source-test parity status, equal-output assertion status, and abstract delta tickets.
- Agent 0 has verified source coverage using only abstract clean-side reports and returns no open blocking deltas.
