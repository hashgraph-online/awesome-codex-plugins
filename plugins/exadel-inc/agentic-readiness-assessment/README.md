# Agentic Readiness Assessment

![Exadel AI Agentic Readiness Assessment](banner.png)

**Agentic Readiness Assessment** is an agent plugin that evaluates a software repository for readiness to be developed and maintained by AI coding agents. It inspects the repository in place and produces an evidence-based readiness scorecard together with actionable recommendations.

Built by [Exadel](https://exadel.com/).

## Description

The assessment establishes, with evidence, whether an AI coding agent can independently understand this repository, find the right change points, build a reproducible environment, validate its work, and prepare a change for delivery.

It scores **14 areas**, weighted, for an applicable maximum of 105 points:

| # | Area | Max |
|---|---|---:|
| 1 | Agent guidance and navigation | 10 |
| 2 | Reproducible environment and dependency setup | 10 |
| 3 | Build, package, render, or deliverable validation | 10 |
| 4 | Lint, format check, typecheck, static analysis, or policy validation | 10 |
| 5 | Unit or component tests | 10 |
| 6 | Integration, contract, or functional tests | 5 |
| 7 | Runtime, API, CLI, or local-preview validation | 5 |
| 8 | Browser or UI validation | 5 |
| 9 | Coverage and feedback-loop quality | 5 |
| 10 | CI enforcement and parity with local validation | 10 |
| 11 | Safety, test isolation, artifacts, and cleanup | 5 |
| 12 | Delivery workflow from task through review or PR | 5 |
| 13 | Agent guardrails and permission scoping | 10 |
| 14 | Context economy | 5 |

Areas that do not apply to the repository's archetype are marked N/A and subtracted from the maximum, so the normalized score stays comparable across different kinds of repository.

**Three gates sit above the score.** Gate 1 anchors on setup, Gate 2 on the deliverable, Gate 3 on whichever area holds the archetype's primary verification surface. A gate passes only when its anchor area is fully verified, so a high average can never hide a failed gate.

**Evidence, not configuration.** A command that was not executed is a claim. The assessment runs safe commands and records each one with its working directory, result and artifacts. A capability is verified only when a check proved it, never because a config file mentions it.

**A probe proves the loop.** One small reversible edit confirms the repository can actually take a change from edit to green, then it is reverted. Nothing else is modified.

**Guardrails have a hard cap.** A permission bypass, a blanket allow-all policy, an unguarded secret file or a committed plaintext credential caps area 13 at 2 regardless of what else is in place, and each one becomes its own P0 or P1 fix record. Paths are reported, values never are.

The run produces a status of **Ready**, **Partially ready** or **Not ready**, paired with a verification confidence of High, Medium or Low, so a weak score and a weakly-evidenced score never read the same.

The plugin ships a single Agent Skill, [`agentic-readiness-assessment`](skills/agentic-readiness-assessment/SKILL.md). The skill runs entirely locally: it reads the repository in your working directory, requires no backend or MCP server, and sends no repository contents anywhere.

## Supported clients

This is a skill written in the open [Agent Skills](https://agentskills.io/specification) format. It includes native manifests for Cursor-compatible Agent Plugins, Codex, and Claude Code:

- [`plugin.json`](plugin.json) for the portable [Agent Plugins](https://agent-plugins.org/specification) format used by Cursor;
- [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) for ChatGPT and Codex;
- [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) for Claude Code.

The three packages point to the same skill and require no backend or MCP server.

Clients that read the Agent Skills format directly, including Gemini CLI, Antigravity, Zed, Warp, Windsurf and Amp, load the skill from `skills/agentic-readiness-assessment/` with no conversion. A [`gemini-extension.json`](gemini-extension.json) manifest is present for Gemini CLI's extension installer.

## Installation

### Cursor

Once published, install it from the [Cursor marketplace](https://cursor.com/marketplace).

### Claude Code

Add this repository as a marketplace and install the plugin:

```sh
claude plugin marketplace add exadel-inc/agentic-readiness-assessment
claude plugin install agentic-readiness-assessment@exadel-agent-plugins
```

To try it without adding a marketplace, clone the repository and load it directly with `claude --plugin-dir .`.

### ChatGPT and Codex

Public installation will be available after OpenAI review and publication. The native Codex package is already present in the repository for submission and local packaging.

### Gemini CLI

```sh
gemini extensions install https://github.com/exadel-inc/agentic-readiness-assessment
```

Or install the skill on its own, without the extension manifest:

```sh
gemini skills install https://github.com/exadel-inc/agentic-readiness-assessment --path skills/agentic-readiness-assessment
```

### GitHub Copilot CLI

```sh
copilot plugin marketplace add exadel-inc/agentic-readiness-assessment
```

### JetBrains Junie

Open `/extensions`, go to the Marketplaces tab, choose Add marketplace and paste the repository URL. Junie reads the `.claude-plugin/marketplace.json` in this repository.

### Any client that reads Agent Skills

```sh
npx skills add exadel-inc/agentic-readiness-assessment
```

For Zed, Warp, Windsurf, Amp and anything else that discovers skills on the filesystem, copy `skills/agentic-readiness-assessment/` into the client's skills directory, usually `.agents/skills/` in the repository you want to assess.

### From source

Clone the repository and point a compatible client at the repository root:

```sh
git clone https://github.com/exadel-inc/agentic-readiness-assessment.git
```

## Getting Started

Ask your agent for an assessment from inside the repository you want to evaluate:

- "Run an agentic readiness assessment on this repository."
- "Generate an AI-readiness scorecard for this codebase."
- "How ready is this repo for AI coding agents, and what should we fix first?"

There are no arguments or configuration. The skill reads the repository in your current working directory.

**It writes exactly one file:** `reports/agentic-readiness.md`, creating `reports/` if it does not exist. That single document holds both the decision content and the supporting evidence, in thirteen fixed sections:

1. Verdict
2. Run and Scope
3. Glossary
4. Readiness Scorecard
5. Mandatory Gates
6. What to Fix
7. What Can Be Delegated Today
8. What Is Already Good
9. Surface Resolution
10. Golden Path
11. Probe
12. Commands Executed
13. Confidence and Limits

Sections 1 to 8 are the decision document, ordered so a reader has the whole readiness picture before reaching the action list. Sections 9 to 13 are the evidence behind it.

Nothing else in your repository is changed. The one exception is the probe, a single reversible edit that is reverted before the report is written.

## Example report

[`examples/fs-demo-project/agentic-readiness.md`](examples/fs-demo-project/agentic-readiness.md) is a full run against a Next.js 14 application with Prisma and PostgreSQL. It scored 71 of 100, **Partially ready**, at Medium confidence. The golden path and the test suite verified cleanly; a port conflict on the audit host blocked the database and, with it, the probe. That is the useful case to read, because the report separates what the repository is missing from what this particular machine could not prove.

More runs, and what was redacted before publishing, in [`examples/`](examples/README.md).

## System Requirements

- An agent client that reads the Agent Skills format (see [Supported clients](#supported-clients)).
- No additional runtime dependencies. The skill uses prompt-driven analysis only.

## Data handling and privacy

- The skill performs read-only analysis of the repository in the current working directory.
- No repository contents are transmitted to any external service by the plugin itself. Your agent client's own model requests are subject to that client's privacy policy.
- The plugin contains no credentials and requires none.

## Limitations

**The audit machine shapes what can be proven.** If a required tool, service, network route or permission is missing on the machine running the assessment, that is recorded as an environment blocker rather than counted against the repository. Those areas score at most half and the run's confidence drops, so the score stays a property of the repository.

**Some commands are never run.** Anything that pushes, publishes, deploys, runs a production migration, uses real credentials or customer data, calls a paid service, or needs root is refused by design. A refused command is recorded with its class, and the area is scored on the safe evidence that remains.

**A locked install that fails caps its own area.** If the repository's frozen install cannot complete, the assessment retries once without mutating any resolution file and labels the result an unfrozen fallback. Downstream evidence stays valid, but the setup area scores at most half.

**Hard questions get abandoned on purpose.** After roughly five attempts on the same unresolved question, the assessment records `not determined` and scores on the evidence in hand.

**Monorepos are audited in full or not at all.** Every applicable workspace and component is covered; the assessment will not silently sample a subset. On a very large repository this is the main cost driver.

**A Low confidence rating is a real result.** When less than half the applicable areas could be executed, or a required probe did not complete, the report says so on its face.

## Versioning

The `version` field in [`plugin.json`](plugin.json) is the canonical source of truth. Platform marketplaces require self-contained manifests, so the same value is mirrored in [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) and [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json). The skill reads the portable root manifest and records that value as `prompt_version` in every generated report.

The current version is the `version` field of [`plugin.json`](plugin.json). `MAJOR.MINOR` continues the assessment prompt's own revision history, which predates this repository, so reports produced here stay on one timeline with reports produced by earlier revisions of the prompt. `PATCH` covers packaging changes that leave the prompt untouched.

Bump it as follows:

| Change | Bump | Example |
| --- | --- | --- |
| The report contract breaks: scoring areas or weights, gates, readiness thresholds, or report sections change such that scores are no longer comparable | major | `4.5.0` → `5.0.0` |
| The prompt changes while the report contract holds | minor | `4.5.0` → `4.6.0` |
| Packaging, README, or manifest changes only, with no change to prompt semantics | patch | `4.5.0` → `4.5.1` |

Scores are directly comparable across reports sharing the same `MAJOR.MINOR`. A minor bump may shift scores, so compare across one with care; a major bump breaks the contract, so do not compare across it at all.

Describe what changed in the commit message and in [CHANGELOG.md](CHANGELOG.md), not inside `SKILL.md`. The revision history lives in git:

```sh
git log --follow skills/agentic-readiness-assessment/SKILL.md
```

## Documentation

- [Skill definition](skills/agentic-readiness-assessment/SKILL.md)
- [Example reports](examples/README.md)
- [Publishing guide](docs/PUBLISHING.md)
- [Changelog](CHANGELOG.md)

## Contributing

Contributions are welcomed and greatly appreciated. See [CONTRIBUTING.md](CONTRIBUTING.md).

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

After creating your first contributing PR you will be requested to sign our Contributor License Agreement by commenting your PR with a special message.

## License

Distributed under the Apache License 2.0. See [LICENSE](LICENSE) for the full terms and [NOTICE](NOTICE) for attribution.

## What this does not do

The assessment is narrow by design. It audits one repository, on your machine, and hands you a ranked backlog with the evidence behind every line.

It does not fix any of it. It does not look at how your teams actually work. And it will not tell you which of your fifty repositories to start with, or what the whole estate costs you.

Those are the questions people ask us next, so we do them as work:

- **Working the backlog.** [AI-Enabled Product Engineering](https://exadel.com/services/ai-enabled-product-engineering/): engineers who do the remediation alongside your team.
- **A portfolio instead of a repository.** [AI Maturity & Readiness Assessment](https://exadel.com/services/ai-maturity-readiness-assessment/): the organization-level version of this report, covering people and process as well as code.
- **Once the repositories are ready.** [Exadel Colleague](https://exadel.com/solutions/exadel-colleague/): the AI teammate we put to work inside them.

If any of that would help: [exadel.com/contact](https://exadel.com/contact/).

## Support

Open an [issue](https://github.com/exadel-inc/agentic-readiness-assessment/issues) for anything about the assessment itself. Security reports go through [SECURITY.md](SECURITY.md).

For anything commercial: [exadel.com/contact](https://exadel.com/contact/).

## Privacy

[Exadel privacy policy](https://exadel.com/privacy-policy) and [terms](https://exadel.com/terms-and-conditions). The plugin itself collects nothing and transmits nothing.

## Contact

Built by [Exadel](https://exadel.com/).
