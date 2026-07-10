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

It activates on any coding task — no further configuration. Hooks (auto-format, context injection) run natively on Claude Code and Codex 0.131+. On Codex 0.128–0.130, enable them with `[features] plugin_hooks = true` in `~/.codex/config.toml`; otherwise run formatters manually (see [`AGENTS.md`](AGENTS.md)).

## Why

LLMs are great at writing code and terrible at remembering why they wrote it. Two sessions in, the requirements are gone, the rejected alternatives are gone, and the agent rebuilds context from the diff alone.

This plugin pushes that context to disk — into files that outlive the context window:

```
Code + Git    →  WHAT changed
Plan files    →  HOW it was built
Chronicles    →  WHY it happened
```

- **Plan files** (`docs/plans/`) — the single source of truth for a task: state, clarifications, HOW-level locks, checklist, implementation log, verification, review. Clear the context and the agent reads this file to pick up where it left off.
- **Chronicles** (`docs/chronicles/`) — the WHY: requirements verbatim, business context, rejected alternatives, discoveries made along the way.

Both are numbered like SQL migrations.

## How it works

Every task is triaged at session start, then routed to the lightest workflow that fits:

- **`PASS_THROUGH`** — trivial, reversible, single-file (rename, typo, format). Runs directly.
- **`LIGHT`** — mechanical, no design choice. A 6-step inline flow, no plan file.
- **`FULL`** (default) — four gated phases, each a hard checkpoint:

| Phase | What happens |
|---|---|
| **1 · Research + Plan** | Gather context, write a plan with a 6-dimension *HOW-level locks* table (edge cases · data shapes · error semantics · contract boundaries · test scope · rollback). **The user approves before any code is written.** |
| **2 · Chronicle** | Capture the WHY, or mark it `NOT NEEDED` with a reason. |
| **3 · Implement + Verify** | Main-thread TDD (RED → GREEN → REFACTOR). No positive claim without fresh evidence: `IDENTIFY → RUN → READ → VERIFY → CLAIM`. |
| **4 · Review + Finalize** | The `staff-reviewer` subagent runs a two-stage review (spec compliance → code quality) until `APPROVED`. You decide whether to commit. |

The principles enforced across every phase live in [`shared/iron-rules.md`](shared/iron-rules.md) — 13 rules plus one meta-rule (spirit beats letter), referenced everywhere instead of duplicated.

## What's included

**24 skills**, activated automatically by task or invoked with `/name`:

- **Workflow** — `core-dev`, `brainstorming`, `debugging`, `create-test`
- **Languages** — `python-dev`, `typescript-dev`, `java-dev`, `swift-dev`, `frontend-dev`
- **Review & quality** — `staff-review`, `roast-my-code`, `eval-regression`, `ai-agent-bench`
- **Utilities** — `commit`, `changelog`, `distill`, `align-docs`, `resolve-merge`, `best-practices`, and more

**One subagent** — `staff-reviewer`. Implementation and verification stay in the main thread ([why](shared/phases/phase-3-implement-verify.md)): fewer handoffs, less state to reconstruct.

**Auto-format on edit** (Claude Code) — ruff, biome/prettier, google-java-format, ktfmt, swift-format. On Codex, run formatters manually (commands in [`AGENTS.md`](AGENTS.md)).

## Acknowledgments

Inspired by [superpowers](https://github.com/obra/superpowers) by Jesse Vincent — spec-first brainstorming, subagent review, and bite-sized TDD plans. This plugin diverges with language-specific patterns, persistent chronicles for decision rationale, and a single canonical Iron Rules file referenced by every component.

## Contributing

Contributions welcome — especially new language skills (Rust, Go, Kotlin, Ruby, C#). Open an issue first, then see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
