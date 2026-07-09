# Competitive Monitoring Guide

Reference knowledge for ongoing competitor intelligence, change detection, social listening, share of voice calculation, competitive response playbooks, and alert management. Use this when setting up or executing competitive monitoring workflows.

---

## 1. Competitor Identification and Categorization

### Category Definitions

| Category | Definition | Examples | Monitoring Priority |
|---|---|---|---|
| **Direct** | Same product/service, same target market. Competes for the same customers and keywords. | Two SaaS project management tools targeting mid-market | Highest — monitor daily to weekly |
| **Indirect** | Different product, solves the same underlying need. Customers choose between you. | Project management tool vs. spreadsheet-based workflow | Medium — monitor weekly to monthly |
| **Aspirational** | Where you want to be. Market leaders or category-defining brands you benchmark against. | A startup benchmarking against Salesforce or HubSpot | Low — monitor monthly to quarterly |
| **Emerging** | Startups, new entrants, or adjacent players expanding into your market. | A CRM adding project management features | Medium-high — monitor weekly (early detection is critical) |

### Competitor Profiling Template

For each tracked competitor, maintain a structured profile:

- **Company**: Name, URL, founding year, funding stage/revenue estimate, employee count
- **Product**: Core features, pricing tiers, free tier availability, key differentiators
- **Market**: Target segments, geographic focus, vertical specializations
- **Digital presence**: Domain authority, estimated organic traffic, top ranking keywords (count), social following by platform, ad spend estimates
- **Content strategy**: Blog cadence, content types (blog, video, podcast, webinar), gated vs. ungated ratio
- **Messaging**: Tagline, primary value proposition, positioning statement, key claims
- **Last updated**: Timestamp of most recent profile refresh

---

## 2. Monitoring Cadence by Category

### Daily Monitoring (Automated)

- **Pricing changes**: Scrape pricing pages. Compare to stored snapshot. Alert on any change to tier names, prices, feature inclusions, or plan structure
- **Stock/availability changes**: For eCommerce competitors, monitor product availability status changes
- **Critical keyword movements**: Track positions for top 10-20 head terms. Alert on competitor entering top 3 or displacing your position
- **Ad creative changes**: Monitor Google Ads Transparency Center and Meta Ad Library for new creatives from tracked competitors
- **Press/news mentions**: News API or Google Alerts for competitor brand mentions in news sources

### Weekly Monitoring

- **Content publishing**: Check competitor blog RSS feeds or scrape blog index pages. Log new posts with title, URL, topic, word count estimate, target keyword
- **Social media activity**: Pull posting frequency, engagement rates, follower growth. Flag anomalies (posting frequency change >50%, engagement spike >3x average)
- **Backlink acquisition**: Check new referring domains to competitor sites via backlink monitoring APIs. Flag high-authority links (DA 60+)
- **Ad messaging themes**: Review active ads across platforms. Categorize by offer type (discount, free trial, feature highlight, social proof)
- **SERP feature changes**: Track which competitors appear in Featured Snippets, AI Overviews, PAA, Knowledge Panels for target keywords

### Monthly Monitoring

- **Strategy shifts**: Review competitor blog topics, ad messaging, product updates, and hiring patterns for strategic direction signals
- **Positioning changes**: Compare current messaging to previous month. Flag tagline changes, new claims, repositioning language
- **Share of voice recalculation**: Full SOV analysis across organic, paid, and social channels
- **Technology stack changes**: Monitor via BuiltWith or similar for CMS, analytics, marketing automation, CRM platform changes
- **Review/sentiment trends**: Aggregate G2, Capterra, Trustpilot ratings. Track sentiment trajectory

### Quarterly Monitoring

- **Full competitive audit**: Complete refresh of all competitor profiles. Update market positioning map
- **Win/loss analysis**: Review CRM win/loss data for the quarter. Identify competitor-specific patterns
- **Content gap analysis**: Compare your content coverage to top 3 competitors. Identify topics they cover that you do not
- **Feature comparison matrix update**: Refresh product feature comparison. Note new features, deprecated features, pricing changes

