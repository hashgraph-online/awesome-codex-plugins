<p align="center">
  <img src="assets/devrecap-logo.webp" width="220" alt="DevRecap logo">
</p>

<h1 align="center">DevRecap</h1>

<p align="center">
  <em>Your coding history already knows what you did. DevRecap turns it into a recap.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/jquinteiroo/devrecap?style=flat-square&color=111111&label=stars" alt="GitHub stars">
  <img src="https://img.shields.io/badge/OpenAI%20Plugins%20Directory-live-111111?style=flat-square" alt="Available in the OpenAI Plugins Directory">
  <img src="https://img.shields.io/badge/version-0.3.0-111111?style=flat-square" alt="DevRecap 0.3.0">
  <img src="https://img.shields.io/badge/node-%3E%3D24-111111?style=flat-square" alt="Node.js 24+">
  <img src="https://img.shields.io/badge/license-MIT-111111?style=flat-square" alt="MIT license">
</p>

<p align="center">
  <strong>Codex + Claude + Git → evidence-backed developer recaps.</strong>
</p>

<p align="center">
  <strong>Published in the OpenAI Plugins Directory.</strong><br>
  For Codex CLI, install from the repository marketplace, then run <code>$devrecap</code>.
</p>

---

You know the question.

**“What did I actually work on this week?”**

Then you open GitHub, scroll through commits, search old terminal sessions, try to remember what was finished, what was only investigated, and what is still in progress.

DevRecap reconstructs that work for you.

It reads only the local coding history and Git evidence you explicitly authorize, correlates the evidence, separates completed work from unfinished work, and lets the host AI turn those facts into a polished work report.

**Not a timesheet. Not background monitoring. A recap you explicitly ask for when you need it.**

## Install

DevRecap 0.3.0 is published in the OpenAI Plugins Directory. Directory visibility and the Codex CLI curated catalog can differ by client version, account, or rollout state, so the repository marketplace is currently the reliable CLI installation path.

### Codex CLI — recommended

Add the DevRecap repository marketplace and install the plugin:

```bash
codex plugin marketplace add jquinteiroo/devrecap --ref main
codex plugin add devrecap@devrecap-marketplace
```

Start or restart Codex, then invoke the Skill:

```text
$devrecap
```

If you already added the repository marketplace and want to refresh it first:

```bash
codex plugin marketplace upgrade devrecap-marketplace
codex plugin add devrecap@devrecap-marketplace
```

### Codex UI / Plugins Directory

You can also install it interactively when DevRecap appears in your client catalog:

```text
/plugins
```

Search for **DevRecap**, install it, start a new thread, then run:

```text
$devrecap
```

If DevRecap does not appear in `/plugins`, use the repository marketplace commands above.

### OpenAI curated CLI catalog

Some Codex clients may expose DevRecap directly through the built-in OpenAI curated marketplace. You can inspect the catalog with:

```bash
codex plugin list --available --json
```

If DevRecap is present there, this shorter install also works:

```bash
codex plugin add devrecap@openai-curated
```

If that command returns `plugin devrecap was not found in marketplace openai-curated`, the curated CLI catalog has not exposed DevRecap for that client/account yet. Use the repository marketplace path instead; the plugin package itself is the same public repository release.

Then ask naturally:

```text
Help me remember what I worked on this week.
```

Or:

```text
Me ajuda a lembrar tudo que trabalhei nas últimas duas semanas.
Quero um relatório detalhado em português.
```

On first use, DevRecap requires explicit permission before reading local Codex history, Claude history, or Git evidence.

## What you get

DevRecap is designed to produce a recap you can actually use in a daily, weekly review, 1:1, sprint review, handoff, or performance conversation.

A typical report groups work into meaningful fronts such as:

```text
Executive summary

Main focus
• Contract generation and document workflow
• Tournament API consistency and filtering

Confirmed deliveries
• Evidence-backed completed work

Investigations
• Work that was explored but not proven complete

In progress
• Active work without completion evidence
```

The final HTML report is editorial rather than commit-centric: context and narrative first, raw evidence available when you need to inspect it.

## The rule

> **Evidence first. If DevRecap cannot support a claim from the collected evidence, it must not present it as completed.**

A file edit is not automatically a finished feature.  
A command is not automatically a delivered fix.  
A conversation is not automatically proof that something shipped.

DevRecap combines session evidence with Git history and keeps uncertain work uncertain.

## Before / after

Without DevRecap:

```text
I think I worked on the PDF generation flow...
I also fixed something in the product-selection flow.
And I investigated a bit the issues with the reports.
```

With DevRecap:

```text
This week

Completed
• Improved the contract-generation flow and correlated the work with Git commits.
• Fixed frontend behavior in the product-selection journey.

Investigated
• Report-generation issues that still lacked completion evidence.

In progress
• New user creation in the admin panel.
```

The goal is not to make your week sound busier.

The goal is to make it **accurate, useful, and easy to present**.

## How it works

