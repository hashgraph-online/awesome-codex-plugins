<p align="center">
  <img src="./assets/hero.svg" alt="Codex Quota Optimizer" width="100%" />
</p>

<p align="center">
  <a href="./README.zh-CN.md"><strong>简体中文</strong></a> · <strong>English</strong>
</p>

<p align="center">
  <a href="./LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-111827.svg"></a>
  <img alt="Codex Skill" src="https://img.shields.io/badge/Codex-Skill-111827.svg">
  <img alt="Codex Plugin" src="https://img.shields.io/badge/Codex-Plugin-111827.svg">
  <img alt="Plus & Pro" src="https://img.shields.io/badge/ChatGPT-Plus%20%2F%20Pro-111827.svg">
  <img alt="No telemetry" src="https://img.shields.io/badge/telemetry-none-0F766E.svg">
</p>

# Spend less Codex allowance. Keep the engineering quality.

**Codex Quota Optimizer** is an open-source Codex Skill + Plugin that reduces avoidable Plus / Pro usage while keeping the task correct. The same canonical Skill powers both direct Skill installs and Plugin distribution.

Codex does not only spend allowance on writing code. It can also spend it on **re-reading a repository, using a stronger model than necessary, over-reasoning, running broad tests too early, spawning unnecessary subagents, and doing work outside the requested scope**.

This Skill gives Codex a simple policy:

> **Use the cheapest reliable execution path first. Escalate only when the evidence says it is necessary.**

It does **not** bypass limits, scrape private quota data, or weaken verification to fake savings.

---

## See the difference in 30 seconds

| Typical waste | With Codex Quota Optimizer |
|---|---|
| Use a powerful model for every task | Classify task complexity and route to the lowest adequate model |
| Read large parts of the repo “just in case” | Search first, read only the change surface and direct dependencies |
| Use high reasoning by default | Start low; increase reasoning only when ambiguity requires it |
| Run the full test suite after small edits | Verify in layers: touched file → focused test → package → full suite |
| Spawn subagents because they are available | Use them only when parallel decomposition genuinely helps |
| Refactor nearby code while fixing one issue | Make the smallest coherent patch that satisfies acceptance criteria |
| Let a stronger model rediscover everything | Compress known facts before escalating |

<p align="center">
  <img src="./assets/optimization-loop.svg" alt="Codex Quota Optimizer workflow" width="96%" />
</p>

---

## v0.2 — Zero-friction usage governor

> **The optimizer should not become the overhead.**

v0.2 turns the original Skill policy into a lightweight usage governor while keeping normal Codex execution unobstructed.

| v0.2 capability | How it behaves |
|---|---|
| **Task Classifier** | Classifies XS → XL inside the existing reasoning turn; the optional CLI can also classify locally with heuristics |
| **Soft Session Budget** | Suggests discovery, reasoning, verification and subagent scope without blocking execution |
| **Local Usage Journal** | Stores task-level metadata locally under `~/.cqo`; no telemetry and no private account scraping |
| **Usage Audit** | Records local change surface and CQO policy guardrails without inventing token-savings percentages |
| **`cqo` CLI** | Optional `start / status / audit / history / doctor` inspection layer; Codex does not depend on it |

CQO itself adds **no automatic model call, no network request, no blocking budget gate, and no automatic subagent**. If correctness requires more context or verification than the suggested budget, Codex should simply continue.

---

## Install

### Option A — One-line Skill install · recommended

Install the Skill with the cross-agent Skills CLI:

```bash
npx skills add ctdaniel/codex-quota-optimizer --skill codex-quota-optimizer
```

This is the fastest path for Codex users and also makes the Skill discoverable through the wider Skills ecosystem.

The Skill works immediately; the local `cqo` CLI is optional. If you also want the short `cqo` command after a Skills CLI install:

```bash
mkdir -p ~/.local/bin
chmod +x ~/.agents/skills/codex-quota-optimizer/scripts/cqo.py
ln -sfn ~/.agents/skills/codex-quota-optimizer/scripts/cqo.py ~/.local/bin/cqo
```

If `~/.local/bin` is not in your shell `PATH`, you can still run the script directly with Python.

### Option B — Direct global install

Use the repository installer across all of your Codex projects:

```bash
git clone https://github.com/ctdaniel/codex-quota-optimizer.git
cd codex-quota-optimizer
./install.sh
```

It installs the Skill to:

```text
~/.agents/skills/codex-quota-optimizer
```

and creates the optional CLI shortcut at:

```text
~/.local/bin/cqo
```

