# Loomaly plugin

Your site's SEO problems, fixed by the coding agent you already use. Loomaly checks every page of your site and ranks what to fix first; Claude Code, Codex or Cursor gets each problem with a fix prompt for your framework, makes the change in your repo for you to review, and asks Loomaly to re-check the page once the fix is live. Loomaly never changes your site itself.

- MCP server: `https://loomaly.com/mcp` (the first time, your browser opens so you can sign in or create a free account)
- Skills: `fix-seo`, `site-health`, `internal-links`, `weekly-loop`
- Docs: https://loomaly.com/docs/mcp

## Claude Code

```bash
claude mcp add --transport http loomaly https://loomaly.com/mcp
```

Then run `/mcp` in Claude Code and sign in.

## Codex

```bash
codex mcp add loomaly --url https://loomaly.com/mcp
```

Codex opens your browser to sign in straight away; if you close it, run `codex mcp login loomaly`.

## Cursor

[Add to Cursor](https://cursor.com/en/install-mcp?name=loomaly&config=eyJ1cmwiOiJodHRwczovL2xvb21hbHkuY29tL21jcCJ9), or add this to `~/.cursor/mcp.json`:

```json
{ "mcpServers": { "loomaly": { "url": "https://loomaly.com/mcp" } } }
```

## Try it

From your site's repository:

> Use Loomaly to check example.com. Fix the 3 problems it ranks first in this repo, and open a PR for me to review.
