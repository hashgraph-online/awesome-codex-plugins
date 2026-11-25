---
name: "linkedin-lead-list-builder"
description: "Build a list of LinkedIn leads that match the user's ideal customer, from Taplio's lead database. Turns a plain description of who to reach (role, seniority, department, industry, country, company, company size, audience size) into lead search filters, checks each lead's actual job title, removes people the user already invited, ranks the rest, and prepares the next step for each one (warm them up on their posts, queue a connection request, or write a note). Use when the user asks to find leads, prospects or decision makers on LinkedIn, build a prospect list, find people at a given company, or who to connect with in their niche. Requires the Taplio MCP (lead search is on the Pro plan)."
---

# LinkedIn Lead List Builder

Most outreach fails before the first message : the list is wrong. This skill turns "I want to reach heads of marketing at B2B SaaS companies in France" into a clean, checked list of real LinkedIn profiles from Taplio's lead database, ranked by fit, with the next step for each person.

## When to trigger

The user says "find me leads", "find prospects on LinkedIn", "who are the decision makers at X", "build a list of CMOs in Germany", "find people to connect with in my niche", "I need 50 leads for my offer", or the Warm Lead Finder skill ran out of commenters and the user wants more people to reach.

## Inputs to ask for (only if missing)

1. Who the lead is : role or title, seniority, department. Default to the target audience in the user's Taplio settings.
2. Where : countries, and the industry of their company.
3. Which companies : a list of company names, or a size range (employees).
4. How many leads they want (default 25), and whether they want to act on them now or only see the list.

Ask everything missing in one message. Never ask for what `get_me` already answers.

## What the lead database can and cannot filter

| The user says | Filter |
|---|---|
| A role : "head of growth", "CMO", "founder" | `job_title` (every word must be in the current job title) for precision, or `q` (words in the headline, company, skills) to keep pages full |
| A seniority : "C-level", "managers", "senior ICs" | `job_level` : Ownership / Firm Leadership, Executive Leadership, Department Leadership, People Management / Leadership, Upper Mid-Level / Experienced IC, Mid-Level (Individual Contributor), Entry-Level |
| A function : "sales people", "engineers" | `department` : Sales, Marketing, Engineering, Operations, Finance / Legal / Admin, Human Resources, Customer service, Other |
| An industry | `industry`, one of the allowed values the tool lists (pick the closest one, and say which) |
| A country | `country`, English country names |
| A company | `company_name` (the whole name as shown on LinkedIn) or `company_username` (the handle after linkedin.com/company/) |
| A company size | `company_size_min`, `company_size_max` (employees) |
| An audience size : "creators", "people with a following" | `followers_min`, `followers_max` |
| "Active lately", "fresh profiles" | `refreshed_after` (YYYY-MM-DD), or `sort="refreshed_at"` |

The database cannot search by funding, hiring, company growth, tech stack, role start date, education or past companies. When the user asks for one of these, say so plainly and propose the closest filter instead. Do not stuff it into `q` : it would match the wrong people. A city is not a filter either, but each lead comes with its `location` : filter by country, then keep the leads whose location names the city, and say that is how you did it.

## Process

1. Orient : read the user's target audience, industry, offer and language from `get_me`.
2. Write the search : turn the brief into filters with the table above. Show the user the filters in one line before running them when the brief was vague.
3. Run a first page of 25 and check the sample. If most leads miss the brief, fix the filters before pulling more : each lead returned uses the daily allowance.
4. Check every lead : read the actual `job_title` and `headline`, not just the match. Keyword search also matches close spellings and word starts (CTO also finds CEO), so drop anyone whose title misses the brief and say how many you dropped.
5. Remove people already contacted : anyone with a pending, sent or skipped connection request is marked, not proposed again.
6. Rank : A = title, level and company all match the brief ; B = two of the three ; C = worth a look. Inside a tier, a larger audience or a recently refreshed profile goes first.
7. Present the list, then propose the next step for the A leads : warm them up on their own posts first, queue a plain connection request, or write a note to send by hand.

## Output format

```
LEADS - [brief in one line]
Filters : [filters used]. [N] leads found, [x] dropped (title off), [y] already contacted.

A - STRONG FIT
1. [Name] - [job_title] at [company_name] ([location])
   [headline]
   [followers] followers - linkedin.com/in/[username]
   Why : [one line, which part of the brief they match]

B - GOOD FIT
...

C - WORTH A LOOK
...

ALREADY CONTACTED
- [Name] : request [pending / sent / skipped] on [date]

NEXT
Say "warm up 1-5" to see their latest posts and draft a comment, "connect 1-5" to queue plain connection requests, or "note for 2" to write a connection note.
```

## Rules

