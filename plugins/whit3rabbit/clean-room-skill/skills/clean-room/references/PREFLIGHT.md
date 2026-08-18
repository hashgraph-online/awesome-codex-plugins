# Preflight Goal Contract

Preflight owns intent. Agent 0 owns orchestration. Later roles execute the recorded goal contract instead of deciding what the destination should become.

Preflight stops after a canonical `preflight-goal.json` is created or validated. Do not create behavior specs, handoff packages, skeleton manifests, implementation plans, coverage ledgers, or clean-run-context artifacts during preflight.

The safest path is `clean-room-skill preflight --template` for drafts and `clean-room-skill preflight --input` for completed contracts. Use generated CLI templates and schema validation instead of hand-writing canonical artifacts from scratch.

## Required Questions

Ask only enough to fill `preflight-goal.json`:

- End goal: clean reimplementation, behavior-compatible port, API-compatible clone, modernization, partial extraction, or spec/test generation only.
- Target stack: language, runtime, framework, package manager, and test framework.
- Intent confirmation: completed and unattended contracts must record that end goal, target stack, and controller mode came from explicit user answers.
- Exactness: public APIs, CLI behavior, config files, output formats, error codes, UI behavior, or behavior-only.
- Visual fallback: when no source code is available, confirm what authorized screenshots are meant to accomplish, the target user flow, screenshot coverage, target stack, UI exactness boundary, and whether visible words are public compatibility surface.
- Forbidden mirroring: internal names, private structure, comments, source file layout, private helper behavior, and dependencies.
- Feature policy: preserve, remove, add, and non-goals.
- Dependency policy: allow new dependencies, prefer standard library, allow/block dependencies, and native/system dependency approval.
- License policy: destination license, allowed dependency licenses, blocked licenses, and source license notes.
- Code hygiene: max lines per code/test file, max files per iteration, split strategy, exceptions, and forbidden patterns.
- Output policy: artifact base, implementation root, assumed output directory, and existing destination handling.
- Controller mode: attended, unattended with finite max iterations, or unattended only after review.

## Defaults

Record every default as an assumption. Do not default the end goal or target stack from source code. Source language, runtime, framework, package manager, and test framework describe the input, not the user's requested destination. If either the end goal or target stack is unknown, keep a blocking `open_questions` entry and do not mark an unattended contract complete. Good defaults:

- Artifact base: `~/Documents/CleanRoom/<project>/tasks/<task-id>/`.
- Implementation root: `~/Documents/CleanRoom/<project>/implementation/`.
- Single-task compatibility layout: task root `~/Documents/CleanRoom/<task-id>/` with implementation root `~/Documents/CleanRoom/<task-id>/implementation/`.
- Existing destination policy: `inspect-and-preserve`.
- Dependency policy: allow new dependencies, prefer standard library, require approval for native/system dependencies.
- Dependency licenses: allow MIT, Apache-2.0, BSD-2-Clause, and BSD-3-Clause; block GPL-3.0 and AGPL-3.0 unless the user explicitly approves otherwise.
- Code hygiene: 500 lines per code file, 800 lines per test file, 12 files per iteration, split by module boundary/public type/feature area.

## Exactness Boundary

Exactness is allowed only for observable public compatibility surfaces:

- public API names
- CLI flags
- serialized outputs
- documented protocol behavior
- public error codes
- config files
- UI behavior

Private structure, comments, internal names, source file layout, private helper behavior, dependency choices, and source-shaped pseudocode remain blocked clean-side material.

## Stage Ordering

The controller must enforce the legacy sequence for existing packages:

1. `preflight`
2. `source-destination-discovery`
3. `agent-0-decomposition`
4. `agent-1-analysis`
5. `agent-1-5-sanitization`
6. `clean-handoff`
7. `clean-planning`
8. `clean-implementation-qc`
9. `agent-0-coverage-verification`

New code-development packages may insert `clean-polish-review` between `clean-implementation-qc` and `agent-0-coverage-verification`. When configured, Agent 4 must pass final polish review before Agent 0 performs coverage verification.

Agent 1 cannot start until Agent 0 records the preflight hash, assigned unit, source scope, evidence policy, and neutral sanitizer brief template.

Agent 1.5 cannot start until Agent 1 writes draft behavior specs with evidence refs only and no direct source excerpts.

For visual fallback runs, Agent 1.5 also cannot receive `visual-index.json`, raw screenshots, visual paths, image hashes, copied visible words, exact palettes, or distinctive UI layout/iconography.

Agent 2 cannot start until Agent 1.5 writes a passed handoff package, approved behavior specs, leakage review status, and `clean-run-context.json`.

Agent 3 cannot start until Agent 2 writes `CLEAN_ROOM_CLEAN_ROOTS/implementation-plan.json` with relative paths, argv-array verification commands, target stack, and code hygiene policy from preflight.

Agent 4 cannot start until Agent 3 writes terminal `CLEAN_ROOM_CLEAN_ROOTS/implementation-report.json` and `CLEAN_ROOM_CLEAN_ROOTS/qc-report.json`. Agent 4 receives only clean artifacts, implementation roots, schema roots, approved public references, and role-session briefs.

When `context_management.enforcement` is `strict`, no role can start until Agent 0 writes a valid `role-session-brief.json` for that role, phase, unit, and spec slice. The brief must fit the recorded budgets and must not contain prior chat, copied artifact bodies, source paths, or contaminated ledgers.

## Recovery

`resume-cr` and `refocus` must stop when new-run artifacts lack `preflight_goal_ref`, `preflight_goal_sha256`, or a complete `handoff_sequence`. Report this as legacy or incomplete preflight state; do not infer intent from prior chat or source.

`start-over` must create a new preflight goal or explicitly reuse a reviewed goal contract before recreating active artifacts.
