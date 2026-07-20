# AgentPack

<p align="center">
  <img src="docs/assets/agentpack-symbol.png" alt="AgentPack symbol: a compact map pack for coding agents" width="160">
</p>

<p align="center">
  <strong>Make AI coding work easier to understand, verify, and continue.</strong>
</p>

<p align="center">
  AgentPack is the local, agent-neutral reliability layer for AI software development.
</p>

<p align="center">
  It gives the coding agents you already use task-aware project context, visible workflow state,<br>
  validation guidance, review evidence, and continuity across sessions.
</p>

<p align="center">
  <a href="#get-started"><strong>Get started</strong></a>
  &nbsp;&middot;&nbsp;
  <a href="docs/index.md">Technical docs</a>
</p>

<p align="center">
  <a href="https://deepwiki.com/vishal2612200/agentpack"><img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki"></a>
  <a href="https://github.com/vishal2612200/agentpack"><img alt="AgentPack" src="docs/assets/agentpack-badge.png"></a>
  <a href="https://github.com/vishal2612200/agentpack"><img alt="AgentPack review" src="docs/assets/agentpack-review-badge.png"></a>
  <a href="https://pypi.org/project/agentpack-cli/"><img alt="PyPI version" src="https://img.shields.io/pypi/v/agentpack-cli.svg?cacheSeconds=300"></a>
  <a href="https://pepy.tech/projects/agentpack-cli"><img alt="PyPI downloads" src="https://static.pepy.tech/personalized-badge/agentpack-cli?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads"></a>
  <a href="https://www.npmjs.com/package/@vishal2612200/agentpack"><img alt="npm version" src="https://img.shields.io/npm/v/@vishal2612200/agentpack.svg?cacheSeconds=300"></a>
  <a href="https://www.npmjs.com/package/@vishal2612200/agentpack"><img alt="npm downloads" src="https://img.shields.io/npm/dm/@vishal2612200/agentpack.svg"></a>
  <a href="https://github.com/vishal2612200/agentpack/releases/latest"><img alt="Release evidence" src="https://img.shields.io/github/v/release/vishal2612200/agentpack?label=release%20evidence"></a>
</p>

<p align="center">
  <a href="https://github.com/vishal2612200/agentpack/actions/workflows/publish.yml"><img alt="PyPI trusted publishing" src="https://img.shields.io/badge/PyPI-trusted%20publishing-blue"></a>
  <a href="https://github.com/vishal2612200/agentpack/actions/workflows/publish-npm.yml"><img alt="npm provenance" src="https://img.shields.io/badge/npm-provenance-blue"></a>
  <a href="https://hol.org/registry/plugins/agentpack%2Fagentpack"><img alt="HOL trust score" src="https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dagentpack%252Fagentpack%26metric%3Dtrust%26style%3Dflat"></a>
  <a href="https://hol.org/registry/plugins/agentpack%2Fagentpack"><img alt="HOL security score" src="https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Dagentpack%252Fagentpack%26metric%3Dsecurity%26style%3Dflat"></a>
  <a href="https://github.com/vishal2612200/agentpack/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/vishal2612200/agentpack/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://www.gnu.org/licenses/agpl-3.0.en.html"><img alt="License: AGPL v3" src="https://img.shields.io/badge/License-AGPL%20v3-blue.svg"></a>
</p>

<p align="center">
  <code>task-aware context</code>
  <code>workflow state</code>
  <code>cited review</code>
  <code>local memory</code>
  <code>agent-neutral</code>
</p>

<p align="center">
  <img src="docs/assets/dashboard/workspace-desktop.png" alt="AgentPack workspace showing repository context, active work, proof, and project state" width="1100">
</p>

<p align="center"><sub>One local workspace for repository context, active work, review evidence, and continuity.</sub></p>

## The Missing Project Layer

AI coding models can generate code, but a software project is more than the
files in a repository. The work also depends on the current task, ownership
boundaries, project rules, prior decisions, expected tests, current changes,
and review state. Those details do not automatically follow work between
agents or sessions.

