<p align="center">
    <a href="https://linux.do/t/topic/2108966/20" alt="LINUX DO">
        <img
            src="https://img.shields.io/badge/LINUX-DO-FFB003.svg?logo=data:image/svg%2bxml;base64,DQo8c3ZnIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxMDAiPjxwYXRoIGQ9Ik00Ni44Mi0uMDU1aDYuMjVxMjMuOTY5IDIuMDYyIDM4IDIxLjQyNmM1LjI1OCA3LjY3NiA4LjIxNSAxNi4xNTYgOC44NzUgMjUuNDV2Ni4yNXEtMi4wNjQgMjMuOTY4LTIxLjQzIDM4LTExLjUxMiA3Ljg4NS0yNS40NDUgOC44NzRoLTYuMjVxLTIzLjk3LTIuMDY0LTM4LjAwNC0yMS40M1EuOTcxIDY3LjA1Ni0uMDU0IDUzLjE4di02LjQ3M0MxLjM2MiAzMC43ODEgOC41MDMgMTguMTQ4IDIxLjM3IDguODE3IDI5LjA0NyAzLjU2MiAzNy41MjcuNjA0IDQ2LjgyMS0uMDU2IiBzdHlsZT0ic3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOmV2ZW5vZGQ7ZmlsbDojZWNlY2VjO2ZpbGwtb3BhY2l0eToxIi8+PHBhdGggZD0iTTQ3LjI2NiAyLjk1N3EyMi41My0uNjUgMzcuNzc3IDE1LjczOGE0OS43IDQ5LjcgMCAwIDEgNi44NjcgMTAuMTU3cS00MS45NjQuMjIyLTgzLjkzIDAgOS43NS0xOC42MTYgMzAuMDI0LTI0LjM4N2E2MSA2MSAwIDAgMSA5LjI2Mi0xLjUwOCIgc3R5bGU9InN0cm9rZTpub25lO2ZpbGwtcnVsZTpldmVub2RkO2ZpbGw6IzE5MTkxOTtmaWxsLW9wYWNpdHk6MSIvPjxwYXRoIGQ9Ik03Ljk4IDcwLjkyNmMyNy45NzctLjAzNSA1NS45NTQgMCA4My45My4xMTNRODMuNDI2IDg3LjQ3MyA2Ni4xMyA5NC4wODZxLTE4LjgxIDYuNTQ0LTM2LjgzMi0xLjg5OC0xNC4yMDMtNy4wOS0yMS4zMTctMjEuMjYyIiBzdHlsZT0ic3Ryb2tlOm5vbmU7ZmlsbC1ydWxlOmV2ZW5vZGQ7ZmlsbDojZjlhZjAwO2ZpbGwtb3BhY2l0eToxIi8+PC9zdmc+" /></a>
    <a href="https://dev.to/_879c5a0279451d52e43c3/aegis-a-method-pack-for-more-reliable-ai-coding-agents-1gfm" alt="DEV.to">
        <img src="https://img.shields.io/badge/DEV.to-Article-0A0A0A?logo=devdotto&logoColor=white" /></a>
</p>

<p align="center">
    <img src="assets/aegis-hero.png" alt="Aegis architecture-driven AI coding agent hero banner" />
</p>

<p align="center">
    <a href="https://github.com/GanyuanRan/Aegis">⭐ Star the repo here to help accelerate updates ❤️</a>
</p>

# Aegis

<p align="center">
    <strong>Aegis Method Pack</strong><br/>
    Runtime-ready workflow discipline for AI coding agents.
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

## Minimal Install

If you are using an AI coding agent, you can ask it to install Aegis for you:

```text
Please read the installation instructions in https://github.com/GanyuanRan/Aegis carefully, identify the correct path for my AI coding host, install Aegis globally, restart or reload the host if needed, then run complete-install verification from the Aegis method-pack root with `python scripts/aegis-doctor.py --write-config --json`. Treat the install as complete only if the JSON output includes `"ok": true`, `"workspaceSupport": "available"`, and `"configStatus": "configured"`; if the host uses a separate skill discovery directory, also verify it with `--discovery-root <path>`.
```

## Updating Aegis

If Aegis is already installed, you can ask your AI coding agent to update it for you:

```text
Please update my installed Aegis to the latest main branch version from https://github.com/GanyuanRan/Aegis, using the correct update path for my current AI coding host, then restart or reload the host if needed and run complete-install verification from the Aegis method-pack root with `python scripts/aegis-doctor.py --write-config --json`. Treat the update as complete only if the JSON output includes `"ok": true`, `"workspaceSupport": "available"`, and `"configStatus": "configured"`; if the host uses a separate skill discovery directory, also verify it with `--discovery-root <path>`.
```

## Optional Lite Global Rules

For smoother host-level behavior, copy the whole block below into your AI
coding tool's global user rules. It improves Aegis routing and skill triggering
without duplicating the full workflows:

```markdown
# Aegis Lite Global Rules

If Aegis is installed:

- At the start of each turn, check whether the task matches an installed Aegis
  skill. If it matches, load and follow that skill.
- Simple, local, low-risk tasks may use a fast path. Do not expand the full
  governance workflow just because Aegis exists.
- Complex, diagnostic, architecture, refactor, contract, cross-module, shared
  module, compatibility, or long-running tasks should use the relevant Aegis
  workflow by default.
- Before implementation, identify the goal, scope, impact surface, and
  verification method. Read project baseline or authority docs when relevant.
- Before claiming completion, provide fresh verification evidence. If
  verification is blocked, state the blocker and residual risk.
- Aegis is a method layer, not a final authority system. Do not claim final
  gate decisions or completion authority.
- The user's current instruction and the target project's rules take priority
  over Aegis guidance.
```

For stricter teams or governance-heavy projects, you can instead start from the
full advanced templates and merge only the parts you need:

- [Advanced English template](GLOBAL_USER_RULES_TEMPLATE.md)
- [Advanced Chinese template](GLOBAL_USER_RULES_TEMPLATE.zh-CN.md)

## Activation Mode

Aegis defaults to automatic mode. To switch to manual mode, edit:

```text
~/.config/aegis/config.toml
```

Windows:

```text
%USERPROFILE%\.config\aegis\config.toml
```

If the file does not exist, create it manually. Add:

```toml
activation_mode = "explicit"
```

To return to automatic mode, set `activation_mode = "auto"` or delete the file.

Then restart the host. In explicit mode, supported bootstrap hooks stop
injecting Aegis automatically, while direct skill calls such as
`aegis:using-aegis` remain available. Host caveats are documented in
[docs/current/AEGIS_ACTIVATION_MODE.md](docs/current/AEGIS_ACTIVATION_MODE.md).

`Aegis` is an Architecture-Driven Development (ADD) method pack for AI coding agents.

It builds on the original `superpowers` methodology and adds evidence-driven governance, TLREF execution flow, and dual-track repair/retirement rules.

In Aegis, ADD means the agent should understand the project's baseline, architecture boundaries, owners, impact surface, compatibility constraints, and verification path before making substantial changes.

Current release shape:

> `Aegis Method Pack (runtime-ready)`

This repository is **not** the full `Aegis Platform`. It does not provide authoritative runtime-core decisions, authoritative `GateDecision`, or completion authority.

## Problems Aegis Solves

AI coding agents are strong at local execution, but long or risky software work often fails for process reasons:

- work starts before the task boundary and baseline are clear
- the agent claims completion without fresh evidence
- bug fixes add new fallback logic while old owners keep running
- long tasks lose state after compaction, handoff, or multi-agent work
- architecture drift is noticed only after the change has already spread

Aegis addresses those problems at the method-pack layer. It makes the agent frame the task,
read the relevant baseline, keep evidence close to claims, track repair and retirement together,
and maintain resumable checkpoints for long work.

## What Users Get

Installing Aegis gives an AI coding tool a stricter development discipline without requiring a new runtime platform:

- clearer task framing before edits
- safer debugging and refactoring loops
- fewer unsupported "done" claims
- better long-task continuity through todo checkpoints, resume hints, and drift checks
- explicit compatibility and retirement thinking when behavior changes
- portable workflows across Codex, OpenCode, Claude Code, and other skill-aware hosts

## What Aegis Adds

Aegis keeps the useful parts of `superpowers`:

- composable skills
- skill-triggered workflows
- multi-host install and plugin distribution skeletons
- implementation planning, review, debugging, and verification practices

Aegis adds a stricter governance spine:

- baseline-first work
- evidence before claims
- impact-aware task framing
- TLREF / DIVE / Reflection / QA execution discipline
- repair track plus retirement track for bug fixes, refactors, contract changes, and governance cleanup
- long-task continuation with todo checkpoints, resume hints, drift checks, and evidence bundles
- runtime-ready artifacts that remain drafts, hints, projections, and evidence bundles

