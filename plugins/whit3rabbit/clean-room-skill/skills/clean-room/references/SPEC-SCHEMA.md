# Spec Schema Guide

## Artifact Names

Use these canonical artifact names unless the surrounding project already has a stricter convention:

- `task-manifest.json`
- `preflight-goal.json`
- `init-config.json`
- `clean-run-context.json`
- `source-index.json`
- `visual-index.json`
- `coverage-ledger.json`
- `evidence-ledger.json`
- `handoff-package.json`
- `role-session-brief.json`
- `controller-status.json`
- `behavior-spec.json`
- `skeleton-manifest.json`
- `implementation-plan.json`
- `implementation-report.json`
- `polish-report.json`
- `clean-room-result.json`
- `qc-report.json`
- `contamination-incident.json`

For multiple source units, place unit specs under a clean directory such as `behavior-specs/` and keep each file schema-compatible with `behavior-spec.schema.json`.

## Artifact CLI Discipline

Canonical artifacts are created and checked through CLI gates, not invented freehand by role agents.

- New artifact: run `clean-room-skill artifact template --kind <kind> --output <path>` or the artifact-specific generator, edit the generated file, then run `clean-room-skill artifact validate --path <path>`.
- Existing artifact: run `clean-room-skill artifact validate --path <path>` before using or editing it, then run validation again after edits.
- When `task-manifest.json` exists, use `clean-room-skill artifact validate --task-manifest <task-manifest.json> --path <artifact>` for runner-equivalent root, leakage, and handoff checks.

Do not ask shell-free roles to create missing canonical JSON from scratch. `preflight-goal.json`, `source-index.json`, and `visual-index.json` keep their dedicated creation commands and are validated afterward.

## Evidence Status

Use one of these values on claims:

- `observed`: Directly visible in authorized source, public behavior, generated analysis, or runtime output.
- `derived`: Calculated from observed facts, such as an interface shape inferred from manifest metadata.
- `inferred`: Reasonable but not directly proven.
- `unknown`: Material question not answered.
- `error`: Tooling or analysis failed in a way that affects confidence.

Do not upgrade `inferred` or `unknown` claims to `observed` during clean editing.

## Task Manifest Content

Capture:

- authorization and scope
- target identifier and source acquisition basis
- source workspace and clean workspace identifiers
- trust boundary and required profiles
- controller policy when the run is explicitly attended or unattended
- `preflight_goal_ref` and `preflight_goal_sha256`
- required `handoff_sequence`
- optional initialization snapshot copied from `init-config.json`
- user-selected output format profile
- Agent 0-4 pipeline responsibilities, required Agent 1.5 sanitizer role, and handoff rules
- artifact paths and retention policy
- contaminated artifact roots for `CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS`
- clean implementation roots for `CLEAN_ROOM_IMPLEMENTATION_ROOTS`
- implementation status, plan refs, and report refs
- optional `source_index_ref` for contaminated controller preflight output
- optional `visual_index_ref` for fallback contaminated visual-index preflight output
- optional `loop_context` for nested controller runs
- prohibited actions
- role assignments
- handoff policy
- tool and model policy
- source units with neutral ids
- per-unit `unit_kind`, with exactly one `foundation` unit and remaining implementation slices as `behavior` units
- optional per-unit `source_index_refs` such as `source-index:batch-0001` or `source-index:segment-file-000001-0001`
- optional per-unit `visual_index_refs` such as `visual-index:batch-0001` or `visual-index:image-000001`
- expected artifacts
- audit log refs

Use neutral ids such as `unit-foundation`, `unit-auth-flow`, or `unit-config-loading`. Avoid source path mirroring unless the path is already a public API or package name.

The foundation unit is first in code-development runs. It captures target stack, package or module boundaries, public manifest surfaces, test entrypoints, dependency policy, and destination constraints before behavior implementation starts. Public/package compatibility facts may appear in a normal behavior spec; destination/build constraints belong in `clean-run-context.json`, `skeleton-manifest.json`, and `implementation-plan.json`. Do not copy source dependency lists or package manifests into clean artifacts merely because they exist.

When a role needs more than one runtime profile, keep the role name stable and set `profile_purpose` to distinguish the sessions. For example, Agent 3 may use `report-review` for clean artifact work and `implementation` for the clean implementation workspace.

## Preflight, Initialization, And Clean Context

