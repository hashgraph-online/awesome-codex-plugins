# Val Town

Build and deploy on [Val Town](https://val.town) — serverless TypeScript that runs on Deno.

This plugin bundles:

- The hosted **Val Town MCP server** (`https://api.val.town/v3/mcp`) — create, edit, run, and deploy vals; manage SQLite, blobs, and environment variables. On first use, Codex runs the OAuth flow in your browser.
- **Platform skills** — short guides Codex loads on demand: HTTP vals, cron/intervals, SQLite, email, OAuth, React UI, third-party integrations, and templates.

Source of truth: <https://github.com/val-town/plugins>

## Install

```
codex plugin marketplace add val-town/plugins
codex /plugins
```