## Current Scope

Aegis currently owns:

- method-pack skills
- initial instructions and contributor guardrails
- host installation guidance
- representative tests and verification assets
- runtime-ready artifact shapes
- release, rollback, known-limitation, and compatibility checklists for maintainers

Aegis does not currently own:

- `Host Adapters`
- `Runtime Core`
- authoritative `GateDecision`
- final completion authority
- full production rollout guarantees

For the current authority map, read:

- [docs/current/README.md](docs/current/README.md)
- [docs/adr/ADR-0001-aegis-method-pack-is-not-runtime-core.md](docs/adr/ADR-0001-aegis-method-pack-is-not-runtime-core.md)

## Host Compatibility

Aegis keeps the multi-host plugin-installable goal.

Current host-facing status:

| Host | Current status |
| --- | --- |
| `Codex` | Representative smoke path verified; Git Bash naive smoke still has known observation items |
| `OpenCode` | Base suite and integration closeout have passed in the current method-pack scope |
| `Claude Code` | Plugin skeleton and install guide exist; release-level fresh host smoke is still pending |
| `CodeBuddy` | Plugin skeleton and native `SKILL.md` manual install guide exist; release-level fresh host smoke is still pending |
| `DeepSeek-TUI` | Native `SKILL.md` discovery supports manual Aegis skill install; release-level fresh host smoke is still pending |
| `Trae` | Native `SKILL.md` discovery supports manual Aegis skill install; release-level fresh host smoke is still pending |

Other hosts remain product targets, but are not yet current release-level verdicts.

Read:

- [docs/current/AEGIS_HOST_COMPATIBILITY_MATRIX_SNAPSHOT.md](docs/current/AEGIS_HOST_COMPATIBILITY_MATRIX_SNAPSHOT.md)
- [docs/current/AEGIS_KNOWN_LIMITATIONS.md](docs/current/AEGIS_KNOWN_LIMITATIONS.md)

## Installation

Aegis can be installed through each host's native discovery or plugin path.
A public marketplace listing is not required for the paths below.

After installation and host restart, Aegis skills are discovered automatically.
For normal use, users can ask for development work naturally; the agent should
select the relevant Aegis method when the task matches a skill. Explicit skill
commands are still available when you want to force, test, or debug a workflow.

### Codex

macOS / Linux:

```bash
git clone https://github.com/GanyuanRan/Aegis.git ~/.codex/aegis
mkdir -p ~/.agents/skills
ln -s ~/.codex/aegis/skills ~/.agents/skills/aegis
```

Windows PowerShell:

```powershell
git clone https://github.com/GanyuanRan/Aegis.git "$env:USERPROFILE\.codex\aegis"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\aegis" "$env:USERPROFILE\.codex\aegis\skills"
```

Optional Codex config for subagent-heavy skills:

```toml
[features]
multi_agent = true
```

Restart Codex, then ask it to use `aegis:using-aegis` or an Aegis skill such as
`brainstorming`.

### OpenCode

Use the plugin shortcut by adding Aegis to the `plugin` array in your global or
project `opencode.json`:

```json
{
  "plugin": ["aegis@git+https://github.com/GanyuanRan/Aegis.git"]
}
```

If the file already has plugins, append Aegis:

```json
{
  "plugin": [
    "other-plugin",
    "aegis@git+https://github.com/GanyuanRan/Aegis.git"
  ]
}
```

Then restart OpenCode and verify:

```bash
opencode --version
```

Ask: `Tell me about your aegis`.

### Claude Code

Marketplace flow:

```bash
claude plugin marketplace add GanyuanRan/Aegis
claude plugin install aegis@aegis-dev --scope user
```

Local checkout flow:

```bash
git clone https://github.com/GanyuanRan/Aegis.git ~/aegis
claude --plugin-dir ~/aegis
```

Inside Claude Code, run `/reload-plugins`, then try `/aegis:using-aegis`.

### CodeBuddy

CodeBuddy supports both plugin metadata and native `SKILL.md` skill discovery.
For the transparent manual path:

macOS / Linux:

```bash
git clone https://github.com/GanyuanRan/Aegis.git ~/.codebuddy/aegis
mkdir -p ~/.codebuddy/skills
cp -R ~/.codebuddy/aegis/skills/* ~/.codebuddy/skills/
```

