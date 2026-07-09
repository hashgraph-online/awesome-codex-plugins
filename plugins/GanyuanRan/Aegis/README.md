<p align="center">
    <a href="https://linux.do/t/topic/2108966/20" alt="LINUX DO">
        <img
            src="https://img.shields.io/badge/LINUX-DO-FFB003.svg?logo=data:image/svg%2bxml;base64,DQo8c3ZnIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAiIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIj48cGF0aCBkPSJNNjguMi0uMDU1aDYuMjVxMjMuOTY5IDIuMDYyIDM4IDIxLjQyNmM1LjI1OCA3LjY3NiA4LjIxNSAxNi4xNTYgOC44NzUgMjUuNDV2Ni4yNXEtMi4wNjQtMjMuOTY4LTIxLjQzIDM4LTExLjUxMiA3Ljg4NS0yNS40NDUgOC44NzRoLTYuMjVxLTIzLjk3LTIuMDY0LTM4LjAwNC0yMS40M1EuOTcxIDY3LjA1Ni0uMDU0IDUzLjE4di02LjQ3M0MxLjM2MiAzMC43ODEgOC41MDMgMTguMTQ4IDIxLjM3IDguODE3IDI5LjA0NyAzLjU2MiAzNy41MjcuNjA0IDQ2LjgyMS0uMDU2IiBzdHlsZT0ic3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOmV2ZW5vZGQ7ZmlsbDojZWNlY2VjO2ZpbGwtb3BhY2l0eToxIi8+PHBhdGggZD0iTTQ3LjI2NiAyLjk1N3EyMi41My0uNjUgMzcuNzc3IDE1LjczOGE0OS43IDQ5LjcgMCAwIDEgNi44NjcgMTAuMTU3cS00MS45NjQuMjIyLTgzLjkzIDAgOS43NS0xOC42MTYgMzAuMDI0LTI0LjM4N2E2MSA2MSAwIDAgMSA5LjI2Mi0xLjUwOCIgc3R5bGU9InN0cm9rZTpub25lO2ZpbGwtcnVsZTpldmVub2RkO2ZpbGw6IzE5MTkxOTtmaWxsLW9wYWNpdHk6MSIvPjxwYXRoIGQ9Ik03Ljk4IDcwLjkyNmMyNy45NzctLjAzNSA1NS45NTQgMCA4My45My4xMTNRODMuNDI2IDg3LjQ3MyA2Ni4xMyA5NC4wODZxLTE4LjgxIDYuNTQ0LTM2LjgzMi0xLjg5OC0xNC4yMDMtNy4wOS0yMS4zMTctMjEuMjYyIiBzdHlsZT0ic3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOmV2ZW5vZGQ7ZmlsbDojZjlhZjAwO2ZpbGwtb3BhY2l0eToxIi8+PC9zdmc+" /></a>
    <a href="https://dev.to/_879c5a0279451d52e43c3/aegis-a-method-pack-for-more-reliable-ai-coding-agents-1gfm" alt="DEV.to">
        <img src="https://img.shields.io/badge/DEV.to-Article-0A0A0A?logo=devdotto&logoColor=white" /></a>
    <a href="https://github.com/GanyuanRan/Aegis/actions/workflows/ci.yml" alt="CI">
        <img src="https://img.shields.io/github/actions/workflow/status/GanyuanRan/Aegis/ci.yml?branch=main&label=CI" /></a>
    <a href="https://github.com/GanyuanRan/Aegis/releases/latest" alt="Latest Release">
        <img src="https://badgen.net/github/release/GanyuanRan/Aegis?label=Latest%20Release" /></a>
</p>

<p align="center">
    <img src="assets/aegis-hero.png" alt="Aegis architecture-driven AI coding agent hero banner" />
</p>

# Aegis

<p align="center">
    <strong>Aegis Method Pack</strong><br/>
    Baseline-first, evidence-driven workflow discipline for AI coding agents.
</p>

<p align="center">
    <a href="README.md"><strong>English</strong></a>
    ·
    <a href="README.zh-CN.md"><strong>中文</strong></a>
    ·
    <a href="docs/current/AEGIS_WORKFLOW_GUIDE.md">Workflow Guide</a>
    ·
    <a href="docs/current/AEGIS_WORKFLOW_GUIDE_ZH.md">工作流程说明</a>
</p>

## Why Aegis

Aegis is a **Superpowers upgrade** for teams using AI coding agents on real
software work. It keeps the useful idea of composable skills, then adds:

