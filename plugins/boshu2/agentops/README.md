# AgentOps

AgentOps is the operations layer for agentic engineering. It is a set of
portable skills and evidence contracts that make one coding-agent change
independently judgeable: the context that wrote the code does not get to
declare it done. Your tracker keeps the work, Git keeps the history, and your
coding agents keep running the execution; AgentOps joins them as a
federated integration graph and adds the judgment step. A fresh context reads
the exact change and returns `PASS`, `FAIL`, or `NOT_PROVEN`. The standard
path is one RPI traversal:

```text
RPI -> Plan -> Implement -> fresh Validate -> repair to convergence -> report
```

The selected **CDLC (Context Delivery Lifecycle)** contract adds maintained
external context and learning around disposable agents. Discovery (shaped by
Plan), Implement and Validate remain bounded by caller intent; a selected outer
goal can authorize a new experiment within its native limits. This is contract
adoption: Recall, extended Learn, evolve and the Go evidence migration are later
work, not new runnable entrypoints. It promises neither weight training nor
deterministic inference, and the current trial demonstrates no memory benefit.
External reviewed Markdown/OKF memory, protected non-Git evidence and separate
support/disclosure/utility claims are specified in
[ADR-0016](docs/adr/ADR-0016-state-tiers.md).

## Quickstart

```bash
npx skills@latest add boshu2/agentops --all -g
```

One command installs the skill bundle into every coding agent you use. The
skills run **inside your coding agent** (Claude Code, Codex, Cursor, …): type
`/rpi` in that agent's chat, or ask for `plan`, `implement`, `validate`, and
`learn` by name. Most skills need nothing beyond the coding agent; these need
more:

| Skill | Needs | Why |
|---|---|---|
| `rpi` | `python3`, conditional | invokes plan and validate, which may run `python3` (see below); rpi's own procedure only cites `scripts/run_once.py` as reference behavior |
| `plan` | `python3`, conditional | runs `scripts/validate.py snapshot-intent` only when the intent source is not durable |
| `validate` | `python3` | its helper commands run `python3` against `scripts/validate.py` |
| `fitness` | `ao` | its whole procedure is running one `ao goals` subcommand |
| `using-gc` | `ao` | rig prep runs `ao gc prepare` and `ao gc check` |
| `handoff` | `ao`, optional | `ao session handoff`/`rehydrate` cover the same artifact; the skill can write it directly |
| `status` | `ao`, optional | describes `ao status`'s output shape; the report can be read directly from `.agents/ao/` |
| `reverse-engineer` | `python3` | Phase 1's mechanical teardown runs `scripts/reverse_engineer.py` |
| `skill-builder` | `python3`, conditional | Create mode's `build.sh` runs `scripts/generate-skill-mesh.py`; heal/check/audit modes are bash-only |
| `ms` | `python3`, conditional, plus `ms` binary | the MCP-search fallback runs `python3 skills/ms/scripts/mcp-search.py`; the `ms` binary is required for CLI load, write, and admin operations |
| `toil-mining` | `python3`, conditional | the recent-human extractor runs `scripts/recent_human.py` for Codex JSONL session sources |
| `security` | `python3`, conditional | the composable suite and offline redteam surfaces run `security_suite.py` when that scan type is selected |
| `cass` | `python3`, optional | `scripts/prompt_miner.py` mines repeated prompts; one of several selectable Scripts-table entries |

The plugin and `npx skills@latest add boshu2/agentops --all -g` install all 54 skills today, regardless of whether you have `python3` or `ao`.

Ran it? Tell us what it judged. Open an issue, and paste the `verdict.v2` if
you asked `validate` to persist one:
<https://github.com/boshu2/agentops/issues>.

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

