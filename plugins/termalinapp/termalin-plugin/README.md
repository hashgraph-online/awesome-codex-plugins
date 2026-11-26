# Termalin plugin

Manage your own Linux servers from a conversation with Claude, ChatGPT, Cursor, Kiro, Grok Build, Gemini CLI, Antigravity or Hermes Agent: run commands over SSH, read and write files over SFTP, query databases, and watch server health and alerts — through the [Termalin](https://termal.in) connector, without pasting an SSH key or a password into the chat.

This plugin bundles the Termalin MCP connector (`https://termal.in/mcp`) with ten skills that teach the agent how to use it well:

| Skill | What it does |
| --- | --- |
| `server-health` | Answers "how are my servers doing" from Termalin's monitoring data (CPU, memory, disk, load, failed services, certificates, alerts) before running anything. |
| `incident-triage` | Works through an alert or outage step by step, read-only first, and asks before any fix. |
| `run-commands` | The rules for running commands and editing files safely: bounded output, background jobs for long tasks, backups before config edits, no secrets in the chat, no destructive commands without a yes. |
| `deploy-check` | Verifies a server after a deployment: services, ports, logs, external response, certificate, metrics. |
| `database-access` | Explores and queries Postgres, MySQL/MariaDB, Redis, MongoDB and SQLite on a server, read-only by default. |
| `backups` | Checks that a server is backed up, proposes an encrypted backup job for folders and databases (the owner confirms it), and backs up right before a risky change. |
| `security-updates` | Lists pending updates and known vulnerabilities (CVEs), plans the update with you, installs it as a background job and checks what is left. |
| `server-setup` | Prepares a fresh VPS step by step: updates, a sudo user, SSH settings, firewall, swap, Docker, HTTPS. |
| `internal-sites` | Opens Grafana, Portainer or any service on localhost from your Termalin account, without opening a port. |
| `remote-desktop` | Works on Windows (RDP) and Linux or Mac (VNC) desktops you open for AI: screenshot, click, type, one step at a time, never typing passwords. |

## Use it

1. Sign in at [termal.in](https://termal.in/account) and install a Connector on a server (one command, no inbound port). The Connector is part of Pro; a new account gets a 14-day Pro trial, no card needed.
2. Add this plugin, then connect the Termalin connector from the plugin's **Connectors** tab and approve access on the consent screen.
3. Ask Claude: "Are all my servers online?", "Check disk space on prod", "Tail the nginx error log and explain the errors", "What's in the orders table?", "I just deployed the API, is it fine?".

Each connection has a policy you set in your Termalin account (full access, an allowlist of commands, or read-only), a note that tells Claude what to be careful with on that server, and a full audit trail of every command. You can disconnect Claude from your account page at any time.

## Install in other agents

The same repository carries a manifest for each plugin format, so one install works everywhere; the MCP server is the same `https://termal.in/mcp` and signs you in with OAuth on first use.

| Agent | How |
| --- | --- |
| Claude (claude.ai, Claude Desktop, Cowork) | [Termalin in the Claude directory](https://claude.ai/directory/termalin) |
| Claude Code | `/plugin marketplace add termalinapp/termalin-plugin`, then `/plugin install termalin@termalin` |
| ChatGPT and Codex | Termalin in the ChatGPT app directory; the `chatgpt/` folder is that package |
| Cursor, Kiro and other [Agent Plugins](https://agent-plugins.org) clients | Root `plugin.json` + `mcp.json`; install from this repository URL or from the marketplace once listed |
| Gemini CLI | `gemini extensions install https://github.com/termalinapp/termalin-plugin` |
| Antigravity | `agy plugin install https://github.com/termalinapp/termalin-plugin` |
| Hermes Agent | `hermes plugins install termalin`, then `hermes plugins enable termalin`; see [Hermes Agent](#hermes-agent) below for the sign-in entry |
| Grok Build | `/plugin` marketplace, or install from this repository URL |
| Qwen Code | `qwen extensions install termalinapp/termalin-plugin` (reads the root `plugin.json`, `mcp.json` and the skills as an Agent Plugins v1 package) |
| Clients that only speak stdio: CI jobs, scripts, Claude Desktop with an API key | `npx -y termalin-mcp` with `TERMALIN_API_KEY` in the environment, the open-source bridge [termalin-mcp](https://github.com/termalinapp/termalin-mcp) (MIT, npm) |
| Any agent that uses the skills CLI ([skills.sh](https://skills.sh)) | `npx skills add termalinapp/termalin-plugin` installs the ten skills; add the MCP server by URL as below |
| Grok, Gemini, Mistral Le Chat, Perplexity, VS Code, Zed and any other MCP client | Add a custom connector with the URL `https://termal.in/mcp` ([instructions](https://termal.in/mcp/)) |

### Local models: LM Studio, Jan, Open WebUI, Goose, Msty, 5ire, Zed

The hosted server works with any model that can call tools, including local ones. The chat runs on your machine; only the tool calls go to termal.in, which forwards them to your servers through their Connector.

| App | How |
| --- | --- |
| LM Studio (0.3.17+) | [![Add MCP Server termalin to LM Studio](https://files.lmstudio.ai/deeplink/mcp-install-light.svg)](https://lmstudio.ai/install-mcp?name=termalin&config=eyJ1cmwiOiJodHRwczovL3Rlcm1hbC5pbi9tY3AifQ%3D%3D) or add `"termalin": {"url": "https://termal.in/mcp", "headers": {"Authorization": "Bearer <API key>"}}` to `mcp.json` (LM Studio has no OAuth sign-in, so use an API key from [termal.in/account](https://termal.in/account)) |
| Jan | Settings → MCP Servers → add a remote server with the URL `https://termal.in/mcp`; Jan runs the OAuth sign-in itself |
| Open WebUI (0.6.31+) | Admin → External Tools → add an **MCP (Streamable HTTP)** server with the URL `https://termal.in/mcp` and OAuth 2.1, or a Bearer header with an API key |
| Goose | Extensions → Browse (the official MCP registry lists Termalin as `in.termal/termalin-web`), or Add custom extension → Streamable HTTP → `https://termal.in/mcp` |
| Msty Studio | Toolbox → add an HTTP tool with the URL `https://termal.in/mcp` and OAuth or a bearer token |
| 5ire | Marketplace → Termalin (asks for the API key), or Tools → add with the URL |
| Zed | Agent panel → Add Remote Server → `https://termal.in/mcp`; Zed prompts for the OAuth sign-in |
| Ollama | The Ollama app has no MCP client; run a local model through one of the apps above, or `ollama launch` Claude Code, OpenCode or Codex with Termalin installed there |

An API key is bound to the servers you choose and can be read-only; it never carries an SSH key.

### Hermes Agent

The repository root is also a portable Agent Plugins package for [Hermes Agent](https://hermes-agent.nousresearch.com): `plugin.json`, `mcp.json` and the same `skills/` folder. Hermes installs it switched off, so enable it after installing:

```bash
hermes plugins install termalin
hermes plugins enable termalin
```

`hermes plugins install termalin` takes the pinned release from the Hermes plugin catalog; `hermes plugins install termalinapp/termalin-plugin` takes this repository directly.

The package's `mcp.json` cannot run the sign-in on its own, so add the server to `~/.hermes/config.yaml` with OAuth. Keep `trust: untrusted`: an entry in `config.yaml` replaces the package's, including its trust setting, and `untrusted` makes Hermes ask before every tool that can change something on a server (`ssh_exec`, `sftp_write`, `job_start`, `data_query` with writes, backups, web links).

```yaml
mcp_servers:
  termalin:
    url: https://termal.in/mcp
    auth: oauth
    trust: untrusted
```

Then sign in and check the connection:

```bash
hermes mcp login termalin
hermes mcp test termalin
```

The browser page lets you pick which of your enrolled servers Hermes may reach. Hermes stores and refreshes the tokens; the package holds no credentials.

## Data

The plugin itself stores nothing and runs no code on your machine. The commands, file contents and query results Claude requests travel from your server through its Termalin Connector to `termal.in` and back to the chat. Access is granted through OAuth from your Termalin account; each command is authenticated with a short-lived certificate issued by Termalin's SSH CA. See the [privacy policy](https://termal.in/privacy) and [terms](https://termal.in/terms).

## Works with

The Termalin desktop app (Windows, macOS, Linux), the iOS app and the web cabinet — none of them needs to be open for the plugin to work. Support: [termal.in/support](https://termal.in/support) · support@termal.in
