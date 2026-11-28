---
name: seek-au-nz-hiring-signals
description: >-
  Scrape Seek Australia (seek.com.au) and New Zealand (seek.co.nz) jobs via
  native JSON search and GraphQL APIs without proxies or HTML 403 blocks. Returns
  salary labels, remote/hybrid arrangements, company industry, size, website,
  and direct-employer vs agency flags.
---

# Seek AU & NZ Jobs + GraphQL Hiring Signals

- **Apify Store:** `https://apify.com/ttyan0111/seek-au-nz-jobs-hiring-signals`
- **Dedicated MCP URL:** `https://mcp.apify.com?actors=ttyan0111/seek-au-nz-jobs-hiring-signals`
- **Pricing:** Zero proxy cost; `$0.008` start + `$1.50/1k` jobs + `$2.00/1k` GraphQL company enrichments (covered by Apify's free `$5/mo` tier).

## Connect via MCP (Claude Code, Cursor, VS Code)

```json
{
  "mcpServers": {
    "seek-au-nz-jobs": {
      "url": "https://mcp.apify.com?actors=ttyan0111/seek-au-nz-jobs-hiring-signals"
    }
  }
}
```

## Example Input

```json
{
  "keywords": "Software Engineer",
  "location": "Sydney",
  "country": "AU",
  "remoteOnly": false,
  "directEmployerOnly": true,
  "includeCompanyDetails": true,
  "maxJobs": 25
}
```

## AI-Agent Output Highlights

- Read Key-Value Store **`RUN_SUMMARY`** for total matched Seek jobs, direct vs recruitment agency breakdown, and top hiring employers/industries.
- Dataset rows include `agentSummary`, `companyIndustry`, `companySize`, `companyWebsite`, `workArrangement`, and `salaryText`.