That gap matters because an agent can produce plausible code while starting
from stale task state, overlooking a nearby test, missing a local rule, or
continuing assumptions from an earlier session. More model capability does not
by itself make the surrounding project evidence consistent or inspectable.

AgentPack keeps that evidence in one local system and presents a task-relevant
view around the agent you choose. It prepares context, tracks workflow state,
exposes validation and review evidence, and carries structured handoffs
forward. It is not a coding agent, a hosted context index, or a correctness
oracle.

## One Product Across the Workflow

AgentPack connects the work before an edit, while it is active, during review,
and when another session needs to continue it. These are not separate products
or isolated command families. They share the same local repository, task,
session, context, evidence, and memory state.

### Prepare with project evidence

AgentPack starts from a concrete task and the repository as it exists now. It
ranks likely relevant files and tests, applies repository rules and matching
skills, surfaces useful commands and warnings, and maps semantic relationships
where language support is available.

Selection receipts explain why files were included or omitted. Token guidance
keeps the starting context bounded, while targeted retrieval lets an agent ask
for more evidence when the initial map is not enough. The result is an
inspectable starting point, not a guarantee that every selected file is right.

### Coordinate active work

Task and session state, context freshness, token guidance, and same-worktree
overlap warnings stay connected. The local dashboard makes the repository,
active work, queued work, proof, and handoff state visible without requiring a
hosted project index.

Structured handoffs carry acceptance criteria, completed and remaining work,
decisions, blockers, changed files, and validation evidence into another
supported session. A handoff transfers bounded project state; it does not
pretend to recreate the original host conversation.

### Verify with source-backed evidence

AgentPack links context to focused validation guidance and review evidence. Its
staged PR review separates repository understanding, candidate findings,
criticism, and publishing so unsupported findings can be rejected before they
become inline comments.

The PR comment resolution workflow follows a validate, plan, fix, verify, and
reply loop. Plans and replies require source citations, validation status, and
the current PR head, making it harder to close a comment with an unsupported
claim or stale location.

### Continue without turning memory into truth

AgentPack records local task events, episodes, reusable procedures, learning
feedback, and observer signals. Those records can explain why a file was
selected, suggest relevant prior work, or surface repeated weak spots in the
dashboard.

Skill review extends the same reliability approach to agent instructions. It
audits a skill and generates balanced trigger and non-trigger evaluation cases
so activation behavior can be checked instead of assumed.

AgentPack does not edit source code or replace the developer's chosen agent.
The agent still reads the code, makes the change, runs the checks, and exercises
judgment. AgentPack makes the surrounding project state explicit and
inspectable.

## How AgentPack Fits Around Existing Tools

AgentPack is a project layer around tools that already own important parts of
software delivery. It connects their evidence without claiming to replace
them.

| Existing surface | AgentPack's role |
|---|---|
| Coding agents | Prepare task-aware context, workflow state, and evidence for the agent that will reason and edit. |
| IDE and repository search | Provide a ranked starting map and related-file evidence; direct search remains available for verification and exploration. |
| Git, tests, and CI | Surface likely validation paths and record results; the underlying diff and test output remain authoritative. |
| Pull requests | Prepare cited review artifacts and comment-resolution evidence against an immutable base and head. |
| Team trackers | Carry local task and handoff context without replacing planning, ownership, approval, or governance systems. |

This separation is deliberate. AgentPack can improve how project evidence is
prepared and carried forward, but correctness still comes from source
inspection, testing, runtime behavior, and human or agent judgment.

## For Developers and Teams

### For developers

AgentPack gives an individual developer a concrete starting map, visible task
state, focused validation guidance, and a structured way to continue work in a
later session. It is especially useful when the repository is large enough
that orientation, ownership, and test discovery are part of the task.