- baseline-first planning before risky changes
- evidence before completion claims
- repair track plus retirement track for bugs, fallbacks, and compatibility paths
- workflow quality guardrails so simple tasks stay cheap
- portable method-pack skills across skill-aware hosts

Aegis is useful when agents otherwise start coding before the goal, owner,
architecture boundary, or verification path is clear.

## Quick Install

Give this prompt to your AI coding agent:

```text
Read https://github.com/GanyuanRan/Aegis, identify my current AI coding host, and install Aegis globally using the correct host guide. Restart or reload the host if needed, then run complete-install verification from the installed Aegis method-pack root. Do not run the doctor command from the target project directory. First locate `<aegis-method-pack-root>`, then run `cd <aegis-method-pack-root> && python scripts/aegis-doctor.py --write-config --json`. Treat the install as complete only if the JSON includes `"ok": true`, `"workspaceSupport": "available"`, and `"configStatus": "configured"`; if the host uses a separate skill discovery directory, also verify it with `--discovery-root <path>`; if the host guide declares a skill directory name prefix, also pass `--discovery-name-prefix <prefix>`.
```

## Updating Aegis

After a complete install has registered the current host, later updates can use
natural language such as `update Aegis` or the explicit skill request
`aegis:update`. The agent can route either form through the local update path:
locate the installed method-pack root, use the host-scoped registry, and call
`scripts/aegis-update.py` for the current host by default. Updating every
registered host requires an explicit `--all` request. Aegis does not run
background automatic updates by default.

## Before You Use It

Aegis is currently:

> `Aegis Method Pack (runtime-ready)`

It is **not** the full Aegis Platform, a daemon, a background runner, a runtime
core, an authoritative `GateDecision`, an authoritative `PolicySnapshot`, or
final completion authority. User instructions and target-project rules outrank
Aegis guidance.

For smoother host-level behavior, use:

- [Lite global rules](GLOBAL_USER_RULES_LITE.md)
- [Advanced global rules template](GLOBAL_USER_RULES_TEMPLATE.md)

Activation mode defaults to automatic. To switch to explicit mode, run this
from the installed method-pack root:

```bash
cd <aegis-method-pack-root>
python scripts/aegis-doctor.py activation-mode explicit
```

Restart the host after changing activation mode. Details and host caveats live
in [docs/current/AEGIS_ACTIVATION_MODE.md](docs/current/AEGIS_ACTIVATION_MODE.md).

TDD mode defaults to `off`: Aegis does not automatically require TDD, and
completion verification still applies. To enable automatic TDD routing when you
want Aegis to choose strict, light, or skipped by task risk:

```bash
cd <aegis-method-pack-root>
python scripts/aegis-doctor.py tdd-mode auto
```

You can also request strict TDD directly in a query with explicit markers such
as `TDD Route: strict`, `strict TDD`, `test-first`, or
`RED / GREEN / REFACTOR`.

Details live in [docs/current/AEGIS_TDD_MODE.md](docs/current/AEGIS_TDD_MODE.md).

## Supported Hosts

Aegis keeps a multi-host, plugin-installable distribution goal.

| Host group | Current status | Start here |
| --- | --- | --- |
| `Codex`, `OpenCode` | Fresh evidence exists for the current method-pack scope | [Codex](docs/README.codex.md), [OpenCode](docs/README.opencode.md) |
| `Claude Code`, `CodeBuddy`, `DeepSeek-TUI`, `Trae`, `GitHub Copilot`, `Qoder`, `Kimi Code CLI`, `ZCode` | Install guides exist; release-level fresh host smoke is still pending | [Claude Code](docs/README.claude-code.md), [CodeBuddy](docs/README.codebuddy.md), [DeepSeek-TUI](docs/README.deepseek-tui.md), [Trae](docs/README.trae.md), [GitHub Copilot](docs/README.copilot.md), [Qoder](docs/README.qoder.md), [Kimi Code CLI](docs/README.kimi-code.md), [ZCode](docs/README.zcode.md) |
| `CC GUI (JetBrains IDEA)` | Structural IDE plugin layer support for Claude Code / OpenAI-GPT provider paths; release-level fresh host smoke is still pending | [CC GUI](docs/README.cc-gui.md) |
| `Antigravity CLI`, `Antigravity IDE`, `Antigravity App` | `Antigravity CLI` is the current active closeout target; `IDE/App` remain structural targets and release-level fresh host smoke is still pending | [Antigravity](docs/README.antigravity.md) |
| `Pi CLI`, `OpenClaw`, `Hermes Agent` | Structural Agent Skills / `SKILL.md` skill-host adaptations; release-level fresh host smoke is still pending | [Pi CLI](docs/README.pi.md), [OpenClaw](docs/README.openclaw.md), [Hermes Agent](docs/README.hermes-agent.md) |
| `Gemini CLI` | Transitional compatibility surface while Antigravity support matures | [Compatibility Matrix](docs/current/AEGIS_HOST_COMPATIBILITY_MATRIX_SNAPSHOT.md) |

