# Clean-Room Process

## Purpose

Use this process to turn authorized source analysis into clean behavioral specifications and then into clean implementation code without moving source expression into the clean workspace. Treat the wall as a process, filesystem, and profile boundary. Prompt instructions alone are not sufficient.

This process reduces engineering risk. It does not resolve patent, trade-secret, license, contract, or jurisdiction-specific legal questions.

## Workspace Separation

Use separate locations for each trust domain:

- Contaminated source workspace: source-readable, read-only where practical, no clean implementation output. In visual fallback runs, authorized screenshot/image roots are source evidence roots.
- Contaminated artifact workspace: `preflight-goal.json`, `init-config.json`, `task-manifest.json`, source indexes, visual indexes, draft behavior specs, coverage ledgers, and abstract delta tickets. Configure it with `CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS`.
- Clean artifact workspace: sanitized clean run contexts, behavior specs that passed leakage review, skeleton manifests, implementation plans, implementation reports, QC reports, polish reports, incidents, and test plans. Configure it with `CLEAN_ROOM_CLEAN_ROOTS`.
- Clean implementation workspace: clean destination code, tests, fixtures, and real project files only. Configure it with `CLEAN_ROOM_IMPLEMENTATION_ROOTS`.
- Clean allowed reference workspace: public documentation or destination constraints explicitly configured for clean and source-denied role reads.

### Path Naming Guards

Clean, contaminated, and implementation paths must remain neutral. If the user does not provide an explicitly approved neutral task ID, generate one as `task-` plus 8 lowercase hex characters and use it under `~/Documents/CleanRoom/`.

Tasks targeting the same destination default to a clean-room project: `~/Documents/CleanRoom/<project>/tasks/<task-id>/` with one shared `<project>/implementation/` root. Project names follow the same neutrality rules as task IDs: a random neutral word pair (such as `amber-meadow`) or `proj-` plus 8 lowercase hex characters, matching `[a-z0-9][a-z0-9-]{0,63}`. Because the shared implementation root serves every task in the project, run at most one active task per project at a time; root-separation checks for one task cannot see a sibling task's concurrent clean implementation session. `clean-room-skill run` enforces this with an advisory `.clean-room-implementation.lock` in each implementation root, but manually launched role sessions outside the runner must still respect the rule. Use the legacy flat `~/Documents/CleanRoom/<task-id>/` layout only when explicitly running single-task compatibility mode.

Do not derive task IDs, project names, clean roots, contaminated artifact roots, or implementation roots from source folder names. The initialization wizard and environment preflight reject artifact paths that contain a source root basename or meaningful non-generic tokens from that basename.

Prefer separate agent profiles or homes when the host supports them. Do not rely on one chat context with role labels as the only separation control.

Use host-level policy where available:

- Claude role agents live in `agents/`.
- Claude hook scaffolding lives in `hooks/`.
- Codex agent templates live in `examples/codex/.codex/agents/`.
- Codex plugin hooks may require enabling plugin hook support in the user or project config before they run.

For clean roles, configure read hooks as deny-by-default. `CLEAN_ROOM_CLEAN_ROOTS` is the clean artifact allowlist, `CLEAN_ROOM_IMPLEMENTATION_ROOTS` is the clean destination foundation allowlist, and `CLEAN_ROOM_SCHEMA_DIR` is readable for bundled schemas. For Agent 1.5, configure reads as source-denied: assigned contaminated artifacts, `CLEAN_ROOM_SCHEMA_DIR`, and `CLEAN_ROOM_ALLOWED_READ_ROOTS` are allowed; source roots, visual roots, clean roots, implementation roots, `source-index.json`, and `visual-index.json` are denied. `CLEAN_ROOM_ALLOWED_READ_ROOTS` is the extra clean/source-denied read allowlist for public documentation or destination constraints. `CLEAN_ROOM_SOURCE_ROOTS` remains denied for source-denied roles even if a source path is also listed elsewhere.

