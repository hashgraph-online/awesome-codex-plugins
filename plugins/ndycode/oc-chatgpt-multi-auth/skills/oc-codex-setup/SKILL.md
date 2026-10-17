---
name: oc-codex-setup
description: Install or refresh oc-codex-multi-auth in OpenCode, choose the right config mode, and verify Codex OAuth with ChatGPT Plus or Pro access.
---

# oc-codex-setup

Use this skill when the user wants to install, reinstall, upgrade, or troubleshoot `oc-codex-multi-auth` in OpenCode. Requires Node >= 22.19.

## Happy path

```bash
npx -y oc-codex-multi-auth@latest   # 1. install (default: plugin entries only, provider.openai preserved)
opencode auth login               # 2. pick a "Codex OAuth" method and sign in
oc-codex-multi-auth doctor        # 3. verify
```

The default install registers the OpenCode plugin and the TUI quota-status plugin without touching `provider.openai`. A config that already registers this plugin — including a path to the user's own checkout — is kept as written; the published package name is added only when nothing resolves to this plugin.

## Config modes (choose at most one)

| Flag | When to use |
| --- | --- |
| _(none)_ / `--plugin-only` | User already manages `provider.openai` (default) |
| `--modern` | Compact catalog: 11 base OAuth model families + variant presets |
| `--full` | Compact bases plus 59 explicit selector IDs (e.g. `openai/gpt-5.5-medium`, `openai/gpt-6-astra-high`) |
| `--legacy` | 59 explicit model IDs only, for OpenCode versions without variant support |
| `--v2` | Register for OpenCode V2 (`plugins` entry; plugin-only, includes quota UI) |

`--v2` cannot combine with a catalog mode; it refuses an existing `opencode.jsonc` or V1 `plugin` entries. Other installer flags: `--dry-run`, `--no-cache-clear`, `--version`, `--help`.

## Refresh without touching config

```bash
npx -y oc-codex-multi-auth@latest update   # clears the managed package cache only; restart OpenCode after
```

`update` never reads or writes `opencode.json` or `tui.json`. Prefer it over re-running the installer when the goal is just a fresh package cache.

## Verify

```bash
# modern/--full selectors use base + variant:
opencode run "Explain this repository" --model=openai/gpt-5.5 --variant=medium
opencode run "Explain this repository" --model=openai/gpt-6-astra --variant=medium
opencode run "Explain this repository" --model=openai/gpt-5.6-sol --variant=medium
# explicit IDs only exist after --full or --legacy:
opencode run "Explain this repository" --model=openai/gpt-5.5-medium
```

## Standalone CLI (no agent cost)

```bash
oc-codex-multi-auth status
oc-codex-multi-auth list
oc-codex-multi-auth limits
oc-codex-multi-auth doctor
oc-codex-multi-auth health
oc-codex-multi-auth warm
oc-codex-multi-auth dashboard
oc-codex-multi-auth diag
oc-codex-multi-auth limits --refresh   # live reads
oc-codex-multi-auth doctor --fix       # verified refresh + stale-marker cleanup
```

## Config knobs that matter

All live in `~/.opencode/openai-codex-auth-config.json`; every boolean env override is truthy for `"1"` only.

| Knob | Default | Purpose |
| --- | --- | --- |
| `perProjectAccounts` | `true` | Per-project pools under `~/.opencode/projects/<key>/` |
| `rotationStrategy` | `hybrid` | `sticky` / `round-robin` alternatives |
| `maskEmail` | `false` | Render emails as `us***@example.com` |
| `quotaNotifications.autoProtectCredits` | `true` | 30-min `/wham/usage` poll that blocks spent accounts pre-429 |
| `autoUpdate` | `true` | Daily npm version check + cache eviction |
| `CODEX_KEYCHAIN=1` | off | Opt-in OS-keychain credential backend |

## Troubleshooting

- Config must register the plugin: `"plugin": ["oc-codex-multi-auth"]` (V1) or a `plugins` entry (V2).
- `opencode auth login` again if tokens expired or the wrong workspace was picked.
- Failed requests: `ENABLE_PLUGIN_REQUEST_LOGGING=1`, then inspect `~/.opencode/logs/codex-plugin/` (set `CODEX_PLUGIN_LOG_BODIES=1` only for raw bodies).
- Deeper docs: `docs/getting-started.md`, `docs/configuration.md`, `docs/troubleshooting.md`, `docs/faq.md`.

## Usage boundaries

Personal development use with your own ChatGPT Plus or Pro subscription. For production or shared services, prefer the OpenAI Platform API.
