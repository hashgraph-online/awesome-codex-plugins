---
name: video-script
description: "Write a production-ready video script — 3 hook variants, timestamped dialogue with visual and audio direction columns, CTA placement map, retention notes, accessibility package, and thumbnail concepts. Detects whether the script is organic or an ad: organic scripts declare a search/browse discovery intent, ad scripts inherit objective, audience, and offer from campaign context and follow per-format rules (6s bumper, 15s skippable, 30s spot, UGC-style with disclosure). Triggers on \"/digital-marketing-pro:video-script\", \"write a YouTube script about X\", \"script a 15-second ad\", \"TikTok video for our launch\", \"explainer video script\". Reads the brand profile and campaign briefs; every script passes the /digital-marketing-pro:check gate before delivery."
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
2.4. **Identify the script class — organic or ad — and load campaign context**: These are different disciplines with different physics. **Organic** content earns its audience (discovery intent, step 2.5). **Ads** buy theirs, so the craft is about what happens inside a paid, often skippable slot. If this script belongs to a campaign, read the campaign context first — `~/.claude-marketing/brands/{slug}/campaigns/` and any campaign-plan output — so the script inherits the campaign's objective, funnel stage, audience, and offer instead of inventing parallel ones. A mid-funnel retargeting ad and a cold-audience awareness ad are different scripts for the same product; the campaign brief decides which one this is.

For ad scripts, apply the format's structural rules:
   - **6s bumper (unskippable)**: ONE message, no arc — there is no time to earn attention, only to land a single point. Brand visible by second 2. If the brief has two messages, that is two bumpers.
   - **15s skippable**: the skip button appears at 5s — the script's real deadline. The hook and the core message both land BEFORE it; everything after is for the viewers who chose to stay. A 15s script that saves its point for second 9 was, for most of its audience, a 5-second logo exposure.
   - **30s spot**: room for one arc (PAS or before/after), still front-loaded — assume drop-off at every second, pay off early and again late.
   - **UGC-style / native ad**: reads as platform-native content, disclosed as an ad per FTC/ASA rules — native-feeling is a style, not a disclosure exemption. Hook physics match organic; compliance rules match ads.
2.5. **Declare the discovery intent** (organic scripts): State how this video gets found — **Search** (typed queries; ranks over months; the topic phrasing must match how people actually search — pull it from /digital-marketing-pro:keyword-research), **Browse** (suggested/home feeds; lives or dies on click-through and early retention), or **Both**. A video with no search or browse logic has no discovery reason, and no script fixes that — send the topic back to development rather than producing a well-made video nobody will be shown. The intent drives everything downstream: search videos front-load the query answer; browse videos spend more on the open. (Ad scripts skip this step — distribution is bought, and step 2.4's format rules govern instead.)
3. **Select script structure**: Choose the optimal narrative framework based on video type and goals — AIDA (Attention-Interest-Desire-Action), PAS (Problem-Agitate-Solution), problem-solve-CTA, storytelling arc (setup-tension-resolution), listicle, before/after, or direct response. Justify the choice based on audience awareness level and platform norms. **For long-form: every body section must carry its own payoff — a point delivered, not just promised. No section ends on setup; a section that only sets up the next one is where viewers leave, so either give it a payoff or fold it into the section that has one.**
4. **Write 3 hook variants**: Craft three distinct opening hooks for the first 3 seconds — each using a different hook technique (bold claim, question, visual shock, pattern interrupt, relatable pain point, or curiosity gap). Provide rationale for why each hook works for the target audience and platform.
5. **Draft full script with timestamps**: Write the complete script with second-by-second or scene-by-scene timestamps. Include speaker dialogue or voiceover lines, pause beats, transition cues, and pacing notes. Ensure the script hits the target duration within a 10% margin.
6. **Add visual direction notes**: Create a visual column alongside the script specifying camera angles (wide, medium, close-up, overhead), b-roll suggestions, graphics and text overlay placements, transitions (cut, dissolve, swipe), product shots, and screen recordings where applicable.
7. **Place CTAs at optimal points**: Position call-to-action moments at strategically timed intervals based on video length — verbal CTA, on-screen CTA overlay, end card CTA, and pinned comment CTA. For shorter videos, place a single CTA at the natural climax; for longer videos, use a soft mid-roll CTA and a strong end CTA.
8. **Add accessibility notes**: Write a closed caption script ensuring all spoken content and meaningful sound effects are transcribed. Include audio description notes for key visual-only moments. Specify caption styling (font size, positioning, background contrast) per platform requirements.
9. **Create thumbnail and cover frame concept**: Design a thumbnail concept for YouTube or a cover frame for Reels/TikTok — specify text overlay (1-3 words; 7 absolute max), facial expression or product shot, color treatment, and contrast elements that drive click-through. Include 2 thumbnail variant ideas for A/B testing. **Apply the pairing rule: the title carries context and keywords for the platform's systems; the thumbnail text carries the tension a human reacts to — they never say the same thing, and any thumb word that already appears in the title is rejected as wasted real estate.** For dedicated packaging work or a critique of an underperforming video, use /digital-marketing-pro:video-packaging.
10. **Review against brand voice and platform best practices**: Audit the complete script against brand voice settings, compliance requirements, and platform content policies. Flag any potential issues with claims, disclosures, music licensing, or platform-specific restrictions. Verify pacing matches platform consumption patterns.
11. **Run the unified quality gate before delivery**: Route the finished script's narration and on-screen text through /digital-marketing-pro:check — the same hallucination + brand-voice + claims gate every other deliverable passes. A spoken statistic is the same liability as a printed one, and a rendered video is harder to correct than any page. For ad scripts this gate is non-negotiable: paid distribution multiplies whatever the script gets wrong, and ad platforms adjudicate claims complaints against the advertiser, not the agency.

## Output

A structured video script package containing:

- **3 hook variants** with rationale explaining the technique used and expected audience response for each
- **Full script with timestamps** — second-by-second or scene-by-scene timing from open to end card
- **Visual direction column** specifying what the viewer sees at each timestamp — camera angles, b-roll, graphics, text overlays, transitions, and product shots
- **Audio direction column** covering voiceover delivery notes, background music cues (genre, energy, licensing notes), sound effects, and silence beats
- **On-screen text callouts** with exact copy, timing, positioning, font size guidance, and animation style
- **CTA placement map** with timing rationale — why each CTA appears where it does based on viewer retention curves
- **Retention notes** — for long-form: the 2-3 points where viewers are most likely to drop (the setup stretch, the mid-video sag, the pre-CTA fade) and the specific hold at each — a re-hook, an open loop paid off later, a pattern interrupt. Naming the sag points is the difference between a script that reads well and one that retains; a script with no identified risk points has not been read as a viewer.
- **Platform-specific formatting notes** — aspect ratio, duration compliance, safe zones, caption areas, and algorithm optimization tips
- **Accessibility package** — closed caption script, audio description notes, and caption styling specifications
- **Thumbnail/cover frame concept** — 2 variant ideas with text overlay, imagery, color treatment, and click-through optimization rationale
- **Production notes** — talent requirements, location suggestions, props and wardrobe, equipment recommendations, and lighting direction
- **Estimated production complexity** rating (low/medium/high) with justification based on required assets, talent, locations, and post-production
- **Alternative cut guidance** — how to create a shorter or longer version from the same shoot, specifying which sections to cut or expand

## Agents Used

- **content-creator** — Script writing, hook development, narrative structure, visual and audio direction, CTA placement, accessibility scripting, thumbnail concept, brand voice alignment, and platform-specific formatting
