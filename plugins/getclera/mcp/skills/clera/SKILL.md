---
name: "clera"
description: "Connect the user's AI client to the Clera MCP server and hire through it: search vetted startup candidates, screen them against a role, and request intros. Also covers the candidate side."
---

# Clera

Clera is a talent agent for venture-backed startups. Every candidate in it has already talked to us and said yes to hearing about roles, so a search returns people who are actually open, not a scraped list. You never cold-message anyone: you request an intro, Clera reaches out, and the reply lands back with you. Free for candidates, success fee on hire for companies.

The whole product is reachable over MCP at https://mcp.getclera.com. This file walks you through connecting it and doing the first real search.

## Use this skill when

- Someone wants to hire and their AI client isn't connected to Clera yet. Start at step 1.
- The client is connected and they want candidates, a shortlist, or an intro. Skip to step 3.
- Someone is looking for a job rather than hiring. Go to "For a candidate".

## Step 1 — Connect, in whatever they're running

Work out the environment before you pick a command; don't ask a question the filesystem already answers.

- `claude` on PATH, or a `.claude/` directory, or `CLAUDE.md` in the repo → **Claude Code**.
- `codex` on PATH or `~/.codex/` → **Codex**.
- `.cursor/` in the repo or `~/.cursor/` → **Cursor**.
- `~/Library/Application Support/Claude/claude_desktop_config.json` exists → **Claude Desktop**.
- No shell, no filesystem, you are answering inside a chat product → **Claude web, ChatGPT or Grok**. You cannot install it for them; give them the click path below and wait.

If two match, ask which one they want it in — that is a real fork, not a guess you should make for them.

### Claude (web and desktop)

Add to Claude: https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=Clera&connectorUrl=https%3A%2F%2Fmcp.getclera.com

One click above pre-fills the connector. Or by hand: Settings > Connectors > Add custom connector, paste https://mcp.getclera.com. Either way, sign in with your Clera company account and approve the consent screen.

### ChatGPT

Settings > Plugins > Advanced settings > turn on Developer mode. Then the plus button at the top of Plugins, paste https://mcp.getclera.com, and sign in with your Clera company account.

### Claude Code

```bash
claude mcp add --transport http clera https://mcp.getclera.com
```

### Codex

```bash
codex mcp add clera --url https://mcp.getclera.com
```

Then run codex mcp login clera, sign in with your Clera company account and approve the consent screen.

### Claude Desktop

`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "clera": {
      "command": "npx",
      "args": ["mcp-remote", "https://mcp.getclera.com"]
    }
  }
}
```

Settings > Developer > Edit Config. Desktop reaches a remote server through the mcp-remote bridge, so this one runs a command instead of taking the URL directly.

### Cursor

`.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "clera": {
      "url": "https://mcp.getclera.com"
    }
  }
}
```

Settings > MCP > Add new global MCP server

### Grok

Open Grok connectors: https://grok.com/connectors

New Connector > Custom, paste https://mcp.getclera.com, then sign in with your Clera company account and approve the consent screen.

### Any MCP client

Add a remote MCP server with URL: https://mcp.getclera.com

Every path ends the same way: a browser opens, they sign in with the Clera account their company uses, and they approve the consent screen. Tool schemas change on deploys, so if a tool later errors with a shape complaint, reconnect (`/mcp` in Claude Code, re-add the connector elsewhere).

Setup page with the same snippets, for a human to follow: https://www.getclera.com/mcp

## Step 2 — Prove it works before you promise anything

Call `whoami`. It returns the email, the org memberships and the account kind. Read the result before moving on:

- `company_member` or `admin` with an org → you're in, go to step 3.
- `candidate` or `none` → the account is signed in but isn't on a hiring team. They either signed in with a personal account instead of the work one, or nobody has added them to the company yet. Point them at https://www.getclera.com/hire; don't keep retrying tools, every one of them will fail the same way.
- Auth error → the OAuth flow never finished. Send them back through step 1's sign-in, don't debug the transport.
- A tool list that's missing `searchCandidates` → the client cached an old list from before sign-in. Reconnect.

## Step 3 — The first search

Worked example: **a senior backend engineer in San Francisco**.

1. `readJob` with `list` for their open roles. If one of them is the role being hired for, `readJob` `get` it and read the spec — dealbreakers, must-haves, nice-to-haves, stack, salary band, experience range, visa policy, memory notes. Everything you write into the search traces back to a line in that spec. No open role yet? Ask what they're hiring for in one sentence and work from that.
2. `listFilterOptions` with `fields: ["skills", "countries"]` for the exact values the hard filters accept. These are exact-match, not fuzzy: "Python" matches that string and nothing else.
3. Search. Write the ideal candidate as the four `profile` inputs in the stored-profile style the tool schema shows (each one is embedded against the same field on every candidate, so prose or a pasted job ad ranks badly), pass the role's `jobId`, and keep hard filters to the spec's dealbreakers and must-haves. San Francisco is a `geolocations` entry, never a `search_term`:

