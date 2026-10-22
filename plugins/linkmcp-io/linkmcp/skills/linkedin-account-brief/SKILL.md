---
name: linkedin-account-brief
description: "Prepare a one-page account brief before a sales call, demo or meeting, with LinkedIn data from the LinkMCP connector. The brief covers the company and its recent posts, the people the user will meet and their posts, and shared connections. It also gives talking points and questions to ask. Use when the user asks to research a company or a person on LinkedIn before a call. Also use it when the user asks for call prep, meeting prep or an account brief with LinkedIn data. Reads LinkedIn data only and sends nothing."
license: MIT
compatibility: "Needs the LinkMCP connector (remote MCP server) in the AI client. Some steps (company search by name, people search, shared connections) need a paid LinkMCP plan with a connected LinkedIn account."
metadata:
  author: LinkMCP
  version: "1.0.0"
---

# LinkedIn account brief

Make a short brief that the user can read in two minutes before a call. Use only facts from the LinkMCP tools and from the user. Mark each guess as a guess.

## Rules

- This skill only reads. Do not send messages or connection requests. Do not post, comment or react.
- If the user asks for an introduction message, write it in the chat as a draft. Do not send it. A send is a separate request, and it needs the user's approval of that exact message.
- Do not make a LinkedIn URL from the name of a person. Ask the user for the URL, or use people search (step 4).
- Do not look up email addresses or phone numbers. The brief does not need them.
- LinkMCP lookups can use part of the monthly LinkMCP usage of the user. Do not request the same data two times.

## Tools

This skill uses these LinkMCP tools. All of them only read: `linkedin_get_company`, `linkedin_get_company_posts`, `linkedin_get_profile`, `linkedin_get_person_posts`, `linkedin_search_people`, `linkedin_get_shared_connections`.

Your client can show a tool name with a prefix, for example `mcp__linkmcp__linkedin_get_company`. Use the tool whose name ends with the name in this skill.

## Steps

1. Make sure that the LinkMCP tools are available, for example `linkedin_get_company`. If they are not available, stop and tell the user how to connect LinkMCP:
   - With the LinkMCP plugin: connect the LinkMCP connector of the plugin and sign in. In Claude, the connector is on the Connectors tab of the plugin.
   - Without the plugin: add LinkMCP as a remote MCP server with the URL `https://app.linkmcp.io/api/mcp?ref=skills` and sign in. Setup steps for each AI client: https://app.linkmcp.io/docs/quick-start
2. Get the inputs. You need the company (the LinkedIn company URL is best, or the name), the person (LinkedIn profile URL), or both. If the user did not give the goal of the call, ask for it.
3. Company:
   - Call `linkedin_get_company` with `identifier` (a LinkedIn company URL, slug or ID). If you only know the name of the company, use `name` instead. A search by name needs a connected LinkedIn account. If that is not available, ask the user for the LinkedIn URL of the company.
   - If you get a list of candidates, ask the user which company is correct.
   - Call `linkedin_get_company_posts` one time. Use the posts of the last 90 days.
4. People (up to 3 people, unless the user asks for more):
   - For each LinkedIn profile URL, call `linkedin_get_profile`.
   - For each person, call `linkedin_get_person_posts` one time. Use the posts of the last 90 days.
   - If the user gives a role but no person, use `linkedin_search_people`. Put the role and the company name in `keywords`. Show the results and let the user select the person. This tool needs a connected LinkedIn account.
5. Warm introductions (optional): for each person, call `linkedin_get_shared_connections`. This tool needs a connected LinkedIn account. If it is not available, write "Not checked" and the reason in the brief.
6. Write the brief in the format below.

## Brief format

Title: **<Company>: brief for <goal of the call>** and the date of today.

1. **Company:** what it does, industry, size, headquarters and website. One to three sentences.
2. **Now:** three to five topics from the recent company posts. Give the date and the link of each post.
3. **People:** for each person, the role, the time in the role, the background in one line, and the topics of the recent posts, with links.
4. **Shared connections:** the names and how each person can help, or "Not checked" and the reason.
5. **Talking points:** three to five points. Connect each point to a fact above.
6. **Questions to ask:** three to five open questions.
7. **Gaps:** the data that you could not find or check.

Keep the brief under 400 words. Do not show raw tool output.

## When a tool fails

- If a tool needs a connected LinkedIn account or a paid plan, it tells you. Give that message to the user. Then continue with the other steps.
- If a tool reports a limit or tells you to wait, do what it says. Do not call the tool again and again. If the wait is long, stop and tell the user.
- If LinkMCP cannot find a profile or a company, ask the user for the exact LinkedIn URL.