---

## 3. Change Detection Methodology

### HTML Diffing for Content Changes

- **Page content hashing**: Generate SHA-256 hash of main content area (exclude navigation, footer, ads). Compare to stored hash. Hash change = content change
- **Selective element monitoring**: Track specific CSS selectors per competitor page:
  - Pricing page: `.pricing-table`, `.plan-card`, `.price-amount`
  - Homepage: `.hero-section`, `.value-prop`, `.social-proof`
  - Product page: `.feature-list`, `.integration-list`, `.changelog`
- **Diff generation**: When hash changes, generate line-by-line diff. Classify change as: minor (typo, formatting), moderate (copy update, new section), major (restructure, new page, pricing change)
- **Screenshot comparison**: Capture viewport screenshots before and after change detection. Visual diff highlights layout/design changes that text diffing misses

### Meta Tag Monitoring

Track per competitor page per check:

| Element | Detection | Significance |
|---|---|---|
| `<title>` tag | Exact string comparison | Keyword targeting change, brand positioning shift |
| `<meta name="description">` | Exact string comparison | Messaging or CTA change |
| `<meta name="robots">` | Exact string comparison | Indexing strategy change (noindex = page being removed) |
| Canonical URL | Exact string comparison | URL structure change, consolidation signal |
| Schema markup types | Parse JSON-LD, compare `@type` values | Rich result strategy change |
| OG tags | Compare `og:title`, `og:description`, `og:image` | Social messaging or creative change |
| Hreflang tags | Count and language codes | International expansion or contraction |

### Structural Change Detection

- **Navigation monitoring**: Parse main navigation links. Flag new menu items (new product, new feature page, new resource section)
- **Sitemap monitoring**: Download and parse `sitemap.xml`. Compare URL count and new URLs to previous snapshot. New URLs indicate new pages/sections
- **Page count tracking**: Track total indexed pages via `site:competitor.com` query count. Significant increases indicate content pushes; decreases indicate pruning

---

## 4. Share of Voice Calculation

### Organic Share of Voice

**Formula**: SOV = Sum of (estimated traffic per keyword) / Sum of (total estimated traffic for all tracked keywords across all competitors)

**Calculation steps**:
1. Define keyword universe: all target keywords relevant to the category (100-1,000 keywords)
2. Pull ranking positions for all competitors for each keyword
3. Apply CTR curve to estimate traffic per keyword per competitor:
   - Position 1: ~28% CTR, Position 2: ~15%, Position 3: ~11%, Position 4: ~8%, Position 5: ~7%
   - Position 6-10: ~2-5%, Position 11-20: ~0.5-2%, Position 21+: ~0%
4. Multiply estimated CTR by keyword search volume = estimated traffic
5. Sum per competitor, divide by total = SOV percentage

### Paid Share of Voice

- **Google Ads Auction Insights**: `impression_share` metric per campaign/keyword. Divide your impression share by sum of all competitors' impression shares for normalized SOV
- **Meta Ads**: Use reach and frequency estimates from Meta Ad Library. Calculate share based on estimated impressions in target audience
- **Spend-based SOV**: If spend data is available (via competitive intelligence tools), SOV = your spend / total category spend
- **SERP ad presence**: For target keywords, count how often each competitor's ad appears in top positions. Presence rate = ad SOV proxy

### Social Share of Voice

- **Volume-based**: Count of brand mentions (including hashtags, @mentions, organic discussion) / total category mentions. Source: social listening tool with Boolean queries
- **Engagement-weighted**: Weight mentions by engagement (likes, shares, comments). Higher-engagement mentions count more
- **Sentiment-adjusted**: Multiply mention volume by sentiment score (positive = 1.0, neutral = 0.5, negative = 0.0). Prevents brands with high negative buzz from showing inflated SOV