For all roles, configure write hooks as deny-by-default. Agent 2 writes only under `CLEAN_ROOM_CLEAN_ROOTS`. Agent 3 writes clean reports under `CLEAN_ROOM_CLEAN_ROOTS` and code/tests only under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`. Agent 4 writes polish reports under `CLEAN_ROOM_CLEAN_ROOTS` and final hygiene/commit state only under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`. Clean-room artifact JSON files do not belong under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`. Contaminated roles may write only under `CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS`. Source roots should remain read-only for contaminated roles.

Agent zero/controller is responsible for computing the role environment block and passing it into every new role session. Sessions must not rely on inherited values. The minimum block is:

- `CLEAN_ROOM_ROLE`
- `CLEAN_ROOM_SOURCE_ROOTS`
- `CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS`
- `CLEAN_ROOM_CLEAN_ROOTS`
- `CLEAN_ROOM_IMPLEMENTATION_ROOTS`
- `CLEAN_ROOM_SCHEMA_DIR`
- `CLEAN_ROOM_ALLOWED_READ_ROOTS` for clean and source-denied roles, even when empty

When `context_management.mode` is `role-session-briefs`, Agent 0 also passes:

- `CLEAN_ROOM_SESSION_BRIEF_PATH`
- `CLEAN_ROOM_FRESH_CONTEXT_REQUIRED=1` when fresh context is required
- `CLEAN_ROOM_ROLE_SESSION_ID`

In strict mode, each role must run in a fresh model session, profile, or thread. Role labels inside one continuing chat are not fresh context. The role reads the session brief first, then loads only the artifact refs named in the brief unless its role policy already permits direct source or destination inspection. If the brief lacks required facts, exceeds the recorded budget, or would require prior chat history, the role blocks or emits an abstract split or delta request.

Optional guardrail value:

- `CLEAN_ROOM_PRIVATE_IDENTIFIER_DENYLIST`: path-separated, line-oriented files containing private source package, module, function, method, variable, constant, field, or other internal identifiers that must not appear in clean artifacts. Blank lines and `#` comments are ignored. Files are bounded to 1,000,000 bytes each, 20,000 total terms, and 512 characters per term. This is for hook scanning only; keep it outside clean/source-denied readable roots and do not include its contents in clean artifacts or sanitizer-readable briefs.

