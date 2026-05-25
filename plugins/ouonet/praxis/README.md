<p align="center">
  <a href="https://ouonet.github.io/praxis/" target="_blank">
    <img src="https://raw.githubusercontent.com/ouonet/praxis/main/assets/logo.svg" alt="Praxis" width="260"/>
  </a>
</p>

<p align="center">
  <a href="https://ouonet.github.io/praxis/" target="_blank" style="text-decoration: none;">
    <strong>What, not how.</strong>
  </a>
</p>

---

**Praxis** is a discipline framework for AI coding agents. Tell your agent *what you need* and *what done looks like*—not *how to do it*. As AI gets smarter, this gap widens: the agent can apply domain expertise, handle edge cases, and adapt faster than step-by-step instructions allow.

Inspired by [Superpowers](https://github.com/obra/superpowers), rewritten to be significantly cheaper while keeping the core capabilities.

**📖 [Full documentation](https://ouonet.github.io/praxis/)**

## Quick Start

```bash
claude plugins marketplace add ouonet/praxis 
claude plugins install praxis@praxis
claude 'do a todo list app'
```

## How it works

At session start, a hook injects the `praxis:using-praxis` startup skill. It tells your agent:

1. Classify scope inline using the triage table embedded in `using-praxis` — no Skill call needed.
2. Load only the skills that scope needs. **Trivial tasks skip the waterfall entirely.**
3. Follow the loaded skill literally; don't freelance past `<gate>` markers.

## Skills

| Skill     | When                                        |
| --------- | ------------------------------------------- |
| discover  | problem space undefined — unknown what to build, for whom, or whether it's worth building |
| onboard   | existing project with no docs/tech-spec.md  |
| design    | scope ≥ standard, anything new             |
| plan      | after design                                |
| tdd       | implementing or fixing                      |
| debug     | something broken                            |
| review    | before merge / after subagent task          |
| worktree  | non-trivial or parallel work                |
| subagents | independent tasks, fan-out                  |
| ship      | merge / PR / cleanup                        |
| release   | version / tag / publish                     |

Skills range from ~100 to ~400 tokens each. Compare to Superpowers' 2,500–3,500 per skill.

## Token budget

|                              | Superpowers   | Praxis                        |
| ---------------------------- | ------------- | ----------------------------- |
| Bootstrap (every session)    | ~2,200        | ~450 (using-praxis + inline triage) |
| Per skill load               | ~2,500–3,500 | ~100–400                            |
| Trivial task                 | ~11,000       | ~450 (bootstrap only)               |
| Standard task (design→ship) | ~30–50k      | ~1,300 (bootstrap + 4 skills)       |
| Complex task (all skills)    | ~40–60k      | ~2,900 (all skills combined)  |

## Documentation Structure

Praxis enforces a strict documentation structure and keeps code and docs in sync at every step.

### Living Documentation

Your project must maintain:

- **`README.md`** — Project overview, what it is, who it's for, how to use it. Links to technical spec.
- **`docs/tech-spec.md`** — Main technical specification (declarations only, no narrative).
- **`docs/specs/*.md`** — Split-out details when the main spec grows too large.

Technical specs are **facts only**: contracts, data shapes, invariants, failure modes. No interpretation, no plans.

### Discovery Area

During exploration of vague or undefined goals, Praxis uses:

- **`docs/discovery/YYYY-MM-DD-<topic>.md`** — Discovery note: hypotheses, investigation plan, experiments, findings.
- **`spikes/YYYY-MM-DD-<topic>/`** — Throwaway code validating a hypothesis. Deleted when discovery ends.

Discovery notes are **never deleted** — they accumulate as a permanent record across sessions. When discovery concludes, it either hands off to `design` or produces a knowledge artifact (`docs/discovery/<topic>-spec.md`) directly.

### Staging Area

During active work, Praxis uses:

- **`docs/staging/specs/YYYY-MM-DD-<topic>.md`** — Working spec for the current change.
- **`docs/staging/plans/YYYY-MM-DD-<topic>.md`** — Executable milestone tasks.

At `ship`, the staging spec merges into living docs; staging files are deleted (Git keeps history).

### Code-Docs Sync

Praxis enforces synchronization at multiple checkpoints:

- **During `tdd`**: After each RED-GREEN-refactor cycle, sync docs before commit.
  - If staging spec exists → update it to match reality.
  - If no staging spec (small tasks) → update living docs directly.
- **At `ship` gate**: Staging spec must reflect actual code behavior.
- **At `review`**: Check that README/comments reflect actual behavior.

**The rule**: Code changes without doc updates fail review. Docs that don't match code block merge.

## Install

### Install from a branch

To try an unreleased branch before it merges:

**Claude Code**
```bash
claude plugins marketplace add ouonet/praxis#<branch>
claude plugins install praxis
```

**Codex** — set in `opencode.json`:
```json
{
  "plugin": ["praxis@git+https://github.com/ouonet/praxis.git#<branch>"]
}
```

Replace `<branch>` with the branch name, e.g. `feat/discover-skill`.

---

### Claude Code

```
claude plugins marketplace add ouonet/praxis
claude plugins install praxis
```

To update after new releases:

```
claude plugins update praxis
```

> Claude Code does not auto-update plugins. Run the update command manually after repo changes.

### Codex (CLI / app)

Praxis is distributed as a Codex marketplace. Register the marketplace from the CLI:

```bash
codex plugin marketplace add ouonet/praxis
```

Then open the plugin directory and install it from the Codex UI:

```
/plugins
```

Search for `praxis` and select **Install Plugin**.

If the marketplace was already added before an update, refresh it first:

```bash
codex plugin marketplace upgrade praxis-marketplace
```

### OpenCode

See [`.opencode/INSTALL.md`](.opencode/INSTALL.md).

### GitHub Copilot CLI

```
copilot plugin install ouonet/praxis
```

(Or symlink `.copilot-plugin/plugin.json` per Copilot's plugin convention.)

### VsCode Copilot

```
open customization of copilot -> Plugins -> Install Plugin From Source -> input  "ouonet/praxis"
```

### Manual / fallback

For harnesses without plugin support, add an instruction that reads `bootstrap.md` first.

## Verify it's working

Start a fresh session. Send: `let's build a react todo list`.

Expected: outputs `praxis: scope=standard, loading=design,plan,tdd,review` (no `Skill(praxis:triage)` call — triage is inline) and starts asking clarifying questions before touching code.

Send: `fix the typo "teh" in README`.

Expected: agent outputs `praxis: scope=trivial, loading=` and just fixes it. **No design doc, no plan, no TDD ceremony.**

## Scripts

### Vague goal

```
You: I want to build something that helps developers manage their workflow
Agent: triage -> vague -> discover
```

Discover asks one question per turn to surface hypotheses. Runs experiments (including spike code in `spikes/`). Ends when the direction is confirmed — either handing off to `design` or producing a knowledge artifact directly.

### Tiny fix

```
You: fix the typo "teh" in README
Agent: triage -> trivial -> edit -> done
```

### Standard feature

```
You: add OAuth login with GitHub
Agent: triage -> design -> plan -> tdd -> review -> ship
```

Design asks only needed questions, plan writes milestone tasks, ship updates living specs and CHANGELOG `Unreleased`.

### Parallel work

```
You: migrate the entire API from REST to tRPC
Agent: triage -> design -> plan -> worktree -> subagents -> review -> ship
```

Subagents expand milestones at dispatch time; the coordinator reviews and marks tasks complete.

### Onboard existing project

```
You: take over this project / add Praxis to this codebase
Agent: triage -> onboard
```

Onboard explores the codebase and produces `docs/tech-spec.md` — a factual record of stack, contracts, conventions, and invariants. No code changes, no plans. After confirmation, the normal `design → plan → tdd` flow resumes.

### Release

```
You: release 1.2.0
Agent: triage -> release
```

Release confirms the version, moves CHANGELOG `Unreleased`, then asks before commit, tag, push, or publish.

## Common Signals

| You ask                | Praxis does                        |
| ---------------------- | ---------------------------------- |
| I want to build X (vague) | vague → discover              |
| fix typo               | trivial                            |
| add small field        | small -> tdd                       |
| add feature            | standard -> design/plan/tdd/review |
| migrate module         | complex -> worktree/subagents      |
| failing behavior       | debug                              |
| take over this project | onboard                            |
| release 1.2.0          | release                            |

## Compared to Superpowers

Praxis is directly inspired by [Superpowers](https://github.com/obra/superpowers). The core idea is the same: inject structured discipline into an agent session via skill files.

| Superpowers skill                                                 | Praxis equivalent                          |
| ----------------------------------------------------------------- | ------------------------------------------ |
| `using-superpowers`                                             | `using-praxis` (triage inline)         |
| `brainstorming`                                                 | `design`                                 |
| `writing-plans`                                                 | `plan`                                   |
| `executing-plans`                                               | `tdd`                                    |
| `test-driven-development`                                       | `tdd`                                    |
| `systematic-debugging`                                          | `debug`                                  |
| `requesting-code-review` / `receiving-code-review`            | `review`                                 |
| `using-git-worktrees`                                           | `worktree`                               |
| `dispatching-parallel-agents` / `subagent-driven-development` | `subagents`                              |
| `finishing-a-development-branch`                                | `ship`                                   |
| `verification-before-completion`                                | gate markers in `tdd` / `ship`         |
| `writing-skills`                                                | — (not needed; skills are plain Markdown) |
| —                                                                | `discover` (no Superpowers equivalent)   |
| —                                                                | `onboard` (no Superpowers equivalent)    |
| —                                                                | `archive` (no Superpowers equivalent)    |
| —                                                                | `release` (no Superpowers equivalent)    |

**Philosophy difference:** Superpowers gives agents detailed recipes—prose specs, step-by-step plans, narrative reasoning. Praxis gives agents *declarations of intent*—decisions, contracts, validation gates. This works because:

- Agents get smarter; recipes become obsolete. Declarations stay relevant.
- Leaner artifacts = faster iteration and long-term maintainability.
- The agent brings domain knowledge; Praxis provides *what matters*, not *how to do it*.

**Token savings:** The skill files are smaller (avg ~230 vs ~1,760 tokens), and artifacts are too. Praxis `design` outputs a spec (decisions, contracts, invariants) with no narrative; `plan` outputs milestone stubs with one-line goals. At `ship`, working notes are archived and the spec merges into living docs—context stays lean across sessions.

**When to use Superpowers:** You want battle-tested, narrative-rich workflows and token cost isn't a constraint.

**When to use Praxis:** You want agents to think, not follow recipes. You want specs and plans that survive across sessions and scale with AI capability.

## Philosophy

- **Intent, not instruction.** Tell the agent what to achieve and what done looks like. Let it decide how to do it.
- **Pay for discipline only when it pays back.** Triage decides.
- **Skills are short.** If a rule needs 3,000 tokens to express, it's probably not a rule, it's a manual.
- **Cross-harness via env detection,** not per-harness skill copies.
- **No ceremony around the rules** — state each rule once, clearly.

## Layout

```
bootstrap.md           # manual / fallback entrypoint
skills/<name>/SKILL.md # skills (Claude Code native + file-read harnesses)
hooks/
  hooks.json           # hook registry
  run-hook.cmd         # Windows hook runner
  session-start        # session-start hook script
.claude/               # Claude Code settings
.claude-plugin/        # Claude Code plugin manifest
.codex-plugin/         # Codex plugin manifest
.copilot-plugin/       # Copilot CLI plugin manifest
.opencode/             # OpenCode config + install doc
```

## License

MIT.
