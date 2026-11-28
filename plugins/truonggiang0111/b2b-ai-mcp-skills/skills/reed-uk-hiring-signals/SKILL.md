---
name: reed-uk-hiring-signals
description: >-
  Extract UK jobs and direct-employer B2B hiring signals from Reed.co.uk with
  structured GBP salaries, Outside/Inside IR35 flags, automatic bootcamp/training
  ad exclusion (~48% spam removal), and clean descriptions. Use when an AI agent
  needs UK job market intelligence or direct in-house employer leads via MCP or REST.
---

# Reed.co.uk UK Jobs & Direct-Employer Hiring Signals

- **Apify Store:** `https://apify.com/ttyan0111/reed-uk-jobs-hiring-signals`
- **Dedicated MCP URL:** `https://mcp.apify.com?actors=ttyan0111/reed-uk-jobs-hiring-signals`
- **Pricing:** Free `$5/mo` Apify credit covers hundreds of runs (`$0.008` start + `$1.50/1k` jobs + `$2.00/1k` enriched details). Zero proxies required by default.

## Connect via MCP (Claude Code, Cursor, VS Code)

```json
{
  "mcpServers": {
    "reed-uk-jobs": {
      "url": "https://mcp.apify.com?actors=ttyan0111/reed-uk-jobs-hiring-signals"
    }
  }
}
```

## Example Input (B2B Direct-Employer Lead Search)

```json
{
  "keywords": "Python Developer",
  "location": "London",
  "remoteOnly": false,
  "contractType": "CONTRACT",
  "directEmployerOnly": true,
  "excludeIntermediaryPosts": true,
  "excludeTrainingCourses": true,
  "includeFullDescription": true,
  "maxJobs": 25
}
```

## AI-Agent Workflow (Minimal Tokens)

1. Run `ttyan0111--reed-uk-jobs-hiring-signals` (or `POST https://api.apify.com/v2/acts/ttyan0111~reed-uk-jobs-hiring-signals/run-sync-get-dataset-items`).
2. Read Key-Value Store record **`RUN_SUMMARY`** first for aggregate direct-employer ratio, Outside IR35 count, and top hiring companies.
3. Fetch dataset rows with `fields=jobId,title,employerName,isDirectEmployer,outsideIr35,salaryText,agentSummary,jobUrl`.