Do not grant shell-style tools to Agent 0, Agent 1, Agent 1.5, Agent 2, or the default Agent 3/4 profiles. Agent 3 terminal verification may use shell-style tools only when `CLEAN_ROOM_ALLOW_AGENT3_SHELL=1`, strict hooks are installed, the command cwd is under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, and the command invokes the installed `agent3-verification-runner.py`. Agent 4 final polish verification and local commit may use shell-style tools only when `CLEAN_ROOM_ALLOW_AGENT4_SHELL=1`, strict hooks are installed, the command cwd is under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`, and the command invokes the installed `agent4-polish-runner.py`. Shell access still does not replace OS/profile isolation for untrusted test code.

Agent 3 verification may use `--backend docker` or `--backend podman` only for verification/build commands from `implementation-plan.json`. Container backends mount the selected implementation root read/write, clean artifact roots read-only, schemas read-only, and approved public/reference roots read-only. They must not mount `CLEAN_ROOM_SOURCE_ROOTS`, `CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS`, a Docker socket, or privileged host paths. For the first Docker milestone, use `network: "off"` and `dependency_mode: "offline"` or `"locked"`; reject networked dependency installation.

Create or validate `preflight-goal.json` before source discovery, source indexing, visual indexing, Agent 0 decomposition, attended execution, or unattended execution. Treat it as controller/contaminated-side only. It may contain source license notes and output roots, so it must not cross to Agent 1.5, clean roles, or clean handoff packages. Clean roles receive only clean-safe goal fields and `code_hygiene_policy` through `clean-run-context.json`.

Run `scripts/build_source_index.py` only as source-index controller preflight before clean-room role sessions. Treat `source-index.json` as contaminated-only: it may record source paths, private import/export identifiers, file metrics, skipped-entry coverage gaps, large-file line spans, optional AST/indexing tool status, and dependency relationships. The indexer enforces file and byte limits after read, records files that change during read as skipped, reports directory walk errors, and prunes traversal after global limits with an aggregate skipped entry. Agent 0 may consume it to create neutral `task-manifest.json` units, but it must not cross to Agent 1.5, clean roles, or clean handoff packages.

Run `scripts/build_visual_index.py` only when no indexable source code exists and the user has authorized screenshot/image folders as the only evidence. Treat `visual-index.json` and raw images as contaminated-only: the index records visual paths, media types, dimensions, bytes, hashes, skipped-entry coverage gaps, and batches for Agent 0. It must not cross to Agent 1.5, clean roles, or clean handoff packages. Do not OCR, copy visible words, extract exact palettes, or preserve distinctive UI expression in clean artifacts. Include visual roots in `CLEAN_ROOM_SOURCE_ROOTS` so clean and source-denied roles cannot read raw screenshots.

Use `scripts/clean_room_tool_manager.py --status` when the controller needs to inspect optional AST/indexing helpers before indexing. It checks env overrides, `~/.cache/re-skills/clean-room-tools/`, skill-local tools, system PATH roots, and user toolchain PATH roots. It does not install anything unless the user explicitly runs `--install-local` with a strict SemVer version. Local npm-backed installs hold a cache-local lock before mutating the shared npm prefix and return structured JSON error facts for prefix creation failures, subprocess timeouts, and subprocess launch errors. Target-project `.local/bin`, `.bin`, and `node_modules/.bin` stay untrusted unless `--allow-working-project-tools` or `RE_SKILLS_TRUST_PROJECT_TOOLS=1` is set. Tools discovered under `/opt/homebrew` or `/usr/local` remain stat-only during `--probe-tools` unless `--allow-user-toolchain-probes` is also set.

Post-write hooks fail closed on filesystem races. Schema validation, leakage scanning, and handoff integrity checks should report redacted validation failures when an artifact cannot be statted, read, parsed, scanned, or hashed, rather than surfacing raw Python exceptions or absolute source-derived paths.

## Artifact Creation And Validation

The controller, durable runner, or main skill session runs artifact CLI commands. Shell-free role agents must not hand-write missing canonical JSON artifacts from scratch.

Use this sequence for every canonical clean-room JSON artifact:

- New artifact: `clean-room-skill artifact template --kind <kind> --output <path>` or the artifact-specific generator, then edit, then `clean-room-skill artifact validate --path <path>`.
- Existing artifact: `clean-room-skill artifact validate --path <path>` before reuse or edits, then validate again after edits.
- Manifest-backed run: prefer `clean-room-skill artifact validate --task-manifest <task-manifest.json> --path <artifact>` so root policy, leakage checks, and handoff checks match runner behavior.

Creation exceptions stay explicit: `preflight-goal.json` uses `clean-room-skill preflight --template` or `--input`; `source-index.json` uses `scripts/build_source_index.py`; `visual-index.json` uses `scripts/build_visual_index.py`. Validate all three after generation with `clean-room-skill artifact validate`.

Do not treat skill frontmatter or allowed tool lists as a complete enforcement boundary.

The task manifest records `preflight_goal_ref`, `preflight_goal_sha256`, the required `handoff_sequence`, and the Agent 0-4 pipeline plus Agent 1.5 for new runs:

- Agent 0 is the contaminated manager/verifier.
- Agent 1 is the contaminated source analyst and neutral task/spec generator.
- Agent 1.5 is the contaminated handoff sanitizer and independent source-denied scrubber.
- Agent 2 is the clean architect and implementation planner.
- Agent 3 is the clean implementer/verifier and emits one terminal implementation report for Agent 0.
- Agent 4 is the clean polish reviewer and emits one terminal polish report before contaminated coverage verification when configured.

Agent 1.5 runs in the contaminated domain but must not read source roots, visual roots, `source-index.json`, `visual-index.json`, contaminated evidence ledgers, raw screenshots, or Agent 1 source-reading chat history.
Agent 2, Agent 3, and Agent 4 are clean-domain roles. They may read `clean-run-context.json`, approved behavior specs, handoff packages, schemas, approved public references, and clean implementation roots only. Agent 2 writes implementation plans, not code. Agent 3 writes implementation code only under implementation roots. Agent 4 writes final polish changes, `AGENTS.md`, `.gitignore`, and local commits only under implementation roots. They must not read source workspaces, contaminated ledgers, contaminated chat history, or the full `task-manifest.json`. Agent 0 may influence these roles only through durable sanitized artifacts, not direct messages, implementation hints, progress feedback, or priority changes.

## Controller Modes

`task-manifest.json` may include `controller_policy`. Missing policy means `attended`. `task-manifest.json` may also include `loop_context` when a spec-development parent loop invokes the inner clean-room loop for one approved spec slice.

- `attended`: agent zero pauses for human review at scope gate, clean handoff, terminal implementation delta review, terminal polish delta review, blocked units, and final coverage.
- `unattended`: agent zero runs a bounded inner clean-room loop only after a complete preflight goal sets `unattended_allowed_after_preflight: true` and has no open questions. It reloads `task-manifest.json`, `coverage-ledger.json`, `evidence-ledger.json`, and clean QC artifacts at the start of each iteration, selects at most one pending or gap unit inside `loop_context.approved_scope_refs`, requires `loop_context.foundation_unit_ref` to point at the single foundation unit, starts each role session from fresh context with the required environment block, validates schema and leakage results before state advances, and stops on any configured safety or ambiguity condition.

The outer loop evolves specs, resolves abstract deltas, and chooses the next approved spec slice. The inner clean-room loop must not expand scope. It returns to the outer loop only through `clean-room-result.json` after Agent 0 has consumed Agent 3's terminal report, any configured Agent 4 polish report, and verified coverage from the contaminated side.

`task-manifest.json` may also include `run_state` to record the run generation, start timestamp, optional previous generation reference, and restart reason. It may include `initialization_snapshot`, an immutable copy of the effective `init-config.json` choices for resumability. New runs use generation `1`; start-over recovery increments generation or creates a fresh task id when prior state is not trusted.

The durable tasklist is `task-manifest.json` `units`, generated by agent zero during decomposition. Each unit declares `unit_kind: "foundation"` or `unit_kind: "behavior"`. New unattended code-development manifests must have exactly one foundation unit and approve it before behavior units. For multi-file scopes, the task manifest may reference contaminated `source-index.json` batches through `source_index_ref` and per-unit `source_index_refs`. For visual fallback scopes, it may reference contaminated `visual-index.json` batches through `visual_index_ref` and per-unit `visual_index_refs`. Progress is tracked in contaminated-side `coverage-ledger.json` and `evidence-ledger.json`; clean-side feedback returns only after terminal Agent 3/4 status through `implementation-report.json`, `qc-report.json`, `polish-report.json`, and abstract delta tickets. Prior chat is not a source of truth for the next iteration.

`controller-status.json` is Agent 0 compact memory for resume and handoff preparation. Keep it contaminated-side only. It may summarize current gate, selected unit, coverage state, clean implementation state, QC state, blockers, latest artifact refs, and next safe action. It must not be treated as clean input.

## Recovery Entry Points

Use recovery entry points only when durable artifacts already exist:

- `resume-cr`: reload the manifest, referenced preflight goal, initialization snapshot, ledgers, clean run context, handoff artifacts, implementation plan, implementation report, QC report, and abstract delta tickets; validate schema and leakage state; continue from the earliest incomplete gate under the recorded controller policy. Agent 0 may write or refresh `controller-status.json`, then create the next role-specific `role-session-brief.json`. Clean roles must receive the brief and clean artifact refs, not full resume state. If reusable `init-config.json` differs from the manifest snapshot, report drift and stop before applying changes. If new-run artifacts lack preflight refs or handoff sequence, stop for reviewed preflight migration.
- `start-over`: require explicit confirmation, archive or quarantine current artifacts without deletion, then return to the preflight gate with a fresh `task_id`.
- `refocus`: compare current artifacts to declared scope and preflight goal, identify missed gates or open deltas, and steer Agent 0 back to the earliest required gate without expanding scope.

All recovery flows preserve the clean-room wall. Source indexes, visual indexes, raw screenshots, private identifiers, contaminated evidence ledgers, and contaminated chat history remain out of Agent 1.5, clean roles, and clean handoff packages.

## Role Duties

Contaminated manager/verifier:

- Confirm authorization and source scope.
- Create or validate `preflight-goal.json` before source discovery and record its ref/hash in `task-manifest.json`.
- Do not infer end goal, target language, runtime, framework, package manager, test framework, dependency policy, license policy, exactness policy, output directory, or feature add/remove policy from source. Completed and unattended preflight contracts require explicit user intent confirmation.
- Create or update controller-side `init-config.json` when the user invokes initialization, then snapshot effective preferences into `task-manifest.json`.
- Produce sanitized `clean-run-context.json` for Agent 2, Agent 3, and Agent 4. Include clean artifact paths, implementation root environment references, target profile, clean-safe goal contract fields, code hygiene policy, approved public refs, clean-safe rules, clean-side model preferences, and artifact-only coordination policy only.
- Record optional `context_management` budgets in `task-manifest.json` and `clean-run-context.json` when low-context handoffs are enabled.
- Maintain contaminated-side `controller-status.json` and create one compact `role-session-brief.json` per role launch.
- Consume contaminated `source-index.json` when present.
- For visual fallback only, consume contaminated `visual-index.json` and pause in attended mode to ask what the screenshots are meant to accomplish, including product goal, target user flow, screenshot coverage, target stack, UI exactness boundary, and whether visible words are public compatibility surface.
- Split work into bounded logical units that can map to one source-index or visual-index batch.
- Create exactly one foundation unit first. It captures target stack, package or module boundaries, public manifest surfaces, test entrypoints, dependency policy, and destination constraints. Do not approve behavior slices until the foundation unit is covered.
- Track coverage in `coverage-ledger.json`.
- Track contaminated evidence references in `evidence-ledger.json`.
- Provide Agent 1.5 only a neutral sanitizer brief with domain purpose, target profile, unit intent, public compatibility allowlist, and blocked categories.
- Compare clean artifacts and terminal implementation, QC, and polish reports against source behavior, discovered source tests, equal-output requirements, and public API/schema compatibility.
- For exact-public-contract or behavior-compatible units, split broad public surfaces into smaller units or maintain `public_surface_coverage` entries for every required `public_surface:<spec_id>:<kind>:<name>` obligation before marking coverage complete.
- Keep high-priority `discovery_leads` unresolved only while coverage is partial, blocked, or waiting for a follow-up unit. Do not mark a unit covered or send it to handoff with unresolved high-priority discovery leads.
- Do not treat the foundation unit as permission to copy package manifests or dependency lists. Dependencies are preserved only when required by public compatibility, destination evidence, or explicit preflight policy.
- Return only abstract delta tickets into a fresh clean artifact cycle, such as "retry behavior after transient network failure is missing."

Contaminated source analyst/spec writer:

- Verify Agent 0 provided the preflight goal hash, assigned unit, source scope, evidence handling policy, target stack, and compatibility policy before reading source.
- Read the bounded source needed to fully inventory the assigned unit's observable surface while staying inside assigned refs.
- In visual fallback units, use assigned `visual_index_refs` and `view_image` only from the contaminated role. Describe UI intent, screen states, hierarchy, accessibility expectations, interaction purpose, and broad style goals without copying visible text, exact palettes, exact iconography, spacing, or distinctive layout expression.
- Describe observable behavior, public contracts, states, errors, invariants, and compatibility requirements.
- For foundation units, describe public package/module boundaries, target stack, test entrypoints, dependency policy, and destination constraints without copying private package layout or source dependency lists.
- When relevant, account for CLI arguments, flags, environment overrides, TUI commands, keyboard shortcuts, menu states, UI states, accessibility expectations, config keys, protocol entry points, and public user-visible behavior. Record related authorized surfaces that cannot be analyzed in the assigned context as contaminated `discovery_leads`, not clean spec fields.
- Treat discovered source tests as behavioral evidence and convert them into clean `test_scenarios` that validate the same observable outputs.
- Define equal output in behavioral terms: public return values, serialized data, CLI or API responses, errors, state changes, ordering, and compatibility-relevant side effects.
- For exact-public-contract or behavior-compatible ports, capture invariant-level acceptance tests, not only module/API coverage.
- Use the existing behavior-spec fields for protocol parity. When present, record transcript shape, request/response ID pairing, error budget counters, streaming event order, queue bounds, sampling registry aliases, async behavior, and typed JSON or nested argument preservation in `invariants`, `compatibility_notes`, and `test_scenarios`.
- Non-empty `open_questions` in approved behavior specs must become abstract delta tickets or block completion.
- Mark every claim as `observed`, `derived`, `inferred`, `unknown`, or `error`.
- Treat package, module, class, function, method, variable, constant, and field names as private identifiers unless they are public compatibility surface.
- Write drafts and flag suspected leakage, but do not approve your own work for handoff.

Contaminated handoff sanitizer:

- Start from a fresh source-denied context with no Agent 1 source-reading chat history.
- Verify Agent 0 provided only a neutral sanitizer brief and assigned draft artifact paths; reject any full preflight goal, source index, visual index, raw screenshot, or evidence ledger input.
- Read only Agent 0's neutral brief, assigned draft artifacts, schema assets, and explicit public or destination reference roots.
- Remove source expression, source paths, visual paths, image hashes, copied visible words, import/export listings, dependency graphs, source test names, fixture structure, private helpers, copied comments, raw diffs, distinctive strings, exact UI palettes/layouts/iconography, and source-shaped structure before handoff.
- Preserve public names only when listed in `public_surface` with compatibility reasons.
- Record `leakage_review.reviewer_role` as `contaminated-handoff-sanitizer`.
- Quarantine failed artifacts and return only abstract regeneration feedback to Agent 0.

Clean architect/implementation planner:

- Start from the clean artifact workspace and read only `clean-run-context.json`, approved clean artifacts, schemas, approved public references, and `CLEAN_ROOM_IMPLEMENTATION_ROOTS`.
- Validate `clean-run-context.json` includes clean-safe goal contract fields and code hygiene policy before planning.
- Ignore direct Agent 0 messages or manager notes unless they arrive as schema-valid clean artifacts for a fresh clean session.
- Merge approved handoff artifacts into the selected clean schema base.
- Inspect the clean destination foundation and approved foundation spec to identify relative target paths, local patterns, tests, dependency policy, package boundaries, and argv-array verification commands.
- Read any existing `skeleton-manifest.json` and maintain it as the whole clean destination architecture map.
- Define architecture areas with owned relative path prefixes, responsibilities, forbidden responsibilities, allowed area dependencies, and refactor triggers.
- Assign every planned target and test path to one or more architecture areas.
- Record split, move, merge, or extract work as planned refactors before implementation.
- Produce `CLEAN_ROOM_CLEAN_ROOTS/implementation-plan.json` as the primary code-development contract.
- Keep `skeleton-manifest.json` valid and current for code-development runs.
- Do not write implementation code.

Clean implementer/verifier:

- Start from the clean domain and validate `clean-run-context.json` before using run preferences.
- Validate the implementation plan includes the preflight-derived code hygiene policy before editing code.
- Read `implementation-plan.json` and implement each unblocked work item for the selected spec slice and current unit.
- Read `skeleton-manifest.json` before editing and touch only paths owned by the work item's referenced architecture areas.
- Refuse unowned target paths and unplanned cross-area refactors by recording an abstract delta.
- Write code, tests, fixtures, and destination project files only under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`.
- Run bounded argv-array verification commands only through the installed Agent 3 verification runner.
- Produce or update `CLEAN_ROOM_CLEAN_ROOTS/implementation-report.json` with changed paths, verification results, blockers, and abstract delta tickets.
- Maintain `CLEAN_ROOM_CLEAN_ROOTS/qc-report.json` for schema, leakage, and clean artifact status when the run expects it.
- In unattended inner-loop mode, stop at the selected spec slice. If the plan expands beyond that slice or cannot fit one fresh clean implementation context, mark the unit blocked with `spec-delta-required` or `split-required`.