Read the current host verdict before making support claims:

- [Host compatibility matrix](docs/current/AEGIS_HOST_COMPATIBILITY_MATRIX_SNAPSHOT.md)
- [Known limitations](docs/current/AEGIS_KNOWN_LIMITATIONS.md)

## How To Use

After installation and host restart, use normal development requests. Aegis
skills should be selected when the task matches the method.

Use a portable goal frame before risky work. It frames the goal, then continues
into the routed workflow by default:

```text
Aegis goal: Fix the auth refresh bug without rewriting the auth system.
```

Use explicit skills when you want a specific method:

- `aegis:brainstorming`
- `aegis:systematic-debugging`
- `aegis:writing-plans`
- `aegis:first-principles-review`
- `aegis:requesting-code-review`
- `aegis:verification-before-completion`

If an expected skill does not trigger, treat it as trigger-chain diagnosis:
verify install/version visibility, host skill discovery, activation mode,
`using-aegis` routing, task-to-skill routing, and context pressure. Read
[docs/current/AEGIS_TRIGGER_HEALTH_BASELINE.md](docs/current/AEGIS_TRIGGER_HEALTH_BASELINE.md).

## Workflow Shape

Aegis routes work by complexity:

- Low-complexity: concise intent, baseline check, TDD Route, verification.
- Medium-complexity: baseline read set, Spec Brief or stable requirements,
  writing plan, atomic tasks, verification.
- High-complexity: Design Spec, plan, user review when required, then execution.

The core discipline is:

- **Baseline first**: read current project authority before substantial changes.
- **Code necessity before edits**: before adding any source-code path, Aegis
  naturally states why a non-code path is insufficient, what the minimum change
  boundary is, and then enters `code-change`; non-trivial source edits use the
  fuller `Change Necessity` slot.
- **Visible governance, on-demand trace**: Aegis naturally exposes the risk it
  helped control at key governance points. When auditability is requested, it
  can output a `Trace Digest` summarizing execution trace, evidence chain, rule
  effects, skill stability, and verification chain without exposing raw internal
  reasoning.
- **Evidence before claims**: no completion claim without fresh verification.
- **Repair plus retirement**: fix the owner and state what old path remains or retires.
- **Workflow Quality**: keep simple tasks cheap and expand only when risk demands it.

For the full workflow, read:

- [Workflow Guide](docs/current/AEGIS_WORKFLOW_GUIDE.md)
- [Workflow Quality Baseline](docs/current/AEGIS_WORKFLOW_QUALITY_BASELINE.md)
- [Runtime-ready boundary](docs/current/AEGIS_RUNTIME_READY_BOUNDARY.md)
- [Artifact schema baseline](docs/current/AEGIS_ARTIFACT_SCHEMA_BASELINE.md)

## For Maintainers

Primary verification entry:

```bash
bash tests/e2e/run-all.sh --full --host-profile fast
```

Focused docs / method-pack checks:

```bash
bash tests/e2e/boundary-compliance-check.sh
bash tests/e2e/workflow-quality-check.sh
bash tests/e2e/install-verification-policy-check.sh
bash tests/e2e/layer1-fast-check.sh --host-profile none
```

Read:

- [docs/testing.md](docs/testing.md)
- [Release checklist](docs/current/AEGIS_METHOD_PACK_RELEASE_CHECKLIST.md)
- [Current authority map](docs/current/README.md)
- [Contributing](CONTRIBUTING.md)

## Relationship To Superpowers

Aegis is derived from **[Superpowers](https://github.com/obra/superpowers)**,
created by [Jesse Vincent](https://github.com/obra). Superpowers pioneered
composable, multi-harness agent skills. Aegis keeps that foundation and adds an
architecture- and evidence-focused method layer for real software projects.

Additional inspiration comes from
[mattpocock/skills](https://github.com/mattpocock/skills), especially concise
communication, shared language, and disciplined debugging patterns. These ideas
were re-implemented in Aegis format rather than copied verbatim.

## License

MIT License. See [LICENSE](LICENSE).