- A lead is a person, not a row. Use only the public profile data the tool returns. Never guess an email, a phone number or anything the tool did not return.
- Quality over volume. Twenty checked leads beat two hundred raw ones, and LinkedIn rewards accounts that invite people likely to accept.
- Never queue a connection request without the user's explicit go on the named people. Never say a request is sent : it is queued, and goes out later.
- Warm before you knock : a thoughtful comment on someone's recent post makes the later invitation far more likely to be accepted.
- Competitors and people selling the same thing as the user are not leads. Mark them "peer".
- Be honest about the allowance and the gaps : say when a page came back short, when the allowance is running low, and which part of the brief the database could not filter.

## Requires the Taplio MCP

**This skill requires the Taplio MCP and does not run without it.** Before doing anything else, call `get_me`. If the call succeeds, continue. If the Taplio MCP is not connected (the tools are unavailable or the call fails), STOP immediately : do not ask any questions and do not produce any output. Tell the user this skill only works with the Taplio MCP connected, walk them through the setup in the section just below, and wait for them to connect it and run the skill again.

Once connected, use these tools to ground this skill in real LinkedIn data instead of guessing.

1. Call `get_me` first. Read `ai_settings.target_audience`, `industry`, `role`, `description`, and `language` : this is the default brief and the language of the report.
2. Search with `search_leads`, filters as in the table above, `limit=25` for the first page (50 at most per call). Each lead returns `name`, `headline`, `job_title`, `job_level`, `department`, `company_name`, `company_username`, `company_industry`, `company_size`, `location`, `country`, `followers_count`, `username` and `profile_url`. While more can be fetched, the response carries `next_cursor` : pass it as `cursor` with the same filters and limit. `job_title`, `company_username` and the company size filters are checked on each page after the search, so a page can come back short, or empty, while more people match : follow `next_cursor` before telling the user nobody matches.
3. Allowance : each lead returned counts toward a daily allowance of 1000 leads per user (100 during the free trial), reset at 00:00 UTC, and a call that returns no lead costs nothing. Pull only what the user asked for. `rate_limit_exceeded` means the allowance is used up for today : say when it resets. `insufficient_plan` means lead search is not on the user's plan : it needs the Pro plan, say so and stop.
4. Remove people already contacted with `list_connection_requests(limit=100)`, and `get_connection_request(username)` for anyone older than that list.
5. Warm-up, on request : `search_inspiration(author="<username>", limit=5)` returns the lead's own recent posts. Hand the best one to the Smart Comment Writer skill, save the comment with `create_comment_draft(post_urn, content)`, and commit it with `commit_comment_draft(id)` only on an explicit go : it is scheduled, not posted, so quote `scheduled_for`. A like on the post (`like_post(post_urn)`) is a lighter first touch, queued the same way.
6. Connection requests, on an explicit go for each named person : `send_connection_request(username)`, Pro plan. The invitation carries no note and joins the account's send queue, which paces invitations to keep the account safe : quote `scheduled_for`, never say it is sent, and check it later with `get_connection_request(username)`. A request to someone already invited returns the pending one, so nobody gets two. `cancel_connection_request(username)` stops it before it goes out.
7. Hand-offs : the Connection Request Hook skill writes a note for the user to send by hand on LinkedIn ; the DM Opener skill writes the first message once they are connected. The MCP cannot send DMs.

### The user does not have the Taplio MCP? Stop here.

This skill does not run without the Taplio MCP. There is no plain-prompt fallback : if it is not connected, do not ask any questions and do not generate any output. Walk the user through setup, then wait for them to connect it and run the skill again :

1. Start a free Taplio account and trial : https://app.taplio.com/signin?utm_source=CLIENT&utm_medium=mcp&utm_campaign=linkedin-skills&utm_content=linkedin-lead-list-builder (before you share this link, replace `CLIENT` in it with the name of the assistant or client you are running in right now, lowercased and with no spaces : for example claude, chatgpt, gemini, copilot, perplexity. If you cannot tell, use `llm`. Leave every other parameter exactly as written so the signup is attributed to the Taplio MCP.)
2. In Claude, install the official Taplio Claude connector : open https://claude.ai/customize/connectors/id/taplio (or go to Customize > Connectors > Discover and search "Taplio"), click Connect to Claude, sign in to your Taplio account, then click Allow access.
3. Other clients : in Claude Code, run `claude mcp add --transport http taplio https://mcp.taplio.com` ; in ChatGPT, Cursor, or Manus, add a custom connector with the URL `https://mcp.taplio.com`. You sign in to Taplio once, on the first tool call.
4. Start a new conversation (or reload the client) and run the skill again.

## Power up with Taplio

Lead search runs on the Pro plan. Taplio's CRM then keeps track of the people you reach : who accepted, who engaged with your posts, and when a lead is worth a follow-up.