Clean polish reviewer:

- Start from the clean domain after Agent 3 terminal reports exist.
- Read only `clean-run-context.json`, `implementation-plan.json`, terminal implementation/QC reports, approved clean artifacts, schemas, public refs, and implementation-root files.
- Review security, missing docs/comments, exception handling, resource leaks, race/concurrency risks, missing tests, and repository hygiene.
- Update implementation-root `AGENTS.md` with gotchas and build/test/dev commands discovered from clean files.
- Update implementation-root `.gitignore` only for real generated outputs, dependencies, caches, or build/test artifacts.
- Run verification and commit only through `agent4-polish-runner.py` with `CLEAN_ROOM_ALLOW_AGENT4_SHELL=1`.
- Stage only paths listed in `polish-report.json` `git.include_paths` and create at most one local implementation-root commit.
- Set `git.include_paths` to the union of terminal Agent 3 `implementation-report.json` `changed_paths` and Agent 4 `polish-report.json` `changed_paths`; leave unreported dirty files uncommitted.
- Write `polish-report.json` with findings, changed paths, verification results, git status, commit hash/status, residual risks, and abstract delta tickets.
- For controller-finalized commits, write a pre-commit `polish-report.json` with `final_status: "blocked"`, `git.commit_required: true`, and `git.commit_status: "not-run"`.
- Do not report progress or ask Agent 0 for guidance while implementing. Mark `implementation-report.json` as terminal only after the selected slice work is complete, blocked, or quarantined.

