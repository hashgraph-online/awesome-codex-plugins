# Meta Ads — Facebook & Instagram Reference

## Campaign Structure Overview

### Campaign Budget Optimization (CBO) vs Ad Set Budget Optimization (ABO)

| Factor | CBO | ABO |
|---|---|---|
| Budget control | Campaign level — Meta distributes | Ad set level — you control each |
| Best for | Testing many audiences, scaling winners | Controlled tests, fixed audience budgets |
| Algorithm advantage | Meta optimizes spend toward best performers | You maintain precise spend allocation |
| When to use | 3+ ad sets, scaling phase | Launch testing, strict budget requirements |
| Minimum budget | $30–50/day per campaign (recommended) | $10–20/day per ad set (recommended) |

### Advantage+ Campaigns

| Type | Use Case | Key Difference |
|---|---|---|
| Advantage+ Shopping | E-commerce, product catalog | Fully automated targeting + creative |
| Advantage+ App | App installs | Automated audience, placement, creative |
| Standard with Advantage+ features | Lead gen, awareness | Selective automation on specific components |

### Recommended Account Structure
```
Account
├── Prospecting (CBO)
│   ├── Advantage+ Audience — broad targeting
│   ├── Lookalike stack — 1%, 3%, 5%
│   └── Interest-based — layered interests
├── Retargeting (ABO)
│   ├── Website visitors 1–7 days
│   ├── Website visitors 8–30 days
│   ├── Engaged social audience
│   └── Cart/checkout abandoners
├── Retention / Upsell (ABO)
│   ├── Existing customers — cross-sell
│   └── Lapsed customers — win-back
└── Advantage+ Shopping Campaign (if e-commerce)
    └── Existing customer budget cap set at 20–30%
```

## Audience Strategy

### Custom Audiences

| Source | Retention Window | Quality Rating | Notes |
|---|---|---|---|
| Customer list (email/phone) | Refreshed monthly | High | Min 1,000 records; hash before upload |
| Website visitors (all) | 180 days max | Medium-High | Use Pixel + CAPI for completeness |
| Website — specific pages | 30–90 days | High | Product pages, pricing, cart |
| Video viewers (25%, 50%, 75%, 95%) | 365 days | Medium | Layer by engagement depth |
| Lead form openers/submitters | 90 days | High | Great for retargeting non-converters |
| Instagram/Facebook engagers | 365 days | Medium | Broad but relevant |
| App activity | 180 days | High | In-app events drive precision |

### Lookalike Audiences

| Seed Audience | Recommended % | Expected Quality |
|---|---|---|
| Purchasers / high-LTV customers | 1% | Highest |
| All converters (leads + purchases) | 1–3% | High |
| Add-to-cart visitors | 1–3% | Medium-High |
| Website visitors (all) | 3–5% | Medium |
| Engaged video viewers | 3–5% | Medium |
| Page engagers | 5–10% | Lower |

### Advantage+ Audience (Recommended Default)
- Replaces manual targeting with Meta's ML-driven audience discovery
- Provide **audience suggestions** (former interests/lookalikes) as signals, not restrictions
- Outperforms manual targeting in 60–70% of A/B tests (Meta internal data)
- Best practice: run Advantage+ Audience against your best manual audience in a split test

## Creative Specs by Placement

| Placement | Format | Aspect Ratio | Resolution (min) | Max File Size |
|---|---|---|---|---|
| Feed (FB + IG) | Image | 1:1 or 4:5 | 1080x1080 / 1080x1350 | 30 MB |
| Feed (FB + IG) | Video | 1:1 or 4:5 | 1080x1080 / 1080x1350 | 4 GB |
| Stories / Reels | Image | 9:16 | 1080x1920 | 30 MB |
| Stories / Reels | Video | 9:16 | 1080x1920 | 4 GB |
| Right column (FB) | Image | 1:1 | 1080x1080 | 30 MB |
| In-stream video | Video | 16:9 | 1920x1080 | 4 GB |
| Audience Network | Image/Video | Varies | 1080 min width | 30 MB / 4 GB |
| Messenger | Image | 1:1 | 1080x1080 | 30 MB |

### Video Best Practices
- First 3 seconds must hook — assume sound off
- Add captions/text overlays (85% watch without sound)
- Optimal length: 15–30 seconds for conversion; 6–15 seconds for awareness
- Vertical (9:16) outperforms horizontal in mobile-first placements

## iOS ATT Mitigation Strategy

### Impact Summary
iOS 14.5+ App Tracking Transparency reduced Meta's signal fidelity significantly. These are the current countermeasures.

### Conversions API (CAPI) Implementation
- [ ] Server-side event tracking configured (Purchase, Lead, AddToCart, ViewContent minimum)
- [ ] Event match quality score above 6.0 (target 8.0+)
- [ ] Deduplicate events — send both Pixel and CAPI with matching `event_id`
- [ ] Include maximum user parameters: email, phone, IP, user agent, fbc, fbp
- [ ] Hash PII before sending (SHA-256)
- [ ] Verify events in Events Manager > Test Events

### Aggregated Event Measurement (AEM)
- [ ] Domain verified in Business Manager
- [ ] 8 conversion events configured and prioritized
- [ ] Event priority ranked (Purchase > Lead > AddToCart > ViewContent)
- [ ] Value optimization enabled for top-priority event
- [ ] 72-hour delay expected after configuration changes

### Additional Signal Recovery
- [ ] Enhanced conversions enabled
- [ ] Advanced matching turned on (automatic + manual)
- [ ] Broad targeting to compensate for audience signal loss
- [ ] Conversion lead optimization (offline conversion import) for lead gen
- [ ] UTM parameters on all ad URLs for GA4 cross-reference

