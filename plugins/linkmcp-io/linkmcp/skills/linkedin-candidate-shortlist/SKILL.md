---
name: linkedin-candidate-shortlist
description: "Screen LinkedIn candidates for an open role and make a ranked shortlist, with the LinkMCP connector. For each candidate the shortlist shows the current role, the relevant experience, a check of each must-have requirement with evidence from the profile, the gaps, and questions for the first call. Use when the user gives LinkedIn profile links and a role, a job description or a LinkedIn job link, and asks to screen, compare, rank or shortlist candidates. With a paid LinkMCP plan and the user's LinkedIn account connected, it can also find candidates with LinkedIn search and send invitations. Works in the free trial with profile links. Sends nothing without the user's OK of the exact text."
license: MIT
compatibility: "Needs the LinkMCP connector (remote MCP server https://app.linkmcp.io/api/mcp) in the AI app. Screening profile links works on every LinkMCP plan, also the free trial. Candidate search, shared connections and invitations need a paid LinkMCP plan with the user's LinkedIn account connected."
metadata:
  author: LinkMCP
  version: "1.0.0"
---

# LinkedIn candidate shortlist

Screen candidates against the real requirements of a role, show the evidence for each rating, and give the recruiter or hiring manager a shortlist with questions for the first call. A person makes the hiring decision. This skill helps with the first screen only.

## Setup: connect LinkMCP first

1. Check that the LinkMCP tools are available, for example `linkedin_bulk_get_profiles`. If they are, go to "Before you start".
2. If they are not available, stop. Tell the user how to connect LinkMCP:
   - No LinkMCP account yet: sign up at https://linkmcp.io/?utm_source=skills&utm_medium=skill&utm_campaign=linkedin-candidate-shortlist. The free trial can screen profile links.
   - Add LinkMCP to the AI app as a remote MCP server (in Claude: a custom connector) with this URL, then sign in: `https://app.linkmcp.io/api/mcp?ref=skill-candidate-shortlist`
   - Steps for each AI app: https://app.linkmcp.io/docs/quick-start
   - If the LinkMCP plugin is installed: connect the LinkMCP connector of the plugin and sign in.

## Rules

- Rate candidates only on facts that matter for the job: skills, experience, education, certifications, and location or work type when the role needs it.
- Do not use, guess or mention age, gender, ethnicity, nationality, religion, health, disability, family status or other personal traits. Do not guess them from a name, a photo, graduation years or gaps in a career.
- Write "Not shown" when the profile does not show a requirement. A missing fact is not a "No".
- Do not look up email addresses or phone numbers of candidates. If the user asks for one specific candidate, tell the user that `find_email` finds work emails at the current employer, and ask before you use it.
- Do not send connection requests or messages, unless the user asks for it in step 10 and approves each exact text, as "Rules for sending" says.
- Each profile and post lookup uses part of the user's LinkMCP usage allowance. Do not look up the same person two times. Ask the user before you screen more than 20 candidates in one run.
- Keep the data in the chat. Save a file only when the user asks for it.

## Rules for sending (step 10 only)

- Send nothing without the user's OK of that exact text, for that one person.
- Ask about one invitation at a time. Show the name, the profile link and the full note (or "No note"). Send only after a clear yes for that invitation.
- One OK is for one invitation. If the user says "send all", still confirm each invitation before you send it.
- Send the text exactly as the user approved it. If the text changes, show the new text and ask again.
- Send 10 invitations or fewer in one run. Make one call at a time.
- If the tool says that the user is already connected to this person or already sent a request, skip that person and continue.
- Any other refusal stops all sending for this run: a limit, a wait, or a refusal from LinkedIn. Tell the user the tool's message.
- If the result says that LinkedIn did not confirm the send, do not send it again. Tell the user to check LinkedIn first.

## Tools

These tools only read: `linkedin_get_job`, `linkedin_bulk_get_profiles`, `linkedin_get_person_posts`, `linkedin_who_am_i`, `linkedin_search_people`, `linkedin_search_sales_navigator`, `linkedin_get_shared_connections`. One tool writes: `linkedin_send_connection_request`. Use it only in step 10, as "Rules for sending" says.

Your AI app can show a tool name with a prefix, for example `mcp__linkmcp__linkedin_bulk_get_profiles`. Use the tool whose name ends with the name in this skill.

## Before you start: ask the user

Ask only for what you do not know yet:

1. The role: the title, 3 to 5 must-have requirements, the nice-to-have requirements, and the location or work type. The user can also paste a job description or a LinkedIn job link.
2. The candidates: LinkedIn profile links. If the user has no links, step 3 can search for candidates, with a paid LinkMCP plan.
3. How many candidates to put on the shortlist. The default is 5.

## Steps

