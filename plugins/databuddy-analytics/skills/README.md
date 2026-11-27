# Databuddy for AI agents

[Databuddy](https://www.databuddy.cc) is cookieless web and product analytics. This plugin connects your coding agent or assistant to it, so you can ask about your site in plain words and find out why a number changed.

It contains:

- **The Databuddy MCP server** (`https://api.databuddy.cc/v1/mcp`). Ask about traffic, top pages, referrers, campaigns, visits from AI assistants, goals, funnels, revenue, errors, Core Web Vitals and session replays. Read investigations that show the evidence for what changed. Manage goals, funnels, annotations, feature flags and short links, with a preview before every change.
- **The `databuddy-mcp` skill**, which teaches the agent how to query the server well.
- **The `databuddy` skill**, which helps the agent add Databuddy tracking, custom events and feature flags to your app.

You sign in with your Databuddy account the first time the agent needs your data. You choose the organization, websites and permissions; changes stay off until you allow them.

## Try asking

- Why did signups drop last week? Check the funnel, errors and replays.
- Which pages do visitors from ChatGPT and other AI assistants land on?
- What were my top pages and traffic sources last month, compared with the month before?
- Which step of the signup funnel loses the most people, and which referrers convert best?
- Did any errors or slow pages start after yesterday's release?

## Install

### Claude Code

```bash
/plugin install databuddy --marketplace databuddy-analytics/skills
```

Or, step by step:

```bash
claude plugin marketplace add databuddy-analytics/skills
claude plugin install databuddy@databuddy
```

### Codex

```bash
codex plugin marketplace add databuddy-analytics/skills
```

Then open `/plugins` in Codex and install **Databuddy**.

### Cursor

[Add the Databuddy MCP server to Cursor](https://cursor.com/en/install-mcp?name=databuddy&config=eyJ1cmwiOiJodHRwczovL2FwaS5kYXRhYnVkZHkuY2MvdjEvbWNwIn0%3D), or install this repository as a plugin.

### Gemini CLI

```bash
gemini extensions install https://github.com/databuddy-analytics/skills
```

### Skills only (any agent)

```bash
npx skills add databuddy-analytics/skills
```

### Any other MCP client

Add a Streamable HTTP server with the URL `https://api.databuddy.cc/v1/mcp`. Clients that can't sign in can send a Databuddy API key in the `x-api-key` header instead. See the [MCP docs](https://www.databuddy.cc/docs/api/mcp) for every client.

## Links

- [MCP server docs](https://www.databuddy.cc/docs/api/mcp)
- [Databuddy docs](https://www.databuddy.cc/docs)
- [Privacy policy](https://www.databuddy.cc/privacy)
- Support: support@databuddy.cc