- **npx / [skills.sh](https://skills.sh)**: universal; copies skills you can edit.
- **Plugins**: a read-only bundle that stays current with the repo.
- **Checkout + `ao skills link`**: source-tracked symlinks for contributors
  (see [Install and day-2 operations](docs/install-day2-ops.md)).

## Admission-control hooks (on by default)

AgentOps ships a PreToolUse **policy dispatcher**: deterministic guards that
block a small set of known-destructive commands (staging the private bead
ledger, hand-editing the hash-chained provenance ledger, overwriting installed
skill copies) and route you to the correct tool instead. Silent on every clean
call; every block is one line.

- **Claude Code plugin installs:** active automatically; nothing to run.
- **npx / skills.sh copies:** run `~/.claude/skills/cc-hooks/scripts/install-hooks.sh` once.
- **git clone / brew:** run `scripts/install-policy-dispatch.sh` once.

Disable anytime (`/plugin disable agentops`, or remove the two PreToolUse
matchers from settings). Policy list and design:
`skills/cc-hooks/SKILL.md`.

Remove with your runtime's plugin uninstall, or delete the linked skill
directories.

## Intent lives in a bead

[Beads](https://github.com/steveyegge/beads) is the preferred tracker
(optional; `brew install beads`). Plan
writes [BDD](https://cucumber.io/docs/bdd/) acceptance and DDD [ubiquitous
language](https://martinfowler.com/bliki/UbiquitousLanguage.html) into the bead;
Implement builds against it; Validate judges a hashed snapshot under
`.agents/ao/intents/sha256/`. No beads? Plan shapes the caller's issue or chat
text and the runtime snapshots those bytes the same way. These are standalone
product-proof defaults; selected CDLC knowledge/disclosure evidence requires
protected external routing before storage (ADR-0016).

`validate` must run in a fresh context (not the author session). Risky surfaces
and caller-required diversity need both fresh and cross-family exact-subject
judgments; an unavailable required leg leaves PASS unproven. Other surfaces
may use the same model. See the authorized bounded
[model-dispatch recipe](skills/agent-native/references/model-dispatch.md).

## Multi-agent systems

The default is one agent, one writer. When you need a fleet,
[`swarm`](skills/swarm/SKILL.md), [`agent-native`](skills/agent-native/SKILL.md),
[`ntm`](skills/ntm/SKILL.md), and [`using-gc`](skills/using-gc/SKILL.md)
orchestrate multi-agent work. They dispatch; they do not own the verdict.

### Choose a software factory

AgentOps supplies skills and evidence contracts, not another software-factory
runtime or a competing Gas City pack. Install the skills in the agent runtime
used by the factory you choose; its Mayor, coordinator, and workers can then use
`plan`, `implement`, `test`, `validate`, and the rest of the catalog.

Two factory stacks are supported:

- [Gas City](https://github.com/gastownhall/gascity) is the preferred choice
  for durable, supervised workflows. Use the upstream
  [`gascity` build pack](https://github.com/gastownhall/gascity-packs/tree/main/gascity),
  the workflow family used by Maintainer City. It owns formulas, roles,
  worktrees, dispatch, draining, and run state. The
  [`using-gc`](skills/using-gc/SKILL.md) skill covers installation, launch,
  observation, and recovery.
- Jeffrey Emanuel's
  [Agentic Coding Flywheel](https://agent-flywheel.com) is a supported
  alternative built from Beads, Agent Mail, NTM, and the wider Flywheel tool
  stack. Use its native workflow and let its agents consume the same AgentOps
  skills. The [`using-flywheel`](skills/using-flywheel/SKILL.md) skill covers
  provisioning, skill visibility, and the evidence boundary.

AgentOps does not wrap either factory or translate factory completion into
semantic PASS. When proof is required, a fresh `validate` context judges the
exact candidate and evidence.

## Optional: `ao` CLI

Deterministic checks, inspection, and skill linking. `fitness` and
`using-gc` call it directly; the rest of the skills work without it. Install
steps (Homebrew or `go install`), and `ao skills link` for
tracking skills from a local checkout:
[Install and day-2 operations](docs/install-day2-ops.md#maintainer--contributor-the-ao-binary).

## Why AgentOps exists

### 1. The agent said it was done

Same session that wrote the code also declared victory. AgentOps separates
authorship from judgment: `implement` produces a candidate; `validate` must
run in a fresh context and may use a different model. It issues `PASS`,
`FAIL`, or `NOT_PROVEN`.

### 2. One perspective rubber-stamped another

A single context can share blind spots with the author. Opt into
[`idea-genie`](skills/idea-genie/SKILL.md) or [`council`](skills/council/SKILL.md)
for sealed or multi-judge review. They return a report; an author-distinct
[`validate`](skills/validate/SKILL.md) context issues the binding result.

### 3. Acceptance drifted mid-flight

Without a fixed behavior and write scope, "done" is whatever the agent
improvised. `plan` locks acceptance in the bead before anyone builds. Later
phases bind to that digest.

### 4. Nobody can replay what was judged

Chat scrolls away. When replay or automation needs durable evidence, `validate`
writes a content-addressed `verdict.v2` under
`.agents/ao/verdicts/sha256/` with checked scope, omissions, and evidence refs.
Plain JSON. No hosted service required. Interactive validation does not create
one unless requested.

## Core skills

| Skill | Job |
|---|---|
| [`rpi`](skills/rpi/SKILL.md) | guard once, Plan and Implement at most once, fresh Validate plus admitted bounded repairs; report |
| [`anti-ceremony`](skills/anti-ceremony/SKILL.md) | STOP/CONTINUE guard before Plan: name the consumer, the decision, the defect, and the retirement condition, or do not create the artifact |
| [`plan`](skills/plan/SKILL.md) | create the bead (BDD + DDD ubiquitous language) |
| [`implement`](skills/implement/SKILL.md) | TDD against the bead: RED → GREEN → refactor |
| [`validate`](skills/validate/SKILL.md) | fresh context (optionally different model); optionally persist `verdict.v2` |

Optional later: [`learn`](skills/learn/SKILL.md). Strategies:
[`council`](skills/council/SKILL.md), [`idea-genie`](skills/idea-genie/SKILL.md),
[`premortem`](skills/premortem/SKILL.md), [`postmortem`](skills/postmortem/SKILL.md),
[`one-way-door`](skills/one-way-door/SKILL.md) (is this decision reversible?),
[`reality-check`](skills/reality-check/SKILL.md) (does the repo match the claim?).
Not sure which skill owns a request? Ask [`route`](skills/route/SKILL.md).

## One skill, many shapes

AgentOps prefers a smaller skill set you can steer over dozens of near-duplicate
skills. Modes and flags change behavior inside one contract.

| Skill | Steer with | Examples |
|---|---|---|
| [`doc`](skills/doc/SKILL.md) | `--mode` | `readme`, `oss`, default API/docs; README mode runs a docs-prose (de-slop) pass |
| [`codebase-recon`](skills/codebase-recon/SKILL.md) | mode · view · lens · depth | `baseline`/`delta`; emphasize audit or mental model; one domain lens per pass |
| [`idea-genie`](skills/idea-genie/SKILL.md) | elicit \| duel | portfolio vs sealed multi-perspective challenge |
| [`rpi`](skills/rpi/SKILL.md) | bead / intent ref | one full traversal against a frozen bead |

Read the skill's mode table before inventing a sibling skill. Full inventory:
[Skill Router](docs/SKILL-ROUTER.md).

## Evidence contract

A `PASS` binds unchanged acceptance, a deterministic subject manifest, complete
changed-path coverage inside write scope, distinct author and validator context
IDs, a freshness attestation, and criterion-level evidence.

Missing identity, mutation, or incomplete coverage → `NOT_PROVEN`. Proven
out-of-scope change or failed criterion → `FAIL`.

[RPI traversal](docs/architecture/rpi-traversal.md) · [CLI](cli/docs/COMMANDS.md) · [Docs](docs/documentation-index.md)

Contributing: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md). License: Apache-2.0.
