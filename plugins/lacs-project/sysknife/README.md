<p align="center">
  <a href="https://github.com/lacs-project/sysknife">
    <img src="assets/logo/sysknife.svg" alt="SysKnife" width="170" height="170"/>
  </a>
</p>

<h1 align="center">SysKnife</h1>

<p align="center">
  <em>Your sysadmin co-pilot. Plan. Approve. Audit.</em>
</p>

<p align="center">
  <a href="https://github.com/lacs-project/sysknife/actions"><img src="https://img.shields.io/github/actions/workflow/status/lacs-project/sysknife/ci.yml?branch=main&style=flat-square&logo=github&label=CI" alt="CI"></a>
  <a href="https://github.com/lacs-project/sysknife/blob/main/LICENSE"><img src="https://img.shields.io/github/license/lacs-project/sysknife?style=flat-square" alt="License"></a>
  <a href="https://github.com/lacs-project/sysknife/stargazers"><img src="https://img.shields.io/github/stars/lacs-project/sysknife?style=flat-square&logo=github" alt="Stars"></a>
  <a href="https://github.com/lacs-project/sysknife/issues"><img src="https://img.shields.io/github/issues/lacs-project/sysknife?style=flat-square" alt="Issues"></a>
  <a href="https://github.com/lacs-project/sysknife/discussions"><img src="https://img.shields.io/github/discussions/lacs-project/sysknife?style=flat-square&label=discuss" alt="Discussions"></a>
  <a href="https://www.npmjs.com/package/sysknife-setup"><img src="https://img.shields.io/npm/v/sysknife-setup?style=flat-square&logo=npm&label=npx%20setup" alt="npm version"></a>
  <a href="https://glama.ai/mcp/servers/lacs-project/sysknife"><img src="https://glama.ai/mcp/servers/lacs-project/sysknife/badges/score.svg" alt="Glama MCP server quality score"></a>
</p>

<p align="center">
  <strong>Distros</strong>&nbsp;
  <img src="https://img.shields.io/badge/Ubuntu%2020.04%2B-supported-2f855a?style=flat-square&logo=ubuntu&logoColor=white" alt="Ubuntu 20.04 and later supported">
  <img src="https://img.shields.io/badge/Ubuntu%2022.04%20%7C%2024.04%20%7C%2026.04-VM%20validated-2f855a?style=flat-square&logo=ubuntu&logoColor=white" alt="Ubuntu 22.04, 24.04 and 26.04 VM validated">
  <img src="https://img.shields.io/badge/Fedora%20Atomic%2041%2B-eligible%2C%20unvalidated-b7791f?style=flat-square&logo=fedora&logoColor=white" alt="Fedora Atomic 41 and later eligible but not VM validated">
</p>

<p align="center">
  <a href="#install">Install</a> ·
  <a href="#how-it-works">How it works</a> ·
  <a href="#why-not-just-x">Why not <em>X</em>?</a> ·
  <a href="docs/distro-support.md">Distro matrix</a> ·
  <a href="ROADMAP.md">Roadmap</a> ·
  <a href="CONTRIBUTING.md">Contribute</a> ·
  <a href="https://github.com/lacs-project/sysknife/discussions">Discuss</a>
</p>

<p align="center">
  <img src="assets/demo/mcp-flow.gif" alt="SysKnife in Claude Code via MCP" width="900"/>
</p>

<p align="center">
  <em>A deterministic reproduction of the Claude Code MCP flow, rendered offline by
  <a href="assets/demo/mcp-flow-mock.sh">mcp-flow-mock.sh</a> so it replays identically from a
  fresh checkout. The same flow works in Cursor and Codex CLI.</em><br/>
  <em>Looking for the standalone CLI? See <a href="docs/cli.md">the CLI guide</a>.</em>
</p>

> **Describe what you want in plain language.** Review a typed plan with risk
> levels. Approve explicitly. Watch it execute with live output. Atomic-host
> changes (rpm-ostree) roll back automatically on failure. Every action is
> Ed25519-signed and audited.

The AI never supplies a command. Every action is a **typed operation** with a
formal risk level, and the daemon builds the command line itself from the
action's own definition — some actions do run through `sh -c`, but the shell
fragment is constructed by SysKnife, never by the model. The AI cannot touch
your system directly. A privileged daemon executes only what you approve, writes
a tamper-evident Ed25519-signed audit chain, and rolls back atomic-host
(rpm-ostree) changes automatically on failure.