`preflight-goal.json` records user intent before source discovery, source indexing, visual indexing, decomposition, attended execution, or unattended execution. It is a controller/contaminated-side artifact and must not be placed in clean-role readable roots.

Capture:

- end goal, success definition, destination kind, and existing destination handling
- target stack: language, runtime, framework, package manager, and test framework
- license policy and dependency policy
- compatibility/exactness policy, with exactness limited to public observable surfaces
- feature preserve/remove/add lists and non-goals
- code hygiene limits
- optional execution policy: `host`, `docker`, or `podman`; one first-phase container profile; network and dependency install policy; native toolchain flag; and bounded CPU, memory, and timeout limits
- output policy
- controller mode and open questions

Unattended mode requires `unattended_allowed_after_preflight: true`, finite `max_iterations`, and no `open_questions`.

`init-config.json` records reusable controller-side preferences. It may contain source roots and contaminated-only rules, so keep it outside clean-role readable roots.

### Path Naming Guards

Default artifact roots live under `~/Documents/CleanRoom/<project>/tasks/<task-id>/` with a shared `~/Documents/CleanRoom/<project>/implementation/` root. If the user does not provide an explicitly approved neutral task ID, generate one as `task-` plus 8 lowercase hex characters. If the user does not provide an explicitly approved neutral project ID, generate one as `proj-` plus 8 lowercase hex characters. Do not use the source folder name as the task ID or project ID.

The legacy flat `~/Documents/CleanRoom/<task-id>/` layout remains valid only for explicit single-task compatibility. Project names follow the same neutrality rules as task IDs and are never derived from source folder names.

Clean artifact, contaminated artifact, and implementation roots must not contain source root basenames or meaningful non-generic tokens from those basenames. The environment preflight enforces this for `CLEAN_ROOM_CLEAN_ROOTS`, `CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS`, and `CLEAN_ROOM_IMPLEMENTATION_ROOTS`.

Capture:

- artifact base root, defaulting to `~/Documents/CleanRoom/<project>/tasks/<task-id>/` with neutral project and task IDs
- `project_id` and `project_root` for the default project layout, omitted only for explicit single-task compatibility
- source roots or fallback visual evidence roots, contaminated artifact root, clean artifact root, clean implementation roots, quarantine root, and approved public references
- target profile
- default model plus optional clean, contaminated, or per-role overrides
- clean isolation mode `clean-workspace`
- user rules split into `clean_safe` and `contaminated_only`
- reconfiguration policy requiring confirmation for root, schema, and model changes

`clean-run-context.json` is the only run context Agent 2, Agent 3, and Agent 4 should read. It may contain clean artifact paths, implementation root environment references, target profile, native artifact expectations, clean-safe goal contract fields, code hygiene policy, approved public references, clean-safe rules, clean-side model preferences, optional Agent 4 local commit policy (e.g. `implementation.polish_commit` with `agent4_shell_allowed`, `cwd_policy`, and `git_policy`), and the artifact-only coordination boundary. It must not contain source roots, visual roots, contaminated artifact roots, source index refs, visual index refs, coverage ledgers, evidence ledgers, contaminated-only rules, full `preflight-goal.json`, or the full `task-manifest.json`.

`context_management` is optional on `task-manifest.json` and `clean-run-context.json`. When present with `mode: "role-session-briefs"`, it records advisory or strict enforcement plus budgets for prompt characters, brief characters, artifact refs, and referenced artifact bytes. Strict mode requires a fresh role session and a valid `role-session-brief.json` for each stage.

## Source Index Content

`source-index.json` is a contaminated-only planning artifact generated before clean-room role sessions. Keep it under `CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS`.

Capture:

- generator name, version, scanner modes, limits, and source roots
- file metrics: bytes, lines, words, characters, and estimated tokens
- best-effort imports, exports, resolved local relationships, and unresolved references
- logical dependency groups, large word-count indicators, line-span file segments, and recommended Agent 1 batches
- optional AST/indexing dependency status recorded during preflight
- skipped files or directories and aggregate metrics

Skipped entries are bounded coverage metadata. They can include ignored directories, file count or byte caps, total byte caps, binary files, stat/read errors, post-read size changes, files that changed during read, symlinks outside the source root, directory traversal errors, and aggregate remaining-files-skipped-after-limit entries after global caps are reached.

