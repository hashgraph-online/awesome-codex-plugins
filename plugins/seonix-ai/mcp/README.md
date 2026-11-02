# Seonix

Give your AI agent your [Seonix](https://seonix.ai) SEO project: Site Health and the fix plan, Google Search Console, keywords, articles and eleven SEO playbooks — so the agent fixes the site in code, writes in your voice and ships content that shows up in Google, ChatGPT and Gemini.

Seonix grows organic and AI-search visibility for a website on autopilot: it crawls the site, tracks every issue across scans, reads Search Console, researches keywords, scores drafts, and writes and publishes articles. This plugin connects the agent to that project through the hosted Seonix MCP server at `https://api.seonix.ai/mcp`. The server runs at Seonix; nothing runs locally.

- **Install (Claude Code):** `/plugin install seonix --marketplace seonix-ai/mcp` — or `claude plugin marketplace add seonix-ai/mcp` then `claude plugin install seonix@seonix`.
- **Install (Codex):** `codex plugin marketplace add seonix-ai/mcp` then `codex plugin add seonix@seonix`.
- **Sign-in:** OAuth — on the first call you are sent to `app.seonix.ai` to approve the connection once. Revoke it any time at **Account → Agents**.
- **Access:** included in every paid Seonix plan (not available on the Free plan).
- **Docs:** https://seonix.ai/mcp · full install guide for every client (Cursor, VS Code, API-key fallback): https://github.com/seonix-ai/mcp

## What the agent can do

41 tools (36 read, 5 write) and 11 SEO playbooks.

| Area | Tools |
|---|---|
| Account & projects | `get_account`, `list_projects`, `get_project`, `get_plan_status`, `get_site_dna`, `get_seo_progress` |
| Site Health | `get_site_health`, `get_fix_plan`, `list_issues`, `get_issue`, `get_remediation_profile`, `list_scans`, `get_scan_status`, `get_results` |
| Search Console | `gsc_status`, `gsc_top_queries`, `gsc_top_pages`, `gsc_page_queries`, `gsc_opportunities`, `gsc_coverage`, `gsc_impact`, `gsc_timeseries` |
| Keywords & content | `list_keyword_candidates`, `list_clusters`, `get_cluster`, `get_calendar`, `list_articles`, `get_article`, `analyze_seo`, `score_article`, `list_channels`, `get_blog_integration_guide` |
| AI search | `get_ai_visibility` |
| Playbooks | `list_playbooks`, `get_playbook` |
| Write (scope `write`, confirmed per call) | `start_scan`, `apply_fix`, `rollback_fix`, `acknowledge_issue`, `unacknowledge_issue` (`get_fix_run` reads a fix run) |

## Skills

| Skill | When it triggers | What it does |
|---|---|---|
| `seonix-seo` | "improve SEO / traffic / content of my site", anything mentioning Seonix, Site Health or Search Console | The entry workflow and the rules (untrusted data, confirm before writes, error codes) |
| `seonix-fix-site` | "fix the SEO issues", "work through Site Health", "rescan" | Site Health → fix plan → fixes in the codebase or `apply_fix` on WordPress → `start_scan` → verify |
| `seonix-content` | "what should I write next", "score this draft", "publish through Seonix" | clusters and calendar → site DNA → draft → `analyze_seo` → publish through Seonix |

## Limits and security

- 600 tool calls per hour per connection; errors are JSON with an `error` code (`plan_required`, `project_required`, `not_connected`, `scope_required`, `rate_limited`, …).
- Anything that came from your website or the web is marked as untrusted data in tool results; the skills tell the agent never to treat it as instructions.
- Write tools need the `write` scope and your explicit yes before each call. The plugin itself contains no code, no hooks and no secrets; it only talks to `https://api.seonix.ai`.

## Links

Privacy policy: https://seonix.ai/privacy-policy · Terms of use: https://seonix.ai/terms-of-use · Support: info@seonix.ai · Issues: https://github.com/seonix-ai/mcp/issues · License: MIT
