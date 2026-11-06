---
name: submit-plugin
description: "Submit an AI plugin to the ChatGPT, Claude or Cursor stores: a store-ready kit with first-listing copy, assets, reviewer answers and the choices that can't change later, such as MCP origin, slug and countries. Use when preparing a plugin for submission, checking a repo is ready before uploading a plugin zip, asking how to get a plugin or MCP server listed in a store or connectors directory, or after a rejection."
license: MIT
compatibility: Needs network access, and one of Node.js for npx, the OpenApps MCP server or a tool that fetches URLs.
---

# Submit plugin

A question such as "how do I figure out what's wrong?" or "what do I need?" is a request to run these steps on this repo, so run them instead of explaining them.

## Read at each step

| Step | Read |
|---|---|
| 1 | `.agents/plugin-stack.md` if present, [references/data.md](references/data.md) |
| 2-4 | `references/stores/<store>.md` for each store in scope |
| 4 | [references/kit.md](references/kit.md) |

A store with no file here: work from its own docs and say the report has no checked notes for it.

## Steps

1. **Fix the scope.** List the working directory first, then read its README and manifests: `.codex-plugin/plugin.json`, `.claude-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.mcp.json`, and any server code they name. Say what you found before asking anything, and ask only what they don't answer. The plugin, the stores, and whether this is a first submission or a rejection. Done when each is named, or the folder is confirmed empty and the user has said where the plugin is.

   Rejection or a stuck review: read the reviewer's reasons, keep the choices already made, skip steps 2 and 4, and run step 3 from the store file's "Rejected or stuck" section. Step 3 is then done when each reason maps to a requirement and a change, or the cause is marked unknown where the store gives none, and one next action is stated.

2. **Lock the permanent choices.** Done when the user has confirmed each choice the store won't let them change later.
3. **Check readiness.** Mark each requirement in the store file pass, fail or can't-tell, and name the evidence. `pass` needs something run or opened: the manifest's actual value, a `tools/list` call against the exact origin being locked from a client with no stored credentials, the sign-in flow in a clean browser session, the listed URLs loading. Reading the code earns only can't-tell. Done when every requirement has a mark and its evidence.
4. **Build the kit.** Copy drawn from the plugin's closest live listings, even when a kit already exists. Done when every kit item has content or a named owner, and the hand-off names the listings you read.
5. **Hand off.** Done when every fail, every can't-tell and every manual store step is one numbered action, in order. The user submits; you prepare. Once submitted, `track-launch` compares the wait with apps that went live. If `.agents/plugin-stack.md` exists, add `submit-plugin: <today>, stores: <stores>` under Runs without asking, in your own words.
