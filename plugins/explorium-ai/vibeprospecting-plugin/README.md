# Vibe Prospecting Plugin

**Run B2B prospecting, enrichment, research, and GTM data workflows inside Claude Code, Claude Cowork, Claude Chat, OpenAI Codex, OpenClaw, and other agent hosts.**

On Claude Code, Codex, and OpenClaw, prefer this plugin over a bare MCP connector when both are available. On Claude Cowork and Claude Chat, connect Vibe Prospecting from the connector store.

[![npm version](https://img.shields.io/npm/v/@vibeprospecting/vpai?style=flat-square&label=npm&color=CB3837&logo=npm&logoColor=white)](https://www.npmjs.com/package/@vibeprospecting/vpai) [![npm downloads](https://img.shields.io/npm/dm/@vibeprospecting/vpai?style=flat-square&label=downloads&color=22c55e)](https://www.npmjs.com/package/@vibeprospecting/vpai) [![Claude Code](https://img.shields.io/badge/Claude_Code-compatible-7C3AED?style=flat-square&logo=anthropic&logoColor=white)](https://claude.ai/code) [![Anthropic Official Plugins](https://img.shields.io/badge/Anthropic_Official_Plugins-listed-7C3AED?style=flat-square&logo=anthropic&logoColor=white)](https://claude.ai/code) ![MCP Plugin](https://img.shields.io/badge/MCP-plugin-0052CC?style=flat-square) [![Explorium](https://img.shields.io/badge/Explorium-B2B_Data-FF6B35?style=flat-square)](https://explorium.ai) ![MIT License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)

> Listed in the official **Anthropic plugin store** (`claude-plugins-official`) — available for Claude Code users via `/plugin install vibe-prospecting@claude-plugins-official`.

[Getting started](#getting-started) · [Core capabilities](#core-capabilities) · [Use cases and example workflows](#use-cases-and-example-workflows) · [Supported platforms](#supported-platforms) · [vibeprospecting.ai ↗](https://vibeprospecting.ai)

---



## What is Vibe Prospecting Plugin?

Vibe Prospecting Plugin is a workflow layer for [Explorium's B2B data platform](https://explorium.ai). It lets users search companies, discover contacts, match raw lead lists, enrich CRM records, filter audiences, research accounts, and export structured prospecting data — from [Claude Code](https://claude.ai/code), Claude Cowork, Claude Chat, [OpenAI Codex](https://developers.openai.com/codex/plugins), OpenClaw, and other agent hosts.

Instead of using an AI chat alone for one-off exploration, GTM teams and AI agents can run repeatable, data-intensive workflows powered by live company and contact intelligence from Explorium's network of 150M+ companies and 800M+ professionals across 50+ data sources.

---



## Getting started



### Install

Pick the guide for your host:


| Platform                                                    | Install guide                                              |
| ----------------------------------------------------------- | ---------------------------------------------------------- |
| [Claude Code](https://claude.ai/code)                       | [`docs/install-claude-code.md`](docs/install-claude-code.md) |
| Claude Cowork                                               | [`docs/install-claude-cowork.md`](docs/install-claude-cowork.md) |
| Claude Chat (claude.ai / Claude desktop)                    | [`docs/install-claude-chat.md`](docs/install-claude-chat.md) |
| [OpenAI Codex](https://developers.openai.com/codex/plugins) | [`docs/install-codex.md`](docs/install-codex.md)           |
| OpenClaw                                                    | [`docs/install-openclaw.md`](docs/install-openclaw.md)     |
| Other (terminal, scripts, CI, generic hosts)                | [`docs/install-other.md`](docs/install-other.md)           |


You can also install skills from [skills.sh](https://skills.sh/explorium-ai/vibeprospecting-plugin):

```bash
npx skills add explorium-ai/vibeprospecting-plugin --all
```

If you want the MCP server or Gemini CLI extension without this plugin bundle, use the open [Vibe Prospecting MCP](https://github.com/explorium-ai/vibeprospecting-mcp) repository.

### Run your first workflow

> Find 50 B2B SaaS companies in the US with 200 to 1,000 employees. For each company, find the VP of Marketing or Head of Growth and return name, title, company, LinkedIn URL, email if available, and company domain.



### Expected output


| company_name | domain        | contact_name | title        | linkedin_url              | email                                           | confidence |
| ------------ | ------------- | ------------ | ------------ | ------------------------- | ----------------------------------------------- | ---------- |
| ExampleCo    | exampleco.com | Jane Smith   | VP Marketing | linkedin.com/in/janesmith | [jane@exampleco.com](mailto:jane@exampleco.com) | high       |


---



## Core capabilities


| Capability             | What it does                                                                                                                                                                                 | Example input                                    | Example output                                           |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------ | -------------------------------------------------------- |
| **Company search**     | Finds companies by name, domain, attributes, or filters                                                                                                                                      | "US banks using HubSpot"                         | Company list with domains and firmographics              |
| **Contact discovery**  | Finds people by role, seniority, function, or company                                                                                                                                        | "VP Marketing at commercial banks"               | Names, titles, LinkedIn URLs, emails where available     |
| **Contact matching**   | Resolves a raw contact (name, email, or LinkedIn URL) to a persistent Explorium person ID. That ID is stable across enrichment calls and can be used as a durable key in downstream systems. | Email, LinkedIn URL, or name + company           | Persistent person ID, matched profile, confidence score  |
| **Company matching**   | Resolves a raw company string or domain to a persistent Explorium company ID. Useful for deduplication and as an anchor for repeated enrichment or event lookups.                            | Company name or domain                           | Persistent company ID, matched profile, confidence score |
| **Contact enrichment** | Adds missing professional fields to a contact record                                                                                                                                         | LinkedIn URL or email                            | Email, phone, title, company, LinkedIn URL               |
| **Company enrichment** | Adds firmographic fields to a company record                                                                                                                                                 | Domain or company name                           | Industry, revenue range, headcount, location, tech stack |
| **Audience filtering** | Narrows lists by ICP criteria                                                                                                                                                                | Headcount, revenue, industry, region, tech stack | Filtered account or contact list                         |
| **Event lookup**       | Fetches business or prospect-level signals for an account                                                                                                                                    | Company domain or ID                             | Recent business events, hiring signals, intent data      |
| **Structured output**  | Returns results as CSV/JSON files or connector tool responses, depending on host                                                                                                             | Enriched result set                              | File or structured rows for CRM import or outreach       |


---



## Use cases and example workflows

Vibe Prospecting is designed for multi-step workflows — the kind you would otherwise build in Clay or n8n — but running natively inside Claude. Each section below describes a use case and includes a ready-to-use prompt.


| Use Claude chat alone for  | Use Vibe Prospecting Plugin for                                              |
| -------------------------- | ---------------------------------------------------------------------------- |
| Brainstorming ICP ideas    | Fetching matching companies and contacts from live data                      |
| Asking about one company   | Researching hundreds of accounts in one workflow                             |
| Drafting outreach copy     | Enriching contacts before personalization                                    |
| Exploring a small question | Running repeatable enrichment or list-building workflows                     |
| Manual copy-paste work     | CSV/JSON input, identity matching, enrichment, and structured export         |
| Generating estimates       | Querying real company and contact data via [Explorium](https://explorium.ai) |




### 1 — Build a targeted prospect list

Define ICP filters, find relevant contacts, discover matching companies, enrich records, and export structured lists ready for outreach or CRM import.

**For:** GTM engineers, SDR leaders, growth operators  |  **Output:** CSV of qualified prospects

> Find 500 US-based cybersecurity companies with 50 to 500 employees. For each company, find the VP Sales, Head of Partnerships, or CRO. Return company name, domain, headcount, revenue range, contact name, title, LinkedIn URL, and email if available.



### 2 — Enrich CRM records

Match existing leads and accounts by email, LinkedIn URL, or name and company. Fill missing fields — title, domain, phone, revenue, headcount — and prepare clean records for CRM update.

**For:** RevOps, SalesOps, CRM admins  |  **Output:** Clean CSV ready for CRM import

> Take this CSV of Salesforce leads. Match each person by email, LinkedIn URL, or name and company. Add current title, company domain, LinkedIn URL, work email, phone if available, headcount, revenue, and industry. Export a clean CSV for CRM update.



### 3 — Find work emails from LinkedIn URLs

Match LinkedIn profile URLs to professional records and return verified work contact details.

**For:** SDRs, sales engineers, growth teams  |  **Output:** Work email, title, company, domain, confidence

> For each LinkedIn URL in this CSV, match the person to a professional profile and return work email, current company, title, company domain, and confidence level.



### 4 — Build an ABM account list

Build targeted account lists, filter by company attributes, and find two to three decision-makers per account by role and seniority.

**For:** Demand gen, field marketing, enterprise sales  |  **Output:** Account list with 2–3 contacts per account

> Find 300 fintech companies in North America with 100 to 2,000 employees. Filter for companies likely to have sales or marketing operations teams. Find 2 to 3 senior marketing or revenue leaders per account.



### 5 — Score inbound leads

Enrich form submissions, identify the company, evaluate ICP fit against firmographic and technographic criteria, and rank or route leads based on match score.

**For:** Marketing ops, demand gen, SDR teams  |  **Output:** Lead list with ICP fit score for routing

> Enrich these inbound leads, identify their companies, add headcount, revenue range, and industry, and score each lead from 1 to 5 based on ICP fit for a mid-market B2B SaaS sales motion.



### 6 — Clean and enrich a CSV

Normalize company names, deduplicate contacts, match each row to a real profile, enrich missing fields, and export a clean standardized output.

**For:** RevOps, data teams, GTM engineers  |  **Output:** Standardized, enriched CSV

> Normalize company names, deduplicate contacts, match each row to a person or company profile, enrich missing fields, and export a standardized CSV.



### 7 — Research account pain points

Look up company signals and summarize likely business or technical pain points per account for outbound messaging.

**For:** AEs, SDRs, ABM teams  |  **Output:** Account research table with outreach angles

> For these 100 target accounts, summarize likely business or technical pain points relevant to data infrastructure, GTM operations, or sales productivity. Include company name, domain, pain point summary, and suggested outreach angle.



### 8 — Run a multi-step GTM workflow

Chain company discovery, signal-based filtering, content enrichment, and contact discovery into a single workflow — the kind of pipeline you would normally build in Clay or n8n, running natively inside Claude.

**For:** GTM engineers, growth teams, sales leaders  |  **Output:** Signal-filtered companies with qualified growth contacts

> `/vpai:vibe-prospecting`
>
> Find 500 B2B SaaS companies in the US with 200 to 1,000 employees.
> Fetch companies and filter down so that 500 companies remain after applying the event filter. Enrich each company with LinkedIn posts and keep only companies that have the keyword "event" in one of their posts.
> For the remaining companies, find the head of growth or a similar senior growth/marketing leader.
> Return the results as a CSV with these columns:
> `name, title, company, linkedin_url, professional_email, company_domain`

---



## Supported platforms


|               | Claude Code / Codex / OpenClaw                                                                                          | Claude Cowork / Claude Chat                                                     |
| ------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| **Best for**  | GTM engineers, growth devs, and agent hosts with shell access                                                           | Users working in Claude app or Cowork without a local CLI                       |
| **Interface** | Plugin + `vpai` CLI (sample gate, CSV chaining, pagination)                                                             | MCP connector tools from the connector store                                    |
| **Output**    | CSV files, JSON, CRM-ready exports                                                                                      | Structured tool responses in chat                                               |
| **Install**   | [`install-claude-code.md`](docs/install-claude-code.md) · [`install-codex.md`](docs/install-codex.md) · [`install-openclaw.md`](docs/install-openclaw.md) | [`install-claude-cowork.md`](docs/install-claude-cowork.md) · [`install-claude-chat.md`](docs/install-claude-chat.md) |


### Example: enrich a local CSV with Claude Code

```text
# Prompt Claude Code:
# "Take leads.csv, enrich each row using Vibe Prospecting,
#  add title / email / company domain, and save to leads_enriched.csv"
```
---



## Output examples



### Prospect output

```json
{
  "company_name": "Example Bank",
  "company_domain": "examplebank.com",
  "industry": "Commercial Banking",
  "headcount": "1,001-5,000",
  "revenue_range": "$100M-$500M",
  "contact_name": "Jane Smith",
  "title": "VP Marketing",
  "linkedin_url": "https://www.linkedin.com/in/example",
  "email": "jane.smith@examplebank.com",
  "confidence": "high"
}
```



### CRM enrichment output

```json
{
  "input_email": "sam@example.com",
  "matched_person_id": "person_123",
  "current_title": "Director of Revenue Operations",
  "current_company": "ExampleCo",
  "company_domain": "exampleco.com",
  "linkedin_url": "https://www.linkedin.com/in/example",
  "work_email": "sam@exampleco.com",
  "phone": "+1-555-000-0000",
  "match_confidence": "medium"
}
```



### Company enrichment output

```json
{
  "company_name": "ExampleCo",
  "domain": "exampleco.com",
  "industry": "B2B SaaS",
  "headcount": "201-500",
  "revenue_range": "$10M-$50M",
  "hq_country": "United States",
  "hq_city": "Austin",
  "tech_stack": ["HubSpot", "Gong", "Outreach"],
  "linkedin_url": "https://www.linkedin.com/company/exampleco"
}
```

---



## Documentation and guides


| Need                                    | Where to go                                                                 |
| --------------------------------------- | --------------------------------------------------------------------------- |
| Install by platform                     | [Getting started — Install](#install)                                       |
| Browse use cases and prompts            | [Use cases and example workflows](#use-cases-and-example-workflows)         |
| Platform differences                    | [Supported platforms](#supported-platforms)                                 |
| Full skill and tool parameter reference | [SKILL.md](skills/vibe-prospecting/SKILL.md)                                |
| Open-source MCP server                  | [vibeprospecting-mcp](https://github.com/explorium-ai/vibeprospecting-mcp)  |


---



## Security and data handling

- Sign-in is handled through your [Vibe Prospecting](https://www.vibeprospecting.ai/) account. CLI hosts store credentials locally under `~/.config/vpai`; Cowork and Claude Chat use the connector auth flow instead.
- All data queries are routed through Explorium's API infrastructure. Data is subject to [Explorium's data terms](https://explorium.ai) and your account permissions.
- Do not include raw API keys or credentials in prompts or exported files.
- For enterprise data handling, compliance, and DPA questions, contact [Explorium](https://explorium.ai).

---



## Troubleshooting


| Issue                                | Likely cause                                | Resolution                                                                                    |
| ------------------------------------ | ------------------------------------------- | --------------------------------------------------------------------------------------------- |
| Plugin not recognized in Claude Code | Installation not complete                   | Follow [`docs/install-claude-code.md`](docs/install-claude-code.md), then restart Claude Code |
| Plugin not recognized in Codex       | Installation not complete                   | Follow [`docs/install-codex.md`](docs/install-codex.md)                                       |
| Connector tools missing              | Connector not connected                     | Follow [`docs/install-claude-cowork.md`](docs/install-claude-cowork.md) or [`docs/install-claude-chat.md`](docs/install-claude-chat.md) |
| Authentication error                 | Expired session or missing credentials      | Re-auth using your platform install guide                                                     |
| Empty results                        | Filters too narrow or no matches            | Broaden ICP criteria or reduce required filters                                               |
| Low email match rate                 | Contacts found without verified work emails | Request enrichment with a confidence threshold; email availability varies                     |
| Slow workflow                        | Large result sets or multi-step enrichment  | Reduce batch size or break workflow into smaller steps                                        |


---



## Learn more


| Resource                           | Link                                                                                                                   |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Product and site                   | [vibeprospecting.ai](https://vibeprospecting.ai)                                                                       |
| Explorium data platform            | [explorium.ai](https://explorium.ai)                                                                                   |
| Skill and tool reference           | [skills/vibe-prospecting/SKILL.md](skills/vibe-prospecting/SKILL.md)                                                   |
| Vibe Prospecting MCP (open source) | [github.com/explorium-ai/vibeprospecting-mcp](https://github.com/explorium-ai/vibeprospecting-mcp)                     |
| npm package                        | [@vibeprospecting/vpai](https://www.npmjs.com/package/@vibeprospecting/vpai)                                           |
| Email support                      | [support@vibeprospecting.ai](mailto:support@vibeprospecting.ai)                                                        |
| GitHub Issues                      | [github.com/explorium-ai/vibeprospecting-plugin/issues](https://github.com/explorium-ai/vibeprospecting-plugin/issues) |
| License                            | MIT — [LICENSE](https://github.com/explorium-ai/vibeprospecting-plugin/blob/main/LICENSE)                              |


---

Vibe Prospecting Plugin is built and maintained by [Explorium](https://explorium.ai). It connects Claude Code, Claude Cowork, Claude Chat, OpenAI Codex, OpenClaw, and other agent hosts to Explorium's B2B data platform for GTM teams, AI agents, and revenue operations workflows.