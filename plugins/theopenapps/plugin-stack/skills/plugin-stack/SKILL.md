---
name: plugin-stack
description: "Plan the next move for an AI plugin you build: a ChatGPT app, Claude plugin or connector, Cursor plugin or MCP server. Use when asked what to do next to ship or grow one, where to start after installing these skills, for a full review across a plugin's listing, tools and widgets, or to set up `.agents/plugin-stack.md`."
license: MIT
compatibility: Needs network access, and one of Node.js for npx, the OpenApps MCP server or a tool that fetches URLs.
---

# plugin-stack

## Steps

1. **Read `.agents/plugin-stack.md`.** Missing: do step 2, then step 3. Present: go to step 3.
2. **Set up.** Follow [references/setup.md](references/setup.md), using [references/data.md](references/data.md) and [references/context-template.md](references/context-template.md). Done when the user has approved the file, it is written, and they have seen one finding about their plugin.
3. **Suggest.** Look up each listing in the file per references/data.md, then follow [references/menu.md](references/menu.md). Done when the user has two or three next steps, each citing the state that earned it. Stop there; the user picks.
