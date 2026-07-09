---
name: video-script
description: "Write video scripts. Use when: creating YouTube, TikTok, Reels, LinkedIn, demo, or explainer video content."
argument-hint: "[topic or format]"
---

# /digital-marketing-pro:video-script

## Purpose

Write a production-ready video marketing script with hook variants, timestamps, visual direction notes, CTA placement, and platform-specific formatting. Produces a complete script package ready for production with visual and audio columns, accessibility notes, and thumbnail concepts.

## Input Required

The user must provide (or will be prompted for):

- **Video type**: The format of the video — ad spot, explainer, testimonial, product demo, social short, educational tutorial, brand story, or event recap
- **Target platform**: Where the video will be published — YouTube, TikTok, Instagram Reels, LinkedIn, YouTube Shorts, Facebook, or multi-platform
- **Target length**: Desired duration — 15s, 30s, 60s, 90s, 2-3 min, 5-10 min, or long-form 10+ min
- **Key message or topic**: The core idea, value proposition, or subject matter the video must communicate
- **Call to action**: What the viewer should do after watching — visit URL, subscribe, purchase, sign up, download, follow, etc.
- **Target audience**: Who the video is for — demographics, psychographics, awareness level, and platform behavior
- **Brand tone**: Desired tone and energy level — professional, casual, humorous, inspirational, educational, urgent, or conversational
- **Available assets**: What production resources are available — on-camera talent, b-roll footage, product samples, graphics/animation capability, studio vs. location, screen recordings
- **Competitor video references**: Optional — links or descriptions of competitor or aspirational videos to benchmark against
- **Performance goals**: What success looks like — views, watch-through rate, click-through rate, conversions, engagement, or brand lift

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for custom templates at `~/.claude-marketing/brands/{slug}/templates/`. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Determine platform specs and format constraints**: Reference platform-specific requirements — aspect ratio (16:9, 9:16, 1:1), max duration, safe zones for text overlays, caption placement areas, and native content conventions. Apply platform algorithm preferences (e.g., TikTok favors native-feeling content, LinkedIn rewards professional storytelling, YouTube prioritizes watch time).
3. **Select script structure**: Choose the optimal narrative framework based on video type and goals — AIDA (Attention-Interest-Desire-Action), PAS (Problem-Agitate-Solution), problem-solve-CTA, storytelling arc (setup-tension-resolution), listicle, before/after, or direct response. Justify the choice based on audience awareness level and platform norms.
4. **Write 3 hook variants**: Craft three distinct opening hooks for the first 3 seconds — each using a different hook technique (bold claim, question, visual shock, pattern interrupt, relatable pain point, or curiosity gap). Provide rationale for why each hook works for the target audience and platform.
5. **Draft full script with timestamps**: Write the complete script with second-by-second or scene-by-scene timestamps. Include speaker dialogue or voiceover lines, pause beats, transition cues, and pacing notes. Ensure the script hits the target duration within a 10% margin.
6. **Add visual direction notes**: Create a visual column alongside the script specifying camera angles (wide, medium, close-up, overhead), b-roll suggestions, graphics and text overlay placements, transitions (cut, dissolve, swipe), product shots, and screen recordings where applicable.
7. **Place CTAs at optimal points**: Position call-to-action moments at strategically timed intervals based on video length — verbal CTA, on-screen CTA overlay, end card CTA, and pinned comment CTA. For shorter videos, place a single CTA at the natural climax; for longer videos, use a soft mid-roll CTA and a strong end CTA.
8. **Add accessibility notes**: Write a closed caption script ensuring all spoken content and meaningful sound effects are transcribed. Include audio description notes for key visual-only moments. Specify caption styling (font size, positioning, background contrast) per platform requirements.
9. **Create thumbnail and cover frame concept**: Design a thumbnail concept for YouTube or a cover frame for Reels/TikTok — specify text overlay (7 words max), facial expression or product shot, color treatment, and contrast elements that drive click-through. Include 2 thumbnail variant ideas for A/B testing.
10. **Review against brand voice and platform best practices**: Audit the complete script against brand voice settings, compliance requirements, and platform content policies. Flag any potential issues with claims, disclosures, music licensing, or platform-specific restrictions. Verify pacing matches platform consumption patterns.

## Output

A structured video script package containing:

- **3 hook variants** with rationale explaining the technique used and expected audience response for each
- **Full script with timestamps** — second-by-second or scene-by-scene timing from open to end card
- **Visual direction column** specifying what the viewer sees at each timestamp — camera angles, b-roll, graphics, text overlays, transitions, and product shots
- **Audio direction column** covering voiceover delivery notes, background music cues (genre, energy, licensing notes), sound effects, and silence beats
- **On-screen text callouts** with exact copy, timing, positioning, font size guidance, and animation style
- **CTA placement map** with timing rationale — why each CTA appears where it does based on viewer retention curves
- **Platform-specific formatting notes** — aspect ratio, duration compliance, safe zones, caption areas, and algorithm optimization tips
- **Accessibility package** — closed caption script, audio description notes, and caption styling specifications
- **Thumbnail/cover frame concept** — 2 variant ideas with text overlay, imagery, color treatment, and click-through optimization rationale
- **Production notes** — talent requirements, location suggestions, props and wardrobe, equipment recommendations, and lighting direction
- **Estimated production complexity** rating (low/medium/high) with justification based on required assets, talent, locations, and post-production
- **Alternative cut guidance** — how to create a shorter or longer version from the same shoot, specifying which sections to cut or expand

## Agents Used

- **content-creator** — Script writing, hook development, narrative structure, visual and audio direction, CTA placement, accessibility scripting, thumbnail concept, brand voice alignment, and platform-specific formatting
