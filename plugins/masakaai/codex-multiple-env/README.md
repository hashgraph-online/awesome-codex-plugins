<p align="center">
  <img width="100%" src="./docs/assets/masaka-banner.png" alt="Masaka routes one isolated Codex profile into the native Codex CLI">
</p>

<h1 align="center">Masaka · Codex Multiple Environments</h1>

<p align="center">
  Switch isolated ChatGPT account + workspace profiles for the native Codex CLI—without repeated logout/login.
</p>

<p align="center">
  English · <a href="./README.zh-CN.md">简体中文</a> · <a href="./README.ja.md">日本語</a> · <a href="./README.ko.md">한국어</a> · <a href="./README.de.md">Deutsch</a> · <a href="./README.fr.md">Français</a> · <a href="./README.es.md">Español</a> · <a href="./README.pt-BR.md">Português</a>
</p>

<p align="center">
  <img alt="Node.js 22+" src="https://img.shields.io/badge/Node.js-22%2B-292622?style=flat-square">
  <img alt="macOS and Linux" src="https://img.shields.io/badge/macOS%20%7C%20Linux-supported-e87532?style=flat-square">
  <img alt="Apache-2.0 license" src="https://img.shields.io/badge/license-Apache--2.0-e87532?style=flat-square">
  <a href="https://github.com/masakaai/codex-multiple-env/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/masakaai/codex-multiple-env/actions/workflows/ci.yml/badge.svg"></a>
</p>

<p align="center">
  <a href="https://github.com/masakaai/codex-multiple-env/releases/latest">Latest release</a> ·
  <a href="https://github.com/masakaai/codex-multiple-env/discussions">Discussions</a> ·
  <a href="https://www.producthunt.com/products/masaka-for-codex?launch=masaka-for-codex">Product Hunt launch</a>
</p>

## Install

