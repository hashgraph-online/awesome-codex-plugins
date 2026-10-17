<div align="center">

<img src="docs/assets/logo.svg" alt="AgentOps" width="72" height="72">

# AgentOps

**DevOps discipline for AI coding agents.**

[![Validate](https://github.com/boshu2/agentops/actions/workflows/validate.yml/badge.svg?branch=main)](https://github.com/boshu2/agentops/actions/workflows/validate.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Latest release](https://img.shields.io/github/v/release/boshu2/agentops)](https://github.com/boshu2/agentops/releases/latest)
[![Skills](https://img.shields.io/badge/skills-catalog-black.svg)](docs/SKILL-ROUTER.md)

[Install](#quickstart) · [The loop](#the-operational-loop) ·
[Goals](#goals) · [Try it](#try-it) · [Skills](#skills-at-a-glance) ·
[Make it yours](#make-it-yours) · [Evidence](#evidence) ·
[Beyond AgentOps](#beyond-agentops)

</div>

DevOps makes software delivery repeatable through shared practices, automated
checks and feedback. AgentOps brings that discipline to agentic coding sessions:
paved paths your agents can follow from intent to checked results, with memory
to carry useful context into the next task.

Those paths combine [skills](docs/SKILL-ROUTER.md) with the [`ao` CLI](#optional-ao-cli)
and your existing engineering tools. [Plan](skills/plan/SKILL.md) clarifies the
expected behavior; [Test](skills/test/SKILL.md) helps check it;
[Validate](skills/validate/SKILL.md) adds independent judgment where needed.
Skills guide the agent's decisions; executable gates check specific contracts.
[Beads](https://github.com/gastownhall/beads) preserves the work graph, decisions,
results and project memories. [Memory](skills/memory/SKILL.md) curates supported
findings into linked project knowledge, connecting lessons to the work and
sources behind them. The next session can use that record instead of starting over.

The skills are a kit, and you are expected to change it. Each skill is one
Markdown file of instructions. Keep the ones that fit how you work, rewrite the
ones that almost fit, delete the rest, and add skills you write yourself or find
in other libraries. What you end up with is your own operating model for agents,
which is the reason this project exists. [Make it yours](#make-it-yours) shows
how.

Use these paths with Claude Code, Codex, Cursor, OpenCode, Gemini CLI, Pi and
other coding agents, or personal assistants such as OpenClaw and Grok Bot.
Start with [one useful task](#try-it); follow the [operational loop](#the-operational-loop)
for a change or the [goal workflow](#goals) for work across sessions. When you
need a larger software factory, [extend the same practices](#beyond-agentops)
with Gas City or tools from the Agentic Coding Flywheel.

<a id="why-these-skills-exist"></a>

## Why use AgentOps?

A [software factory](https://learn.microsoft.com/en-us/archive/msdn-magazine/2006/december/service-station-web-service-software-factory)
makes engineering practices reusable through tools, guidance and repeatable
workflows. AgentOps brings that approach into the coding session: clear intent,
automated checks, recorded decisions and a feedback loop into later work. Pick
the path your task needs and use the same practices when you change agents.

[Behavior-driven development (BDD)](https://dannorth.net/introducing-bdd/)
starts by agreeing on what the software should do in a concrete situation.
For retries, that could mean: “If a completed job arrives again, return its
result and charge the customer only once.” The same behavior guides the
implementation, its tests and any review. [Plan](skills/plan/SKILL.md) helps you
settle those expectations before the agent starts editing.

| When you need to… | AgentOps adds |
|---|---|
| Get the agent to build what you meant | [Plan](skills/plan/SKILL.md) makes the expected behavior clear enough to implement and test. [Domain](skills/domain/SKILL.md) keeps the same names for concepts in the request, code and tests. |
| Keep a project moving after the chat ends | [Interview](skills/interview/SKILL.md) settles a large goal with you. [Beads](https://github.com/gastownhall/beads) preserves its intent, decisions and results in a searchable work graph, with persistent project memories for later sessions. [Navigate](skills/navigate/SKILL.md) identifies ready work, blockers and gaps in the goal. |
| Check whether the finished change meets the request | [Test](skills/test/SKILL.md) helps write checks for the intended behavior. Ordinary changes finish on checks and CI; [Validate](skills/validate/SKILL.md) adds one fresh review when requested, hard to undo, or uncovered by a deterministic check. |
| Turn earlier work into useful context | [Research](skills/research/SKILL.md) traces the code and cites what it finds. [Memory](skills/memory/SKILL.md) can draw on Beads handoffs, Git changes and check results to explain a decision in a report, or curate supported lessons into reviewed project documents. Later agents can recall the lesson and follow its sources. |
| Make a useful method repeatable | [Skill Builder](skills/skill-builder/SKILL.md) turns supported expertise into guidance with clear inputs, actions and limits. [Skill Eval](skills/skill-eval/SKILL.md) measures whether that guidance helps a named task, so it can be retained, revised or removed. |

<a id="install"></a>

## Quickstart

Pick one method per agent: a plugin plus npx on the same agent gives you every
skill twice.

<details>
<summary><strong>Claude Code</strong></summary>

<a id="claude-code"></a>

```bash
claude plugin marketplace add boshu2/agentops
claude plugin install agentops@agentops-marketplace
claude plugin details agentops@agentops-marketplace
```

Check that `agentops` appears in the plugin inventory. The bundle includes
skills, four agents and [tool-call guards](#optional-admission-control-hooks).

</details>

<details>
<summary><strong>Codex</strong></summary>

<a id="codex"></a>

```bash
codex plugin marketplace add boshu2/agentops
codex plugin add agentops@agentops-marketplace
codex plugin list --json
```

Check that `agentops` appears in the inventory. Skills use the `agentops:` prefix;
custom roles and read limits have [separate setup](docs/install-day2-ops.md#install-and-update-runtime-plugins).

</details>

<details>
<summary><strong>Everything else</strong> (Cursor, OpenCode, Gemini CLI, Pi, OpenClaw, Grok Bot)</summary>

<a id="everything-else"></a>

With Node.js installed, run from your project directory, then pick your agents
and skills:

```bash
npx skills@latest add boshu2/agentops
```

Add `-g` for a user-level install. In scripts, name the agents:
`npx skills@latest add boshu2/agentops -g -a cursor opencode -y`
(`-y` without `-a` can install into every agent the installer knows).
Installer targets include `cursor`, `opencode`, `gemini-cli`, `antigravity`,
`pi`, `grok` (Grok Build) and `openclaw`. Grok Bot has no installer target; add
the same `SKILL.md` folders through [its skill settings](https://docs.x.ai/grok-bot/skills-routines-and-automations).
Some skills need extra tools ([install guide](docs/install-day2-ops.md)); what
each host has been tested for is in [host coverage and limits](docs/contracts/multi-runtime-tier-charter.md#host-and-install-surface-mapping).

</details>

Start a new session so the skills load. Most skills need only your coding
agent; a few use the [`ao` CLI](#optional-ao-cli) when it is installed. Invocation names
vary by agent: this README shows Claude Code's `/agentops:<skill>`; Codex uses
`$agentops:<skill>`.

<a id="workflow"></a>

## The operational loop

Each change is shaped, built and checked. Use one fresh review when requested,
when a mistake cannot be cheaply undone, or when no deterministic check covers
the changed behavior. You (or Plan) write intent as
behavior ([BDD](https://dannorth.net/introducing-bdd/)), using one word per
concept ([DDD](https://martinfowler.com/bliki/DomainDrivenDesign.html)'s
[ubiquitous language](https://martinfowler.com/bliki/UbiquitousLanguage.html)).
For a system that calls queued work a **Job**, in [Gherkin](https://cucumber.io/docs/gherkin/reference/):

```gherkin
Feature: Job redelivery is idempotent
  A Job is one unit of queued work. Delivering it again never repeats its side effect.

  Scenario: A completed Job is delivered again
    Given Job "J-42" completed and charged the customer $20
    When the worker receives Job "J-42" again
    Then it returns the completed result of "J-42"
    And the customer has been charged $20 exactly once

  Scenario: A Job that failed before charging is delivered again
    Given Job "J-43" failed before charging the customer $20
    When the worker receives Job "J-43" again
    Then Job "J-43" completes
    And the customer has been charged $20 exactly once
```

The feature defines the domain term once; each scenario has concrete data, one
action and an observable result. Keep scenarios in the issue or conversation;
no `.feature` file is required.

<p align="center">
  <img src="docs/assets/agentops-routes.svg" alt="Clear accepted intent goes straight to Implement; unclear intent goes to Plan first. Implement runs native checks and CI. Ordinary changes finish on those checks. Use one fresh author-distinct review when requested, when a mistake cannot be cheaply undone, or when no deterministic check covers the changed behavior. An existing change can enter at review. Repair findings within scope and confirm with affected checks; another review requires a caller request. NOT_PROVEN reports missing evidence without claiming PASS. The optional learning loop sends a result to a protected draft, fresh support and disclosure review, reviewed .context/ pages, and later work." width="100%">
</p>

| Step | Skill | What it does with the scenarios |
|---|---|---|
| Shape | [`plan`](skills/plan/SKILL.md) | Turns the request into scenarios for one small change. Skip it when intent is clear. |
| Build | [`implement`](skills/implement/SKILL.md) | Makes the change and tests both scenarios. |
| Judge when needed | [`validate`](skills/validate/SKILL.md) | A new session that didn't write it returns `PASS`, `FAIL` or `NOT_PROVEN` against the same scenarios. |
| Learn | [`memory`](skills/memory/SKILL.md) | Optional: reviewed `.context/` pages that later work can query. |

Enter at the step you need. An existing change can enter at Validate when an
acceptance judgment is needed. Ordinary changes finish on checks and CI. Review
is one round: repair findings and confirm with affected checks; review again only
when you ask. Report `NOT_PROVEN` with its gaps. The author cannot issue its own
`PASS`. Merging and releasing follow your repo's rules.

<a id="goals-many-rpis-over-a-bead-graph"></a>

## Goals

[`rpi`](skills/rpi/SKILL.md) runs Plan → Implement → checks, with Validate where a
mistake is costly, for one outcome
without check-ins (your agent's permission prompts still apply) and stops at
acceptance, a blocker or a spent limit. Bigger work becomes a goal (it
needs Beads: `brew install beads`, then `bd init` in your repo):

1. **[Interview](skills/interview/SKILL.md).** One question at a time, each with
   a recommended answer. You settle the outcome, its examples, domain terms,
   non-goals, authority and budget before agents go autonomous.
2. **[Craft Goal](skills/craft-goal/SKILL.md).** Returns `SAFE_TO_CREATE` plus a
   prompt to paste into `/goal` (Claude Code or Codex), `USE_RPI` (small enough
   for `rpi`), or `UNSAFE_GOAL` plus what's undecided. It creates nothing itself.
3. **[Navigate](skills/navigate/SKILL.md) each round.** Picks a few ready work
   items (beads); each gets one RPI, checks and CI, with one fresh Validate
   when requested, hard to undo, or uncovered by a deterministic check. The goal ends
   `ACHIEVED`, `NOT_ACHIEVED` or `NEEDS_OPERATOR`.

<p align="center">
  <img src="docs/assets/agentops-goal-graph.svg" alt="A goal observes the Beads work graph, picks ready beads, consumes checks and any verdicts, then ratchets or stops. Each bead gets one RPI: Plan when unclear, Implement, and checks. When delegation is authorized, each fresh worker starts with one bead. Validate runs in a separate fresh context only when requested, when a mistake is hard to undo, or when no deterministic check covers the change. Results and notes return to the bead." width="100%">
</p>

**Beads remembers the work.** [Beads](https://github.com/gastownhall/beads) (`bd`)
keeps the goal and its history outside any conversation. The root epic holds
acceptance; child beads carry the scoped work, design decisions, handoffs and
result notes. Record which checks ran and link any review evidence to the same
bead. That connects the original intent to the checked output, so the next
session can continue from the record instead of reconstructing the chat.
`bd ready` finds unblocked work; search and history help explain earlier choices.

Beads also has a [persistent memory store](https://github.com/gastownhall/beads/blob/main/docs/cli-reference/remember.md).
`bd remember` saves project facts, `bd memories` searches them, `bd recall`
retrieves one by key, and `bd prime` brings stored memories into session context.
The work graph and the memory store serve different needs: one preserves what
happened; the other keeps selected facts easy to find again.

[Memory](skills/memory/SKILL.md) helps you use that material: recall relevant
context, examine recorded decisions and outcomes, or draft a report with links
to its evidence. When you want a reusable project document, it curates supported
findings into reviewed `.context/` pages or an external document bundle. Beads
keeps the work record; Git and the original evidence locations keep the code and
check artifacts. Reusable documents link back to those sources.

```bash
bd search "redelivery" --status all     # include finished work
bd show <bead-id>                        # intent, notes and relationships
bd history <bead-id>                     # how the record changed
bd remember "Redelivery returns the stored Job result" --key job-redelivery
bd recall job-redelivery                # retrieve the saved project fact
```

**One bead per worker.** When the goal delegates, the orchestrator holds the
graph and results, and each worker starts with one bead instead of the
orchestrator's transcript. Reviewers, when needed, start fresh.

```bash
bd create "Job redelivery is idempotent" -t epic
bd create "Return the completed result on redelivery" --parent <epic-id>
bd dep add <later-id> <earlier-id>         # real ordering only
bd ready --parent <epic-id>                # the frontier
```

Navigate shows `bd` commands; another tracker with status, dependencies and
notes works if you map them. AgentOps never builds a second work index.

## Try it

Start read-only in any repo, then swap the Job example for your own change.

```text
# First look (changes nothing)
/agentops:research how does this repo validate input? cite files and lines, change nothing

# One change
/agentops:plan make Job redelivery return the completed result without repeating the side effect
/agentops:implement
/agentops:validate     # when requested, hard to undo, or uncovered by checks; use a new session

# One outcome, end to end
/agentops:rpi make Job redelivery return the completed result without repeating the side effect

# A goal
/agentops:interview make the job worker safe under redelivery, retries and crash recovery
/agentops:craft-goal   # then paste its prompt into /goal
```

<a id="how-independent-review-works"></a>

<details>
<summary><strong>Validate an existing change</strong></summary>

Pick a finished change whose accepted behavior is recorded in an issue or
conversation. Run the required checks and keep the candidate unchanged.
[Installing `ao`](#optional-ao-cli) is optional; it gives Validate a content
manifest for the change. Then open a **new conversation**, fill in the
references and paste:

```text
Use the AgentOps Validate skill to judge this finished change.
Original accepted behavior: [issue link or original request text]
Candidate: [commit, branch or working tree; list every changed path]
Author context ID: [task/session ID that made the change]
Checks run: [commands and results]
I opened this new conversation for fresh review. Derive the exact subject
identity at the start and end, inspect every changed path against the original
behavior, and do not modify the candidate. Report PASS, FAIL or NOT_PROVEN with
evidence for each criterion, checked, not_checked, author and reviewer context
IDs, and freshness attestation.
```

`PASS` needs evidence for every criterion and an empty `not_checked`. `FAIL`
names failed behavior or an out-of-scope change. Missing proof, identity or
path coverage is `NOT_PROVEN`.

</details>

<a id="try-one-task"></a>

<details>
<summary><strong>Read-only skill-loading smoke test</strong></summary>

Paste this in an agent conversation in your project. It needs no `ao` CLI.

```text
Use the AgentOps Research skill to trace how this repository validates user
input. Follow one path from the input through its checks and tests. Cite the
files and line numbers, explain one edge case, and identify missing coverage.
Name the Research skill file you loaded. Answer here without changing files.
```

The reported skill path catches missing or duplicate installs. Invoke Research
directly with `/agentops:research` in Claude Code, `$agentops:research` in
Codex, or `/` and the installed Research entry in Cursor.

</details>

<a id="choose-skills-by-the-work"></a>

## Skills at a glance

All skills are optional. Load one when it answers a specific question. Full
catalog: **[docs/SKILL-ROUTER.md](docs/SKILL-ROUTER.md)**.

| Group | Skills | What it covers |
|---|---|---|
| Operational loop | [`plan`](skills/plan/SKILL.md) [`implement`](skills/implement/SKILL.md) [`validate`](skills/validate/SKILL.md) | Shape and build a change; judge it where a mistake is costly |
| Autonomous | [`rpi`](skills/rpi/SKILL.md) | One outcome, end to end |
| Goals | [`interview`](skills/interview/SKILL.md) [`craft-goal`](skills/craft-goal/SKILL.md) [`navigate`](skills/navigate/SKILL.md) | Shape, write and walk a goal over the bead graph |
| Coordination | [`orchestrate`](skills/orchestrate/SKILL.md) [`agent-native`](skills/agent-native/SKILL.md) | Fresh workers per bead, disjoint scopes, integration |
| On demand | [`research`](skills/research/SKILL.md) [`domain`](skills/domain/SKILL.md) [`test`](skills/test/SKILL.md) [`refactor`](skills/refactor/SKILL.md) [`review`](skills/review/SKILL.md) [`security`](skills/security/SKILL.md) [`doc`](skills/doc/SKILL.md) [`reverse-engineer`](skills/reverse-engineer/SKILL.md) | Reached for when a specific question comes up |
| Learning | [`memory`](skills/memory/SKILL.md) | Curated `.context/` pages safe to commit |
| Judgment strategies | [`council`](skills/council/SKILL.md) [`premortem`](skills/premortem/SKILL.md) [`postmortem`](skills/postmortem/SKILL.md) [`reality-check`](skills/reality-check/SKILL.md) [`idea-genie`](skills/idea-genie/SKILL.md) | Multi-model councils (debates, idea duels, interview panels), idea brainstorms, plan challenges, postmortems and claim audits |
| Runtimes and factories | [`codex-exec`](skills/codex-exec/SKILL.md) [`claude-exec`](skills/claude-exec/SKILL.md) [`agy-native`](skills/agy-native/SKILL.md) [`using-gc`](skills/using-gc/SKILL.md) | Selected executors and Gas City integration |
| Skill craft | [`skill-builder`](skills/skill-builder/SKILL.md) [`skill-eval`](skills/skill-eval/SKILL.md) | Author skills and measure whether they help |

## Make it yours

Every skill here is a folder with one `SKILL.md`: plain instructions an agent
loads when a task calls for them. No skill depends on the full set, and coding
with none of them still works. That makes the library easy to take apart, and
you should. The 29 skills are a starting point for an operating model that fits
your work.

- **Start small.** Install two or three skills that match work you already do.
  Add another when a real task asks for it.
- **Cut what you override.** If you or the agent keep ignoring a rule, change
  the rule or remove the skill. `npx skills` lets you pick skills per agent, and
  [`ao skills link --skill <name>`](docs/install-day2-ops.md#install-source-checkout)
  links an exact subset from a checkout.
- **Rewrite what almost fits.** Fork this repository, edit the `SKILL.md` and
  install from your fork with the same commands, or link a checkout so every
  agent on your machine reads your edits. A plugin update replaces the installed
  copy, so keep your changes in a repository you control.
- **Write your own.** When you have explained the same thing to an agent three
  times, it is a skill. [Skill Builder](skills/skill-builder/SKILL.md) drafts the
  package, and tells you when a note in an existing file is enough.
- **Mix libraries.** Run these next to your company's skills, the
  [Agentic Coding Flywheel](#agentic-coding-flywheel) tools or any other
  library. `ao skills link` never replaces a skill it did not install.
- **Change the workflows too.** The [operational loop](#the-operational-loop)
  and the [goal workflow](#goals) are defaults. Skip the steps your work does
  not need, reorder them, or write your own. The Claude Code workflow scripts in
  [`workflows/`](workflows/) link into a project with
  [`ao workflows link`](docs/install-day2-ops.md#workflows-claude-code-only).
- **Measure what you change.** `claude plugin eval` compares an agent with and
  without a plugin on the same request. To measure one edit, run the old and
  the new version as two plugins. [Skill Eval](skills/skill-eval/SKILL.md)
  covers how to read the result, and [Evidence](#evidence) shows the cases this
  repository runs; copy them for your own skills.

## Evidence

A skill is a page of instructions, so the test is whether an agent does anything
differently with it installed. AgentOps runs that test on Claude Code's own
evaluator, `claude plugin eval`: one realistic request per skill, three runs
with the plugin and three without, each answer graded against four or five
criteria taken from the practice the skill teaches. For Test, one criterion is
that a regression test is shown failing without the fix.

On Claude Opus 5.5, measured 2026-10-05:

| | No plugin | AgentOps 3.9.0 | AgentOps 3.10 |
|---|---:|---:|---:|
| Practice criteria met on 28 requests | 269 of 372 (72%) | 292 of 372 (78%) | 349 of 372 (94%) |
| Matching skill loaded on a blind request | | 11 of 48 runs | 29 of 48 runs |

Fourteen of the 29 skills moved their case by 0.15 or more. Craft Goal, Claude
Exec, Plan, Memory and Skill Builder gained the most. The other 15 made no
measurable difference, and for eight of those the agent already met every
criterion with no plugin.

Read the limits before you quote these numbers:

- One request per skill, three runs, one model. A difference under 0.15 is
  noise.
- The 28 requests in the first row were also used to tune the 3.10
  descriptions, which flatters 3.10. The blind requests in the second row were
  written without sight of the descriptions.
- The criteria come from each skill's own rules. A pass shows the rule landed on
  that request. It says nothing about the outcome of a real task, and an earlier
  [coding pilot](PRODUCT.md#evidence-and-claim-limits) found no end-to-end
  difference.
- Loading is the weak point. Nine skills did not load on a request they had
  never seen, and Implement does not load on a quick fix. Name the skill when
  you want its rules applied.

The [full report](docs/evals/2026-10-05-plugin-eval-opus-5-5.md) has every case,
the method and what was rerun. The cases live in
[`evals/plugin-eval/`](evals/plugin-eval/README.md): run them against your own
changes, or copy the layout to test your own skills.

## Where AgentOps fits

AgentOps grew from applying DevOps experience and established engineering
practice to agents. The [Practice Registry](PRACTICE-REGISTRY.md) records the
lineage; [how it works](docs/how-it-works.md) covers responsibilities.

<details>
<summary>Compare libraries, trackers and agent factories</summary>

| Project or tool | Role alongside AgentOps |
|---|---|
| [Compound Engineering](https://github.com/EveryInc/compound-engineering-plugin) | A connected development workflow and reusable solution records |
| [Matt Pocock's skills](https://github.com/mattpocock/skills) | Composable practices for intent, domain modeling, TDD and review |
| [Beads](https://github.com/gastownhall/beads) or your existing tracker | Owns work status, dependencies and handoffs |
| Factories such as [Gas City](skills/using-gc/SKILL.md) | Own agent coordination and execution through their native control plane |

Choose which workflow leads the task. Carry accepted behavior and evidence
into checks, and into [independent judgment](skills/validate/SKILL.md) where a
mistake would be costly. Shared practices are not
proof that every combination has been tested.

</details>

<a id="optional-ao-cli"></a>

## `ao` CLI (optional)

Most skills need only your coding agent. With `ao` installed, Validate binds
the exact change it judges to a content manifest; without it, Validate names
the commit and the changed paths.

```bash
brew tap boshu2/agentops
brew trust --tap boshu2/agentops
brew install agentops
ao version
```

With Go installed: `go install github.com/boshu2/agentops/cli/cmd/ao@latest`.
`ao init` is optional evidence setup; `ao config --show` inspects configuration;
`ao gate check` runs this repository's own gates (mainly for contributors). See the [command reference](cli/docs/COMMANDS.md) and
[installation guide](docs/install-day2-ops.md).

## Updating and advanced setup

<details>
<summary><strong>Upgrading to 3.10</strong></summary>

<a id="upgrading-to-310"></a>
<a id="upgrading-to-39"></a>
<a id="upgrading-to-38"></a>
<a id="upgrading-to-37"></a>

Version 3.10 keeps every 3.9 command and skill name. It rewrites the skill
descriptions so skills load on plain requests, adds
[`claude-exec`](skills/claude-exec/SKILL.md) and lets Validate run without `ao`.
Read the [3.10 release notes](docs/releases/2026-10-05-v3.10.0-notes.md). Use the
[plugin update instructions](docs/install-day2-ops.md#install-and-update-runtime-plugins)
or, for npx installs, `npx skills@latest update` ([update notes](docs/install-day2-ops.md#update)).
For Homebrew: `brew update && brew upgrade agentops`. In a source checkout, run
`git pull --ff-only`, then rerun `ao skills link` with the selectors you used
before, adding `--skill claude-exec` for the new skill; without selectors it
links every skill. Start a new session afterward; new installs do not silently
remove obsolete copies.

**Upgrading from 3.8 or earlier:** version 3.9 removed ten bundled external tool
skills, retired three delivery workflows, deleted the old curl installers and
changed the Codex plugin to read `skills/` directly. Read the
[3.9 release notes](docs/releases/2026-10-03-v3.9.0-notes.md) first.

**Upgrading from 3.6 or earlier:** read the [migration guide](docs/MIGRATION.md).
Version 3.7 removed commands and skill names, including `learn`, `codebase-recon`
and `swarm`; their current owners are `memory`, `research` and `agent-native`.
See the [3.7 removals](docs/releases/2026-09-13-v3.7.0-notes.md).

</details>

<details>
<summary><strong>Skill dependencies</strong></summary>

<a id="other-installation-paths"></a>

Skill installation does not install tool dependencies:

| Skill | Needs | Why |
|---|---|---|
| `rpi` | `ao`, conditional | delegates exact-subject checks to Validate; only persists `verdict.v2` when requested |
| `plan` | `ao`, conditional | runs `ao provenance snapshot-intent` with an explicit evidence root when the intent source is not durable |
| `implement` | `ao`, conditional | at an integration boundary whose changed paths affect bound evidence, runs `ao provenance evidence-orphans` |
| `validate` | `ao`, optional | with `ao`, derives exact subject identity from a content manifest and uses `ao provenance store-verdict` when persistence is requested; without it, names the commit and changed paths |
| `reality-check` | `ao`, conditional | inspect selected goal measurements with `ao goals` or evidence-store facts with `ao status` |
| `using-gc` | `ao` | rig prep runs `ao gc prepare` and `ao gc check` |
| `doc` | `ao`, optional | a requested continuity handoff may use `ao session handoff`/`rehydrate` |
| `reverse-engineer` | `python3` | Phase 1's mechanical teardown runs `scripts/reverse_engineer.py` |
| `skill-builder` | `ao` 3.9 or later outside a source checkout, Go inside one; `python3`, conditional | build, check, heal and audit run through `ao skills`; build (without `--init-only`) and heal's fix mode also run `scripts/generate-skill-mesh.py`, and `audit.sh --legacy` needs PyYAML |
| `memory` | `python3`, conditional | a selected toil investigation can use the repository helper `scripts/toil-mining/recent_human.py` on cleared Codex sources |
| `security` | `python3`, conditional | the composable suite and offline redteam surfaces run `security_suite.py` when that scan type is selected |

</details>

<details>
<summary><strong>Shared project context</strong></summary>

<a id="shared-project-context"></a>

[Memory](skills/memory/SKILL.md) can read reviewed `.context/` notes with ordinary
filesystem tools; no `ao` or Beads is needed. See this repo's [context map](.context/README.md).

Adding notes requires authorized sources and fresh review of factual support
and disclosure before Git admission. Drafts and evidence stay in protected
external storage. These procedures do not enforce access permissions or prove
that saved notes improve later work. See [Memory's storage rules](skills/memory/SKILL.md#access-storage-and-honest-limits).

</details>

<details>
<summary><strong>Permissions, optional hooks, and removal</strong></summary>

<a id="optional-admission-control-hooks"></a>

The Claude Code plugin includes PreToolUse guards for private tracker data in
commits, manual provenance-ledger edits and installed-skill overwrites. Installing
only `ao` does not add hooks; other paths can opt in through the [native hook installer](scripts/install-policy-dispatch.sh).
Read-budget guards, Codex roles and trusted Codex hooks have [separate setup](docs/install-day2-ops.md#install-and-update-runtime-plugins).

Disable Claude's plugin with `/plugin disable agentops`. Remove it with
`claude plugin uninstall agentops@agentops-marketplace`; for Codex, use
`codex plugin remove agentops@agentops-marketplace`; for npx installs, use
`npx skills@latest remove`.

</details>

<details>
<summary><strong>Architecture and saved review evidence</strong></summary>

AgentOps is the operations layer for agentic engineering. Its federated integration graph
connects evidence while Git owns content, the tracker owns work and the coding
runtime or selected factory owns execution. Your repository owns delivery.

Native execution requires zero AgentOps skills. [RPI](skills/rpi/SKILL.md),
[Gas City](skills/using-gc/SKILL.md) and [Agentic Coding Flywheel](https://agent-flywheel.com)
are optional; their completion reports do not replace required checks or judgment.

On request, Validate can save `verdict.v2` with exact content, checked scope and
evidence. New proof belongs in selected, protected storage outside Git;
existing evidence is preserved.

Read the [architecture](docs/ARCHITECTURE.md), [operating contract](docs/agent-workflow-reference.md)
and [storage rules](docs/adr/ADR-0016-state-tiers.md).

</details>

## Troubleshooting

<details>
<summary>Common problems and how to report one</summary>

| Symptom | What to check |
|---|---|
| `plugin` is not recognized | Update your agent to a version with plugin support |
| A skill is missing | Check its inventory or picker, then start a new session |
| `ao` is not found | Install the CLI and check PATH; Go installs usually use `$(go env GOPATH)/bin` |
| A skill needs another tool | Check its dependencies in the installation guide |
| An old skill name fails | Check the [migration guide](docs/MIGRATION.md#skills) and stale copies |

[Report a reproducible issue](https://github.com/boshu2/agentops/issues) with your
runtime version, install method, command or prompt, and observed result.
Share only evidence you are authorized to disclose.

</details>

## Limits

Skills guide agents; installation alone does not enforce their instructions.
A green test suite or an agreeing model can still miss a defect. Missing proof
stays `NOT_PROVEN`. Saving notes does not establish improved outcomes or
automatic knowledge compounding. See [product evidence and limits](PRODUCT.md).

## FAQ

<details>
<summary>CLI, reviewer model and storage questions</summary>

**Do I need the CLI, an orchestrator or several agents?**

No. Start with one coding agent and a skill such as Research, Test or Refactor.
Use checks and CI for ordinary changes. Obtain one fresh, author-distinct
judgment when requested, hard to undo, or uncovered by a deterministic check. The Validate skill
requires `ao`; native independent review does not.

**Must the reviewer use another model provider?**

No. The default is a fresh context from the author's model family. Cross-model
review is an explicit choice; independence still matters.

**Must durable work live in Git?**

No. Keep source in Git, handoffs in your tracker and requested proof in protected
external storage, following each owner's access and retention rules.

</details>

## Beyond AgentOps

Start with one agent and a paved path. When work needs several agents, a factory
can add scheduling, coordination and runtime supervision. Install AgentOps
skills into its agent runtimes to carry the same behavior, testing and review
practices into each task. The factory runs the agents; your checks and any
required independent judgment establish what the result proves.

### Gas City

[Gas City](https://github.com/gastownhall/gascity), from the organization behind
[Beads](https://github.com/gastownhall/beads), provides configurable building
blocks for multi-agent software factories: runtime providers, work routing,
workflow formulas, packs and supervision. AgentOps ships a
[Gas City adapter](skills/using-gc/SKILL.md) and an
[executor integration pack](packs/agentops-executor/pack.toml). Use the adapter
to work through Gas City's native coordinator and observe its runs; workers can
use AgentOps skills for implementation, tests and validation.

### Agentic Coding Flywheel

[Agentic Coding Flywheel](https://agent-flywheel.com) is Jeffrey Emanuel's
([Dicklesworthstone](https://github.com/Dicklesworthstone)) ecosystem of tools
and workflows for operating coding agents. Its
[setup project](https://github.com/Dicklesworthstone/agentic_coding_flywheel_setup)
assembles a multi-agent development environment. You can also adopt individual
tools alongside AgentOps:

| Need | Upstream tool | How it fits |
|---|---|---|
| Block covered destructive shell operations | [Destructive Command Guard (`dcg`)](https://github.com/Dicklesworthstone/destructive_command_guard) | Checks commands before execution through its configured integration. Adds mechanical protection alongside agent guidance. |
| Find an earlier investigation or solution | [Coding Agent Session Search (`cass`)](https://github.com/Dicklesworthstone/coding_agent_session_search) | Indexes and searches agent session histories. Retrieve relevant episodes as evidence for Memory or a new investigation. |
| Turn session evidence into reusable skills | [Meta Skill (`ms`)](https://github.com/Dicklesworthstone/meta_skill) | Can mine selected CASS sessions into skill candidates with source links. Review the guidance and test it on another task before relying on it. |

For example, use CASS to find how a recurring migration failure was resolved.
Use [Memory](skills/memory/SKILL.md) to examine the supported lesson and curate
project context. If the method belongs in a repeatable path,
[Skill Builder](skills/skill-builder/SKILL.md) can help package it and
[Skill Eval](skills/skill-eval/SKILL.md) can measure whether it helps later work.
This connects session history to guidance you can inspect and improve.

Gas City, the Flywheel and these tools are independent projects. AgentOps ships
its own Gas City adapter and pack; install external tools and their skills from
their authors. Follow their native workflows, integrations and distribution terms.

## Contributing

Contributions are welcome: documentation fixes, reproducible bug reports,
tests, CLI improvements and skills. Read the [contribution guide](docs/CONTRIBUTING.md);
to work on skills from a checkout, link them with
[`ao skills link`](docs/install-day2-ops.md#install-source-checkout).

Licensed under [Apache-2.0](LICENSE).