## Creative Best Practices

### Ad Creative Framework: The 4C Method

| Element | Description | Example |
|---|---|---|
| **Catch** | Pattern interrupt in first 1–3 seconds | Bold text overlay, unexpected visual, direct question |
| **Connect** | Relate to audience pain point | "Tired of spending hours on reports?" |
| **Convince** | Proof, features, social evidence | Testimonial, demo, stats, before/after |
| **Close** | Clear CTA aligned with funnel stage | "Shop Now," "Get Free Trial," "Learn More" |

### Creative Volume & Testing
- Launch with 3–6 creative variations per ad set minimum
- Test across these dimensions (one variable at a time):
  - Hook / opening (biggest impact)
  - Format (static vs video vs carousel)
  - Copy angle (benefit vs feature vs testimonial vs UGC)
  - CTA (direct vs soft)
- Kill underperformers after 2x target CPA spend with zero or poor conversions
- Refresh creative every 2–4 weeks to combat fatigue

### Creative Types That Perform

| Format | Best For | Tips |
|---|---|---|
| UGC-style video | Conversion, consideration | Authentic feel, real people, not polished |
| Static with bold text | Retargeting, offers | Clear value prop, minimal design, high contrast |
| Carousel | Multi-product, storytelling | First card must hook; use all 10 cards |
| Collection / Instant Experience | E-commerce, catalog | Full-screen mobile experience |
| Reels-native video | Prospecting, awareness | Trending audio, fast cuts, vertical only |

## Advantage+ Shopping Campaign Setup

### Pre-Launch Checklist
- [ ] Product catalog connected and healthy (no disapprovals)
- [ ] Pixel + CAPI firing correctly with purchase events and values
- [ ] Customer list uploaded (for existing customer cap)
- [ ] Creative assets ready: 5–10 images/videos minimum
- [ ] Set existing customer budget cap (recommended: 20–30%)

### Configuration
- [ ] Select Advantage+ Shopping campaign type
- [ ] Set daily budget (minimum $50/day recommended, ideally 10x target CPA)
- [ ] Attribution window: 7-day click, 1-day view (default and recommended)
- [ ] Country targeting set
- [ ] Existing customer definition configured
- [ ] Upload 5–10+ creative assets across formats
- [ ] Primary text: 3–5 variations
- [ ] Headlines: 3–5 variations

### Optimization Timeline
| Week | Action |
|---|---|
| Week 1 | Launch — do not touch. Let learning phase complete. |
| Week 2 | Review performance. Replace worst creative if CPA > 2x target. |
| Week 3 | Add 2–3 new creative assets. Adjust budget if ROAS on track. |
| Week 4+ | Scale budget by 20% increments every 3–5 days if profitable. |

## CAPI Implementation Checklist

### Direct Integration
- [ ] Choose integration method: Partner (Shopify, WordPress), Gateway, or Direct
- [ ] Configure server endpoint to receive and forward events
- [ ] Map required parameters: event_name, event_time, event_source_url, action_source
- [ ] Map user data parameters: em, ph, fn, ln, ct, st, zp, country, external_id
- [ ] Include fbc and fbp cookie values
- [ ] Set event_id for deduplication with browser Pixel
- [ ] Test with Events Manager > Test Events tool
- [ ] Verify Event Match Quality > 6.0
- [ ] Monitor in Diagnostics for errors or dropped events
- [ ] Document integration for maintenance and team knowledge

### Event Priority (Recommended Order)
1. Purchase (with value and currency)
2. Lead / CompleteRegistration
3. AddToCart
4. InitiateCheckout
5. ViewContent
6. AddPaymentInfo
7. Search
8. PageView (lowest priority, usually Pixel-only)

## Budget Scaling Methodology

### The 20% Rule
Never increase budget more than **20% every 3–5 days**. Larger jumps reset the learning phase and destabilize performance.

### Scaling Decision Framework

| Signal | Action |
|---|---|
| CPA below target for 5+ days | Scale budget by 20% |
| CPA at target, stable | Hold, test new creative |
| CPA 10–30% above target | Refresh creative, check frequency |
| CPA 30%+ above target | Reduce budget, diagnose audience or creative fatigue |
| Frequency > 3.0 (prospecting) | Expand audience or pause/refresh creative |
| Frequency > 6.0 (retargeting) | Reduce budget or expand window |

### Horizontal vs Vertical Scaling

| Method | Description | When to Use |
|---|---|---|
| **Vertical** | Increase budget on winning campaigns | Stable CPA, headroom in audience |
| **Horizontal** | Duplicate winning ads into new audiences or campaigns | Audience saturation, testing expansion |

### Budget Allocation Framework (Starting Point)

| Funnel Stage | % of Total Budget | Objective |
|---|---|---|
| Prospecting (TOF) | 60–70% | New audience acquisition |
| Retargeting (MOF) | 15–25% | Warm audience conversion |
| Retention (BOF) | 10–15% | Customer LTV and repeat purchase |

## Key Benchmarks (Cross-Industry Averages)

| Metric | Prospecting | Retargeting | Advantage+ Shopping |
|---|---|---|---|
| CTR | 0.8–1.5% | 1.5–3.0% | 1.0–2.0% |
| CPC | $0.60–$2.00 | $0.30–$1.00 | $0.40–$1.50 |
| CPM | $8–$18 | $10–$25 | $8–$15 |
| Conv Rate | 1–3% | 4–10% | 2–5% |
| Frequency (healthy) | < 3.0 | < 6.0 | < 4.0 |

> **Note:** These are directional. Benchmarks vary widely by vertical, geography, season, and creative quality. Calibrate to your own data within 30 days of launch.
