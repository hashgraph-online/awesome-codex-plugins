---
name: paid-advertising
description: "Plan paid advertising campaigns. Use when: managing Google Ads, Meta Ads, LinkedIn Ads, bid strategy, or budget optimization."
---

# Paid Advertising

## Recent platform API changes (as of June 2026)

Target **Google Ads API v24.2** (released 24 June 2026 — current latest). v24.0 was the last release with breaking changes; v24.1 and v24.2 are non-breaking additive releases. Full detail — including AI Max — lives in [`google-ads.md`](google-ads.md), the single source for the Google Ads API surface. Source: [Google Ads API release notes](https://developers.google.com/google-ads/api/docs/release-notes).

**Highlights that affect campaign construction:**

- **v24.2 (24 Jun 2026):** first-class **Local Services Ads** support (`AssetGroup.google_local_services_info`), landing-page-text auto-generation (`AssetAutomationType.GENERATE_LANDING_PAGE_TEXT`), and a beta Multi-Party Auth review resource for regulated verticals (finance, health, political).
- **v24.1 (13 May 2026) — AI Max:** four new experiment types (`ADOPT_AI_MAX`, `ADOPT_BROAD_MATCH_KEYWORDS`, `OPTIMIZE_ASSETS`, `PMAX_REPLACEMENT_SHOPPING`). **Run an `ADOPT_AI_MAX` experiment before any AI Max rollout** — it gives statistically-clean lift numbers vs the baseline. Also adds `mobile_device_platform` (iOS vs Android) reporting segmentation.
- **v24.0 (22 Apr 2026) — breaking:** `videos` + `logo_images` now REQUIRED on `DemandGenVideoResponsiveAdInfo`/`VideoResponsiveAdInfo` (and `business_name` on the latter); `Campaign.video_brand_safety_suitability` REMOVED (moved to the Customer level); `CallAd`/`CallAdInfo` fully removed (use Call Assets).
- **v23.1 (25 Feb 2026):** `text_guidelines.term_exclusions` + `text_guidelines.messaging_restrictions` on AI-generated **Performance Max** and **Search** assets — pipe a brand's banned-word list (`profile.json → restrictions.md → banned_words`) and approved messaging straight into PMax asset-gen guardrails.

## When to Use This Skill

Activate this skill when the user's request involves any of the following:

- Creating, auditing, or optimizing campaigns on Google Ads, Meta/Facebook Ads, LinkedIn Ads, or TikTok Ads
- Designing campaign structures, ad groups, or ad set hierarchies on any paid platform
- Selecting or troubleshooting bid strategies (manual CPC, target CPA, target ROAS, maximize conversions, etc.)
- Building audience strategies including prospecting, retargeting, lookalike/similar audiences, or custom audiences
- Allocating or pacing budgets across platforms or campaigns
- Setting up or optimizing Google Shopping, Performance Max, YouTube Ads, or Display campaigns
- Working with Meta Advantage+ campaigns or manual campaign structures
- Running LinkedIn Ads with account-based marketing (ABM) targeting
- Launching TikTok Ads including Spark Ads or TikTok Shop integrations
- Programmatic advertising including DSP selection, connected TV (CTV), or digital out-of-home (DOOH)
- Retail media networks including Amazon Ads, Walmart Connect, Target Roundel, Kroger Precision Marketing, or Instacart Ads
- Any question about paid media strategy, creative strategy for ads, or paid channel mix decisions

## Brand Context (Auto-Applied)

Before producing any marketing output from this module:

1. **Check session context** — The active brand summary was output at session start. Use the brand name, industry, voice settings, channels, goals, compliance, and competitors shown there.
2. **If you need the full profile**, read: `~/.claude-marketing/brands/{slug}/profile.json`
3. **Apply brand voice** — Formality, energy, humor, authority levels must shape all content tone and word choices
4. **Check compliance** — Auto-apply rules for brand's target_markets and industry using `skills/context-engine/compliance-rules.md`
5. **Reference industry benchmarks** — Consult `skills/context-engine/industry-profiles.md` for the brand's industry
6. **Use platform specs** — Reference `skills/context-engine/platform-specs.md` for character limits and format requirements
7. **Check campaign history** — Run `python campaign-tracker.py --brand {slug} --action list-campaigns` before planning new work
8. **If no brand exists**, say: "No brand profile found. Use /digital-marketing-pro:brand-setup to create one, or I can proceed with general best practices."
9. **Check brand guidelines** — If `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` exists, load and enforce: `restrictions.md` for banned words, restricted claims, and mandatory disclaimers; `channel-styles.md` for channel-specific tone overrides (may differ from base voice); `messaging.md` for approved key messages, taglines, and positioning language; `voice-and-tone.md` for detailed voice rules beyond the 4 numeric scores. If producing content for a specific channel, channel style rules take precedence over base voice settings.

Do not ask the user for information that already exists in their brand profile.

## Required Context

Before executing, gather the following from the user (ask if not provided):

- **Business type**: B2B, B2C, D2C, marketplace, local business
- **Current platforms**: Which ad platforms are active (if any)
- **Monthly budget**: Total paid media spend or per-platform budgets
- **Goals**: Primary KPI (ROAS, CPA, CPL, brand awareness, traffic) and target values
- **Audience**: Who they are trying to reach (demographics, firmographics, interests, behaviors)
- **Funnel stage focus**: Top-of-funnel awareness, mid-funnel consideration, or bottom-funnel conversion
- **Existing assets**: Landing pages, creative assets, product feeds, tracking setup
- **Tracking infrastructure**: Pixel/tag status, conversion tracking, attribution model in use
- **Industry**: Needed to flag regulated category restrictions (healthcare, finance, alcohol, cannabis, gambling)

## Capabilities

### Campaign Structure Design
- Platform-specific campaign architecture (campaigns, ad groups/ad sets, ads)
- Naming conventions for scalable account management
- Campaign type selection per objective (Search, Display, Shopping, Video, App, PMax, Demand Gen)
- Ad group theming and keyword/audience segmentation strategies

### Audience Strategy
- **Prospecting**: Interest-based, behavior-based, demographic, and contextual targeting
- **Retargeting**: Website visitors, video viewers, lead form engagers, customer lists, cart abandoners
- **Lookalike/Similar audiences**: Source audience selection, expansion percentages, layering strategies
- **ABM targeting**: Company lists, job title targeting, seniority filtering (LinkedIn-specific)
- **Exclusion strategies**: Negative audiences, customer suppression, converter exclusion windows

### Bid Strategy Selection
- Manual vs automated bidding decision framework
- Target CPA, target ROAS, maximize conversions, maximize conversion value
- Portfolio bid strategies for Google Ads
- Learning phase management and bid strategy transitions
- Seasonality adjustments and bid modifiers

### Creative Strategy
- Ad format selection per platform and objective
- Responsive search ads (RSA) best practices and pin strategies
- Meta creative diversification (static, video, carousel, collection, instant experience)
- LinkedIn creative formats (single image, carousel, video, document, conversation ads)
- TikTok native-style creative principles
- Creative testing frameworks (variable isolation, iterative testing)

### Budget Allocation and Pacing
- Cross-platform budget distribution models
- Campaign-level budget optimization vs ad-set level budgets
- Daily vs lifetime budgets and when to use each
- Pacing strategies for monthly/quarterly targets
- Budget scaling rules (20% rule for Google, CBO adjustments for Meta)

### Platform-Specific Expertise
- **Google Ads**: Search, Display, Performance Max, YouTube (in-stream, Shorts, Discovery), Shopping, Demand Gen
- **Meta Ads**: Advantage+ Shopping, Advantage+ App, manual campaigns, catalog ads, lead gen forms
- **LinkedIn Ads**: Sponsored Content, Message Ads, Lead Gen Forms, Document Ads, ABM list targeting
- **TikTok Ads**: In-Feed, TopView, Spark Ads, TikTok Shop product ads, Branded Effects
- **Programmatic**: DSP selection (DV360, The Trade Desk, Amazon DSP), CTV, DOOH, audio
- **Retail Media**: Amazon Sponsored Products/Brands/Display, Walmart Connect, Target Roundel, Kroger Precision Marketing, Instacart Ads

## Process

### Standard Campaign Build (Most Common Use Case)

1. **Define objectives** -- Clarify the primary KPI and success metric. Map to the correct campaign type per platform.
2. **Audience architecture** -- Design the full-funnel audience strategy: cold prospecting segments, warm retargeting pools, and hot remarketing lists. Define exclusions.
3. **Campaign structure** -- Build the campaign hierarchy with naming conventions. Determine budget allocation across campaigns.
4. **Bid strategy selection** -- Choose the appropriate bid strategy based on data maturity, conversion volume, and goals. Reference `bid-strategy.md` for decision trees.
5. **Creative strategy** -- Define ad formats, messaging angles, and creative variations. Map creative to funnel stage and audience segment.
6. **Tracking validation** -- Confirm pixel/tag setup, conversion actions, and attribution model before launch.
7. **Launch plan** -- Set launch budgets (often lower than steady-state), define learning phase expectations, and establish the first optimization checkpoint (typically 7-14 days).
8. **Optimization cadence** -- Define weekly/biweekly optimization actions: bid adjustments, audience refinements, creative refreshes, budget reallocation.

### Campaign Audit Process

1. **Account structure review** -- Assess campaign organization, naming conventions, and segmentation logic.
2. **Audience overlap analysis** -- Check for audience fragmentation or cannibalization across campaigns.
3. **Bid strategy assessment** -- Evaluate whether current bid strategies match conversion volume and goals.
4. **Creative performance** -- Identify top/bottom performers, creative fatigue signals, and testing gaps.
5. **Budget efficiency** -- Analyze spend distribution vs performance distribution. Flag underspending winners and overspending losers.
6. **Tracking audit** -- Verify conversion tracking accuracy, attribution consistency, and data freshness.

## Reference Files

- `google-ads.md` -- Google Ads campaign types, settings, optimization tactics, and platform-specific features
- `meta-ads.md` -- Meta Ads campaign structures, Advantage+ configurations, creative specs, and iOS ATT strategies
- `linkedin-ads.md` -- LinkedIn Ads targeting options, ABM strategies, lead gen optimization, and B2B-specific tactics
- `tiktok-ads.md` -- TikTok Ads creative best practices, Spark Ads setup, TikTok Shop integration, and audience strategies
- `programmatic.md` -- DSP selection criteria, CTV planning, DOOH strategies, and programmatic deal types
- `bid-strategy.md` -- Bid strategy decision trees, learning phase management, and portfolio strategy configurations
- `retail-media-networks.md` -- Platform-specific setup for Amazon, Walmart, Target, Kroger, and Instacart advertising

## Output Formats

- **Campaign plan**: Structured document with campaign hierarchy, audience definitions, bid strategies, budget allocation, creative briefs, and KPI targets
- **Platform audit**: Scorecard with findings, severity ratings, and prioritized action items
- **Budget allocation model**: Spreadsheet-ready breakdown of spend by platform, campaign, and funnel stage with projected outcomes
- **Creative brief**: Per-ad-format briefs with messaging angles, CTA options, and spec requirements
- **Optimization playbook**: Weekly/monthly checklist of optimization actions with decision criteria

## Edge Cases

### iOS ATT Impact on Meta Targeting
Post-iOS 14.5, Meta audience sizes shrunk and attribution windows shortened. When working with Meta campaigns, default to broader targeting with Advantage+ audience expansion, use Conversions API (CAPI) alongside the pixel, recommend 7-day click attribution, and set expectations that reported ROAS will undercount actual performance by 15-30%.

### Performance Max Cannibalizing Brand Search
PMax campaigns frequently capture branded search traffic, inflating their reported performance. Always recommend running a brand exclusion list in PMax, maintaining a separate brand search campaign, and comparing incrementality by analyzing total account performance rather than PMax in isolation.

### LinkedIn High CPC Management
LinkedIn CPCs are typically 3-10x higher than other platforms. Compensate by focusing on lead quality over volume, using lead gen forms (higher conversion rate than landing pages), tightening audience targeting to reduce waste, and evaluating on cost-per-qualified-lead rather than CPC.

### TikTok Creative Fatigue
TikTok ad creative typically fatigues in 3-7 days. Build creative refresh cadences into every TikTok campaign plan. Recommend 3-5 active creatives per ad group with new batches produced weekly. Use Spark Ads (boosted organic) to extend creative life since they feel less like ads.

### Retail Media Incrementality
Retail media ads often capture purchases that would have happened organically. When auditing retail media, question whether sales are truly incremental. Recommend running incrementality tests (holdout groups), analyzing new-to-brand metrics (Amazon provides this), and comparing organic rank changes during ad pauses.

### Small Budget Cross-Platform Allocation
When total monthly budget is under $5,000, do not spread across multiple platforms. Recommend concentrating on one primary platform that best matches the audience and objective. Only expand to a second platform after the first is optimized and hitting diminishing returns.

### Regulated Industry Restrictions
Healthcare, finance, alcohol, cannabis, gambling, and political advertising face platform-specific restrictions. Always check platform policies before recommending campaign types. Some platforms ban certain industries entirely (TikTok restricts financial services ads in some markets). Reference platform-specific docs for current restriction lists.

## Related Skills

- **CRO** -- Landing page and conversion optimization for ad traffic destinations
- **Analytics & Insights** -- Attribution modeling, conversion tracking setup, and performance analysis
- **Audience Intelligence** -- Deep audience research to inform targeting strategies
- **Content Engine** -- Ad creative copywriting and messaging frameworks
- **Funnel Architect** -- Full-funnel strategy that paid advertising plugs into
- **Emerging Channels** -- Social commerce and newer ad platforms (TikTok Shop, CTV)