### Feature-Weighted SOV (Composite)

Combine channel SOVs with strategic weighting:

| Channel | Suggested Weight | Rationale |
|---|---|---|
| Organic search | 35% | High-intent traffic, long-term brand authority |
| Paid search | 20% | Direct conversion channel, reflects investment level |
| Social organic | 15% | Brand awareness and community engagement |
| Social paid | 15% | Targeted reach, campaign-driven visibility |
| AI engine visibility | 15% | Growing channel, represents future discovery patterns |

---

## 5. Competitive Response Playbooks

### Competitor Price Drop

1. **Detect**: Pricing page change detected. Calculate % reduction and affected tiers
2. **Assess**: Determine if price drop is permanent, promotional, or segment-specific. Check for accompanying messaging changes (new tagline, "most affordable" positioning)
3. **Decision tree**:
   - If competitor targets your strongest segment: **High urgency**. Prepare value-based counter-messaging within 48 hours. Do not match price unless margin analysis supports it
   - If competitor targets a segment you are weak in: **Low urgency**. Monitor for 2 weeks. Assess if their pricing attracts your existing customers
   - If promotional/temporary: **No immediate action**. Document promotion terms and duration. Prepare counter-promotion if deal velocity drops
4. **Response options**: Emphasize value/ROI over price, bundle features to increase perceived value, introduce a competitive migration offer (limited time), create comparison content highlighting total cost of ownership

### Competitor Product Launch

- **T+0 (Detection)**: Log launch details — feature name, positioning, pricing impact, target segment
- **T+24h (Analysis)**: Deep-dive on feature capabilities. Test if possible (free trial, demo). Assess overlap with your roadmap
- **T+48h (Messaging)**: Draft positioning response. Options: "we already do this" (if true), "here's why our approach is better," or "this validates the category we're building"
- **T+1 week (Content)**: Publish comparison content if strategically valuable. Update feature comparison pages. Brief sales team with competitive battle card
- **T+1 month (Assessment)**: Monitor adoption signals (social mentions, review site feedback, search volume for feature name). Determine if a product response is needed

### Competitor Content Push

- **Signal**: Competitor increases publishing frequency >2x or launches new content format (podcast, video series, newsletter)
- **Assessment**: Analyze content topics for keyword overlap with your strategy. Check if their new content is ranking for your target terms
- **Response**: Prioritize content creation for overlapping keywords where you have ranking potential. Accelerate planned content in affected topic clusters. Do not reactively create content on topics outside your strategy

---

## 6. Win/Loss Feedback Integration

### CRM Data Collection Points

- **Deal stage field**: `Competitor Mentioned` — multi-select field populated during discovery and negotiation stages
- **Win/loss reason**: Structured field with categories: Price, Features, Brand/Trust, Relationship, Timing, Integration, Support
- **Post-decision survey**: Sent within 48 hours of closed-won or closed-lost. 3-5 questions: primary alternative considered, decisive factor, perception of each vendor
- **Sales debrief notes**: Free-text field for qualitative context from the sales rep

### Analysis Patterns

- **Competitor frequency**: Which competitors appear most in deals? Trend over time (increasing = growing threat)
- **Win rate by competitor**: When competitor X is in the deal, what is your win rate? Segment by deal size, segment, and region
- **Loss reason by competitor**: When you lose to competitor X, why? Identifies specific weaknesses to address
- **Content influence**: Which content pieces were shared during deals you won vs. lost? Identifies effective competitive content
- **Segment vulnerability**: Are certain customer segments more likely to choose specific competitors? Guides targeting and positioning

---

## 7. Alert Management and Escalation

### Escalation Tiers

