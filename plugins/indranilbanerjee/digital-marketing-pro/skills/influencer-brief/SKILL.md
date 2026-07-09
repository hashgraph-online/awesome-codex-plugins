---
name: influencer-brief
description: "Create influencer campaign briefs. Use when: setting creator criteria, FTC compliance, or measurement plans."
argument-hint: "[campaign-objective]"
---

# /digital-marketing-pro:influencer-brief

## Purpose

Create a complete influencer campaign brief that covers creator discovery criteria, content guidelines, compliance requirements, compensation framework, and performance measurement.

## Input Required

The user must provide (or will be prompted for):

- **Campaign objective**: Awareness, engagement, conversions, content generation, or event promotion
- **Product/service**: What the influencer will promote
- **Target audience**: Who the campaign should reach
- **Platform(s)**: Instagram, TikTok, YouTube, X, LinkedIn, podcasts
- **Budget**: Total influencer budget or per-creator range
- **Creator tier**: Nano (1-10K), Micro (10-100K), Mid (100K-500K), Macro (500K-1M), Mega (1M+)
- **Timeline**: Campaign dates and content delivery deadlines
- **Content type**: Posts, stories, reels, videos, reviews, unboxing, tutorials, live streams

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. Define creator discovery criteria: niche, audience demographics, engagement rate minimums, brand safety filters, aesthetic alignment
3. Build the creator brief: campaign overview, key messages, creative freedom boundaries, required and prohibited elements, hashtags, disclosures
4. Draft compensation framework: flat fee, performance bonus, affiliate commission, product gifting, or hybrid
5. Create content approval workflow: draft review, revision rounds, posting timeline
6. Build FTC/ASA compliance checklist: disclosure requirements, claim restrictions, platform-specific rules
7. Define usage rights: organic only, paid amplification, repurposing, duration
8. Set measurement framework: reach, engagement, clicks, conversions, CPE, EMV

## Output

A structured influencer campaign brief containing:

- Campaign overview with objectives and success metrics
- Creator discovery criteria and ideal profile description
- Creator brief document (shareable with influencers)
- Key messaging framework with creative guardrails (including any AI-tool restrictions — see below)
- Compensation structure and negotiation guidelines
- Content approval and revision process
- FTC/ASA compliance checklist with required disclosures
- Usage rights and licensing terms
- Measurement dashboard with KPIs and reporting cadence

### AI-tool clauses for creator briefs (May 2026)

Creators increasingly use AI image/video tools (Nano Banana Pro, Gemini Omni, Veo 3.1, Kling v3.0 Pro, Runway Gen-4, Midjourney; **note:** OpenAI's consumer Sora app was discontinued 26 Apr 2026 and the Sora API ends 24 Sep 2026 — do not specify Sora in new briefs) inside sponsored content. The brief must spell out three things to keep the brand safe:

1. **Permitted AI use**: Allowed for B-roll, mood, and stylised visuals. **Not permitted for** synthetic depictions of real people (including the creator themselves in altered form), synthetic product imagery that misrepresents the brand's actual product, or AI-generated voiceover impersonating a real person without explicit release.
2. **Required disclosures**: Any AI-generated visual or audio in the sponsored content must (a) be flagged in the creator's platform-native AI disclosure (TikTok AI label, Meta AI Content label, YouTube "altered or synthetic content" toggle) AND (b) carry C2PA Content Credentials if the creator ships the file to the brand for paid amplification — provide `/digital-marketing-pro:c2pa-metadata` workflow link in the brief.
3. **EU deepfake clause** (mandatory for EU-distributed campaigns): Synthetic-human content (face swaps, AI voices resembling real people, AI-cloned likeness) must carry a visible deepfake disclosure perceivable at normal viewing distance. See `skills/context-engine/compliance-rules.md` §1.1b.i (Article 50 draft guidelines, May 2026). Creators who refuse this clause should not be cleared for EU placements.

## Agents Used

- **influencer-manager** — Creator strategy, brief development, compliance, measurement, campaign architecture
