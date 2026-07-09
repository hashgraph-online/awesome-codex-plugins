---
name: campaign-plan
description: "Build multi-channel campaign plans. Use when: objectives, audience targeting, channel mix, budget, timeline, KPIs."
argument-hint: "[campaign-objective]"
---

# /digital-marketing-pro:campaign-plan

## Purpose

Generate a comprehensive multi-channel campaign plan ready for execution. Covers strategic objectives, audience segmentation, channel selection, budget distribution, phased timeline, and measurable KPIs.

## Input Required

The user must provide (or will be prompted for):

- **Campaign goal**: What the campaign should achieve (awareness, leads, sales, retention, etc.)
- **Product/service**: What is being promoted
- **Target audience**: Who the campaign is for (or use existing brand personas)
- **Budget**: Total available budget or budget range
- **Timeline**: Campaign duration or key dates (launch, event, season)
- **Constraints**: Any channel restrictions, compliance requirements, or creative limitations

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. Clarify campaign objective and classify as awareness, consideration, or conversion
3. Define primary and secondary audience segments with targeting parameters
4. Recommend channel mix based on audience behavior, budget, and objective
5. Allocate budget across channels using expected CPM/CPC benchmarks for the industry
6. Build a phased timeline: pre-launch, launch, sustain, optimize, wrap-up
7. Define KPIs per channel and overall campaign success metrics
8. Identify dependencies, risks, and contingency actions
9. Output the full plan in a structured, actionable format

## Output

A structured campaign plan document containing:

- Campaign overview and SMART objectives
- Audience segments with targeting criteria
- Channel strategy with rationale for each channel
- Budget allocation table with expected reach/cost estimates
- Phased timeline with milestones and deliverables
- KPI dashboard framework with targets and measurement approach
- Risk register with mitigation strategies

## Agents Used

- **marketing-strategist** — Campaign architecture, audience strategy, objective setting
- **media-buyer** — Channel selection, budget allocation, performance benchmarks
