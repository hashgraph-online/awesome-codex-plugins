# Development skills

This repo IS the source of the `development-skills` plugin: a 3-tier workflow (PASS_THROUGH · LIGHT · FULL 4-phase) plus skills, hooks, and a single `staff-reviewer` subagent, distributed to Claude Code and Codex CLI.

0. **Don't pander to the user, always be critical when necessary**
1. **Maximize simplicity, minimize complexity.** use critical thinking to always maximize simplicity while keeping all the features, abstracting the complexity
2. **All signal, zero noise.** Everything must earn its place. If it doesn't add value, remove it.
3. **Zero regression policy in refactoring tasks** Verify with all appropriate test suites after every change.
4. **Document every discovery.** Write insights, useful and non-trivial information (chronicles, plans, rules).
5. **Comments explain why, not what.** Comment non-obvious business logic, flows, and workarounds only.
6. **Refactoring objective:** clear, descriptive, efficient, performant, reliable, robust, maintainable.
7. **Keep AGENTS.md aligned** AGENTS.md max 60-70 lines with only very specific and brief directives about absolutely non-trivial or domain project specific things + references to the additional details in `.agents/rules/<topic>.md`. Do not add section headings or any other decoration to the `AGENTS.md`, only a list of valuable brief directives/sentences.
8. **Single working language is English; MEMORY.md stays minimal.** All written artifacts (plans, chronicles, code comments, rules, MEMORY.md, AGENTS.md, SKILL.md, shared files) in English. MEMORY.md must not duplicate project docs — project facts → `AGENTS.md` / `.agents/rules/`; user-specific (env paths, personal tooling) → gitignored `.claude/CLAUDE.md` (Claude) or `~/.codex/AGENTS.md` / `AGENTS.override.md` (Codex).

- Canonical 9 Pillars + 4 Process Rules live in `shared/iron-rules.md`; never restate them in skills, AGENTS.md, README, or chronicles — reference by path.
- Canonical workflow tiers (LIGHT / FULL) live in `shared/workflow.md`; phase contracts in `shared/phases/`. A change to a phase file ripples to every FULL execution — edit deliberately.
- Versioning is automated via `make bump-version-{minor,major,patch}` (commitizen): `cz bump` atomically updates `[tool.commitizen] version` in `pyproject.toml`, `VERSION`, `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, and `.claude-plugin/marketplace.json`, then creates the annotated git tag `$version`. Never bump version files manually.
- Only one named subagent ships: `staff-reviewer`. Implementation and verification run in the main thread per `shared/phases/phase-3-implement-verify.md` — do not introduce extra subagents without explicit design discussion.
- Hooks in `hooks/` are Claude-Code-native; on Codex they require `[features] plugin_hooks = true` in `~/.codex/config.toml` (0.128+). Document the manual fallback whenever a hook is added.
- `evals/evals.json` is the regression suite — any skill behavior change that moves pass/fail outcomes MUST update the matching eval expectation in the same change.
- `pyproject.toml` exists for plugin-internal scripts (eval runners, lint helpers) — the plugin is markdown-first and not distributed as a PyPI package.
- Personal per-machine context: `.claude/CLAUDE.md` (Claude) or `~/.codex/AGENTS.md` (Codex). Both must stay gitignored; never commit either.

| Rule | Scope (`paths:`) | Topic |
|------|------------------|-------|
| `.agents/rules/skill-authoring.md` | `skills/**`, `agents/**` | SKILL.md / subagent frontmatter, references/ subdirs, what NOT to duplicate from `shared/` |
| `.agents/rules/shared-canonical.md` | `shared/**` | Canonical files inventory; iron-rules / workflow / phases / templates editing rules |
| `.agents/rules/plugin-packaging.md` | `.claude-plugin/**`, `.codex-plugin/**`, `.agents/plugins/**`, `evals/**`, `VERSION`, `CHANGELOG.md`, `pyproject.toml` | Version sync (4 files + pyproject), dual manifest, dual marketplace catalog, marketplace-only install, changelog format, eval suite |
| `.agents/rules/formatting-hooks.md` | `hooks/**` | Auto-format command table, hook authoring conventions, Codex parity |

Local machine instructions: Claude → `.claude/CLAUDE.md` (gitignored). Codex → `~/.codex/AGENTS.md` (user-global) — avoid in-repo `AGENTS.override.md` because Codex loads one file per directory and an override fully replaces this file rather than merging.
