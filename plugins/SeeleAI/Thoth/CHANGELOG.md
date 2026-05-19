# Changelog

## [Unreleased]

No pending changes.

## [0.2.2] - 2026-05-19

### Fixed
- Fixed README inline-code formatting in the locked planning authority table row and published it as a new plugin version so remote-only host updates refresh installed marketplace caches.

## [0.2.1] - 2026-05-19

### Fixed
- Fixed `thoth init --preview` so it writes only migration preview evidence and does not apply generated project authority files unless `--apply` is explicitly selected.
- Added plugin-wrapper dependency bootstrapping through a user-local runtime venv so marketplace installs can run without relying on globally installed Python packages.
- Broadened Codex micro-prompt runtime lookup to support both observed and shorter plugin cache layouts.

## [0.2.0] - 2026-05-14

### Added
- Published the first stable compact release for the current `.thoth/objects` runtime.
- Added README launch notes for durable runs, locked work items, reviewable verdicts, and Claude Code / Codex plugin parity.
- Strengthened generated `AGENTS.md` / `CLAUDE.md` project contracts with Think Before Coding, Simplicity First, Surgical Changes, and Goal-Driven Execution guidance.

### Changed
- Standardized current authority, runtime, and dashboard read models on `work_item`, `work_id`, `work_kind`, and `runnable`.
- Renamed dashboard public routes and API endpoints from task naming to work-item naming, including `/work-items` and `/api/work-items`.
- Updated publishable plugin metadata and generated host surfaces to version `0.2.0`.

### Breaking Changes
- Removed `task_id` from current public authority, dashboard output, runtime summaries, generated surfaces, and selftest samples.
- Replaced current `work_type=task|milestone` payload shape with `work_kind=execution|milestone`; runnable execution eligibility now depends on `runnable=true`.
- Removed `/tasks`, `/api/tasks`, `/api/tasks/{task_id}`, `/api/tasks/{task_id}/active-run`, and `/api/tasks/{task_id}/runs` from the dashboard public surface.
- Removed obsolete root plugin residue directories `skills/`, `contracts/`, and `hooks/hooks.json`; publishable plugin surfaces now live under the generated Claude/Codex plugin manifests, `commands/`, `plugins/thoth/skills/thoth/`, `bin/thoth`, `scripts/thoth-cli-entry.py`, and the `thoth/` runtime package.

## [0.1.4] - 2026-04-23

### Changed
- Upgraded host hook behavior so Claude and Codex hooks now inject advisory runtime context, append standardized hook events, and refresh active-run heartbeat without becoming runtime authority

### Fixed
- Restored explicit `thoth:*` public command names so installed plugin commands render as `/thoth:*` instead of bare command names

## [0.1.2] - 2026-04-23

### Changed
- Collapsed Codex delegation into `--executor codex` on the main public commands
- Moved internal behavioral contracts out of the public plugin `skills/` surface into `contracts/`
- Added internal `thoth-main` and `codex-worker` agents plus plugin `settings.json`
- Retired the earlier shape that exposed dedicated public Codex command variants plus a matching rescue agent; the supported replacement is the smaller `/thoth:*` surface together with `--executor codex` on `run`, `loop`, and `review`

### Fixed
- Removed internal Thoth helper modules and dedicated Codex variants from the public slash-command surface

## [0.1.1] - 2026-04-22

### Changed
- Migrated plugin commands to standard root-level `commands/` layout
- Added teaser figure asset and linked it from the README
- Rewrote README for public open-source plugin positioning

### Added
- Added `.claude-plugin/marketplace.json` for Claude Code marketplace distribution
- Added repository homepage and author metadata to the plugin manifest

### Fixed
- Updated `hooks/hooks.json` to match Claude Code plugin validation format

## [0.1.0] - 2026-04-19

### Added
- Initial plugin skeleton
- 7 skills: core, audit, exec, memory, counsel, codex, testing
- 11 commands + 3 codex variants
- Session lifecycle hooks (SessionStart, SessionEnd)
- Codex rescue subagent
