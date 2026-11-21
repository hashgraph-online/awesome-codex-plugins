# GitRanks Contribute

Find open-source GitHub issues to contribute to, matched to your skills and checked ready for a pull request. Your
agent fixes one; you review the change and approve the pull request on
[gitranks.com](https://gitranks.com/contribute?utm_source=github&utm_campaign=plugin-readme), and it opens under your
name.
Every pull request opened from gitranks.com says it was made with GitRanks Contribute and your agent (with its model
when the agent reports one), and links where maintainers can tell us something is off or opt out.

[![In Claude Code: install the plugin with one command, sign in once on gitranks.com, then ask for an open-source issue and get your picks](assets/one-command.gif)](#claude-code)

This repository connects your own agent (Claude Code, Codex, Cursor, Gemini CLI and others) to the GitRanks Contribute
MCP server at `https://mcp.gitranks.com/mcp`, and adds a `contribute` skill that walks it through one issue. It holds
only configuration and instructions: the server runs on GitRanks.

GitRanks Contribute is in beta. It is free.

## How you connect

Add the server's URL to your agent, then sign in from it. Your agent opens gitranks.com in your browser: sign in with
GitHub, check what the agent will be able to do, and press **Allow**. Your agent keeps the access it gets and renews it
by itself while you use it. Nobody copies a token.

Each agent you connect is listed on gitranks.com under **Contribute → Settings → Your own agent (MCP)**, where you can
disconnect it at any time.

A client that can't sign in can still use a personal token: see [Use a token instead](#use-a-token-instead).

**Then ask your agent:** "Find me an open-source issue to work on with GitRanks." It shows you a few issues and you
choose one. When it hands the change back, it gives you a link: review the change there and approve the pull request.
Unless you turn autopilot on, nothing reaches GitHub before you approve it; the first time, gitranks.com asks for GitHub
access to fork the repository and open the pull request in your name. Setup for every client, troubleshooting and help:
[the MCP docs](https://gitranks.com/contribute/mcp?utm_source=github&utm_campaign=plugin-readme).

## Install

One click, then confirm in your client and sign in on gitranks.com when it asks:

- **Claude** (claude.ai and Claude Desktop): [Add GitRanks Contribute to Claude](https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=GitRanks%20Contribute&connectorUrl=https%3A%2F%2Fmcp.gitranks.com%2Fmcp)
- **Cursor:** [![Add gitranks MCP server to Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://cursor.com/en/install-mcp?name=gitranks&config=eyJ1cmwiOiJodHRwczovL21jcC5naXRyYW5rcy5jb20vbWNwIn0%3D)
- **VS Code:** [![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_GitRanks_Contribute-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vscode.dev/redirect/mcp/install?name=gitranks&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fmcp.gitranks.com%2Fmcp%22%7D)
- **Kiro:** [![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](https://kiro.dev/launch/mcp/add?name=gitranks&config=%7B%22url%22%3A%22https%3A%2F%2Fmcp.gitranks.com%2Fmcp%22%7D)

Each link opens the client's own add-server dialog with the URL filled in; nothing is added until you confirm it there.
The setup line for every other client is below. Whichever client you use, the same limits keep it
[fair to maintainers](#fair-to-maintainers).

### Claude Code

```bash
claude plugin marketplace add gitranks/contribute
claude plugin install gitranks-contribute@gitranks
```

On Claude Code 2.1.292 or later, one line does both:
`claude plugin install gitranks-contribute --marketplace gitranks/contribute`.

Then run `/mcp`, pick `plugin:gitranks-contribute:gitranks`, choose **Authenticate** and sign in on gitranks.com.

Without the plugin: `claude mcp add --scope user --transport http gitranks https://mcp.gitranks.com/mcp`, then `/mcp` → `gitranks` →
**Authenticate**.

### Claude Desktop and claude.ai

Use the [Add to Claude link](https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=GitRanks%20Contribute&connectorUrl=https%3A%2F%2Fmcp.gitranks.com%2Fmcp)
above, or by hand: **Customize → Connectors → Add → Add custom connector**, name `GitRanks Contribute`, URL
`https://mcp.gitranks.com/mcp`. Then **Connect** it and sign in on gitranks.com.

In Claude Desktop and claude.ai you can find, claim and track issues. The fix needs Claude Code or another agent that
can run a shell, signed in to the same account: it picks up your claim.

### ChatGPT

On [chatgpt.com/plugins](https://chatgpt.com/plugins), press **+** and choose **Add custom MCP server**. Name it
`GitRanks Contribute`, paste `https://mcp.gitranks.com/mcp` and set authentication to **OAuth**. Confirm the warning
with **I understand and want to continue**, press **Create as a plugin**, then install it. ChatGPT asks you to sign in:
your browser opens GitRanks, where you allow it. Then start a new chat and pick it with **@**.

In ChatGPT, on the web, desktop or your phone, you can find, claim and track issues. The fix needs Codex or another
agent that can run a shell, signed in to the same account: it picks up your claim.

### Gemini CLI

```bash
gemini extensions install https://github.com/gitranks/contribute
```

Then run `/mcp auth gitranks` and sign in on gitranks.com.

Without the extension: `gemini mcp add --scope user --transport http gitranks https://mcp.gitranks.com/mcp`, then
`/mcp auth gitranks`.

### Codex

Codex can work on open-source issues picked for your skills, and you review every change before a pull request opens
in your name. The work runs on your ChatGPT plan. GitRanks picks the issue, briefs Codex on it, checks the patch and
opens the pull request you approve; it runs no model for you.

1. Add GitRanks:

   ```bash
   codex mcp add gitranks --url https://mcp.gitranks.com/mcp
   ```

2. Sign in: `codex mcp login gitranks` opens gitranks.com. Sign in with GitHub and press **Allow**. There's no token to
   copy.
3. Ask Codex: "Find me an open-source issue to work on with GitRanks." Codex calls `find_issues` and lists issues
   picked for you. For the one you choose it calls `claim_issue`, which holds it for you and returns the repository's
   rules and how to test. Codex then works on a fresh clone and hands the commits back with `submit_patch`.
4. Review on gitranks.com: look at the diff, the checks and the pull request text, then approve, send it back with a
   note, or discard it. The pull request opens from your fork, in your name, and says it was made with AI. The first
   time, gitranks.com asks for GitHub access to fork the repository and open the pull request.

Or, instead of steps 1 and 2, the plugin, which adds the skill too: this repository is a Codex plugin marketplace.
Run `codex plugin marketplace add gitranks/contribute`, then install GitRanks Contribute from `/plugins` in Codex (or
the Plugins Directory in the ChatGPT desktop app) and sign in on gitranks.com when it asks.

### Cursor

GitRanks hands Cursor's agent an open-source issue that fits your skills, and you review the change before a pull
request opens in your name. The agent runs on your Cursor plan.

1. Use the Cursor button above, or add this to `~/.cursor/mcp.json`:

   ```json
   { "mcpServers": { "gitranks": { "url": "https://mcp.gitranks.com/mcp" } } }
   ```

2. Cursor offers to sign in when it connects: gitranks.com opens, you sign in with GitHub and press **Allow**. There's
   no token to copy.
3. In the agent panel, ask: "Find me an open-source issue to work on with GitRanks." Pick one from the list, and
   Cursor's agent claims it, fixes it and hands the change back. Then review and approve on gitranks.com.

### VS Code and Kiro

Use the buttons above, or add the server by its URL alone; the editor offers to sign in when it first connects.

- **VS Code** (`.vscode/mcp.json` in a workspace, or **MCP: Open User Configuration**):

  ```json
  { "servers": { "gitranks": { "type": "http", "url": "https://mcp.gitranks.com/mcp" } } }
  ```

- **Kiro** (`~/.kiro/settings/mcp.json`, or `.kiro/settings/mcp.json` in a workspace):

  ```json
  { "mcpServers": { "gitranks": { "url": "https://mcp.gitranks.com/mcp" } } }
  ```

### Other clients

Each one connects by the URL alone and signs in on gitranks.com in your browser:

- **GitHub Copilot CLI:** `copilot mcp add --transport http gitranks https://mcp.gitranks.com/mcp`. The browser opens to
  sign in on first use; `/mcp auth gitranks` signs in again. The plugin may also install with
  `copilot plugin install gitranks/contribute` (not tested yet).
- **Devin** (CLI and Desktop): `devin mcp add gitranks https://mcp.gitranks.com/mcp`, then `devin mcp login gitranks`.
- **Amp:** `amp mcp add gitranks https://mcp.gitranks.com/mcp`. Amp opens the sign-in page in your browser when it
  starts.
- **opencode:** `opencode mcp add gitranks --url https://mcp.gitranks.com/mcp`, then `opencode mcp auth gitranks`.
- **Zed:** Settings → AI → MCP Servers → Add Server → Add Remote Server, or in `settings.json`
  `{ "context_servers": { "gitranks": { "url": "https://mcp.gitranks.com/mcp" } } }`. Zed asks you to sign in when it
  connects.
- **Cline:** `cline mcp add gitranks https://mcp.gitranks.com/mcp --transport http`, or in `cline_mcp_settings.json`
  (set the type: without it Cline falls back to the old SSE transport):

  ```json
  { "mcpServers": { "gitranks": { "type": "streamableHttp", "url": "https://mcp.gitranks.com/mcp" } } }
  ```

  Then authorize it (OAuth) when Cline offers to, and sign in.
- **Factory droid:** `droid mcp add gitranks https://mcp.gitranks.com/mcp --type http`, then `/mcp` in Droid and sign
  in in the browser.
- **Warp:** Settings → Agents → MCP servers → **+ Add**, paste
  `{ "gitranks": { "url": "https://mcp.gitranks.com/mcp" } }`, then **Start**: the browser opens to sign in.
- **Clients without sign-in for remote servers** (JetBrains AI Assistant, Augment, clients that only run local
  servers): connect through the [`mcp-remote`](https://github.com/geelen/mcp-remote) bridge, which signs in for them.
  It opens the browser on first run:

  ```json
  { "mcpServers": { "gitranks": { "command": "npx", "args": ["-y", "mcp-remote", "https://mcp.gitranks.com/mcp", "--transport", "http-only"] } } }
  ```

- **Any MCP client** with streamable HTTP and sign-in: URL `https://mcp.gitranks.com/mcp`, nothing else.

### Antigravity

1. Add the server to Antigravity's MCP config, `~/.gemini/config/mcp_config.json`, with the URL alone. In the IDE, open
   it from the … menu at the top of the agent panel → MCP Servers → Manage MCP Servers → View raw config.

   ```json
   { "mcpServers": { "gitranks": { "serverUrl": "https://mcp.gitranks.com/mcp" } } }
   ```

2. In the **agent's window**, click **Customizations**, scroll down to **MCP servers** and click **Sign in** next to
   `gitranks`. Your browser opens gitranks.com: sign in with GitHub and press **Allow**.

Don't use the **Authenticate** button on the **Manage MCP Servers** page: it only opens Settings → Customizations,
which has no MCP servers section. Sign in from the agent's window instead.

A token works too: see [Use a token instead](#use-a-token-instead).

### Plugin formats in this repository

The skill in `skills/contribute/SKILL.md` works in any agent that reads Agent Skills. The repository packages it with
the server for each plugin format below. Each connects by signing in.

- `.claude-plugin/` and `.mcp.json`: the Claude Code plugin and its marketplace (`gitranks`);
- `gemini-extension.json`: the Gemini CLI extension;
- `plugin.json` and `mcp.json` at the root: an [Agent Plugins](https://github.com/agentplugins/agent-plugins-spec)
  package, for clients and marketplaces that install that format, with the listing and review details for the ChatGPT
  and Codex plugin directory;
- `.agents/plugins/marketplace.json`: the Codex plugin marketplace;
- `.devin-plugin/plugin.json`: the Devin plugin manifest;
- `.antigravity-plugin/plugin.json` and `mcp_config.json`: the Antigravity plugin manifest and its server, by sign-in
  (installing the plugin is not tested in Antigravity yet; the setup in [Antigravity](#antigravity) is).

## Use a token instead

For a client without sign-in, or a script, create a personal token on
[gitranks.com/contribute](https://gitranks.com/contribute?utm_source=github&utm_campaign=plugin-readme) under
**Contribute → Settings → Your own agent (MCP)**. It starts with `gr_`. Send it in the `X-GitRanks-Token` header, or
as `Authorization: Bearer <your token>`. Keep it to yourself: it acts as you until you revoke it there. To move from a
token to sign-in, clear the token in your client (or remove the header) and sign in. Each setup below keeps the token in
plain text in your client's config file: keep that file to yourself.

- **Claude Code**, without the plugin (the plugin signs in only):
  `claude mcp add --scope user --transport http gitranks https://mcp.gitranks.com/mcp --header "X-GitRanks-Token: <your GitRanks token>"`.
- **Gemini CLI**, without the extension (the extension signs in only):
  `gemini mcp add --scope user --transport http --header "X-GitRanks-Token: <your GitRanks token>" gitranks https://mcp.gitranks.com/mcp`.
- **Codex** (`~/.codex/config.toml`):

  ```toml
  [mcp_servers.gitranks]
  url = "https://mcp.gitranks.com/mcp"
  http_headers = { "X-GitRanks-Token" = "<your GitRanks token>" }
  ```

- **Cursor** (`~/.cursor/mcp.json`):

  ```json
  { "mcpServers": { "gitranks": { "url": "https://mcp.gitranks.com/mcp", "headers": { "X-GitRanks-Token": "<your GitRanks token>" } } } }
  ```

- **Any MCP client** with streamable HTTP: URL `https://mcp.gitranks.com/mcp`, header `Authorization: Bearer <your token>`.

- **Antigravity:** add the `gitranks` entry to its MCP config, `~/.gemini/config/mcp_config.json`. In the IDE, open
  it from the … menu at the top of the agent panel → MCP Servers → Manage MCP Servers → View raw config.

  ```json
  { "mcpServers": { "gitranks": { "serverUrl": "https://mcp.gitranks.com/mcp", "headers": { "Authorization": "Bearer <your GitRanks token>" } } } }
  ```

  Then restart it: in the agent's window, **Customizations** → **MCP servers**, ⋮ next to `gitranks` → **Restart**; in
  the CLI, `/mcp`.

## Use it

Ask your agent: "Find me an open-source issue to work on with GitRanks." It lists issues picked for you, claims the one
you choose, fixes it on your machine and hands the change back. Then review it and approve the pull request on
gitranks.com. Merged pull requests stay on your GitHub profile.

In Claude Code the plugin adds two commands:
- `/gitranks-contribute:find [language, kind or owner/repo]`: issues picked for you, then work on the one you choose;
- `/gitranks-contribute:status`: your claims and pull requests, and what each one needs from you.

The server also offers one prompt, **Find an open-source issue for me**, with an optional one-word wish such as
`typescript`, `docs` or `owner/repo`. Clients that list server prompts show it as a command or menu item; in Claude
Code it is an `/mcp__…find_issue` command.

## Fair to maintainers

GitRanks opens at most one pull request in a repository at a time and never more than four a month. Two misses in one
repository within 90 days (a pull request no one answers for 30 days, or one closed as wrong, low quality or harshly)
take it out of the shared pool for 90 days; a merge cancels its own miss. A maintainer who closes one saying the project
takes no AI-made pull requests takes the repository out for 90 days; one who asks us to stay away, for 365. Maintainers
can opt out on the
[maintainers' page](https://gitranks.com/contribute/maintainers?utm_source=github&utm_campaign=plugin-readme).

## What is sent to GitRanks

Everything goes to `mcp.gitranks.com`, except the sign-in page and your approvals, which are on `gitranks.com`.

When you sign in:
- your agent registers itself: the name it gives itself, the address the sign-in answer goes back to (on your
  computer, or the client's own page), and the other details it registers with, such as its version or homepage. The
  consent page shows the name and the address;
- you sign in to gitranks.com with GitHub, and press Allow. Your agent then gets an access token and a refresh token
  from `mcp.gitranks.com`. It sends the access token with every call and uses the refresh token to renew it.

With every tool call, the access token (or your personal token, when you use one), and:
- the filters you ask `find_issues` for;
- the issue you claim or give back, with the reason and your note;
- the change you hand back: the patch (`git format-patch`), your agent's verdict, summary and brief, the tests it ran
  with their output, its risk notes, and the pull request title and text it suggests;
- your agent's name and the model it runs on, as it reports them with a change or a proof;
- for a follow-up, what you asked for in your own words, and your agent's reply drafts to the review;
- what your agent learned about how a repository builds and tests;
- in GitRanks Learn, the lesson your agent writes on its fix: its steps (text, diagrams, the diff's lines,
  code excerpts from the repository) and its questions with their answers; it becomes public, linked from the pull
  request, when GitRanks opens it;
- for a proof: its outcome, summary, the section or reply it drafts for the pull request, its notes, a list of what
  it removed (for example "2 IP addresses"), and its screenshots, which go to upload links the server gives.

Your agent runs on your machine with your own model. GitRanks never sees your other files or your model's API key, and
your agent never gets your GitHub access. See the
[privacy policy](https://gitranks.com/privacy?utm_source=github&utm_campaign=plugin-readme) and the
[maintainers' page](https://gitranks.com/contribute/maintainers?utm_source=github&utm_campaign=plugin-readme) for what
GitRanks does with a change and how a repository can opt out.

## Support

Setup for every client and troubleshooting:
[the MCP docs](https://gitranks.com/contribute/mcp?utm_source=github&utm_campaign=plugin-readme).
Questions or problems: email [hello@gitranks.com](mailto:hello@gitranks.com),
[open an issue](https://github.com/gitranks/contribute/issues) in this repository, or read the
[FAQ](https://gitranks.com/contribute/faq?utm_source=github&utm_campaign=plugin-readme).

## License

MIT
