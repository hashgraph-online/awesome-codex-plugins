# host0 skills

[![skills.sh](https://skills.sh/b/host0-ai/skills)](https://skills.sh/host0-ai/skills)

**host0 hosts whatever your agent creates** — HTML pages, sites, apps with a shared database, Markdown, PDFs — at a link you can share. This repo holds the host0 skill: it teaches any coding agent to publish a file or folder to a live `https://<slug>.host0.app` URL in one step.

## Install

```bash
npx skills add host0-ai/skills
```

Works with Claude Code, Cursor, Codex, Antigravity CLI, Gemini CLI, GitHub Copilot, Windsurf, Cline and every other agent the [skills CLI](https://github.com/vercel-labs/skills) supports. Google moved Google AI Pro, Ultra and free users from Gemini CLI to Antigravity CLI on June 18, 2026; Gemini Code Assist Standard and Enterprise licenses and paid API keys keep Gemini CLI. Add `-g` to install it for all your projects. `npx skills add https://host0.ai` installs the same skill straight from host0.

No Node? One curl command installs the same files into your agent's skills folder. It uses no sudo and never overwrites a copy you changed without `--force`:

```bash
curl -fsSL https://host0.ai/install.sh | bash
```

### As a plugin: the skill and the MCP server in one install

The skill publishes; the [MCP server](https://host0.ai/docs#quickstart) manages what's live (sharing, versions, analytics, shared data). The plugin brings both.

Claude Code:

```bash
/plugin install host0 --marketplace host0-ai/skills
```

Codex:

```bash
codex plugin marketplace add host0-ai/skills
```

Then install host0 from the plugin directory.

Gemini CLI:

```bash
gemini extensions install https://github.com/host0-ai/skills
```

Cursor supports the same `plugin.json` and `mcp.json`, but host0 isn't in its marketplace yet. Copy this repository to `~/.cursor/plugins/local/host0` and reload Cursor, or install the skill and the MCP server separately. We haven't run the plugin in Cursor.

### Just the MCP server

Connect any MCP client to `https://mcp.host0.ai/mcp`. It's a hosted remote server (Streamable HTTP) with OAuth sign-in, so there's nothing to install or run. It manages apps you've already published and doesn't deploy: use the skill to publish.

## Use it

Ask your agent:

- "Deploy this to host0"
- "Give me a link to this PDF"
- "Build a team todo list with a shared database and publish it"
- "Roll back the last deploy"

The first publish starts a device login: the agent shows a link and a short code, you approve it on host0.ai in your own browser, and the agent gets an API key. Nothing personal is typed into the chat.

## What you get

- **Private by default.** Only you and people you invite by email can open an app. Open it to anyone with the link, or make it public on the web, when you want to.
- **A shared database with no server code.** Declare record collections in an `h0.json` and the app's frontend reads and writes them on its own origin.
- **Versions and one-click restore**, cookieless analytics, and a readable URL whenever you rename it.
- **Any file or folder**: a static site, a single HTML page, a PDF, images, video, Markdown.

There is a free plan. Docs: [host0.ai/docs](https://host0.ai/docs).

## Skills

| Skill | What it does |
|---|---|
| [`host0`](skills/host0/SKILL.md) | Publish files, folders and apps with shared data to `*.host0.app`; manage visibility, sharing, versions and URLs over the host0 API. |

## Source

This repo is a mirror. The skill is developed alongside the host0 platform and synced here on every change, so the copy at [host0.ai/skill.md](https://host0.ai/skill.md) and this one are always the same. Report issues at [support@host0.ai](mailto:support@host0.ai) or open an issue here.

## License

MIT