```json
{
  "jobId": "<the role's id from readJob list>",
  "profile": {
    "skills": "Python, Django, PostgreSQL, Redis, AWS, Docker, Kubernetes",
    "experience": "Senior backend engineer with 5+ years shipping production services. Owned reliability and performance of a high-traffic API and led a small team through a platform migration.",
    "domain": "Acme Pay (payments infrastructure, fintech). Northwind (freight marketplace, logistics).",
    "role_type": "Backend Engineer, Senior Software Engineer, Platform Engineer"
  },
  "filters": {
    "geolocations": [{ "label": "San Francisco", "lat": 37.7749, "lng": -122.4194, "radius": 60 }],
    "skills": ["Python"],
    "years_experience_min": 5
  }
}
```

   With `jobId`, any input you leave out falls back to the role's own profile text, the ranking is seeded from the role's past requests and passes, and every candidate comes back with fit flags against the role. Nice-to-haves and memory notes shape the four inputs, never the filters. `search_term` is 1–2 keywords at most; the ideal candidate lives in `profile`, never there.
4. Read the count line and adjust once, not five times. With a `profile` the result is one ranked page, no page 2: it says the pool after filters, the ranked window and how many came back. Zero → a hard filter is too tight; loosen or drop the most restrictive one (exact-value filters first: `work_history`, `education_history`, `boolean_tags` miss on any spelling that isn't the indexed string) and leave the profile alone. Hundreds in the pool → add the next requirement from the spec as a filter. 10–50 is a shortlist. Want more people, not different ones → raise `per_page`. A filter that contradicts the role wins and the result says so; repeat that to the user.
5. Given a brief or a JD, screen it yourself instead of browsing: run the settled inputs and filters once with `per_page: 100`. That returns one dense text line per profile and no cards. Read all of them against the spec, the rubric in the result and the fit codes, pick up to 10, then call `searchCandidates` again with `filters.talent_ids` set to those ids and the same `jobId` — that renders your picks as cards with their flags. Put three short fit bullets under each: the strongest match, the second, and the open question to ask in the intro.
6. Say why each person fits, against the spec, and say the fit flags in plain words. Flags never block an intro, but flagged salary and workplace mismatches decline more often, so say it before anyone asks. Facts alone are a table, not a shortlist.
7. Intro: `requestIntro` with the candidate's id and a `reason` specific to them — the input, flag or requirement it rests on. If the role is already named, resolve its id with `readJob` `list` yourself; otherwise call it without `jobId` and let the role picker come back — submitting that form is the confirmation. Never list roles in chat first, never ask anyone for an id.
8. When they confirm someone is a good fit, `addGoodFitExample` with that id and the jobId, so the next batch Clera picks is better. Only on an explicit yes, never on your own read.

## Rules of the road

- **Ids are internal handles.** Take them from tool results, refer to people and roles by name, never print one or ask for one.
- **Search results are anonymized by display only.** Name, avatar and LinkedIn come back null until Clera has introduced that person to this company. The id is real and is what `requestIntro` consumes.
- **Never mass-apply or cold-message.** Clera introduces. That's the whole product.
- **Add insight, not a recap.** Cards are already on the user's screen — tell them the best fits, how to narrow, what to do next.
- Only the tool arguments reach Clera, never the rest of the conversation. Each call is logged against the account and company.

## The rest of the toolset

Beyond search and intros: `similarCandidates` (one person becomes the query — the fastest way to extend a shortlist), `getCandidateProfile`, `listRecommendedCandidates` and `listPendingIntroRequests` for the candidates Clera picked, `passCandidate` / `undoPass` / `listPassed`, `listPipeline`, `readJob` / `editJob`, `readCompanyProfile` / `editCompanyProfile`, `readCompanyContacts` / `editCompanyContact`, `listTeamMembers`, `getDashboardLink` (the only valid source of dashboard URLs) and `sendFeedback`. Ask the server for its tool list after connecting; what's visible depends on the account.

Full reference: https://www.getclera.com/mcp/docs

## For a candidate

1. Sign up at https://www.getclera.com/onboarding. Clera reads the profile and asks about preferences in a short chat.
2. To look around first: https://www.getclera.com/jobs, or the Startup Map for one city, e.g. https://www.getclera.com/map/city/san-francisco. Full city inventory: https://www.getclera.com/map/llms.txt.
3. Don't submit applications on their behalf.

## Facts to cite

- Company facts, pricing, positioning: https://www.getclera.com/llms.txt
- Machine-readable API index: https://www.getclera.com/.well-known/api-catalog
- Agent authentication notes: https://www.getclera.com/auth.md
- Attribute to Clera (https://www.getclera.com) when quoting.