## Workflow

1. Preflight goal gate:
   - Create or validate `preflight-goal.json`.
   - Record end goal, target stack, license policy, dependency policy, compatibility policy, feature policy, code hygiene policy, output policy, controller policy, and open questions.
   - Stop before source discovery if authorization, scope, output roots, or blocking product intent are unclear.
2. Initialization gate:
   - Record reusable preferences in `init-config.json` when requested.
   - Default the task root to `~/Documents/CleanRoom/<project>/tasks/<task-id>/` unless the user selects another separated location. Generate a neutral `task-` plus 8 lowercase hex characters when the user does not provide an explicitly approved neutral task ID.
   - Use the project recorded by `.clean-room/local-state.json` when adding work to an existing destination project; otherwise create or record a neutral project, share the project-level `implementation/` root, and record `project_id` and `project_root` in `init-config.json` and the manifest `initialization_snapshot`.
   - Reject clean, contaminated, or implementation roots that mirror source root basenames or meaningful non-generic source-name tokens.
   - Record model preferences as a default model plus optional domain or role overrides.
   - Split user rules into clean-safe and contaminated-only rules.
   - Set clean isolation mode to `clean-workspace` and record separate implementation roots.
3. Scope gate:
   - Record requester, target identifier, authorization text, source scope, clean output scope, prohibited actions, and evidence handling.
   - Record the user's selected `format_selection.target_profile` and native artifact expectations. The archived reference `docs/research/archive/ARCHIVED-research-skill-spec.md` is historical guidance only, not active contract documentation.
   - Record `preflight_goal_ref`, `preflight_goal_sha256`, and `controller_policy` from preflight when the task should run in explicit attended or bounded unattended mode.
   - Record `run_state` with generation, start timestamp, and restart reason.
   - Record `initialization_snapshot` when init preferences exist.
   - Record the Agent 0-4 pipeline, required Agent 1.5 sanitizer role, required `handoff_sequence`, and handoff rules.
   - Record the source roots, contaminated artifact roots, clean roots, implementation roots, schema directory, and clean/source-denied allowed read roots that agent zero/controller will pass to each session.
   - Stop if authorization or ownership is unclear.
