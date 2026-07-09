# Native Advertising — Content Discovery & In-Feed Campaigns

## Platform Landscape

### Major Native Ad Networks

| Platform | Reach | Strength | Publisher Quality | Self-Serve | Min Spend |
|---|---|---|---|---|---|
| **Taboola** | 500M+ daily users, 9,000+ publishers | Largest content discovery network, strongest algorithm | Mixed (premium + long tail) | Yes | $10/day |
| **Outbrain** | 340M+ daily users, premium publishers | Premium publisher network (Condé Nast, BBC, CNN, Washington Post) | High (curated) | Yes | $20/day |
| **Nativo** | 600+ premium publishers | True native rendering — ad inherits publisher CSS/layout | Very high (brand-safe by default) | Managed + self-serve | $5K/month typical |
| **TripleLift** | Programmatic scale via DSPs | In-feed and in-article programmatic native | Varies (exchange-based) | Via DSP | DSP minimums apply |
| **Sharethrough** | Programmatic scale via DSPs | Enhanced native with headline optimization engine | Varies (exchange-based) | Via DSP | DSP minimums apply |
| **MGID** | 850M+ monthly users | Strong in EMEA and LATAM, lower CPCs | Mixed | Yes | $5/day |
| **Yahoo Native** | 900M+ monthly users | Yahoo/AOL properties, closed ecosystem | High (owned properties) | Yes (via Yahoo DSP) | Varies |

### Platform Selection Decision Tree

```
START: What is your primary goal?
│
├── Content amplification (blog posts, guides) → Taboola or Outbrain
├── Premium brand safety required → Nativo or Outbrain
├── Programmatic buying via DSP → TripleLift or Sharethrough
├── Lowest CPC / testing budgets → Taboola or MGID
├── Publisher-native look and feel → Nativo (true native rendering)
└── Headline optimization priority → Sharethrough (auto-enhanced headlines)
```

---

## Campaign Types

### Native Ad Formats Explained

| Format | Placement | User Experience | Best For |
|---|---|---|---|
| **Content Discovery** | Widget at bottom/side of articles ("Recommended For You") | User sees thumbnails + headlines among organic recommendations | Blog amplification, lead magnets, awareness |
| **In-Feed** | Appears within publisher content feed (between articles) | Seamless — matches surrounding editorial content | Product pages, landing pages, eCommerce |
| **Recommendation Widget** | Sidebar or bottom-of-article widget | Thumbnail grid or list alongside organic links | Content marketing, affiliate, lead gen |
| **In-Article** | Placed between paragraphs of editorial content | Integrated mid-read — high viewability | Brand awareness, video distribution |
| **Branded Content** | Full sponsored article on publisher site | Long-form storytelling, bylined or "Sponsored by" | Thought leadership, complex products, B2B |
| **Native Video** | Auto-play video in feed or in-article | Sound-off by default, captions essential | Product demos, brand stories, explainers |

---

## Creative Specifications

### Platform-by-Platform Specs

| Spec | Taboola | Outbrain | Nativo | TripleLift | Sharethrough |
|---|---|---|---|---|---|
| **Title length** | 60 chars (max 100) | 80 chars (max 150) | Publisher-dependent | 90 chars max | 90 chars max |
| **Description** | 150 chars | Not used | Publisher-dependent | 300 chars max | 200 chars max |
| **Image size** | 1000x600 min | 1200x800 min | Publisher template | Adaptive to supply | 1200x627 recommended |
| **Thumbnail** | 400x350 | 400x350 | N/A | N/A | N/A |
| **Text on image** | Allowed (max 20%) | Not allowed | Publisher rules | Not recommended | Not recommended |
| **Brand logo** | Optional | Not required | Publisher template | Recommended | Required |
| **Video** | MP4, 15-60s | MP4, 6-30s | Varies | VAST tag | VAST tag |
| **File size** | 5 MB max | 1 MB max | Varies | Via DSP specs | Via DSP specs |
| **Landing page** | Required | Required | Article or LP | Required | Required |

### Creative Best Practices

- **Headlines:** Questions outperform statements by 15-20%. Numbers outperform both ("7 Ways..." format). Avoid clickbait — platforms penalize misleading headlines with lower distribution.
- **Images:** Photos of people generate 30%+ higher CTR than objects or abstract images. Avoid stock photo aesthetics — editorial-style imagery blends better. Close-up shots outperform wide shots. High contrast and warm colors improve thumbnail performance.
- **Descriptions:** Lead with value proposition, not brand name. Include a soft CTA ("Learn how..." vs "Buy now").
- **Landing pages:** Article-style landing pages (advertorial format) convert better than product pages for cold traffic. Match landing page headline to ad headline for continuity. Include social proof early.

---

## Bidding & Budget Strategy

### Bidding Models

