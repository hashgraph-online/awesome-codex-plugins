# Google Ads — Campaign Reference Guide

## API version notes (June 2026)

If you're writing code or constructing API requests against the Google Ads API, target **v24.2** (released 24 June 2026 — current latest). v24.0 was the last release with breaking changes; v24.1 and v24.2 are non-breaking additive releases.

### v24.2 (24 June 2026 — current)

Non-breaking additions:

| What | Where | Why it matters for ads ops |
|---|---|---|
| `AssetAutomationType.GENERATE_LANDING_PAGE_TEXT` | New enum value on the asset-automation API for Demand Gen video ads | Lets PMax/Demand Gen auto-generate the landing-page text variants that Google's asset gen needs — fewer manual writes per campaign |
| `AssetGroup.google_local_services_info` | New field on `AssetGroup` | First-class Local Services Ads (LSA) support inside the standard API. Plumbers / electricians / cleaners / locksmiths / lawyers etc. can now manage LSA from the same API surface as PMax |
| `MultiPartyAuthReview` resource + `MultiPartyAuthReviewService` (beta) | New API resource | Lets advertisers and their agencies coordinate Multi-Party Authorization reviews via API — relevant for regulated verticals (finance, health, political ads) |

### v24.1 (13 May 2026)

Non-breaking additions:

| What | Where | Why it matters for ads ops |
|---|---|---|
| 4 new experiment types: `ADOPT_AI_MAX`, `ADOPT_BROAD_MATCH_KEYWORDS`, `OPTIMIZE_ASSETS`, `PMAX_REPLACEMENT_SHOPPING` | `ExperimentType` enum | Official Google-recommended A/B framework for migrating to AI Max + broad match + Performance Max replacing standard Shopping. **Run `ADOPT_AI_MAX` before any AI Max rollout** — gives you statistically-clean lift numbers vs the baseline |
| `mobile_device_platform` segment | Reporting segments | Split campaign-/ad-/keyword-level performance by iOS vs Android. First time the OS split has been first-class in the API |

### v24 (22 April 2026) — last release with breaking changes

| Object | Change | Effect |
|---|---|---|
| `DemandGenVideoResponsiveAdInfo` | `videos` and `logo_images` now REQUIRED | Requests without both fields fail |
| `VideoResponsiveAdInfo` | `videos`, `logo_images`, and `business_name` now REQUIRED | Requests without all three fields fail |
| `Campaign.video_brand_safety_suitability` | REMOVED — moved to Customer level | Set the control once on the Customer object, not per-campaign |
| `CallAd` / `CallAdInfo` | REMOVED (deprecation completed) | Use Call Assets instead |

### v23.1 (25 February 2026)

Added `text_guidelines.term_exclusions` and `text_guidelines.messaging_restrictions` to AI-generated assets in **Performance Max** and **Search** — use these to pipe a brand's banned-word list and approved messaging directly into PMax's asset-gen guardrails.