| Tier | Trigger | Response Time | Notification Channel | Recipient |
|---|---|---|---|---|
| **P1 — Critical** | Pricing change, product launch, acquisition, executive departure, major rebrand | < 4 hours | Slack DM + email | Marketing lead, product lead, sales lead |
| **P2 — Important** | Messaging change, new ad campaign, significant content push, new partnership | < 24 hours | Slack channel | Marketing team |
| **P3 — Informational** | Minor content updates, social activity changes, small feature updates | Weekly digest | Email digest | Subscribed stakeholders |

### Alert Fatigue Prevention

- **Deduplication**: Group related changes into a single alert (e.g., 5 new blog posts = 1 "content push" alert, not 5 separate alerts)
- **Threshold tuning**: Start with sensitive thresholds, then widen based on false positive rate. Target: <20% false positive rate
- **Digest mode**: P3 alerts always delivered as weekly digest. Never real-time for informational changes
- **Snooze capability**: Allow recipients to snooze specific competitors or change types for defined periods
- **Channel routing**: Different alert types to different channels. Sales gets pricing/product alerts. Content team gets content/SEO alerts. Leadership gets P1 only

### Competitive Intelligence Database Schema

```
competitors (
  id, name, url, category, status, created_at, updated_at
)
competitor_snapshots (
  id, competitor_id, page_type, content_hash, screenshot_path,
  meta_title, meta_description, schema_types, snapshot_date
)
change_log (
  id, competitor_id, change_type, severity, page_url,
  old_value, new_value, detected_at, acknowledged_by, acknowledged_at
)
pricing_history (
  id, competitor_id, plan_name, price, currency, billing_cycle,
  features_json, effective_date, detected_at
)
content_inventory (
  id, competitor_id, url, title, publish_date, word_count,
  estimated_keyword, content_type, first_detected
)
alert_history (
  id, competitor_id, alert_tier, alert_type, message,
  sent_at, channel, acknowledged, response_action
)
```

---

## 8. Ad Monitoring Sources

### Google Ads Transparency Center

- **URL**: `https://adstransparency.google.com/`
- **Search by**: Advertiser name, domain, or keyword topic
- **Data available**: All ads run by an advertiser in the last 30 days, ad format (text, image, video), regions where ad was shown, date ranges
- **Limitations**: No spend data, no targeting data, no performance data. Creative and messaging analysis only
- **Monitoring approach**: Weekly screenshot captures of active ads. Categorize by messaging theme, offer type, and CTA. Track creative rotation frequency

### Meta Ad Library

- **URL**: `https://www.facebook.com/ads/library/`
- **API**: `GET /ads_archive` with `search_terms`, `ad_reached_countries`, `ad_active_status`
- **Data available**: All active and inactive ads, creative assets (image/video), ad copy, start date, platform (Facebook, Instagram, Messenger, Audience Network), page name
- **For political/social ads**: Additional data includes spend ranges, impressions, demographic reach
- **Monitoring approach**: Pull active ads weekly via API. Store creatives and copy. Compare to previous week to identify new campaigns, paused campaigns, and creative refreshes

### LinkedIn Ad Monitoring

- **No public ad library** (unlike Google and Meta). Monitor via:
  - Following competitor company pages and checking "Ads" tab
  - LinkedIn feed observation (sponsored content appears in-feed)
  - Third-party tools that aggregate LinkedIn ad sightings
- **Data limitations**: Cannot see all ads, targeting, or spend. Best-effort monitoring only

### Competitive Ad Analysis Framework

For each captured ad, document:

- **Messaging theme**: What value proposition is emphasized? (price, features, outcomes, social proof, urgency)
- **Offer type**: Free trial, discount, demo, content download, webinar, no specific offer
- **CTA**: Exact CTA text and action type (learn more, sign up, buy now, get started, talk to sales)
- **Landing page**: Destination URL and page type (homepage, product page, landing page, content, pricing)
- **Creative style**: Photo, illustration, screenshot, video, carousel, UGC-style, testimonial
- **Trend analysis**: Week-over-week, which themes are increasing? Which offers are being tested? Which creatives have the longest run time (likely high performers)?