| Model | How It Works | Best For | Typical Range |
|---|---|---|---|
| **CPC** (Cost Per Click) | Pay only when user clicks | Content amplification, lead gen, testing | $0.20–$4.00 |
| **vCPM** (Viewable CPM) | Pay per 1,000 viewable impressions | Brand awareness, reach campaigns | $2.00–$12.00 |
| **Target CPA** | Platform optimizes to target cost per action | Conversion campaigns (requires pixel + data) | Varies by vertical |
| **Smart Bidding** | Platform auto-optimizes bids using ML | Mature campaigns with sufficient conversion data (50+/week) | Platform-managed |
| **oCPC** (Optimized CPC) | CPC with conversion optimization overlay | Transition from CPC to CPA optimization | Starts at CPC, adjusts to CPA |

### Budget Allocation Guidelines

| Campaign Phase | Budget Split | Duration | Goal |
|---|---|---|---|
| **Testing** | 20% of native budget | 1–2 weeks | Test 5+ headlines, 3+ images per campaign |
| **Optimization** | 30% of native budget | 2–4 weeks | Scale winners, kill losers, refine targeting |
| **Scaling** | 50% of native budget | Ongoing | Maximize volume at target CPA/ROAS |

**Budget minimums for statistical significance:**
- Per creative variant: $50–$100 minimum spend before judging performance
- Per campaign: $500+ over 2 weeks for reliable data
- Per publisher: 1,000+ impressions before evaluating publisher performance

---

## Audience Targeting

### Targeting Methods by Platform

| Method | Taboola | Outbrain | Nativo | Programmatic (TTL/Sharethrough) |
|---|---|---|---|---|
| **Interest-based** | Yes (reading behavior) | Yes (reading behavior) | Yes | Via DMP/DSP |
| **Contextual** | Yes (article topics) | Yes (article topics) | Yes (strong) | Yes |
| **Retargeting** | Pixel-based | Pixel-based | Pixel-based | DSP pixel + CRM |
| **Lookalike** | Seed audience expansion | Seed audience expansion | CRM-based | DSP modeling |
| **DMP segments** | Limited | Limited | Yes | Full DMP access |
| **Geo targeting** | Country/state/city | Country/state/city | Country/state/DMA | Full geo stack |
| **Device** | Desktop/mobile/tablet | Desktop/mobile/tablet | Yes | Full device graph |
| **Dayparting** | Yes | Yes | Yes | Yes |

### Targeting Strategy by Funnel Stage

| Stage | Targeting | Content Type | Bidding | Success Metric |
|---|---|---|---|---|
| **Awareness** | Broad interest + contextual | Educational articles, guides | vCPM or low CPC | CTR, time on page |
| **Consideration** | Retargeting + lookalike | Comparison guides, case studies | CPC | Scroll depth, pages/session |
| **Conversion** | Retargeting (site visitors) | Product pages, free trials, demos | CPA or oCPC | Conversions, CPA |

---

## Performance Benchmarks by Vertical

| Vertical | CTR | CPC | CVR (Click→Lead) | CPL | Time on Page |
|---|---|---|---|---|---|
| **Tech / SaaS** | 0.15–0.30% | $0.50–$1.50 | 3–8% | $15–$50 | 1:30–3:00 |
| **Finance / Insurance** | 0.10–0.20% | $1.00–$3.00 | 2–5% | $30–$100 | 2:00–4:00 |
| **Health / Wellness** | 0.20–0.40% | $0.30–$0.80 | 4–10% | $8–$25 | 1:00–2:30 |
| **eCommerce / Retail** | 0.15–0.35% | $0.40–$1.20 | 2–6% | $10–$40 | 0:45–2:00 |
| **B2B / Enterprise** | 0.08–0.18% | $1.50–$4.00 | 1–4% | $50–$150 | 2:00–5:00 |
| **Education** | 0.15–0.30% | $0.30–$1.00 | 5–12% | $5–$30 | 2:00–4:00 |
| **Real Estate** | 0.10–0.25% | $0.60–$2.00 | 2–5% | $20–$60 | 1:30–3:00 |

---

## Brand Safety & Quality

### Brand Safety Framework for Native

| Layer | Control | What It Does |
|---|---|---|
| **Publisher whitelists** | Manually curated approved publisher list | Only run on vetted, brand-safe sites |
| **Publisher blocklists** | Exclude specific domains | Block tabloids, low-quality sites, competitors |
| **Category exclusions** | Block content categories (news, politics, adult) | Prevent adjacency to sensitive topics |
| **Third-party verification** | IAS, DoubleVerify integration | Pre-bid and post-bid brand safety scoring |
| **Viewability standards** | MRC: 50% pixels in view for 1+ second | Ensure ads are actually seen |
| **Fraud detection** | Platform-native + third-party | Filter bot traffic, click fraud, domain spoofing |

### Quality Score Factors (Platform-Specific)

