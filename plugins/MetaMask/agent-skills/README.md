# MetaMask Agent CLI Skills

SKILLs for the MetaMask Agent CLI (`@metamask/agent-wallet` v7.3.0). These skills enable AI agents to authenticate, manage wallets, swap tokens, bridge across chains, trade perpetual futures, earn yield on DeFi vaults, and more using the MetaMask Agent Wallet CLI (`mm`).

This repository is also packaged as a **plugin** for Claude Code, Cursor, Codex, Antigravity CLI (`agy`), and Grok Build. The plugin ships the same skills plus a session-start hook that checks CLI readiness via `mm doctor` and records local install attribution.

## Skills

| Skill | Description |
| --- | --- |
| [`metamask-agent-wallet`](./skills/metamask-agent-wallet/SKILL.md) | Full CLI skill that routes the agent to topic-specific reference docs (`references/`) for all MetaMask Agent CLI commands — auth, wallets, transfers, signing, swaps, bridges, perps, prediction markets, DeFi earn/yield vaults, market data, x402 payments, and calldata decoding — plus multistep workflow templates (`workflows/`) for onboarding, swaps, bridges, perps, prediction markets, and earn. |

## Install as a plugin (recommended)

### Claude Code

```bash
claude plugin marketplace add MetaMask/agent-skills
claude plugin install metamask-agent-wallet@metamask
```

Or use `/plugin` → Discover / Install inside Claude Code.

Local development:

```bash
claude --plugin-dir /path/to/agent-skills
```

### Cursor

1. Open **Customize → Plugins**.
2. Add from Git: `https://github.com/MetaMask/agent-skills`.
3. Enable **metamask-agent-wallet**.

Or submit/browse via the [Cursor Marketplace](https://cursor.com/marketplace) once listed.

### Codex

```bash
codex plugin marketplace add MetaMask/agent-skills
codex plugin add metamask-agent-wallet@metamask
```

Or use `/plugins` inside Codex.

Local development:

```bash
codex plugin marketplace add /path/to/agent-skills
codex plugin add metamask-agent-wallet@metamask
```

Codex skips plugin-bundled hooks until you review and trust them. After that, a new session injects MetaMask readiness context the same way as Claude Code and Cursor.

### Antigravity CLI (`agy`)

Install the repo root so skills and session-start hooks resolve:

```bash
agy plugin install /path/to/agent-skills
agy plugin install https://github.com/MetaMask/agent-skills
```

The slim `.antigravity-plugin/` directory (rules only) is for validation; prefer the repo root so `skills/` and `hooks/session-start.sh` are on the plugin path.

Restart `agy` after install, then `agy plugin list`. The extension rule routes wallet work to `skills/metamask-agent-wallet/SKILL.md`.

### Grok Build

Install the repo directly (recommended):

```bash
grok plugin install MetaMask/agent-skills --trust
```

Local development:

```bash
grok plugin install /path/to/agent-skills --trust
```

Optional marketplace (for browsing; install by repo path if name lookup fails):

```bash
grok plugin marketplace add MetaMask/agent-skills
grok plugin marketplace add /path/to/agent-skills
```

Grok skips plugin-bundled hooks, MCP servers, and skills until you trust the plugin (`--trust`). After that, a new session injects MetaMask readiness context the same way as Claude Code and Cursor.

To pick up a newly installed plugin, press `r` in the Plugins tab or start a new session.

### Skills CLI (legacy / non-plugin hosts)

```bash
npx skills add MetaMask/agent-skills
```

Select any one of the SKILLs upon prompt.

## What the session-start hook does

On every new (or resumed) agent session the hook:

1. Reads the pinned CLI version from `skills/metamask-agent-wallet/SKILL.md`.
2. Writes or updates `~/.metamask/attribution.json` with `{ installSource, pluginVersion, firstSeenAt, lastSeenAt }` so analytics can attribute acquisition to this plugin. **No email or personal identity is stored.**
3. If `mm` is on `PATH`, runs `mm doctor --json` (≈15s timeout) and injects a short readiness summary into the session context (install / upgrade / login / init hints).
4. If `mm` is missing, injects guidance to **ask the user** before running `npm install -g @metamask/agent-wallet@<pinned>`.

The hook **never** installs or upgrades the CLI itself. It always exits `0` and never blocks the session.

## CLI install and updates

The plugin does not bundle `mm`. After the agent asks and the user consents:

```bash
npm install -g @metamask/agent-wallet@latest
# or pin to the skill's cliVersion, e.g.:
npm install -g @metamask/agent-wallet@7.3.0
```

Requires a supported Node.js version. Then complete onboarding with `mm login` and `mm init` (see the skill workflows).

When the skill's `cliVersion` advances, the next session-start context (or `mm doctor`) will prompt an upgrade the same way.

## Privacy

| Data | Where | Purpose |
| --- | --- | --- |
| `installSource`, `pluginVersion`, timestamps | `~/.metamask/attribution.json` (mode `0600`) | First-touch acquisition channel for MetaMask product analytics after the user runs `mm` |
| Host env (`CLAUDECODE`, `CURSOR_AGENT`, `CODEX_THREAD_ID`, `ANTIGRAVITY_AGENT`, `GROK_PLUGIN_ROOT`, …) | Read by `mm` at command time | Tag Segment events with the calling agent host |
| Cursor `user_email` / other PII from hooks | **Not written** | — |

Product analytics from the CLI respect `MM_TELEMETRY_DISABLED=1`, `DO_NOT_TRACK=1`, and dashboard Osano consent.

## Release coupling

When `@metamask/agent-wallet` ships a new `major.minor`:

1. Bump `metadata.cliVersion` (and `metadata.version`) in `skills/metamask-agent-wallet/SKILL.md`.
2. Bump `version` in `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.cursor-plugin/plugin.json`, `.codex-plugin/plugin.json`, `.grok-plugin/plugin.json`, `.grok-plugin/marketplace.json`, and root `plugin.json`.
3. Ship one PR; Claude Code, Cursor, Codex, Antigravity CLI, and Grok Build auto-pull plugin updates from Git.

Do **not** rename the plugin `name` (`metamask-agent-wallet`) after marketplace listing — it is an immutable slug.

## Repository layout

```text
.
├── plugin.json                 # Agent Plugins 1.0 (skills only)
├── hooks.json                  # Cursor sessionStart
├── .claude-plugin/
│   ├── plugin.json
│   └── marketplace.json
├── .cursor-plugin/
│   └── plugin.json
├── .codex-plugin/
│   └── plugin.json
├── .antigravity-plugin/        # Antigravity CLI (`agy`)
│   ├── plugin.json
│   ├── hooks.json
│   └── rules/
├── .grok-plugin/               # Grok Build
│   ├── plugin.json
│   └── marketplace.json
├── .agents/plugins/
│   └── marketplace.json        # Codex / ChatGPT repo marketplace
├── hooks/
│   ├── hooks.json              # Claude SessionStart
│   ├── codex-hooks.json        # Codex SessionStart
│   ├── antigravity-hooks.json  # Antigravity repo-root SessionStart
│   ├── grok-hooks.json         # Grok Build SessionStart
│   └── session-start.sh
└── skills/
    ├── metamask-agent-wallet/
    └── metamask-agent-workflows/
```

## License

[MIT](./LICENSE)

## Marketplace listing

See [docs/MARKETPLACE_SUBMISSION.md](./docs/MARKETPLACE_SUBMISSION.md) for Claude Code, Cursor, Codex, Antigravity CLI, and Grok Build submission steps (human review required after this repo is pushed).
