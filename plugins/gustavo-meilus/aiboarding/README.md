# AIBoarding

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./assets/aiboarding-wordmark-dark.svg">
  <img src="./assets/aiboarding-wordmark-light.svg" alt="AIBoarding — a current boarding pass for every coding agent" width="600">
</picture>

**AIBoarding keeps `AGENTS.md` alive.** It is a repository-onboarding lifecycle for maintainers using AI coding agents: canonical guidance stays current across supported agents without duplicated instruction sources or broad rewrites of unchanged guidance.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Release](https://img.shields.io/badge/release-v1.0.2-blue.svg)](./RELEASE-NOTES.md)

## Why

Agents arrive like new engineers: they need the stack, commands, architecture, guardrails, and known failure modes before touching code. Without maintained guidance they repeatedly rediscover the repository—**onboarding drift**. AIBoarding creates a canonical `AGENTS.md`, keeps `CLAUDE.md` as a thin import, and tracks lifecycle state outside instruction files.

## See it

![Fixture-derived lifecycle: AGENTS.md is canonical, CLAUDE.md imports it, and state is separate.](./assets/aiboarding-demo.svg)

The example is derived from [`tests/fixtures/modern`](./tests/fixtures/modern): it demonstrates the intended file relationship, not a live install or a universal agent-quality result.

## Quick start (Claude Code)

```text
/plugin marketplace add gustavo-meilus/aiboarding
/plugin install aiboarding@aiboarding
```

Then create the onboarding files and lifecycle:

```text
/aiboarding:create-agent-onboarding
```

Run the deterministic suite after repository changes (Git Bash is required on Windows):

```bash
bash tests/run.sh
```

## Proof and limits

- The offline lifecycle contract is covered by [`bash tests/run.sh`](./tests/run.sh) and the focused test suites.
- Live-runtime loading and hook delivery are opt-in protocols; their current availability and degraded paths are recorded in the [verification runbook](./docs/VERIFICATION.md).
- The retained [benchmark report](./benchmarks/agent-outcomes/results/codex-command-discovery-v2/report.md) is limited to its task and runtime. It is not a general speed, token, or coding-quality claim.
- Portable `SKILL.md` files can be copied to `.agents/skills/` for Codex and Copilot CLI. That route does not install lifecycle hooks, so run updates manually.

## What it does

| Lifecycle step | Outcome |
| --- | --- |
| Create | Generates `AGENTS.md`, thin `CLAUDE.md`, sidecar state, and hooks behind a validation gate. |
| Update | Triages changed scope; patches affected guidance or advances only the state pointer on a no-op. |
| Migrate | Moves legacy `AIBOARDING.md` guidance to the current layout without discarding it. |
| Compress | Reduces instruction bloat while byte-preserving commands, paths, URLs, and code. |
| Audit | Reports stale commands, contradictions, secrets, size risks, and instruction-chain limits without editing files. |

Use `/aiboarding:update-agent-onboarding` after meaningful commits, `/aiboarding:migrate-aiboarding` for the legacy layout, and the namespaced compression/audit skills when needed.

## Safety and supported surfaces

`AGENTS.md` is the canonical source; `CLAUDE.md` imports it rather than duplicating it. The sync pointer remains in `.aiboarding/state.json`, preventing bookkeeping from modifying instructions. Hooks are small, deterministic, and advisory: native loading still works if hooks are unavailable, disabled, or untrusted. Older runtimes and Windows systems without Git Bash can have reduced hook behavior; see the runbook for exact boundaries.

Claude Code has the tested marketplace installation above. Codex plugin installs include optional native hooks subject to `/hooks` trust review. Copilot, Cursor, and other agents consume canonical repository guidance through their native or portable instruction mechanisms; live compatibility verification is documented rather than implied.

## Architecture and documentation

`skills/` owns lifecycle reasoning, `templates/` owns installed copies, and `tests/` prove deterministic behavior. Read [AGENTS.md](./AGENTS.md) for repository conventions, [loop engineering](./docs/LOOP-ENGINEERING.md) for where this fits in an agent loop, [verification](./docs/VERIFICATION.md) for manual protocols, and [release notes](./RELEASE-NOTES.md) for versioned history.

## Help, contributing, and security

Report reproducible bugs or propose scoped features through [GitHub issues](https://github.com/gustavo-meilus/aiboarding/issues). Read [CONTRIBUTING.md](./CONTRIBUTING.md), follow the [Code of Conduct](./CODE_OF_CONDUCT.md), and use [SECURITY.md](./SECURITY.md) for private vulnerability reporting—do not file vulnerabilities as public issues.

Licensed under [MIT](./LICENSE). Keep your agents current, then let them get on with the work.