1. If the user gave a LinkedIn job link, call `linkedin_get_job` with `job` set to the link. Take the title, location, experience level and the requirements from the description. In the free trial the tool reads the public job page, so the work type can be empty: then ask the user. Show the must-have requirements that you found and ask the user to confirm or change them. If `linkedin_get_job` is not available in the AI app, ask the user to paste the job text.
2. If the user gave profile links, remove duplicates and go to step 4.
3. Find candidates (only when there are no links):
   - Call `linkedin_who_am_i`. If the answer shows `is_trial` as true, tell the user that candidate search needs the user's own LinkedIn account, which is part of the paid LinkMCP plans. If the tool says that the LinkedIn account is not connected or has an error, tell the user to connect or reconnect it at the link that the tool gives. In both cases, ask for profile links instead, wait for them, and then go to step 4.
   - If Sales Navigator is active, call `linkedin_search_sales_navigator` with `keywords` (the title and one key skill), `location`, and if useful `seniority`, `function` or `tenure` (total years of experience). If not, call `linkedin_search_people` with `keywords` and `location`. The user can also paste a LinkedIn or Sales Navigator search URL: then pass it as `url`.
   - Read one page of results. Show how many results LinkedIn reports, or say that LinkedIn gave no total. Ask the user before you read the next page (with `cursor`). Read 3 pages or fewer. Make one search call at a time.
   - Choose up to 20 people whose headline (or current position, in Sales Navigator) best matches the role, and use their profile links in step 4.
4. Look up the profiles. Call `linkedin_bulk_get_profiles` with up to 10 identifiers in each call and `detail` set to "full", so you get all positions and education.
5. Screen each candidate:
   - For each must-have requirement: "Yes", "Partly", "No" or "Not shown", with the evidence (the position, the company and the years, or the education).
   - The years of relevant experience: add up only the positions that match the role. Say how you counted.
   - The gaps and the risks, as facts (for example "No people management shown").
   - A rating: "Strong", "Possible" or "Weak", from the must-haves first, then the nice-to-haves.
6. For the candidates with the best rating (up to the shortlist size), call `linkedin_get_person_posts` one time each. Note posts of the last 12 months that show work on the requirements. If there are none, write "No relevant posts".
7. Optional, paid plans: call `linkedin_get_shared_connections` for the first shortlisted candidate. If it says that it needs the user's own LinkedIn account, do not call it again: write "Not checked" for every candidate. If it works, call it for the other shortlisted candidates, one call at a time. Name up to 3 shared connections who could give an introduction or a reference.
8. Show the shortlist in the format below.
9. Optional: if the user wants to contact candidates, draft a connection note for each chosen candidate:
   - 300 characters or fewer. Count the characters.
   - Refer to one real fact from the profile or a post, and name the role.
   - Do not promise anything.
   - The user can also choose "No note".
10. Send the approved invitations, as "Rules for sending" says. This needs the user's own LinkedIn account. For each approved invitation, call `linkedin_send_connection_request` with `identifier` (the profile link) and `message` (the approved note; leave `message` out for "No note"). Tell the user the result before you ask about the next one.

## Output format

Title: **Shortlist: <role title>**, and the date of today. Under it, the must-have requirements as one line.

| # | Name | Current role | Relevant experience | Must-haves met | Rating | Gaps | Profile |
|---|---|---|---|---|---|---|---|

Then, for each candidate on the shortlist:

- **<Name>**: one line why the candidate fits.
- Evidence: each must-have with "Yes", "Partly", "No" or "Not shown" and its source.
- Recent posts: up to 2 relevant posts with date and link, or "No relevant posts".
- Shared connections: names, or "Not checked".
- Questions for the first call: 3 questions about the gaps and the "Not shown" items.

After that, list the other screened candidates in one line each, with the main reason that they are not on the shortlist. Then give the counts: candidates screened, not found, on the shortlist. Offer the table as CSV.

If invitations were sent, end with a summary: sent, skipped, and not sent because of a refusal, with the names.

## Done means

- Every rating has evidence from the profile, and every unknown is "Not shown".
- The shortlist uses no personal traits, as the rules say.
- No invitation was sent without the user's OK of that exact text.

## Limits and refusals

- LinkMCP has daily limits for actions in the user's LinkedIn account. Invitations also have a weekly limit, and a lower daily limit for an account that is new or did not send invitations for some time. Daily limits count from 00:00 UTC. The weekly limit counts the last 7 days.
- In bulk results, an item with the status `usage_cap_reached` means that the usage allowance is used up. Stop all lookups. Mark the rest "Not looked up", not "Not found".
- If a tool says that the lookups or the usage allowance are used up, stop all lookups. Tell the user the tool's message in your own words. On a paid plan, the message gives the date when the allowance resets. In the free trial, the date in the message is the end of the trial, not a reset: lookups come back only after the user subscribes.
- If a message says "daily limit", "weekly limit" or "warming up", stop that kind of call for this run. Tell the user the limit that the message gives, and the wait time if it has one. If the message gives no time, say so. Do not guess a time.
- If a read (not an invitation) gets "Please wait at least N s" and N is 120 or less, wait one time, then make one call at a time. If a call is refused again, or N is more than 120, stop and report.
- Do not try again in a loop, and do not use a different tool to get around a limit.
- If a tool says that it needs the user's own LinkedIn account or a paid plan, tell the user that answer in your own words, with its link, one time. Do not call that tool again in this run. Continue with the steps that work without it.
- If a profile is not found, ask the user for the exact profile link. Do not guess it.
