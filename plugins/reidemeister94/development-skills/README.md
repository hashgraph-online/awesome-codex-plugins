# development-skills

A plugin for [Claude Code](https://docs.claude.com/en/docs/claude-code) and [Codex CLI](https://github.com/openai/codex) that adds a 4-phase development workflow, language-specific patterns for Python, Java, TypeScript, Swift, and frontend frameworks, and a `staff-reviewer` subagent that does a fresh-eyes code review on every change.

<a href="https://github.com/reidemeister94/development-skills/releases"><img src="https://img.shields.io/github/v/release/reidemeister94/development-skills?style=flat-square&color=blue" alt="Release"/></a>
<a href="LICENSE"><img src="https://img.shields.io/github/license/reidemeister94/development-skills?style=flat-square" alt="License"/></a>

## Installation

Same marketplace flow on both CLIs.

### Claude Code

```text
/plugin marketplace add reidemeister94/development-skills
/plugin install development-skills@development-skills
```

### Codex CLI

```bash
codex plugin marketplace add reidemeister94/development-skills
```

Then run `codex`, open `/plugins`, search `development-skills`, install.

Activates on any coding task. No further configuration needed.

For native hook execution on Codex (auto-format, SessionStart context inject), add to `~/.codex/config.toml`:

```toml
[features]
plugin_hooks = true
```

Without it, Codex skills + subagents still work; only the auto-format / SessionStart hooks need to be run manually (commands in [`AGENTS.md`](AGENTS.md)).

## Why it exists

LLMs are good at writing code and bad at remembering why they wrote it. Two sessions in, the original requirements are gone, the rejected alternatives are gone, and the agent rebuilds context from the diff. This plugin pushes that context to disk in two places that survive `/compact` and `/clear`:

- **Plan files** (`docs/plans/NNNN__YYYY-MM-DD__implementation_plan__slug.md`) — the single source of truth for a task. Accumulates across phases: workflow state, clarifications, HOW-level locks, task checklist, implementation log, verification results, review log. When the context window clears, the agent reads this file and picks up where it left off.
- **Chronicles** (`docs/chronicles/NNNN__YYYY-MM-DD__slug.md`) — the WHY. User requirements verbatim, business context, rejected alternatives, discoveries made during implementation.

```
Code + Git    →  WHAT changed
Plan files    →  HOW it was built
Chronicles    →  WHY it happened
```

Numbered like SQL migrations.

## Workflow

Triaged at session start:

- **`PASS_THROUGH`** — trivial single-file mechanical change (rename, format, typo). Skips the workflow.
- **`LIGHT`** — mechanical change with no design choice, no logic/business/architecture impact, no new patterns. Follows a 6-step inline flow (detect language → read patterns → sketch+gate → implement+verify → iron-rules walk → done) without plan file or staff-reviewer. File count is NOT the criterion — qualitative.
- **`FULL`** (default on uncertainty) — runs the four phases below in order. Each is a hard gate.

| Phase | What happens | Output |
|---|---|---|
| 1. Research + Plan | Reads existing research, fills gaps via an isolated research subagent only when needed, writes a plan with a 6-dimension HOW-level locks table (edge cases / data shapes / error semantics / contract boundaries / test scope / rollback). Asks the user to approve. | Plan file with `## Plan`, `### HOW-level locks`, user approval |
| 2. Chronicle | Initialises the chronicle file, or marks `NOT NEEDED` with a reason. | Chronicle file (or annotated WORKFLOW STATE) |
| 3. Implement + Verify | Main-thread TDD (RED → GREEN → REFACTOR). Anti-slop self-check during REFACTOR. 5-step verification gate (`IDENTIFY → RUN → READ → VERIFY → CLAIM`) before any positive claim. | Updated `## Task Checklist`, `## Implementation Log`, `## Verification Results` |
| 4. Review + Finalize | `staff-reviewer` subagent runs two-stage review (spec compliance → code quality), iterates until `APPROVED`. Chronicle finalised. Docs aligned. User decides whether to commit. | `## Review Log`, completed chronicle |

The rules that apply across phases live in [`shared/iron-rules.md`](shared/iron-rules.md) — 9 Core Pillars + 4 Process Rules (A · B · C · D, including spirit-beats-letter), referenced from every skill and phase rather than duplicated.

## What's included

**26 skills**

- **Workflow** — `using-development-skills`, `core-dev`, `brainstorming`, `debugging`, `chronicles`
- **Languages** — `python-dev`, `java-dev`, `typescript-dev`, `swift-dev`, `frontend-dev` (React / Next.js / Vite / Raycast auto-detection)
- **Testing** — `create-test`, `roast-my-code` (`--fix` optional), `eval-regression`, `ai-agent-bench`
- **Utilities** — `commit`, `distill`, `align-docs`, `resolve-merge`, `update-precommit`, `update-reqs`, `update-reqs-dev`, `best-practices`, `claude-to-agents`
- **User-invocable** — `context-transfer`, `produce-feedback`, `ingest-feedback`

**1 named subagent:** `staff-reviewer`. Implementation and verification run in the main thread per [`shared/phases/phase-3-implement-verify.md`](shared/phases/phase-3-implement-verify.md) — fewer context handoffs, less state to reconstruct.

**Auto-format on edit** (Claude Code only): ruff (Python), biome or prettier (JS/TS), google-java-format (Java), ktfmt (Kotlin), swift-format (Swift). On Codex run formatters manually — commands in [`AGENTS.md`](AGENTS.md).

## Design notes

A few choices that aren't obvious from the file listing:

- **HOW-level locks before any code.** Phase 1 forces a 6-row table filled or explicitly marked `N/A`. A blank cell means the model doesn't know yet — it must ask. This is the primary "zero ambiguity at implementation start" gate.
- **No positive claim without fresh evidence.** The 5-step verification gate blocks `should work`, `looks good`, and `done` unless the matching command was run in the current turn and its output read.
- **Lint as a blocking gate (JS/TS).** [`shared/lint-enforcement.md`](shared/lint-enforcement.md) detects the *union* of configured linters (biome + eslint + oxlint), not the first match. Any one failing = Phase 3 fails.
- **Package-manager detection is mandatory** before emitting any `install` / `run` / `exec` command. [`shared/package-manager.md`](shared/package-manager.md) handles `packageManager` field → lockfile priority → user prompt. The result is recorded in WORKFLOW STATE so it survives compaction.
- **Verbose output stays off the main thread.** Implementation reasoning lands in `## Implementation Log`. Full verification output lands in `## Verification Results` (or a temp file path); only the pass/fail summary surfaces in chat. Staff-reviewer reads the plan file directly from disk rather than from a forwarded summary.

For the longer write-up on templates, lifecycle, and how individual skills compose, see the [**in-depth guide**](docs/GUIDE.md).

## Acknowledgments

Inspired by [superpowers](https://github.com/obra/superpowers) by Jesse Vincent — spec-first brainstorming, subagent-per-task dispatch with two-stage review, bite-sized TDD plans, and git worktree isolation.

This plugin diverges in three places: language-specific patterns (5 languages with framework-level guidance), persistent chronicles for capturing decision rationale, and a canonicalised Iron Rules file referenced by every component.

## Contributing

Contributions welcome — especially new language skills (Rust, Go, Kotlin, Ruby, C#). See [CONTRIBUTING.md](CONTRIBUTING.md). Open an issue first. PRs need a passing `/eval-regression`.

## License

MIT
