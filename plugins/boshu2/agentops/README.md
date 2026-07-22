# AgentOps

AgentOps is the operating loop a coding agent follows: one intent, one bounded
build, one fresh judge, one durable verdict. It also ships skills to orchestrate
multi-agent systems. For contested calls, opt into
[`council`](skills/council/SKILL.md) (independent judges) or
[`idea-genie`](skills/idea-genie/SKILL.md) duel mode (sealed perspectives
before Plan).

```text
RPI -> Plan -> Implement -> fresh Validate -> durable verdict -> report and stop
```

## Quickstart

```bash
npx skills@latest add boshu2/agentops --all -g
```

One command, every coding agent — `npx skills` installs the corpus into all
your agents at once. The loop runs as skills **inside your coding agent**
(Claude Code, Codex, Cursor, …): type `/rpi` — or ask for `plan`,
`implement`, `validate`, `learn` by name — in that agent's chat. No other
runtime is required.

## Plugins (Claude Code / Codex)

Prefer a managed bundle that updates with the release:

```bash
# Claude Code
claude plugin marketplace add boshu2/agentops
claude plugin install agentops@agentops-marketplace

# Codex
codex plugin marketplace add boshu2/agentops
codex plugin add agentops@agentops-marketplace
```

Three install paths:

- **npx / [skills.sh](https://skills.sh)** — universal; copies skills you can edit.
- **Plugins** — a read-only bundle that stays current with the repo.
- **Checkout + `ao skills link`** — source-tracked symlinks for contributors
  (see [Install and day-2 operations](docs/install-day2-ops.md)).

## Admission-control hooks (on by default)

AgentOps ships a PreToolUse **policy dispatcher** — deterministic guards that
block a small set of known-destructive commands (staging the private bead
ledger, hand-editing the hash-chained provenance ledger, overwriting installed
skill copies) and route you to the correct tool instead. Silent on every clean
call; every block is one line.

- **Claude Code plugin installs:** active automatically — nothing to run.
- **npx / skills.sh copies:** run `~/.claude/skills/cc-hooks/scripts/install-hooks.sh` once.
- **git clone / brew:** run `scripts/install-policy-dispatch.sh` once.

Disable anytime (`/plugin disable agentops`, or remove the two PreToolUse
matchers from settings). Policy list and design:
`skills/cc-hooks/SKILL.md`.

Remove with your runtime's plugin uninstall, or delete the linked skill
directories.

## Intent lives in a bead

[Beads](https://github.com/steveyegge/beads) is the preferred tracker
(optional — `brew install beads`). Plan
writes [BDD](https://cucumber.io/docs/bdd/) acceptance and DDD [ubiquitous
language](https://martinfowler.com/bliki/UbiquitousLanguage.html) into the bead;
Implement builds against it; Validate judges a hashed snapshot under
`.agents/ao/intents/sha256/`. No beads? Plan shapes the caller's issue or chat
text and the runtime snapshots those bytes the same way.

`validate` must run in a fresh context (not the author session). Same model or
a different one — both are supported.

## Multi-agent systems

The default loop is one agent, one writer. When you need a fleet,
[`swarm`](skills/swarm/SKILL.md), [`agent-native`](skills/agent-native/SKILL.md),
[`ntm`](skills/ntm/SKILL.md), and [`using-gc`](skills/using-gc/SKILL.md)
orchestrate multi-agent work. They dispatch; they do not own the verdict.

AgentOps already borrows heavily from that ecosystem. Two stacks people run
around the same loop:

- [Gas City](https://github.com/gastownhall/gascity) — orchestration-builder for
  multi-agent coding workflows
- Jeffrey Emanuel's [Agentic Coding Flywheel](https://agent-flywheel.com) —
  coordinated multi-agent tooling (mail, beads, NTM, and friends)

## Optional: `ao` CLI

Deterministic checks, inspection, and skill linking. Skip it if you only need
the skills.

```bash
brew tap boshu2/agentops https://github.com/boshu2/homebrew-agentops
brew install agentops
```

Without Homebrew: `go install github.com/boshu2/agentops/cli/cmd/ao@latest`

To track skills from a local checkout instead of a release bundle, run
`ao skills link` from that checkout.

## Why AgentOps exists

### 1. The agent said it was done

Same session that wrote the code also declared victory. AgentOps separates
authorship from judgment: `implement` produces a candidate; `validate` must
run in a fresh context and may use a different model. It issues `PASS`,
`FAIL`, or `NOT_PROVEN`.

### 2. One perspective rubber-stamped another

A single context can share blind spots with the author. Opt into
[`idea-genie`](skills/idea-genie/SKILL.md) or [`council`](skills/council/SKILL.md)
for sealed or multi-judge review. They return a report;
[`validate`](skills/validate/SKILL.md) writes `verdict.v2`.

### 3. Acceptance drifted mid-flight

Without a fixed behavior and write scope, "done" is whatever the agent
improvised. `plan` locks acceptance in the bead before anyone builds. Later
phases bind to that digest.

### 4. Nobody can replay what was judged

Chat scrolls away. `validate` writes a content-addressed `verdict.v2` under
`.agents/ao/verdicts/sha256/` with checked scope, omissions, and evidence
refs. Plain JSON. No hosted service required.

## Core skills

| Skill | Job |
|---|---|
| [`rpi`](skills/rpi/SKILL.md) | run Plan, Implement, and fresh Validate at most once |
| [`plan`](skills/plan/SKILL.md) | create the bead (BDD + DDD ubiquitous language) |
| [`implement`](skills/implement/SKILL.md) | TDD against the bead: RED → GREEN → refactor |
| [`validate`](skills/validate/SKILL.md) | fresh context (optionally different model); persist `verdict.v2` |

Optional later: [`learn`](skills/learn/SKILL.md). Strategies:
[`council`](skills/council/SKILL.md), [`idea-genie`](skills/idea-genie/SKILL.md),
[`premortem`](skills/premortem/SKILL.md), [`postmortem`](skills/postmortem/SKILL.md).

## One skill, many shapes

AgentOps prefers a smaller skill set you can steer over dozens of near-duplicate
skills. Modes and flags change behavior inside one contract.

| Skill | Steer with | Examples |
|---|---|---|
| [`doc`](skills/doc/SKILL.md) | `--mode` | `readme`, `oss`, default API/docs; README mode runs a docs-prose (de-slop) pass |
| [`codebase-recon`](skills/codebase-recon/SKILL.md) | mode · view · lens · depth | `baseline`/`delta`; emphasize audit or mental model; one domain lens per pass |
| [`idea-genie`](skills/idea-genie/SKILL.md) | elicit \| duel | portfolio vs sealed multi-perspective challenge |
| [`rpi`](skills/rpi/SKILL.md) | bead / intent ref | one full loop against a frozen bead |

Read the skill's mode table before inventing a sibling skill. Full inventory:
[Skill Router](docs/SKILL-ROUTER.md).

## Evidence contract

A `PASS` binds unchanged acceptance, a deterministic subject manifest, complete
changed-path coverage inside write scope, distinct author and validator context
IDs, a freshness attestation, and criterion-level evidence.

Missing identity, mutation, or incomplete coverage → `NOT_PROVEN`. Proven
out-of-scope change or failed criterion → `FAIL`.

[Operating loop](docs/architecture/operating-loop.md) · [CLI](cli/docs/COMMANDS.md) · [Docs](docs/documentation-index.md)

Contributing: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). License: Apache-2.0.
