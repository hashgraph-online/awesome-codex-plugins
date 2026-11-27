# Taplio for LinkedIn (Claude plugin)

A Claude plugin with **27 Claude Skills for LinkedIn**. Install it once and Claude can write, plan, find leads, engage, and grow your LinkedIn presence, working on your real voice, audience, and analytics through your Taplio account.

Taplio is an independent product. It is not affiliated with, endorsed by, or sponsored by LinkedIn. LinkedIn is a registered trademark of LinkedIn Corporation.

## What's inside

**27 skills** across six areas:

- **Content creation**: post writer, hook generator, carousel builder, repurposer, story extractor, CTA optimizer
- **Research and inspiration**: niche creator finder, viral post analyzer, trending topics scanner, swipe file builder
- **Strategy**: niche definer, content pillars builder, audience persona builder, content calendar planner
- **Analytics and profile**: post performance critic, analytics interpreter, profile optimizer
- **Engagement**: comment opportunity finder, smart comment writer, comment reply manager, warm lead finder, engagement watchlist builder, daily engagement routine, engagement tracker
- **Networking**: lead list builder (searches Taplio's lead database for prospects that match your ideal customer), connection request hook, DM opener

The plugin contains markdown skills and one remote MCP server declaration, the Taplio connector (`https://mcp.taplio.com/`). No scripts, no hooks, nothing that runs on your machine.

## Runs on the Taplio connector

Every skill runs on the **Taplio connector for Claude** (the Taplio MCP server, `https://mcp.taplio.com/`), the same server that is listed in the Claude directory. The plugin declares it with that exact URL, so if you already connected the Taplio connector you keep one set of Taplio tools, not two.

- **Claude on the web, desktop, or mobile, and Cowork**: if the connector is not connected yet, connect it from [claude.ai/customize/connectors/id/taplio](https://claude.ai/customize/connectors/id/taplio) (or Customize > Connectors > Discover, search "Taplio", Connect to Claude, sign in, Allow access).
- **Claude Code**: the plugin brings the server. Sign in to Taplio in the browser on the first tool call. If you previously added it by hand with `claude mcp add`, remove that entry (`claude mcp remove taplio`) to avoid seeing the tools twice.

You sign in with your Taplio account; you can create one on the sign-in page.

Each skill calls `get_me` first. If the connector is not connected, the skill stops and walks you through the setup above: there is no plain-prompt fallback.

## What the skills do with the connector

Through the connector, the skills read your Taplio profile settings, your posts, drafts, and analytics, inspiration posts from other creators, leads from Taplio's lead database (Pro plan), and the comment threads worth engaging with. They can save drafts, schedule posts, draft and schedule comments and replies under your name, like posts and comments, and queue plain connection requests. All of it goes through your own Taplio account; the skills send nothing to any other service.

Nothing reaches LinkedIn without your say-so. Publishing a post, committing a comment or reply, liking, and sending a connection request are always gated behind your explicit confirmation, and the skills quote the scheduled time instead of saying something is live until the connector confirms it.

## Use

Skills are invoked as `/taplio:<skill-name>`, for example `/taplio:linkedin-post-writer`, or simply by asking ("write a LinkedIn post about...", "who in my comments is worth talking to?").

To install it in Claude Code from this repository (it is also a plugin marketplace, `.claude-plugin/marketplace.json`):

```bash
/plugin marketplace add TaplioOfficial/taplio-linkedin-plugin
/plugin install taplio@taplio
```

To try a local copy:

```bash
claude --plugin-dir ./taplio-linkedin-plugin
```

## Cursor

The same repository is also a Cursor plugin (`.cursor-plugin/plugin.json`). In Cursor, the plugin brings the 27 skills **and** the Taplio MCP server (`https://mcp.taplio.com/`), so there is nothing to connect separately: install it, then sign in to Taplio in the browser on the first tool call.

To try it locally, copy this folder to `~/.cursor/plugins/local/taplio` and restart Cursor. If you already added a `taplio` server in `~/.cursor/mcp.json`, remove it to avoid seeing the tools twice.

## Grok Build

The repository is also a Grok Build plugin (`.grok-plugin/plugin.json`), for the [xAI plugin marketplace](https://github.com/xai-org/plugin-marketplace). It brings the 27 skills, and one more command adds the Taplio MCP server (`https://mcp.taplio.com/`).

Install it straight from this repository, then add the Taplio MCP server:

```bash
grok plugin install TaplioOfficial/taplio-linkedin-plugin --trust
grok mcp add taplio https://mcp.taplio.com/
```

Then open `/mcps` in Grok, select `taplio` and press `i` to sign in to Taplio in the browser.

## GitHub Copilot

The repository is also an [Agent Plugins v1.0.0](https://agent-plugins.org) plugin (root `plugin.json`, skills in `skills/`, MCP server in `mcp.json`), which GitHub Copilot CLI and VS Code load natively. As in Cursor, it brings the 27 skills **and** the Taplio MCP server (`https://mcp.taplio.com/`); sign in to Taplio in the browser on the first tool call.

```bash
copilot plugin install TaplioOfficial/taplio-linkedin-plugin
```

The [`copilot/`](copilot) folder holds a separate Copilot package for the Awesome Copilot marketplace: 10 of the skills, the same MCP server, and no setup steps meant for other clients. When Taplio is not connected, its skills work from what you paste instead of stopping. It is generated by `node scripts/build-copilot.mjs` from `skills/` and `copilot-src/`: edit those, then rebuild, never the folder itself.

## Gemini CLI

The repository is also a Gemini CLI extension (`gemini-extension.json`). It brings the 27 skills and the Taplio MCP server; Gemini CLI discovers the OAuth sign-in on the first tool call.

```bash
gemini extensions install https://github.com/TaplioOfficial/taplio-linkedin-plugin
```

## Kiro

[![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](https://kiro.dev/launch/mcp/add?name=taplio&config=%7B%22url%22%3A%22https%3A%2F%2Fmcp.taplio.com%2F%22%2C%22oauthScopes%22%3A%5B%22taplio%3Amcp%22%5D%7D)

The button adds the Taplio MCP server (`https://mcp.taplio.com/`) to Kiro, with the `taplio:mcp` OAuth scope; Kiro opens the Taplio sign-in in the browser when it connects. It adds the MCP server only, not the skills.

## ChatGPT (Business, Enterprise and Edu workspaces)

Until Taplio is in the public ChatGPT plugin directory, a workspace admin or owner can add it on ChatGPT web:

1. **The Taplio MCP server:** in Plugins, select **+**, then **Add custom MCP server**. Enter `https://mcp.taplio.com/` as the endpoint and OAuth as the authentication, accept the risk warning, select **Create as a plugin**, and sign in to Taplio when prompted. Then publish it for the workspace (Admin Console > Plugins).
2. **The 27 skills (optional):** in Admin Console > Plugins, select **Add** > **Import marketplace** and enter `https://github.com/TaplioOfficial/taplio-linkedin-plugin`. ChatGPT reads `.claude-plugin/marketplace.json` and syncs the skills daily.

Each member then signs in to their own Taplio account on the first tool call.

## Other agents (skills only)

To add the 27 skills to any agent supported by [skills.sh](https://skills.sh), then connect the Taplio MCP server (`https://mcp.taplio.com/`) in that agent:

```bash
npx skills add TaplioOfficial/taplio-linkedin-plugin
```

## Links

- Skills source: https://github.com/TaplioOfficial/taplio-linkedin-claude-skills
- MCP server: https://github.com/TaplioOfficial/taplio-linkedin-mcp
- Product page: https://taplio.com/claude-skills-for-linkedin
- Support: https://intercom.help/taplio
- Privacy policy: https://taplio.com/our-privacy-policy
- Terms of service: https://taplio.com/terms-of-service
- Security: see [SECURITY.md](SECURITY.md)

## License

MIT