4. Clean context:
   - Create `clean-run-context.json` for Agent 2, Agent 3, and Agent 4.
   - Include only clean artifact paths, implementation root environment references, target profile, native artifact expectations, approved public references, clean-safe goal contract fields, code hygiene policy, clean-safe rules, clean-side model preferences, and optional context-management budgets.
   - Do not include source roots, contaminated roots, source index refs, visual index refs, coverage ledgers, evidence ledgers, contaminated-only rules, `preflight-goal.json`, or the full task manifest.
5. Source index preflight:
   - Run `scripts/build_source_index.py` outside clean-room role sessions when source scope is larger than a single obvious unit.
   - Write `source-index.json` under the contaminated artifact workspace.
   - Keep dependency detection pre-loop and bounded; do not install Homebrew, npm, SDK, pip, or local-download tools implicitly.
   - Validate the source index schema before Agent 0 consumes it.
   - If no indexable source code exists and screenshots are authorized as the only evidence, run `scripts/build_visual_index.py` instead, write `visual-index.json` under the contaminated artifact workspace, and validate its schema before Agent 0 consumes it.
6. Decompose:
   - Create the tasklist as bounded source units with neutral ids in `task-manifest.json`.
   - Prefer behavior or public surface groupings over source-file mirroring.
   - Use source-index dependency groups, `recommended_batches`, `large_items`, and `file_segments` to keep Agent 1 context small while preserving import/export relationships.
   - For visual fallback, use visual-index `recommended_batches` to keep Agent 1 screenshot review bounded; do not derive unit ids from screenshot filenames.