```text
You invoke $devrecap
        ↓
DevRecap resolves the requested period
        ↓
Authorized Codex + Claude sessions
        +
Read-only Git evidence
        ↓
Normalize events
        ↓
Build meaningful Activities and Workstreams
        ↓
Correlate session activity with Git evidence
        ↓
Build an evidence-only analysis contract
        ↓
Codex / Claude writes the narrative
        ↓
DevRecap validates IDs, status and completion claims
        ↓
Editorial HTML report
```

The coding agent is the writing layer.

The DevRecap CLI is the factual layer.

That separation is intentional.

## Privacy model

DevRecap is **explicit-invocation only**.

It does not automatically scan your repositories, watch your filesystem, or monitor your work in the background.

Before local collection, the user chooses which sources are allowed:

```text
Codex history     optional
Claude history    optional
Git               optional, read-only
```

Disabled sources are not invoked.

Git collection is guarded as read-only. DevRecap does not commit, push, checkout, reset, merge, rebase, or modify repositories as part of report generation.

See [PRIVACY.md](PRIVACY.md) for the full privacy model.

## Skill workflow

The public Codex plugin ships the canonical Skill at:

```text
skills/devrecap/SKILL.md
```

Claude support is also available in the repository:

```text
.claude/skills/devrecap/SKILL.md
```

The AI-first flow is:

```text
prepare
   ↓
.devrecap/run.json
   ↓
host AI analyzes contract.facts only
   ↓
.devrecap/analysis.json
   ↓
validate
   ↓
render
   ↓
reports/derecap-YYYY-MM-DD.html
```

The agent is instructed to:

- analyze only facts exposed by DevRecap;
- group related Activities into coherent work fronts;
- reference valid activity IDs;
- never promote `in_progress`, `blocked`, or `unknown` work to completed;
- prefer context, outcomes, fixes, features, investigations, validation and blockers over command-by-command narration;
- avoid exposing raw transcripts, credentials, or secrets.

## Sources

### Codex

DevRecap can collect authorized local Codex session history inside the requested time range.

### Claude

Authorized Claude coding sessions can be included in the same recap, allowing work performed across agents to appear in one report.

### Git

DevRecap correlates relevant work with read-only Git evidence.

Commit evidence is especially useful for distinguishing:

```text
worked on it
```

from:

```text
there is evidence that this work was completed
```

## Local development

The repository marketplace is the most reliable way to use DevRecap from Codex CLI today. Clone the repository only if you want to develop or inspect the project locally.

### Requirements

- **Node.js 24 LTS or newer**
- **Git**
- Optional: **Chrome / Chromium** for direct PDF generation

Clone:

```bash
git clone https://github.com/jquinteiroo/devrecap.git
cd devrecap
npm run setup
```

Run the CLI from the repository:

```bash
npm run recap -- "this week"
```

Useful commands:

```bash
npm run setup
npm test
npm run typecheck
npm run smoke
npm run dev
```

## Deterministic CLI fallback

The direct CLI can still generate a deterministic recap without host-AI synthesis:

```bash
devrecap today
devrecap week
devrecap remember "last 14 days"
```

The preferred experience for polished reports is the Skill, because Codex or Claude can turn the structured Activities into a more natural narrative while DevRecap remains responsible for factual validation.

## Architecture

```text
devrecap/
├── plugin.json
├── skills/
│   └── devrecap/
│       └── SKILL.md
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── .claude/
│   └── skills/
│       └── devrecap/
│           └── SKILL.md
├── apps/
│   ├── cli/
│   ├── server/
│   └── web/
├── packages/
│   ├── collectors/
│   ├── activity-engine/
│   ├── report-engine/
│   └── shared/
├── scripts/
└── tests/
```

## Why evidence matters

Developer activity is messy.

A single task may appear across:

- several Codex sessions;
- a Claude session;
- multiple files;
- failing tests;
- a later successful test;
- one or more Git commits.

A naive summary sees these as unrelated events.

DevRecap tries to reconstruct the **workstream**.

That makes the output useful for:

- daily standups;
- weekly recaps;
- sprint reviews;
- performance reviews;
- project handoffs;
- personal work journals;
- remembering what happened after a long week.

## Principles

DevRecap is built around a few simple ideas:

1. **Evidence over memory.**
2. **Outcomes over command logs.**
3. **Uncertainty should stay uncertain.**
4. **Local development history is useful context, not a productivity score.**
5. **The agent should improve the writing — never invent the facts.**

## Support and contributing

Issues, ideas, integrations, report styles, collectors, and improvements are welcome.

- [Open an issue](https://github.com/jquinteiroo/devrecap/issues)
- [Privacy policy](PRIVACY.md)
- [Terms of service](TERMS.md)
- [Support](SUPPORT.md)

If DevRecap becomes useful in your workflow, consider starring the repository. It helps other developers discover the project.

## License

MIT. [LICENSE](LICENSE)

---

<p align="center">
  <strong>You already did the work.</strong><br>
  DevRecap helps you remember what the evidence says you did.
</p>
