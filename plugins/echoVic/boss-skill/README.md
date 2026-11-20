# boss-skill

[![skills.sh](https://skills.sh/b/echovic/boss-skill)](https://skills.sh/echovic/boss-skill)
[![G-Star Incubation](https://img.shields.io/badge/G--Star-Incubation-C71D23)](https://atomgit.com/echoVic/boss-skill)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

**Languages / 语言 / 言語 / 언어 / Idiomas / Langues:** English · [中文](./README.zh-CN.md) · [日本語](./README.ja.md) · [한국어](./README.ko.md) · [Español](./README.es.md) · [Français](./README.fr.md) · [Português](./README.pt-BR.md)

![boss-skill promo](https://raw.githubusercontent.com/echoVic/boss-skill/main/boss-skill-promo.png)

> Part of the AtomGit G-Star Incubation Program. GitHub is the canonical repository; AtomGit is an automatically synchronized mirror. Please open issues and pull requests on [GitHub](https://github.com/echoVic/boss-skill).

**Boss is an expert-squad workflow for coding agents.** It turns one agent into a structured engineering team: PM, Architect, UI Designer, Tech Lead, Scrum Master, Frontend, Backend, QA and DevOps. Each role works to a hard quality contract and writes its result to disk, and an independent verifier checks the contract instead of the author. Run one role on the code you already have, such as a review of the current branch, or the whole pipeline from an idea to a pull request.

Boss works with Claude Code, Codex, OpenClaw, Antigravity, Hermes and DeepSeek Harness.

## DeepSeek Harness

Boss also ships a DeepSeek Harness bundle, [`dsh-boss-mode`](https://www.npmjs.com/package/dsh-boss-mode), with a selectable **Boss Expert Squad** preset and a sidebar that reads live Agent Teams members and tasks.

```bash
dsh plugin --profile desktop add dsh-boss-mode
```

Restart DeepSeek Harness, create a session and pick **Boss Expert Squad**.

## Why Boss

- **Useful on existing code**: `/boss:review` reviews the current branch's diff, `/boss:qa` tests it and `/boss:ship` opens the pull request. Each command does its one stage and stops.
- **Hard quality contracts**: each role has a non-negotiable requirements table (a PRD needs Given-When-Then scenarios, an architecture must compare two options, QA must record the command and exit code behind every claim).
- **The author does not grade its own work**: a script checks what a script can decide, then a separate verifier agent judges the rest and quotes its evidence. A failed contract blocks the next stage unless you waive it.
- **Artifact-driven**: every stage writes a real file under `.boss/<feature>/`; progress is judged by what is on disk, not by what the agent claims.
- **TDD by default**: development stages write a failing test first, watch it go RED, then make it GREEN with the minimum code.
- **Local by default**: no telemetry and no remote proxy. Boss pushes, opens a pull request or deploys only when you run `ship` or say yes.

## Expert squad commands

Each command runs one stage, verifies it and stops, naming the next command:

| Command           | Role               | Writes                                                         |
| ----------------- | ------------------ | -------------------------------------------------------------- |
| `/boss:pm`        | PM                 | `prd.md`                                                       |
| `/boss:architect` | Architect          | `architecture.md`                                              |
| `/boss:ui`        | UI Designer        | `ui-spec.md`, `ui-design.json`                                 |
| `/boss:review`    | Tech Lead          | `code-review.md` for a diff, or `tech-review.md` and `plan.md` |
| `/boss:tasks`     | Scrum Master       | `tasks.md`                                                     |
| `/boss:dev`       | Frontend / Backend | code and tests                                                 |
| `/boss:qa`        | QA                 | `qa-report.md`                                                 |
| `/boss:ship`      | DevOps             | a pull request, or a deployment with `--deploy`                |
| `/boss:verify`    | Verifier           | `verification.md` for the artifacts that already exist         |

Add `--continue` to keep going down the chain, or `--stop-after <stage>` to stop at a later stage. The full chain is `pm → architect → ui → review → tasks → dev → qa → ship`; run all of it with `/boss:boss <request>` in Claude Code, or by asking Boss to build something end to end.

In Claude Code these are real slash commands. On other agents, invoke the Boss skill and name the stage, for example "use Boss to review this branch".

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

The cheapest first run is a read-only review of the branch you are on: `/boss:review` writes `.boss/<branch>/code-review.md` and changes no source file. For the full pipeline:

```text
/boss:boss Build a local personal todo app --skip-ui
```

`--skip-ui` skips UI design for API/CLI projects, and `--quick` skips routine clarification prompts.

Artifacts live under `.boss/<feature>/`: `prd.md`, `architecture.md`, `ui-spec.md`, `ui-design.json`, `tech-review.md`, `plan.md`, `code-review.md`, `tasks.md`, `qa-report.md`, `deploy-report.md` and `verification.md`. Each one starts with a summary so downstream agents read the conclusion first. They are written in the language of your request; `--lang <code>` overrides it.

## Workflow

The full pipeline, with each stage verified before the next one starts:

```text
request → clarify (unless --quick)
  → PM: prd.md
  → Architect: architecture.md
  → UI: ui-spec.md + ui-design.json (skip with --skip-ui)
  → Tech Lead: tech-review.md + plan.md
  → Scrum Master: tasks.md
  → Frontend / Backend: TDD implementation
  → QA: qa-report.md
  → DevOps: pull request or deployment, deploy-report.md
```

## Quality gates

Each stage's contract is checked twice: `skill/scripts/check-artifacts.mjs` applies the rules a script can decide, and the verifier agent judges the rest. Beyond the contracts, real commands decide each gate and the verdict is recorded in the stage artifact:

| Gate             | Stage                   | Checks                                                                      |
| ---------------- | ----------------------- | --------------------------------------------------------------------------- |
| 0 (code quality) | after dev, before QA    | typecheck and lint pass, no high-severity dependency vulnerabilities        |
| 1 (testing)      | after QA, before deploy | unit and integration tests pass, coverage ≥ 70%, no P0/P1 bugs, E2E written |
| 2 (performance)  | before web deploy       | Lighthouse ≥ 80, API P99 < 500 ms (web projects)                            |

If you don't need a traceable `.boss/` folder, you probably don't need the full pipeline; use a single role instead.

## Security and privacy

Boss is local-first and makes no outbound requests by default; `ship` pushes or deploys only when you run it or confirm it. Release provenance lives in `.agents/plugins/provenance.json` and pins the repository URL, source commit, publisher and manifest digests; verify it with `npm run provenance:verify`. The full data and network boundary is in [PRIVACY.md](./PRIVACY.md).

## Evals

Three layers check Boss itself:

```bash
npm run test:install-smoke   # loads the repo through the skills CLI and `claude plugin validate`
npm run evals                # scores captured transcripts; no model is called
npm run evals:agent          # runs evals/ against a real Claude Code agent (uses API credit)
```

`npm run evals:agent` wraps [`claude plugin eval`](https://code.claude.com/docs/en/plugin-evals). Its cases check that a small edit does not trigger Boss, that a stage stops when it is done, that a review edits no source file, and that verification reports a broken contract. The same suite runs weekly in `.github/workflows/skill-behavior.yml` once an `ANTHROPIC_API_KEY` secret is set.

## Development

You need Node.js ≥ 22.18.

```bash
git clone https://github.com/echoVic/boss-skill.git
cd boss-skill
npm install
npm run typecheck
npm test
```

Other useful scripts: `npm run test:skills` (transcript parsing), `npm run test:contracts` (the artifact checker), `npm run lint` (Biome). Releases use `npm run release -- patch|minor|major|<version>`; the script checks for a clean worktree, runs typecheck, lint and tests, then syncs versions, commits, tags and pushes. See [CONTRIBUTING.md](./CONTRIBUTING.md) and [docs/dsh-release.md](./docs/dsh-release.md).

## Design

Boss is inspired by BMAD (Breakthrough Method of Agile AI-Driven Development) and the "write less, higher quality code" philosophy. The expert-squad model keeps the harness lean — no runtime state machine, no event sourcing, no hooks — while keeping hard quality contracts and artifact-driven collaboration. Read [DESIGN.md](./DESIGN.md) and `skill/references/principles.md`.

## License

[MIT](LICENSE)
