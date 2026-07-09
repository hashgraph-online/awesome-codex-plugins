---
name: funnel-audit
description: "Audit funnel performance. Use when: finding drop-off points, conversion gaps, or stage bottlenecks."
argument-hint: "[funnel-stage or URL]"
---

# /digital-marketing-pro:funnel-audit

## Purpose

Analyze the complete customer acquisition and conversion funnel to identify where prospects drop off, why they disengage, and what changes will have the highest impact on overall conversion rate.

## Input Required

The user must provide (or will be prompted for):

- **Funnel stages**: The stages to analyze (or use standard: Awareness > Interest > Consideration > Intent > Purchase > Retention)
- **Funnel data**: Metrics per stage (traffic, leads, MQLs, SQLs, opportunities, customers) or qualitative description
- **Traffic sources**: Where visitors/leads originate
- **Conversion points**: Key actions at each stage (form fill, demo request, trial start, purchase)
- **Known pain points**: Any stages the user already suspects are underperforming
- **Tech stack**: CRM, analytics, and marketing automation tools in use

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. Map the current funnel with conversion rates between each stage
3. Benchmark stage-to-stage conversion rates against industry averages
4. Identify the biggest drop-off points and calculate revenue impact of each gap
5. Analyze potential causes per bottleneck: messaging, targeting, UX, timing, offer, follow-up
6. Evaluate lead quality signals — are the right people entering the funnel?
7. Assess nurture effectiveness at each stage
8. Model improvement scenarios: "If stage X improves by Y%, overall revenue increases by Z%"
9. Prioritize recommendations by revenue impact and implementation effort

## Output

A structured funnel audit containing:

- Funnel visualization with conversion rates per stage
- Industry benchmark comparison per stage
- Top 3 bottlenecks ranked by revenue impact
- Root cause analysis per bottleneck with supporting evidence
- Improvement scenarios with projected revenue impact
- Prioritized action plan with quick wins and strategic projects
- Measurement framework to track improvements

## Agents Used

- **marketing-strategist** — Funnel architecture, lead quality analysis, strategic recommendations
- **analytics-analyst** — Conversion data analysis, benchmarking, impact modeling
- **cro-specialist** — Conversion bottleneck diagnosis, A/B test recommendations, form and checkout optimization, statistical significance testing
