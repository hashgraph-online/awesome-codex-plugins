---
name: qa
description: Playbook for /qa. Verify a release or bug against CHANGELOG claims, install journey, tests, and hygiene. Invoke via /qa; do not auto-load.
version: 0.1.0
category: core
disable-model-invocation: true
---

# QA playbook

Operator slash: `/qa`. ADR: `.cursor/memory/decisions/2026-09-16_qa-l0-slash-no-new-agent.md`. HITL labels: [hitl-gates](https://github.com/agent-kit-startup/agent-kit/blob/main/skills/hitl-gates/SKILL.md). Command SoT: [qa.md](https://github.com/agent-kit-startup/agent-kit/blob/main/.cursor/commands/qa.md).

## When to use

- A new kit release should be checked (tag, npm version, CHANGELOG object)
- A bug needs a repro in one checkout
- CHANGELOG feat/fix/chore claims need a pass/fail matrix, including install

Do **not** use this for plan audits (`/plan-external-review`, `/plan-review-triage`) or inbox filing (`/dogfood`).

## Hard stops

1. One repository: the invocation root. Ask before leaving it.
2. No new L0 agent. Dispatch `.cursor/agents/test-suites.md` when that file exists; otherwise run readiness / profile `testCommands` in-session.
3. Report only. Do not silently patch product bugs. `/backlog-add` residuals.
4. Never `/git-prod`. Never commit `.env`, tokens, or keys. Redact `ANTHROPIC_*` and Hostinger tokens in the report.
5. `sync-landing` / missionkit.io is factory-only. Skip unless the operator has `HOSTINGER_API_TOKEN`.

## HITL

Ask questions. Numbered-list fallback is path 1. Cancel or skip means stop.

**Mode** (when the invocation is ambiguous):

1. `QA this release`
2. `Repro this bug`
3. `Claims only`
4. `Cancel`

**Scratch install** (when a clean install is needed):

1. `Use a scratch git repo`
2. `QA this checkout only`
3. `Cancel`

Ask before expensive or destructive steps (fresh `git init` outside this repo, live Hostinger, rotating secrets).

## Broad Intake

Same buckets and triage labels as `/backlog-add` (`ignore` / `error` / `include` / `note`).

| Bucket | How |
|--------|-----|
| Prepared repository | `.cursor/agent-kit.json`, `.cursor/context/readiness.json` |
| Active session | HANDOFF, Context Pack |
| Plans | `.cursor/context/plan-index.json` + HANDOFF only. Tolerate a missing gitignored index. Do not glob `.cursor/plans/*.plan.md`. |
| Decisions / memory | Theme-matched ADRs, errors, plan-monitors |
| Unprocessed dogfood | Titles only; do not auto-analyze |
| Local docs | CHANGELOG, install recipes, getting-started |
| Working tree / recent commits | `git status`, `git log`, related SHAs |
| Product version | `package.json`, npm `latest`, Git tag |

## Claim matrix

Release object = CHANGELOG + Git tag/SHA + npm version + live CLI. Docs are indicative.

Columns: Claim | Source | Check | Result | Evidence

Include every public **Added** / **Fixed** / **Changed** (and **Removed**) row for the version in scope. On the factory checkout, also include fenced `changelog-private` **Changed** rows. `Claims only` skips the full journey but still fills this table.

## Tests

1. Prefer existing commands: profile `quality.testCommands`, `readiness.json` evidence, or this repo's `pnpm test:root-node` when that is the predetermined suite.
2. For a scratch consumer: `agent-kit status` (or `npx @dadado/agent-kit-cli@<version> status`) after install. Add `doctor` when the claim is about overlay/PATH drift.
3. Add a new test only when a claim has no existing command.
4. Record the exact command and pass/fail. Do not claim tests ran without that evidence.

## User journey

Minimum paths when mode is `QA this release` (not `Claims only`):

| Path | Check |
|------|--------|
| Existing checkout | `status`; PATH binary vs CLI version; printed `npx -y @dadado/agent-kit-cli@<version>` pin |
| Fresh git repo | `git init` then install. Ubuntu recipe: `docs/install-ubuntu24-bare-metal.md`. Do not require a pre-existing remote. |
| Update | Overlay restamps to the applying CLI version; missing L0 commands are a fail |

`Use a scratch git repo` may `git init` a **new** directory. It must not write kit files into a second existing product checkout.

## Report shape

Hygiene strip: no people, consumer workspace names, secrets, or chat meta-language.

```markdown
## QA report
- Mode: release | repro | claims-only
- Object: <tag / npm version / SHA>
- Checkout: <invocation root; scratch path if used>
- Claim matrix: <pass/fail per row, with command or SHA evidence>
- Journey: <paths run, or skipped>
- Tests: <commands + results>
- Residuals: none | names for /backlog-add
```

Do not invent Field Report cards.

## Related

- Analog (check, not apply): `/cursor-update-awareness`
- Residuals: `/backlog-add`
- Plan audits (different surface): `/plan-external-review`, `/plan-review-triage`
