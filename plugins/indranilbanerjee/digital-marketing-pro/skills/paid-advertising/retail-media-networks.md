# Retail Media Networks — Amazon, Walmart & More

## Retail Media Landscape Overview

### What Are Retail Media Networks (RMNs)?
Retail media networks are advertising platforms built on top of retailer ecosystems. They leverage first-party shopper data (purchase history, search behavior, browsing patterns) to deliver ads at or near the point of purchase. This is the fastest-growing segment of digital advertising, projected to exceed $150B globally by 2026.

### Why Retail Media Matters
- **First-party data**: Based on actual purchase behavior, not inferred interests
- **Closed-loop measurement**: See ad exposure through to purchase without attribution gaps
- **High purchase intent**: Shoppers are already in buying mode on retail platforms
- **Cookie-proof**: No reliance on third-party cookies or mobile IDs
- **Digital shelf influence**: Ads directly impact product visibility and organic ranking

### Retail Media Network Comparison

| Network | Monthly Visitors (US) | Ad Revenue | Self-Serve | Off-Site (DSP) | Strengths |
|---|---|---|---|---|---|
| **Amazon Ads** | 200M+ | $50B+ | Yes | Yes (Amazon DSP) | Deepest shopper data, largest scale |
| **Walmart Connect** | 120M+ | $3B+ | Yes | Yes (TTD partnership) | Omnichannel (in-store + online) |
| **Target Roundel** | 50M+ | $1.5B+ | Limited | Yes | Loyal customer base, household data |
| **Kroger Precision Mktg** | 60M+ | $1B+ | Limited | Yes (via 84.51°) | Grocery purchase data, CPG focus |
| **Instacart Ads** | 30M+ | $1B+ | Yes | Limited | Grocery delivery, impulse-at-cart |
| **Albertsons Media Collective** | 30M+ | Growing | Limited | Yes | Grocery loyalty data |
| **Best Buy Ads** | 50M+ | Growing | Limited | Yes | Electronics, appliance purchase data |
| **Ulta Beauty** | 30M+ | Growing | Limited | Yes | Beauty category authority |
| **Dollar General** | 20M+ | Growing | Limited | Yes | Rural, value shopper data |
| **Wayfair** | 40M+ | Growing | Yes | Limited | Home and furniture category |

## Amazon Ads Deep-Dive

### Ad Types Overview

| Ad Type | Placement | Targeting | Billing | Avg CPC/CPM | Best For |
|---|---|---|---|---|---|
| **Sponsored Products** | Search results, product pages | Keywords, product/category | CPC | $0.50–$2.00 | Direct sales, keyword conquest |
| **Sponsored Brands** | Top of search, video | Keywords, categories | CPC | $0.75–$3.00 | Brand awareness at point of search |
| **Sponsored Display** | Product pages, off-Amazon | Audience, product targeting | CPC/vCPM | $0.30–$1.50 | Retargeting, competitor targeting |
| **Amazon DSP** | Amazon + open web | Audience segments, AMC | CPM | $3–$10 (CPM) | Full-funnel, awareness, off-site |

### Sponsored Products Strategy

#### Match Type Strategy (Amazon-Specific)

| Match Type | Behavior | Strategy |
|---|---|---|
| **Broad** | Widest match, includes synonyms | Discovery, keyword research |
| **Phrase** | Contains phrase in order | Mid-funnel, category terms |
| **Exact** | Precise term match | Proven converters, brand defense |
| **Auto (Close Match)** | Amazon matches to product listing | Discovery and indexing |
| **Auto (Loose Match)** | Broader automated matching | Category exploration |
| **Auto (Substitutes)** | Competitor product pages | Competitive conquest |
| **Auto (Complements)** | Related product pages | Cross-sell, adjacency |

#### Sponsored Products Campaign Architecture
```
Account
├── Brand Defense Campaign (Exact match, brand terms)
│   └── Goal: Protect branded searches at low ACoS
├── Category Campaign (Phrase + Broad match)
│   └── Goal: Capture category demand
├── Competitor Conquest Campaign (Exact match, competitor brands)
│   └── Goal: Win competitor shoppers
├── Auto Campaign (all match types)
│   └── Goal: Discovery, feed keyword research to manual campaigns
└── Product Targeting Campaign
    └── Goal: Show on specific competitor/complementary ASINs
```

