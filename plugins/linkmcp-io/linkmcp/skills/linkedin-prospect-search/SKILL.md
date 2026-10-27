---
name: linkedin-prospect-search
description: "Find new prospects with LinkedIn or Sales Navigator search, research the best matches, and send connection requests that the user approves one by one, with the LinkMCP connector. Use when the user describes an ideal customer (job title, seniority, industry, region) and asks to find people on LinkedIn, build a lead list from LinkedIn search, or connect with prospects. Needs a paid LinkMCP plan with the user's own LinkedIn account connected. Sends a connection request only after the user approves the exact note for that person, and stops at the LinkMCP limits."
license: MIT
compatibility: "Needs the LinkMCP connector (remote MCP server https://app.linkmcp.io/api/mcp) in the AI app and a paid LinkMCP plan with the user's LinkedIn account connected. Sales Navigator search needs a Sales Navigator subscription on that LinkedIn account."
metadata:
  author: LinkMCP
  version: "1.0.0"
---

# LinkedIn prospect search

Find the people who match the user's ideal customer, show why each one fits, and send connection requests only with notes that the user approved. Quality comes before volume: a short list of good matches with a real reason to connect.

## Setup: connect LinkMCP first

1. Check that the LinkMCP tools are available, for example `linkedin_search_people`. If they are, go to step 1 of "Steps".
2. If they are not available, stop. Tell the user how to connect LinkMCP:
   - No LinkMCP account yet: sign up at https://linkmcp.io/?utm_source=skills&utm_medium=skill&utm_campaign=linkedin-prospect-search. This skill needs a paid plan with your LinkedIn account connected.
   - Add LinkMCP to the AI app as a remote MCP server (in Claude: a custom connector) with this URL, then sign in: `https://app.linkmcp.io/api/mcp?ref=skill-prospect-search`
   - Steps for each AI app: https://app.linkmcp.io/docs/quick-start
   - If the LinkMCP plugin is installed: connect the LinkMCP connector of the plugin and sign in.

## Rules for sending

- Send nothing without the user's OK of that exact text, for that one person.
- Ask about one invitation at a time. Show the name, the profile link and the full note (or "No note"). Send only after a clear yes for that invitation.
- One OK is for one invitation. If the user says "send all", still confirm each invitation before you send it.
- Send the text exactly as the user approved it. If you or the user change the text, show the new text and ask again.
- Send 10 invitations or fewer in one run, unless the user asks for more. Make one call at a time.
- Do not send messages or InMail in this skill. Do not schedule anything. Do not plan automatic follow-ups.
- Do not send an invitation to a person who is already a 1st-degree connection, or who already has a pending invitation.
- If the tool says that the user is already connected to this person or already sent a request, skip that person and continue.
- Any other refusal stops all sending for this run: a limit, a wait, or a refusal from LinkedIn. Tell the user the tool's message.
- If the result says that LinkedIn did not confirm the send, do not send it again. Tell the user to check LinkedIn first.

## Other rules

- Do not make a LinkedIn URL from a name. Use the profile links from the search results or from the user.
- Do not look up email addresses or phone numbers in this skill.
- Each lookup uses part of the user's LinkMCP usage allowance. Searches and invitations also count against the daily limits of the user's LinkedIn account in LinkMCP. Read 3 pages of search results or fewer in one run, unless the user asks for more.
- Keep the data in the chat. Save a file only when the user asks for it.

## Tools

These tools only read: `linkedin_who_am_i`, `linkedin_search_people`, `linkedin_search_sales_navigator`, `linkedin_bulk_get_profiles`, `linkedin_get_person_posts`, `linkedin_get_shared_connections`. One tool writes: `linkedin_send_connection_request`. Use it only as "Rules for sending" says.

Your AI app can show a tool name with a prefix, for example `mcp__linkmcp__linkedin_search_people`. Use the tool whose name ends with the name in this skill.

## Steps

1. Call `linkedin_who_am_i`.
   - If the answer shows `is_trial` as true, tell the user that this skill needs the user's own LinkedIn account, which is part of the paid LinkMCP plans. Offer what works now: if the user has a list of LinkedIn profile links, you can rank them and find work emails. Then stop.
   - If the tool says that the LinkedIn account is not connected or has an error, tell the user to connect or reconnect it at the link that the tool gives. Then stop.
   - Note whether Sales Navigator is active.
