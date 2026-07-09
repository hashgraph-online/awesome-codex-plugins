---
name: retargeting-strategy
description: "Design retargeting strategy. Use when: planning cross-platform remarketing, audience segmentation, or ad sequencing."
---

# /digital-marketing-pro:retargeting-strategy

## Purpose

Design a cross-platform retargeting strategy with audience segmentation by funnel stage and behavior, creative sequencing, frequency management, and budget allocation. Produces a complete retargeting playbook ready for implementation across advertising platforms.

## Input Required

The user must provide (or will be prompted for):

- **Website traffic volume**: Monthly unique visitors and page views (approximate is fine)
- **Conversion funnel stages**: The key stages in the user journey (visit, product view, add to cart, checkout, purchase -- or equivalent for lead gen funnels)
- **Platforms in use**: Which advertising platforms are active or available (Google Ads, Meta, LinkedIn, TikTok, programmatic DSPs, etc.)
- **Retargeting budget**: Monthly budget allocated or available for retargeting campaigns
- **Product catalog**: For dynamic retargeting -- whether a product feed exists and on which platforms it is configured
- **Average purchase cycle**: Typical time from first visit to conversion (days, weeks, months)
- **Current retargeting setup**: Any existing retargeting campaigns, pixel/tag status, audience definitions already in place, and current performance
- **Pixel and tracking status**: Which pixels/tags are installed and firing correctly (Meta Pixel, Google Tag, LinkedIn Insight Tag, TikTok Pixel, etc.)

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply voice, compliance, industry context. Check `guidelines/_manifest.json` for restrictions, messaging, channel styles, voice-and-tone rules, and templates. If a template matching this command exists in `~/.claude-marketing/brands/{slug}/templates/`, apply its format. If no brand exists, prompt for `/digital-marketing-pro:brand-setup` or proceed with defaults.
2. **Check campaign history**: Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/campaign-tracker.py" --brand {slug} --action list-campaigns` to review existing retargeting campaign performance and identify what has already been tested.
3. **Audit tracking infrastructure**: Verify pixel and tag installation status across platforms. Identify gaps in tracking that would prevent audience building or conversion attribution before designing the strategy.
4. **Define retargeting audience segments**: Create segments based on funnel stage (awareness visitors, product viewers, cart abandoners, past purchasers, lapsed customers), behavior signals (pages visited, time on site, visit frequency, content consumed), and recency windows (1-3 days, 4-7 days, 8-14 days, 15-30 days, 31-90 days). Size each segment based on traffic volume.
5. **Design creative sequence per segment**: Map a messaging sequence for each audience segment that progresses the user toward conversion -- awareness segments get educational and value-prop messaging, consideration segments get social proof and differentiation, cart abandoners get urgency and incentive, past purchasers get upsell and cross-sell, and lapsed customers get re-engagement offers.
6. **Set frequency caps per platform**: Define impression frequency limits per user per day and per week for each platform. Balance visibility against ad fatigue -- typically 3-5 impressions per day for display, 1-2 per day for social feed placements, and 15-20 per week maximum across all placements combined.
7. **Plan cross-platform coordination**: Orchestrate retargeting across platforms so users see a coherent journey rather than redundant messages. Assign primary and secondary roles per platform (e.g., Meta for awareness retargeting, Google Display for mid-funnel, search remarketing for high-intent, LinkedIn for B2B decision-makers).
8. **Design exclusion lists**: Define converter exclusion windows (exclude purchasers for 7-30 days post-conversion), cross-segment exclusions (prevent users from seeing both awareness and cart abandonment ads simultaneously), and negative audience rules to prevent waste and brand fatigue.
9. **Set budget allocation per segment**: Distribute the retargeting budget across segments based on audience size, proximity to conversion, and expected ROAS. Bottom-funnel segments (cart abandoners) typically receive the highest per-user spend despite smaller audience sizes.
10. **Configure dynamic retargeting**: If a product catalog is available, specify dynamic ad setup -- feed requirements, template design, product recommendation logic (viewed items, complementary products, best sellers), and fallback creatives for users without product-level data.
11. **Define KPIs and optimization triggers**: Set success metrics per segment and platform (ROAS, CPA, view-through conversions, frequency, CTR). Define optimization triggers -- when to refresh creative, adjust bids, reallocate budget, or expand/contract audience windows.
12. **Create UTM structure for tracking**: Build a UTM naming convention that enables granular tracking of retargeting performance by segment, platform, creative variant, and funnel stage in analytics.

## Output

A structured retargeting strategy document containing:

- Audience segment definitions with sizing estimates, recency windows, and behavioral criteria
- Creative brief per segment with messaging themes, ad formats, and sequencing logic
- Frequency cap recommendations per platform with rationale for each limit
- Cross-platform coordination plan showing which platform serves which funnel role
- Exclusion list definitions with converter suppression windows and cross-segment rules
- Budget allocation table by segment and platform with expected ROAS targets
- Dynamic retargeting setup guide with feed requirements and product recommendation logic
- KPI framework with targets per segment, optimization triggers, and review cadence
- UTM structure and naming conventions for retargeting campaign tracking
- 30/60/90-day optimization roadmap with milestone checkpoints and scaling criteria
- Privacy and compliance considerations (cookie consent, GDPR/CCPA audience restrictions, platform-specific privacy limitations)
- Tracking infrastructure checklist with pixel/tag verification requirements per platform

## Agents Used

- **media-buyer** -- Audience segmentation, platform-specific retargeting setup, frequency management, budget allocation, bid strategy, dynamic retargeting configuration, and campaign structure design
- **marketing-strategist** -- Creative sequencing strategy, cross-platform coordination, funnel-stage messaging architecture, and optimization roadmap planning
