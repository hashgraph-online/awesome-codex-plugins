# Ecosystem

Where this package sits, as of 2026-11-08: the vendor-published agent skill for TypeSafe Jev, the community skills around decision models, and what this package delivers. Every community item is labeled **community, not required, inspiration only**. Nothing here is a dependency.

## Contents

- Refresh Policy
- The vendor-published skill
- Community skills
- What this package delivers
- How to read this landscape
- Unverified items
- Sources

## Refresh Policy

- last_verified_at: 2026-11-08
- refresh_when:
  - the vendor skill ships a new release or changes its install routes
  - a community skill listed here is archived, renamed, or moved
  - another vendor publishes an official decision-API skill
- supports_rules:
  - rules/modes-and-routing.md

## The vendor-published skill

TypeSafe publishes one skill, `typesafe-ai`, in the `typesafe-ai/skills` repository. On 2026-11-08 the repository held a single `SKILL.md` (288 lines) and a license, with no references or scripts; the last release was v0.6.2 on 2026-10-23, a near-complete rewrite of v0.5.7 (2026-09-12).

Install routes on the vendor page; the page asks for exactly one, because a stale copy is what makes an agent invent request or response fields:

```bash
claude plugin marketplace add typesafe-ai/skills
claude plugin install typesafe@typesafe-ai
npx skills add typesafe-ai/skills --skill typesafe-ai
```

What v0.6.2 teaches, and where this package adopted it:

| Vendor guidance | Adopted in |
|---|---|
| Judgments from the model, decisions in code: keep the decision as a truth table and ask only for the judgments | `../rules/modes-and-routing.md` §2 |
| The human test: a capable person with only this state and question could answer at once | `../rules/modes-and-routing.md` §2, `./question-design.md` |
| Confidence is rarely the gate; act on the selected option's probability | `../rules/safety-and-boundaries.md` §5, `./patterns.md` |
| Yellow flags ("prompt gymnastics"): criteria naming test items, a clause per failing case, thresholds fitted to cases, tests asserting exact probabilities, code silently overriding answers | `./eval-and-audit.md` |
| One constants module holding questions, options, criteria, and thresholds as the review surface | `../assets/templates/constants.template.ts` |
| Open the live docs while working, and say so when a page cannot be read | `../rules/safety-and-boundaries.md` §10 |

## Community skills

Each row was opened on 2026-11-08 by reading its `SKILL.md`; the last-commit date is from the repository.

| Family | Name and repository | Last commit | What it does |
|---|---|---|---|
| Design guidance | `system-one`, magnus919/agent-skills | 2026-10-15 | Design, integrate, evaluate, and self-host System One decision models across several vendors |
| Design guidance | `building-with-decision-models`, aaddrick/building-with-decision-models | 2026-10-10 | Vendor-neutral successor of `building-with-typesafe-jev`, one provider file per vendor |
| Design guidance | `building-with-typesafe-jev`, aaddrick/building-with-typesafe-jev | 2026-09-27 | Jev intent-to-shape map, API reference, patterns, six eval cases |
| Vendor gateway | `openrouter-decisions`, OpenRouterTeam/skills | 2026-10-29 | Implements the OpenRouter Decisions API: primitives, state, model pinning, threshold probes |
| Framework | `langgraph-decision-models`, langchain-ai/langchain-skills | 2026-09-25 | Replaces LangGraph routing with decision-model classifiers |
| Question generation | `grill-jev`, grgy078033/grill-jev; Blue-And-White/Grill-Jev; notque/vexjoy-agent | 2026-09-20 to 2026-10-30 | Ask a decision model at each decision point of a plan or task |
| Classification | `jev-triage`, wuyoscar/jev-skill (and several forks) | 2026-09-22 | Inbox and ticket triage with a smoke-test pilot |
| Evaluation | `jev-eval`, OneWave-AI/claude-skills; BarakChamo/jev-kit; wuyoscar/jev-skill | 2026-09-22 to 2026-09-29 | Labeled sets, criteria and threshold sweeps, confident-wrong hunting |
| Evaluation | `jev-avaliar`, ia-automation/How-to-use-JEV | 2026-10-01 | Portuguese-language domain evaluation with a frozen held-out set |
| Audit | `jev-audit`, OneWave-AI/claude-skills; idogoldd/skills; magicbeansai/jev-audit; chaseai-yt/jev-audit | 2026-09-19 to 2026-10-07 | Find label-only LLM calls or heuristic code and rank replacements |

## What this package delivers

- Files, not advice: request JSON per dialect, a constants file, caller code per route and language, a template set, an eval case skeleton, and a read-only audit table.
- One contract across vendors: neutral `boolean`, `choice`, `score`, and `box` types, a dialect map, and four route tiers that say whether a probability comes back.
- An offline checker per dialect that needs no key and no network.
- Volatile facts in dated references only, refreshed after 30 days.

The overlap with the design-guidance family is deliberate and shallow: this package links to the vendor references for what a model can do and spends its length on the generated artifact and its checks.

## How to read this landscape

Names on this page are leads, not dependencies. A community skill may be unmaintained, disagree with current vendor documentation, or target a model version that no longer exists. Star and install counts are not a selection signal here; what counts is whether a skill produces the artifact in hand and matches the vendor's current page. No vendor other than TypeSafe and OpenRouter published a decision-API skill on 2026-11-08.

## Unverified items

- Install counts and registry listings of community skills: one registry search on one day, not relied on.
- Forks and mirrors of `jev-triage` and `jev-audit`: some repositories are mirrors, not originals; only the originals are listed.
- A skill named like an item above but with unrelated content exists (`hraness/system-one-skills`); match by content, never by name.

## Sources

> Links checked 2026-11-08.

| Claim | Source |
|---|---|
| The vendor skill's repository, release history, and contents | <https://github.com/typesafe-ai/skills> (release v0.6.2, 2026-10-23) |
| The install routes, the one-method rule, and the stale-copy failure | <https://docs.typesafe.ai/agent-skill.md> |
| Community skill locations, contents, and last commits | the repositories named in the table, opened on GitHub on 2026-11-08 |
| The delivery statement and the adopted practices | this package's own rules and references |

### Evidence grade

`VENDOR` for the vendor-published skill section, read from its repository and the vendor page on 2026-11-08. `COMMUNITY` for the community table: each row was opened, but nothing there is endorsed or checked for accuracy. `LOCAL` for the delivery statement.
