# Retargeting & Remarketing — Audience Strategy Reference

## Audience Segment Taxonomy

### Website-Based Segments

| Segment | Definition | Typical Size | Intent Level | Recommended Window |
|---------|-----------|-------------|-------------|-------------------|
| All website visitors | Anyone who visited any page | Large | Low | 30-90 days |
| Specific page visitors | Visited product, pricing, or feature pages | Medium | Medium-High | 14-30 days |
| Category browsers | Viewed multiple products in same category | Medium | Medium | 14-30 days |
| Cart abandoners | Added to cart but did not purchase | Small-Medium | High | 7-14 days |
| Checkout starters | Began checkout flow, did not complete | Small | Very High | 3-7 days |
| Form starters | Started lead form, did not submit | Small | Very High | 7-14 days |
| Repeat visitors | 3+ visits in past 14 days | Small-Medium | High | 14-30 days |
| High-engagement visitors | Session duration >3 minutes or >5 pages | Small-Medium | Medium-High | 30-60 days |
| Blog/content readers | Visited blog or resource pages | Large | Low-Medium | 30-90 days |

### Customer-Based Segments

| Segment | Definition | Use Case |
|---------|-----------|----------|
| Past purchasers (recent) | Purchased in last 30-60 days | Cross-sell, complementary products |
| Past purchasers (lapsed) | Purchased 60-180 days ago, no repeat | Win-back, re-engagement offers |
| High-value customers | Top 20% by LTV or order value | VIP offers, loyalty, exclusions from discount ads |
| Subscription churned | Cancelled subscription in last 90 days | Win-back with improved offer |
| One-time buyers | Purchased once, never repeated | Second purchase incentive |
| Multi-buyers | 2+ purchases | Loyalty programs, referral asks |

### Engagement-Based Segments

| Segment | Definition | Platform |
|---------|-----------|----------|
| Video viewers (25/50/75/95%) | Watched video to specific completion | Meta, YouTube, TikTok |
| App users (active) | Used app in last 7-30 days | Meta, Google, TikTok |
| App users (lapsed) | Haven't opened app in 30+ days | Meta, Google, TikTok |
| Email openers | Opened email in last 30 days | Meta (Custom Audiences), Google (Customer Match) |
| Email non-openers | On list but no opens in 90+ days | Meta, Google |
| Social engagers | Liked, commented, shared, saved | Meta, TikTok, LinkedIn |
| Lead form openers | Opened in-platform lead form | Meta, LinkedIn, TikTok |
| Event attendees | Attended or RSVPed to event | Meta, LinkedIn |

### Expansion Segments

| Segment | Definition | Use Case |
|---------|-----------|----------|
| Lookalike / Similar (1%) | Top 1% most similar to seed audience | Highest-quality prospecting |
| Lookalike / Similar (1-3%) | Broader similarity match | Scaled prospecting |
| Lookalike / Similar (3-5%) | Widest useful similarity | Volume-focused prospecting |
| Customer Match lookalike | Similar to uploaded customer list | Acquisition of look-alike customers |
| High-value lookalike | Similar to top 20% customers by LTV | Best-customer acquisition |

---

## Platform-Specific Retargeting Capabilities

### Google Ads

| Feature | How It Works | Setup Requirement |
|---------|-------------|-------------------|
| RLSA (Remarketing Lists for Search Ads) | Bid adjustments or targeting for past visitors on search | Google Tag + audience list (1,000 minimum for search) |
| Display Remarketing | Banner ads to past visitors across Google Display Network | Google Tag + audience list (100 minimum for display) |
| YouTube Remarketing | Video ads to past visitors or channel engagers | Google Tag + linked YouTube channel |
| Dynamic Remarketing | Auto-generated ads showing specific products viewed | Google Tag + Merchant Center product feed |
| Customer Match | Upload email/phone lists for targeting on Search, YouTube, Gmail | Hashed customer list (minimum 1,000 matched users) |
| Similar Segments | Auto-generated audiences similar to your lists | Existing audience with 100+ users |

### Meta (Facebook & Instagram)

