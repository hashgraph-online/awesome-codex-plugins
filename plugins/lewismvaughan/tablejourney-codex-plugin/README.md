# TableJourney plugin for Codex

Food travel answers inside Codex, from [TableJourney](https://tablejourney.com)'s hosted MCP server:

- hand-checked restaurants, cafes, bakeries, markets and street food in 200+ cities, searchable by cuisine, dietary need, price tier, opening time or distance from a point;
- food festivals with the dates of their next edition;
- signature dishes and where to eat them, editorial day-by-day itineraries;
- bookable food tours, cooking classes, attraction tickets, stays and car hire.

Each venue page shows the source it was checked against, the date it was checked and its open status.

## What is in this repository

No code. Only:

- `.codex-plugin/plugin.json`: the plugin manifest;
- `.mcp.json`: one remote MCP server, `https://tablejourney.com/mcp` (streamable HTTP, read-only, no account, no API key);
- `skills/tablejourney-food-travel/SKILL.md`: tells Codex which of the 12 tools to call for which question, and how to cite and label links;
- `assets/icon.svg`: the TableJourney icon.

## Install

Add this repository as a plugin marketplace source in Codex, or install it from the [awesome-codex-plugins](https://github.com/hashgraph-online/awesome-codex-plugins) marketplace once it is listed. Any other MCP client can use the server directly; see the [TableJourney MCP docs](https://github.com/lewismvaughan/tablejourney-mcp) and https://tablejourney.com/agents/.

## Try

- "Which food festivals are on in Italy in the next two months?"
- "Find vegan places open now near the Pantheon in Rome."
- "What should I eat in Oaxaca, and where?"

## Tools

`search_places`, `place`, `plan_day`, `festivals`, `dishes`, `itineraries`, `cities`, `things_to_do`, `experiences`, `tickets`, `stays`, `car_hire`. All read-only and idempotent.

## Affiliate links and terms

The data and the server are free. Booking links (`book`, `booking`) are TableJourney affiliate links, which pay for the work; the skill asks Codex to pass them on unchanged and to say they are affiliate links. Terms: https://tablejourney.com/agents/#terms. Privacy: https://tablejourney.com/privacy/.

## Licence

MIT for the files in this repository. The data returned by the server is TableJourney's and is covered by the terms above.
