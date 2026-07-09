---
name: help
description: "Show the getting started guide, available commands, examples, and help for Digital Marketing Pro"
argument-hint: "[--commands | --examples | --troubleshoot]"
---

# /digital-marketing-pro:help

Show the Digital Marketing Pro getting started guide with setup instructions, available commands, usage examples, and troubleshooting.

## Behavior

When invoked, display a structured help overview with the following sections. Use the reference documentation in `docs/getting-started.md` for full details.

### 1. Quick Start Summary

Display this quick orientation:

```
=== DIGITAL MARKETING PRO — HELP ===

Version: 2.7.0
Agents: 25 specialist agents
Skills: 141 slash commands (/digital-marketing-pro:*) — all with argument-hint autocomplete
Modules: 16 marketing knowledge domains
Connectors: 14 HTTP + 68 npx integrations

Getting Started:
  1. /digital-marketing-pro:brand-setup        — Create your brand profile (start here)
  2. /digital-marketing-pro:import-guidelines   — Import voice guides, restrictions, templates
  3. /digital-marketing-pro:integrations        — See which connectors are active
  4. /digital-marketing-pro:connect <name>      — Set up a new connector
  5. Just ask!               — Describe what you need in natural language
```

### 2. Arguments

| Argument | Effect |
|----------|--------|
| (none) | Show the full help overview |
| `--commands` | List all 117 slash commands grouped by category |
| `--connectors` | Show connector status (shortcut for /digital-marketing-pro:integrations) |
| `--brand` | Show current brand profile summary |
| `--examples` | Show 10 example prompts across different marketing tasks |
| `--troubleshoot` | Show common issues and solutions |

### 3. Commands by Category

When `--commands` is specified, group all commands into these categories:

| Category | Example Commands |
|----------|-----------------|
| **Brand Management** | `/digital-marketing-pro:brand-setup`, `/digital-marketing-pro:switch-brand`, `/digital-marketing-pro:import-guidelines` |
| **Strategy & Planning** | `/digital-marketing-pro:campaign-plan`, `/digital-marketing-pro:launch-plan`, `/digital-marketing-pro:social-strategy`, `/digital-marketing-pro:media-plan` |
| **Content Creation** | `/digital-marketing-pro:content-brief`, `/digital-marketing-pro:email-sequence`, `/digital-marketing-pro:ad-creative`, `/digital-marketing-pro:video-script` |
| **SEO & Technical** | `/digital-marketing-pro:seo-audit`, `/digital-marketing-pro:tech-seo-audit`, `/digital-marketing-pro:keyword-research`, `/digital-marketing-pro:aeo-audit` |
| **Analytics & Reporting** | `/digital-marketing-pro:performance-report`, `/digital-marketing-pro:roi-calculator`, `/digital-marketing-pro:attribution-model` |
| **Paid Advertising** | `/digital-marketing-pro:media-plan`, `/digital-marketing-pro:launch-ad-campaign`, `/digital-marketing-pro:budget-optimizer` |
| **Social Media** | `/digital-marketing-pro:social-strategy`, `/digital-marketing-pro:schedule-social`, `/digital-marketing-pro:content-calendar` |
| **Email Marketing** | `/digital-marketing-pro:email-sequence`, `/digital-marketing-pro:send-email-campaign` |
| **CRM & Data** | `/digital-marketing-pro:crm-sync`, `/digital-marketing-pro:lead-import`, `/digital-marketing-pro:pipeline-update`, `/digital-marketing-pro:data-export` |
| **Competitive Intelligence** | `/digital-marketing-pro:competitor-analysis`, `/digital-marketing-pro:competitor-monitor`, `/digital-marketing-pro:share-of-voice` |
| **PR & Outreach** | `/digital-marketing-pro:pr-pitch`, `/digital-marketing-pro:influencer-brief`, `/digital-marketing-pro:crisis-response` |
| **Audience** | `/digital-marketing-pro:audience-profile`, `/digital-marketing-pro:focus-group`, `/digital-marketing-pro:segment-audience` |
| **CRO & Growth** | `/digital-marketing-pro:landing-page-audit`, `/digital-marketing-pro:funnel-audit`, `/digital-marketing-pro:ab-test-plan` |
| **Quality & Evaluation** | `/digital-marketing-pro:eval-content`, `/digital-marketing-pro:verify-claims`, `/digital-marketing-pro:quality-report` |
| **Multilingual** | `/digital-marketing-pro:translate-content`, `/digital-marketing-pro:localize-campaign`, `/digital-marketing-pro:language-config` |
| **Execution & Publishing** | `/digital-marketing-pro:publish-blog`, `/digital-marketing-pro:send-email-campaign`, `/digital-marketing-pro:launch-ad-campaign` |
| **Monitoring** | `/digital-marketing-pro:performance-check`, `/digital-marketing-pro:anomaly-scan`, `/digital-marketing-pro:budget-tracker` |
| **Connector Discovery** | `/digital-marketing-pro:integrations`, `/digital-marketing-pro:connect`, `/digital-marketing-pro:add-integration` |
| **Agency Operations** | `/digital-marketing-pro:agency-dashboard`, `/digital-marketing-pro:client-report`, `/digital-marketing-pro:sop-library` |
| **Memory & Knowledge** | `/digital-marketing-pro:save-knowledge`, `/digital-marketing-pro:search-knowledge`, `/digital-marketing-pro:sync-memory` |

