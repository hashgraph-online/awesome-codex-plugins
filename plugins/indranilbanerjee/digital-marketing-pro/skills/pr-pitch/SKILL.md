---
name: pr-pitch
description: "Create media pitch packages. Use when: building pitch templates, media lists, outreach strategy, or HARO responses."
argument-hint: "[topic or news-hook]"
---

# /digital-marketing-pro:pr-pitch

## Purpose

Create compelling media pitch packages designed to earn coverage. Includes pitch templates customized by outlet type, target media identification, outreach sequencing, and journalist-ready materials.

## Input Required

The user must provide (or will be prompted for):

- **Story angle**: What is newsworthy (launch, data, trend, expert commentary, milestone)
- **Pitch type**: Proactive pitch, reactive (newsjacking), journalist-request-platform response (e.g., Qwoted, Featured, Source of Sources), or thought leadership placement
- **Target outlets**: Desired publications or tier level (Tier 1 national, trade, local, podcasts)
- **Spokesperson**: Who speaks for the brand, their credentials and availability
- **Supporting assets**: Data, quotes, images, press releases, case studies available
- **Timing**: Embargo dates, event tie-ins, or urgency level

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. Identify the core news hook and refine the angle for maximum editorial appeal
3. Craft pitch templates tailored to outlet type (national, trade, broadcast, podcast, newsletter)
4. Build a target media list with journalist names, beats, outlets, and contact approach
5. Design an outreach sequence: initial pitch, follow-up timing, alternative angles
6. Prepare supporting materials: press release draft, fact sheet, quote bank, boilerplate
7. If responding to a journalist request platform (e.g., Qwoted, Featured, Source of Sources): craft a source response optimized for journalist selection criteria
8. Review all materials for brand voice consistency and factual accuracy

## Output

A complete PR pitch package containing:

- Core pitch template (email-ready) with subject line options
- Outlet-specific pitch variations (3-5 versions)
- Target media list with journalist details and pitch approach notes
- Outreach timeline with follow-up cadence
- Press release or media advisory draft
- Fact sheet and quote bank
- HARO response template (if applicable)
- Measurement framework: coverage tracking, share of voice, backlink value

## Agents Used

- **pr-outreach** — Pitch crafting, media targeting, outreach strategy, journalist relations