Source: [Google Ads API release notes](https://developers.google.com/google-ads/api/docs/release-notes).

### Adoption recommendation

If you have time before your next ship:
- **Upgrade clients to v24.2** to unlock Local Services Ads + landing-page-text generation
- **Wire `ADOPT_AI_MAX` experiments** (v24.1) into any AI Max migration plan — Google's preferred lift-measurement path
- **Add `mobile_device_platform` segmentation** to any iOS-vs-Android performance reports (v24.1)

## Campaign Types Overview

| Campaign Type | Best For | Targeting | Creative Format | Typical ROAS Range |
|---|---|---|---|---|
| Search | High-intent capture | Keywords | Text ads (RSAs) | 3x–10x |
| Performance Max | Full-funnel automation | Signals + Google AI | All formats | 2x–8x |
| Display | Awareness, retargeting | Audiences, placements | Image, responsive | 1x–4x |
| YouTube (Video) | Brand lift, consideration | Demographics, intent | Video (6s–3min) | 1x–5x |
| Shopping (Standard) | Product-level control | Product feed | Product listing ads | 3x–12x |
| Demand Gen | Mid-funnel discovery | Lookalikes, audiences | Image + video | 2x–6x |

## Account Structure Best Practices

### Modern Simplified Structure (Recommended)
```
Account
├── Brand Search Campaign
│   └── 1–3 ad groups (brand, brand + product, brand + competitor)
├── Non-Brand Search Campaign(s)
│   └── Themed ad groups by service/product category
├── Performance Max Campaign(s)
│   └── Asset groups segmented by product/service line
├── Retargeting Campaign
│   └── Display/YouTube remarketing
└── Video/Demand Gen Campaign
    └── Top/mid-funnel awareness
```

### Structure Principles
- [ ] Consolidate campaigns to feed algorithm more data per campaign
- [ ] Minimum 30 conversions per campaign per month for automated bidding
- [ ] Avoid single-keyword ad groups (SKAGs) — outdated with broad match + smart bidding
- [ ] Segment by budget priority, not granular keyword themes
- [ ] Use labels and naming conventions for reporting clarity

## Bidding Strategy Decision Tree

```
START: What is your primary objective?
│
├── Maximize Conversions (volume)
│   ├── Have a target CPA? → Target CPA (tCPA)
│   └── No CPA target? → Maximize Conversions
│
├── Maximize Revenue (value)
│   ├── Have a target ROAS? → Target ROAS (tROAS)
│   └── No ROAS target? → Maximize Conversion Value
│
├── Traffic / Clicks
│   └── Maximize Clicks (set max CPC cap)
│
├── Awareness / Impressions
│   └── Target Impression Share
│
└── Full Control (low volume)
    └── Manual CPC (Enhanced optional)
```

### Bidding Strategy Selection Criteria

| Strategy | Min. Monthly Conversions | When to Use | Watch Out For |
|---|---|---|---|
| tCPA | 30+ | Stable CPA goal, lead gen | Set realistic targets (start at 2x actual) |
| tROAS | 50+ | E-commerce, variable values | Needs accurate conversion values |
| Max Conversions | 15+ | New campaigns, budget-constrained | Can overspend on low-quality conversions |
| Max Conv Value | 15+ | Revenue focus, no ROAS target | May chase high-value outliers |
| Manual CPC | Any | Low volume, testing | Labor-intensive, misses signals |

## Keyword Match Type Strategy

| Match Type | Syntax | Behavior (2024+) | Use Case |
|---|---|---|---|
| Broad | `keyword` | Widest reach; meaning + intent | Pair with smart bidding; primary driver |
| Phrase | `"keyword"` | Contains meaning in order | Mid-control; specific intent sequences |
| Exact | `[keyword]` | Closest meaning match | High-value, proven converters |

### Modern Keyword Strategy
1. **Start with broad match + tCPA/tROAS** — let smart bidding optimize
2. **Use exact match for top performers** — protect budget on proven terms
3. **Phrase match for specificity** — when broad pulls irrelevant traffic
4. **Search term analysis weekly** — mine for negatives and new keywords
5. **Avoid keyword overlap** — deduplicate across ad groups to prevent self-competition

## Quality Score Optimization

### Quality Score Components

| Component | Weight | How to Improve |
|---|---|---|
| Expected CTR | ~35% | Compelling ad copy, strong CTAs, ad extensions |
| Ad Relevance | ~25% | Match ad copy to keyword intent, use keyword in headlines |
| Landing Page Experience | ~40% | Page speed, mobile-friendly, relevant content, clear CTA |

### Quality Score Improvement Checklist
- [ ] Keyword appears in at least 2 of 15 RSA headlines
- [ ] Landing page headline matches search intent
- [ ] Page loads in under 3 seconds (mobile)
- [ ] Mobile-responsive design verified
- [ ] Clear above-the-fold CTA
- [ ] Content directly addresses searcher's query
- [ ] Minimal pop-ups and interstitials
- [ ] HTTPS enabled
- [ ] Structured data markup present

## RSA (Responsive Search Ad) Writing Strategy

### Headline Framework (15 Headlines)

| Slot | Purpose | Example |
|---|---|---|
| H1–H3 | Primary value prop (pin H1 to position 1) | "Award-Winning Project Management Software" |
| H4–H6 | Features / differentiators | "Real-Time Collaboration Tools" |
| H7–H9 | Social proof / trust signals | "Trusted by 10,000+ Teams Worldwide" |
| H10–H12 | CTAs and offers | "Start Your Free 14-Day Trial" |
| H13–H14 | Keyword insertion / location | "Best {KeyWord:PM Tool} for Teams" |
| H15 | Seasonal or test variant | "New 2025 Features Now Available" |

### Description Framework (4 Descriptions)
1. **Primary value prop + CTA** — comprehensive benefit statement with action
2. **Features and proof points** — specific capabilities, stats, awards
3. **Objection handling** — no credit card, free trial, money-back guarantee
4. **Urgency / offer** — limited time, seasonal hook, discount

### Pinning Strategy
- Pin your strongest brand headline to Position 1
- Pin your strongest CTA to Position 2 (optional)
- Never pin more than 2 headlines — let Google optimize
- Pin one description only if compliance requires specific language

## Performance Max Setup Checklist

### Pre-Launch
- [ ] Conversion tracking verified (offline + online, with values if possible)
- [ ] Enhanced conversions enabled
- [ ] Google Merchant Center connected (e-commerce)
- [ ] Google Business Profile linked (local)
- [ ] YouTube channel linked
- [ ] Audience signals configured (custom segments, customer lists, website visitors)
- [ ] Brand exclusions applied (if available)

### Asset Group Configuration
- [ ] 20 text assets (5 headlines, 5 long headlines, 5 descriptions, 1 business name, 4 sitelinks minimum)
- [ ] 20 image assets (various aspect ratios: 1.91:1, 1:1, 4:5)
- [ ] 5 video assets (landscape, portrait, square — at least 10 seconds)
- [ ] Final URL expansion ON or OFF based on strategy
- [ ] URL exclusions set to prevent irrelevant landing pages

### Post-Launch Monitoring
- [ ] Allow 2–4 weeks learning phase before major changes
- [ ] Review asset performance ratings weekly (replace "Low" assets)
- [ ] Check Insights tab for audience and search category data
- [ ] Monitor placement reports for brand safety
- [ ] Compare PMax performance against brand search (cannibalization check)

## Negative Keyword Management

### Negative Match Types

| Type | Syntax | Blocks |
|---|---|---|
| Broad Negative | `keyword` | Any query containing all negative terms (any order) |
| Phrase Negative | `"keyword"` | Queries containing the exact phrase in order |
| Exact Negative | `[keyword]` | Only the exact query |

### Negative Keyword Best Practices
- [ ] Create shared negative keyword lists at account level
- [ ] Review search terms report weekly (daily during launch)
- [ ] Maintain standard exclusion lists: jobs, free, DIY, reviews, competitors (if desired)
- [ ] Add negatives at campaign level for specificity, account level for universal
- [ ] Export and audit negative lists quarterly — over-negating kills volume
- [ ] Cross-reference negatives against active keywords to prevent conflicts

### Standard Negative Lists to Maintain
1. **Brand Protection**: competitor names (if not targeting)
2. **Intent Exclusion**: "free," "jobs," "salary," "how to," "DIY"
3. **Irrelevant Modifiers**: "cheap," "used," (industry-specific terms)
4. **Compliance**: restricted terms for your vertical

## Shopping Feed Optimization

### Required Feed Attributes (Optimize These)

| Attribute | Optimization Tip |
|---|---|
| `title` | Front-load with brand + product type + key attribute (color, size). Max 150 chars. |
| `description` | Include relevant keywords naturally. First 160 chars matter most. |
| `product_type` | Use full category path: Home > Furniture > Sofas > Sectional Sofas |
| `google_product_category` | Map to most specific Google taxonomy ID |
| `image_link` | White background, high resolution, no watermarks, no promotional overlays |
| `price` | Must match landing page exactly; use `sale_price` for promos |
| `availability` | Keep in sync — disapprovals for mismatches hurt account health |
| `gtin` / `mpn` | Always provide when available; enables richer placements |
| `custom_labels` | Tag by margin, best-seller, seasonal, clearance for bid segmentation |

### Feed Health Checklist
- [ ] Zero disapprovals (check Diagnostics daily)
- [ ] Supplemental feed for overrides without touching primary feed
- [ ] Feed refresh frequency: minimum daily, ideally every 6 hours
- [ ] All variants (size, color) listed as separate items
- [ ] Promotional feed connected for merchant promotions
- [ ] Feed rules configured for automated attribute fixes
- [ ] Competitive pricing data reviewed via Price Competitiveness report

## Key Metrics & Benchmarks (Cross-Industry Averages)

| Metric | Search | Shopping | Display | YouTube |
|---|---|---|---|---|
| CTR | 3–6% | 0.8–1.5% | 0.3–0.6% | 0.5–2% (TrueView) |
| CPC | $1–$5 | $0.30–$1.50 | $0.20–$0.80 | $0.02–$0.10 (CPV) |
| Conv Rate | 3–7% | 1.5–3.5% | 0.5–1.5% | 0.5–2% |
| Quality Score | 7+ target | N/A | N/A | N/A |

> **Note:** Benchmarks vary dramatically by industry, geography, and season. Use these as directional starting points and calibrate to your own historical data within 30–60 days.