2. Get the ideal customer from the user, if you do not know it: job titles or keywords, seniority, industry, region, and what the user sells. Ask how many people the user wants on the shortlist (default 20). The default network distance is 2nd-degree connections, because they are easier to reach. The user can also paste a LinkedIn or Sales Navigator search URL.
3. Search, one call at a time:
   - With Sales Navigator: call `linkedin_search_sales_navigator` with `keywords`, `location`, `industry`, `seniority` (numbers: 5 Manager, 6 Director, 7 VP, 8 CXO, 10 Owner), `function` if useful, and `network_distance` [2]. Or pass the user's search URL as `url`.
   - Without Sales Navigator: call `linkedin_search_people` with `keywords`, `location`, `industry` and `network_distance` [2]. Or pass the user's search URL as `url`.
   - Show how many results LinkedIn reports, or say that LinkedIn gave no total. If there are too many, suggest a narrower filter before you read more. Ask before you read the next page (with `cursor`).
4. Make the shortlist. Remove duplicates, 1st-degree connections and people with a pending invitation (`pendingInvitation`, in Sales Navigator results). Rank by how well the headline (or the current position, in Sales Navigator) and the location match the ideal customer. Keep the number that the user asked for.
5. Research the top 10 of the shortlist:
   - Call `linkedin_bulk_get_profiles` with their profile links and `detail` set to "slim" to confirm the current title and company. With Sales Navigator results, skip this call: they already have the current position.
   - Call `linkedin_get_person_posts` one time for each of the top 5. Note the newest post of the last 90 days that the person wrote, with its date and link.
   - Call `linkedin_get_shared_connections` for each of the top 5, one call at a time. Note up to 2 shared connections.
6. Show the shortlist in the format below.
7. Ask the user if they want to send connection requests, and to whom. Tell the user that LinkMCP limits invitations each day and each week, and that the tool refuses when a limit is reached.
8. Draft a note for each chosen person:
   - 300 characters or fewer. Count the characters.
   - Plain words, in the language of the person's profile. Refer to one real fact: a recent post, a shared connection or the person's role.
   - No sales pitch, no links, no fake urgency, no invented facts.
   - The user can also choose "No note".
9. Send, as "Rules for sending" says. For each approved invitation, call `linkedin_send_connection_request` with `identifier` (the profile link) and `message` (the approved note; leave `message` out for "No note"). Tell the user the result of each call before you ask about the next one.
10. Show the summary: invitations sent, skipped, refused, and not sent because of a limit, with the names.

## Output format

Title: **Prospects: <the ideal customer in a few words>**, and the date of today.

| # | Name | Title | Company | Location | Degree | Recent post | Shared connections | Fit | Why | Profile |
|---|---|---|---|---|---|---|---|---|---|---|

- Put the best fit first. "Fit" is "High", "Medium" or "Low", with one reason from the data in "Why".
- "Recent post": the topic, the date and the link, or "No recent posts". "Shared connections": names, or "None". For people outside the top 5, write "Not checked" in both columns.

After the table, give the counts: results that LinkedIn reported (or "no total"), results read, people on the shortlist. Offer the table as CSV.

For the invitations, show each draft as:

> **<Name>** (<profile link>)
> Note (<number> characters): <the note>
> Send this invitation? Answer yes, edit or skip.

## Done means

- Every person on the shortlist has a reason from the data.
- Every invitation that was sent had the user's OK of that exact note.
- The summary lists every invitation that was not sent, with the reason.

## Limits and refusals

- LinkMCP has daily limits for actions in the user's LinkedIn account. Invitations also have a weekly limit, and a lower daily limit for an account that is new or did not send invitations for some time. The limits depend on the safety level that the user chose in LinkMCP. Daily limits count from 00:00 UTC. The weekly limit counts the last 7 days.
- If a message says "daily limit", "weekly limit" or "warming up", stop that kind of call for this run. Tell the user the limit that the message gives, and the wait time if it has one. If the message gives no time, say so. Do not guess a time.
- If a read (not an invitation) gets "Please wait at least N s" and N is 120 or less, wait one time, then make one call at a time. If a call is refused again, or N is more than 120, stop and report.
- Do not try again in a loop, and do not use a different tool to get around a limit.
- If LinkedIn refuses an invitation, stop all sending. LinkedIn can refuse because of its own limit or a restriction on the account. Tell the user the tool's message, and suggest that the user checks the account on LinkedIn.
- If the usage allowance is used up, the tool says so and gives the date when it resets. Stop and tell the user that date.
- If a tool says that it needs the user's own LinkedIn account, a paid plan or Sales Navigator, tell the user that answer in your own words, with its link, one time. Do not call that tool again in this run. Continue with the steps that work without it.
