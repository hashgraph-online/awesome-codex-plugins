---
name: martech-audit
description: "Audit the martech stack. Use when: evaluating marketing tools, recommending consolidation, or choosing between platforms."
---

# /digital-marketing-pro:martech-audit

## Purpose

Evaluate the current marketing technology stack for gaps, overlaps, integration issues, and optimization opportunities. Produces a comprehensive stack assessment with actionable consolidation and upgrade recommendations tied to ROI projections and implementation feasibility.

## Input Required

The user must provide (or will be prompted for):

- **Current tools/platforms**: List of marketing tools in use, organized by category if possible (e.g., CRM: Salesforce, Email: Mailchimp)
- **Budget for martech**: Current annual martech spend and available budget for changes or additions
- **Team size and technical skill level**: How many people use the stack, their roles, and technical proficiency (beginner, intermediate, advanced)
- **Primary marketing goals**: What the stack needs to support (lead gen, e-commerce, content marketing, ABM, retention, etc.)
- **Pain points with current stack**: Known issues, bottlenecks, manual workarounds, data silos, or team frustrations
- **Growth plans**: Expected team or business growth that may affect stack requirements in the next 12-18 months
- **Compliance requirements**: Any data privacy, security, or regulatory constraints (GDPR, HIPAA, SOC 2, etc.)
- **Integration priorities**: Which tools absolutely must talk to each other (e.g., CRM-to-email, ads-to-analytics)
- **Evaluation scope**: Full stack audit or focused assessment of specific categories (e.g., just analytics, just automation)

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Map current stack to marketing functions**: Categorize every tool across 11 core functions — CRM, email/marketing automation, analytics/BI, paid advertising, social media management, CMS, attribution/tracking, data/CDP, content creation, SEO, and customer support
3. **Identify gaps**: Flag marketing functions with no tool coverage, assess the business impact of each gap, and recommend solutions at multiple price points
4. **Identify overlaps**: Detect multiple tools serving the same function, quantify redundant license costs, and estimate wasted spend from feature duplication
5. **Assess integration quality**: Evaluate data flow between tools — native integrations, API connections, middleware (Zapier, Make), manual CSV transfers, and isolated data silos that break reporting
6. **Benchmark against industry stack patterns**: Compare the stack composition, tool count, and spend-per-employee against industry norms for the brand's size, vertical, and growth stage
7. **Evaluate cost-per-function efficiency**: Calculate what each marketing function costs to operate factoring tool fees, team time overhead, integration maintenance, and training costs
8. **Score stack maturity**: Rate overall stack maturity on a 5-level scale (manual, basic, integrated, optimized, intelligent) with specific criteria for advancement
9. **Recommend consolidation or additions**: Propose specific tool swaps, upgrades, or additions with rationale — prioritized by impact, implementation effort, and team readiness
10. **Assess future-readiness**: Evaluate whether the current or proposed stack can support the brand's growth plans, emerging channels (AI, conversational, video), and evolving privacy requirements
11. **Create migration/implementation roadmap**: Phase recommendations into immediate wins (0-30 days), short-term changes (1-3 months), and strategic shifts (3-12 months) with risk mitigation and rollback plans for each transition

## Output

A structured martech audit report containing:

- **Stack map**: Visual matrix of current tools mapped to marketing functions showing coverage, gaps, and overlaps
- **Gap analysis**: Uncovered functions with recommended solutions at multiple price points and priority ranking
- **Overlap analysis**: Redundant tools with consolidation recommendations, projected savings, and migration complexity
- **Integration assessment**: Data flow diagram, integration health scores, silo identification, and middleware dependencies
- **Cost analysis**: Per-function cost breakdown comparing current spend to optimized spend with annual savings projection
- **Stack maturity score**: Current maturity level with specific actions needed to reach the next level
- **Recommended changes**: Prioritized list of additions, removals, and replacements with ROI estimates and payback periods
- **Vendor comparison notes**: For recommended new tools, brief comparison of top 2-3 options with pros/cons
- **Implementation roadmap**: Phased migration plan with timelines, dependencies, risk factors, training needs, and rollback plans
- **Future-readiness assessment**: How well the recommended stack supports growth plans, emerging channels, and evolving privacy regulations
- **Quick wins summary**: Top 3 changes that deliver the most impact with the least effort — for executive stakeholder buy-in

## Agents Used

- **marketing-strategist** — Stack strategy alignment with business goals, function prioritization, industry benchmarking, maturity assessment
- **analytics-analyst** — Integration assessment, data flow analysis, measurement infrastructure evaluation, attribution stack review
