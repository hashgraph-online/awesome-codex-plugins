---
name: content-brief
description: "Create detailed content briefs. Use when: keyword targets, outline, structure, voice guidelines, SEO requirements."
argument-hint: "[topic]"
---

# /digital-marketing-pro:content-brief

## Purpose

Create a production-ready content brief that a writer can execute without additional context. Includes keyword strategy, content outline, structural requirements, brand voice guidelines, and on-page SEO specifications.

## Input Required

The user must provide (or will be prompted for):

- **Topic or working title**: What the content is about
- **Content type**: Blog post, landing page, pillar page, guide, whitepaper, etc.
- **Target keyword(s)**: Primary keyword or topic cluster (or ask for research)
- **Target audience**: Who this content is for
- **Funnel stage**: Awareness, consideration, or decision
- **Competitive URLs**: Optional — existing content to outperform

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. Research keyword landscape: primary keyword, secondary keywords, related questions
3. Analyze top-ranking content for the target keyword to identify gaps and opportunities
4. Define content angle and unique value proposition versus existing results
5. Build a detailed outline with H2/H3 structure, key points per section, and word count targets
6. Specify on-page SEO requirements: title tag, meta description, URL slug, internal links, schema markup
7. Document voice and tone guidelines specific to this piece
8. Define success metrics: target ranking, traffic, engagement, conversions

## Output

A structured content brief containing:

- Target keyword map (primary, secondary, LSI, questions to answer)
- Content outline with heading hierarchy and key points per section
- Word count target and content format specifications
- Brand voice and tone guidance for this specific piece
- On-page SEO checklist (title, meta, headers, links, schema)
- Visual/media requirements — specify whether visuals are AI-generated and which model (see guidance below)
- Internal and external linking strategy
- Success metrics and measurement plan

### Visual/media spec — AI generation guidance (May 2026)

If the piece includes AI-generated images, infographics, or short video, the brief must specify:

- **Model**: `Nano Banana Pro` for high-fidelity stills with on-image text (best text rendering in any image model as of May 2026), `Gemini Omni` for connected hero-image + cutdown-video + audio packages, or alternatives (Midjourney, Firefly, gpt-image-1) for concept work.
- **Provenance marking**: All AI assets shipped to EU readers must carry C2PA Content Credentials. Default to "sign all AI visuals" — the cost of running `/digital-marketing-pro:c2pa-metadata` post-production is trivial vs the Article 50 penalty exposure.
- **Deepfake / synthetic-human flag**: If the visual includes a photoreal human (real or synthetic), call this out — synthetic humans typically need a visible disclosure under EU Article 50 draft guidelines (May 2026).
- **Editorial-responsibility owner**: For long-form on health, finance, elections, or public-safety topics, name the human editor who will sign off. AI-written copy on these topics requires the editorial-responsibility carve-out to skip an "AI-assisted" byline disclosure — see `skills/context-engine/compliance-rules.md` §1.1b.i.

## Agents Used

- **content-creator** — Outline structure, angle, voice guidelines, content strategy
- **seo-specialist** — Keyword research, on-page SEO requirements, competitive content analysis