#### Keyword Research Workflow
1. Launch auto campaign → harvest converting search terms (7–14 days)
2. Move winners to manual exact match campaigns
3. Negate harvested terms from auto campaign to prevent overlap
4. Use Brand Analytics (top search terms) for category intelligence
5. Run broad match campaigns for ongoing discovery with tight ACoS targets
6. Review search term reports weekly; negate irrelevant terms

### Sponsored Brands Strategy

| Format | Description | Best For |
|---|---|---|
| **Product Collection** | Brand logo + headline + 3 products | Brand + category awareness |
| **Store Spotlight** | Brand logo + 3 store pages | Driving traffic to Brand Store |
| **Video** | Auto-playing video in search results | Product demonstration, differentiation |

### Sponsored Brands Best Practices
- [ ] Custom headline under 50 characters, benefit-focused
- [ ] Feature best-selling products (highest review count and rating)
- [ ] Link to Brand Store (not product page) for collection and spotlight
- [ ] Video: 15–30 seconds, loop-friendly, text overlays for silent viewing
- [ ] Test headline variations monthly (benefit vs feature vs promotion)

### Sponsored Display Strategy

| Targeting | Description | Use Case |
|---|---|---|
| **Product targeting** | Target specific ASINs or categories | Competitor conquest, cross-sell |
| **Audience: Views remarketing** | Retarget product/category viewers | Re-engage shoppers who didn't convert |
| **Audience: Purchase remarketing** | Retarget past purchasers | Replenishment, cross-sell |
| **Audience: In-market** | Amazon in-market segments | Prospecting high-intent shoppers |
| **Audience: Lifestyle** | Interest-based segments | Broader awareness within Amazon |

### Amazon DSP

#### Audience Segments Available

| Segment Type | Examples | Source |
|---|---|---|
| In-market | "In-market for running shoes" | Amazon browsing + purchase signals |
| Lifestyle | "Health enthusiasts," "Tech early adopters" | Long-term behavioral patterns |
| Remarketing | Product viewers, cart abandoners, past purchasers | Your product interaction data |
| Lookalike | Modeled from your purchasers or remarketing seeds | Amazon ML modeling |
| Advertiser audiences | CRM upload, website pixel (AAP tag) | Your first-party data |
| AMC custom audiences | Custom queries on Amazon Marketing Cloud | Cross-signal analysis |

#### Amazon DSP Checklist
- [ ] Define audience strategy: prospecting vs retargeting vs loyalty
- [ ] Set up Amazon Attribution for off-Amazon traffic measurement
- [ ] Create audience segments in DSP console or via AMC
- [ ] Prepare creative: display (300x250, 728x90, 160x600, 970x250) and video (15s/30s)
- [ ] Set frequency caps: 3–5/day (display), 2–3/day (video)
- [ ] Enable Amazon Audiences for prospecting campaigns
- [ ] Configure supply sources: Amazon owned (IMDb, Twitch, Fire TV) + open exchange
- [ ] Set up AMC (Amazon Marketing Cloud) for advanced attribution and overlap analysis

## Walmart Connect

### Ad Types

| Ad Type | Placement | Targeting | Billing |
|---|---|---|---|
| **Sponsored Products** | Search results, browse pages, product pages | Keywords (auto + manual), product | CPC |
| **Sponsored Brands** | Search banner, brand shelf | Keywords, category | CPC |
| **Display (onsite)** | Walmart.com + app | Audience, category, keyword | CPM |
| **Display (offsite)** | Walmart DSP (via TTD) | Walmart purchase data | CPM |

### Walmart Connect Unique Advantages
- **Omnichannel closed-loop**: Track online ad exposure to in-store purchase (via Walmart+, loyalty data)
- **In-store connection**: 4,700+ stores provide physical touchpoint data
- **TTD partnership**: Use Walmart first-party data for offsite programmatic targeting
- **Lower competition**: Less saturated than Amazon (lower CPCs for many categories)