| Feature | How It Works | Setup Requirement |
|---------|-------------|-------------------|
| Website Custom Audiences | Target visitors by URL, time spent, events | Meta Pixel + Conversions API (CAPI) |
| Dynamic Product Ads (DPA) | Auto-show products users viewed/carted | Meta Pixel + Product Catalog |
| Engagement Custom Audiences | Target based on Instagram/Facebook engagement | Connected business page/account |
| Video Custom Audiences | Target by video view completion percentage | Video content published on Meta |
| Customer List Audiences | Upload email/phone for matching | Customer list (CSV upload or CRM integration) |
| Lookalike Audiences | Find similar users to seed audience | Seed audience (100+ people, 1,000+ recommended) |
| Advantage+ Catalog Ads | ML-optimized dynamic ads from catalog | Product catalog + Pixel + CAPI |

### LinkedIn

| Feature | How It Works | Setup Requirement |
|---------|-------------|-------------------|
| Website Retargeting | Target visitors who triggered LinkedIn Insight Tag | LinkedIn Insight Tag (300+ matched members) |
| Contact Targeting | Upload company or contact email lists | CSV list (10,000+ recommended for match rates) |
| Company Targeting | Target employees of specific companies | Company name or LinkedIn Company Page URL list |
| Video Viewers | Target users who viewed LinkedIn video ads | Previous video ad campaigns |
| Lead Gen Form Openers | Target users who opened but didn't submit form | Previous Lead Gen Form campaigns |
| Event Attendees | Target attendees of LinkedIn Events | LinkedIn Event association |
| Lookalike Audiences | Similar professionals to seed audience | Matched Audience with 300+ members |

### TikTok

| Feature | How It Works | Setup Requirement |
|---------|-------------|-------------------|
| Website Custom Audiences | Target visitors based on TikTok Pixel events | TikTok Pixel + Events API |
| App Activity Audiences | Target based on in-app events | App SDK integration |
| Engagement Audiences | Users who engaged with TikTok content | Published TikTok content or ad campaigns |
| Customer File Audiences | Upload email, phone, or device IDs | Customer list (CSV or partner integration) |
| Lookalike Audiences | Expand reach beyond seed audiences | Seed audience with 10,000+ users |

---

## Sequential Retargeting Strategies

### Awareness to Conversion Sequence

```
Stage 1: Awareness (Days 1-7 post-visit)
├── Creative: Brand story, social proof, educational content
├── Format: Video (15-30s), carousel showcasing range
├── Frequency cap: 1 impression/day
└── Goal: Build familiarity and trust

Stage 2: Consideration (Days 8-14)
├── Creative: Product benefits, comparison, testimonials
├── Format: Carousel, collection ads, case studies
├── Frequency cap: 2 impressions/day
└── Goal: Drive deeper engagement

Stage 3: Conversion (Days 15-21)
├── Creative: Specific offer, urgency, direct CTA
├── Format: Single image/video with strong CTA
├── Frequency cap: 3 impressions/day
└── Goal: Drive purchase or lead submission

Stage 4: Re-engagement (Days 22-30)
├── Creative: Final offer, scarcity, alternative products
├── Format: Dynamic ads, new angle messaging
├── Frequency cap: 1 impression/day
└── Goal: Capture remaining intent before audience expires
```

### Cart Abandonment Sequence

| Touchpoint | Timing | Channel | Message |
|-----------|--------|---------|---------|
| Email 1 | 1 hour | Email | Cart reminder, no discount |
| Retargeting ad | 2-6 hours | Meta/Google Display | Dynamic product ad, social proof |
| Email 2 | 24 hours | Email | Urgency + reviews |
| Retargeting ad | 24-72 hours | Meta/Google Display | Scarcity messaging, limited stock |
| Email 3 | 48-72 hours | Email | Small incentive (if margins allow) |
| Retargeting ad | 72+ hours | Meta/Google Display | Discount offer or free shipping |

---

## Frequency Capping Guidelines

| Segment Intent Level | Recommended Frequency Cap | Rationale |
|---------------------|--------------------------|-----------|
| Very high (checkout abandoners) | 5-7 impressions/week | High conversion probability justifies frequency |
| High (cart abandoners, repeat visitors) | 4-6 impressions/week | Strong intent, avoid oversaturation |
| Medium (page visitors, category browsers) | 3-5 impressions/week | Balance between reminder and annoyance |
| Low (all visitors, content readers) | 2-3 impressions/week | Light touch to stay top of mind |
| Prospecting (lookalikes) | 2-3 impressions/week | Cold audience, focus on reach over frequency |

### Burn Pixels and Exclusions

A burn pixel is a tracking event placed on the conversion/thank-you page that triggers audience exclusion.

