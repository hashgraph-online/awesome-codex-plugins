# Treza plugin

Make AI videos from your coding agent. This plugin connects Cursor, Codex, Gemini CLI, Claude Code, and any client that supports [Agent Plugins](https://agent-plugins.org) or MCP to Treza, so your agent can make a clip from a description, finish media you already have, and build video pipelines that render and post to YouTube and TikTok on a schedule.

- Server: `https://www.trezalabs.com/api/mcp` (Streamable HTTP, OAuth with dynamic client registration)
- Setup for each app: https://www.trezalabs.com/integrations
- Docs: https://docs.trezalabs.com/api/mcp-server
- Privacy: https://docs.trezalabs.com/terms-and-privacy/privacy

## Install

The first connection signs you in to Treza with Google and creates your account. There is no key to paste.

**Cursor.** [Add to Cursor](https://www.trezalabs.com/integrations/cursor), or put this in `~/.cursor/mcp.json` (or `.cursor/mcp.json` in a project) and restart Cursor:

```json
{
  "mcpServers": {
    "treza": { "url": "https://www.trezalabs.com/api/mcp" }
  }
}
```

**Codex CLI.**

```bash
codex mcp add treza --url https://www.trezalabs.com/api/mcp
codex mcp login treza
```

In the ChatGPT desktop app, Treza is in the plugin catalog ChatGPT and Codex share: open Plugins, open Treza and add it.

**Gemini CLI.** This repo is a Gemini CLI extension:

```bash
gemini extensions install https://github.com/treza-labs/treza-plugin
```

Then run `/mcp auth treza` inside Gemini CLI. Gemini also loads the skill in `skills/`.

**Antigravity CLI.** Add Treza to `~/.gemini/config/mcp_config.json`, then type `/mcp` to sign in:

```json
{
  "mcpServers": {
    "treza": { "serverUrl": "https://www.trezalabs.com/api/mcp" }
  }
}
```

**Claude Code.** This repo is a Claude Code plugin and marketplace. Installing it adds the Treza server and the skill. Inside Claude Code:

```
/plugin install treza --marketplace treza-labs/treza-plugin
```

Or from a shell:

```bash
claude plugin marketplace add treza-labs/treza-plugin
claude plugin install treza@treza
```

Then run `/mcp`, pick `treza` and sign in. The skill runs as `/treza:treza-video-pipelines`, and Claude also picks it up on its own when you ask for a video. To add only the server, without the skill:

```bash
claude mcp add --transport http --scope user treza https://www.trezalabs.com/api/mcp
```

**Cline.** Follow [`llms-install.md`](llms-install.md), or add the URL under MCP Servers, Remote Servers, with Streamable HTTP, then click Authenticate.

**Clients that only start local servers.** This repo ships [`treza-mcp`](https://www.npmjs.com/package/treza-mcp), a small Node bridge that forwards every tool, prompt, and resource to the hosted server. It needs a scoped key from the [API keys page](https://www.trezalabs.com/platform/api-keys) in `TREZA_API_KEY`:

```json
{
  "mcpServers": {
    "treza": {
      "command": "npx",
      "args": ["-y", "treza-mcp"],
      "env": { "TREZA_API_KEY": "treza_live_..." }
    }
  }
}
```

`TREZA_MCP_URL` overrides the endpoint (staging, self-hosted). The bridge runs nothing locally; it is a proxy.

## What is inside

| File | Purpose |
|---|---|
| `plugin.json` | Agent Plugins manifest |
| `.cursor-plugin/plugin.json` | Cursor plugin manifest: the same server and skill, with the logo |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Claude Code plugin and the one-plugin marketplace it installs from |
| `mcp.json` | Declares the remote Treza MCP server for plugin-aware clients |
| `skills/treza-video-pipelines/` | A skill that teaches the agent the shortest path to a video, and to price a render before it starts |
| `gemini-extension.json` | Gemini CLI extension manifest (the same remote server) |
| `llms-install.md` | Setup steps an agent such as Cline can follow on its own |
| `bin/treza-mcp.mjs` | The stdio bridge published to npm as `treza-mcp`. The plugin itself does not run it |

## Tools

Twenty-six tools your agent can call:

- **Make a video:** `make_video` turns a description into one clip in a single call. It picks the model, prepares the render, and returns the price; `run_pipeline` starts it once the person accepts.
- **Finish media you have:** `list_assets` browses the library, `import_media` adds a file (a public link, or a local file sent through `create_upload_url`), `edit_asset` runs one operation over one file (captions, upscale, trim, crop, overlay, background removal), and `assemble_video` joins clips over narration and a music bed, with captions.
- **Pipelines:** `list_pipeline_templates`, `list_node_types`, `get_node_type`, `create_pipeline`, `update_pipeline`, `publish_pipeline`, `list_pipelines`, `get_pipeline`, `set_schedule_paused`
- **Runs:** `run_pipeline`, `get_run`, `list_runs`, `cancel_run`
- **Channels and publishing:** `list_connected_channels`, `connect_channel` returns a link that connects a YouTube channel or TikTok account in the person's own browser, and `publish_asset` lays a finished video out for review before it posts
- **Budget and account:** `estimate_run_cost`, `get_credit_balance`, `get_profile`, `create_api_key` (OAuth connections only)

Two more, `open_library` and `confirm_publish`, belong to Treza's panels: they run when the person uses the panel, never from the model.

Read-only tools carry `readOnlyHint`. Renders spend prepaid credits, so `make_video` and `estimate_run_cost` quote a price first, and `run_pipeline` starts a quoted run once, at that price. Renders run in the background and return a run to poll with `get_run`.

In clients that show MCP Apps panels, such as ChatGPT and Claude, results appear as panels: the finished file, the price with a Start render button, a library to pick files from, a map of a pipeline, and the post before it goes out. Other clients get the same answers as text and links. Posting with `publish_asset` needs a panel; without one, publish through a pipeline that ends in a `youtube-upload` or `tiktok-upload` node.

Runs spend prepaid credits on your Treza account. Agents with a wallet can top up over [x402](https://www.trezalabs.com/x402) with no human in the loop.

MIT licensed. Support: hello@trezalabs.com