### Walmart Connect Checklist
- [ ] Ensure product listings are optimized (content, images, reviews)
- [ ] Start with auto campaigns for keyword discovery
- [ ] Segment by brand, category, and competitor targets
- [ ] Set daily budget minimums ($50/day recommended for Sponsored Products)
- [ ] Monitor search term reports weekly (available in Walmart Ad Center)
- [ ] Leverage Walmart DSP for upper-funnel with offsite reach
- [ ] Track in-store attribution via Walmart's closed-loop reporting

## Target Roundel

### Capabilities

| Feature | Description |
|---|---|
| **Onsite display** | Ads on Target.com and Target app |
| **Offsite programmatic** | Reach Target shoppers across the open web |
| **CTV** | Connected TV ads using Target shopper data |
| **In-store (Roundel Media Studio)** | Digital screens, sampling, in-store media |
| **Measurement** | Closed-loop ROAS with Target Circle loyalty data |

### Target Roundel Best Practices
- [ ] Leverage Target Circle data for audience creation (120M+ members)
- [ ] Combine onsite + offsite for full-funnel coverage
- [ ] Focus on seasonal activations aligned with Target promotional calendar
- [ ] Use CTV for reaching Target households during streaming
- [ ] Minimum campaign investment typically $25K–$50K

## Kroger Precision Marketing (via 84.51°)

### Key Features
- Built on Kroger loyalty card data (60M+ households)
- Purchase-based targeting: category buyers, brand switchers, lapsed buyers
- Onsite ads on Kroger.com ecosystem (Kroger, Ralphs, Fred Meyer, etc.)
- Offsite programmatic via partnerships (TTD, Roku, Pinterest)
- Closed-loop sales measurement at household level

### Kroger Targeting Segments

| Segment | Description | Use Case |
|---|---|---|
| Brand buyers | Current purchasers of your brand | Loyalty, retention |
| Competitor buyers | Purchase competitor products | Conquest, trial |
| Category buyers | Active in category, not your brand | Category penetration |
| Lapsed buyers | Previously purchased, stopped | Win-back |
| New movers | Recently relocated households | Trial, introduction |

## Instacart Ads

### Ad Types

| Ad Type | Description | Placement |
|---|---|---|
| **Sponsored Products** | Promoted items in search and browse | Search results, category pages, post-checkout |
| **Display** | Banner ads across Instacart surfaces | Homepage, department pages, cart |
| **Shoppable Display** | Rich media with add-to-cart functionality | Homepage, interstitials |
| **Shoppable Video** | Video ads with direct purchase capability | In-app placements |

### Instacart Strategy Notes
- Instacart captures the impulse moment — shoppers are actively building baskets
- Sponsored Products at checkout influence last-minute additions
- Target competitive conquesting when shoppers search category terms
- Monitor incrementality: Instacart reports include new-to-brand metrics
- Minimum spend varies but typically $5K/month for meaningful testing

## Product Listing Optimization (Cross-Platform)

### Universal Listing Optimization Checklist

| Element | Amazon | Walmart | Instacart | Priority |
|---|---|---|---|---|
| **Title** | Brand + product + key attributes (200 chars) | Brand + product + attributes (75 chars) | Brand + product (mirror retailer) | Critical |
| **Images** | 7+ images, infographics, lifestyle, white BG main | 4+ images, white BG main | Mirror retailer images | Critical |
| **Bullet points** | 5 bullets, benefit-led, keyword-rich | Key features section | N/A (limited) | High |
| **Description / A+ Content** | Enhanced Brand Content (A+ pages) | Rich media modules | N/A | High |
| **Reviews** | 50+ reviews, 4.0+ rating target | 20+ reviews minimum | Linked to retailer reviews | Critical |
| **Keywords (backend)** | Search terms field (250 bytes) | Hidden keywords | N/A | High |
| **Price** | Competitive; avoid suppression | Price parity with Amazon | Set by retailer | High |
| **Availability** | In-stock rate >95% | In-stock rate >95% | In-stock rate >95% | Critical |

### Content Quality Impact on Ad Performance
- Products with A+ Content see 5–10% conversion rate lift on Amazon
- Products with 4.0+ star rating have 2x the conversion rate of 3.5-star products
- Rich, keyword-optimized titles improve ad relevance and reduce CPC
- In-stock consistency prevents wasted ad spend on unavailable products

## Budget Allocation Across Retail Media

### Budget Framework by Objective

