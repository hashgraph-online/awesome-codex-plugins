---
name: launch-plan
description: "Build product launch playbooks. Use when: planning pre-launch, launch day, or post-launch phases."
argument-hint: "[product-name]"
disable-model-invocation: true
---

# /digital-marketing-pro:launch-plan

## Purpose

Build a comprehensive launch playbook that coordinates all marketing activities across three phases — pre-launch, launch, and post-launch — to maximize impact and sustain momentum.

## Input Required

The user must provide (or will be prompted for):

- **What is launching**: Product, feature, service, rebrand, or event
- **Launch date**: Target date or date range
- **Launch goals**: Signups, revenue, coverage, awareness targets
- **Target audience**: Primary and secondary audiences for the launch
- **Available channels**: Which channels are active and resourced
- **Budget**: Dedicated launch budget (if any)
- **Assets available**: What already exists (product pages, demos, press materials, creative)
- **Team**: Who is involved and their roles

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. Define launch tier (Tier 1 major, Tier 2 moderate, Tier 3 minor) to calibrate effort
3. **Pre-launch phase** (T-30 to T-1): Teaser content, audience building, press seeding, influencer outreach, email list warming, landing page, waitlist
4. **Launch phase** (T-0 to T+3): Coordinated announcement across all channels, press release, email blast, social blitz, paid media activation, community engagement
5. **Post-launch phase** (T+4 to T+30): Performance monitoring, user feedback collection, content follow-up, retargeting, optimization, case studies
6. Build detailed timeline with owners, deliverables, and deadlines per task
7. Define success metrics per phase and overall launch KPIs
8. Identify risks and build contingency plans

## Output

A structured launch playbook containing:

- Launch overview with tier classification and success criteria
- Pre-launch checklist with timeline, deliverables, and owners
- Launch day runbook with hour-by-hour coordination plan
- Post-launch optimization plan with feedback loops
- Channel-by-channel activation plan with specific tactics
- Content and asset requirements list
- Risk register with contingency actions
- KPI dashboard with targets per phase

## Agents Used

- **marketing-strategist** — Launch architecture, phasing, goal setting, channel coordination
- **content-creator** — Launch messaging, content assets, announcement copy
- **pr-outreach** — Media strategy, press materials, influencer seeding
