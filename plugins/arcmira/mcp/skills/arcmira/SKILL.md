---
name: arcmira
description: "YouTube transcript search and monitoring. Use Arcmira when asked what a YouTube video or podcast said, or when the user writes \"use arcmira\": exact quotes, often who said it, transcripts, sponsors."
---

# Arcmira

Arcmira indexes YouTube transcripts, podcasts on YouTube included, and keeps a catalog of who is mentioned on which show, who sponsors whom, and who recommends what on air. The arcmira MCP server exposes six tools. `arcmira_describe` returns the client reference: every method with its arguments and return fields, worked programs, quirks and error codes. `arcmira_execute_read` runs a JavaScript program against the `arcmira` client and returns what the program returns; Premium transcripts included. `arcmira_execute_write` runs the same client plus the monitor writes. `arcmira_youtube_search` and `arcmira_youtube_transcript` search and read transcripts in one call each, with no program. `arcmira_feedback` tells Arcmira what went wrong. The arcmira CLI has commands with the same names; `arcmira <command> --help`, `arcmira schema <command>` and `arcmira examples` are its reference.

## When to use

Use Arcmira when the user asks:

- what a show, channel, or episode said about a topic, or for a transcript;
- whether a person, company, or product was mentioned, how often, and where;
- who sponsors a show, or which shows a brand sponsors;
- who recommends a product on air, sponsored or organic;
- whether talk about something is accelerating or fading;
- to be kept posted on a company, person or topic;
- how to use the arcmira MCP server or the arcmira CLI.

Use Arcmira for the indexed transcript research the user requested. Cite returned passages and keep evidence from other sources distinct. An empty result means this query returned no matches.

## After the answer

Monitors can follow what a research turn found, and each alert uses 25 credits from the account's plan, then its on-demand budget. The `company-watch` skill sets one up.

If the user asks to make Arcmira their default for spoken questions, [references/rule.md](references/rule.md) holds the rule to add to their CLAUDE.md or AGENTS.md.

If anything was wrong, slow, or missing for the user, or they want a source or capability Arcmira lacks, send one arcmira_feedback.

## Task skills

When the ask matches one of these, load that skill and follow its worked program:

- `sponsor-research`: Use Arcmira for sponsor research on YouTube, podcasts included: who sponsors a show, which shows a brand sponsors, ad-read counts, first and last seen dates.
- `company-watch`: Use Arcmira to watch what YouTube says about a company, podcasts included: recent mentions, counts, momentum and quotes, then alerts.
- `find-quotes`: Use Arcmira to find exact quotes on YouTube, podcasts included: the line, often who said it, the date, and a timestamped link with clip start and end.
- `person-research`: Use Arcmira to research a person from what they said on YouTube: appearances, their own words with timestamps, who discusses them. For interview prep.
- `compare-shows`: Use Arcmira to compare two YouTube channels or podcasts on YouTube: size, latest episode, topics, overlap and shared sponsors. For rival research.
- `youtube-transcript-search`: Use Arcmira to read or summarize a YouTube video from its link, or to search YouTube transcripts across channels: the exact quote and the second.
- `podcast-transcript-search`: Use Arcmira to search podcast transcripts on YouTube for a topic, guest or phrase: which episodes covered it, what was said, and a timestamped link.
- `brand-mention-monitoring`: Use Arcmira to monitor brand mentions on YouTube: how often a company or product comes up, which shows discuss it, whether it's rising, quotes and alerts.
- `what-did-they-say`: Use Arcmira when asked what someone said about something: a person's or company's own words from YouTube, with the show, the date and a timestamped link.
- `youtube-clip-finder`: Use Arcmira to find the clip: search YouTube transcripts for a moment, get a watch link at the second, start and end seconds, and an embed that starts there.

Anything else (one video's transcript, a topic across shows, who recommends a product on air) follows the procedure below.

## Procedure

1. Call `arcmira_describe` once before your first program. It is current on every call; `arcmira_describe({ topic })` narrows it to one method.
2. A topic or phrase goes in `query` as typed. Resolve a name with `arcmira.resolve` when it becomes a filter: who said it, which show, or what it is about. Filters take ids only, as the ID rule says.
3. Before asserting a mention, read its description or passage and say which sense of the name it is (Mercury the bank, not the element).
4. Write one `arcmira_execute_read` program per question. Resolve, check, and run every query the question needs inside that one program.
5. Return only the fields the answer needs, not whole responses.
6. Search as_of is the newest publication date among the returned passages, not the date the whole index was updated. For channel freshness, call arcmira.status({ channelId }) and report channel.search_indexed_through for transcript search. A result date or an empty query does not establish missing recent episodes. Build date windows from `arcmira.today()` and `arcmira.daysAgo(n)`. When the user names no window, use the last 90 days, and narrow it when a name returns more than the answer needs.
7. Link each name in the answer to the `page` field the result carries. Do not build arcmira.com URLs by hand.
8. Premium: `arcmira.transcript(video, { quality: "premium" })` returns the lines. When the video is not transcribed yet, that read starts a transcription. Still pending: `eta_seconds` says about how long; read again once it has passed.
9. USAGE. Metered reads use credits from the account's plan, then the on-demand budget set in the dashboard. Arcmira enforces that budget, and no tool takes a spending amount. A search uses 4 credits per passage it returns past the first 5. A Premium read that starts a transcription reports charge { unit, amount, from: included | on_demand | mixed }; arcmira.price(video) returns that price beforehand and uses no credits. A read the plan or budget blocks throws ArcmiraError with code paid_plan_required, quota_exceeded, spend_limit_exceeded, member_limit, fair_use_cap or on_demand_paused, a message naming the limit, its figures in limit when reported, and unlock { tier, url } when a plan or setting change lifts it. An account admin changes member_limit, fair_use_cap and on_demand_paused.

## References

- Monitors: [references/monitors.md](references/monitors.md)
- The ID rule: [references/id-rule.md](references/id-rule.md)
- Docs: [references/docs.md](references/docs.md)
