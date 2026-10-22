# Clera MCP

<!-- mcp-name: com.getclera/clera -->

Hire with agents, straight from your chat.

Clera MCP puts Clera's talent network inside Claude, ChatGPT, Cursor, Codex, Grok and any MCP client. Describe the role the way you would brief a recruiter. Your assistant searches 210,000+ vetted candidates who have opted in to hearing about roles, reviews the people Clera already picked for you, and requests intros. Clera does the outreach and replies land back in the same thread.

- **Server URL:** `https://mcp.getclera.com`
- **Transport:** Streamable HTTP
- **Auth:** OAuth 2.1 with dynamic client registration. Sign in with your Clera company account.
- **Pricing:** Free during the beta. Companies pay a success fee on hire. Always free for candidates.
- **Docs:** https://www.getclera.com/mcp/docs
- **Early access:** https://www.getclera.com/mcp#waitlist

## Install

**Claude (web and desktop):** [Add to Claude](https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=Clera&connectorUrl=https%3A%2F%2Fmcp.getclera.com), or Settings > Connectors > Add custom connector and paste `https://mcp.getclera.com`.

**ChatGPT:** Settings > Plugins > Advanced settings > turn on Developer mode, then add `https://mcp.getclera.com`.

**Claude Code:**

```bash
claude mcp add --transport http clera https://mcp.getclera.com
```

Or install the plugin (MCP plus the Clera hiring skill):

```bash
/plugin marketplace add getclera/mcp
/plugin install clera@clera
```

**Codex:**

```bash
codex mcp add clera --url https://mcp.getclera.com
codex mcp login clera
```

**Cursor:** add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "clera": { "url": "https://mcp.getclera.com" }
  }
}
```

**Grok:** Connectors > New Connector > Custom, paste `https://mcp.getclera.com`.

**Any MCP client:** add a remote MCP server with URL `https://mcp.getclera.com`. Clients without native OAuth can use `npx mcp-remote https://mcp.getclera.com`.

## What you can ask

| You say | Tools |
| --- | --- |
| Find senior backend engineers in Berlin with Go and Postgres experience. | `searchCandidates` |
| Show me the candidates Clera pre-selected for our Head of Product role. | `listRecommendedCandidates` |
| Pull up the full profile for this candidate and tell me if they're a fit. | `getCandidateProfile` |
| Help me write a job description for a Staff Frontend Engineer, remote in DACH. | `editJob` |
| Intro me to the top 3 candidates for the backend role. | `searchCandidates`, `requestIntro` |
| Who on my team has access? Add our new hiring manager. | `listTeamMembers`, `editCompanyContact` |

Read tools run right away. Anything that writes (intros, passes, role edits) asks you first in Claude and ChatGPT. Candidate profiles stay anonymized until Clera has introduced the person to your company.

## Privacy

Clera sees only the arguments of the tools your assistant calls, never the rest of your conversation. Privacy policy: https://www.getclera.com/privacy. Terms: https://www.getclera.com/terms.

## Support

hello@getclera.com, or ask your assistant to use the `sendFeedback` tool.

## This repo

Config and listing metadata for the hosted Clera MCP server: `server.json` (Official MCP Registry), `.cursor-plugin/` (Cursor Marketplace), `.claude-plugin/` (Claude Code plugin marketplace), `skills/clera/SKILL.md` (agent skill). The server itself is hosted by Clera.
