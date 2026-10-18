# Setting up DropTheHassle in your agent

Three ways in. None needs an account for the first deploy.

| | CLI | Local MCP server | Hosted MCP connector |
| --- | --- | --- | --- |
| Run | `npx -y dropthehassle@latest deploy [folder] --email <the user's email>` | `npx -y dropthehassle-mcp` (stdio) | `https://dropthehassle.com/mcp` (Streamable HTTP) |
| Reads the folder from disk | yes | yes (`folder`, absolute path) | no: files are sent inline |
| No-token tools | deploy | `deploy_site` (npm 0.4.2). Source 0.4.3 adds `search_domain` and `whoami` | `deploy_site`, `search_domain`, `whoami` |
| Needs | Node.js 18+, network to dropthehassle.com | Node.js 18+, network to dropthehassle.com | an MCP client that supports remote servers |

Versions checked on 2026-10-01: npm `dropthehassle` 0.3.0, npm `dropthehassle-mcp` 0.4.2. The
hosted connector reports 0.4.2 but already takes `site` addresses and allows `search_domain`
without a token. Current versions are listed in https://dropthehassle.com/llms.txt.

## Token (only for account tools)

- The human opens https://dropthehassle.com, menu (top right), **Connect your AI**, and copies a
  token that starts with `dth_`. An account can have up to 10 live tokens.
- Local server: put it in the server's `env` as `DTH_TOKEN`. Hosted: send
  `Authorization: Bearer <token>`.
- Leave it out until the human has the real token. A placeholder is never right. Don't commit it.
  Use a gitignored local config file where the tool has one.
- The token can deploy, list sites, rearrange names and create a payment link. It cannot pay.

## Claude Code

```bash
claude mcp add dropthehassle -- npx -y dropthehassle-mcp
```

With a token, run `claude mcp add dropthehassle -e DTH_TOKEN=dth_… -- npx -y dropthehassle-mcp`.
Do this in the human's own terminal so the token doesn't end up in the chat. To share the setting
with a project, `--scope project` writes `.mcp.json`. Only commit that file without a token in it.

Or skip MCP and run the CLI from the agent's shell, in the project folder after the build:
`npx -y dropthehassle@latest deploy . --email <the user's email>`.
Ask the user for their email first, then run it.

**Claude Code on the web** (claude.ai/code) runs in a cloud machine whose default network level
(Trusted) blocks dropthehassle.com. Either add the hosted connector `https://dropthehassle.com/mcp`
as a custom connector in claude.ai and enable it for the session, or edit the environment: set
network access to Custom, add `dropthehassle.com` and tick the default package-manager list. The
cloud machine is temporary, so `.dropthehassle.json` does not survive the session.
Guide: https://dropthehassle.com/guides/claude-code-on-the-web-deploy-custom-domain

## Cursor

`.cursor/mcp.json` in the project, or `~/.cursor/mcp.json` for every project:

```json
{
  "mcpServers": {
    "dropthehassle": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "dropthehassle-mcp"]
    }
  }
}
```

Add `"env": { "DTH_TOKEN": "dth_…" }` only with a real token, and keep a file with a token out of
git. One-click install link (no token):
`cursor://anysphere.cursor-deeplink/mcp/install?name=dropthehassle&config=eyJkcm9wdGhlaGFzc2xlIjp7ImNvbW1hbmQiOiJucHgiLCJhcmdzIjpbIi15IiwiZHJvcHRoZWhhc3NsZS1tY3AiXX19`

## Codex

```bash
codex mcp add dropthehassle --url https://dropthehassle.com/mcp
```

or in `~/.codex/config.toml`:

```toml
[mcp_servers.dropthehassle]
url = "https://dropthehassle.com/mcp"
```

Codex keeps network access off in its sandbox by default. To use the CLI instead, approve the one
`npx -y dropthehassle@latest deploy . --email <the user's email>` command when Codex asks for network access. Setting
`[sandbox_workspace_write] network_access = true` opens the network for every command.
**Codex cloud**: turn on internet access for the environment and allow `dropthehassle.com` (plus
package managers so npm works). On the legacy setup, a GET-only method filter blocks the upload.
Codex's docs don't list MCP for cloud tasks, so use the CLI there.
Guide: https://dropthehassle.com/guides/codex-deploy-custom-domain

## Windsurf

New Windsurf tabs use the Devin Local agent. Put the server in the gitignored local file
`.devin/mcp_config.local.json`, or run `devin mcp add dropthehassle -- npx -y dropthehassle-mcp`:

```json
{
  "mcpServers": {
    "dropthehassle": {
      "command": "npx",
      "args": ["-y", "dropthehassle-mcp"]
    }
  }
}
```

Cascade (the older agent) opens its own MCP config from the Cascade panel, with the same
`mcpServers` shape. Guide: https://dropthehassle.com/guides/windsurf-deploy-custom-domain

## Any other MCP client

Use the same `mcpServers` block (`npx -y dropthehassle-mcp`), or add the hosted URL
`https://dropthehassle.com/mcp` as a remote server.

## Put the spending rule in the project

Paste this into `CLAUDE.md`, `AGENTS.md` or a Cursor rule so every session follows it:

```markdown
# DropTheHassle

Never buy anything without asking me. Never buy a domain, email or subscription for me without asking first. When something costs money, give me the payment link and let me pay.

The token cannot pay.
```

## Hosted connector: sending files inline

`deploy_site` on `https://dropthehassle.com/mcp` takes
`files: [{ "path": "index.html", "content": "<!doctype html>…", "encoding": "utf8" }, …]`.

- Paths are relative to the site root, with forward slashes.
- Use `utf8` for text files and `base64` (standard alphabet) for images, fonts and other binaries.
- Leave out `node_modules`, `.git` and hidden files. `.well-known` is allowed.
- The decoded files count against the same caps: 25 MB and 1,000 files before a claim, 100 MB and
  5,000 files signed in. Big video usually doesn't fit. Use the CLI or the local server for big
  sites, because they zip the folder from disk instead of sending it through the conversation.