### 4. Example Prompts

When `--examples` is specified, show these real-world examples:

```
Getting Started:
  /digital-marketing-pro:brand-setup
  → Create your brand profile interactively (5 quick questions or 17 detailed)

Strategy:
  "Plan a product launch for our new cold brew line"
  → Activates Campaign Orchestrator with your brand context

Content:
  "Write a 3-email welcome sequence for new subscribers"
  → Creates emails in your brand voice with compliance rules applied

SEO:
  /digital-marketing-pro:seo-audit https://example.com
  → Full technical + content + E-E-A-T audit with action items

Competitive:
  /digital-marketing-pro:competitor-analysis "Blue Bottle, Counter Culture, Stumptown"
  → Multi-dimensional analysis: content, SEO, ads, social, positioning

Paid Ads:
  /digital-marketing-pro:media-plan --budget=50000 --channels="google,meta,linkedin"
  → Channel allocation, flight schedule, creative rotation plan

Analytics:
  /digital-marketing-pro:performance-check
  → Pull live metrics from all connected platforms

Execution:
  /digital-marketing-pro:publish-blog --platform=wordpress --status=draft
  → Publish with SEO metadata, or export HTML for manual upload

AI Visibility:
  /digital-marketing-pro:aeo-audit
  → Check how your brand appears in ChatGPT, Perplexity, Google AI Overviews

Connectors:
  /digital-marketing-pro:connect hubspot
  → Step-by-step OAuth setup for HubSpot CRM connector
```

### 5. Troubleshooting

When `--troubleshoot` is specified, show common issues:

| Issue | Solution |
|-------|----------|
| "No active brand" message | Run `/digital-marketing-pro:brand-setup` to create your first brand profile |
| Python features unavailable | Install: `pip install nltk textstat` (lite mode) or full requirements.txt |
| MCP connector not working | Run `/digital-marketing-pro:integrations` to check status, `/digital-marketing-pro:connect <name>` for setup |
| Brand voice seems off | Run `/digital-marketing-pro:brand-setup --full` for detailed 17-question profiling |
| Commands not recognized | Ensure plugin is installed: check "Manage Plugin" in Cowork or `claude plugin list` |
| Session context missing | Brand context loads on SessionStart — start a fresh session |
| Google Drive not showing | Google Drive is a platform-level integration — check Claude Desktop → Settings → Integrations |

### 6. Skill Platform Features

When `--platform` argument is used or when showing the full help, include this section:

```
=== SKILL PLATFORM FEATURES ===

Argument Hints (55 skills):
  All user-invocable skills show autocomplete hints in the Skills UI.
  Example: /digital-marketing-pro:seo-audit shows [URL]
  Example: /digital-marketing-pro:campaign-plan shows [product/service --budget=N]

Execution Safety (17 skills):
  Skills that write to external platforms require explicit user invocation.
  Claude cannot auto-trigger: publish-blog, send-email-campaign,
  launch-ad-campaign, schedule-social, send-report, and 12 more.
  This works alongside the MCP write approval hook.

Quality Evals (3 skills):
  campaign-plan, seo-audit, and content-engine have evals/evals.json
  with structured test cases for quality benchmarking.
```

### 7. Documentation References

Point users to these resources for deeper dives:

| Guide | What it covers |
|-------|---------------|
| `docs/getting-started.md` | Full setup walkthrough with examples |
| `docs/brand-guidelines.md` | Importing voice guides, restrictions, templates |
| `docs/integrations-guide.md` | Connecting marketing tools (67 integrations) |
| `docs/multi-brand-guide.md` | Agency workflows, brand switching |
| `docs/strategy-and-kpis.md` | KPI frameworks, reporting dashboards |
| `docs/architecture.md` | Technical deep dive: modules, agents, hooks |
| `docs/claude-interfaces.md` | Cowork-specific capabilities |
| `docs/competitor-intelligence.md` | Competitive monitoring setup |
| `docs/cross-channel-sync.md` | Cross-channel campaign coordination |
| `CONNECTORS.md` | All available connectors by category |

## Output Format

Present information in clean, scannable tables and code blocks. Keep the output concise — this is a quick reference, not a tutorial. Link to the full documentation for detailed walkthroughs.
