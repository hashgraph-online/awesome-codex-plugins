---
name: preflight
description: Creates or reviews the required Clean Room preflight goal contract before source discovery, decomposition, attended execution, or unattended execution.
argument-hint: [new goal details or existing preflight-goal.json path]
disable-model-invocation: true
---

# Clean Room Preflight

Create or validate `preflight-goal.json` before active clean-room artifacts start.

Preflight stops after a canonical `preflight-goal.json` is created or validated. Do not create behavior specs, handoff packages, skeleton manifests, implementation plans, coverage ledgers, or clean-run-context artifacts during preflight.

Use the canonical `clean-room` workflow and read `skills/clean-room/references/PREFLIGHT.md` when collecting missing goal details. Preserve the clean-room boundary: `preflight-goal.json` is a controller/contaminated-side artifact and must not be placed in clean-role readable roots.

If the user provides output from CLI `clean-room-skill init` (or `npx clean-room-skill@latest init` if the binary is not available), check the generated bootstrap scaffold before creating or copying `preflight-goal.json`: `clean-room-bootstrap.json`, `contaminated/`, `clean/`, the implementation root, `quarantine/`, target repo `.clean-room/README.md`, `.clean-room/.gitignore`, and `.clean-room/local-state.json` must exist and agree. In the project layout the task root sits at `<base>/<project>/tasks/<task-id>/`, the implementation root is the shared project-level `implementation/`, and `clean-room-project.json` must exist at the project root. Treat target-repo `.clean-room/tasks/` as noncanonical unless explicitly configured; active artifacts belong in the external task root. Treat that scaffold as convenience output only; it is not an active `preflight-goal.json`, `init-config.json`, `task-manifest.json`, or `clean-run-context.json`.

## Required Contract

Record these decisions:

- End goal, success definition, destination kind, and existing destination handling.
- Target stack: language, runtime, framework, package manager, and test framework.
- License and dependency policy, including blocked licenses, blocked dependencies, and native dependency approval.
- Compatibility policy: public behavior/API exactness only. Private structure, comments, and internal names must not be mirrored.
- Feature policy: preserve, remove, add, and non-goals.
- Code hygiene policy: file line caps, max files per iteration, split strategy, exceptions, and forbidden patterns.
- Output policy: artifact base root, implementation root, assumed output directory, and write mode.
- Controller policy: attended or unattended, iteration cap, and whether unattended is allowed after preflight.
- Intent confirmation: `intent_confirmation` with explicit-user-answer sources for end goal, target stack, and controller mode, plus user-facing summaries of the goal and target stack.
- Open questions, with blocking questions clearly marked.

The artifact must use the canonical `preflight-goal.schema.json` shape. Required top-level keys are `goal_id`, `created_at`, `end_goal`, `target_stack`, `license_policy`, `dependency_policy`, `compatibility_policy`, `feature_policy`, `code_hygiene_policy`, `output_policy`, `controller_policy`, and `open_questions`. Completed preflight inputs and unattended contracts also require `intent_confirmation`.

Reject non-canonical or legacy-shaped preflight artifacts instead of treating them as complete. Do not accept invented fields such as `version`, `created`, `source`, `destination`, `exactness_policy`, `output_policy.artifact_base`, `output_policy.contaminated_root`, `output_policy.clean_root`, or `output_policy.quarantine_root` as substitutes for canonical fields. Report the missing or invalid canonical fields and stop for review.

## Mode Rules

Attended runs may continue with recorded `open_questions`, but each blocking question becomes a pause gate before the affected work starts.

Unattended runs require a complete `preflight-goal.json` with:

- `controller_policy.mode: "unattended"`
- `controller_policy.unattended_allowed_after_preflight: true`
- finite `controller_policy.max_iterations`
- `intent_confirmation` showing the end goal, target stack, and controller mode came from explicit user answers
- empty `open_questions`

Do not infer end goal, target language, runtime, framework, package manager, test framework, license, dependency policy, exactness policy, output directory, or feature add/remove policy from source code. If the user's end goal or target stack is unknown, leave blocking `open_questions`, keep unattended disabled, and do not write runner-ready `task-manifest.json` or `clean-run-context.json`.

## CLI Helper

Use `clean-room-skill init` or `npx clean-room-skill@latest init` to create bootstrap scaffolds before this step. Project layout is canonical: `~/Documents/CleanRoom/<project>/tasks/<task-id>/` holds per-task `contaminated/`, `clean/`, and `quarantine/`, while `~/Documents/CleanRoom/<project>/implementation/` is shared by every task in that project. Do not accept hand-created folders as a bootstrap substitute.

Use the preflight CLI (`clean-room-skill` if installed, or `npx clean-room-skill@latest` as fallback) only for template creation or validation/copying:

The safest path is `clean-room-skill preflight --template` for drafts and `clean-room-skill preflight --input` for completed contracts.

```bash
clean-room-skill preflight --template --output ~/Documents/CleanRoom/task-xxxxxxxx/contaminated/preflight-goal.json
clean-room-skill preflight --input ./preflight-goal.json --output ~/Documents/CleanRoom/task-xxxxxxxx/contaminated/preflight-goal.json
clean-room-skill preflight --template --bootstrap ~/Documents/CleanRoom/task-xxxxxxxx
clean-room-skill preflight --template --bootstrap ~/Documents/CleanRoom/<project>/tasks/task-xxxxxxxx
```

`--template` writes an attended draft with blocking open questions. It does not support unattended mode. Use `--input` for completed contracts. `--bootstrap` accepts either the generated task root or `clean-room-bootstrap.json`, writes to the generated contaminated artifact root after scaffold validation, and requires completed input contracts to match the bootstrap artifact and implementation roots.

## Handoff

Agent 0 must record `preflight_goal_ref`, `preflight_goal_sha256`, and the required `handoff_sequence` in `task-manifest.json`.

Clean roles receive only the clean-safe goal subset through `clean-run-context.json` `goal_contract` plus `code_hygiene_policy` and optional Agent 4 local commit policy. Do not send the full `preflight-goal.json` to Agent 1.5, Agent 2, Agent 3, Agent 4, or clean handoff packages.
