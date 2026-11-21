---
name: find-opening
description: "Find an opening before building an AI plugin: which ChatGPT, Claude or Cursor categories and tags are growing, which are crowded, how locked the top apps are, where one store is thin next to another, and a short ranked list of openings with dated evidence. Use when deciding what to build, asking which category is underserved or saturated, whether an idea's space is crowded, or where there's a gap in the ChatGPT app store or the Claude directory. Not for tracking named rivals or for a plugin that's already live."
license: MIT
compatibility: Needs network access, and one of Node.js for npx, the OpenApps MCP server or a tool that fetches URLs.
---

# Find opening

A question such as "what should we build?" or "is this space crowded?" is a request to run these steps, so run them instead of explaining them.

## Read at each step

| Step | Read |
|---|---|
| 1 | `.agents/plugin-stack.md` if present, [references/data.md](references/data.md) |
| 2-4 | [references/signals.md](references/signals.md) |

## Steps

1. **Fix the scope.** The store or stores, the space, and what the user can build. Take them from the file when it's there, else from the request; ask only what neither answers. The space is one idea ("a flight-deal app"), one category or tag, or a whole store. A store with no word from the user means ChatGPT and Claude. On Claude, connectors and plugins are separate markets, so name which. Done when the stores and the space are named.
2. **List the candidates.** From the tag tree, 6 to 16 tags or categories: for an idea, the tag it would carry, its siblings and its children; for a whole store, the top-level use-case tags, and on ChatGPT the store's categories too. Done when each candidate has an id and its listing count per store in scope.
3. **Pull the signals.** For each candidate: supply, launch share now against four weeks before, how locked its top is, the gap against another store, and on ChatGPT the countries. Done when every candidate has each signal or a stated gap.
4. **Rank.** Openings first, each with the three numbers that put it there, then the crowded ones and why. Done when every candidate has a verdict, opening, crowded or unclear, and every number has a date and a basis.
5. **Report.** The candidate table, then up to five openings ranked, then the crowded ones, then the section 'What this can't tell you', then any `Degraded:` lines. Close on one next step: `submit-plugin` to pick the category at submission, or `watch-competitors` on the top apps of the chosen opening. If `.agents/plugin-stack.md` exists, add `find-opening: <today>, top opening: <opening>` under Runs without asking, in your own words. Done when the report says plainly that it measures listings, not demand.