| Objective | Sponsored Products | Sponsored Brands | Display / DSP | Offsite |
|---|---|---|---|---|
| Launch new product | 60% | 20% | 15% | 5% |
| Grow market share | 40% | 25% | 20% | 15% |
| Defend category leadership | 50% | 20% | 15% | 15% |
| Brand awareness | 15% | 25% | 30% | 30% |
| Seasonal push | 50% | 25% | 15% | 10% |

### Budget Allocation by Platform (Multi-Retailer)

| Factor | Consideration |
|---|---|
| Revenue share by retailer | Allocate proportionally to where your sales already happen |
| Category competition | Higher investment where competition is fierce |
| Data availability | Invest more where measurement is most complete |
| Growth opportunity | Overweight emerging RMNs with less competition and lower CPCs |
| Incrementality | Shift budget toward platforms proving incremental lift |

### Minimum Viable Budgets

| Platform | Monthly Minimum (Testing) | Monthly Recommended |
|---|---|---|
| Amazon Ads (Sponsored) | $5,000 | $15,000–$50,000+ |
| Amazon DSP | $10,000 (managed) | $35,000+ |
| Walmart Connect | $3,000 | $10,000–$30,000 |
| Target Roundel | $25,000 (campaign minimum) | $50,000+ |
| Instacart Ads | $5,000 | $10,000–$25,000 |
| Kroger (84.51°) | $25,000 (campaign minimum) | $50,000+ |

## Measurement Framework

### Key Retail Media Metrics

| Metric | Definition | Target Range | Why It Matters |
|---|---|---|---|
| **ACoS** (Advertising Cost of Sales) | Ad spend / attributed revenue | 15–30% (varies by category) | Core efficiency metric on Amazon |
| **ROAS** | Revenue / ad spend (inverse of ACoS) | 3x–7x | Universal efficiency metric |
| **TACoS** (Total ACoS) | Ad spend / total revenue (organic + paid) | 5–15% | Shows overall ad dependency |
| **New-to-Brand %** | % of conversions from first-time brand buyers | 40–70% (prospecting) | Measures true acquisition |
| **Share of Voice (SOV)** | % of top search results you own (paid + organic) | Varies by objective | Competitive position metric |
| **Conversion Rate** | Orders / clicks | 8–15% (Amazon SP average) | Listing and offer quality signal |
| **Impressions Share** | Your impressions / total available | 15–40% (category-dependent) | Market coverage |

### Measurement Checklist
- [ ] Set up Amazon Attribution for external traffic sources
- [ ] Configure AMC (Amazon Marketing Cloud) for cross-channel analysis
- [ ] Track TACoS alongside ACoS to monitor organic health
- [ ] Measure new-to-brand % for all prospecting campaigns
- [ ] Monitor SOV weekly using Brand Analytics or third-party tools (Helium 10, Jungle Scout)
- [ ] Compare ROAS across RMNs using consistent attribution windows
- [ ] Run incrementality tests (holdout markets or audiences) quarterly
- [ ] Report total retail media ROI to leadership monthly with blended ROAS

### Attribution Considerations
- Each RMN uses its own attribution model — they are not directly comparable
- Amazon: 14-day click attribution (Sponsored), 14-day click + 14-day view (DSP)
- Walmart: 14-day click attribution
- Standard caveat: all platforms over-attribute; cross-reference with sales data
- Use AMC or third-party tools (Pacvue, Skai, CommerceIQ) for unified reporting
- The most honest metric is TACoS: total ad spend relative to total sales on the platform

## Troubleshooting Common Issues

| Issue | Cause | Fix |
|---|---|---|
| High ACoS on Sponsored Products | Broad targeting, weak listing | Tighten match types, optimize listing content, negate irrelevant terms |
| Low impressions | Low bids, poor relevance, out of stock | Increase bids, ensure listing is indexed for target keywords, check inventory |
| High spend, low sales | Poor conversion rate | Optimize images, pricing, reviews; check competitor pricing |
| New-to-brand % declining | Retargeting existing customers | Shift budget to prospecting audiences, conquest campaigns |
| Budget not spending (Walmart/Instacart) | Low search volume, narrow targeting | Broaden targeting, add more keywords, increase bids |
| Share of voice declining | Competitor investment increasing | Increase investment on key terms, defend branded searches |
