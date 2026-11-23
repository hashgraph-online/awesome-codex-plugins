---
name: "lemlist-find-leads"
description: "Find B2B leads that match an ideal customer profile in the lemlist people database (companies first, then the right people inside them), size the audience, and save the chosen leads to the lemlist CRM or a campaign. Use when the user says 'find me leads', 'build a prospect list', 'who are the heads of sales at fintechs in France', 'how many CTOs match this', or 'add these people to my campaign'. Requires the lemlist MCP server, which runs the search on the user's own lemlist team."
---

# Find leads in lemlist

Turn a description of who the user wants to reach into a short, checked list of real people, then put that list where the user will work it (a contact list or a campaign).

## When to trigger

The user describes a target ("SaaS companies in Germany with 50 to 200 people", "VP Sales at logistics companies"), asks how many people match a profile, or asks to add a list of people to lemlist.

## Requires the lemlist MCP

This skill only works with the lemlist MCP server connected. Before anything else, call `get_team_info`. If the tool is missing or the call fails, stop and walk the user through the setup in "Connect lemlist" at the end. Do not invent leads.

## Process

1. **Load the search guide.** Call `load_skill` with `skillName: "lead-search"`. It returns every filter definition and the search rules the server applies; follow it over anything in this file. If it cannot be loaded, call `get_lemleads_filters` to get the valid filter ids and values.
2. **Pin down the profile in one exchange.** You need: the kind of company (industry or a one-line description of what they do), company size, geography, and the job titles or seniority to reach. Ask only for what is missing, all at once.
3. **Search companies first** when the target is defined by what the company does. Call `lemleads_search` with `mode: "companies"`, the size and country filters, and a `description` written as 2 to 4 sentences in the style of the target company's own "About us" page (not a keyword list). For a niche vertical, pass up to 3 descriptions from different angles. Use `keywords` groups to force a product-type marker, for example software vendor and not consultancy.
4. **Then search people inside those companies.** Call `lemleads_search` with `mode: "people"`, the company ids from step 3 in the `currentCompanyByIds` filter, and `currentTitle`, `seniority` or `department` for the role. Every filter needs both `in` and `out` arrays; omit a filter you do not use.
5. **Show the user before saving anything.** Report `totalCount`, the filters used, and a sample of 10 rows (name, title, company, country). Read `filterWarnings` and fix the filters when the server flags an ambiguous location. If the count is far from what the user expects, adjust the filters and say what changed. To rerun a search with one filter changed, pass its `searchId` as `fromSearchId`.
6. **Save the leads the user approves.**
   - To the CRM: `push_contacts_from_people_database` with the `profileIds` (max 1,000 per call) and, if the user names a list, a `listId` from `get_contact_lists`. Never pass an invented list id.
   - To a campaign: `add_leads_to_campaign` with the `campaignId` (from `get_campaigns`) and up to 100 leads per call, sending `companyDomain` with `companyName` so the lead lands on the right company. Report the `outcome` of each lead (added, already in the campaign, missing identifier).

## Credits

Searching does not ask for confirmation, enrichment does. `enrichFeatures` (`find_email`, `find_phone`) and the `findEmail`, `findPhone`, `verifyEmail`, `linkedinEnrichment` options cost credits, charged only when a value is found. Before turning one on, multiply the per-lead cost the tool description gives by the number of leads, tell the user that maximum, and wait for a yes. `get_team_info` returns the credits left.

## Output format

```
TARGET
- Companies: [description, size, geography]
- People: [titles or seniority]

MATCHES
- Companies: [count]
- People: [count]

SAMPLE (10)
[name | title | company | country]

NEXT STEP
[save to list X / add to campaign Y / refine: what to change]
```

## Rules

- Never make up a person, a company, an email or a count. Everything shown comes from a tool result.
- Never save leads, spend credits or add to a campaign without the user's explicit go.
- An empty result is an answer: say which filter emptied it and propose the one to relax.

## Connect lemlist

1. Create a lemlist account if needed (a free trial works): https://app.lemlist.com
2. Add the remote MCP server `https://app.lemlist.com/mcp` to your client. In Claude Code: `claude mcp add --transport http lemlist https://app.lemlist.com/mcp`. On first use a lemlist sign-in page opens (OAuth); pick your team and allow access.
3. Per-client steps and API key setup: https://help.lemlist.com/en/articles/13728466-set-up-the-lemlist-mcp-server-in-your-llm-client-oauth-or-api-key
4. Start a new conversation and run the skill again.
