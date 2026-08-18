# AIBoarding

**AIBoarding keeps `AGENTS.md` alive.**

AI coding agents join your repo like fresh engineers: they need the stack, the commands, the architecture, the guardrails, and the known failure modes before they touch code. AIBoarding generates, compresses, audits, and updates that guidance, so Claude, Codex, Copilot, Cursor, and OpenCode stop rediscovering your repo from scratch.

Think of it as Dependabot for AI-agent context: the onboarding files stay current as the code evolves, instead of rotting quietly until an agent trips over them.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Status: early](https://img.shields.io/badge/status-v0.5.0%20early-orange.svg)](./RELEASE-NOTES.md)

## What it does

- Creates a high-signal `AGENTS.md` from a repo crawl plus a guided interview.
- Keeps `CLAUDE.md` thin by importing `AGENTS.md` instead of duplicating content.
- Tracks drift in `.aiboarding/state.json` and nudges after relevant commits.
- Patches only the sections affected by recent changes, never the whole file.
- Compresses instructions while byte-preserving commands, paths, URLs, and code.
- Audits bloat, stale commands, contradictions, secrets, and the Codex 32 KiB truncation risk.

```text
/plugin marketplace add gustavo-meilus/aiboarding
/plugin install aiboarding@aiboarding
```

> **Status v0.5.0.** The full lifecycle is implemented: generation (`create-agent-onboarding`), drift triage (`update-agent-onboarding`), one-shot migration from the legacy layout (`migrate-aiboarding`), a verifiable compression engine (`compress-onboarding`), and a read-only auditor (`audit-agent-onboarding`), plus the surgical hook set with a full test harness. Live-runtime protocols (native loading, hook-event delivery) are documented in the [verification runbook](./docs/VERIFICATION.md) and not yet run against a live install (see [Roadmap](#roadmap)).

---

## The Idea

A new engineer joining a project gets onboarded: they read the docs, learn the stack, absorb the domain language, and get warned about the landmines. AI agents get none of that. They re-derive context from scratch every session, and they repeat the same mistakes. AIBoarding closes that gap with one compressed, high-signal `AGENTS.md` per repository, the open cross-agent standard read natively by Codex, Copilot, Cursor, and others, imported into Claude Code via a thin `CLAUDE.md` wrapper, and kept current by a managed lifecycle.

| Stage | Skill | What it does |
| :--- | :--- | :--- |
| **Create** | `create-agent-onboarding` | Hybrid background code-crawl + grilling interview producing a nine-section `AGENTS.md`, the `CLAUDE.md` wrapper, the state sidecar, and hooks, behind a blocking validation gate. |
| **Update** | `update-agent-onboarding` | Triages commits since the last sync; patches only drifted sections, or silently advances the state pointer on no-ops. |
| **Migrate** | `migrate-aiboarding` | One-shot move from the legacy `AIBOARDING.md` layout, preserving the onboarding investment. |
| **Compress** | `compress-onboarding` | Levels `off`/`lite`/`full`/`ultra`; byte-preserves code, commands, URLs, and paths (machine-verified); writes token receipts. |
| **Audit** | `audit-agent-onboarding` | Read-only linter: bloat, contradictions, stale commands, secrets, the Codex 32 KiB truncation cap; `--stats` shows compression receipts. |

## How AIBoarding fits Loop Engineering

A reliable AI coding loop needs durable context before it can act. Loop Engineering, the practice of designing the repeatable system around an agent (trigger, context, action, verification, retry, memory), depends on repo guidance that is accurate and current. AIBoarding manages that context layer.

| Loop ingredient | AIBoarding role |
| :--- | :--- |
| Goal / context | Captures repo purpose, stack, architecture, commands, guardrails |
| Tool use | Gives agents exact build, test, and run commands |
| Observation | Tracks commits since the last sync |
| Verification | Records required checks before completion |
| Retry / escalate | Defines known failure modes and ask-the-user conditions |
| Memory / trace | Stores drift state and compression receipts outside transient chat |
| Safety | Audits secrets, stale commands, contradictions, and context bloat |

AIBoarding is not the loop runner; it is the memory layer the loop depends on. See [docs/LOOP-ENGINEERING.md](./docs/LOOP-ENGINEERING.md) for the full picture. For the loop-runner side (spec, implement, isolated review, bounded repair), it pairs well with [superpipelines](https://github.com/gustavo-meilus/superpipelines).

## Architecture

Delivery is native: Claude Code loads `CLAUDE.md` (and its `@AGENTS.md` import) at session start and re-injects it after `/compact`; Codex and friends read `AGENTS.md` directly. Hooks exist only for the lifecycle behaviors native files cannot do:

| Layer | Mechanism | Purpose |
| :--- | :--- | :--- |
| Cross-agent onboarding | `AGENTS.md` | Canonical repo guidance for all coding agents |
| Claude loader | `CLAUDE.md` (`@AGENTS.md`) | Native load, `/compact` survival, Claude-only notes |
| Drift state | `.aiboarding/state.json` | Sync pointer + compression receipts, outside instruction files |
| Drift hook | `PostToolUse` + `if: Bash(git *)` | Nudge only after git-relevant activity |
| Sub-agent reminder | `SubagentStart` | Short pointer at `AGENTS.md` for spawned agents (never the body) |
| Diagnostics | `InstructionsLoaded` (`AIBOARDING_DEBUG=1`) | Prove which instruction files loaded |
| Fallback | `SessionStart` | Warn only when a file or the import line is missing |

Keeping the sync pointer in the state sidecar, never inside an instruction file, is what makes drift tracking loop-proof: advancing the pointer can't re-trigger the drift hook ([issue #1](https://github.com/gustavo-meilus/aiboarding/issues/1), fixed structurally in v0.3.0).

Hooks are committed into the target repo (`.aiboarding/hooks/` + `.claude/settings.json`), so every collaborator gets them without installing the plugin. All hooks run through a single **polyglot `run-hook.cmd`**, one file valid as both Windows CMD and bash (pattern adapted from [obra/superpowers](https://github.com/obra/superpowers)). If no bash is found on Windows, hooks no-op and the create skill warns once; native loading is unaffected.

## The `AGENTS.md` Document

Tool-agnostic, no frontmatter, nine H2 sections, target under 200 lines / 24 KiB (hard cap 32 KiB, since Codex silently truncates past its `project_doc_max_bytes` default):

```markdown
## Project Purpose            what it does and why
## Stack and Runtime          languages, frameworks, versions
## Build, Test, Run           exact commands; fast + full checks
## Architecture Map           directories, boundaries, data flow
## Domain Model               entities, workflows, invariants, vocabulary
## Agent Guardrails           what agents must NOT assume/refactor/delete
## Known Failure Modes        mistakes agents made or will likely make
## Verification Before Completion   commands to run before claiming done
## Escalation: Ask the User When    stop-and-ask cases
```

`CLAUDE.md` stays thin: the `@AGENTS.md` import plus a marker-fenced block of Claude-only workflow notes. Never duplicate content across the two, because imports expand into context at launch, so duplication doubles token cost.

## Quick Start

```text
# Claude Code
/plugin marketplace add gustavo-meilus/aiboarding
/plugin install aiboarding@aiboarding
```

Then generate the onboarding files and lifecycle in one pass (plugin skills are namespaced; the short names also resolve when unambiguous):

```text
/aiboarding:create-agent-onboarding   # interview + crawl -> AGENTS.md, CLAUDE.md, state, hooks
/aiboarding:update-agent-onboarding   # after commits: triage drift -> targeted patch or pointer advance
/aiboarding:audit-agent-onboarding    # lint the onboarding files; --stats for compression receipts
/aiboarding:compress-onboarding       # compress any instruction file, receipts included
```

Already using the legacy `AIBOARDING.md` layout? Run `/aiboarding:migrate-aiboarding`; it maps your existing content onto the new schema behind a single preview-first approval. The old skill names (`/create-aiboarding`, `/update-aiboarding`) still resolve as deprecated aliases.

Run the test suite (requires Git Bash on Windows):

```bash
bash tests/run.sh
```

Maintainers: run `claude plugin validate . --strict` before a release (see the [runbook](./docs/VERIFICATION.md)).

## Using with Codex, Copilot CLI, and other agents

The generated `AGENTS.md` needs no adapter: Codex, Copilot, Cursor, and other tools read it natively. The AIBoarding skills themselves are standard [SKILL.md](https://agentskills.io) (frontmatter kept to the portable `name` + `description` subset), so they also run outside Claude Code. Install them into a repo for Codex **and** Copilot CLI via the shared discovery path:

```bash
git clone --depth 1 https://github.com/gustavo-meilus/aiboarding /tmp/aiboarding
mkdir -p .agents/skills
cp -r /tmp/aiboarding/skills/* .agents/skills/
```

(Personal installs: `~/.codex/skills/` or `~/.agents/skills/`. Copilot CLI also reads `.github/skills/` and `.claude/skills/`.) On these runtimes the skills skip the Claude Code hook wiring and say so: generation, updating, compression, and auditing work everywhere; drift *nudging* is a Claude Code hook, so elsewhere you run `update-agent-onboarding` manually after meaningful commits.

## Repository Layout

```
aiboarding/
├── .claude-plugin/              # plugin + marketplace manifests
├── skills/
│   ├── create-agent-onboarding/ # 6-phase generation + install + validation gate
│   ├── update-agent-onboarding/ # drift triage + targeted-delta patch
│   ├── migrate-aiboarding/      # one-shot v1 -> v2 migration
│   ├── compress-onboarding/     # compression engine (levels, invariants, receipts)
│   ├── audit-agent-onboarding/  # read-only linter + --stats
│   ├── create-aiboarding/       # deprecated alias stub
│   └── update-aiboarding/       # deprecated alias stub
├── templates/
│   ├── hooks/                   # _lib · session-start · subagent-start ·
│   │                            # drift-check · instructions-loaded · run-hook.cmd
│   ├── tools/                   # inject-fenced · check-size-budget · check-preservation
│   ├── settings/hooks.json      # 4-event .claude/settings.json block
│   └── state/                   # default config.json · .aiboarding/.gitignore payload
├── tests/                       # dependency-free bash harness
│   ├── run.sh · lib/assert.sh
│   ├── fixtures/                # modern / partial / legacy / compression fixtures
│   ├── hooks/ · tools/ · plugin/
├── docs/
│   ├── LOOP-ENGINEERING.md      # where AIBoarding sits in an agent loop
│   ├── VERIFICATION.md          # live-runtime runbook (2a, 3a, 4a)
│   └── superpowers/             # design specs & implementation plans
├── .gitattributes               # pins LF for hook scripts
├── CHANGELOG.md · RELEASE-NOTES.md · LICENSE
```

## Roadmap

- **v0.6.0 (live verification)**: automate runbook protocols 3a/4a against a headless runtime; CI integration.
- **v1.0.0 (evidence)**: benchmark matrix (onboarding configurations × compression levels, with an honest naive-truncation control) published with receipt tables; formal deprecation of the legacy `AIBOARDING.md` mode (still supported today via the drift hook's legacy branch and `migrate-aiboarding`).

## Contributing

Contributions are managed via issues and PRs at [gustavo-meilus/aiboarding](https://github.com/gustavo-meilus/aiboarding). Keep hooks deterministic, small, and silent-by-default; keep reasoning in skills; every changed behavior ships with a test or a labeled manual protocol.

## License

MIT. See [LICENSE](./LICENSE).

---

## Star History

[![GitHub Stars](https://img.shields.io/github/stars/gustavo-meilus/aiboarding?style=social)](https://github.com/gustavo-meilus/aiboarding/stargazers)

[![Star History Chart](https://api.star-history.com/svg?repos=gustavo-meilus/aiboarding&type=Date)](https://star-history.com/#gustavo-meilus/aiboarding&Date)