The workflow remains compatible with normal engineering habits. Developers can
use direct search, inspect any source file, ignore an advisory suggestion, run
different checks, or stop using AgentPack for a task where the exact change is
already obvious.

### For technical leads and teams

Technical leads and teams can inspect consistent local task context, freshness,
overlap warnings, validation evidence, and cited review artifacts across
supported agent entry points. That makes the state around AI-assisted work more
visible without claiming that every host has the same integration depth.

AgentPack coordination is advisory. It does not assign people, enforce policy,
approve changes, or provide hard multi-agent locks. Existing ownership,
security, review, and release processes remain in control.

### Where it fits best

AgentPack is most useful when:

- a repository or monorepo has enough structure that file and test discovery are non-trivial;
- work moves between multiple agent sessions or supported hosts;
- local rules and reusable skills should follow the task;
- PR review needs reproducible understanding, citations, and validation evidence;
- teams want local continuity without uploading the repository to a hosted index.

For a tiny repository, a one-shot read-only question, or a task where the exact
files are already known, AgentPack can remain a light preflight or stay out of
the way.

## Works With Existing Agents

AgentPack supports Codex, Claude Code, Cursor, Windsurf, Antigravity, MCP
clients, CI, and generic Markdown workflows. Integration depth varies by host;
each surface is an entry point into the same local CLI and MCP engine rather
than a separate product.

| Entry point | Product role |
|---|---|
| MCP-capable agents | Pull readiness, current context, deltas, related files, task maps, and cited PR evidence as needed. |
| Agent rules and hooks | Keep task setup, freshness checks, and repository guidance near the host workflow. |
| Local CLI | Own setup, diagnostics, explicit workflows, CI integration, and human inspection. |
| Dashboard | Present repository state, active work, proof, semantic relationships, memory influence, and handoffs visually. |
| Markdown artifacts | Provide a portable, auditable fallback for non-MCP agents, CI logs, and manual review. |

See [integrations](docs/integrations.md) for setup, capabilities, and explicit
advisory-versus-enforced status by host. Plugin and IDE surfaces remain thin
entry points into AgentPack rather than independent implementations of context
or review logic.

## Evidence Through Review

A reliability layer should expose why it made a recommendation and what proved
the resulting change. AgentPack keeps evidence visible at several points:

- selection receipts record why context candidates were included or omitted;
- freshness metadata ties context to the active task and repository snapshot;
- citation manifests connect packed claims to source locations and hashes;
- review artifacts keep understanding, findings, criticism, and approved output separate;
- resolution artifacts connect comment dispositions, fixes, validation, and cited replies;
- benchmark artifacts show the exact scope and limits of published quality claims.

These artifacts are inputs to engineering judgment, not replacements for it.
They are designed to be inspected, checked, regenerated, or discarded when the
repository has moved.

## Local and Auditable

### Core local path

Core scan, route, pack, stats, explain, and benchmark operations do not require
hosted indexing, embeddings, or model API calls. Generated context, receipts,
task state, snapshots, and memory are stored locally under `.agentpack/` so
they can be inspected or removed.

Repository ignore rules, redaction, and bounded packs help control what enters
generated context. Context packs can still contain source excerpts, task text,
paths, hashes, and repository metadata, so they should be reviewed before being
shared outside the machine.

### Explicit network paths

AgentPack does not require repository upload for its core analysis. Explicit
GitHub operations, optional issue enrichment, package and release checks, and
workflows that invoke external agents or providers can use the network. Those
actions are separate from the local context engine and should be evaluated
under the credentials and policies of the external system they call.

### Trust order

Generated context, memory, observer state, and integration hints are advisory.
Source files, diffs, tests, runtime evidence, and PR state remain the source of
truth. Native host integrations are also advisory unless a host provides a
blocking API that can enforce behavior before an edit.

Read the [privacy model](docs/privacy.md), [technical architecture](docs/architecture.md),
[data flow](docs/data-flow.md), [threat model](docs/threat-model.md), and
[known limitations](docs/limitations.md).

