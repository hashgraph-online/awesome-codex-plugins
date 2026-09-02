# oc-codex-multi-auth: ChatGPT OAuth and multi-account Codex routing for OpenCode

[![npm version](https://img.shields.io/npm/v/oc-codex-multi-auth.svg)](https://www.npmjs.com/package/oc-codex-multi-auth)
[![npm downloads](https://img.shields.io/npm/dw/oc-codex-multi-auth.svg)](https://www.npmjs.com/package/oc-codex-multi-auth)
[![CI](https://github.com/ndycode/oc-codex-multi-auth/actions/workflows/ci.yml/badge.svg)](https://github.com/ndycode/oc-codex-multi-auth/actions/workflows/ci.yml)
[![MIT license](https://img.shields.io/npm/l/oc-codex-multi-auth.svg)](LICENSE)

`oc-codex-multi-auth` is an OpenCode plugin for ChatGPT Plus/Pro OAuth, Codex and GPT-5 model routing (including GPT-5.6 Sol/Terra/Luna), multi-account rotation, account switching, health checks, quota visibility, diagnostics, and recovery tools. It installs the OpenCode provider/TUI configuration, registers a 24-tool `codex-*` command toolkit, and routes OpenCode OpenAI SDK requests through the ChatGPT-backed Codex flow with local account state.

Use it when you want OpenCode to run Codex-style coding workflows from your own ChatGPT subscription while keeping accounts visible, switchable, health-checked, and recoverable from the terminal.

<img width="1227" height="702" alt="oc-codex-multi-auth OpenCode plugin dashboard for ChatGPT OAuth, Codex routing, and multi-account health" src="https://github.com/user-attachments/assets/b796eb2f-282e-468a-ba6a-acadf09d731b" />



> [!NOTE]
> This package is the supported OpenCode plugin line.
> Older package names and config entries should be replaced with `oc-codex-multi-auth`.

## What You Get

- OpenCode plugin support for ChatGPT Plus/Pro OAuth and Codex/GPT-5 coding workflows
- GPT-5.6 Sol, Terra, and Luna (responses-lite path) plus GPT-5.5, GPT-5.5 Fast, GPT-5.4 Mini, GPT-5.4 Nano, GPT-5.1, and Codex model templates
- Compact modern OpenCode config with 12 base families and 53 variant presets; explicit legacy selector IDs when needed
- Stateless Codex-compatible request handling with `store: false` and `reasoning.encrypted_content`
- Multi-account rotation with hybrid health scoring, cooldowns, automatic token refresh, and failover
- Explicit saved-account listing, account switching, labeling, tagging, notes, health checks, and diagnostics
- Per-project account storage under `~/.opencode/projects/<project-key>/...`
- Guided setup, doctor, next-action, dashboard, export/import, keychain, and troubleshooting tools
- Optional OS-native keychain backend for stored account pools
- TUI prompt quota status and quota detail views for OpenCode sessions
- Request logging, runtime metrics, routing visibility, and redacted diagnostic snapshots for debugging
- Stable docs for install, configuration, troubleshooting, privacy, architecture, testing, and release history

---

## Why Developers Use It

`oc-codex-multi-auth` makes OpenCode's ChatGPT OAuth state understandable and operable. Instead of treating auth as one opaque provider file, you get a local account pool, deterministic account switching, health-aware request selection, visible quota status, JSON-friendly diagnostics, and safe repair commands for stale or damaged state. The plugin is designed for personal development workflows: credentials stay local, OpenCode keeps owning the host runtime, and the plugin only handles the OAuth-backed Codex routing layer it is installed for.

---

## Current Architecture At A Glance

`oc-codex-multi-auth` ships four user-visible surfaces:

| Surface | Purpose |
| --- | --- |
| `oc-codex-multi-auth` | npm CLI; explicit install modes manage OpenCode provider/TUI config, while `update` only clears the managed package cache. Also runs standalone commands: `doctor`, `status`, `list`, `limits`, `dashboard`, `health`, `diag`, `warm` |
| OpenCode plugin entry (`index.ts`) | auth loader, OAuth login modes, provider fetch pipeline, account rotation, retry/failover, and `codex-*` tool registry |
| OpenCode TUI plugin (`tui.ts`) | prompt quota status, quota details, shared quota cache, and active-account-aware display |
| 24 `codex-*` tools | setup, help, status, list, switch, warm, limits, health, metrics, doctor, dashboard, pool, backup, keychain, diagnostics, and recovery actions |

The plugin does not replace OpenCode. OpenCode remains the host; this package installs provider/TUI config and supplies the OAuth-backed Codex request pipeline that OpenCode calls.

---

<details open>
<summary><b>Terms and Usage Notice</b></summary>

> [!CAUTION]
> This project is for personal development use with your own ChatGPT Plus/Pro subscription.
>
> By using this plugin, you acknowledge:
> - This is an independent open-source project, not an official OpenAI product
> - It is not intended for commercial resale, shared multi-user access, or production services
> - You are responsible for your own usage and policy compliance
> - For production/commercial workloads, use the OpenAI Platform API

</details>

---

## Installation

<details open>
<summary><b>For Humans</b></summary>

### Option A: Standard install (preserve provider config)

Default mode registers the OpenCode and TUI plugin entries without changing `provider.openai`.

```bash
npx -y oc-codex-multi-auth@latest
```

Installer flags:

| Flag | Effect |
| --- | --- |
| (default) / `--plugin-only` | Register the plugin and TUI integration without changing `provider.openai` |
| `--modern` | Install compact modern catalog: 12 bases, 53 variants |
| `--full` | Compact bases plus 53 explicit selector IDs |
| `--legacy` | Explicit-only catalog for older OpenCode |
| `--dry-run` | Show changed config paths without values or writes |
| `--no-cache-clear` | Skip clearing the OpenCode plugin cache |

### Option B: Compact modern model catalog

```bash
npx -y oc-codex-multi-auth@latest --modern
```

Use this when OpenCode does not already provide the OAuth model definitions or you want the shipped variant presets.

### Option C: Full explicit model catalog

Use this when you want direct selector IDs such as `openai/gpt-5.5-medium` in addition to OpenCode variants.

```bash
npx -y oc-codex-multi-auth@latest --full
```

### Updating without config changes

```bash
npx -y oc-codex-multi-auth@latest update
```

`update` clears only the OpenCode-managed package cache. It does not read or write `opencode.json` or `tui.json`; restart OpenCode afterward to install the current package.

### Option D: Verify wiring

```bash
opencode --version
opencode debug config
opencode auth login
```

The default installer only normalizes the plugin entry in `~/.config/opencode/opencode.json`, enables the TUI status plugin in `~/.config/opencode/tui.json`, and clears the cached plugin copy. Catalog modes additionally merge their selected `provider.openai` definitions. Changed config files are backed up before writing.

### Standalone CLI (no agent / no token cost)

```bash
oc-codex-multi-auth status
oc-codex-multi-auth list
oc-codex-multi-auth warm
oc-codex-multi-auth doctor
oc-codex-multi-auth health
oc-codex-multi-auth limits
oc-codex-multi-auth dashboard
oc-codex-multi-auth diag
# or: npx -y oc-codex-multi-auth@latest warm --json
```

</details>

<details>
<summary><b>For LLM Agents</b></summary>

### Step-by-step

1. Register the plugin without changing `provider.openai`:
   - `npx -y oc-codex-multi-auth@latest`
   - Use `--modern` only when the shipped compact model catalog is required.
2. Run first login flow:
   - `opencode auth login`
3. Validate config:
   - `opencode debug config`
4. Run a smoke request (after OpenCode or `--modern` supplies the selector):
   - `opencode run "Explain this repository" --model=openai/gpt-5.5 --variant=medium`
5. Inspect plugin state with the OpenCode tool surface:
   - `codex-status`
   - `codex-doctor`
   - `codex-list`

### Verification

```bash
opencode debug config
opencode auth login
opencode run "ping" --model=openai/gpt-5.5 --variant=medium
```

</details>

---

## Quick Start

Install and sign in:

```bash
npx -y oc-codex-multi-auth@latest
opencode auth login
```

Run a prompt with compact modern selectors:

```bash
opencode run "Summarize the failing test and suggest a fix" --model=openai/gpt-5.5 --variant=medium
opencode run "Summarize the failing test and suggest a fix" --model=openai/gpt-5.5-fast --variant=medium
opencode run "Plan the refactor" --model=openai/gpt-5.6-sol --variant=high
```

Use Codex-focused routing:

```bash
opencode run "Refactor the retry logic and update the tests" --model=openai/gpt-5-codex --variant=high
```

If browser launch is blocked, use the alternate login paths in [docs/getting-started.md](docs/getting-started.md#remote-or-headless-login).

---

## Command Toolkit

### Start here

| Tool | What it answers |
| --- | --- |
| `codex-setup` | How do I finish first-run setup safely? |
| `codex-help` | Which plugin commands exist and what do they do? |
| `codex-doctor` | What is wrong with auth, config, storage, or routing? |
| `codex-next` | What should I do next to get unstuck? |

### Daily use

| Tool | What it answers |
| --- | --- |
| `codex-list` | Which accounts are saved and which one is active? |
| `codex-switch` | How do I move to a different saved account? |
| `codex-warm` | How do I start every account's usage window now (stagger quota cooldowns)? |
| `codex-status` | Which account, model family, and routing state are active? |
| `codex-limits` | What quota or rate-limit state is visible now? |
| `codex-reset` | Do I have a banked rate-limit reset credit, and how do I redeem it? |
| `codex-dashboard` | Can I manage accounts from one interactive surface? |
| `codex-pool` | Which accounts are preferred for each model, and how do I change them? |

Most of these also run as a **direct CLI** with no agent/model involvement (no token cost) — e.g. `oc-codex-multi-auth warm`, `oc-codex-multi-auth status`, or `npx -y oc-codex-multi-auth@latest warm`. Use `oc-codex-multi-auth warm` to open every enabled account's usage window at the start of a session and stagger the rolling quota cooldowns. Add `--json` for scriptable output.

### Account management

| Tool | What it answers |
| --- | --- |
| `codex-label` | How do I name an account? |
| `codex-tag` | How do I group accounts with tags? |
| `codex-note` | How do I attach a private note to an account? |
| `codex-remove` | How do I remove a saved account safely? |
| `codex-refresh` | How do I refresh or re-login an account? |

### Diagnostics and backup

| Tool | What it answers |
| --- | --- |
| `codex-health` | Which accounts look healthy, limited, or disabled? |
| `codex-metrics` | What runtime counters and request metrics are visible? |
| `codex-diag` | Can I export a redacted diagnostic snapshot? |
| `codex-diff` | What changed between account/config snapshots? |
| `codex-export` | How do I back up account storage? |
| `codex-import` | How do I restore accounts with a dry-run first? |
| `codex-keychain` | Which credential backend is active and can I migrate it? |

### Reliability behavior

- stateless request handling forces `store: false`
- `reasoning.encrypted_content` is preserved for multi-turn continuity
- GPT-5.6 tiers use the responses-lite request shape and default client identity `opencode`; other models default to `codex_cli_rs`
- account rotation is health-aware (`rotationStrategy` default `hybrid`) and avoids repeatedly selecting cooling accounts
- same-host OpenCode processes sharing an account file serialize refresh-token exchange and commit so one current single-use token is exchanged once
- 5xx bursts, network failures, and quota responses penalize account health
- token refresh is queued to avoid refresh races
- unsupported-model handling is strict by default, with opt-in fallback controls
- TUI quota status follows the account/workspace used by the latest request
- Business workspace memberships and Personal accounts keep separate usage and quota windows. Business members sharing one workspace are distinguished by their member/seat identity, so their usage is not collapsed into one row.

---

## Storage Paths

| File | Default path |
| --- | --- |
| OpenCode config | `~/.config/opencode/opencode.json` |
| OpenCode TUI config | `~/.config/opencode/tui.json` |
| OpenCode auth tokens | `~/.opencode/auth/openai.json` |
| Plugin config | `~/.opencode/openai-codex-auth-config.json` |
| Global account storage | `~/.opencode/oc-codex-multi-auth-accounts.json` |
| Per-project accounts | `~/.opencode/projects/<project-key>/oc-codex-multi-auth-accounts.json` |
| Flagged accounts | `~/.opencode/oc-codex-multi-auth-flagged-accounts.json` |
| Backups | `~/.opencode/backups/` or `~/.opencode/projects/<project-key>/backups/` |
| Logs | `~/.opencode/logs/codex-plugin/` |
| TUI quota cache | OpenCode state path plus `~/.opencode/oc-codex-multi-auth-tui-quota.json` fallback |

Per-project storage is enabled by default. The plugin walks up from the current directory to find a project root, then stores account pools under the project-specific key. If no project root is found, it falls back to global storage.

---

## Configuration

Primary config files:

- `~/.config/opencode/opencode.json`
- `~/.config/opencode/tui.json`
- `~/.opencode/openai-codex-auth-config.json`

### Desktop quota notifications

Quota notifications are an optional macOS-only feature. While the plugin is
running, it checks all enabled accounts and alerts through Notification Center
when the best remaining 5-hour or weekly pool quota crosses 25%, 10%, or 0%.
The feature is disabled by default.

Each line reports the enabled account with the most headroom in that window,
together with that same account's reset time, so the pair always describes a
quota that one account actually has. Windows a plan has switched off are
skipped rather than counted as full. Account identities are omitted for
readability and lock-screen privacy:

```text
5h: 10% | resets 22:30
Weekly: 72% | resets 22:30 on Aug 30
```

```json
{
  "quotaNotifications": {
    "enabled": true,
    "intervalMs": 1800000,
    "notifyEveryCheck": false,
    "thresholds": [25, 10, 0]
  }
}
```

Add the object above to `~/.opencode/openai-codex-auth-config.json`, or set
`CODEX_AUTH_QUOTA_NOTIFICATIONS=1`, then quit and restart OpenCode. The minimum
interval is 30 seconds. If macOS blocks the alert, allow notifications for
the process shown in **System Settings > Notifications**. The setting is
ignored on Windows and Linux.

Set `"notifyEveryCheck": true` to show the aggregate quota notification after
every successful poll interval instead of only when a configured threshold is
crossed. Set `"thresholds": []` to turn threshold alerts off entirely; pair it
with `"notifyEveryCheck": true` or the monitor has nothing to deliver and stops
polling.

Delivery state lives beside the accounts file the alerts are computed from, so
OpenCode processes working in the same account scope show only one alert per
interval. With the default `perProjectAccounts`, that scope is one project:
two projects have separate account pools and therefore alert independently.

### Route models to preferred accounts

Use `modelAccountPools` to assign one or more preferred ChatGPT accounts or Business seats to a
model. Account references use stable account or Business-seat identities, so
adding, removing, or reordering accounts does not silently change a model's
routing. A Business membership and a Personal account remain separate pool and
usage identities even when they belong to the same login.

```json
{
  "modelAccountPools": {
    "gpt-5.6-sol": [
      "org-example-account-id",
      "00000000-0000-0000-0000-000000000000"
    ],
    "gpt-5.6-terra": [
      "org-another-account-id"
    ]
  },
  "modelAccountPoolModes": {
    "gpt-5.6-sol": "strict",
    "gpt-5.6-terra": "preferred"
  }
}
```

Save this configuration in `~/.opencode/openai-codex-auth-config.json`, then
restart OpenCode. Model matching is case-insensitive and uses the effective
model after request model normalization.

Use `codex-pool` to manage these mappings with ordinary 1-based account
numbers. The tool resolves those numbers and writes stable IDs to disk:

```text
codex-pool
codex-pool action="set" model="gpt-5.6-sol" accounts=[7,8]
codex-pool action="add" model="gpt-5.6-sol" accounts=[9]
codex-pool action="remove" model="gpt-5.6-sol" accounts=[7]
codex-pool action="set-mode" model="gpt-5.6-sol" poolMode="strict"
codex-pool action="clear" model="gpt-5.6-sol"
```

Add `dryRun=true` to preview a mutation. Use `format="json"` for structured
output; stable IDs remain redacted unless `includeSensitive=true` is also set.
Restart OpenCode after an applied mutation. The plugin configuration is global
while account storage is per-project by default, so a reference unresolved in
the current project is reported but never automatically deleted.

Routing behavior:

- A mapped model defaults to `preferred` mode and uses healthy, selectable accounts in its pool.
- Existing rotation strategy, quota, cooldown, and token-health rules still apply within the preferred pool.
- In `preferred` mode, an unavailable pool falls back to the healthy general account pool.
- In `strict` mode, routing never leaves the configured pool and immediately returns `strict_pool_unavailable` when no pooled account is selectable.
- An unmapped model or an empty account list uses the general account pool directly.
- `codex-status`, `codex-dashboard`, and routing diagnostics also report `strict` and `strict-unavailable` modes.

Account IDs are local account metadata but should still be treated as private
configuration. Do not publish a populated configuration file.

Selected runtime/environment overrides:

| Variable | Effect |
| --- | --- |
| `OPENAI_BASE_URL=https://gateway.example/v1` | OpenAI-compatible OAuth inference gateway; requires `CODEX_AUTH_ALLOW_OPENAI_BASE_URL=1` |
| `CODEX_AUTH_ALLOW_OPENAI_BASE_URL=1` | Explicitly allow the trusted gateway to receive the ChatGPT OAuth access token; remote gateways require HTTPS, while HTTP is accepted only on literal loopback IPs |
| `CODEX_AUTH_REQUEST_TRANSFORM_MODE=legacy` | Re-enable legacy Codex request rewriting |
| `CODEX_MODE=0/1` | Disable/enable bridge prompt behavior |
| `CODEX_TUI_V2=0/1` | Disable/enable codex-style tool output |
| `CODEX_TUI_COLOR_PROFILE=truecolor\|ansi256\|ansi16` | Force terminal color profile |
| `CODEX_TUI_GLYPHS=ascii\|unicode\|auto` | Force terminal glyph style |
| `CODEX_TUI_MASK_EMAIL=0/1` | Mask account emails across account-display surfaces (list/status/limits/health/dashboard/menus + TUI quota status) |
| `CODEX_TUI_MASK_EMAIL_DETAILS=0/1` | Also hide account email in quota details when prompt masking is enabled |
| `CODEX_AUTH_PER_PROJECT_ACCOUNTS=0/1` | Disable/enable per-project account pools |
| `CODEX_AUTH_AUTO_UPDATE=0/1` | Disable/enable daily npm update check and cache refresh |
| `CODEX_AUTH_ROTATION_STRATEGY=hybrid\|sticky\|round-robin` | Account selection strategy |
| `CODEX_AUTH_UNSUPPORTED_MODEL_POLICY=strict\|fallback` | Control unsupported-model retry behavior |
| `CODEX_AUTH_ACCOUNT_ID=<id>` | Force a specific workspace/account id |
| `CODEX_AUTH_FETCH_TIMEOUT_MS=<ms>` | Request timeout override |
| `CODEX_AUTH_STREAM_STALL_TIMEOUT_MS=<ms>` | SSE stream stall timeout override |
| `ENABLE_PLUGIN_REQUEST_LOGGING=1` | Enable request metadata logs |
| `CODEX_PLUGIN_LOG_BODIES=1` | Include raw request/response bodies in logs; sensitive |
| `CODEX_KEYCHAIN=1` | Opt in to OS-native keychain account storage |

Boolean env overrides are truthy only for the literal string `"1"`.

Validate config after changes:

```bash
opencode debug config
opencode run "test" --model=openai/gpt-5.5 --variant=medium
```

Modern OpenCode versions use [config/opencode-modern.json](config/opencode-modern.json). Older versions can use [config/opencode-legacy.json](config/opencode-legacy.json). See [config/README.md](config/README.md) for the full model template matrix.

---

## Credential Storage

<details open>
<summary><b>Default JSON backend</b></summary>

By default, account pools are stored locally as V3 JSON files. File permissions are restricted where the platform supports them.

Use JSON storage when you want predictable, inspectable local files and easy backup/export behavior.

</details>

<details>
<summary><b>Optional OS keychain backend</b></summary>

Set `CODEX_KEYCHAIN=1` to store account pools in the OS keychain instead:

- macOS: Keychain
- Windows: Credential Manager
- Linux: libsecret, with a running secret service such as GNOME Keyring or KWallet

Manage the backend from OpenCode:

```text
codex-keychain status
codex-keychain migrate
codex-keychain rollback
```

If the keychain is unavailable, the plugin logs a warning and falls back to JSON storage for that operation. Credentials are never silently deleted.

</details>

---

## Troubleshooting

<details open>
<summary><b>60-second recovery</b></summary>

```text
codex-doctor fix=true
codex-next
codex-status format="json"
```

If still broken:

```bash
opencode auth login
```

</details>

<details>
<summary><b>Common symptoms</b></summary>

- Plugin does not load: rerun `npx -y oc-codex-multi-auth@latest`, then restart OpenCode
- Config looks wrong: run `opencode debug config` and confirm `"plugin": ["oc-codex-multi-auth"]`
- OAuth callback fails: free port `1455`, then rerun `opencode auth login`
- Browser launch is blocked: use the remote/headless login path from [docs/getting-started.md](docs/getting-started.md#remote-or-headless-login)
- Wrong account is selected: run `codex-list`, then `codex-switch`
- Account pool looks unhealthy: run `codex-health format="json"` and `codex-doctor deep=true format="json"`
- Import/export feels risky: run `codex-import path="..." dryRun=true` before applying
- Debugging model fallback: enable `ENABLE_PLUGIN_REQUEST_LOGGING=1` and inspect `~/.opencode/logs/codex-plugin/`

</details>

<details>
<summary><b>Diagnostics pack</b></summary>

```text
codex-status format="json"
codex-limits format="json"
codex-health format="json"
codex-next format="json"
codex-list format="json"
codex-dashboard format="json"
codex-metrics format="json"
codex-doctor deep=true format="json"
```

</details>

---

## Documentation

- Docs portal: [docs/README.md](docs/README.md)
- Documentation map: [docs/DOCUMENTATION.md](docs/DOCUMENTATION.md)
- Getting started: [docs/getting-started.md](docs/getting-started.md)
- Configuration: [docs/configuration.md](docs/configuration.md)
- Config templates: [config/README.md](config/README.md)
- Troubleshooting: [docs/troubleshooting.md](docs/troubleshooting.md)
- FAQ: [docs/faq.md](docs/faq.md)
- Privacy: [docs/privacy.md](docs/privacy.md)
- Public architecture: [docs/architecture.md](docs/architecture.md)
- Maintainer architecture: [docs/development/ARCHITECTURE.md](docs/development/ARCHITECTURE.md)
- Testing: [docs/development/TESTING.md](docs/development/TESTING.md)
- Discoverability guide: [docs/development/GITHUB_DISCOVERABILITY.md](docs/development/GITHUB_DISCOVERABILITY.md)

---

## Release Notes

- Current published version: see the npm badge above, or run `npm view oc-codex-multi-auth version`
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Releases are automated with [release-please](https://github.com/googleapis/release-please)

Merging the release-please PR cuts the tagged release and publishes the package through the configured release workflow. Manual `npm publish` is not required for routine releases.

## License

MIT License. See [LICENSE](LICENSE).

<details>
<summary><b>Legal</b></summary>

- Not affiliated with OpenAI.
- "ChatGPT", "GPT-5", "Codex", and "OpenAI" are trademarks of OpenAI.
- You assume responsibility for your own usage and compliance.

</details>