7. Analyze:
   - Start from a fresh role session brief when context management is enabled.
   - Read source in the contaminated workspace.
   - Write draft behavior specs using the schema fields.
   - If source tests are discovered, record their behavioral intent as evidence and create leakage-safe `test_scenarios` for the same observable outputs.
   - Record equal-output expectations for public return values, serialized data, CLI or API responses, errors, state changes, ordering, and compatibility-relevant side effects.
   - Include only compatibility-relevant public names.
   - Record retained public names in `public_surface` with `name`, `kind`, `visibility`, and compatibility reasons.
   - For visual fallback, record UI claims as behavior-spec observations with evidence refs; do not copy visible words unless preflight recorded them as public compatibility surface.
8. Sanitize:
   - Apply `LEAKAGE-RULES.md`.
   - Start Agent 1.5 from fresh context without source access or Agent 1 source-reading chat history.
   - Use only the neutral sanitizer brief and assigned draft artifact paths.
   - When strict context management is enabled, the role session brief must name those assigned artifacts and no source-side ledgers.
   - Remove copied expression and source-shaped structure.
   - Run the leakage hook with `CLEAN_ROOM_PRIVATE_IDENTIFIER_DENYLIST` when a private identifier list exists.
   - Record unresolved questions instead of guessing.
9. Handoff:
   - Move only Agent 1.5-approved structured artifacts and `clean-run-context.json` to the clean workspace.
   - Include only allowed handoff artifact types: `clean-run-context`, `behavior-spec`, `coverage-ledger-summary`, `open-questions`, `test-plan`, and `abstract-delta-ticket`.
   - Use `coverage-ledger-summary` for neutral coverage status only; do not include raw contaminated ledgers.
   - Do not include `task-manifest.json`, `preflight-goal.json`, `source-index.json`, `visual-index.json`, raw screenshots, source or visual paths, image hashes, import/export listings, or dependency graphs.
   - Do not include clean-produced skeleton manifests, implementation plans, implementation reports, or QC reports in contaminated-to-clean handoff packages.
   - Preserve producer role and Agent 1.5 review status.
   - Create `handoff-package.json`.
10. Plan implementation:
   - Start from a fresh role session brief when context management is enabled.
   - Agent 2 starts from the clean artifact workspace and builds or merges the clean schema base from `clean-run-context.json`, approved handoff artifacts, the selected target profile, target constraints, and clean implementation foundation.
   - Update `skeleton-manifest.json` as the clean destination architecture map before writing work items.
   - Produce `CLEAN_ROOM_CLEAN_ROOTS/implementation-plan.json` with relative destination paths, architecture area refs, work items, tests, code hygiene policy, constraints, risks, planned refactors, and argv-array verification commands.
   - Keep `skeleton-manifest.json` valid and current for code-development runs.
   - Avoid implementation code, private algorithm choices, source-derived layout, and source-shaped pseudocode.