- [ ] Place burn pixels on all conversion confirmation pages
- [ ] Exclude purchasers from acquisition campaigns (save budget, reduce annoyance)
- [ ] Re-include purchasers only in cross-sell or loyalty campaigns
- [ ] Exclude employees via IP, email list, or company targeting exclusion
- [ ] Exclude existing customers from free trial or demo campaigns
- [ ] Exclude users who completed forms from lead gen retargeting
- [ ] Set maximum exposure caps per user across all campaigns (platform-level)

---

## Dynamic Retargeting Setup

### Product Catalog Requirements

| Platform | Feed Format | Key Attributes | Refresh Frequency |
|----------|-----------|----------------|-------------------|
| Google Merchant Center | XML, TSV, CSV | id, title, description, image, price, availability, link | Every 6 hours minimum |
| Meta Catalog | CSV, XML, Google Sheets | id, title, description, image_link, price, availability, url | Daily minimum |
| TikTok Catalog | CSV, XML | sku_id, title, description, image_link, price, availability_status, landing_page_url | Daily minimum |

### Dynamic Ad Personalization Layers

| Layer | What Changes | Example |
|-------|-------------|---------|
| Product | Shows specific items the user viewed | "Still interested in the Blue Running Shoes?" |
| Category | Shows top products from browsed category | "Popular in Men's Running Shoes" |
| Price | Displays current price (including sales) | "$89.99 (was $129.99)" |
| Availability | Shows stock status | "Only 3 left in stock" |
| Social proof | Adds review stars or purchase count | "Rated 4.8/5 by 2,341 customers" |
| Recommendations | ML-driven cross-sell suggestions | "Customers also bought..." |

---

## Cross-Device Retargeting

### Matching Methods

| Method | Accuracy | Coverage | Requirement |
|--------|----------|----------|-------------|
| Deterministic (logged-in) | Very high (~95%) | Limited to logged-in users | User login across devices |
| Probabilistic (device graph) | Moderate (~60-70%) | Broader reach | Platform's device graph |
| Platform-native (Google, Meta) | High (~80-90%) | Platform-dependent | Platform tags + user logged in |
| Customer Match (email-based) | High | Limited to known users | Email list upload |
| First-party data (CDP) | High | Depends on data collection | CDP implementation |

### Cross-Device Strategy

