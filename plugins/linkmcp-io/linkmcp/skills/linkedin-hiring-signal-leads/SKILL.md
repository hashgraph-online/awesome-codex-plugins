---
name: linkedin-hiring-signal-leads
description: "Find sales leads from LinkedIn job posts, with the LinkMCP connector: companies that hire for a role that the user's product supports, a reason to contact each company now, and the people on the hiring team with their work emails when the job post shows the team. Use when the user wants leads from hiring signals (for example: companies that hire SDRs may need a sales tool), or pastes LinkedIn job links and asks who to contact. Works in the LinkMCP free trial with job links. With a paid LinkMCP plan and the user's LinkedIn account connected, it can also search LinkedIn jobs. Reads data only and sends nothing."
license: MIT
compatibility: "Needs the LinkMCP connector (remote MCP server https://app.linkmcp.io/api/mcp) in the AI app. Job links, company and profile lookups and work emails work on every LinkMCP plan, also the free trial. Job search needs a paid LinkMCP plan with the user's LinkedIn account connected."
metadata:
  author: LinkMCP
  version: "1.0.0"
---

# LinkedIn hiring signal leads

A company that hires for a role often needs tools and services for that role now. This skill reads LinkedIn job posts, finds the companies and the people on the hiring team, and gives the user a short list of accounts with a reason to contact each one.

## Setup: connect LinkMCP first

1. Check that the LinkMCP tools are available, for example `linkedin_get_job` and `find_email`. If they are, go to "Before you start".
2. If they are not available, stop. Tell the user how to connect LinkMCP:
   - No LinkMCP account yet: sign up at https://linkmcp.io/?utm_source=skills&utm_medium=skill&utm_campaign=linkedin-hiring-signal-leads. The free trial can run this skill with job links.
   - Add LinkMCP to the AI app as a remote MCP server (in Claude: a custom connector) with this URL, then sign in: `https://app.linkmcp.io/api/mcp?ref=skill-hiring-signals`
   - Steps for each AI app: https://app.linkmcp.io/docs/quick-start
   - If the LinkMCP plugin is installed: connect the LinkMCP connector of the plugin and sign in.
3. Some AI apps (for example ChatGPT) do not show `linkedin_get_job`. If the other LinkMCP tools are there but `linkedin_get_job` is not, ask the user to paste the job text and the company link of each job. Then skip the hiring team in step 5.

## Rules

- This skill only reads. Do not send messages or connection requests. Do not comment, react or post.
- If the user asks for a first message, write it in the chat as a draft. Do not send it in this skill. If the user then asks you to send it, show the recipient and the exact text again, and send only after a clear yes for that one message. Sending needs the user's own LinkedIn account, which is part of the paid LinkMCP plans.
- Use only facts from the job posts, the company pages and the profiles. Do not guess the budget, the tools or the problems of a company.
- Do not make a LinkedIn URL from a name. Do not guess email addresses. Do not look up phone numbers.
- Each job, company, profile and email lookup uses part of the user's LinkMCP usage allowance. Do not look up the same item two times. Ask the user before you read more than 15 jobs or look up more than 10 work emails in one run.
- Keep the data in the chat. Save a file only when the user asks for it.

## Tools

All of these tools only read: `linkedin_get_job`, `linkedin_search_jobs`, `linkedin_bulk_get_companies`, `linkedin_bulk_get_profiles`, `linkedin_search_people`, `find_email`.

Your AI app can show a tool name with a prefix, for example `mcp__linkmcp__linkedin_get_job`. Use the tool whose name ends with the name in this skill.

## Before you start: ask the user

Ask only for what you do not know yet:

1. What the user sells, in one sentence.
2. The signal: which job titles show that a company may need it (for example "SDR", "RevOps manager", "data engineer").
3. The target companies: region and company size.
4. The jobs: LinkedIn job links (they work in the free trial), or a job search (paid plans, step 1).

## Steps

