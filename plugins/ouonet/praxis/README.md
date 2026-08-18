<p align="center">
  <a href="https://ouonet.github.io/praxis/" target="_blank">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/ouonet/praxis/main/assets/logo-dark.svg"/>
      <img src="https://raw.githubusercontent.com/ouonet/praxis/main/assets/logo.svg" alt="Praxis" width="260"/>
    </picture>
  </a>
</p>

<p align="center">
  <a href="https://ouonet.github.io/praxis/" target="_blank" style="text-decoration: none;">
    <strong>What, not how.</strong>
  </a>
</p>

---

**Praxis** is a discipline framework for AI coding agents to build complex, multi-module, multi-repository projects through structured workflows—delivering **high quality**, **high efficiency**, and **extreme token savings**.

Tell your agent *what you need* and *what done looks like*—not *how to do it*. As AI gets smarter, declarations of intent, trigger-based spec review gates, 3D quality standards, and multi-module topology ensure robust, enterprise-grade execution without context bloat.

### Core Value Pillars

- **Workflow-Driven**: Inline triage routes tasks to precise skill chains (`design` → `plan` → `tdd` → `review` → `ship`).
- **High Quality**: Parallel spec review gates and 3D quality standards (mechanical checks, convention adherence, design cohesion, doc-coverage) guarantee production readiness.
- **High Efficiency & Token-Lean**: Inline triage loads only required skills (~150 to ~1,180 tokens per skill; ~3,600 tokens for a standard feature cycle). No ceremony for trivial edits.
- **Multi-Module & Multi-Repo**: Coordinate complex changes across multiple repositories seamlessly via designated coordinator specs and change-set manifests.

