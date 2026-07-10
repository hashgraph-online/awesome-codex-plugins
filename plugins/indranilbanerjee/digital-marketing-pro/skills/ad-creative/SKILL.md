---
name: ad-creative
description: "Generate platform-specific ad copy. Use when: Google RSA, Meta, LinkedIn, TikTok ad variations with quality scoring."
argument-hint: "[platform]"
---

# /digital-marketing-pro:ad-creative

## Purpose

Generate high-performing ad copy variations tailored to specific platforms and formats. Each variation is scored for quality and compliance, with recommendations for testing strategy.

## Input Required

The user must provide (or will be prompted for):

- **Product/service**: What is being advertised
- **Platform(s)**: Google Ads, Meta (Facebook/Instagram), LinkedIn, TikTok, X, Pinterest
- **Ad format**: RSA, single image, carousel, video script, story, etc.
- **Campaign objective**: Awareness, traffic, leads, conversions, app installs
- **Target audience**: Who the ads are for
- **Key offer/CTA**: Promotion, value prop, or desired action
- **Landing page URL**: Where the ad will drive traffic (optional)

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. Identify platform-specific constraints: character limits, format requirements, policy restrictions
3. Generate 3-5 ad copy variations per platform, each with a distinct angle (benefit, urgency, social proof, curiosity, direct)
4. Score each variation on: brand alignment, clarity, emotional impact, CTA strength, policy compliance
5. Flag any potential policy violations (restricted claims, prohibited language)
6. Recommend A/B testing groupings and priority order
7. If landing page URL is provided, check message match between ad and page

## Output

Per platform, a set of ad copy variations including:

- Headlines, descriptions, and CTAs formatted to platform specifications
- Quality score (1-10) with reasoning per variation
- Policy compliance check with flagged issues
- A/B testing recommendation with hypothesis for each test
- Message match assessment (if landing page provided)
- Creative direction notes for visual/video assets (see AI image/video generation guidance below)

### AI image & video generation guidance (May 2026)

When the brief includes static visuals or short-form video, recommend the model that fits the use case and call out the compliance overhead:

| Asset type | Recommended model (May 2026) | When to use | Compliance note |
|---|---|---|---|
| Product hero stills, lifestyle photography, e-commerce tiles | **Google Nano Banana Pro** (Gemini 2.5 Image, multi-image composition, character/object consistency) | Strong text rendering inside images (logos, on-pack copy), brand-character consistency across a campaign, high-fidelity product realism. | Outputs ship with SynthID watermarking by default; ALSO sign with C2PA via `/digital-marketing-pro:c2pa-metadata` before any EU distribution. |
| Short-form social video (≤8s reels, organic vertical) | **Gemini Veo 3.1** (synchronized native audio, longer/more coherent clips than Veo 3.0) | Reels, TikTok, Shorts cut-downs, ad-creative experimentation. | Synthetic-voice / synthetic-human content must carry a visible deepfake disclosure under EU Article 50 — see `skills/context-engine/compliance-rules.md` §1.1b. |
| Long-form video with native audio / multi-modal storytelling | **Gemini Omni** (multimodal generation, May 2026 I/O launch — text + image + audio + video unified) | Connected-content campaigns where a single brief produces a hero film, social cut-downs, audio version, and stills consistently. Best for brands with disciplined creative governance — Omni's range outpaces most brand-safety review processes. | Default Omni outputs carry SynthID + Gemini provenance markers. Add C2PA before EU publish. Run synthetic-person outputs past Legal — Omni's photoreal humans frequently hit "substantial AI manipulation" thresholds under Article 50. |
| Static image — fast iteration / mood-boarding | OpenAI gpt-image-1, Midjourney v7, Adobe Firefly | Internal mood boards, concept exploration. Not for shipped EU creative without C2PA. | None of these auto-embed C2PA — manually sign with `/digital-marketing-pro:c2pa-metadata` before EU publish. |

**Workflow recommendation:**

1. Brief the visual concept in this skill's output (subject, composition, brand-character constraints, on-pack text if any).
2. Hand the visual spec to whichever production track owns image/video — typically **SocialForge** (`/socialforge:compose-creative` for stills, `/socialforge:generate-video` for short-form, with Vertex AI / Nano Banana / Veo wired up via `/socialforge:setup`) or an external creative team.
3. Treat all AI-generated visuals as **Article 50 in-scope** until proven otherwise. The pre-publish gate (`/digital-marketing-pro:check`) blocks unsigned AI assets for EU-targeted campaigns.

## Agents Used

- **content-creator** — Ad copy generation, angle development, CTA crafting
- **media-buyer** — Platform specs, policy compliance, testing strategy
- **brand-guardian** — Voice alignment, compliance review, claim verification