Windows PowerShell:

```powershell
git clone https://github.com/GanyuanRan/Aegis.git "$env:USERPROFILE\.codebuddy\aegis"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.codebuddy\skills"
Copy-Item -Recurse -Force "$env:USERPROFILE\.codebuddy\aegis\skills\*" "$env:USERPROFILE\.codebuddy\skills\"
```

Aegis also ships `.codebuddy-plugin/` metadata for CodeBuddy plugin flows.
Restart CodeBuddy, then ask it to describe its Aegis skills.

### DeepSeek-TUI

DeepSeek-TUI discovers skills from `SKILL.md` directories. Install Aegis by
copying its skill directories into DeepSeek-TUI's global skills path:

macOS / Linux:

```bash
git clone https://github.com/GanyuanRan/Aegis.git ~/.deepseek/aegis
mkdir -p ~/.deepseek/skills
cp -R ~/.deepseek/aegis/skills/* ~/.deepseek/skills/
```

Windows PowerShell:

```powershell
git clone https://github.com/GanyuanRan/Aegis.git "$env:USERPROFILE\.deepseek\aegis"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.deepseek\skills"
Copy-Item -Recurse -Force "$env:USERPROFILE\.deepseek\aegis\skills\*" "$env:USERPROFILE\.deepseek\skills\"
```

Restart DeepSeek-TUI, then verify with `/skills` and `/skill using-aegis`.

### Trae

Trae discovers skills from `SKILL.md` directories. Install Aegis by copying its
skill directories into Trae's global skills path:

macOS / Linux:

```bash
git clone https://github.com/GanyuanRan/Aegis.git ~/.trae/aegis
mkdir -p ~/.trae/skills
cp -R ~/.trae/aegis/skills/* ~/.trae/skills/
```

Windows PowerShell:

```powershell
git clone https://github.com/GanyuanRan/Aegis.git "$env:USERPROFILE\.trae\aegis"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.trae\skills"
Copy-Item -Recurse -Force "$env:USERPROFILE\.trae\aegis\skills\*" "$env:USERPROFILE\.trae\skills\"
```

Restart Trae, then ask it to describe its Aegis skills.

Full host guides:

- [Claude Code](docs/README.claude-code.md)
- [CodeBuddy](docs/README.codebuddy.md)
- [Codex](docs/README.codex.md)
- [DeepSeek-TUI](docs/README.deepseek-tui.md)
- [OpenCode](docs/README.opencode.md)
- [Trae](docs/README.trae.md)

The project still preserves the broader multi-host distribution skeleton inherited from `superpowers`, including Cursor and Gemini-related package surfaces. Those surfaces should not be interpreted as current fresh release-level closeout unless the compatibility matrix says so.

## First Project Baseline

Aegis works best when the target project has a small, explicit baseline before
large development work starts. Without one, Aegis can still run, but task
framing, authority lookup, verification, and drift checks rely more on ad-hoc
context and may be less stable.

For a new or undocumented project, first ask the agent to create a lightweight
project baseline, for example:

```text
Use Aegis to establish this project's baseline before implementation:
purpose, current architecture, authority docs, run/test commands, compatibility
boundaries, non-goals, and verification expectations.
```

For an existing project, point the agent at the repository's current source of
truth, such as `README`, `CONTRIBUTING`, architecture docs, ADRs, or local
project rules, and ask it to treat those as baseline references before changing
code.

## Execution Model

Aegis is not a daemon, background runner, or authoritative runtime core.
It works through host-level skill discovery, bootstrap context, and explicit skill loading.

Automatic behavior:

- Codex discovers Aegis skills from the configured skills directory at startup.
- OpenCode loads the Aegis plugin, mirrors skills into OpenCode's global skills path,
  and injects compact bootstrap context.
- Claude Code loads Aegis through its plugin namespace or a local plugin directory.
- CodeBuddy discovers copied Aegis skill directories from native `SKILL.md`
  skill paths, or loads Aegis through `.codebuddy-plugin/` metadata.
- DeepSeek-TUI discovers copied Aegis skill directories from its native
  `SKILL.md` skill paths.
- Trae discovers copied Aegis skill directories from its native `SKILL.md`
  skill paths.
- `using-aegis` tells the agent to check whether a task-specific skill applies before responding.
- In day-to-day use, you do not need to manually name a skill for every request;
  explicit commands are the override path when you want a specific method.

