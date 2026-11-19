# boss-skill

[![skills.sh](https://skills.sh/b/echovic/boss-skill)](https://skills.sh/echovic/boss-skill)
[![G-Star Incubation](https://img.shields.io/badge/G--Star-Incubation-C71D23)](https://atomgit.com/echoVic/boss-skill)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Languages / 语言 / 言語 / 언어 / Idiomas / Langues:** English · [中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Português](./README.pt-BR.md)

![boss-skill promo](https://raw.githubusercontent.com/echoVic/boss-skill/main/boss-skill-promo.png)

> Part of the AtomGit G-Star Incubation Program. GitHub is the canonical repository; AtomGit is an automatically synchronized mirror. Please open issues and pull requests on [GitHub](https://github.com/echoVic/boss-skill).

**Boss is an expert-squad workflow for coding agents.** It turns one agent into a structured engineering team: PM, Architect, UI Designer, Tech Lead, Scrum Master, Frontend, Backend, QA and DevOps. Unlike prompt-only agent teams, Boss enforces a hard quality contract per role, produces replayable artifacts and chains the stages automatically — start anywhere and it runs the rest until you say stop.

Boss works with Claude Code, Codex, OpenClaw, Antigravity, Hermes and DeepSeek Harness.

## DeepSeek Harness

Boss also ships a DeepSeek Harness bundle, [`dsh-boss-mode`](https://www.npmjs.com/package/dsh-boss-mode), with a selectable **Boss Expert Squad** preset and a sidebar that reads live Agent Teams members and tasks.

```bash
dsh plugin --profile desktop add dsh-boss-mode
```

Restart DeepSeek Harness, create a session and pick **Boss Expert Squad**.

## Why Boss

- **Hard quality contracts**: each role has a non-negotiable requirements table (a PRD needs Given-When-Then scenarios, an architecture must compare two options, QA must record verified or honestly-unverified evidence). A failed contract blocks the next stage unless you override it.
- **Artifact-driven**: every stage writes a real file under `.boss/<feature>/`; progress is judged by what is on disk, not by what the agent claims.
- **Continuation chain**: start at any stage and Boss auto-runs every downstream stage until `ship`.
- **TDD by default**: development stages write a failing test first, watch it go RED, then make it GREEN with the minimum code.
- **Local by default**: no telemetry and no remote proxy; the only network surface is an opt-in loopback preview server on `127.0.0.1`.

## Expert squad commands

Each slash command is an entry point that auto-runs the downstream stages:

| Command           | Starts at          | Runs through          |
| ----------------- | ------------------ | --------------------- |
| `/boss`           | PM                 | the full chain → ship |
| `/boss:pm`        | PM                 | Architect → … → Ship  |
| `/boss:architect` | Architect          | UI → … → Ship         |
| `/boss:ui`        | UI Designer        | Review → … → Ship     |
| `/boss:review`    | Tech Lead          | Tasks → … → Ship      |
| `/boss:tasks`     | Scrum Master       | Dev → QA → Ship       |
| `/boss:dev`       | Frontend / Backend | QA → Ship             |
| `/boss:qa`        | QA                 | Ship                  |
| `/boss:ship`      | DevOps             | ends the chain        |

The full chain is `pm → architect → ui → review → tasks → dev → qa → ship`. Stop it by saying "stop", "only do this step", or passing `--stop-after <stage>`.

## Quick start

Install Boss into your coding agent — the skill ships through marketplaces, with the DeepSeek Harness bundle separate on npm:

```text
# Claude Code
/plugin marketplace add echoVic/boss-skill
/plugin install boss@boss-skill

# Codex
codex plugin marketplace add echoVic/boss-skill   # then install boss in /plugins

# Any agent with the skills CLI
npx skills add echoVic/boss-skill

# DeepSeek Harness
dsh plugin --profile desktop add dsh-boss-mode
```

The cheapest first run is a read-only review against existing code: `/boss:review` writes `tech-review.md` and `plan.md` and touches nothing else. For a full pipeline:

```text
/boss Build a local personal todo app --skip-ui
```

`--skip-ui` skips UI design for API/CLI projects, and `--quick` skips routine clarification prompts.

Artifacts live under `.boss/<feature>/`: `prd.md`, `architecture.md`, `ui-spec.md`, `ui-design.json`, `tech-review.md`, `plan.md`, `tasks.md`, `qa-report.md` and `deploy-report.md`. Each one starts with a summary so downstream agents read the conclusion first.

## Workflow

```text
request → clarify (unless --quick)
  → PM: prd.md
  → Architect: architecture.md
  → UI: ui-spec.md + ui-design.json (skip with --skip-ui)
  → Tech Lead: tech-review.md + plan.md
  → Scrum Master: tasks.md
  → Frontend / Backend: TDD implementation
  → QA: qa-report.md
  → DevOps: deploy-report.md
```

## Quality gates

Beyond the per-role contracts, real commands decide each gate and the verdict is recorded in the stage artifact:

| Gate             | Stage                   | Checks                                                                      |
| ---------------- | ----------------------- | --------------------------------------------------------------------------- |
| 0 (code quality) | after dev, before QA    | typecheck and lint pass, no high-severity dependency vulnerabilities        |
| 1 (testing)      | after QA, before deploy | unit and integration tests pass, coverage ≥ 70%, no P0/P1 bugs, E2E written |
| 2 (performance)  | before web deploy       | Lighthouse ≥ 80, API P99 < 500 ms (web projects)                            |

If you don't need a traceable `.boss/` folder, you probably don't need the full pipeline; use a single role instead.

## Security and privacy

Boss is local-first and makes no outbound requests by default. Release provenance lives in `.agents/plugins/provenance.json` and pins the repository URL, source commit, publisher and manifest digests; verify it with `npm run provenance:verify`. The full data and network boundary is in [PRIVACY.md](./PRIVACY.md).

## Evals

Captured transcripts are scored without starting a real LLM:

```bash
npm run evals
npm run evals:release   # adds release-evidence and pipeline-compliance checks
```

## Development

You need Node.js ≥ 22.18.

```bash
git clone https://github.com/echoVic/boss-skill.git
cd boss-skill
npm install
npm run typecheck
npm test
```

Other useful scripts: `npm run test:skills` (skill behaviour only), `npm run evals`, `npm run lint` (Biome). Releases use `npm run release -- patch|minor|major|<version>`; the script checks for a clean worktree, runs typecheck, lint and tests, then syncs versions, commits, tags and pushes. See [CONTRIBUTING.md](./CONTRIBUTING.md) and [docs/dsh-release.md](./docs/dsh-release.md).

## Design

Boss is inspired by BMAD (Breakthrough Method of Agile AI-Driven Development) and the "write less, higher quality code" philosophy. The expert-squad model keeps the harness lean — no runtime state machine, no event sourcing, no hooks — while keeping hard quality contracts and artifact-driven collaboration. Read [DESIGN.md](./DESIGN.md) and `skill/references/principles.md`.

## License

[MIT](LICENSE)
