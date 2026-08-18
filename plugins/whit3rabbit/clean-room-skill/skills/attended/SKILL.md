---
name: attended
description: Starts the Clean Room startup wizard in attended controller mode for authorized source-to-implementation work with human review pauses at clean-room gates.
argument-hint: [authorized source scope and separated output roots]
disable-model-invocation: true
---

# Clean Room Attended

Start the clean-room startup wizard with `controller_policy.mode` fixed to `attended`.

In Pi, this entry point is invoked as `/skill:attended`.

Use the canonical `clean-room` skill workflow and references in this plugin. Preserve the same clean-room boundary, role separation, artifact schemas, leakage rules, implementation-root rules, and hook expectations.

Before asking setup or preflight questions, use the canonical `clean-room` "Run State Discovery Before Wizard" rules. Resolve explicit artifact paths first, then current-repo `.clean-room/local-state.json`, then configured clean-room roots, then bounded `~/Documents/CleanRoom/task-*` (legacy) and `~/Documents/CleanRoom/*/tasks/task-*` (project layout) candidates. Treat target-repo `.clean-room/tasks/` as noncanonical unless explicitly provided or named by the local pointer. If a valid `task-manifest.json` exists, route to `resume-cr`. If a `task-manifest.json` exists but is invalid or legacy-shaped, stop and report its exact path and validation errors. If a valid canonical `preflight-goal.json` exists without a manifest, continue at source/destination discovery and manifest creation. If a preflight artifact exists but is invalid, stop with schema errors instead of restarting preflight. If a project is found with only completed tasks and the user wants more work, create the next task in that project by default. If multiple candidates are found without an explicit path, list them and stop for selection.

Load or create `preflight-goal.json` first. Attended mode may continue with unresolved questions only when they are recorded as `open_questions`; blocking questions become pause gates before affected work starts.

Gather only required setup facts:

- Authorization statement, requester, allowed actions, prohibited actions, and evidence handling.
- Artifact base root, defaulting the task root to `~/Documents/CleanRoom/<project>/tasks/<task-id>/`. If the user does not provide an explicitly approved neutral task ID, generate one as `task-` plus 8 lowercase hex characters. Do not derive task IDs or output directory names from source folder names.
- Project grouping, following the canonical `clean-room` project layout rules: `<base>/<project>/tasks/<task-id>/` with one shared `<base>/<project>/implementation/` root, an existing project from `.clean-room/local-state.json` when available, otherwise a neutral project name (`proj-` plus 8 lowercase hex unless the user supplies an approved neutral name, matching `[a-z0-9][a-z0-9-]{0,63}`, never source-derived), and at most one active task per project. Use legacy flat `<base>/<task-id>/` roots only when the user explicitly chooses single-task compatibility.
- Source roots, contaminated artifact root, clean artifact root, clean implementation root, quarantine root, and optional public or destination reference roots.
- Target stack, destination constraints, dependency/license policy, exactness policy, feature policy, code hygiene policy, and output policy from `preflight-goal.json`.
- Target schema profile: `openspec-delta`, `gsd-planning-package`, `speckit-feature-folder`, or `kiro-spec-folder`.
- Default model plus optional clean, contaminated, or per-role overrides.

Before indexing or artifact generation, confirm that source roots, contaminated artifact roots, clean artifact roots, clean implementation roots, approved public reference roots, and schema directory are separate paths, and that clean/contaminated/implementation root names are not source-derived. Stop if authorization is unclear, if clean and contaminated roots overlap, if implementation roots overlap another trust-domain root, or if root paths contain source root basenames or meaningful non-generic source-name tokens. Clean roles must receive `clean-run-context.json` and, when enabled, `role-session-brief.json`; they must not receive the full `task-manifest.json`. Agent 0 must influence clean roles only through durable sanitized artifacts.

Record `preflight_goal_ref`, `preflight_goal_sha256`, required `handoff_sequence`, and `controller_policy.mode` as `attended`. Pause for human review at preflight open questions, scope gate, clean handoff, terminal implementation or polish deltas, blocked units, and final coverage. Include stop conditions for `authorization-missing`, `scope-change`, `contamination-suspected`, `schema-validation-failed`, `leakage-scan-failed`, `unit-blocked`, `implementation-complete`, and `coverage-complete`; attended mode does not add an iteration-limit stop unless the user explicitly sets one.

For multi-file source scope, guide agent zero/controller to run `skills/clean-room/scripts/build_source_index.py` as preflight outside clean-room role sessions. Store `source-index.json` only under the contaminated artifact root and never include it in clean handoff packages. If no indexable source code exists and screenshots/images are the only authorized evidence, guide agent zero/controller to run `skills/clean-room/scripts/build_visual_index.py` instead, store `visual-index.json` only under the contaminated artifact root, include visual roots in `CLEAN_ROOM_SOURCE_ROOTS` (ensuring screenshot evidence directories are explicitly added to `CLEAN_ROOM_SOURCE_ROOTS` during execution so that path-aware read hooks such as `hooks/deny-clean-source-read.py` can protect them as expected), and pause before decomposition to clarify the product goal, target user flow, screenshot coverage, target stack, UI exactness boundary, and public-compatibility status of visible words.
