# codex-multi-auth

[![npm version](https://img.shields.io/npm/v/codex-multi-auth.svg)](https://www.npmjs.com/package/codex-multi-auth)
[![npm downloads](https://img.shields.io/npm/dw/codex-multi-auth.svg)](https://www.npmjs.com/package/codex-multi-auth)
[![CI](https://github.com/ndycode/codex-multi-auth/actions/workflows/ci.yml/badge.svg)](https://github.com/ndycode/codex-multi-auth/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/npm/l/codex-multi-auth.svg)](LICENSE)

<img width="1270" height="729" alt="codex-multi-auth terminal dashboard for Codex CLI multi-account OAuth account status" src="https://github.com/user-attachments/assets/0cecb77e-a6d3-432a-ba48-3577db0c7093" />

`codex-multi-auth` is a multi-account OAuth manager for the official `@openai/codex` CLI. It keeps a named pool of ChatGPT sign-ins on your machine, lets you switch the active account, and — when you run Codex through its optional wrapper — rotates accounts across live requests through a loopback-only proxy. It never installs or shadows a `codex` binary; the official OpenAI install keeps owning that command.

Use it when one Codex account is not enough: you hit rate limits or quota windows, you split work across organizations and workspaces, you want per-project account pools, or you run unattended agents that need JSON diagnostics and safe repair commands instead of one opaque auth file.

Using OpenCode rather than the Codex CLI? The sibling project [`oc-codex-multi-auth`](https://github.com/ndycode/oc-codex-multi-auth) is the plugin that manages the same kind of account pool there.

## What it does

- **Account pool** — OAuth login for multiple ChatGPT accounts, stored locally under `~/.codex/multi-auth` (files `0600`, directories `0700`), with per-project pools under `projects/<project-key>/`.
- **Switching and selection** — pin an account, pick the forecast-best one, or let health- and quota-aware hybrid selection rotate for you.
- **Runtime rotation** — a default-on, loopback-only proxy that forwards Responses API and model-discovery traffic through the best available account during wrapper-launched Codex sessions.
- **Diagnostics and repair** — status, live health checks, quota forecasts, JSON reports, and `fix`/`doctor`/`verify` commands that recover stale or damaged local state.
- **Local governance** — file-backed usage ledger, budget guards, account tags/weights/pause/drain policies, routing profiles, and an optional loopback bridge with bearer tokens for local OpenAI-compatible clients.
- **Desktop routing (optional)** — a reversible bind of the packaged Codex app plus user-level launcher helpers; official app binaries are never patched.

## The four binaries

| Binary | Role |
| --- | --- |
| `codex-multi-auth` | The account manager. Runs all 31 management subcommands locally (`login`, `status`, `switch`, `forecast`, `rotation`, `fix`, ...). The `auth` prefix is optional: `codex-multi-auth login` ≡ `codex-multi-auth auth login`. |
| `codex-multi-auth-codex` | Opt-in wrapper. Handles `auth ...` locally and forwards every other command to the official Codex CLI, enabling the rotation proxy for request-bearing commands. |
| `mcodex` | Convenience launcher over the wrapper, with optional `--monitor` and `--tmux` modes. No account logic of its own. |
| `codex-multi-auth-app-launcher` | User-level OS launcher routing helper (Windows shortcut, macOS wrapper app, Linux `.desktop`). |

## Install

Requirements: Node.js >= 22.19, and the official Codex CLI on `PATH` (`npm i -g @openai/codex`, Homebrew, or a release binary).

```bash
npm i -g codex-multi-auth
```

> [!NOTE]
> The legacy scoped prerelease `@ndycode/codex-multi-auth` is migration-only. Install `codex-multi-auth` for all new setups; see [docs/upgrade.md](docs/upgrade.md) to migrate.

## Quick start (5 minutes)

```bash
# 1. Sign in a ChatGPT account (browser OAuth, loopback callback on localhost:1455)
codex-multi-auth login

# 2. Repeat login to add more accounts, then inspect the pool
codex-multi-auth status

# 3. Probe account health and preview which account would serve next
codex-multi-auth check
codex-multi-auth forecast --live
```

Headless or remote shell? Use `codex-multi-auth login --device-auth` — no callback port needed. Blocked browser? See [alternate login paths](docs/getting-started.md#log-in).

Run Codex through the wrapper so requests rotate across the pool:

```bash
codex-multi-auth-codex          # interactive TUI, rotation on by default
codex-multi-auth-codex exec "summarize this repo"
mcodex                          # same wrapper, shorter name
```

## Command map

`codex-multi-auth` ships 31 subcommands. The full surface — every flag, hotkey, and JSON mode — is in [docs/reference/commands.md](docs/reference/commands.md).

| Group | Commands | Purpose |
| --- | --- | --- |
| Accounts | `login`, `list`, `status`, `switch <i>`, `unpin`, `workspace` | sign in, inspect the pool, pin or switch the active account, pick workspaces |
| Selection | `forecast`, `best`, `why-selected`, `check`, `limits`, `models` | preview, explain, and probe which account serves the next request |
| Runtime | `rotation status` `enable` `disable` `bind-app` `unbind-app` `reset-runtime` `reset-rate-limits` | inspect and control live rotation and the app bind |
| Repair | `fix`, `doctor`, `report`, `verify`, `verify-flagged`, `uninstall` | diagnose and repair storage, flagged accounts, and install residue; machine-readable health report |
| Governance | `usage`, `budget`, `account`, `monitor`, `history`, `resets` | usage ledger, budget limits, tags/weights/pause/drain, snapshots |
| Local clients | `bridge`, `integrations` | bearer tokens and client snippets for the loopback bridge |
| Config | `config explain` `template`, `init-config`, `debug bundle`, `features` | effective-config report, config templates, sanitized debug bundle |

Everyday examples:

```bash
codex-multi-auth switch 2                     # pin account #2
codex-multi-auth report --live --json         # full machine-readable health report
codex-multi-auth fix --live --model gpt-6.1-sol   # live repair probes with a chosen model
codex-multi-auth doctor --fix                 # diagnose and apply the safest fixes
codex-multi-auth usage --since 24h --by model # local usage ledger summary
codex-multi-auth rotation status              # is live rotation enabled?
```

## Runtime rotation, in one paragraph

With rotation on (the default), request-bearing wrapper commands — `exec`, `review`, `resume`, `fork`, `app`, and the bare TUI — route through a local proxy that picks the healthiest account per request, refreshes tokens as needed, and fails over across the pool on rate limits within a bounded retry budget. The proxy listens on loopback only, authenticates its own clients with a per-process token, forwards only Responses API, model-discovery, image, and thread-goal calls, and never writes account emails or tokens to client headers or logs. Plain `codex` is never touched: rotation exists only inside `codex-multi-auth-codex`/`mcodex` sessions, or inside the packaged desktop app after an opt-in, reversible bind. Turn it off with `codex-multi-auth rotation disable` or `CODEX_MULTI_AUTH_RUNTIME_ROTATION_PROXY=0`.

## Where state lives

| What | Path |
| --- | --- |
| Accounts, settings, quota cache, usage ledger, policies, observability | `~/.codex/multi-auth/` |
| Per-project account pools | `~/.codex/multi-auth/projects/<project-key>/` |
| Official Codex state (kept by the official install) | `~/.codex/` |
| Override the multi-auth root | `CODEX_MULTI_AUTH_DIR=<path>` |

Full path map: [docs/reference/storage-paths.md](docs/reference/storage-paths.md).

## Troubleshooting in 60 seconds

```bash
codex-multi-auth doctor --fix
codex-multi-auth check
codex-multi-auth forecast --live
```

Common symptoms — wrong active account, OAuth callback port `1455` already bound, Windows/WSL port contention, `EBUSY`/`EPERM` on Windows — are covered in [docs/troubleshooting.md](docs/troubleshooting.md).

## Documentation

| Doc | What it covers |
| --- | --- |
| [docs/index.md](docs/index.md) | Product overview — what it does at runtime and who needs it |
| [docs/README.md](docs/README.md) | Full documentation portal and sitemap |
| [docs/getting-started.md](docs/getting-started.md) | Install, first login, day-1 commands |
| [docs/features.md](docs/features.md) | Feature tour |
| [docs/architecture.md](docs/architecture.md) | Components, request flow, trust boundaries |
| [docs/configuration.md](docs/configuration.md) | Settings and environment overrides |
| [docs/reference/commands.md](docs/reference/commands.md) | Every command, flag, and hotkey |
| [docs/reference/public-api.md](docs/reference/public-api.md) | Public API stability tiers and semver contract |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Recovery playbooks |
| [docs/faq.md](docs/faq.md) | Common questions |
| [docs/upgrade.md](docs/upgrade.md) | Version and legacy-package migration |
| [docs/privacy.md](docs/privacy.md) | Data handling and local storage behavior |
| [config/README.md](config/README.md) | Modern vs. legacy catalog templates |
| [CHANGELOG.md](CHANGELOG.md) | Release history (short version) |

## Release notes

- Current stable: [v2.19.1](docs/releases/v2.19.1.md) — `npm i -g codex-multi-auth`
- Earlier stable lines: [v2.6.0](docs/releases/v2.6.0.md), [v2.5.0](docs/releases/v2.5.0.md)
- Full release archive: [docs/README.md#release-history](docs/README.md#release-history)

## Terms and license

`codex-multi-auth` uses OAuth account credentials and is intended for personal development use. It is an independent open-source project, not an official OpenAI product; you are responsible for your own usage and policy compliance, and for production or commercial workloads you should use the OpenAI Platform API. "ChatGPT", "Codex", and "OpenAI" are trademarks of OpenAI.

MIT license — see [LICENSE](LICENSE).
