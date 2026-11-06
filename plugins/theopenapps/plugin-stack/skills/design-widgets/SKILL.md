---
name: design-widgets
description: "Design an AI plugin's widgets from real ones in the stores. Pull: fetch a listing's rendered widgets. Audit: critique your widget against them. Redesign: propose a new version backed by precedent. Use for ChatGPT app widgets, MCP Apps UI, or inline cards."
license: MIT
compatibility: Needs network access, and one of Node.js for npx, the OpenApps MCP server or a tool that fetches URLs.
---

# Design widgets

Read [references/data.md](references/data.md) and, if present, `.agents/plugin-stack.md`.

| The user wants | Operations | Read |
|---|---|---|
| To see how others do it | Pull | [references/pull.md](references/pull.md) |
| Feedback on a widget | Pull, then Audit | pull.md, [references/audit.md](references/audit.md) |
| A better version | Pull, then Redesign | pull.md, [references/redesign.md](references/redesign.md) |

Mark each design claim by its source: precedent (widgets from two or more apps), example (one app, however many widgets) or opinion (no widget). Each precedent cites the listing, the tool and its `since`, and says whether it's from the user's category.

Done when every design claim is marked precedent, example or opinion, and every widget cited links its listing.

If `.agents/plugin-stack.md` exists, add `design-widgets: <today>, operation: <operation>` under Runs without asking, in your own words.