**Why typed actions and not a guarded shell?** Red-team research (GuardFall)
found that **10 of 11 AI agents bypass raw-string shell guards** — an allowlist
or regex is filtering a language rich enough to hide intent. SysKnife removes
the shell string entirely: the model emits
[typed actions](docs/typed-actions.md), and a
[public-key-verifiable audit chain](docs/the-audit-chain.md) records every one.

---

## Install

The fastest path is the setup wizard. It installs the daemon and wires
SysKnife into your AI IDE — Claude Code, Cursor, or Codex CLI — so you can
plan and execute from chat.

```sh
npx sysknife-setup
```

Needs **Node 18 or newer**. On Ubuntu 22.04 `apt install nodejs` gives Node 12,
which is too old; the installer says so and how to get a current Node. No Rust
toolchain and no compile: it downloads verified prebuilt binaries.

[![npm version](https://img.shields.io/npm/v/sysknife-setup?style=flat-square&logo=npm)](https://www.npmjs.com/package/sysknife-setup)

What this does:

1. **Downloads the prebuilt `sysknife` + `sysknife-daemon` binaries** for your
   architecture (x86_64 / aarch64) from GitHub Releases, **SHA-256-verifies**
   each against the release checksum file — a mismatch aborts the install — and
   places them in `~/.local/bin` (no sudo). Pass `--no-binary` to skip the
   download and build from source instead.
2. Asks for your **LLM provider, key, and model** — OpenAI / Anthropic / Gemini
   / Ollama / Groq / DeepSeek / Mistral / xAI (Ollama needs no key). The key
   prompt is skipped when the matching env var is already set.
3. Asks **which AI integration** to wire up (or pick `--claude` / `--cursor` /
   `--codex` / `--all`) and your **daemon target(s)** — socket, plus an optional
   vsock token for a remote VM.
4. **Writes the integration-specific MCP config** (merging into any existing
   file, never clobbering) so the next chat session sees the `sysknife_*` tools —
   `sysknife_plan`, `sysknife_execute`, `sysknife_history`, `sysknife_doctor`,
   `sysknife_audit_verify` — as first-class tools.
5. **Installs and starts the daemon as a service** (last step) — a systemd
   *user* service by default (no sudo; kept alive across logout via linger).
   That service runs as you, so read-only actions work but **mutating ones do
   not**: installing packages or restarting services needs the system-level
   service, whose sudoers grants belong to the `sysknife` system user. Pick the
   system service on any host where you intend to change something, and pass
   `--daemon-mode=system|user|skip` to choose without a prompt. `--daemon-mode=system`
   does not install the system service from the wizard — it needs root-owned
   sudoers, polkit and helper policy that `sudo make install` owns — so it prints
   the exact sequence and reports the daemon as not yet installed.

   To verify the download against a checksum list you trust independently of the
   release, set `SYSKNIFE_PINNED_SHA256SUMS=/path/to/sums`; see
   [SECURITY.md](SECURITY.md#release-artefact-trust).

| Client          | Files written                                        |
|-----------------|------------------------------------------------------|
| **Claude Code** | `.mcp.json` + `.claude/hookify.*.local.md`           |
| **Cursor**      | `.cursor/mcp.json` + `.cursor/rules/sysknife.mdc`    |
| **Codex CLI**   | `~/.codex/config.toml` (appended) + `AGENTS.md`      |

Then in your chat: ask for what you want and review the plan with risk pills.
Approve each transaction with `sysknife approve <transaction-id>` in a
terminal, return the one-time receipts, and watch it execute. The daemon, not
the prompt, enforces the receipt boundary.

> **Prefer the standalone CLI?** Same engine, no IDE — see the
> [CLI guide](docs/cli.md) for `sysknife "..."`, `--dry-run`, `--json`,
> approval prompts, and audit-log inspection.

<details>
<summary><strong>Manual install — Ubuntu 20.04+</strong></summary>

Needs Rust stable **and a C compiler** (`build-essential`): the TLS and SQLite
dependencies build native code, so a rustup-only machine stops at
`error: linker cc not found`. `cmake` is not required. Budget 7 to 12
minutes for the ~400-crate build (6m56s on Ubuntu 24.04, 11m43s on 22.04).

```sh
sudo apt-get install -y build-essential
git clone https://github.com/lacs-project/sysknife
cd sysknife
make build                            # builds sysknife (CLI) + sysknife-daemon
sudo make install                     # installs both; daemon runs as a system service
sudo systemctl enable --now sysknife-daemon

# Join the socket group and one role group, or every request is refused with
# "Permission denied" before any role check runs: /run/sysknife is 0750
# sysknife:sysknife, and a sudo admin is not in that group automatically.
# Role groups: sysknife-observer (read-only), sysknife-dev (medium risk),
# sysknife-admin (high risk). Members of wheel are treated as admin.
sudo usermod -aG sysknife,sysknife-admin "$USER"
newgrp sysknife                       # or log out and back in

# Then wire your IDE — --no-binary skips the download since you just built them
# (--daemon-mode=skip: make install already set the service up)
npx sysknife-setup --no-binary --daemon-mode=skip
```

### Uninstall

Whichever way you installed, there is one command for it.

```sh
# Removes what the wizard installed: the user service, the binaries in
# ~/.local/bin, and the MCP + agent config in the current directory.
npx sysknife-setup --uninstall

# See exactly what that would touch, without touching it.
npx sysknife-setup --uninstall --dry-run
```

**Your audit history is kept by default.** Removing the software should not
destroy the record of what it did, so the audit database, the safety-audit log
and `~/.config/sysknife` are left in place and their paths printed. Delete those
too, only if you mean to, with:

```sh
npx sysknife-setup --uninstall --purge   # names each file before deleting it
```

If you installed the **system** service with `sudo make install`, remove it with
the Makefile that owns its sudoers grants, polkit rules and privileged helpers.
`--uninstall` deliberately will not touch those, because half a removed
privilege boundary is worse than none:

```sh
sudo make uninstall
```

All three Ubuntu LTS releases record a live-VM run of the 79-story Ubuntu
suite, and each run has a replay twin that reproduces it: 22.04, 24.04 and 26.04
all at 79/79, every twin serving every call with zero misses. The runs are in
`tests/evidence/story-runs/`. The suite grew from 50 when every Debian-only
action got a story, `GetHostState` first.
Fedora Atomic is the rpm-ostree target; record a current Silverblue 44 VM run
before treating a release as current-validated. Plain Fedora Workstation and
Server remain experimental until the `dnf` action family ships. See the
[`distro support matrix`](docs/distro-support.md) for evidence and scope.
</details>

<details>
<summary><strong>Dry run — plan only, nothing executes</strong></summary>

```sh
# Requires the sysknife binary (see manual install above, or `npx sysknife-setup`).
# Plans only: no daemon, no approval, no execution.
export ANTHROPIC_API_KEY=sk-ant-...
sysknife --dry-run "show disk usage and list services that ate cpu in the last hour"
```
</details>

## Prefer the terminal? The CLI is a first-class path

Same engine, no IDE and no MCP client — plain language to a typed plan to live
execution, straight from your shell, with `--dry-run`, `--json`, `--yes` up to a
risk ceiling, and `sysknife audit verify`. This is a fully supported way to run
SysKnife, not an afterthought. See the [CLI guide](docs/cli.md).

<p align="center">
  <img src="assets/demo/demo.gif" alt="sysknife CLI — plan, approve, and execute in the terminal" width="900"/>
</p>

<p align="center">
  <em>A deterministic reproduction of a real planning and execution session, rendered offline by
  <a href="assets/demo/demo-mock.sh">demo-mock.sh</a>. Live LLM calls are nondeterministic and the
  tape has to render with no daemon or provider configured, so the recording is scripted rather
  than captured; the output styling is generated from the same code paths as the real CLI.</em>
</p>

> **Also: a desktop GUI — development paused.** An experimental Tauri desktop
> app (`sysknife-shell`) wraps the same plan → approve → execute loop in a
> window. **Its development is paused for now**, and effort is going to Ubuntu
> across its supported versions instead. The code stays in the tree and still
> builds, but it is not being reviewed, tested, or extended, so reach for it
> only if you specifically want a graphical approval flow and can live with
> that. The MCP integration and the CLI are the maintained surfaces.

## How it works

```
sysknife-brain   →   approval gate    →   sysknife-daemon
  (planner)         (you, in a         (executor)
   talks to LLM      terminal)          only privileged
   never to OS       shows the plan,    process; signs
                     takes y/n          every action
```

The approval gate is a surface, not a component. In the maintained paths it is
`sysknife approve <transaction-id>` in your terminal — for the CLI and for MCP
alike, which is why an AI client cannot approve its own plan. The paused Tauri
GUI (`sysknife-shell`) is a third implementation of that same gate, not a step
the other two route through.

1. You type a natural-language request.
2. The brain proposes a plan — each step is a **typed action** with
   a risk level (`Low` · `Medium` · `High`).
3. The shell shows the plan with previews, side-effects, and rollback
   metadata.
4. You approve each step explicitly (or set `--yes` up to a risk ceiling).
5. The daemon executes, streams live output, rolls back automatically on
   high-risk failure.
6. Every execution is logged to a hash-chained SQLite or Postgres audit
   trail you can verify with `sysknife audit verify`.

The brain *proposes*; only the daemon is privileged. The daemon *enforces*
policy, executes typed actions, writes the signed chain, and triggers
atomic-host rollback (rpm-ostree) on failure. The trust boundary is
mechanical: no shell strings cross the wire.

## Why not just X?

| Tool | The gap |
|---|---|
| **Open Interpreter** | Runs arbitrary Python/Shell. No formal risk model. No audit chain. |
| **Goose / Continue** | General-purpose. Ad-hoc confirmation, not typed risk levels. |
| **Claude Computer Use** | Uncontrolled desktop automation, not system administration. |
| **Ansible** | YAML written in advance. Not conversational. No risk classification. |
| **shell-gpt / Copilot** | Suggests raw shell commands. You still run raw shell. |
| **AIShell-Gate** | Closest peer, but proprietary and closed; audit is symmetric HMAC (the verifier holds the signing secret, so a proof convinces no one else). No rollback. |
| **Manual** | No audit trail. No rollback. One typo = lost work. |

SysKnife is different by construction: typed actions, an Ed25519-signed audit
chain, explicit approval gate, automatic rollback for atomic-host (rpm-ostree)
changes, polkit-mediated privilege boundary. The AI never holds a shell. See the
full [SysKnife vs. alternatives](docs/comparison.md) breakdown (AIShell-Gate,
gate-oc-audit, MCP gateways, generic mcp-shell).

## Status

The trust chain is built, tested, and shipping. Multi-distro is the active
milestone.

| Component | State |
|---|---|
| `sysknife-brain` — LLM planner, tool loop, safety fence | ✅ |
| `sysknife-daemon` — 190 typed actions, auth, preview, transactions | ✅ |
| Live IPC + streaming + atomic-host rollback (rpm-ostree) | ✅ |
| Terminal approval gate — one-time, TTL-bounded receipts | ✅ |
| MCP server (Claude Code / Cursor / any MCP client) | ✅ |
| Tamper-evident Ed25519-signed audit chain | ✅ |
| RFC 5424 syslog forwarding (Splunk / Sentinel / QRadar) | ✅ |
| Postgres backend (RDS / Cloud SQL / Neon / Supabase) | ✅ |
| **Ubuntu support** — 79/79 stories on a live 22.04 VM, recorded in `tests/evidence/story-runs/` | ✅ |
| **Every Ubuntu LTS validated** — 22.04, 24.04 and 26.04 all at 79/79, each with a replay twin that reproduces it | ✅ |
| Telegram approval interface | 📋 roadmap |

**1,759 Rust tests and 72 frontend tests** form the current deterministic
release baseline.

## Configure your LLM

SysKnife works with **Ollama** (no key, recommended for privacy / offline /
homelab) or **OpenAI**, **Anthropic**, **Gemini**, **Groq**, **DeepSeek**,
**Mistral**, **xAI**.

```toml
# ~/.config/sysknife/config.toml
[llm]
provider     = "ollama"          # or anthropic / openai / gemini / groq / ...
model        = "qwen3:8b"        # provider-specific
ollama_url   = "http://localhost:11434"
max_turns    = 10

[daemon]
socket   = "/run/sysknife/daemon.sock"
database = "/var/lib/sysknife/daemon.sqlite"

[storage]                         # production-recommended
backend = "postgres"
url     = "postgres://sysknife:${PG_PASSWORD}@db.example.com/audit?sslmode=verify-full"
```

Env vars always win over the config file. Full reference in
[`docs/configuration.md`](docs/configuration.md).

## MCP protocol

SysKnife implements the [Model Context Protocol](https://modelcontextprotocol.io/)
and exposes approval-gated planning and execution tools. `sysknife_plan`
returns a daemon-issued transaction ID for each step. After reviewing the
plan, the user runs `sysknife approve <transaction-id>` in a real terminal and
gives the one-time receipt to the agent. `sysknife_execute` rejects missing,
expired, mismatched, or replayed receipts. The MCP server cannot mint approval
receipts itself.

Use the setup wizard (above) to wire it into Claude Code, Cursor, or Codex CLI.
All config files that may contain API keys are created with `chmod 0600`.

## Roadmap

See [ROADMAP.md](ROADMAP.md) for the full milestone breakdown.

- ✅ **Ubuntu 22.04** — 79/79 stories on a live VM (recorded in `tests/evidence/story-runs/`)
- ✅ **Ubuntu 24.04 and 26.04** — 79/79 and 79/79 on live VMs; every LTS run has a replay twin that reproduces it
- 📋 Telegram inline-button approvals
- 📋 `sysknife audit export` (CEF / NDJSON for SIEM ingest)
- 📋 Fleet plan/execute (one plan, N targets, parallel approval)

## Protocol

SysKnife is the reference implementation of the **LACS (Linux Agent Control
Standard)** protocol — typed actions, risk classification, approval gates,
audit requirements. The spec is CC0 (public domain):

→ **[lacs-project/specification](https://github.com/lacs-project/specification)**

Other implementations for other distros and languages are explicitly
encouraged.

## Contributing

We want help. **Multi-distro** is the highest-impact area to plug into right
now — see [`docs/distro-support.md`](docs/distro-support.md) for the
roadmap matrix and [`CONTRIBUTING.md`](CONTRIBUTING.md) for the workflow.

Issues labelled
[`good first issue`](https://github.com/lacs-project/sysknife/labels/good%20first%20issue)
are scoped with clear acceptance criteria.

## Documentation

- [Typed actions — why never a shell string](docs/typed-actions.md)
- [Action reference — every action, generated from the code](docs/action-reference.md)
- [The audit chain — Ed25519, public-key verifiable](docs/the-audit-chain.md)
- [Automatic rollback](docs/automatic-rollback.md)
- [SysKnife vs. alternatives](docs/comparison.md)
- [Architecture overview](docs/architecture.md)
- [Distro support matrix](docs/distro-support.md)
- [Configuration](docs/configuration.md)
- [Audit storage and recovery](docs/storage-cloud.md)
- [Developer guide](docs/developer-guide.md)
- [Testing guide](docs/contributing/testing.md)
- [VM daemon setup](docs/vm-daemon-setup.md)
- [Security policy](SECURITY.md)
- [Release readiness checklist](docs/release-readiness.md)
- [Roadmap](ROADMAP.md)
- [ADR 0001 — System boundaries](docs/adr/0001-system-boundaries.md)
- [ADR 0002 — Brain provider layer](docs/adr/0002-brain-provider-layer.md)
- [ADR 0003 — IPC wire protocol](docs/adr/0003-ipc-wire-protocol.md)

## Where to find SysKnife

| Channel | Install | Notes |
|---------|---------|-------|
| **npm** | `npx sysknife-setup` | [npmjs.com/package/sysknife-setup](https://www.npmjs.com/package/sysknife-setup) — setup wizard; needs Node 18+, no compile |
| **crates.io** | `cargo install sysknife-cli` / `cargo install sysknife-daemon` | Needs `build-essential`; ~7-12 min build. Published by reviewed version tags; see [docs/release.md](docs/release.md) |
| **MCP Registry** | `io.github.lacs-project/sysknife` | [registry.modelcontextprotocol.io](https://registry.modelcontextprotocol.io) — resolves to the crates.io install above. Directory pages that sandbox a server list every tool but cannot call the ones needing the daemon; [docs/mcp-registry.md](docs/mcp-registry.md#what-a-directory-sandbox-can-and-cannot-tell-you) explains the split |
| **GitHub Releases** | Download from [Releases](https://github.com/lacs-project/sysknife/releases) | Prebuilt x86_64 + aarch64 binaries with SHA-256 checksums on every tag |

## License

[MIT](LICENSE). Free to use, modify, distribute, and embed in proprietary
products without restriction.

The [LACS specification](https://github.com/lacs-project/specification) is
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) — public domain.

---

<p align="center">
  Built by <a href="https://github.com/vladimirrott">Vladimir Rotariu</a>.
  ·
  Issues, ideas, war stories — <a href="https://github.com/lacs-project/sysknife/discussions">come say hi</a>.
</p>