Do not send `source-index.json`, file paths, import/export listings, dependency graphs, or private symbols to Agent 1.5 or clean roles. Agent 0 may map recommended batches or segment refs into neutral `task-manifest.json` units, where one unit is one bounded Agent 1 source-reading assignment.

## Visual Index Content

`visual-index.json` is a contaminated-only fallback planning artifact generated before clean-room role sessions when no indexable source code exists and screenshots/images are the authorized evidence. Keep it under `CLEAN_ROOM_CONTAMINATED_ARTIFACT_ROOTS`.

Capture:

- generator name, version, limits, and visual roots
- image metadata: relative path, media type, dimensions, bytes, and SHA-256
- recommended Agent 1 visual batches
- skipped files or directories and aggregate metrics

Skipped entries are bounded coverage metadata. They can include ignored directories, unsupported formats, file count or byte caps, total byte caps, stat/read errors, post-read size changes, files that changed during read, symlinks outside the visual root, and directory traversal errors.

Do not send `visual-index.json`, raw screenshots, visual paths, image hashes, copied visible text, exact palettes, exact iconography, exact spacing/layout reproduction, or distinctive visual expression to Agent 1.5 or clean roles. Agent 0 may map recommended batches into neutral `task-manifest.json` units. Agent 1 may use `view_image` only in the contaminated role and must convert observations into UI behavior, state, accessibility, interaction-purpose, hierarchy, and broad style claims with evidence refs.

## Controller Policy And Run State

`controller_policy` is optional. Missing policy means `attended`.

- `attended`: agent zero pauses for human review at scope gate, handoff, QC deltas, polish deltas, blocked units, and final coverage.
- `unattended`: agent zero runs a bounded inner clean-room loop only after preflight allows unattended mode with no open questions. It uses `max_iterations`, one unit per iteration, fresh role context, schema and leakage validation before advancing state, and hard stop conditions.

`loop_context` records the parent/child controller relationship when an outer spec-development loop invokes the inner clean-room loop. Capture:

- `parent_loop_kind: "spec-development"`
- `child_loop_kind: "clean-room"`
- `parent_loop_ref`
- `spec_slice_ref`
- `foundation_unit_ref`
- `approved_scope_refs`
- `acceptance_refs`
- `public_surface_refs`
- `return_to: "outer-spec-loop"`
- `outer_iteration`
- `inner_iteration`
- `max_inner_iterations`

The inner loop may select only units named by `approved_scope_refs`. `foundation_unit_ref` must resolve to the one `unit_kind: "foundation"` unit. A non-foundation slice must not run or complete until the foundation unit is covered. If a needed unit is outside that slice, return `spec-delta-required` instead of expanding scope.

`run_state` is optional for compatibility with older manifests. When present, it records `generation`, `started_at`, optional `previous_generation_ref`, and `restart_reason`. Valid restart reasons are `user-requested`, `contamination`, `scope-change`, and `invalid-state`.

Agent zero generates the durable tasklist as `task-manifest.json` `units`. It may use `source-index.json` batches to keep assigned source-reading context small while preserving source relationships, or `visual-index.json` batches for fallback screenshot/image analysis. It tracks source-side progress in `coverage-ledger.json` `source_units`, source-side evidence in `evidence-ledger.json`, terminal clean-side feedback in `implementation-report.json`, `qc-report.json`, and `polish-report.json`, and loop-back work as abstract delta tickets. Do not use prior chat history or live clean-role feedback as the source of truth for the next iteration.

Agent zero may also maintain `controller-status.json` as compact contaminated-side resume state. It records only current gate, selected unit, coverage state, implementation state, QC state, blockers, latest artifact refs, and next safe action. It must not be placed in clean roots or used as clean-role input.

## Format Selection

`task-manifest.json` records the user's output choice in `format_selection`. Use one canonical source model plus one target profile:

- `openspec-delta`: OpenSpec delta artifacts with `ADDED`, `MODIFIED`, `REMOVED`, or `RENAMED Requirements`.
- `gsd-planning-package`: GSD `.planning/` project and phase artifacts.
- `speckit-feature-folder`: Spec Kit `.specify/` constitution plus `specs/<feature-id>/` artifacts.
- `kiro-spec-folder`: Kiro `.kiro/specs/<slug>/` requirements, design, and tasks.