**[Full documentation](https://ouonet.github.io/praxis/)**

> 💡 **Looking for the single-module version (v2.4.0)?** If you prefer the legacy single-module setup of Praxis without multi-module topology or spec review gates, checkout or install from the [`single-module`](https://github.com/ouonet/praxis/tree/single-module) branch.

## Quick Start

Install Praxis across your agent harnesses in one command with the **Praxis CLI**:

```bash
# Universal install for all detected AI agent CLIs on your machine
npx @ouonet/praxis install --host all

# Or install for a specific agent host
npx @ouonet/praxis install --host claude
npx @ouonet/praxis install --host codex
npx @ouonet/praxis install --host opencode
```

Then prompt your agent:

```bash
claude 'do a todo list app'
# or
pi 'do a todo list app'
```

## How it works

At session start, a hook injects the `praxis:using-praxis` startup skill. It tells your agent:

1. Classify scope inline using the triage table embedded in `using-praxis` — no Skill call needed.
2. Load only the skills that scope needs. **Trivial tasks skip the waterfall entirely.**
3. Follow the loaded skill literally; don't freelance past `<gate>` markers.

Multi-module is a **topology**, declared alongside scope: when one change spans multiple modules or repositories, the agent adds `topology=multi-module` to the announcement and every loaded skill follows the multi-module protocol. See [Multi-module work](#multi-module-work) below.

## Skills

| Skill | Description | Tokens |
| ----- | ----------- | ------ |
| [onboard](skills/onboard/SKILL.md) | existing project with no docs/tech-spec.md | ~450 |
| [design](skills/design/SKILL.md) | scope ≥ standard, anything new; handles vague goals & trigger-based spec reviewers | ~1,180 |
| [plan](skills/plan/SKILL.md) | after design approval; milestone tasks | ~740 |
| [tdd](skills/tdd/SKILL.md) | implementing or fixing; 3D quality refactor gate | ~590 |
| [debug](skills/debug/SKILL.md) | something broken; root cause isolation | ~160 |
| [review](skills/review/SKILL.md) | before merge / after subagent task; checks standards & doc-coverage | ~420 |
| [worktree](skills/worktree/SKILL.md) | non-trivial or parallel work in Git worktrees | ~320 |
| [subagents](skills/subagents/SKILL.md) | independent tasks, fan-out; includes ROLE charters and MODEL tiers | ~1,030 |
| [ship](skills/ship/SKILL.md) | merge / PR / cleanup | ~430 |
| [archive](skills/archive/SKILL.md) | merge spec into living docs, delete staging files | ~730 |
| [release](skills/release/SKILL.md) | version / tag / publish | ~230 |

Shared protocols & reference standards:
- [Quality Standard](skills/references/quality.md) (~430 tokens): mechanical checks, convention adherence, design assessment, and doc-coverage rules.
- [Spec Reviewers](skills/references/reviewers.md) (~1,640 tokens): trigger table and charters for parallel spec review subagents.
- [Multi-Module Protocol](skills/references/multi-module.md) (~870 tokens): topology specification for cross-repository/module changes.

## Token budget

Praxis minimizes prompt overhead by executing triage inline at session start and loading skills only when their scope is required:

| Task Scope | Loaded Skills | Approximate Token Budget |
| ---------- | ------------- | ------------------------ |
| Bootstrap (session start) | `using-praxis` (inline triage) | ~680 |
| Trivial task | None (bootstrap only) | ~680 |
| Small task | `tdd` | ~1,270 |
| Standard task | `design` + `plan` + `tdd` + `review` | ~3,600 |
| Complex task | `design` + `plan` + `worktree` + `subagents` + `review` + `ship` | ~4,800 |

## Model tiers

When dispatching subagents (`subagents` skill) or design reviewers (`design` review gate), Praxis uses three capability tiers instead of hardcoded model IDs:

| Tier | Use when | Examples |
|------|----------|----------|
| `fast` | Mechanical edits, simple checks | rename a constant, pattern-match review |
| `balanced` | Standard implementation, single-file work | add a function, write routine tests |
| `strongest` | Complex reasoning, safety review | implement a protocol, review crash-recovery |

Resolution: `.praxis/model-tiers.yaml` in project root or user home maps each tier to a concrete model ID. No config file → all subagents use the harness default. Template: [`model-tiers.example.yaml`](model-tiers.example.yaml).

## Multi-module work

> **Availability:** Multi-module topology is supported in Praxis v4.0+ as an **experimental coordination protocol** (declaration blocks, revision sets, non-atomic cross-repo commits). See `skills/references/multi-module.md`.

When one change spans multiple modules or repositories, Praxis runs in **multi-module topology**. The agent declares it at triage and carries it on every turn:

```
praxis: scope=complex, topology=multi-module, loading=design,plan,worktree,subagents,review,ship
```

(`topology=multi-module` is omitted on ordinary single-module turns.)

**Coordinator.** You designate one *existing* repository as the coordinator - the agent won't infer this. It owns the cross-module spec/plan and the change manifest.

**Mode marker.** The coordinator spec (created at `design`) and workspace plan (created at `plan`) each open with a declaration block. This on-disk declaration is what keeps the agent in multi-module mode across a long change - it reads the declaration to re-establish mode instead of relying on session memory:

```
topology: multi-module
change-set: <topic-id>
coordinator: <repo path>
repos: <repo paths>
```

The workspace plan adds module plan paths and the integration task. Each module also gets its own spec and plan in its owning repository, referencing shared contracts defined once in the coordinator - never duplicated.

**Scope unchanged.** `topology` doesn't change scope — the skill chain follows scope alone. Multi-module adds execution mechanics (declaration + commit protocol), not process weight.

**Lifecycle.** `design` (coordinator + per-module specs) → `plan` (workspace + per-module plans) → `tdd`/`subagents` per module → integrate against the coordinator's acceptance → commit in dependency order, coordinator last, recording each SHA as the revision set.

**Safety.** Each repo is inspected before editing - a missing repo, red baseline, or unrelated dirty change blocks the change. Praxis never auto-clones, resets, rebases, or discards. Put the change-set ID in branch names and commit subjects, e.g. `[praxis:checkout-v2]`. Cross-repo commits aren't atomic; the recorded revision set is the reproducibility boundary.

Full protocol: [`skills/references/multi-module.md`](skills/references/multi-module.md) (experimental).

## Documentation Structure

Praxis enforces a strict documentation structure and keeps code and docs in sync at every step.

### Living Documentation

**Living documentation** reflects current active ground truth with **zero history, maximum truth density, and instant scannability**:
- **The Living Doc Razor**: Past rationale belongs in `docs/decisions/` or `CHANGELOG.md`; `docs/tech-spec.md` holds exclusively active ground truth.

Structure:
- **`README.md`** — for users: what it is, who for, how to use it
- **`docs/tech-spec.md`** — for developers/agents: current system backbone (≤300 lines, [format](skills/archive/SKILL.md#tech-spec-format))
- **`docs/specs/*.md`** — modular subsystem details split out when bulky (>15 lines); referenced by path
- **`docs/ROADMAP.md`** — direction and milestones (exists when project has ≥3 milestones or long-term direction)

`docs/tech-spec.md` uses a structured declaration format:

```
purpose / user / use-case / architecture / stack / entry /
contract / flow / invariant / constraint / convention / milestone
```

Atomic declarations only (≤25 words per sentence; structured lists/tables). Bulky details (schemas, state machines, deep algorithms) live in `docs/specs/<topic>.md` with a one-line summary in `tech-spec.md`.

**Project artifacts** — records and conventions. Append-only or static.

- **`CHANGELOG.md`** — version history, maintained by `ship`
- **`docs/decisions/`** — architectural decision log, append-only

### Staging Area

During active work, Praxis uses:

- **`docs/staging/specs/YYYY-MM-DD-<topic>.md`** — Working spec for the current change.
- **`docs/staging/plans/YYYY-MM-DD-<topic>.md`** — Executable milestone tasks.

At `ship`, the staging spec merges into living docs; staging files are deleted (Git keeps history).

### Code-Docs Sync

Praxis enforces synchronization at multiple checkpoints:

- **During [`tdd`](skills/tdd/SKILL.md)**: After each RED-GREEN-refactor cycle, sync docs before commit.
  - If staging spec exists → update it to match reality.
  - If no staging spec (small tasks) → update living docs directly.
- **At [`ship`](skills/ship/SKILL.md) gate**: Staging spec must reflect actual code behavior.
- **At [`review`](skills/review/SKILL.md)**: Check that README/comments reflect actual behavior.

**Quality and doc-coverage** are verified: `tdd` runs lint/format/typecheck + checks against `convention`; `review`/`ship` verify `contract` covers the full surface, env/errors documented, README commands runnable. See [`skills/references/quality.md`](skills/references/quality.md).

**The rule**: Code changes without doc updates fail review. Docs that don't match code block merge.

## Install

### Praxis CLI (Recommended)

Praxis provides a unified multi-host CLI tool to install, inspect, update, and remove Praxis configurations across any supported AI agent harness:

```bash
# 1. Universal Install: auto-detects installed agent CLIs and configures them all
npx @ouonet/praxis install --host all

# 2. Host-Specific Install: configure a specific agent in project, local, or user scope
npx @ouonet/praxis install --host claude --scope user
npx @ouonet/praxis install --host codex --scope project
npx @ouonet/praxis install --host opencode --scope project
npx @ouonet/praxis install --host antigravity
npx @ouonet/praxis install --host copilot
npx @ouonet/praxis install --host pi
npx @ouonet/praxis install --host omp
npx @ouonet/praxis install --host qoder
npx @ouonet/praxis install --host agents  # generic .agents directory

# 3. Status Check: inspect installation state across all agent platforms
npx @ouonet/praxis status

# 4. Update: upgrade Praxis to latest version
npx @ouonet/praxis update --host all

# 5. Uninstall
npx @ouonet/praxis uninstall --host codex --scope project
```

#### Scopes Definition

| Scope | Description | Typical Use Case |
| ----- | ----------- | ---------------- |
| `project` | **Project scope (Git-tracked)**: Configures project manifests (`opencode.json`, `.agents/`, `package.json`, etc.) so that Praxis configurations are committed to version control and shared across all team members cloning the repo. (Default inside a repository). | Team repository shared discipline |
| `local` | **Local scope**: Installs directly to local workspace directory (`.claude/plugins/`, `.codex/plugins/`, `.opencode/`, `.pi/skills/`, `.omp/skills/`, etc.) without modifying shared repo manifests. | Developer-local workspace testing without committing |
| `user` (or `global`) | **User scope**: Installs globally in the user's home directory (`~/.claude/`, `~/.codex/`, `~/.gemini/config/`, `~/.config/opencode/`, `~/.pi/`, `~/.omp/`, `~/.agents/`). (Default when run in home directory). | Global availability across all local projects |

#### CLI Options & Flags

| Flag | Description | Default |
| ---- | ----------- | ------- |
| `--host, -H <name>` | Target agent: `claude`, `codex`, `opencode`, `copilot`, `antigravity` (`agy`), `pi`, `omp`, `qoder`, `agents`, `all` | `all` |
| `--scope, -s <scope>` | Target installation scope: `project`, `local`, or `user` / `global` | `project` (in repo) / `user` (in home) |
| `--ref, -r <ref>` | Git branch, tag, or commit to install/pin (e.g. `--ref single-module`) | latest `main` |
| `--dry-run` | Preview actions and file paths without writing files or running commands | `false` |
| `--force, -f` | Overwrite existing configurations or files | `false` |
| `--method, -m <mode>` | Installation method: `auto`, `native`, `link`, `copy` | `auto` |

---

### Host-Specific Details & Native Install Alternatives

If you prefer native package managers or manual configuration over the CLI installer:

#### Claude Code

```bash
# Using Praxis CLI (Recommended)
npx @ouonet/praxis install --host claude

# Native marketplace install
claude plugins marketplace add ouonet/praxis
claude plugins install praxis
```

To update after new releases:
```bash
claude plugins update praxis
```

> Claude Code does not auto-update plugins. Run the update command manually after repo changes.

#### Codex (CLI / app)

```bash
# Using Praxis CLI (Recommended)
npx @ouonet/praxis install --host codex

# Native marketplace install
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

#### OpenCode

```bash
# Using Praxis CLI (Recommended)
npx @ouonet/praxis install --host opencode --scope project
```

See [`.opencode/INSTALL.md`](.opencode/INSTALL.md) for manual plugin configuration details.

#### GitHub Copilot CLI

```bash
# Using Praxis CLI (Recommended)
npx @ouonet/praxis install --host copilot

# Native plugin install
copilot plugin install ouonet/praxis
```

(Or symlink `.copilot-plugin/plugin.json` per Copilot's plugin convention.)

#### VsCode Copilot

```
open customization of copilot -> Plugins -> Install Plugin From Source -> input  "ouonet/praxis"
```

#### Antigravity CLI / AGY

```bash
# Using Praxis CLI (Recommended)
npx @ouonet/praxis install --host antigravity

# Native plugin install
agy plugin install https://github.com/ouonet/praxis
```

Antigravity imports Praxis through the Gemini-compatible plugin path, including the session-start hook and progressive skill disclosure in `~/.gemini/config/plugins/praxis` or project-level `.agents/`.

#### pi CLI

```bash
# Using Praxis CLI (Recommended)
npx @ouonet/praxis install --host pi

# Native pi package install
pi install git:github.com/ouonet/praxis
```

Praxis is distributed as a native pi package — pi auto-discovers skills from the `package.json` manifest. The `using-praxis` bootstrap is injected at session start automatically.

**Install to project scope** (`.pi/settings.json` or `package.json`, shared with team):
```bash
pi install -l git:github.com/ouonet/praxis
```

**Update**:
```bash
pi update git:github.com/ouonet/praxis      # update one package
pi update --extensions                       # update all packages
pi update --all                              # update pi + packages
```

**Uninstall**:
```bash
pi remove git:github.com/ouonet/praxis
```

#### Oh My Pi (omp)

```bash
# Using Praxis CLI (Recommended)
npx @ouonet/praxis install --host omp

# Native omp plugin install (user scope)
omp plugin install https://github.com/ouonet/praxis

# Native omp plugin install (project scope)
omp plugin install https://github.com/ouonet/praxis --scope=project
```

#### Qoder CLI CN

```bash
# Using Praxis CLI (Recommended)
npx @ouonet/praxis install --host qoder

# Manual discovery
git clone https://github.com/ouonet/praxis.git ~/.qoder-cn/praxis
ln -s ~/.qoder-cn/praxis/skills ./skills
```

Or install as an SDK plugin by pointing to the `.qoder-plugin/` manifest in your project config.

The `using-praxis` skill is auto-discovered and triggered at session start by its description.

#### Generic Agent (`.agents`)

```bash
# Using Praxis CLI (Recommended)
npx @ouonet/praxis install --host agents
```

Installs `.agents/skills` and `.agents/hooks` into your workspace for generic agent harnesses (Cursor, Windsurf, Claude Desktop, Antigravity IDE, etc.).

#### Manual / fallback

For harnesses without plugin support, add an instruction that reads `skills/using-praxis/SKILL.md` first.

---

### Install from a branch

To pin or test a specific git branch or tag, pass `--ref <branch>` to `praxis install`, or append `#<branch>` / `@<branch>` to native install URLs:

```bash
npx @ouonet/praxis install --host claude --ref single-module
```

> **Single-module (v2.4.0 legacy):** Append `#single-module` or `@single-module` to install from the legacy single-module branch (e.g. `pi install git:github.com/ouonet/praxis@single-module`).


## Verify it's working

Start a fresh session. Send: `let's build a react todo list`.

Expected: outputs `praxis: scope=standard, loading=design,plan,tdd,review` (no `Skill(praxis:triage)` call — triage is inline) and starts asking clarifying questions before touching code.

Send: `fix the typo "teh" in README`.

Expected: agent outputs `praxis: scope=trivial, loading=` and just fixes it. **No design doc, no plan, no TDD ceremony.**

## Examples

### Vague goal

```
You: I want to build something that helps developers manage their workflow
Agent: triage → vague → design
```

Design asks one clarifying question per turn until the problem is concrete enough to spec. If exploration produces a knowledge artifact (protocol spec, RE findings), it goes to `docs/decisions/` via `archive`.

### Tiny fix

```
You: fix the typo "teh" in README
Agent: triage → trivial → edit → done
```

### Standard feature

```
You: add OAuth login with GitHub
Agent: triage → design → plan → tdd → review → ship
```

Design investigates facts and asks only the current decision frontier in dependency order; plan writes milestone tasks; ship updates living specs and CHANGELOG `Unreleased`.

### Parallel work

```
You: migrate the entire API from REST to tRPC
Agent: triage → design → plan → worktree → subagents → review → ship
```

Subagents expand milestones at dispatch time; the coordinator reviews and marks tasks complete.

### Multi-module change

```
You: add a shared checkout flow across the api and web repos
Agent: triage → topology=multi-module → design (asks you to designate coordinator) → plan → tdd/subagents per module → integrate → ship
```

You designate one existing repo as coordinator; it holds the shared contract and integration check. Each module keeps its own spec/plan in its owning repo. At ship, non-coordinator repos commit in dependency order and the coordinator commits last, all sharing the change-set ID; their SHAs form the revision set.

### Onboard existing project

```
You: take over this project / add Praxis to this codebase
Agent: triage → onboard
```

Onboard explores the codebase and produces `docs/tech-spec.md` — a factual record of stack, contracts, conventions, and invariants. No code changes, no plans. After confirmation, the normal `design → plan → tdd` flow resumes.

### Release

```
You: release 1.2.0
Agent: triage → release
```

Release confirms the version, moves CHANGELOG `Unreleased`, then asks before commit, tag, push, or publish.

## Common Signals

| You ask                | Praxis does                        |
| ---------------------- | ---------------------------------- |
| I want to build X (vague) | vague → design (clarifies first) |
| fix typo               | trivial                            |
| add small field        | small → tdd                       |
| add feature            | standard → design/plan/tdd/review |
| migrate module         | complex → worktree/subagents      |
| change spans repos/modules | topology=multi-module (coordinator) |
| failing behavior       | debug                              |
| take over this project | onboard                            |
| release 1.2.0          | release                            |

## Philosophy

- **Intent, not instruction.** Tell the agent what to achieve and what done looks like. Let it decide how to do it.
- **Pay for discipline only when it pays back.** Triage decides.
- **Skills are short.** If a rule needs 3,000 tokens to express, it's probably not a rule, it's a manual.
- **Cross-harness via env detection,** not per-harness skill copies.
- **No ceremony around the rules** — state each rule once, clearly.

## Layout

```
bin/
  praxis.js            # Praxis CLI binary entrypoint (npx @ouonet/praxis)
src/cli/
  index.js             # CLI command runner & argument parser
  hosts.js             # Multi-host registry & target resolution
  installer.js         # Host installer, updater, and status checker
skills/<name>/SKILL.md # skills (using-praxis is the entrypoint; manual/fallback reads it directly)
skills/references/     # shared protocols (multi-module, quality, reviewers)
model-tiers.example.yaml # template for .praxis/model-tiers.yaml
hooks/
  hooks.json           # hook registry
  run-hook.cmd         # Windows hook runner
  session-start        # session-start hook script
package.json           # npm package & CLI definition + pi package manifest
.claude/               # Claude Code settings
.claude-plugin/        # Claude Code plugin manifest
.codex-plugin/         # Codex plugin manifest
.copilot-plugin/       # Copilot CLI plugin manifest
.qoder-plugin/         # Qoder CLI CN plugin manifest
.opencode/             # OpenCode config + plugin
gemini-extension.json  # Gemini CLI extension manifest
```

## License

MIT.
