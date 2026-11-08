# bowmark plugin

[![Add to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](cursor://anysphere.cursor-deeplink/mcp/install?name=bowmark&config=eyJ1cmwiOiJodHRwczovL2FwaS5ib3dtYXJrLmFpL21jcC9iYWRnZS1jdXJzb3IifQ==)
[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Bowmark-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=bowmark&config=%7B%22name%22%3A%22bowmark%22%2C%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fapi.bowmark.ai%2Fmcp%2Fbadge-vscode%22%7D)

[![MCP](https://img.shields.io/badge/MCP-server-000000?style=flat-square)](https://api.bowmark.ai/mcp)
[![npm](https://img.shields.io/npm/v/%40bowmark%2Fmcp?style=flat-square&label=%40bowmark%2Fmcp)](https://www.npmjs.com/package/@bowmark/mcp)
[![PyPI](https://img.shields.io/pypi/v/bowmark-mcp?style=flat-square)](https://pypi.org/project/bowmark-mcp/)
[![License](https://img.shields.io/badge/license-MIT-A3E635?style=flat-square)](https://opensource.org/licenses/MIT)

<sub>**LM Studio** — GitHub strips a raw `lmstudio:` link, so this one is a paste, not a button. Copy it into your browser's address bar:</sub>

```
lmstudio://add_mcp?name=bowmark&config=eyJ1cmwiOiJodHRwczovL2FwaS5ib3dtYXJrLmFpL21jcC9iYWRnZS1sbXN0dWRpbyJ9
```

The [Bowmark](https://bowmark.ai) plugin for **Claude Code**, **Codex**, **Antigravity**, and every client that reads **[Agent Plugins](https://agent-plugins.org/) 1.0.0** — installs the `bowmark` skill *and* auto-wires the hosted MCP server (`https://api.bowmark.ai/mcp`) in one step, so there's no separate `claude mcp add` / `config.toml` edit.

Jigs: small pages built on Bowmark and published for anyone to use. Each one runs with your own logins on the sites it lists, and your agent can search, open and publish them. Browse the store at https://bowmark.ai/jigs.

Your agent gets one tool for many live websites: it looks up the functions it needs (search, prices, availability, reading a page, and more), writes a short script, and Bowmark runs it and returns typed results. Reading the function library needs no key. Running a script needs a Bowmark account, which starts with a free $10: [create one at bowmark.ai](https://bowmark.ai/sign-up).

## Install — Claude Code

```sh
claude plugin marketplace add bowmark-ai/plugin
claude plugin install bowmark@bowmark-ai
```

## Install — Codex

```sh
codex plugin marketplace add bowmark-ai/plugin
codex /plugins            # open the plugin browser, then install Bowmark
```

## Install — Antigravity

```sh
agy plugin install https://github.com/bowmark-ai/plugin
```

## Install — an Agent Plugins client (ChatGPT, Cursor, Copilot, VS Code, Kiro, …)

There is no one command, because the spec defines no install path. Every host resolves a plugin from a **git repo or a local directory** and then reads the root `plugin.json`. Two shapes cover all of them:

```sh
# repo-level: anyone working in this checkout gets it
git clone https://github.com/bowmark-ai/plugin plugins/bowmark

# personal: the host's own plugin directory, e.g. Codex
git clone https://github.com/bowmark-ai/plugin ~/.codex/plugins/bowmark
```

Hosts with a marketplace UI (Cursor's Settings → Plugins → Team Marketplaces → Import from Repo, Codex's `/plugins` browser) point at `bowmark-ai/plugin` and read the manifests in-tree. **Cursor does not read the root `plugin.json`** — it reads `.cursor-plugin/plugin.json` first and never gets past `.claude-plugin/plugin.json` if that one is present; see the section below.

Any of the three routes gets you the skill + the MCP (tools `mcp__bowmark__get_library`, `mcp__bowmark__run`) and a card in the host's plugin directory.

Other surfaces are unchanged and live elsewhere: skill-only via `npx skills add bowmark-ai/skill` (works on Claude Code, Codex, Cursor, Copilot, OpenCode, …), MCP-only via `claude mcp add` / a Codex `[mcp_servers.bowmark]` block, or point any MCP client straight at the URL. See [bowmark.ai/#install](https://bowmark.ai/#install).

## Install in Kiro

In Kiro, open the **Powers** panel, choose **Add Custom Power**, then **Import power from GitHub**, and paste `https://github.com/bowmark-ai/plugin`. Kiro reads the root `plugin.json` and `mcp.json`, so you get the hosted Bowmark MCP server as a power.

## Privacy and support

- Privacy policy: [bowmark.ai/privacy](https://bowmark.ai/privacy)
- Support: [support@bowmark.ai](mailto:support@bowmark.ai)

## Maintaining this plugin

How the five manifests, the skill mirror, versioning and validation work: [MAINTAINING.md](MAINTAINING.md).