Explicit use:

- Ask for a skill by name, such as `aegis:brainstorming`,
  `aegis:systematic-debugging`, `aegis:long-task-continuation`,
  or `aegis:verification-before-completion`.
- Use `/aegis-goal <task>` or portable `Aegis goal: <task>` when you want a
  thin goal frame before work starts. It sets goal, success evidence, stop
  condition, and non-goals, then routes onward without creating project files
  by default.
  Example: `Aegis goal: Fix the auth refresh bug without rewriting the auth system.`
- In OpenCode, use the native `skill` tool, for example: `use skill tool to load aegis/brainstorming`.
- In Claude Code, use the plugin namespace, for example: `/aegis:using-aegis`.
- In CodeBuddy, ask it to load an Aegis skill such as `systematic-debugging`.
- In DeepSeek-TUI, use the native skill command, for example: `/skill systematic-debugging`.
- In Trae, ask it to load an Aegis skill such as `systematic-debugging`.

Long-task behavior:

- Aegis can keep `TodoCheckpointDraft`, `ResumeStateHint`, `DriftCheckDraft`,
  and `EvidenceBundleDraft` discipline around long work.
- This improves resumability and reduces drift, but it does not create a host watchdog,
  automatic retry loop, or final completion authority.

## Core Workflow

The method pack is organized around agent workflows:

1. **Brainstorming**
   - clarify intent, scope, impact, and baseline read set before implementation
2. **Writing Plans**
   - produce bite-sized, verifiable plans with exact files, verification steps, and compatibility boundaries
3. **Systematic Debugging**
   - move from symptoms to root cause with evidence before fixes
4. **Test-Driven Development**
   - use red/green/refactor where applicable
5. **Requesting Code Review**
   - review for behavioral risks, regressions, and missing tests
6. **Verification Before Completion**
   - no completion claim without fresh verification evidence

Aegis routes work by complexity before implementation:

- Low-complexity tasks can proceed with a concise intent, baseline check, TDD, and verification.
- Medium-complexity tasks require a baseline read set, a Spec Brief or stable requirements, a plan, and atomic tasks before TDD.
- High-complexity tasks require a Design Spec and plan first, with user review where the workflow calls for it.

Workflow Quality guardrails keep that routing practical: simple tasks stay on
the fast path, medium/high-risk tasks get the right evidence and artifacts, and
outputs use compact contracts before expanding into full workflow structure.
Read [docs/current/AEGIS_WORKFLOW_QUALITY_BASELINE.md](docs/current/AEGIS_WORKFLOW_QUALITY_BASELINE.md).

When a project needs persistent Aegis records, Aegis creates a lightweight
project workspace lazily. The default workspace includes `README.md`,
`INDEX.md`, `BASELINE-GOVERNANCE.md`, and standard `adr/`, `baseline/`,
`specs/`, `plans/`, and `work/` directories under `docs/aegis/`. Task process
records live under `docs/aegis/work/YYYY-MM-DD-<task-slug>/`. Existing project
docs and ADRs remain the preferred authority; reusable Aegis outputs are
promoted only when the workflow needs them.

Recommended installs keep the Aegis method-pack root available so project
workspace support can be verified after installation. The Aegis method-pack
repository itself does not ship a precreated live `docs/aegis/` workspace.
Workspace structure checks do not judge evidence sufficiency or grant
completion authority.

Maintainers can verify a complete install and write the durable local helper
paths with:

```bash
python scripts/aegis-doctor.py --write-config --json
```

Complete-install verification must report `"ok": true`,
`"workspaceSupport": "available"`, and `"configStatus": "configured"`.

When a host exposes a separate skill discovery directory, pass it as
`--discovery-root <path>` to confirm it resolves to the current method-pack
skills rather than a stale copied version.

If Aegis is installed but the expected skill does not trigger automatically,
treat it as trigger-chain diagnosis rather than a prompt wording problem:

1. verify the method-pack version and install root
2. verify the host discovery directory points at the current `skills/`
3. confirm the host was restarted or reloaded when required
4. check `activation_mode` and whether automatic bootstrap is expected
5. explicitly invoke `aegis:using-aegis` and then the expected skill
6. compare the task against the trigger-health matrix

After a long session, heavy tool output, resume, or context compaction,
explicitly re-run `aegis:using-aegis` to refresh routing before continuing
non-trivial work.

