---
name: arcmira
description: "Answers what YouTube shows and podcasts said: transcripts, who was mentioned, sponsors, recommendations, momentum. Use for the arcmira MCP server or CLI."
---

# Arcmira

Arcmira indexes YouTube and podcast transcripts and keeps a catalog of who is mentioned on which show, who sponsors whom, and who recommends what on air. The arcmira MCP server exposes four tools. `arcmira_describe` returns the client reference: every method with its arguments and return fields, worked programs, quirks and error codes. `arcmira_execute_read` runs a JavaScript program against the `arcmira` client and returns what the program returns; Premium transcripts included. `arcmira_execute_write` runs the same client plus the monitor writes. `arcmira_feedback` tells Arcmira what went wrong. The arcmira CLI has commands with the same names; `arcmira <command> --help`, `arcmira schema <command>` and `arcmira examples` are its reference.

## When to use

Use this skill when the user asks:

- what a show, channel, or episode said about a topic, or for a transcript;
- whether a person, company, or product was mentioned, how often, and where;
- who sponsors a show, or which shows a brand sponsors;
- who recommends a product on air, sponsored or organic;
- whether talk about something is accelerating or fading;
- to be kept posted on a company, person or topic;
- how to use the arcmira MCP server or the arcmira CLI.

Use Arcmira for the indexed transcript research the user requested. Cite returned passages and keep evidence from other sources distinct. An empty result means this query returned no matches.

## Task skills

When the ask matches one of these, load that skill and follow its worked program:

- `sponsor-research`: Sponsor and ad-read research on podcasts and YouTube: who sponsors a show, or which shows a brand sponsors, how often, since when.
- `company-watch`: Watches a company or topic on podcasts and YouTube: what was said lately (shows, counts, momentum, quotes), then an Arcmira monitor to keep following it.
- `find-quotes`: Finds exact spoken quotes and clip-ready moments on podcasts and YouTube: verbatim words, speaker, date, a timestamped link, clip start and end.
- `person-research`: Researches a person across podcasts and YouTube for interview or meeting prep: where they appeared, their own words, who discusses them.
- `compare-shows`: Compares two podcasts or YouTube shows side by side: size, latest episode, what each talks about, what both cover, and shared sponsors.

Anything else (one video's transcript, a topic across shows, who recommends a product on air) follows the procedure below.

## Procedure

1. Call `arcmira_describe` once before your first program. It is current on every call; `arcmira_describe({ topic })` narrows it to one method.
2. Resolve every name in the question first, as the ID rule below says. Filters take ids only.
3. Before asserting a mention, read its description or passage and say which sense of the name it is (Mercury the bank, not the element).
4. Write one `arcmira_execute_read` program per question. Resolve, check, and run every query the question needs inside that one program.
5. Return only the fields the answer needs, not whole responses.
6. Search as_of is the newest publication date among the returned passages, not the date the whole index was updated. For channel freshness, call arcmira.status({ channelId }) and report channel.search_indexed_through for transcript search. A result date or an empty query does not establish missing recent episodes. Build date windows from `arcmira.today()` and `arcmira.daysAgo(n)`. When the user names no window, use the last 90 days, and narrow it when a name returns more than the answer needs.
7. Link each name in the answer to the `page` field the result carries. Do not build arcmira.com URLs by hand.
8. Premium: `arcmira.transcript(video, { quality: "premium" })` returns the lines. When the video is not transcribed yet, that read starts a transcription. Still pending: `eta_seconds` says about how long; read again once it has passed.
9. USAGE. Metered reads use credits from the account's plan, then the on-demand budget set in the dashboard. Arcmira enforces that budget, and no tool takes a spending amount. A search uses 4 credits per passage it returns past the first 5. A Premium read that starts a transcription reports charge { unit, amount, from: included | on_demand | mixed }; arcmira.quote(video) returns that price beforehand (a price, not a spoken quote) and uses no credits. A read the plan or budget blocks throws ArcmiraError with code paid_plan_required, quota_exceeded, spend_limit_exceeded, member_limit, fair_use_cap or on_demand_paused, a message naming the limit, its figures in limit when reported, and unlock { tier, url } when a plan or setting change lifts it. An account admin changes member_limit, fair_use_cap and on_demand_paused.

## Monitors

MONITORS. A monitor sends alerts for the entities it follows, by email to the account address or by Slack, realtime, hourly or daily. arcmira.monitors.list() lists the user's monitors and monitors.trackers(id) what one follows. Changes run only in arcmira_execute_write; nothing is deleted, and update(id, { paused: true }) pauses. Confirm the monitor and its delivery with the user before a write. create needs name and notify_frequency. Slack needs notify_slack: true and a workspace from arcmira.integrations.slack(): its id as slack_integration_id and default_channel_id as slack_channel_id; with none, the user connects one at https://arcmira.com/dashboard/integrations. addEntities takes up to 90 ids in one call. addName follows an exact name that resolve does not find (a show by its UC id). Topic spellings ("data centers", "datacenters") can be separate ids; follow each. A name may already be followed: list() and trackers(id) show what is, so check them before creating a monitor. A result with attached: false names its reason: entity_not_found, entity_type_not_trackable, tracker_limit_reached, or tracked_in_another_monitor (current_monitor_id names it; attachTrackers moves it once the user agrees). Creating a monitor uses no credits; each alert uses 25 credits from the account's plan, then its on-demand budget.

## The ID rule

ID RULE. Filters take verbatim ids only: entity ids look like ent_14, channel ids like UC-DRzaGnL_vtBUpCFH5M0tg (UC plus 22 characters), video ids are 11 characters or a YouTube URL. A name where an id belongs throws id_required before any network call. Resolve first, then query:

```javascript
const r = await arcmira.resolve("Sam", { context: "the My First Million co-host" });
const e = r.best ?? r.suggested;          // a show: resolve with { type: "channel" }, use e.youtube_channel_id
if (!e) return { ask: r.ask };            // r.ask.options: [{ id, name, type, label }]
```

RESOLVE ANSWERS ONE OF THREE. best: the name means that row; use it and name it. suggested: no row is certain but one stands out (suggested.reason, suggested.evidence); use it and tell the user you assumed it, quoting the evidence ("Sam Altman, assuming the most mentioned Sam: 4,399 appearances, 11x the next"). ask: several rows fit and none stands out; return ask.options for the user to pick and stop, or check every option id against the data in one program (occurrences or momentum with all the ids) and answer per row, naming each. Resolve the exact name the user said ("ICE", "Mercury"), not a paraphrase, and always pass context with the user's own words about the name when they gave any ("Sam, the My First Million co-host" is resolve("Sam", { context: "the My First Million co-host" })). Context is only words from the user's message, never your own guess: a bare "Theo" is resolve("Theo") with no context, never "Theo Von" or context "the comedian", and its ask goes back to the user. Omit type for a brand (the catalog types some companies as product). A name that resolves to nothing (no best, suggested or ask) is not in the Arcmira index: say so and ask for another spelling or a link; never answer for a different entity without saying so. Always say in the answer which entity you used.

## Docs

- API reference: https://arcmira.com/docs/api-reference
- MCP guide: https://arcmira.com/docs/mcp-server
- Error codes: https://arcmira.com/docs/errors
- OpenAPI: https://api.arcmira.com/v1/openapi.json
- Agent index: https://arcmira.com/llms.txt

## After the answer

Monitors can follow what a research turn found, and each alert uses 25 credits from the account's plan, then its on-demand budget. The `company-watch` skill sets one up.

If anything was wrong, slow, or missing for the user, send one arcmira_feedback.