Taboola and Outbrain use internal quality scores that affect distribution and cost:
- **CTR performance** — Higher CTR relative to competition lowers effective CPC
- **Landing page quality** — Load speed, mobile optimization, content depth
- **Creative freshness** — New creatives get initial distribution boost; refresh every 2–3 weeks
- **Policy compliance** — Misleading claims, excessive capitalization, or clickbait reduce score
- **Post-click engagement** — Bounce rate, time on page, pages per session affect quality score over time

---

## Measurement & Attribution

### Native-Specific Metrics

| Metric | What It Measures | Benchmark | Why It Matters |
|---|---|---|---|
| **CTR** | Click rate on native ad | 0.15–0.35% | Primary efficiency metric |
| **Time on page** | Post-click engagement depth | 1:30+ minutes | Indicates content quality and audience fit |
| **Scroll depth** | % of landing page consumed | 50%+ | Measures content consumption |
| **Pages per session** | Navigation depth after click | 1.5+ | Shows deeper site engagement |
| **Bounce rate** | % who leave after one page | < 70% for articles | Lower is better — high bounce = targeting mismatch |
| **View-through conversions** | Conversions after seeing but not clicking ad | Varies | Captures awareness impact |
| **Assisted conversions** | Conversions where native was in the path | Varies | Shows native's role in the full funnel |
| **Content consumption rate** | % of article read (if article-as-LP) | 40%+ | Core metric for branded content campaigns |

### Attribution Approaches

- **Last-click:** Standard but undervalues native (native is usually top-of-funnel)
- **View-through:** Include impressions that led to conversions within 1–7 days (recommended: 1-day view, 7-day click window)
- **Multi-touch:** Assign partial credit to native in the conversion path (position-based or data-driven)
- **Brand lift studies:** Measure awareness, consideration, and intent lift from native exposure (available on Taboola and Outbrain for larger budgets)
- **Incrementality testing:** Holdout groups to measure true lift from native campaigns (gold standard but requires scale)

---

## Optimization Playbook

### Week-by-Week Optimization Timeline

| Week | Action | Decision Criteria |
|---|---|---|
| **Week 1** | Launch with 5+ headline variants, 3+ image variants per campaign. Broad targeting. CPC bidding. | Ensure all creatives get 1,000+ impressions |
| **Week 2** | Pause bottom 50% of creatives by CTR. Review publisher-level performance. Tighten targeting. | Kill creatives with CTR < 50% of top performer |
| **Week 3** | Add new creative variants inspired by winners. Begin publisher-level bid adjustments. Switch to oCPC if 50+ conversions. | New variants should iterate on winning headline/image patterns |
| **Week 4+** | Ongoing: refresh creatives every 2–3 weeks, expand to new platforms, scale winning publisher segments. | Creative fatigue = CTR decline > 20% from peak |

### Publisher-Level Optimization

- Export publisher performance report weekly
- Identify top 20% of publishers by conversion rate — increase bids 10–20% on these
- Identify bottom 20% by bounce rate or zero conversions — block them
- Build a "proven publishers" whitelist over time from consistent performers
- Test new publishers in a separate campaign at lower bids before adding to main campaigns

### Creative Refresh Strategy

- **Refresh cycle:** Every 2–3 weeks for high-volume campaigns, monthly for lower volume
- **Iteration method:** Take winning headline structure and swap the angle/benefit. Take winning image style and swap the subject.
- **Testing structure:** Always have 2–3 "proven" creatives running alongside 2–3 "test" creatives
- **Fatigue signals:** CTR drops 20%+ from peak, CPC rises 15%+, frequency exceeds 3x per user

---

## Integration with Content Marketing

### Content Amplification Strategy

```
Content Funnel for Native Advertising:

1. DISCOVERY (Native Ad) → 2. ENGAGEMENT (Article/Guide) → 3. CAPTURE (CTA/Form) → 4. NURTURE (Email/Retarget)
```

**Which content to amplify via native:**
- Blog posts with proven organic engagement (high time on page, low bounce rate)
- Evergreen guides and how-to content (long shelf life reduces creative refresh burden)
- Data-driven or original research content (high share potential, authority building)
- Comparison or "vs" content (captures consideration-stage intent)

**Content scoring for distribution:** Rate each piece on: organic engagement score (1-5), relevance to target audience (1-5), conversion potential (1-5), headline appeal for native (1-5). Amplify content scoring 16+ out of 20.

**Article-as-landing-page strategy:** Instead of driving native traffic to a product page, send users to an informative article (on your site or on the publisher via branded content). Include soft CTAs within the article. Retarget article readers with conversion-focused ads. This approach typically produces 2-3x higher engagement metrics and lower CPAs for complex or high-consideration products.

> **Key principle:** Native advertising works best when it delivers genuine value before asking for anything. The best-performing native campaigns feel like content recommendations, not advertisements. Optimize for engagement first, then conversion.
