---
name: linkedin-prospect-list
description: "Turn a list of LinkedIn profile links into a ranked prospect list, with the LinkMCP connector. For each person the list shows the role, the company with its size and website, one recent post topic, the work email with its status, and a fit rating with a reason. Use when the user pastes LinkedIn profile links (or a list or CSV of them) and asks to qualify, enrich, rank or prioritize prospects or leads, or to find their work emails. Works in the LinkMCP free trial. Reads data only and sends nothing."
license: MIT
compatibility: "Needs the LinkMCP connector (remote MCP server https://app.linkmcp.io/api/mcp) in the AI app. Works on every LinkMCP plan, also the free trial: it uses only profile, company, post and work email lookups."
metadata:
  author: LinkMCP
  version: "1.0.0"
---

# LinkedIn prospect list

Turn LinkedIn profile links into a ranked list that the user can work from today: who fits best, why, what they talk about, and their work email.

## Setup: connect LinkMCP first

1. Check that the LinkMCP tools are available, for example `linkedin_bulk_get_profiles` and `find_email`. If they are, go to "Before you start".
2. If they are not available, stop. Tell the user how to connect LinkMCP:
   - No LinkMCP account yet: sign up at https://linkmcp.io/?utm_source=skills&utm_medium=skill&utm_campaign=linkedin-prospect-list. The free trial can run this skill.
   - Add LinkMCP to the AI app as a remote MCP server (in Claude: a custom connector) with this URL, then sign in: `https://app.linkmcp.io/api/mcp?ref=skill-prospect-list`
   - Steps for each AI app: https://app.linkmcp.io/docs/quick-start
   - If the LinkMCP plugin is installed: connect the LinkMCP connector of the plugin and sign in.

## Rules

- This skill only reads. Do not send messages or connection requests. Do not comment, react or post.
- If the user asks for a first message to a person, write it in the chat as a draft. Do not send it in this skill. If the user then asks you to send it, show the recipient and the exact text again, and send only after a clear yes for that one message. Sending needs the user's own LinkedIn account, which is part of the paid LinkMCP plans.
- Do not make a LinkedIn URL from a name. Use only the links that the user gives.
- Do not guess email addresses and do not build them from a name pattern. Show only the emails that `find_email` returns.
- Do not look up phone numbers in this skill.
- Each profile, company, post and email lookup uses part of the user's LinkMCP usage allowance. Do not look up the same person or company two times. Ask the user before you look up more than 25 profiles or more than 10 work emails in one run.
- Keep the data in the chat. Save a file only when the user asks for it.

## Tools

All of these tools only read: `linkedin_bulk_get_profiles`, `linkedin_bulk_get_companies`, `linkedin_get_person_posts`, `find_email`.

Your AI app can show a tool name with a prefix, for example `mcp__linkmcp__find_email`. Use the tool whose name ends with the name in this skill.

## Before you start: ask the user

Ask only for what you do not know yet:

1. The profile links. Accept LinkedIn profile URLs, profile slugs or a pasted list or CSV.
2. Who is a good prospect: what the user sells, and the job titles, seniority, company size or region that fit. If the user does not want to describe it, skip the fit rating and order the list by the seniority of the job title.
3. Whether to find work emails. The default is yes, for the 10 people at the top of the list.

## Steps

1. Clean the input. Remove duplicate links. Put aside links that are not person profiles (company pages, posts, jobs, Sales Navigator links) and list them under "Skipped" at the end.
2. Look up the profiles. Call `linkedin_bulk_get_profiles` with up to 10 identifiers in each call and `detail` set to "slim". For each person, keep the name, headline, job title, company name, company link and location. If one profile is not found, keep the person in the list with the status "Not found". If an item has the status `usage_cap_reached`, follow "Limits and refusals".
3. Look up the companies. Collect the company links from step 2 (one time for each company). Call `linkedin_bulk_get_companies` with up to 10 company links in each call. Keep the company size (employee range), the website, the headquarters and the tagline.
4. Rate the fit. Compare each person with the description from the user: job title and seniority, company size and region. Use the industry only when the headline or the company tagline shows it. Give "High", "Medium" or "Low", and one short reason that comes from the data. Do not guess facts that the data does not show.
5. Read recent posts for the 5 people at the top of the list (the best fit, or the most senior if there is no fit rating). Call `linkedin_get_person_posts` one time for each person. Take the newest post of the last 90 days that the person wrote (not a repost). Write its topic in 10 words or fewer, with the date and the post link. If there is no such post, write "No recent posts".
6. Find work emails for the 10 people at the top of the list (High first, then Medium; or by seniority if there is no fit rating), unless the user said no.
   - Call `find_email` with `first_name`, `last_name` and `company_domain`. The domain is the host of the company website from step 3, without "www." (for example "acme.com"). If there is no website, use `company_name` instead.
   - Keep the email and its `status` (valid, catch_all, unknown or invalid). The result already has the status, so do not call `validate_email` for it.
   - If no email is found, write "Not found". Do not try other spellings.
7. Show the list in the format below.

## Output format

Title: **Prospect list: <the user's target in a few words>**, and the date of today.

| # | Name | Title | Company | Size | Location | Recent post | Work email | Email status | Fit | Why | Profile |
|---|---|---|---|---|---|---|---|---|---|---|---|

- Put the best fit first. Leave a cell empty when the data does not have the value.
- "Recent post": the topic, the date and the link, or "No recent posts", or "Not checked" for people outside the top 5.
- "Work email": the email, "Not found", or "Not looked up".

After the table, give these counts: links received, profiles found, profiles not found, links skipped, emails found out of emails looked up.

Then offer:
- the same table as CSV;
- a draft first message for one person (a draft in the chat only);
- more emails or posts for the people who were not checked.

If the user asks what else is possible: shared connections, connection requests and LinkedIn messages need the user's own LinkedIn account, which is part of the paid LinkMCP plans.

## Done means

- Every link from the user is in the table, in "Skipped", or counted as "Not found".
- Every fit rating has a reason from the data.
- No message, invitation or other action was sent.

## Limits and refusals

- In bulk results, an item with the status or the error code `usage_cap_reached` means that the usage allowance is used up. Stop all lookups. Mark the rest "Not looked up", not "Not found".
- If a tool says that the lookups or the usage allowance are used up, stop all lookups. Tell the user the tool's message in your own words. On a paid plan, the message gives the date when the allowance resets. In the free trial, the date in the message is the end of the trial, not a reset: lookups come back only after the user subscribes. Then show the list with the data that you have.
- If a message says "daily limit", "weekly limit" or "warming up", stop that kind of call for this run. Tell the user the limit that the message gives, and the wait time if it has one. If the message gives no time, say so. Do not guess a time.
- If a message says "Please wait at least N s" and N is 120 or less, wait one time, then make one call at a time. If a call is refused again, or N is more than 120, stop and report.
- Do not try again in a loop, and do not use a different tool to get around a limit.
- If a tool says that it needs the user's own LinkedIn account or a paid plan, tell the user that answer in your own words, with its link, one time. Do not call that tool again in this run. Continue with the steps that work without it.
- If one person or company is not found, keep going with the others.