See `docs/current/AEGIS_TRIGGER_HEALTH_BASELINE.md` for the diagnostic layers.

For bug fixes, architecture changes, contract work, and governance cleanup, Aegis requires:

- **Repair track**
  - real root cause
  - canonical owner
  - smallest necessary change
  - compatibility boundary
  - verification method
- **Retirement track**
  - old owner / fallback / patch location
  - whether it is still active
  - reason to keep it, if any
  - deletion or convergence trigger
  - validation before removal

## Runtime-Ready Artifacts

Current method-pack outputs may include:

- `TaskIntentDraft`
- `BaselineReadSetHint`
- `ImpactStatementDraft`
- `EvidenceBundleDraft`
- `GateInputPack`
- `SubagentContextPacket`
- `TodoCheckpointDraft`
- `ResumeStateHint`
- `DriftCheckDraft`

These are advisory and runtime-ready. They are not authoritative runtime decisions.

Read:

- [docs/current/AEGIS_ARTIFACT_SCHEMA_BASELINE.md](docs/current/AEGIS_ARTIFACT_SCHEMA_BASELINE.md)
- [docs/current/AEGIS_RUNTIME_READY_BOUNDARY.md](docs/current/AEGIS_RUNTIME_READY_BOUNDARY.md)

## Testing

Primary verification entry:

```bash
bash tests/e2e/run-all.sh --full --host-profile fast
```

Focused checks:

```bash
bash tests/e2e/boundary-compliance-check.sh
bash tests/e2e/artifact-schema-check.sh
bash tests/e2e/workflow-quality-check.sh
bash tests/opencode/run-tests.sh
bash tests/codex-plugin-sync/test-sync-to-codex-plugin.sh
```

Read:

- [docs/testing.md](docs/testing.md)
- [docs/current/AEGIS_METHOD_PACK_RELEASE_CHECKLIST.md](docs/current/AEGIS_METHOD_PACK_RELEASE_CHECKLIST.md)

## Contributing

Read:

- [CONTRIBUTING.md](CONTRIBUTING.md)
- [SECURITY.md](SECURITY.md)
- [SUPPORT.md](SUPPORT.md)
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

Before changing behavior-shaping skill content, also read:

- [skills/first-principles-review/SKILL.md](skills/first-principles-review/SKILL.md)
- [skills/writing-skills/SKILL.md](skills/writing-skills/SKILL.md)
- [skills/verification-before-completion/SKILL.md](skills/verification-before-completion/SKILL.md)

## Relationship To Superpowers

Aegis is derived from **[Superpowers](https://github.com/obra/superpowers)**, created by [Jesse Vincent](https://github.com/obra). Superpowers pioneered the idea of composable, multi-harness agent skills — the foundation this project builds on.

We are grateful to Jesse and all Superpowers contributors for creating and maintaining the original project under the MIT license, and for establishing the plugin distribution patterns (Claude Code, Codex, Cursor, OpenCode, Gemini CLI) that Aegis continues to use.

This project adds a governance-focused method layer and public release path for the `Aegis Method Pack`, while preserving Superpowers' zero-dependency philosophy and multi-harness compatibility.

## Acknowledgments

We thank [Matt Pocock](https://github.com/mattpocock) and all contributors to [mattpocock/skills](https://github.com/mattpocock/skills) (MIT license) for sharing their skill designs openly. Several ideas from that project — particularly around concise communication, shared language glossaries, and disciplined debugging — have influenced Aegis skill design.

| Aegis skill | Inspired by | What we adapted |
|-------------|-------------|-----------------|
| `communicating-concisely` | `/caveman` | Ultra-compressed communication mode with auto-clarity exception |
| `establishing-project-context` | `/grill-with-docs` | CONTEXT.md shared language system, terminology tightening during brainstorming |
| ADR creation gate | `/grill-with-docs` ADR discipline | Three-condition gate before creating architecture decision records |
| Feedback loop construction | `/diagnose` Phase 1 | Priority ladder for building automated bug reproduction loops |

These ideas were re-implemented in Aegis format — shorter, multi-harness compatible, and integrated with the TLREF/DIVE/Reflection governance spine rather than copied verbatim.

Internal implementation notes are kept out of the public release tree. The
public contract is the skill content, current authority docs, and this
acknowledgment.

## License

MIT License. See [LICENSE](LICENSE).