## Proof, Not Promises

AgentPack's current public benchmark measures file selection against files
changed in historical public commits. Each sampled case checks out the parent
commit, uses the commit subject as the task, and compares selected context with
the files that were actually changed.

It is evidence for the quality of a ranked starting map, not a measurement of
downstream agent outcomes.

| Public file-selection signal | Current result |
|---|---:|
| Historical commit cases | 107 |
| Average recall | 67.2% |
| Average token precision | 50.6% |

Source: [`benchmarks/results/2026-07-06-public.md`](benchmarks/results/2026-07-06-public.md).
Methodology: [benchmarking guide](docs/benchmarking.md).

### What this evidence supports

The public artifact supports a narrow claim: AgentPack can be evaluated as a
ranked file-selection system against historical repository changes. It also
exposes misses and slice-level regressions so ranking changes can be compared
against the same corpus.

### What it does not support

These results do not establish reduced tool calls, lower cost, faster
completion, or improved task success. No public AgentPack-versus-no-AgentPack
E2E outcome report is published yet; progress is tracked in the
[E2E A/B status](benchmarks/results/e2e-ab-status.md).

## Get Started

AgentPack requires Python 3.10 or newer. Install the CLI with `pipx`, then
activate it inside a repository:

```bash
pipx install agentpack-cli
agentpack quickstart
agentpack start "fix auth token expiry"
agentpack next
```

`quickstart` initializes the local project layer, `start` records the active
task, and `next` asks AgentPack for the current safe action. MCP-capable agents
can use the same local state directly after integration setup.

The activation path creates local project state and connects the detected agent
integration. From there, the agent can pull current context, inspect focused
evidence, and continue with normal source reads and tests. The full command and
integration surfaces remain in the technical documentation.

<p align="center">
  <img src="docs/assets/agentpack-demo.gif" alt="Terminal demo of AgentPack context, review, learning, memory, and validation workflows" width="840">
</p>

<p align="center">
  <a href="docs/assets/agentpack-demo.mp4">Watch the MP4 demo</a>
</p>

## Technical Docs

| Need | Start here |
|---|---|
| Product internals and data flow | [Architecture](docs/architecture.md) and [how AgentPack works](docs/how-agentpack-works.md) |
| Setup across agents and hosts | [Integrations](docs/integrations.md) and [agent plugins](docs/agent-plugins.md) |
| CLI and MCP behavior | [Command reference](docs/commands.md) and [MCP context engine](docs/mcp-context-engine.md) |
| Dashboard contracts | [Dashboard v2](docs/dashboard-v2.md) |
| Runtime state, handoffs, and memory | [Runtime loop](docs/runtime-loop.md) |
| Privacy and security | [Privacy](docs/privacy.md), [data flow](docs/data-flow.md), and [threat model](docs/threat-model.md) |
| Quality evidence | [Benchmarking](docs/benchmarking.md) and [limitations](docs/limitations.md) |

Start at the [technical documentation home](docs/index.md) for the complete
guide.

## Status

Alpha: `0.4.0`.

Python and JavaScript/TypeScript currently have the strongest support. APIs may
change before 1.0. Platform targets are macOS, Linux, and Windows PowerShell
with Git for Windows.

PyPI package: `agentpack-cli`. npm package: `@vishal2612200/agentpack`. CLI
command: `agentpack`. This project is unrelated to AgentPack dataset papers or
other repositories with the same name.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup, validation, and pull request
expectations. Community behavior is covered by
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

New contributors can start with
[`good first issue`](https://github.com/vishal2612200/agentpack/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22good%20first%20issue%22),
[`help wanted`](https://github.com/vishal2612200/agentpack/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22help%20wanted%22),
or [`first-timers-only`](https://github.com/vishal2612200/agentpack/issues?q=is%3Aissue%20is%3Aopen%20label%3A%22first-timers-only%22)
issues.

## License

GNU Affero General Public License v3.0
