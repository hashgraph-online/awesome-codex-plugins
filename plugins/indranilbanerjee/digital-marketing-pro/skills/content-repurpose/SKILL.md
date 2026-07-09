---
name: content-repurpose
description: "Repurpose content across channels. Use when: blog-to-social, webinar-to-article, pillar derivatives, format adaptation."
---

# /digital-marketing-pro:content-repurpose

## Purpose

Take one piece of existing content and generate a comprehensive repurposing plan across multiple channels and formats. Produces derivative content pieces, a posting schedule, and platform-specific adaptations to maximize the ROI of every content investment.

## Input Required

The user must provide (or will be prompted for):

- **Original content**: The source material -- a URL, pasted text, uploaded document, or description of the content (blog post, webinar recording, podcast episode, whitepaper, case study, presentation, video, etc.)
- **Target channels**: Which platforms and formats to repurpose into (LinkedIn, Twitter/X, Instagram, email newsletter, blog, YouTube, TikTok, podcast, infographic, etc.) or ask for recommendations
- **Brand voice context**: Tone and style preferences (auto-loaded from brand profile if available)
- **Priority goals**: What the repurposed content should achieve (traffic, engagement, lead gen, thought leadership, SEO backlinks)
- **Timeline**: How quickly the repurposed content needs to go live (same day, one week, two weeks, ongoing drip)
- **Constraints**: Any platforms to exclude, content restrictions, compliance requirements, or approval workflows
- **Content performance data**: Optional -- engagement metrics from the original piece to identify strongest elements

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply voice, compliance, industry context. Check `guidelines/_manifest.json` for restrictions, messaging, channel styles, voice-and-tone rules, and templates. If a template matching this command exists in `~/.claude-marketing/brands/{slug}/templates/`, apply its format. If no brand exists, prompt for `/digital-marketing-pro:brand-setup` or proceed with defaults.
2. **Check campaign history**: Run `python campaign-tracker.py --brand {slug} --action list-campaigns` to identify related campaigns and previously published content that derivative pieces can reference or link to.
3. **Analyze original content**: Extract the core elements -- key messages, data points, compelling quotes, statistics, step-by-step processes, visual concepts, storytelling hooks, counterintuitive insights, and main takeaways. Identify which elements are strongest for each target format.
4. **Map to channel-specific formats**: Build a repurposing matrix mapping the original content to derivative formats: blog to social threads, webinar to blog series, podcast to audiograms, whitepaper to infographic, case study to testimonial posts, presentation to carousel posts, long-form to short-form snippets, and vice versa. Target 10+ derivative pieces per source.
5. **Apply platform specifications**: Reference `skills/context-engine/platform-specs.md` for character limits, image dimensions, video lengths, hashtag best practices, and format requirements per platform. Adapt each piece to fit native platform conventions.
6. **Adapt messaging for each format**: Rewrite and restructure content for each derivative piece -- not simple truncation but genuine adaptation. A LinkedIn post needs a different hook and structure than a Twitter/X thread, which differs from an email newsletter excerpt or an Instagram carousel. Match the native content style of each platform.
7. **Apply channel-specific voice overrides**: If brand guidelines include `channel-styles.md`, apply platform-specific tone adjustments (e.g., more casual on social, more authoritative in email, more concise on Twitter/X).
8. **Generate content calendar for repurposed pieces**: Sequence the derivative content across a publishing timeline. Space out related pieces to avoid audience fatigue. Front-load high-impact formats and follow with supporting pieces. Align with optimal posting times per platform.
9. **Score each variant for brand voice alignment**: Check every derivative piece against brand voice settings (formality, energy, humor, authority) and channel-specific style overrides from guidelines. Flag any pieces that drift from established voice.
10. **Add tracking and attribution**: Attach UTM parameters to all links in derivative content so traffic driven back to the original or landing pages can be attributed to the specific repurposed piece and platform.
11. **Define performance metrics per format**: Set engagement benchmarks for each derivative piece (impressions, clicks, shares, saves, comments) based on platform averages and brand historical performance.

## Output

A structured content repurposing plan containing:

- Original content summary with extracted key elements (messages, data, quotes, hooks, takeaways)
- Repurposing matrix mapping original content to 10+ derivative formats across channels
- Full draft content for each derivative piece, adapted to platform conventions and native style
- Platform-specific formatting notes (character counts, image specs, hashtag sets, posting format)
- Publishing calendar with recommended dates, times, and sequencing logic
- Brand voice alignment score for each piece with adjustment notes where needed
- Cross-linking strategy connecting derivative pieces back to the original and to each other
- Estimated reach and engagement projections per format based on channel benchmarks
- UTM-tagged links for each derivative piece enabling attribution tracking
- Performance benchmarks per format with success criteria for each piece
- Visual asset requirements per derivative piece (image dimensions, video specs, design notes)
- Hashtag and keyword recommendations per platform for discoverability
- Suggested engagement hooks and CTAs tailored to each platform's audience behavior

## Agents Used

- **content-creator** -- Content analysis, derivative content writing, format adaptation, voice alignment, editorial calendar planning, and cross-linking strategy
- **social-media-manager** -- Platform-specific formatting, social post drafting, hashtag strategy, posting schedule optimization, engagement hook design, and cross-platform coordination