Every real task must record the user's actual target profile. Do not default silently. Populate `native_artifacts` and `formatting_rules` from the user's selected profile and current workflow. The archived reference `docs/research/archive/ARCHIVED-research-skill-spec.md` is historical guidance only, not active contract documentation.

## Agent Pipeline

`task-manifest.json` records the required Agent 0-4 handoff contract. New manifests must include schema field `agent_1_5` for the source-denied sanitizer. `agent_4` is optional for compatibility with older manifests, but new code-development manifests should include it:

- Agent 0: `contaminated-manager-verifier`; controller, scope manager, coverage verifier, and receiver of Agent 3's terminal report plus any configured Agent 4 polish report.
- Agent 1: `contaminated-source-analyst`; source reader and neutral draft task/spec generator.
- Agent 1.5: `contaminated-handoff-sanitizer`; source-denied contaminated reviewer that sanitizes draft specs before clean handoff.
- Agent 2: `clean-architect`; clean-domain implementation planner using approved handoff artifacts and clean implementation roots.
- Agent 3: `clean-qa-editor`; clean implementer/verifier that writes code only under implementation roots and emits one terminal report under `CLEAN_ROOM_CLEAN_ROOTS` for Agent 0.
- Agent 4: `clean-polish-reviewer`; clean final reviewer that writes `CLEAN_ROOM_CLEAN_ROOTS/polish-report.json`, implementation-root repo hygiene changes, and one constrained local commit when configured.

Agent 1.5 may read only Agent 0's neutral sanitizer brief, assigned draft artifacts, schema assets, and explicit public or destination reference roots. Do not give it source roots, visual roots, `source-index.json`, `visual-index.json`, raw screenshots, evidence ledger contents, private identifier denylist contents, raw diffs, source excerpts, or Agent 1 source-reading chat history.
Agent 2, Agent 3, and Agent 4 must start in the clean domain and read `clean-run-context.json`, approved clean artifacts, schemas, approved public references, and clean implementation roots only. They must not read source roots, contaminated ledgers, contaminated chat history, or the full `task-manifest.json`. Agent 0 may influence them only through schema-valid durable sanitized artifacts. Agents 3 and 4 report back to Agent 0 only after their assigned clean work is complete, blocked, or quarantined, with abstract findings or delta tickets only.

When context management is enabled, each role starts by reading `CLEAN_ROOM_SESSION_BRIEF_PATH`. The brief carries role, phase, unit, spec slice, fresh-context requirement, compact status, next action, allowed artifact refs with SHA-256, and forbidden inputs. Roles may load only the named artifact refs unless their role policy already permits direct source or destination inspection. If more context is needed than the brief budget permits, split the unit or return an abstract delta.

`handoff_sequence` must record either the legacy compatible order `preflight`, `source-destination-discovery`, `agent-0-decomposition`, `agent-1-analysis`, `agent-1-5-sanitization`, `clean-handoff`, `clean-planning`, `clean-implementation-qc`, and `agent-0-coverage-verification`, or the new code-development order with `clean-polish-review` inserted before `agent-0-coverage-verification`.

## Behavior Spec Content

Capture behavior rather than source structure:

- public surface and compatibility names
- producer role, source unit refs, evidence refs, confidence, and leakage risk
- inputs and outputs
- state transitions
- error conditions
- negative behaviors
- timing or ordering requirements
- security-relevant behavior
- invariants
- persistence, network, concurrency, or timing behavior when observable
- edge cases
- non-goals
- open questions
- test scenarios
- source-test-derived scenarios that validate equal output without copying source test names, fixtures, private helpers, or source-shaped structure
- visual fallback claims about UI intent, states, hierarchy, accessibility, interaction purpose, and broad style goals without copying visible text or exact visual expression
- API, protocol, config, and data/schema compatibility requirements
- leakage review status

For foundation specs, capture public package names, public module names, manifest fields, config keys, and test entrypoints only when they are public compatibility surface or destination constraints. Record dependency allow/block and install behavior through the existing dependency-policy and implementation-plan fields; do not mirror private source manifests.

Do not include source-shaped code blocks, raw screenshots, copied visible words, exact palettes, exact iconography, exact layout measurements, or visual-index contents in behavior specs. Use declarative requirements. Clean implementation code belongs only in `CLEAN_ROOM_IMPLEMENTATION_ROOTS` after Agent 2 has produced `CLEAN_ROOM_CLEAN_ROOTS/implementation-plan.json`.

