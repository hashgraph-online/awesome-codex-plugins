# Silicon Valley Atlas for agents

Search sourced startup and founder profiles, match companies to a product,
and manage your outreach lists through `https://svatlas.io/mcp`.
Sign in with the Google account you use on [SV Atlas](https://svatlas.io).
OAuth uses dynamic registration and PKCE; no API key is required. Meaning
search and product matching use your account's monthly quota. Other reads
are not metered. List changes affect the signed-in account.

The same steps as a web page: [svatlas.io/agents](https://svatlas.io/agents).

## Claude Code

```sh
claude plugin marketplace add https://svatlas.io/plugins/marketplace.json
claude plugin install svatlas@svatlas
```

Requires Claude Code 2.1.224 or later for hosted archive sources. Restart
Claude, open `/mcp`, and authenticate the SV Atlas connection. The plugin
includes `find-customers` and `research-startups` skills.

For the MCP tools alone:

```sh
claude mcp add --transport http svatlas https://svatlas.io/mcp
claude mcp login svatlas
```

Claude's connector directory has a separate, reviewed listing. Installing
this marketplace does not imply Anthropic directory approval.

## OpenCode

Merge this into `opencode.json` (OpenCode 1.x):

```json
{"$schema":"https://opencode.ai/config.json","mcp":{"svatlas":{"type":"remote","url":"https://svatlas.io/mcp","enabled":true}}}
```

```sh
opencode mcp auth svatlas
opencode run 'Use svatlas search_companies to find three AI developer-tool companies.'
```

[Download the config](https://svatlas.io/plugins/opencode.json). To use the
workflows too, unpack the [plugin ZIP](https://svatlas.io/plugins/svatlas.zip)
and copy its `skills/` folders into your project's `.opencode/skills/`.
OpenCode supports remote MCP directly; there is no extra JavaScript package.

## Zed

Open Settings → AI → MCP Servers → Add Remote Server and enter
`https://svatlas.io/mcp`, then authenticate. Equivalent settings:

```json
{"context_servers":{"svatlas":{"url":"https://svatlas.io/mcp"}}}
```

[Download settings](https://svatlas.io/plugins/zed.json). Zed recommends
native remote MCP for hosted servers; its binary/npm context-server
extensions are being deprecated. Atlas is already published in the official
MCP Registry as `io.svatlas/svatlas`; registry publication does not guarantee
inclusion in an editor's curated catalog.

## VS Code

```sh
code --add-mcp '{"name":"svatlas","type":"http","url":"https://svatlas.io/mcp"}'
```

Run **MCP: List Servers**, choose SV Atlas, start it, and complete sign-in.
[Download `.vscode/mcp.json` content](https://svatlas.io/plugins/vscode.json)
and merge its `servers` object into existing configuration.
The generated [install links](https://svatlas.io/plugins/install-links.json)
include a `vscode:mcp/install` one-click URL. GitHub's MCP gallery is curated
separately from the official MCP Registry.

## Cursor

Merge into `.cursor/mcp.json`, then authenticate in MCP settings:

```json
{"mcpServers":{"svatlas":{"url":"https://svatlas.io/mcp"}}}
```

[Download config](https://svatlas.io/plugins/cursor.json) or use the Cursor
one-click URL in [install links](https://svatlas.io/plugins/install-links.json).
Cursor also supports the portable Agent Plugins package: unpack the
[ZIP](https://svatlas.io/plugins/svatlas.zip) into
`~/.cursor/plugins/local/svatlas/` and reload Cursor. This includes the skills.
Marketplace and community-directory review are separate submissions.

## OpenClaw / ClawHub

Configure the hosted connection before using the skills:

```sh
openclaw mcp set svatlas '{"url":"https://svatlas.io/mcp","transport":"streamable-http","auth":"oauth"}'
openclaw mcp login svatlas
openclaw mcp probe svatlas
```

Unpack the [ZIP](https://svatlas.io/plugins/svatlas.zip), then copy the two
`skills/` folders into your OpenClaw workspace's `skills/` directory.
ClawHub publication is separate; do not assume catalog slugs are published
until their listing URLs resolve. A skill install does not install its MCP
connection. ClawHub publishes skills under MIT-0; the hosted Atlas service
remains subject to its [terms](https://svatlas.io/terms) and account limits.

## Grok Build

```sh
grok mcp add --transport http svatlas https://svatlas.io/mcp
grok mcp doctor svatlas --json
```

Authenticate when prompted, then ask Grok to call
`svatlas__search_companies`. Grok Build's official plugin marketplace accepts
remote MCP integrations through reviewed GitHub PRs. The generated Claude
compatibility manifest also works with its plugin loader. Grok.com supports
custom MCP connectors, but that is a separate surface from Grok Build's
public marketplace.

## Codex / ChatGPT

For Codex's MCP tools:

```sh
codex mcp add svatlas --url https://svatlas.io/mcp
codex mcp login svatlas
```

In ChatGPT the plugin is an app, served live by the MCP server rather than
packaged in the ZIP:
- Search and match results render as company cards.
- **Atlas** opens from the sidebar with search, your lists, and company profiles.
- **My lists** opens as a tab beside any conversation.
- Selected companies attach to the chat.
- On desktop, companies can be @-mentioned in the composer.
- The `get-started` skill runs once after install.

To try it before directory approval:
1. Turn on Settings → Security and login → Developer mode.
2. Add `https://svatlas.io/mcp` at [chatgpt.com/plugins](https://chatgpt.com/plugins).
3. To test the whole plugin with its skills, install it from a local
   marketplace in the ChatGPT desktop app
   ([OpenAI guide](https://developers.openai.com/plugins/build/plugins#install-a-local-plugin-manually)).

The [plugin ZIP](https://svatlas.io/plugins/svatlas.zip) contains the portable
Agent Plugins manifest plus a Codex compatibility manifest and the three skills.
It contains no credentials.

## Install from this repository

- Claude Code: `claude plugin marketplace add phnx-labs/svatlas-mcp`, then
  `claude plugin install svatlas@svatlas`.
- Gemini CLI: `gemini extensions install https://github.com/phnx-labs/svatlas-mcp`, then run
  `/mcp auth svatlas` inside Gemini.
- Cursor, Codex and Kiro read the Agent Plugins manifest at the root
  (`plugin.json`, `mcp.json`, `skills/`).
- Cline: see [llms-install.md](llms-install.md).

## About this repository

These manifests and skills are generated from Atlas's plugin source, version
1.3.0. The service itself runs at https://svatlas.io; this repository holds no
application code.

Requires a Google account to sign in to Atlas. Search and product matching
use the account's monthly quota; list tools act only within the user's access
rights.

Network endpoints: https://svatlas.io/mcp (Streamable HTTP); https://svatlas.io/oauth/authorize,
/oauth/token, /oauth/register and /.well-known/ (OAuth 2.1, PKCE and discovery).
Browser sign-in uses Google via Atlas's hosted authentication provider.
No API key, password, or token belongs in this package or chat. Tokens are
stored by the MCP client. Revoke access in Atlas Settings.

Privacy policy: https://svatlas.io/privacy. Terms: https://svatlas.io/terms.
Support: https://svatlas.io/support or support@getrush.ai.

The files here are MIT licensed. Using the hosted service follows its terms.