Codex should detect the Skill automatically. Restart Codex if it does not appear immediately.

### Option C — Repository-local

Copy the canonical Skill source:

```text
skills/codex-quota-optimizer/
```

into your project's:

```text
.agents/skills/codex-quota-optimizer/
```

Commit it with the repository if you want the whole team to use the same usage policy.

> Codex officially supports user-level Skills in `~/.agents/skills` and repository Skills in `.agents/skills`. See the [OpenAI Skills documentation](https://developers.openai.com/docs/build-skills).

---

## Use it

### 1. Explicit invocation

In Codex CLI / IDE, type `$` and select the Skill, or invoke it directly:

```text
$codex-quota-optimizer
Fix this checkout bug. Keep the implementation reliable, but minimize unnecessary Codex usage.
```

### 2. Natural language

Implicit invocation is enabled, so requests like these can trigger it automatically:

```text
Please save my Codex quota while implementing this feature.
```

```text
My Plus allowance is getting low. Finish this with the smallest reliable usage footprint.
```

```text
Use the cheapest adequate model and focused tests first. Escalate only if needed.
```

### 3. Emergency mode

When you tell Codex that your allowance is nearly exhausted, the Skill becomes more aggressive about saving usage:

- no optional refactors,
- no broad repository exploration,
- no unnecessary subagents,
- one implementation path,
- cheapest adequate model,
- focused verification first.

Correctness and explicit acceptance criteria still take priority.

---

## What the Skill optimizes

<table>
<tr>
<td width="50%" valign="top">

### 🧠 Model & reasoning routing

Classifies work from **XS → XL**, then starts with the least expensive model / reasoning level that should reliably handle it.

It escalates only when the task becomes genuinely ambiguous, cross-cutting, risky, or hard to debug.

</td>
<td width="50%" valign="top">

### 🔎 Context control

Uses targeted search, current diffs, project instructions and compact repository maps before opening large amounts of code.

The goal is to avoid paying repeatedly for repository rediscovery.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### ✂️ Minimal change surface

Keeps edits focused on the acceptance criteria and avoids unrelated cleanup, dependency upgrades and “while I'm here” refactors.

</td>
<td width="50%" valign="top">

### ✅ Layered verification

Runs the smallest relevant checks first and expands verification only when the scope or risk justifies it.

</td>
</tr>
<tr>
<td width="50%" valign="top">

### 🧩 Subagent discipline

Parallel agents can multiply work and context. The Skill uses them only when a large task can truly benefit from independent parallel workstreams.

</td>
<td width="50%" valign="top">

### 🧾 Checkpoint compression

For long tasks, Codex keeps a compact handoff state — goal, decisions, touched files, tests, next action — instead of repeatedly reconstructing the same context.

</td>
</tr>
</table>

---

## Model routing philosophy

Current OpenAI guidance positions the model family roughly like this:

| Task shape | Preferred role | Current example | Starting reasoning |
|---|---|---|---|
| Mechanical / repetitive | Fastest, most economical | GPT-5.6 Luna | Low |
| Everyday coding | Balanced | GPT-5.6 Terra | Low / Medium |
| Complex, open-ended work | Deep reasoning | GPT-5.6 Sol | Medium |
| Hardest multi-step / multi-tool work | Strongest available | GPT-6 Astra | As needed |

The exact model lineup and plan availability can change, so the Skill **routes by capability role first, model name second**. It does not hard-code a fixed Plus or Pro message count.

OpenAI also notes that higher reasoning levels consume more time/tokens, and recommends increasing reasoning when the task actually needs deeper analysis. See [Codex model guidance](https://developers.openai.com/docs/models).

---

## Verification ladder

```text
Level 1     touched-file checks
    ↓
Level 2     closest focused behavior test
    ↓
Level 3     package / module typecheck, lint or tests
    ↓
Level 4     full suite / release gate
```

A local change should not automatically pay the cost of Level 4.

---

## Local tools

The Skill works without any helper script. These tools are optional and local-only.

### Compact repository snapshot

```bash
python skills/codex-quota-optimizer/scripts/repo_snapshot.py --compact
```

Produces a compact project map while ignoring common generated/vendor directories such as `node_modules`, `dist`, `.next`, `coverage`, and `.venv`.

### Change-scope analyzer

```bash
python skills/codex-quota-optimizer/scripts/change_scope.py
```

Summarizes the current Git change surface and suggests a sensible verification level.

### Optional `cqo` usage governor CLI

The CLI never sits in the Codex runtime path. Use it only when you want local task budgeting/history:

```bash
cqo start "Fix the checkout bug" --mode economy
cqo status
cqo audit
cqo history
cqo doctor
```

It uses the Python standard library only, performs no network requests, and writes task-level state to `~/.cqo` (or `CQO_HOME`).

If the `cqo` shortcut is not installed, run:

```bash
python ~/.agents/skills/codex-quota-optimizer/scripts/cqo.py status
```

Run `cqo doctor` any time to check Python compatibility, Skill installation, local journal writability, Git availability, and whether the `cqo` shortcut is on PATH — with zero network checks.

The repository snapshot and change-scope scripts are also local-only and dependency-light.

---

## Modes

| Mode | Designed for | Behavior |
|---|---|---|
| **Economy** | Plus, long coding sessions, lower remaining allowance | strict scope, economical model first, focused checks |
| **Balanced** | Pro or normal daily development | balanced model first, deeper model when justified |
| **Emergency** | allowance nearly exhausted | one path, no optional work, minimum reliable exploration and verification |

These are **behavioral budgets**, not fake quota counters.

---

## Benchmarking without fake savings

v0.2.2 adds a paired benchmark framework for comparing **baseline Codex vs CQO** without inventing hidden-token or quota-savings numbers.

Two modes are supported:

- **Controlled** — same starting model/reasoning on both sides, isolating context, verification, repeated exploration and Subagent discipline.
- **Full-policy** — CQO may use its own routing policy; the actual model role/reasoning must be recorded.

The quality gate comes first: **a matched pair only contributes efficiency deltas when both runs pass the same acceptance criteria**.

Observable metrics can include files inspected, searches, focused/broad checks, Subagents, model escalations, repeated reads, and wall time. Unknown values are omitted instead of guessed.

```bash
python benchmarks/report.py path/to/results.jsonl --format markdown
```

See the full [Benchmark methodology](./benchmarks/README.md) · [中文说明](./benchmarks/README.zh-CN.md).

> The project intentionally ships the measurement method before publishing savings claims.

---

## What it deliberately does not do

- ❌ bypass or evade OpenAI usage limits
- ❌ claim to know your exact remaining allowance when Codex does not expose it
- ❌ scrape private account / usage pages
- ❌ collect credentials
- ❌ send telemetry
- ❌ reduce correctness just to make a usage number look smaller

Plus and Pro usage rules can change. OpenAI currently notes that supported agentic features can share an allowance, so current account usage / reset state should be checked in the product's usage UI when it matters. See the [OpenAI Help Center](https://help.openai.com/en/articles/12642688-using-credits-for-flexible-usage-in-chatgpt-freegopluspro).

---

## Project structure

```text
codex-quota-optimizer/
├── plugin.json                    # portable Agent Plugin manifest
├── .codex-plugin/
│   └── plugin.json                # Codex compatibility manifest
├── skills/
│   └── codex-quota-optimizer/     # single canonical Skill source
│       ├── SKILL.md
│       ├── agents/openai.yaml
│       ├── references/
│       └── scripts/
│           ├── cqo.py             # optional local usage governor CLI
│           ├── change_scope.py
│           └── repo_snapshot.py
├── benchmarks/                    # paired baseline/CQO benchmark framework
├── tests/                         # standard-library CLI + benchmark tests
├── assets/                        # Plugin icon + README visuals
├── examples/
├── install.sh                     # installs Skill + optional cqo shortcut
└── README.zh-CN.md
```

---

## Roadmap

- [x] Local **Usage Journal** for task-level observations — no private account scraping
- [x] **Task Classifier** output: task size, recommended model role, reasoning, verification scope
- [x] **Soft Session Budget** for discovery / coding / verification work
- [x] End-of-task **Usage Audit** with honest task-level local observations
- [ ] Framework-aware focused-test discovery
- [x] Plugin packaging for dual Skill / Plugin distribution
- [x] HOL Codex Plugin Catalog listing
- [x] One-line Skills CLI installation
- [x] Paired **Benchmark Framework** comparing baseline and CQO behavior
- [ ] Publish measured real-world benchmark case set

Ideas and PRs are welcome. See [CONTRIBUTING.md](./CONTRIBUTING.md).

---

## Why open source?

The optimization policy should be inspectable.

You should be able to see exactly what the Skill tells Codex to do, change the policy for your own workflow, and contribute better heuristics as Codex evolves.

No black-box quota tricks — just better engineering discipline for agentic coding.

---

## License

MIT © 2026

If this Skill saves you meaningful Codex usage, a ⭐ helps more people find it.