11. Implement and verify:
   - Start from a fresh role session brief when context management is enabled.
   - Agent 3 starts from the clean domain, reads `implementation-plan.json`, and writes code/tests only under `CLEAN_ROOM_IMPLEMENTATION_ROOTS`.
   - In unattended inner-loop mode, Agent 3 executes only work items for the selected spec slice and current unit.
   - Run bounded argv-array verification commands only through the installed Agent 3 verification runner.
   - Record changed paths, verification status, blockers, and abstract delta tickets in `CLEAN_ROOM_CLEAN_ROOTS/implementation-report.json`.
   - Maintain `CLEAN_ROOM_CLEAN_ROOTS/qc-report.json` for schema, leakage, architecture alignment, source-test parity, equal-output assertions, and spec-to-plan-to-test mismatches.
   - Verify public-surface inventory parity item by item; each required public command, API, config, protocol, or user-visible behavior must map from behavior spec test coverage to implementation-plan `public_contract_refs`, terminal report completion, and coverage-ledger `public_surface_coverage`.
   - Treat missing invariant tests as a parity gap when protocol, serialization, streaming, queueing, error-budget, async, or typed-data behavior is in scope.
   - Do not send Agent 0 progress updates or partial findings while work remains in progress.
12. Polish review:
   - Start from a fresh role session brief when context management is enabled.
   - Agent 4 starts from the clean domain, reviews only clean implementation-root files and clean artifacts, and writes `CLEAN_ROOM_CLEAN_ROOTS/polish-report.json`.
   - Create or update implementation-root `AGENTS.md` and `.gitignore` only when the clean implementation actually needs them.
   - Commit only through `agent4-polish-runner.py`, with `git.include_paths` covering terminal Agent 3 changed paths plus Agent 4 polish paths, and with no push, tag, reset, clean, branch deletion, or arbitrary git commands.
13. Verify coverage:
   - Contaminated manager checks gaps against source behavior, discovered source tests, equal-output requirements, public contract compatibility, terminal implementation reports, and terminal polish reports when configured.
   - Reject completion when any required public-surface obligation is missing from behavior spec test coverage, implementation-plan `public_contract_refs`, terminal implementation completion, or coverage-ledger `public_surface_coverage`.
   - Do not mark exact-public-contract or behavior-compatible work complete while approved behavior specs have open questions or untested compatibility-critical invariants.
   - Return only abstract deltas through updated durable artifacts for a fresh clean cycle.
   - In unattended mode, reload durable artifacts and process at most one pending or gap unit per iteration inside the approved spec slice.
   - Repeat analyze, sanitize, handoff, plan, implement, QC, polish, and contaminated-side coverage verification until the selected spec slice is complete, blocked, delta-required, quarantined, or a stop condition is reached. Do not steer an active Agent 2, Agent 3, or Agent 4 session.
   - Write `clean-room-result.json` before returning to the outer spec loop.

## Stop Conditions

Stop the workflow when any of these occur:

- Authorization is missing or narrower than the requested analysis.
- `preflight-goal.json` is missing, invalid, incomplete for unattended mode, or drifted from `task-manifest.json` refs.
- Clean roles were exposed to source, contaminated chat history, raw diffs, or copied source expression.
- Clean roles were given the full `task-manifest.json`, source roots, contaminated roots, source index refs, visual index refs, coverage ledgers, or evidence ledgers instead of `clean-run-context.json`.
- Agent 1.5 was exposed to source roots, visual roots, `source-index.json` contents, `visual-index.json` contents, raw screenshots, contaminated evidence ledgers, private identifier lists, raw diffs, source excerpts, or Agent 1 source-reading chat history.
- Implementation roots overlap source, contaminated artifact roots, clean artifact roots, or schema roots.
- Agent 2 is asked to write code.
- Agent 3 needs shell access without `CLEAN_ROOM_ALLOW_AGENT3_SHELL=1`, outside implementation roots, or for anything except the installed verification runner.
- Schema validation or leakage scan fails.
- A unit is blocked, ownership is unclear, or the source scope changes.
- An unattended loop reaches its configured iteration limit.
- The selected spec slice is complete, blocked, or requires a spec delta.
- No durable artifact changes after an inner-loop iteration.
- The same unit is selected again after a no-progress iteration.
- Patent, trade-secret, license, or contract analysis is needed from counsel.
- The source or visual scope is too large to keep bounded index or coverage records.

## Final Package

Produce a final audit package containing:

- `task-manifest.json`
- `preflight-goal.json`
- `init-config.json`
- `clean-run-context.json`
- contaminated-side `source-index.json`
- contaminated-side `visual-index.json` when visual fallback was used
- contaminated-side `coverage-ledger.json`
- contaminated-side `evidence-ledger.json`
- `handoff-package.json`
- one or more `behavior-spec.json` files, or a directory of unit-specific behavior specs
- `skeleton-manifest.json`
- `implementation-plan.json`
- `implementation-report.json`
- `qc-report.json`
- `contamination-incident.json` records when applicable
- test plan content embedded in behavior specs, skeleton manifest, and implementation plan
- open questions and abstract delta tickets that remain unresolved

The clean artifact workspace package must contain only clean-approved artifacts. The clean implementation workspace contains the destination code changes. Keep raw contaminated ledgers in the contaminated artifact workspace unless a separate audit handoff explicitly includes them outside the clean workspace.
