# Runheed

Error tracking your coding agent can read. Runheed catches exceptions in your Node.js or Python app and serves them over MCP, so Claude Code, Cursor, Codex or any MCP client can read the stack trace, fix the bug and mark it resolved.

- Website: https://runheed.com
- MCP server: `https://runheed.com/api/mcp` (Streamable HTTP). Sign in with OAuth (claude.ai, ChatGPT, Claude Code, Cursor, Codex), or send `Authorization: Bearer al_...` with an agent key.
- Setup for agents: https://runheed.com/SETUP.txt

![Claude Code reads a production error from Runheed, fixes it, runs the tests and marks it resolved (sample session)](assets/demo.gif)

This repo holds the Claude Code plugin, the Google Antigravity plugin, the agent skill and the MCP config. The Runheed service itself is hosted.

## Try it first

A demo server holds invented sample errors. It takes no account or key, and nothing is saved:

```
claude mcp add --transport http runheed-demo https://runheed.com/api/mcp/demo
```

Then ask your agent: "What is the top Runheed error, and what would you change?" Setup for other clients: https://runheed.com/demo#try

## Install

Claude Code plugin (signs you in on first use, no key to copy):

```
/plugin marketplace add getrunheed/runheed-plugin
/plugin install runheed@runheed
```

Or add the server directly:

| Client | How |
|---|---|
| Claude Code | `claude mcp add --transport http --scope user runheed https://runheed.com/api/mcp`, then run `/mcp` and choose Authenticate |
| Codex | `codex mcp add runheed --url https://runheed.com/api/mcp` then `codex mcp login runheed` |
| claude.ai / Claude Desktop | Connect from [Claude's connector directory](https://claude.ai/directory/connectors/runheed), or Customize > Connectors > Add custom connector, URL `https://runheed.com/api/mcp` |
| ChatGPT | Install [Runheed from ChatGPT's plugin directory](https://chatgpt.com/plugins/plugin_asdk_app_6ae8e9d612b48191a9d72706a9950b5e), or Plugins > + > Add custom MCP server, URL `https://runheed.com/api/mcp`, OAuth |
| Cursor | Add `{"mcpServers": {"runheed": {"url": "https://runheed.com/api/mcp"}}}` to `~/.cursor/mcp.json`, then sign in from Cursor Settings > MCP |
| Google Antigravity | `agy plugin install https://github.com/getrunheed/runheed-plugin` (this repo is also an Antigravity plugin: `.antigravity-plugin/plugin.json` + `mcp_config.json`), or add `{"mcpServers": {"runheed": {"serverUrl": "https://runheed.com/api/mcp"}}}` to `~/.gemini/config/mcp_config.json` and click Authenticate under Customizations |
| Gemini CLI | `gemini extensions install https://github.com/getrunheed/runheed-plugin` |

Then add the SDK to your app (Node.js / TypeScript, Python, or plain HTTP). Your agent can do both steps from https://runheed.com/SETUP.txt.

## Install the skill in any agent

`skills/runheed/SKILL.md` tells an agent when to reach for Runheed and how to set it up. It's the same file served at https://runheed.com/SKILL.md.

## Already using a Sentry SDK?

Keep it. Each Runheed project has a Sentry SDK DSN (`https://<key>@runheed.com/<number>`, on the Projects page and from
`runheed_list_projects`). Set it as the DSN in your existing `Sentry.init()` and errors go to Runheed, where your agent reads
them over MCP. Tested with @sentry/node 11, sentry-sdk 2 (Python), sentry-go 0.50, sentry-ruby 7, sentry/sentry 4 (PHP),
Sentry 7 for .NET, sentry-java 8 and @sentry/browser 11. Setup per language: https://runheed.com/for

## What your agent can do

| Tool | What it does |
|---|---|
| `runheed_search_errors` | Searches the workspace's error groups by text, status, project and release (including only the errors a release introduced). |
| `runheed_get_error` | Returns one error group in full: message, status, counts, first and last seen, environment, agent context, the top stack frames (with links to your repository) and the latest breadcrumbs. |
| `runheed_get_recent` | Returns the error groups seen most recently, newest first. |
| `runheed_get_trends` | Returns error statistics for the last 24 hours, 7 days or 30 days. |
| `runheed_get_error_context` | Returns everything recorded around an error: breadcrumbs, runtime, environment, release, the affected user and the agent session. |
| `runheed_resolve_error` | Marks an error group resolved, with an optional note such as the fixing commit. |
| `runheed_ignore_error` | Marks an error group ignored, for known or expected errors. |
| `runheed_unignore_error` | Moves an ignored error group back to unresolved. |
| `runheed_get_project_health` | Returns a 0 to 100 health score for a project, with recent issues and recommendations. |
| `runheed_list_projects` | Lists the workspace's projects with their DSNs. |
| `runheed_create_project` | Creates a project and returns its DSN, so the agent can add the SDK to the app. |
| `runheed_send_test_event` | Sends one test error to a project to check that events arrive. |

Read tools are read-only; the three status tools only flip an error's status, which can be flipped back, and the two setup tools create a project or one test event. Choose Read only when you connect to allow reading alone.

## Pricing

One flat price per workspace, every plan includes the MCP server:

- Solo: $29 a month. 50,000 events a month, 3 projects, 30-day history.
- Pro: $79 a month. 250,000 events a month, 15 projects, 90-day history.
- Scale: $199 a month. 1,000,000 events a month, unlimited projects, 180-day history.

Events over your plan's limit are rejected, never charged. Details: https://runheed.com/pricing

## Support and contributing

Questions: hello@greatwork.company. Issues and pull requests for the skill and plugin files are welcome here.

## Network access

The plugin's only network endpoint is runheed.com (`https://runheed.com/api/mcp`). It contains no scripts that run on your machine.

## Privacy

Privacy policy: https://runheed.com/privacy. Terms: https://runheed.com/terms

## License

MIT. Runheed is made by Great Work LLC.
