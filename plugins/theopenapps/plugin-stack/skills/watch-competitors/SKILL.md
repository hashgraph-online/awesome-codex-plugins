---
name: watch-competitors
description: "Watch an AI plugin's competitors over time: ranks, installs, featuring, listing rewrites, MCP tool changes and the countries that list them, side by side, and what changed since last time. Use when naming rivals in the ChatGPT, Claude or Cursor stores, comparing who's gaining in a category, or for a weekly check or monitor. Not for a one-off chart lookup."
license: MIT
compatibility: Needs network access, and one of Node.js for npx, the OpenApps MCP server or a tool that fetches URLs.
---

# Watch competitors

## Read at each step

| Step | Read |
|---|---|
| 1 | `.agents/plugin-stack.md` if present, [references/data.md](references/data.md) |
| 2 | [references/pull.md](references/pull.md) |

## Steps

1. **Fix the set.** Up to 10 refs, including the user's plugin.
   - Start from the file's listing and competitor refs when it's there.
   - Search matches words one at a time, so check each hit's name against the name asked for before taking it.
   - A plugin on two stores is two refs; its other stores are in `linked`. A plugin with no listing stays out, and the report covers its competitors.
   - With no names, propose a set for the user to confirm. For a category, take the top of `charts_get store=<store> chart=<chart> limit=20`; `stores_get` lists the charts. For a plugin, run `listings_search` on 1-3 nouns from what it does, then `tags_get tag=<job tag from a good hit> store=<store> limit=20`.
   - Done when each name maps to one ref.
2. **Pull.** Done when each ref has ranks, metrics, featuring, changes and tools, or a stated gap for each.
3. **Report.** One row per plugin, then who is gaining inside this set, judged by whether their order relative to each other changed, not raw position; beside each move list any dated change in the same window, worded as timing, not cause. Then what each changed, or "nothing changed" plainly when that's the result. With the user's plugin in the set, close on one or two next steps tied to a listed change, naming `optimize-listing` for copy or `audit-discoverability` for tools. Done when every claim has a date and a basis. If `.agents/plugin-stack.md` exists, add `watch-competitors: <today>, top move: <move>` under Runs without asking, in your own words.
