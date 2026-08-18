<div align="center">

# development-skills

**A disciplined engineering workflow for [Claude Code](https://docs.claude.com/en/docs/claude-code) and [Codex CLI](https://github.com/openai/codex).**

Plan before code · review every change · keep the *why* on disk — so context survives `/compact` and `/clear`.

<a href="https://github.com/reidemeister94/development-skills/releases"><img src="https://img.shields.io/github/v/release/reidemeister94/development-skills?style=flat-square&color=2563EB" alt="Release"/></a>
<a href="LICENSE"><img src="https://img.shields.io/github/license/reidemeister94/development-skills?style=flat-square" alt="License"/></a>

</div>

---

## Install

Same marketplace flow on both CLIs.

**Claude Code**

```text
/plugin marketplace add reidemeister94/development-skills
/plugin install development-skills@development-skills
```

**Codex CLI**

```bash
codex plugin marketplace add reidemeister94/development-skills
```

Then run `codex`, open `/plugins`, search `development-skills`, and install.

It activates on any coding task — no further configuration. The hooks (auto-format on edit, router injection at session start) run natively on Claude Code and Codex 0.131+. On Codex 0.128–0.130, enable them with `[features] plugin_hooks = true` in `~/.codex/config.toml`; otherwise run formatters manually (the commands live in [`hooks/auto-format`](hooks/auto-format)).

## Why

LLMs are great at writing code and terrible at remembering why they wrote it. Two sessions in, the requirements are gone, the rejected alternatives are gone, and the agent rebuilds context from the diff alone.

This plugin is language-agnostic: it ships a methodology, not language conventions. It pushes the reasoning to disk — into files that outlive the context window:

```
Code + Git    →  WHAT changed
Plan files    →  HOW it was built
Chronicles    →  WHY it happened
```

- **Plan files** (`docs/plans/`) — the single source of truth for a task: the situation, the agreed result, decisions and their reasons, a checklist, and a working record of standards, verification, and review. Clear the context and the agent reads this file to resume where it left off.
- **Chronicles** (`docs/chronicles/`) — the WHY: the request in the user's own words, business context, decisions, rejected alternatives, and discoveries made along the way.

Both are numbered like SQL migrations (`0001`, `0002`, …). Colliding numbers after a merge are renumbered by `resolve-merge`.

## How it works

Every task takes one of two paths, defined in [`shared/development-loop.md`](shared/development-loop.md). The agent states the chosen path and why before the first change.

**Direct path** — only when the result, the solution, and the proof are all clear, the change reverses easily, and no business or design choice remains. Inspect, change, verify, report.

**Full path** — everything else; any uncertainty about the path means full.

| Step | What happens |
|---|---|
| **1 · Decide** | Inspect first. State the problem, who it affects, the solved state, constraints, unknowns, and what would prove the answer wrong. `brainstorming` resolves a real choice between approaches. |
| **2 · Define the proof** | Agree on what could expose failure. `create-test` designs the regression proof for non-trivial behavior, KPIs, integrations, or probabilistic output. |
| **3 · Express** | Write the plan (`docs/plans/`) and start the chronicle (`docs/chronicles/`), then present result, checks, scope, approach, files, and risks. **The user approves before any code is written** — the original request alone does not authorize it. |
| **4 · Implement** | Small slices, running the nearest useful check after each. When a test can prove behavior, watch it fail before the fix and pass after. |
| **5 · Verify** | Fresh outcome checks and repository gates that could fail if the claim were false. Fix root causes; never weaken or skip a check. Report what was not checked. |
| **6 · Explain diff** | When the change teaches a business, architecture, lifecycle, trade-off, or failure-mode concept, `explain-diff` transfers the mental model. Skippable when nothing qualifies. |
| **7 · Review** | The `staff-reviewer` subagent reviews specification compliance, then code quality. Fix every blocking finding (CRITICAL/HIGH/MEDIUM), then finalize the plan and chronicle with `align-docs`. Commit only when asked. |

The session-start router ([`skills/using-development-skills/SKILL.md`](skills/using-development-skills/SKILL.md)) enforces the gates that keep this honest: read and apply the writing contract before the first text, discover and record the standards before the first change, state the path before mutating, hand off cleanly from native Plan mode, and invoke `explain-diff` through the real skill rather than imitating it.

## What's included

**16 skills**, auto-triggered by task or invoked with `/name`:

| Group | Skills |
|---|---|
| **Workflow** | `using-development-skills`, `brainstorming`, `create-test` |
| **Review & quality** | `staff-review`, `roast-my-code`, `simplify-stuff` |
| **Docs & release** | `align-docs`, `changelog`, `commit`, `handoff`, `resolve-merge` |
| **Research & evals** | `best-practices`, `explain-diff`, `eval-regression`, `ai-agent-bench`, `plugin-feedback` |

**One subagent** — [`staff-reviewer`](agents/staff-reviewer.md). Implementation and verification stay in the main thread: fewer handoffs, less state to reconstruct.

**Hooks** ([`hooks/`](hooks/)):

| Hook | When | What it does |
|---|---|---|
| `session-start` | session start, `/clear`, `/compact` | Injects the `using-development-skills` router. |
| `auto-format` | after an edit | Best-effort formatting for the edited file — ruff, biome/prettier, google-java-format, ktfmt, swift-format, and more. A convenience, not a language-convention claim. |
| `plan-approved` | leaving Plan mode | Marks the handoff back into the full path. |

## Acknowledgments

Inspired by [superpowers](https://github.com/obra/superpowers) by Jesse Vincent — spec-first brainstorming, subagent review, and bite-sized TDD plans. This plugin diverges with a two-path loop, persistent chronicles for decision rationale, a single review subagent, and a deliberately language-agnostic core.

## Contributing

Contributions welcome — new skills, sharper workflow steps, clearer docs, and bug reports with reproduction steps. Open an issue first, then see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
