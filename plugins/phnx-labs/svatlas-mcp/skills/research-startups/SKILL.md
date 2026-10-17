---
name: research-startups
description: Research AI startups, founders, and funding with the Silicon Valley Atlas directory. Use when someone asks who is building something, wants a market map of a sector, asks about a startup's funding, investors, or founders, or wants recent announcements from companies they track.
---

# Research startups and founders

Connect the hosted SV Atlas MCP server at `https://svatlas.io/mcp` and sign in
with your existing Atlas Google account before using these tools. Never ask
for a password or token in chat. If the server is unavailable or sign-in is
required, explain how to connect and stop; do not invent results. Tool names
may have a client-specific prefix; use the connected server's tool catalog.
Search and product matching use the account's monthly quota; other reads do
not.

For OpenClaw, configure the connection once with
`openclaw mcp set svatlas '{"url":"https://svatlas.io/mcp","transport":"streamable-http","auth":"oauth"}'`,
then `openclaw mcp login svatlas`. Installing this skill does not connect the
server. Ask before creating or changing outreach lists.

- **Who is building X:** `search_companies` with the problem, buyer, or
  technology in plain words. Use `program` to stay within one accelerator.
  For a full sector or a whole list, use `export_companies` and page through.
- **One company:** `get_company` with the slug. Report stage, team size,
  funding rounds with investors, founders, and signals, each with its source.
- **Founders:** `search_people` with keywords, program, vertical, location,
  or founding-year window.
- **What changed:** `company_updates` returns sourced product announcements
  for companies on the person's lists.
- **Missing details:** `enrich_company` or `enrich_founder` queues a refresh.
  Say it was queued; the result appears later, not in this answer.

Every fact in Atlas comes from a public page. Quote the source link when you
state a number or a date, and say plainly when Atlas has no data on
something instead of filling the gap. Link companies as
`https://svatlas.io/companies/<slug>`.
