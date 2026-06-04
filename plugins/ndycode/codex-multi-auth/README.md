# codex-multi-auth: multi-account OAuth for the official Codex CLI

[![npm version](https://img.shields.io/npm/v/codex-multi-auth.svg)](https://www.npmjs.com/package/codex-multi-auth)
[![npm downloads](https://img.shields.io/npm/dw/codex-multi-auth.svg)](https://www.npmjs.com/package/codex-multi-auth)
[![CI](https://github.com/ndycode/codex-multi-auth/actions/workflows/ci.yml/badge.svg)](https://github.com/ndycode/codex-multi-auth/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/npm/l/codex-multi-auth.svg)](LICENSE)

`codex-multi-auth` is a multi-account OAuth manager for the official `@openai/codex` CLI. It gives Codex CLI users explicit ChatGPT account login, account switching, health checks, local diagnostics, project-scoped storage, and default-on runtime Responses rotation without taking over the official `codex` binary. Use `codex-multi-auth ...` for account management, or `codex-multi-auth-codex ...` only when you intentionally want the optional forwarding wrapper.

Use it when you need a local Codex CLI multi-account workflow with visible account state, safer recovery commands, and a loopback-only runtime rotation proxy for request-bearing forwarded Codex sessions.

<img width="1270" height="729" alt="codex-multi-auth terminal dashboard for Codex CLI multi-account OAuth account status" src="https://github.com/user-attachments/assets/0cecb77e-a6d3-432a-ba48-3577db0c7093" />



> [!NOTE]
> Legacy scoped prerelease package `@ndycode/codex-multi-auth` is migration-only.
> Use `codex-multi-auth` for all new installs.

## What You Get

- Codex CLI multi-account OAuth management with a dedicated `codex-multi-auth ...` command family
- Explicit ChatGPT account login, saved-account listing, account switching, health checks, and diagnostics
- Optional `codex-multi-auth-codex ...` forwarding wrapper for official Codex CLI commands when you choose wrapper-launched sessions
- Health-aware account selection, quota forecasting, automatic failover, and flagged-account recovery
- Project-scoped account storage under `~/.codex/multi-auth/projects/<project-key>/...` for repo-specific workflows
- Interactive terminal dashboard for account actions, settings, search, and hotkeys
- Forecast, report, fix, doctor, verify, monitor, and rotation commands for operational confidence
- Local usage ledger, budget guards, account policy controls, routing profiles, and model/account capability views
- Runtime counters, budget/cooldown state, and multi-auth probe visibility in `codex-multi-auth status` / `codex-multi-auth report`
- Default-on loopback Responses proxy for live account rotation inside forwarded Codex CLI/app sessions
- Optional loopback-only local bridge for `/health`, `/v1/models`, and `/v1/responses`, protected by hashed local client tokens
- Reversible packaged Codex app bind and user-level launcher routing helpers that do not patch official app binaries
- Session affinity, live account sync, proactive refresh, and preemptive quota deferral controls
- Codex-oriented request/prompt compatibility with strict runtime handling and documented error contracts
- Stable docs for install, configuration, troubleshooting, upgrade, public API, storage paths, and release notes

---

## Why Developers Use It

`codex-multi-auth` makes local Codex account state visible and recoverable. Instead of one opaque auth file, you get a named account pool, deterministic account switching, health-aware selection, JSON diagnostics for automation, and safe repair commands for stale or damaged local state. The architecture is designed for personal development workflows: credentials stay local, runtime rotation is loopback-only, and official Codex install paths keep owning the `codex` command.

---

## Current Architecture At A Glance

`codex-multi-auth` now ships three distinct global binaries:

| Binary | Purpose |
| --- | --- |
| `codex-multi-auth` | Primary account manager; accepts bare auth subcommands such as `login`, `status`, `switch`, `forecast`, and `rotation status` |
| `codex-multi-auth-codex` | Optional wrapper that handles `auth ...` locally and forwards every other command to the official Codex CLI |
| `codex-multi-auth-app-launcher` | Optional desktop launcher helper for supported user-level shortcuts and wrapper apps |

The package does not publish a global `codex` binary. Keep `codex` owned by the official OpenAI install path and use `codex-multi-auth-codex ...` only when you intentionally want this package's forwarding wrapper.

---

<details open>
<summary><b>Terms and Usage Notice</b></summary>

> [!CAUTION]
> This project uses OAuth account credentials and is intended for personal development use.
>
> By using this package, you acknowledge:
> - This is an independent open-source project, not an official OpenAI product
> - You are responsible for your own usage and policy compliance
> - For production/commercial workloads, use the OpenAI Platform API

</details>

---

## Installation

<details open>
<summary><b>For Humans</b></summary>

### Option A: Standard install

```bash
npm i -g codex-multi-auth
```

### Option B: Migrate from legacy scoped prerelease

```bash
npm uninstall -g @ndycode/codex-multi-auth
npm i -g codex-multi-auth
```

### Option C: Verify wiring

`codex --version` confirms the official Codex CLI is reachable. `codex-multi-auth --version` confirms the installed manager package version. `codex-multi-auth-codex --version` is the optional forwarding wrapper entrypoint.

```bash
codex --version
codex-multi-auth --version
codex-multi-auth status
```

Any official install path is fine as long as `codex` is on `PATH`: `npm i -g @openai/codex`, `brew install --cask codex`, or an official release binary.

</details>

<details>
<summary><b>For LLM Agents</b></summary>

### Step-by-step

1. Install global package:
   - `npm i -g codex-multi-auth`
2. Run first login flow with `codex-multi-auth login`
3. Validate state with `codex-multi-auth status` and `codex-multi-auth check`
4. Confirm routing with `codex-multi-auth forecast --live`

### Verification

```bash
codex-multi-auth status
codex-multi-auth check
```

</details>

---

## Quick Start

Install and sign in:

```bash
npm i -g @openai/codex
npm i -g codex-multi-auth
codex-multi-auth login
```

If you already installed the official native CLI via Homebrew or a release binary, you only need:

```bash
npm i -g codex-multi-auth
codex-multi-auth login
```

Verify the manager and the new account:

```bash
codex-multi-auth status
codex-multi-auth check
```

Use these next:

```bash
codex-multi-auth list
codex-multi-auth switch 2
codex-multi-auth forecast --live
```

If browser launch is blocked, use the alternate login paths in [docs/getting-started.md](docs/getting-started.md#alternate-login-paths).
For remote or headless shells, prefer `codex-multi-auth login --device-auth`.

---

## Command Toolkit

### Start here

| Command | What it answers |
| --- | --- |
| `codex-multi-auth login` | How do I add or re-open the account menu? |
| `codex-multi-auth status` | Is the wrapper active right now? |
| `codex-multi-auth check` | Do my saved accounts look healthy? |

### Daily use

| Command | What it answers |
| --- | --- |
| `codex-multi-auth list` | Which accounts are saved and which one is active? |
| `codex-multi-auth switch <index>` | How do I move to a different saved account? |
| `codex-multi-auth forecast --live` | Which account looks best for the next session? |

### Repair

| Command | What it answers |
| --- | --- |
| `codex-multi-auth verify-flagged` | Can any previously flagged account be restored? |
| `codex-multi-auth verify --paths` | Do my storage path chain and sandbox probes still pass self-test? |
| `codex-multi-auth fix --dry-run` | What safe storage or account repairs are available? |
| `codex-multi-auth doctor --fix` | Can the CLI diagnose and apply the safest fixes now? |
| `codex-multi-auth uninstall` | Remove residual artifacts (run BEFORE `npm uninstall`; npm@7+ no longer fires `preuninstall`) |

### Advanced

| Command | What it answers |
| --- | --- |
| `codex-multi-auth report --live --json` | How do I get the full machine-readable health report? |
| `codex-multi-auth fix --live --model gpt-5.5` | How do I run live repair probes with a chosen model? |
| `codex-multi-auth why-selected --json` | Which account does the selector pick now, and why? |
| `codex-multi-auth usage --since 24h --by project` | What local usage has been recorded recently? |
| `codex-multi-auth monitor --json` | What is the combined usage, policy, quota, runtime, and project state? |
| `codex-multi-auth bridge token create --label local-client` | How do I create a local bridge bearer token? |
| `codex-multi-auth integrations --kind python` | How do I generate local bridge client snippets? |
| `codex-multi-auth rotation status` | Is live runtime account rotation enabled for forwarded Codex sessions? |

### Reliability behavior

- whole-pool replay is disabled by default when every account is rate-limited
- active requests use a bounded outbound request budget so one prompt cannot walk the full pool indefinitely
- repeated cross-account 5xx bursts trigger a short cooldown instead of continuing aggressive rotation
- proactive refresh is staggered to reduce background refresh bursts
- `codex-multi-auth status` surfaces recent runtime request metrics in text output, and `codex-multi-auth report --json` exposes the machine-readable cooldown/runtime snapshot

---

## Dashboard Hotkeys

### Main dashboard

| Key | Action |
| --- | --- |
| `Up` / `Down` | Move selection |
| `Enter` | Select/open |
| `1-9` | Quick switch |
| `/` | Search |
| `?` | Toggle help |
| `Q` | Back/cancel |

### Account details

| Key | Action |
| --- | --- |
| `S` | Set current account |
| `R` | Refresh/re-login account |
| `E` | Enable/disable account |
| `D` | Delete account |

---

## Storage Paths

| File | Default path |
| --- | --- |
| Settings | `~/.codex/multi-auth/settings.json` |
| Accounts | `~/.codex/multi-auth/openai-codex-accounts.json` |
| Flagged accounts | `~/.codex/multi-auth/openai-codex-flagged-accounts.json` |
| Quota cache | `~/.codex/multi-auth/quota-cache.json` |
| Runtime observability | `~/.codex/multi-auth/runtime-observability.json` |
| Usage ledger | `~/.codex/multi-auth/usage/usage-ledger.jsonl` |
| Account policies | `~/.codex/multi-auth/account-policies.json` |
| Routing profiles | `~/.codex/multi-auth/routing-profiles.json` |
| Budget guards | `~/.codex/multi-auth/budget-guards.json` |
| Local client tokens | `~/.codex/multi-auth/local-client-tokens.json` |
| Runtime app helper status | `~/.codex/multi-auth/runtime-rotation-app-helper.json` |
| Persistent app bind state/logs | `~/.codex/multi-auth/app-bind/` |
| Logs | `~/.codex/multi-auth/logs/codex-plugin/` |
| Per-project accounts | `~/.codex/multi-auth/projects/<project-key>/openai-codex-accounts.json` |

Override root with `CODEX_MULTI_AUTH_DIR=<path>`.

---

## Configuration

Primary config root:
- `~/.codex/multi-auth/settings.json`
- or `CODEX_MULTI_AUTH_DIR/settings.json` when custom root is set

Selected runtime/environment overrides:

| Variable | Effect |
| --- | --- |
| `CODEX_MULTI_AUTH_DIR` | Override settings/accounts root |
| `CODEX_MULTI_AUTH_CONFIG_PATH` | Alternate config file path |
| `CODEX_MODE=0/1` | Disable/enable Codex mode |
| `CODEX_MULTI_AUTH_RUNTIME_ROTATION_PROXY=0/1` | Opt out/in of live Responses proxy rotation for forwarded Codex CLI/app sessions |
| `CODEX_MULTI_AUTH_APP_ROTATION_IDLE_MS=<ms>` | Override automatic Codex app helper idle shutdown |
| `CODEX_MULTI_AUTH_APP_BIND_INSTALL=0/1` | Opt out/in of packaged Codex app bind self-heal during install/update or rotation enable |
| `CODEX_MULTI_AUTH_APP_LAUNCHER_INSTALL=0/1` | Opt out/in of routing supported app shortcuts during install/update or rotation enable |
| `CODEX_TUI_V2=0/1` | Disable/enable TUI v2 |
| `CODEX_TUI_COLOR_PROFILE=truecolor\|ansi256\|ansi16` | TUI color profile |
| `CODEX_TUI_GLYPHS=ascii\|unicode\|auto` | TUI glyph style |
| `CODEX_AUTH_BACKGROUND_RESPONSES=0/1` | Opt in/out of stateful Responses `background: true` compatibility |
| `CODEX_AUTH_FETCH_TIMEOUT_MS=<ms>` | Request timeout override |
| `CODEX_AUTH_STREAM_STALL_TIMEOUT_MS=<ms>` | Stream stall timeout override |

Validate config after changes:

```bash
codex-multi-auth status
codex-multi-auth check
codex-multi-auth forecast --live
```

Responses background mode stays opt-in. Enable `backgroundResponses` in settings or `CODEX_AUTH_BACKGROUND_RESPONSES=1` only for callers that intentionally send `background: true`, because those requests switch from stateless `store=false` routing to stateful `store=true`. See [docs/upgrade.md](docs/upgrade.md) for rollout guidance.

Runtime rotation is enabled by default for request-bearing wrapper-launched Codex sessions. Global install/update self-heals supported packaged Codex app binds and user-level launcher routing when possible, while `codex-multi-auth rotation enable` remains the explicit repair command. `codex-multi-auth rotation disable` turns the setting off and removes the persistent app bind. Set `CODEX_MULTI_AUTH_RUNTIME_ROTATION_PROXY=0`, `CODEX_MULTI_AUTH_APP_BIND_INSTALL=0`, or `CODEX_MULTI_AUTH_APP_LAUNCHER_INSTALL=0` to opt out of the matching default behavior.

Installed wrappers may perform a best-effort daily npm version check during normal forwarded Codex startup. When a newer package is detected, the wrapper only prints a manual notice on an interactive TTY or when `CODEX_MULTI_AUTH_DEBUG=1`: `npm install -g codex-multi-auth@latest`. It never runs npm install or update commands for you.

---

## Experimental Settings Highlights

The Settings menu now includes an `Experimental` section for staged features:

- preview-first sync into `oc-chatgpt-multi-auth`
- named local pool backup export with filename prompt
- refresh guard toggle and interval controls moved out of Backend Controls

These flows are intentionally non-destructive by default: sync previews before apply, destination-only accounts are preserved, and backup filename collisions fail safely.

---

## Troubleshooting

<details open>
<summary><b>60-second recovery</b></summary>

```bash
codex-multi-auth doctor --fix
codex-multi-auth check
codex-multi-auth forecast --live
```

If still broken:

```bash
codex-multi-auth login
```

</details>

<details>
<summary><b>Common symptoms</b></summary>

- `codex-multi-auth` unrecognized: run `where codex-multi-auth` or `which codex-multi-auth`, then follow `docs/troubleshooting.md` for install checks
- Switch succeeds but wrong account appears active: run `codex-multi-auth switch <index>`, then restart session
- Requests fail fast with a pool cooldown message: wait for the cooldown window or inspect `codex-multi-auth status`
- Requests fail fast after repeated upstream 5xx errors: inspect `codex-multi-auth report --json` for runtime traffic and cooldown details
- Storage cleanup fails with `EBUSY` / `EPERM` (Windows): run `codex-multi-auth doctor --fix` to retry, or manually remove `~/.codex/multi-auth/<project-key>/` and re-login
- OAuth callback on port `1455` fails: free the port and re-run `codex-multi-auth login`
- Browser launch is blocked or you are in a headless shell: prefer `codex-multi-auth login --device-auth`; use `codex-multi-auth login --manual` or `CODEX_AUTH_NO_BROWSER=1` only when you need the callback-paste fallback
- `missing field id_token` / `token_expired` / `refresh_token_reused`: re-login affected account

</details>

<details>
<summary><b>Diagnostics pack</b></summary>

```bash
codex-multi-auth list
codex-multi-auth status
codex-multi-auth check
codex-multi-auth verify-flagged --json
codex-multi-auth forecast --live
codex-multi-auth fix --dry-run
codex-multi-auth report --live --json
codex-multi-auth doctor --json
```

</details>

---

## Documentation

- Docs portal: [docs/README.md](docs/README.md)
- Getting started: [docs/getting-started.md](docs/getting-started.md)
- Features: [docs/features.md](docs/features.md)
- Configuration: [docs/configuration.md](docs/configuration.md)
- Troubleshooting: [docs/troubleshooting.md](docs/troubleshooting.md)
- Commands reference: [docs/reference/commands.md](docs/reference/commands.md)
- Public API contract: [docs/reference/public-api.md](docs/reference/public-api.md)
- Error contracts: [docs/reference/error-contracts.md](docs/reference/error-contracts.md)
- Settings reference: [docs/reference/settings.md](docs/reference/settings.md)
- Storage paths: [docs/reference/storage-paths.md](docs/reference/storage-paths.md)
- Upgrade guide: [docs/upgrade.md](docs/upgrade.md)
- Privacy: [docs/privacy.md](docs/privacy.md)

---

## Release Notes

- Current stable: [docs/releases/v2.2.2.md](docs/releases/v2.2.2.md) — install via `npm i -g codex-multi-auth`
- Previous stable: [docs/releases/v2.2.1.md](docs/releases/v2.2.1.md)
- Previous stable: [docs/releases/v2.2.0.md](docs/releases/v2.2.0.md)
- Previous stable: [docs/releases/v2.1.12.md](docs/releases/v2.1.12.md)
- Earlier stable: [docs/releases/v2.1.11.md](docs/releases/v2.1.11.md)
- Earlier stable: [docs/releases/v2.1.10.md](docs/releases/v2.1.10.md)
- Earlier stable: [docs/releases/v2.1.8.md](docs/releases/v2.1.8.md)
- Earlier stable: [docs/releases/v2.1.7.md](docs/releases/v2.1.7.md)
- Earlier stable: [docs/releases/v2.1.6.md](docs/releases/v2.1.6.md)
- Earlier stable: [docs/releases/v2.1.5.md](docs/releases/v2.1.5.md)
- Earlier stable: [docs/releases/v2.1.4.md](docs/releases/v2.1.4.md)
- Earlier stable: [docs/releases/v2.1.3.md](docs/releases/v2.1.3.md)
- Earlier stable: [docs/releases/v2.1.2.md](docs/releases/v2.1.2.md)
- Earlier stable: [docs/releases/v2.1.1.md](docs/releases/v2.1.1.md)
- Earlier stable: [docs/releases/v2.1.0.md](docs/releases/v2.1.0.md)
- Earlier stable: [docs/releases/v1.3.2.md](docs/releases/v1.3.2.md)
- Stable archive: [docs/releases/v1.3.1.md](docs/releases/v1.3.1.md)
- Full release archive: [docs/README.md#release-history](docs/README.md#release-history)
- Archived prerelease: [docs/releases/v0.1.0-beta.0.md](docs/releases/v0.1.0-beta.0.md)

## License

MIT License. See [LICENSE](LICENSE).

<details>
<summary><b>Legal</b></summary>

- Not affiliated with OpenAI.
- "ChatGPT", "Codex", and "OpenAI" are trademarks of OpenAI.
- You assume responsibility for your own usage and compliance.

</details>