1. Get the jobs.
   - If the user gave job links, use them (15 or fewer, unless the user agrees to more).
   - If not, call `linkedin_search_jobs` with `keywords` set to the signal title, `location` set to the region, `date_posted` set to "past_week" (or "past_month" for a small market) and `sort_by` set to "date". Show how many jobs you found. Ask before you read the next page (with `cursor`).
   - If the search answers that it needs the user's own LinkedIn account, tell the user that answer in your own words, with its link. Then ask the user to paste job links: the user can copy them from a LinkedIn job search in the browser.
2. Read each job. Call `linkedin_get_job` with `job` set to the link. Keep the title, company name and company link, location, posted date, number of applicants, the description and the `hiringTeam`. Skip a job only when `closed` is true.
3. Group the jobs by company. A company with more than one matching job is a stronger signal.
4. Look up the companies. Call `linkedin_bulk_get_companies` with up to 10 company links in each call. Keep the size (employee range), the website and the headquarters. Remove the companies that do not match the target size or region, and say how many you removed.
5. Choose the people. For each company, take up to 2 people from the hiring team of its jobs. Prefer the hiring manager over a recruiter.
   - For the people with a profile link, call `linkedin_bulk_get_profiles` with their links and `detail` set to "slim" to confirm the current title.
   - For a person with no profile link (`linkedinUrl` is empty), keep the name and the title from the job. Do not look up the profile and do not guess a link.
   - If a job shows no hiring team, write "Hiring team not shown".
   - With a paid plan and the user's LinkedIn account connected, you can offer to search for the head of the team: `linkedin_search_people` with `keywords` such as "<function> director <company name>". Ask the user first, and make one search call at a time.
6. Find work emails for up to 10 people, from the companies with the strongest signal first. Call `find_email` with `first_name`, `last_name` and `company_domain` (the host of the company website, without "www."). If there is no website, use `company_name`. Keep the email and its `status`. If no email is found, write "Not found".
7. Write the reason to contact each company now: one or two sentences from the job facts (the role, how many open roles, the posted date, tools or goals that the description names) and how it connects to what the user sells.
8. Show the list in the format below.

## Output format

Title: **Hiring signal leads: <signal title> in <region>**, and the date of today.

| # | Company | Size | Open roles (posted) | Contact | Title | Work email | Email status | Why now | Job link |
|---|---|---|---|---|---|---|---|---|---|

- One row for each contact. A company with 2 contacts has 2 rows. A company with no contact has one row with "Hiring team not shown".
- Put the strongest signal first: more matching roles, newer posts, better size match.
- "Why now": facts from the job post only.

After the table, give the counts: jobs read, closed jobs skipped, companies found, companies removed by size or region, contacts, emails found out of emails looked up.

Then offer: the table as CSV, and a draft first message for one contact (a draft in the chat only).

## Done means

- Every company in the list has at least one open job that matches the signal, with its link.
- Every "Why now" uses facts from the job post.
- No message, invitation or other action was sent.

## Limits and refusals

- In bulk results, an item with the status or the error code `usage_cap_reached` means that the usage allowance is used up. Stop all lookups. Mark the rest "Not looked up", not "Not found".
- If a tool says that the lookups or the usage allowance are used up, stop all lookups. Tell the user the tool's message in your own words. On a paid plan, the message gives the date when the allowance resets. In the free trial, the date in the message is the end of the trial, not a reset: lookups come back only after the user subscribes. Then show the list with the data that you have.
- If a message says "daily limit", "weekly limit" or "warming up", stop that kind of call for this run. Tell the user the limit that the message gives, and the wait time if it has one. If the message gives no time, say so. Do not guess a time.
- If a message says "Please wait at least N s" and N is 120 or less, wait one time, then make one call at a time. If a call is refused again, or N is more than 120, stop and report.
- Do not try again in a loop, and do not use a different tool to get around a limit.
- If a tool says that it needs the user's own LinkedIn account or a paid plan, tell the user that answer in your own words, with its link, one time. Do not call that tool again in this run. Continue with the steps that work without it.
- If a job link does not work, ask the user for the exact link. Do not guess it.