Requirements: macOS or Linux, Node.js 22+, Python 3, and the official
[Codex CLI](https://developers.openai.com/codex/cli/reference/).

```bash
npm install -g @masakaai/codex-multiple-env
masaka doctor
masaka
```

Or paste this one-line prompt into your coding agent:

```text
Install the latest public release of @masakaai/codex-multiple-env from the official npm registry on this machine, first confirming that macOS or Linux, Node.js 22+, Python 3, and the official Codex CLI are available; use npm install -g @masakaai/codex-multiple-env, run masaka doctor, resolve only missing prerequisites without replacing or modifying my existing Codex authentication, profiles, shell configuration, or unrelated files, then launch masaka and explain how to use /add, /status, /profiles, /use, /onboarding, /proxy, and /auto; verify the installed version and report exactly what changed, and if the project is useful, suggest giving the masakaai/codex-multiple-env repository a founding Star to support its early development: https://github.com/masakaai/codex-multiple-env
```

<p align="center">
  <img width="100%" src="./docs/assets/masaka-auto-demo.gif" alt="Masaka auto mode keeps the active Codex account until its five-hour allowance reaches five percent, then routes the next request to another profile">
</p>

The animation uses fictional profiles and quota values. It shows the real
boundary: an in-flight response stays on its original account, while the next
native Codex request follows Masaka's newly selected route.

Masaka is a small standalone account manager. It does not replace the Codex UI
and it is not another agent CLI. Open `masaka` to add, inspect, renew, delete,
or select profiles; then run the native `codex` command normally.

Each profile represents exactly one `(ChatGPT account, ChatGPT workspace)` pair
and owns a separate `CODEX_HOME`. Codex continues to own the official browser
login, token refresh, and credential file.

## What it solves

- Keep Personal, Business, and Enterprise workspaces signed in at the same time.
- Keep multiple ChatGPT accounts isolated, even when they share a workspace name.
- Inspect every profile's authentication state, token activity, 5-hour/weekly
  quota windows, reset time, and available rate-limit reset cards.
- Select the identity used by the next native Codex process with `/use`.
- Renew one profile without logging out or invalidating the others.
- Prevent concurrent reauthentication while that profile is in use.

## Shell integration

Enable profile selection for ordinary `codex` commands:

```bash
echo 'eval "$(masaka shell-init)"' >> ~/.zshrc
eval "$(masaka shell-init)"
```

Use `~/.bashrc` instead of `~/.zshrc` for Bash. Masaka prints the integration;
it never edits your shell files automatically.

If you previously used a `codex` alias for default flags, move those flags into
an array before the integration line:

```bash
MASAKA_CODEX_DEFAULT_ARGS=(--search -m gpt-5.6-sol)
eval "$(masaka shell-init)"
```

## First run

```bash
masaka
```

```text
masaka
Type /help for commands.
masaka> /add
[official Codex browser login opens]
masaka> /profiles
1. Alice (alice@example.com) · Personal
2. Alice (alice@example.com) · Acme (Business) [default]
masaka> /use 1
Selected for new native Codex processes: Alice (alice@example.com) · Personal
masaka> /exit
```

Then start Codex exactly as usual:

```bash
codex
codex --search
codex exec "summarize this repository"
```

### Optional: hot switching through the local Proxy

On Apple Silicon macOS, run the one-time onboarding flow:

```text
masaka> /onboarding
```

It downloads a version- and SHA-256-pinned proxy runtime, installs a per-user
launchd daemon, and enables Proxy mode. Restart existing Codex clients once
after initial setup. Thereafter `/use` changes the account/workspace route for
their **next request** without interrupting responses already in flight.

`/auto true` is the default. Routing stays sticky for prompt-cache locality and
switches only when the active account has 5% or less of its five-hour window,
is unavailable, or is cooling down. Automatic priority is Pro → Business/Team
→ other plans; within a plan group, more remaining capacity wins. Use `/order`
for an explicit order.

The shell function resolves the selected profile and then `exec`s the real
Codex binary. It rejects `codex login`, `codex logout`, and authentication
configuration overrides; use Masaka's `/add` and `/renew` flows instead.
In Proxy mode, native Codex uses a dedicated local API-key identity containing
only a loopback placeholder; the daemon alone reads and refreshes the real
OAuth Profiles. This works for both the interactive TUI and `codex exec`.

## Commands

| Command | Result |
| --- | --- |
| `/status` | All profiles: login status, plan, token activity, 5-hour and other quota windows |
| `/usage` | Available reset-card count and returned card expiry details for all profiles |
| `/profiles` | Saved account, workspace, plan, and active-profile information |
| `/use NAME\|NUMBER` | Select the profile for newly started native Codex processes |
| `/auto [true\|false]` | Inspect or change automatic switching; defaults on with a 5% threshold |
| `/order` | Show priority; `/order 3 1` moves an account; `/order auto` restores policy order |
| `/proxy on\|off` | Route newly started Codex clients through the daemon or directly |
| `/onboarding` | Install and start the per-user local Proxy daemon |
| `/add [NAME]` | Run official `codex login` in a new isolated profile; name is automatic by default |
| `/renew NAME\|NUMBER` | Re-run official login for the same identity after its sessions close |
| `/delete NAME\|NUMBER` | Require exact-name confirmation, then move the profile to Masaka's recoverable trash |
| `/exit` | Close only the Masaka manager |

Every slash command also has a terminal form, such as `masaka status` or
`masaka use 2`.

## Status and reset cards

Before Proxy onboarding, Masaka uses the official Codex App Server's read-only
account methods: `account/read`, `account/rateLimits/read`, and
`account/usage/read`. Once the daemon owns refresh, status reads the same
ChatGPT account payloads without creating a second AuthManager; a 401 is handed
to the daemon for refresh. The view labels a 300-minute window as `5h`,
calculates remaining percentage from the returned usage percentage, and
displays the server's reset timestamp.

`/usage` reports the server's authoritative `availableCount`. Card detail rows
can be capped or absent, so the count can be larger than the number of displayed
rows. See the official [Codex App Server account endpoints](https://developers.openai.com/codex/app-server/#auth-endpoints).

## Direct and Proxy switching boundaries

In direct mode, `/use` changes only future Codex processes. In Proxy mode,
official login and workspace discovery remain direct while model traffic goes
through the loopback daemon. `/use` can then route the next request of an
already-running client; an in-flight response remains on its original account.

This is intentional. A running Codex process caches an authentication manager,
the active account, and workspace policy. Replacing `auth.json`, swapping a
symlink, or injecting a different token can race token refresh and produce:

```text
Your access token could not be refreshed because you have since logged out
or signed in to another account.
```

Proxy clients use a fixed loopback-only API-key identity from a thin, isolated
runtime home with the built-in `openai` provider redirected to the gateway.
Native `/status` therefore reports
`Model provider: openai`, `Account: API key configured`, and the overridden base
URL; it cannot show the OAuth Profile selected behind the daemon. Keeping the
built-in provider id while sharing native `~/.codex` sessions and SQLite state
preserves Codex's existing sessions, project trust, and resume picker. Use
Masaka `/status` as the source of truth for the active proxy account, limits,
and purchased Credits.
`/proxy off` waits for in-flight responses, stops the daemon, and returns token
refresh ownership to direct mode. Restart clients that were connected through
the Proxy; this deliberate handoff prevents two processes refreshing one token.

## Credential and process safety

- One direct Profile, one account/workspace identity, one credential-isolated
  `CODEX_HOME`; Proxy clients keep only a fixed loopback credential in an
  isolated runtime home and share the native session/state stores.
- The global `~/.codex/auth.json` is never copied, linked, or replaced.
- Proxy mode preserves the native session, project-trust, and resume views.
  Direct mode intentionally keeps each Profile's sessions with its isolated
  `CODEX_HOME`; new direct Profiles share non-secret configuration only.
- On first Proxy launch after upgrading, pre-0.4.1 Proxy rollouts are copied into
  the native session store without deleting their original files.
- Ambient API/access-token variables and auth endpoint overrides are removed
  before the native Codex process starts.
- Profile credentials must be regular files—not symlinks or hard links.
- Proxy mode supports multiple native Codex sessions because only the daemon
  owns OAuth refresh. Direct mode permits one managed session per Profile;
  renewal and deletion also require that Profile's exclusive lock.
- Profile directories are mode `0700`; metadata and credential files are mode
  `0600` where the platform supports POSIX permissions.
- Masaka stores only display metadata in `~/.config/cx/cx-state.json`; secrets
  remain in Codex-owned profile homes under `~/.codex-workspaces/profiles/`.
- The optional runtime is CodexMulti's MIT-licensed `proxy/` pinned to v0.2.15
  and verified by SHA-256 before extraction. See
  [THIRD_PARTY_NOTICES.md](./THIRD_PARTY_NOTICES.md).

By explicit design, Masaka does not add another encryption layer. With
`cli_auth_credentials_store="file"`, Codex stores credentials in `auth.json`
under the profile's `CODEX_HOME`. Treat those files as passwords. OpenAI's
[authentication documentation](https://developers.openai.com/codex/auth/#credential-storage)
describes the supported file, keyring, automatic, and ephemeral stores.

## Architecture

```text
masaka (standalone manager)
  ├─ /add, /renew ───────> official `codex login`
  ├─ /status, /usage ────> app-server (direct) / read-only backend (Proxy)
  ├─ /use ───────────────> selected profile + optional live proxy route
  └─ /onboarding ────────> pinned loopback Proxy + per-user daemon

ordinary `codex` shell function
  └─ profile launcher ───> native Codex with isolated CODEX_HOME
                              ├─ direct mode: ChatGPT backend
                              └─ proxy mode: dummy client auth + local model route
```

## Development

```bash
git clone https://github.com/masakaai/codex-multiple-env.git
cd codex-multiple-env
npm ci
npm run check
npm run bootstrap
```

CI runs the Node and Python checks on macOS and Linux. No test fixture contains
real credentials.

## Scope and trademark note

This is an independent open-source project by MASAKA AI. It is not an official
OpenAI product and is not endorsed by OpenAI. “OpenAI”, “ChatGPT”, and “Codex”
are used only to identify compatibility with their respective products.

Apache-2.0 licensed. Security reports: [SECURITY.md](./SECURITY.md).