Use `evidence_refs` values such as `evidence-ledger:item-001`. They must point to contaminated-side evidence ledger entries and must not carry source text into the clean artifact.

Package, namespace, module, class, function, method, variable, constant, field, and internal event names are private identifiers by default. Include a name only when it is public compatibility surface, and then record it in `public_surface` with `name`, `kind`, `visibility`, and `compatibility_reason`. Do not place source-private names in `summary`, claim text, `test_scenarios`, `open_questions`, or `compatibility_notes`.

Use existing fields for compatibility and parity. Put public API, protocol, config, and data/schema names in `public_surface` only when they are public compatibility surface. Put output equivalence in `outputs`, `observable_behaviors`, `invariants`, and `compatibility_notes` as applicable. Equal output includes public return values, serialized data, CLI or API responses, errors, state changes, ordering, and compatibility-relevant side effects.

Protocol parity checklist for exact-public-contract and behavior-compatible ports:

- Transcript shape: roles, message ordering, paired request/result groups, compaction effects, and retry/nudge history.
- Stable identifiers: request IDs, tool-call IDs, correlation IDs, and one-result-per-call pairing rules.
- Error model: soft versus hard failures, retry budgets, exhaustion thresholds, public error text or codes, and recovery paths.
- Streaming and queues: event order, final sentinels, disconnect behavior, queue serialization, queue caps, and backpressure where observable.
- Data fidelity: typed JSON values, nested objects, arrays, booleans, numbers, optional args, serialization formats, aliases, and registry completeness.
- Async/concurrency: async callable behavior, lifecycle ordering, locking, cancellation, and bounded work.

Use only the existing schema fields: put checklist items into `invariants`, `timing_or_ordering`, `error_conditions`, `compatibility_notes`, and `test_scenarios`. If any checklist item is relevant but unresolved, keep it in `open_questions`; approved specs with non-empty `open_questions` must produce abstract delta tickets or block completion.

For new handoff candidates, set `leakage_review.reviewer_role` to `contaminated-handoff-sanitizer`. Agent 1 may flag concerns in draft notes, but it does not pass its own artifacts for handoff.

## Coverage and Evidence Ledgers

Keep `coverage-ledger.json` and `evidence-ledger.json` in the contaminated artifact workspace. Clean roles may receive abstract coverage summaries or delta tickets only.

Capture:

- source unit status
- behavior spec refs
- evidence refs
- coverage gaps
- public-surface coverage entries using refs shaped as `public_surface:<spec_id>:<kind>:<name>` with status, evidence refs, optional work item refs, and optional verification refs
- contaminated-only discovery leads for authorized related surfaces that were detected but not analyzed, with priority and resolution status
- abstract delta tickets
- contaminated evidence descriptions that do not include source text in clean handoffs
- abstract source-test parity status and equal-output coverage gaps

`handoff-package.json` describes contaminated-to-clean transfer only. It may list `clean-run-context`, Agent 1.5-approved behavior specs, coverage-ledger summaries, open questions, test plans, and abstract delta tickets. Do not list full task manifests, source indexes, visual indexes, raw screenshots, clean-produced skeleton manifests, implementation plans, implementation reports, or QC reports in that handoff.

## Skeleton Manifest Content

Map clean behavior specs to destination architecture areas without imposing a source-derived design:

- architecture summary
- destination area name
- area id naming policy
- owned relative path prefixes
- area responsibilities and forbidden responsibilities
- allowed dependencies between architecture areas
- related behavior spec ids
- public contract refs to preserve
- target constraints supplied by the user or destination repo
- dependency constraints
- forbidden implementation material
- refactor triggers
- test mapping
- tests to create
- open decision status and owner

Keep target language generic unless the user provides one.

Map API, protocol, config, and data/schema compatibility into `public_contracts` and area-level `public_contract_refs`. Map source-test-derived scenarios and equal-output requirements into `test_mapping` and `test_obligations`. For code-development runs, every planned implementation or test path must fall under an owned path prefix for at least one referenced architecture area.

## Implementation Plan Content

`implementation-plan.json` is Agent 2's primary output under `CLEAN_ROOM_CLEAN_ROOTS` for code-development runs. Capture:

- clean implementation root refs such as `CLEAN_ROOM_IMPLEMENTATION_ROOTS[0]`
- clean source artifacts used for planning
- `architecture_manifest_ref` pointing to the current `skeleton-manifest.json`
- destination foundation summary
- code hygiene policy from preflight
- work items with architecture area refs, relative target paths, and test paths
- planned refactors for split, move, merge, or extract work
- local clean-project patterns and dependency constraints
- public contract refs and spec ids
- every exact-public-contract or behavior-compatible public-surface obligation listed in at least one work item's `public_contract_refs`
- argv-array verification commands with cwd set to implementation root refs
- optional per-command container metadata: `run_type`, `container_profile`, `network`, `dependency_mode`, and `timeout_seconds`
- risks, acceptance criteria, and open decisions
- forbidden implementation material

Use only relative destination paths. Do not include source roots, contaminated roots, source paths, private identifiers, raw diffs, copied comments, or source-shaped pseudocode.

Container metadata is declarative policy, not a shell escape hatch. Clean verification containers must not receive source roots or contaminated artifact roots.

## Implementation Report Content

`implementation-report.json` is Agent 3's implementation status artifact under `CLEAN_ROOM_CLEAN_ROOTS`. Capture:

- implementation status
- completed and blocked work items
- changed relative paths and file kinds
- argv-array verification command results and concise output summaries
- implementation or verification findings
- Agent 0 reporting state, with interim updates disallowed
- abstract delta tickets for Agent 0

Do not include raw source excerpts, contaminated evidence, or source stack traces. Agent 3 does not declare source coverage complete, does not report progress to Agent 0, and does not request Agent 0 guidance during implementation. Agent 0 verifies coverage from the contaminated side after the terminal report.

## Polish Report Content

`polish-report.json` is Agent 4's final clean review artifact under `CLEAN_ROOM_CLEAN_ROOTS`. Capture:

- reviewed artifacts
- security, docs/comments, exception handling, resource leak, race/concurrency, repo hygiene, verification, leakage, and correctness findings
- changed relative paths, including `AGENTS.md` and `.gitignore` when touched
- argv-array verification command results
- git repository status, commit-required flag, commit status, included paths, commit message, and commit hash
- residual risks and abstract delta tickets
- final status

Do not include source excerpts, contaminated evidence, source paths, private identifiers, raw diffs, or source-shaped pseudocode. A passing polish report with `git.commit_required: true` requires the constrained local commit to have succeeded and a real commit hash to be recorded. A passing report with `git.commit_required: false` is valid only when the clean-run-context commit policy is disabled and `git.commit_status` is `not-needed`.

## Clean-Room Result Content

`clean-room-result.json` is the inner loop return artifact. It is written only after Agent 0 consumes the terminal Agent 3 report, any configured Agent 4 polish report, and verifies coverage from the contaminated side.

Capture:

- task id
- result: `spec-slice-complete`, `spec-slice-blocked`, `spec-delta-required`, `contamination-suspected`, `iteration-limit-reached`, or `no-progress-detected`
- selected `spec_slice_ref`
- coverage state
- terminal implementation report ref
- QC report ref
- optional polish report ref
- abstract delta tickets
- return timestamp

Do not include source excerpts, raw diffs, source paths, private identifiers, contaminated evidence details, or source-shaped pseudocode. Abstract deltas return to the outer spec loop for resolution.

## QC Report Content

Capture:

- schema validation status
- leakage review status
- artifact hashes
- validator version
- leakage scan summary
- architecture alignment status and architecture findings
- coverage status
- required rerun status
- contamination incidents
- missing behavior
- ambiguous behavior
- untestable claims
- missing source-test parity
- missing equal-output assertions
- mismatches between specs, public contracts, architecture areas, changed paths, and test obligations
- terminology issues
- code hygiene violations
- clean-side changes made
- abstract delta tickets for contaminated verification

QC may edit clean specs for clarity, but must not introduce facts from source.

## Bundled Validator Scope

`hooks/validate-json-schema.py` is a lightweight local guardrail for common schema constraints: JSON syntax, artifact kind detection, required fields, type checks, enums, const values, local `$ref`, string length, regex patterns, date-time strings, numeric bounds, array item counts, uniqueness, `allOf`, `if`/`then`, and `additionalProperties: false`.

It is not a full JSON Schema 2020-12 implementation. Use a full validator for release-quality assurance, especially before publishing schema changes or accepting third-party artifact packages.