- [ ] Ensure tracking tags fire on all devices (responsive site)
- [ ] Use Customer Match to unify known users across devices
- [ ] Enable Google Signals for cross-device GA4 reporting
- [ ] Implement Meta Conversions API (server-side) for better cross-device matching
- [ ] Design creatives for the device context (mobile-first creative for mobile retargeting)
- [ ] Attribute cross-device conversions in reporting (don't under-credit mobile)

---

## Privacy Impact on Retargeting

### Current Landscape

| Change | Impact | Status |
|--------|--------|--------|
| iOS ATT (App Tracking Transparency) | ~75% of iOS users opt out, reducing Meta audience sizes 30-40% | Active since iOS 14.5 |
| Third-party cookie deprecation | Chrome phasing out 3P cookies (delayed but inevitable) | In progress |
| Privacy Sandbox (Google) | Topics API and Attribution Reporting API replace 3P cookies | Rolling out |
| GDPR/CCPA consent | Requires explicit consent for tracking in EU and California | Active |
| Email privacy (Apple MPP) | Apple Mail open rates inflated, can't reliably segment by opens | Active since iOS 15 |

### Adaptation Strategies

| Strategy | Implementation | Impact |
|----------|---------------|--------|
| First-party data collection | Email capture, account creation, loyalty programs | Build owned audience data |
| Server-side tracking | Conversions API (Meta), Enhanced Conversions (Google) | Recover 15-25% of lost signal |
| Contextual targeting | Target based on page content, not user history | Privacy-compliant alternative |
| Google Enhanced Conversions | Send hashed first-party data with conversion tag | Better attribution and audience building |
| Meta CAPI | Server-to-server event passing | Recover lost iOS events |
| Customer Match / Custom Audiences | Upload first-party lists for targeting | Cookie-independent targeting |
| Modeled conversions | Platform ML estimates conversions from partial data | Fill attribution gaps |

---

## Retargeting Window Optimization

### Window Duration by Business Model

| Business Model | Consideration Period | Recommended Primary Window | Extended Window |
|---------------|---------------------|---------------------------|-----------------|
| Impulse eCommerce (<$50) | Hours to days | 7 days | 14 days |
| Considered eCommerce ($50-500) | Days to weeks | 14 days | 30 days |
| High-value eCommerce (>$500) | Weeks to months | 30 days | 60-90 days |
| B2B SaaS (SMB) | 1-4 weeks | 30 days | 60 days |
| B2B SaaS (Enterprise) | 1-6 months | 60 days | 90-180 days |
| Local services | Days to weeks | 14 days | 30 days |
| Travel / hospitality | Weeks to months | 30 days | 90 days |

### Layered Window Strategy

Create separate audience segments by recency and adjust bids accordingly:

| Window | Audience Label | Bid Adjustment | Creative Approach |
|--------|---------------|---------------|-------------------|
| 0-3 days | Hot visitors | +50-80% | Direct CTA, urgency |
| 4-7 days | Warm visitors | +30-50% | Benefits, social proof |
| 8-14 days | Cooling visitors | +10-20% | New angle, testimonials |
| 15-30 days | Cool visitors | Baseline | Brand reinforcement |
| 31-60 days | Cold visitors | -20-30% | Re-awareness, new content |
| 61-90 days | Dormant visitors | -40-50% | Brand story, education |

---

## Creative Strategy by Segment

| Segment | Creative Tone | Message Focus | CTA Style |
|---------|-------------|---------------|-----------|
| Cart abandoners | Urgent, helpful | Product-specific, address friction | "Complete your order" |
| Product page viewers | Informative, persuasive | Product benefits, reviews, comparisons | "Shop now" or "Learn more" |
| Category browsers | Discovery, curated | Category highlights, bestsellers | "Explore collection" |
| Blog/content readers | Educational, thought leadership | Related content, deeper resources | "Read more" or "Download guide" |
| Past customers (recent) | Appreciative, exclusive | Complementary products, new arrivals | "Shop new arrivals" |
| Past customers (lapsed) | Win-back, personal | "We miss you" + incentive or what's new | "Come back and save" |
| High-value customers | VIP, exclusive | Early access, loyalty perks, premium | "Exclusive access" |
| Form abandoners | Reassuring, simple | Simplify the ask, address concerns | "It only takes 2 minutes" |
| Video viewers (75%+) | Direct, next-step | Deeper product/service information | "See how it works" |

---

## Measurement Framework

### Attribution Models for Retargeting

| Model | How It Counts | Best For | Watch Out For |
|-------|-------------|----------|---------------|
| Click-through (7-day) | Conversion within 7 days of click | Direct response, conservative measurement | Misses view-through influence |
| Click-through (28-day) | Conversion within 28 days of click | Longer consideration products | May over-credit if window is too long |
| View-through (1-day) | Conversion within 1 day of impression (no click) | Understanding full retargeting influence | Can over-credit for high-frequency campaigns |
| View-through (7-day) | Conversion within 7 days of impression | Brand awareness retargeting | Likely over-credits; use for directional data only |
| Data-driven attribution | ML-distributed credit across touchpoints | Holistic measurement across channels | Requires significant conversion volume |

### Incrementality Testing

To measure the true lift of retargeting (not just capturing conversions that would happen anyway):

1. **Holdout test** — Suppress retargeting ads for a random 10-20% of your audience for 2-4 weeks
2. **Measure the gap** — Compare conversion rates between exposed group and holdout group
3. **Calculate incremental lift** — (Exposed CVR - Holdout CVR) / Holdout CVR = true retargeting lift
4. **Typical finding** — Retargeting usually drives 10-30% incremental lift (not 100% of attributed conversions)
5. **Adjust ROAS expectations** — True retargeting ROAS is typically 40-70% of reported ROAS after incrementality

### Key Metrics to Track

| Metric | Definition | Benchmark Range |
|--------|-----------|-----------------|
| Frequency | Avg impressions per user per week | 3-7 (varies by segment) |
| Reach | Unique users in audience | Depends on site traffic |
| View-through conversions | Conversions after ad view, no click | 20-50% of total retargeting conversions |
| Audience decay rate | Drop in conversion rate as window lengthens | 40-60% drop from Day 1-7 to Day 14-30 |
| Incremental ROAS | Revenue from true incremental conversions / Ad spend | 3-8x for well-optimized retargeting |
| Audience overlap | % of users appearing in multiple segments | Keep <30% to avoid bid competition |

---

*Retargeting is not about following people around the internet. It is about delivering the right message to the right person at the right moment in their decision process. The best retargeting strategies feel helpful, not invasive, and they adapt to privacy changes by building first-party data foundations rather than relying on third-party cookies.*
