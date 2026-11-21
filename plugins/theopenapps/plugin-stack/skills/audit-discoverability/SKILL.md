---
name: audit-discoverability
description: "Audit whether agents would find and pick an AI plugin or MCP server when a user asks: how its listing and MCP tool descriptions answer target prompts, with a labelled simulated pick against rivals. Use when asked to audit a plugin or MCP server, when agents ignore a plugin, to check prompts people should use it for against rivals, for AEO for plugins, to grade a pasted tool list or tools against a rival's, to check whether an app can be reached in a country, or to fix MCP tool descriptions and annotations such as readOnlyHint. Not for writing store copy."
license: MIT
compatibility: Needs network access, and one of Node.js for npx, the OpenApps MCP server or a tool that fetches URLs.
---

# Audit discoverability

A question such as "how do I figure out what's wrong?" or "what do I need?" is a request to run these steps on this repo, so run them instead of explaining them.

## Read at each step

| Step | Read |
|---|---|
| 1 | `.agents/plugin-stack.md` if present, [references/data.md](references/data.md) |
| 1, 3 | [references/listing.md](references/listing.md) |
| 2, 4 | [references/tools.md](references/tools.md) |
| 5 | [references/simulated-pick.md](references/simulated-pick.md) |

## Steps

1. **Fix the scope.** The plugin, 5-10 target prompts and 3-5 competitors. Done when each is named and at least half the prompts aren't drafted, or the report says coverage is circular.
2. **Can it be reached at all?** Done when the listing, the server and the target country are each marked, with `checked_at` printed beside any stored status. A failed mark is fix #1, and every later step is labelled `conditional on fixing reachability`.
3. **Audit the listing's words.** Done when every target prompt is marked covered or missed, with the competitors that cover it.
4. **Audit the tools.** Read them from `mcp_toolset_get`, the repo's server code, or `tools/list` output the user pastes. Done when every tool has a verdict on saying what it does, when to use it, and its annotations. With none of the three, say so in the report and go to step 5.
5. **Run the simulated pick.** Done when each prompt has a pick, its reason and a run count, labelled as a simulation.
6. **Report.** Ranked fixes. Done when every fix names a target prompt it should help and every number has its date and basis. If `.agents/plugin-stack.md` exists, add `audit-discoverability: <today>, top fix: <fix>` under Runs without asking, in your own words.

## Report order

1. Any `Degraded:` lines, then `This simulation is not informative for this set` if a control failed.
2. `Baseline:` the `best` chart place from the plugin's `listings_search` row, with `meta.as_of`, so the next run has something to compare.
3. Fixes, ranked: reachability, tool text that risks store review, prompts the plugin won and should have lost, then missed prompts, sourced ones before drafted ones. A tool fix gives the replacement text. A listing fix names the missing words and the field, and leaves the copy to `optimize-listing`. With no listing yet, name `submit-plugin`.
4. Evidence: the coverage line, the tool verdicts, the picks with their label, the real-assistant line and what the simulation can't tell you.
