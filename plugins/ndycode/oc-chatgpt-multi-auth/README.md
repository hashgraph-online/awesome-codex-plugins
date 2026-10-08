# oc-codex-multi-auth

[![npm version](https://img.shields.io/npm/v/oc-codex-multi-auth.svg)](https://www.npmjs.com/package/oc-codex-multi-auth)
[![npm downloads](https://img.shields.io/npm/dw/oc-codex-multi-auth.svg)](https://www.npmjs.com/package/oc-codex-multi-auth)
[![CI](https://github.com/ndycode/oc-codex-multi-auth/actions/workflows/ci.yml/badge.svg)](https://github.com/ndycode/oc-codex-multi-auth/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/npm/l/oc-codex-multi-auth.svg)](LICENSE)

<img width="1227" height="702" alt="oc-codex-multi-auth OpenAI accounts picker in OpenCode — add accounts, check quotas, and per-account health" src="https://github.com/user-attachments/assets/b796eb2f-282e-468a-ba6a-acadf09d731b" />

`oc-codex-multi-auth` is an OpenCode plugin that runs Codex-style GPT models on your ChatGPT Plus/Pro subscription over OAuth. It keeps a named pool of ChatGPT accounts on your machine, rotates across them per request with health- and quota-aware selection, shows quota in the TUI prompt line, and ships a 24-tool `codex-*` command kit plus a standalone CLI. Account state stays local under `~/.opencode`.

Use it when one ChatGPT account is not enough: you hit rate limits or quota windows, you split work across accounts and projects, or you run unattended agents that need JSON diagnostics and safe repair commands instead of one opaque auth file.

Using the official Codex CLI rather than OpenCode? The sibling project [`codex-multi-auth`](https://github.com/ndycode/codex-multi-auth) manages the same kind of account pool for `codex` itself.

## What it does

- **Account pool** — OAuth login for multiple ChatGPT accounts, stored locally under `~/.opencode`, with per-project pools under `projects/<project-key>/` on by default.
- **Rotation** — health-scored hybrid selection picks the best enabled account per request, with cooldowns, automatic token refresh, and failover on rate limits.
- **Model catalog** — 11 base models covering 59 variants: GPT-6.1 Sol, GPT-6 Astra/Sol/Luna, the GPT-5.6 tiers, GPT-5.5, and more, routed through the stateless Codex contract (`store: false` + `reasoning.encrypted_content`).
- **Quota in the prompt** — the TUI prompt line shows remaining quota for the serving account, the whole pool, or banked reset credits, with rotating screens.
- **`codex-*` tools** — 24 in-session tools for switching, labeling, tagging, limits, diagnostics, and repair.
- **Standalone CLI** — the same package runs `status`, `list`, `limits`, `doctor`, and friends directly — no agent, no token cost.
- **OpenCode V2** — OpenCode 2.0.16+ loads the plugin through a V2 adapter that shares the account pool and request pipeline.
- **Keychain option** — `CODEX_KEYCHAIN=1` stores the pool in macOS Keychain, Windows Credential Manager, or Linux libsecret.

## Install

Requires Node.js `>=22.19` and [OpenCode](https://opencode.ai).

```bash
npx -y oc-codex-multi-auth@latest
```

> [!NOTE]
> The former package name `oc-chatgpt-multi-auth` is retired. Install `oc-codex-multi-auth` for all new setups; see [docs/faq.md](docs/faq.md) for the rename details.

With no flag, the installer only registers the plugin: it adds the plugin entry to `~/.config/opencode/opencode.json`, enables the TUI quota plugin in `~/.config/opencode/tui.json`, and refreshes the cached package. Your existing `provider.openai` model config is left alone. Add a flag to also install a model catalog:

| Flag | Effect |
| --- | --- |
| (none) / `--plugin-only` | Register the plugin entries only |
| `--modern` | Also install the compact catalog: 11 base models with 59 variants |
| `--full` | Also install the compact bases plus 59 explicit selector IDs (`openai/gpt-5.5-medium`) |
| `--legacy` | Install the explicit-only catalog (59 entries) for older OpenCode |
| `--v2` | Register for OpenCode V2 instead (plugin only; see below) |
| `--dry-run` | Show what would change without writing |
| `--no-cache-clear` | Skip clearing the OpenCode plugin cache |
| `--version` | Print the installed version |

Both `opencode.json` and `opencode.jsonc` are supported, comments and trailing commas included. Changed files are backed up first, and the installer refuses to overwrite a config it cannot parse.

To update later without touching either config file:

```bash
npx -y oc-codex-multi-auth@latest update
```

Removal is manual — see [Uninstall / disable](docs/getting-started.md#uninstall--disable).

## Quick start (5 minutes)

```bash
# 1. Sign in a ChatGPT account (browser OAuth, loopback callback on localhost:1455)
opencode auth login            # choose OpenAI, then a Codex OAuth method

# 2. Repeat login per account, then inspect the pool
oc-codex-multi-auth status
oc-codex-multi-auth limits

# 3. Diagnose anything off
oc-codex-multi-auth doctor

# 4. Run a first prompt (catalog installs only)
opencode run "Explain this repository" --model=openai/gpt-5.5 --variant=medium
```

Headless or remote shell? Four OAuth methods are available (browser, open URL manually, device code, manual URL paste) — see [Getting Started](docs/getting-started.md).

## OpenCode V2

OpenCode **2.0.16+** loads the plugin through a V2 adapter; the account pool, OAuth login, and request pipeline are shared with V1.

```bash
npx -y oc-codex-multi-auth@latest --v2
opencode service restart
opencode auth login   # OpenAI -> Codex OAuth (Add account — ChatGPT Plus/Pro)
```

`--v2` writes a `plugins` entry only — no model catalog — and refuses an existing `opencode.jsonc` or V1 `plugin` entries rather than migrating them (edit the JSONC `plugins` list by hand instead). In V2, tool names normalize to `codex_list`, `codex_switch`, and so on; `/codex-accounts` and the **Codex accounts** palette command list the pool, and **Codex quota details** shows quota. V1's entrypoint remains for OpenCode 1.18.29+. See [Troubleshooting](docs/troubleshooting.md) for V2-specific issues.

## Command map

Two surfaces: **25 `codex-*` tools** inside an OpenCode session, and a standalone CLI for everything else. The full argument reference is in [docs/tools-and-cli.md](docs/tools-and-cli.md).

| Group | Tools | Purpose |
| --- | --- | --- |
| Setup | `codex-setup`, `codex-help`, `codex-next` | guided first-run checklist, help by topic, suggested next action |
| Accounts | `codex-status`, `codex-list`, `codex-switch`, `codex-enable`, `codex-remove` | inspect the pool, pin or switch the active account, re-enable or drop entries |
| Identity | `codex-label`, `codex-tag`, `codex-note` | name accounts, group them with tags, attach private notes |
| Quota | `codex-limits`, `codex-warm`, `codex-reset` | per-account and pool quota, open usage windows, banked reset credits |
| Health | `codex-health`, `codex-doctor`, `codex-diag`, `codex-dashboard`, `codex-metrics`, `codex-refresh` | health view, diagnostics plus safe repairs, redacted snapshots, counters |
| Routing | `codex-pool` | pin models to preferred accounts |
| Backup | `codex-export` / `codex-import`, `codex-diff`, `codex-keychain` | export/restore storage (import previews with `dryRun=true`), compare snapshots, manage the credential backend |

Everyday standalone commands:

```bash
oc-codex-multi-auth status      # pool summary + storagePath
oc-codex-multi-auth list        # accounts, --tag <name> to filter
oc-codex-multi-auth limits      # 5h/weekly usage; --sort account|usage|reset --asc|--desc --refresh
oc-codex-multi-auth warm        # open every enabled account's usage window
oc-codex-multi-auth doctor      # diagnostics; --deep, --fix
oc-codex-multi-auth diag        # alias for doctor --deep
oc-codex-multi-auth health      # local token/account health
oc-codex-multi-auth dashboard   # dashboard guidance
```

These accept `--json` and `--config-path <file>` (`install`/`update` reject `--config-path`); `status`/`list`/`limits` redact identifiers unless `--include-sensitive` is passed. Via npx: `npx -y oc-codex-multi-auth@latest status --json`.

## Rotation, in one paragraph

Each request picks the healthiest enabled account (`rotationStrategy`, default `hybrid`): health scores drop on failures and rate limits, cooldowns keep a burned account out of the running, tokens refresh as needed, and failover walks the pool within a bounded retry budget. Logging into the same account again updates its entry rather than duplicating it. Pools are **per-project by default** — the plugin walks up from the working directory looking for a project marker (`.git`, `package.json`, `.opencode`, and friends), stopping at your home directory; without a marker it uses global storage. Set `CODEX_AUTH_PER_PROJECT_ACCOUNTS=0` to force the global pool.

Accounts whose plan quota is used up are left alone until it resets, even when they hold Codex credits. Set `spendCredits: true` to spend those credits once no account has plan quota left; a toast names the account and its remaining balance. See [Spending Codex credits](docs/configuration.md#spending-codex-credits).

## Models

`--modern` and `--full` install **11 base models** covering **59 variants** (selectable via `--variant`); `--legacy` installs the 59 as explicit IDs.

| Base | Notes |
| --- | --- |
| `gpt-6.1-sol` | newest workhorse; the OpenAI Codex catalog's default since 2026-09-29 |
| `gpt-6-astra` | frontier; rolled out 2026-09-03 |
| `gpt-6-sol` | workhorse coding model |
| `gpt-6-luna` | fast, affordable |
| `gpt-5.6-sol`, `gpt-5.6-terra`, `gpt-5.6-luna` | GPT-5.6 tiers; entitlement-gated |
| `gpt-5.5`, `gpt-5.5-fast` | retires from Codex 2026-10-14 |
| `gpt-5.4-nano` | |
| `gpt-5.1` | |

GPT-6 and GPT-5.6 models use the responses-lite request shape and the `opencode` client identity; other models use `codex_cli_rs`. Requests stay stateless: `store: false` with `reasoning.encrypted_content` for multi-turn continuity.

Retired IDs still route if typed — `gpt-5.4-mini`, `gpt-5-codex`, `gpt-5.1-codex`, `gpt-5.1-codex-max`, and `gpt-5.1-codex-mini` are rescued by the default fallback chains. The Daybreak-gated tiers (`gpt-daybreak-blue-latest`, `gpt-daybreak-red-latest`, `gpt-5.6-cyber`) are routed but deliberately not shipped; add them by hand if your workspace is approved. Full chain details live in [docs/configuration.md](docs/configuration.md).

## Quota status

The TUI prompt line shows quota for the account that served the last request. `quotaStatus.mode` in `~/.opencode/openai-codex-auth-config.json` controls it:

- `active` (default): the serving account's remaining quota
- `overview`: the whole pool on one line, weighted by plan
- `resets`: banked rate-limit reset credits
- `credits`: accounts that still hold Codex credits once plan quota is gone

Pass a list (`["overview", "resets"]`) to rotate screens every `rotateMs` (default 5s). Percentages read as headroom left; set `quotaDisplay: "used"` to show consumption. All layout and forecast options are documented in [docs/configuration.md](docs/configuration.md).

## Where state lives

| File | Path |
| --- | --- |
| Per-project accounts | `~/.opencode/projects/<project-key>/oc-codex-multi-auth-accounts.json` |
| Global accounts | `~/.opencode/oc-codex-multi-auth-accounts.json` |
| Flagged accounts | `oc-codex-multi-auth-flagged-accounts.json`, beside the active accounts file |
| Pre-write snapshots | `backups/codex-credential-snapshot-*.json`, beside the active accounts file |
| Plugin config | `~/.opencode/openai-codex-auth-config.json` |
| OpenCode config | `~/.config/opencode/opencode.json` (or `opencode.jsonc`) |
| Request logs | `~/.opencode/logs/codex-plugin/`, when logging is enabled |

Plugin settings are re-read per request — most edits need no restart. Boolean env overrides are truthy only for the literal `"1"`. Common ones:

| Setting | Effect |
| --- | --- |
| `CODEX_AUTH_PER_PROJECT_ACCOUNTS=0` | Force the global account pool |
| `CODEX_KEYCHAIN=1` | Store accounts in the OS keychain |
| `CODEX_AUTH_ROTATION_STRATEGY=hybrid\|sticky\|round-robin` | Account selection strategy |
| `CODEX_AUTH_SPEND_CREDITS=1` | Spend Codex credits once no account has plan quota left |
| `CODEX_AUTH_QUOTA_DISPLAY=free\|used` | Quota percentages as headroom (default) or consumption |
| `CODEX_RETRY_ALL_UNBOUNDED=1` | Let "wait as long as the backend asks" apply when every account is rate-limited; otherwise capped at 10 minutes |
| `ENABLE_PLUGIN_REQUEST_LOGGING=1` | Write request metadata logs |
| `CODEX_PLUGIN_LOG_BODIES=1` | Also log raw bodies (sensitive) |

Full reference, field by field: [docs/configuration.md](docs/configuration.md).

## Troubleshooting in 60 seconds

```bash
oc-codex-multi-auth doctor --fix
opencode auth login
```

Most issues resolve by signing in again or running `codex-doctor fix=true` inside a session. The callback listener needs port 1455 free. Symptom-by-symptom fixes: [docs/troubleshooting.md](docs/troubleshooting.md); common questions: [docs/faq.md](docs/faq.md).

## Documentation

| Doc | What it covers |
| --- | --- |
| [docs/index.md](docs/index.md) | Product overview — what it does at runtime and who needs it |
| [docs/README.md](docs/README.md) | Documentation portal and page inventory |
| [docs/getting-started.md](docs/getting-started.md) | Install, login methods, first prompt, uninstall |
| [docs/tools-and-cli.md](docs/tools-and-cli.md) | Full tool/CLI argument reference |
| [docs/configuration.md](docs/configuration.md) | Every config key and env var |
| [docs/upgrade.md](docs/upgrade.md) | Upgrades, package renames, storage migration |
| [docs/architecture.md](docs/architecture.md) | How the pieces fit |
| [docs/troubleshooting.md](docs/troubleshooting.md) / [docs/faq.md](docs/faq.md) | Recovery playbooks and common questions |
| [docs/privacy.md](docs/privacy.md) | What is stored and where |
| [config/README.md](config/README.md) | Modern vs. legacy catalog templates |
| [CHANGELOG.md](CHANGELOG.md) | Release history |
| [docs/development/](docs/development/ARCHITECTURE.md) | Maintainer docs |

## Release notes

- Current stable: [v6.28.0](CHANGELOG.md) — `npx -y oc-codex-multi-auth@latest`
- Full release archive: [CHANGELOG.md](CHANGELOG.md)

## Terms and license

`oc-codex-multi-auth` uses OAuth account credentials and is intended for personal development use with your own ChatGPT Plus/Pro subscription. It is an independent open-source project, not an official OpenAI product; for production or commercial workloads, use the OpenAI Platform API. "ChatGPT", "Codex", and "OpenAI" are trademarks of OpenAI.

MIT license — see [LICENSE](LICENSE).
