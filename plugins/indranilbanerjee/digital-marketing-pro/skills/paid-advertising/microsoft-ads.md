# Microsoft Advertising — Campaign Reference Guide

## Platform Overview

Microsoft Advertising (formerly Bing Ads) serves ads across the Microsoft Search Network, which includes Bing, Yahoo, AOL, DuckDuckGo syndication, and the Microsoft Audience Network (Outlook, MSN, Microsoft Edge, LinkedIn).

### Why Microsoft Ads Matters

| Factor | Detail |
|--------|--------|
| Search market share | ~30% of US desktop search (Bing + Yahoo + AOL combined) |
| Unique reach | 63 million searchers not reached by Google |
| Demographics | Skews older (35-54 primary), higher household income ($75K+), more educated |
| Device split | Heavy desktop usage (~60%), growing mobile presence |
| CPC advantage | 30-50% lower CPCs than Google Ads on average |
| LinkedIn integration | Only platform offering LinkedIn profile targeting for search and audience ads |
| Import capability | Direct campaign import from Google Ads reduces setup time to minutes |

### Audience Demographics Profile

| Demographic | Microsoft Search Network |
|-------------|------------------------|
| Age 35-54 | 40% of users (over-indexed vs Google) |
| Household income >$100K | 33% of users |
| College educated | 50%+ of users |
| Decision-makers | Higher proportion of B2B buyers, managers, directors |
| Desktop usage | ~60% of searches (higher than Google's desktop share) |

> **Strategic implication:** Microsoft Ads disproportionately reaches affluent, educated, desktop-heavy audiences making it particularly strong for B2B, financial services, luxury goods, real estate, and professional services.

---

## Campaign Types

| Campaign Type | Description | Best For | Targeting |
|---------------|-------------|----------|-----------|
| Search | Text ads on Bing, Yahoo, AOL SERPs | High-intent keyword capture | Keywords, audiences, demographics |
| Shopping | Product listing ads from Merchant Center | eCommerce product visibility | Product feed attributes |
| Audience | Native ads in Microsoft Audience Network | Mid-funnel consideration, remarketing | Audiences, placements, demographics |
| Display | Banner and responsive ads across partner sites | Awareness, retargeting | Audience segments, placements |
| Multimedia Ads | Large visual search ads (150x auto-generated) | Brand awareness on SERP | Keywords (auto-enabled for eligible campaigns) |
| Video Ads | Video placements across Microsoft network | Brand awareness, consideration | Audiences, demographics |
| Performance Max | AI-optimized across all Microsoft surfaces | Full-funnel automation | Audience signals + Microsoft AI |
| App Install | Drive mobile app installs | App acquisition | Device, audience, keyword |

### Microsoft Audience Network Placements

The Audience Network extends reach beyond search into native and display placements:

- **Microsoft Start (MSN)** — news feed native ads
- **Outlook.com** — inbox and reading pane native ads
- **Microsoft Edge** — new tab page and browser placements
- **Microsoft Casual Games** — in-game ad placements
- **Partner publisher sites** — curated network of premium publishers
- **LinkedIn feed** (via audience targeting) — professional context placements

---

## LinkedIn Profile Targeting (Unique to Microsoft)

This is Microsoft Ads' most significant competitive advantage. Advertisers can layer LinkedIn profile data onto search and audience campaigns.

### Available LinkedIn Targeting Dimensions

| Dimension | Examples | Use Case |
|-----------|----------|----------|
| Company | Microsoft, Salesforce, specific company names | ABM targeting, competitor employees |
| Industry | Financial Services, Technology, Healthcare | B2B vertical campaigns |
| Job Function | Marketing, Finance, IT, Engineering | Role-specific messaging |

### LinkedIn Targeting Best Practices

- [ ] Layer LinkedIn dimensions on top of keyword campaigns (don't replace keywords)
- [ ] Use bid adjustments (+20-50%) for high-value LinkedIn segments rather than restricting targeting
- [ ] Combine job function + industry for precise B2B audiences
- [ ] Create separate ad groups with LinkedIn targeting for tailored messaging
- [ ] Test company targeting for ABM campaigns aimed at named accounts
- [ ] Monitor audience size requirements: minimum 300 users for targeting to activate
- [ ] Use LinkedIn targeting in Audience campaigns for prospecting beyond search intent

### Example: B2B SaaS LinkedIn Targeting Setup

```
Campaign: Project Management Software — Non-Brand
├── Ad Group: General (all audiences, broad keywords)
├── Ad Group: IT Decision Makers
│   └── LinkedIn: Job Function = IT + Industry = Technology
│   └── Bid adjustment: +40%
├── Ad Group: Marketing Leaders
│   └── LinkedIn: Job Function = Marketing + Industry = Any
│   └── Bid adjustment: +30%
└── Ad Group: Enterprise Targets
    └── LinkedIn: Company = [named account list]
    └── Bid adjustment: +50%
```

---

## Import from Google Ads

### What Carries Over Cleanly

- Campaign and ad group structure
- Keywords and match types
- RSA headlines and descriptions
- Bid strategies (mapped to closest Microsoft equivalent)
- Ad extensions (sitelinks, callouts, structured snippets, call extensions)
- Negative keyword lists
- Location and language targeting
- Device bid adjustments

### What Needs Manual Adjustment After Import

| Element | Issue | Fix |
|---------|-------|-----|
| Bids and budgets | Google CPCs don't reflect Microsoft auction dynamics | Reduce bids by 20-30% initially, let data guide |
| Audience lists | Google audiences don't transfer | Rebuild UET-based audiences and import customer lists |
| Conversion tracking | Google tags aren't compatible | Install UET tag separately, configure conversion goals |
| Performance Max | Different signal architecture | Rebuild asset groups and audience signals |
| Automated bid strategies | Different ML models and data scale | Start with enhanced CPC, graduate to automated |
| Shopping feed | Requires separate Merchant Center setup | Connect Microsoft Merchant Center, import or sync feed |
| Display/video creative | Microsoft network has different specs | Review and reformat creative assets |
| Ad customizers | Syntax differences between platforms | Review and update customizer feeds |

### Import Workflow

1. **Import campaigns** via Microsoft Ads import tool (direct Google Ads connection)
2. **Reduce bids** by 20-30% across all campaigns
3. **Reduce budgets** to 15-20% of Google equivalent (start conservative)
4. **Install UET tag** on all site pages
5. **Set up conversion goals** matching your Google conversion events
6. **Rebuild audience lists** using UET data and customer match
7. **Add LinkedIn targeting** where relevant (this is net-new capability)
8. **Review ad extensions** for character limit differences
9. **Enable auto-tagging** or configure UTM parameters for analytics
10. **Monitor for 2-4 weeks** before making bid strategy changes

---

## Bidding Strategies

| Strategy | How It Works | Min. Data Needed | Best For |
|----------|-------------|------------------|----------|
| Enhanced CPC | Manual bids with automated adjustments up/down | Any volume | Starting point, low-volume campaigns |
| Target CPA | Automated bidding to hit cost-per-acquisition target | 30+ conversions/month | Lead gen with stable CPA goals |
| Maximize Conversions | Spends full budget to get maximum conversions | 15+ conversions/month | Budget-constrained volume goals |
| Target ROAS | Automated bidding to hit return on ad spend target | 50+ conversions/month | eCommerce with variable order values |
| Maximize Clicks | Automated bidding for maximum click volume | Any | Traffic campaigns, research/awareness |
| Target Impression Share | Bids to appear in a target % of eligible auctions | Any | Brand campaigns, competitive defense |
| Manual CPC | Full bid control, no automation | Any | Low volume, testing, granular control |

### Bidding Transition Path

```
Week 1-4: Enhanced CPC (establish baseline data)
    ↓ (accumulate 30+ conversions)
Week 5-8: Target CPA or Maximize Conversions
    ↓ (stable performance for 2+ weeks)
Week 9+: Optimize targets based on actual data
```

---

## Ad Extensions

| Extension | Function | Impact |
|-----------|----------|--------|
| Sitelink | Additional links below ad | +10-20% CTR lift |
| Callout | Short feature/benefit phrases | +5-10% CTR lift |
| Structured Snippet | Category-specific lists | Quality Score improvement |
| Call | Click-to-call phone number | Essential for local/service businesses |
| Location | Address from Microsoft Places | Drives foot traffic |
| Image | Visual assets alongside text ads | +15-20% CTR lift |
| Action | Secondary CTA button | Improves conversion path |
| Price | Product/service pricing grid | Pre-qualifies clicks, improves CVR |
| Promotion | Sale/discount callout with timing | Seasonal and promotional campaigns |
| Review | Third-party review excerpts | Trust building |
| Filter Link | Category navigation links | eCommerce product discovery |
| Video | Video content in search ads | Brand awareness on SERP |

---

## Key Differences vs Google Ads

| Factor | Microsoft Ads | Google Ads |
|--------|--------------|------------|
| Search volume | ~30% of US desktop | ~65% of all search |
| Avg CPC | 30-50% lower | Higher (more competition) |
| Audience demographics | Older, higher income, desktop-heavy | Broader, younger-skewing |
| LinkedIn targeting | Yes (exclusive) | No |
| ML/automation maturity | Improving but behind Google | Most advanced |
| Audience data scale | Smaller training data | Largest training data |
| Shopping feed | Microsoft Merchant Center | Google Merchant Center |
| Conversion tag | UET (Universal Event Tracking) | Google Tag / gtag.js |
| Customer Match | Available (lists, email) | Available (broader matching) |
| Responsive Search Ads | 15 headlines, 4 descriptions | 15 headlines, 4 descriptions |
| Image extensions | Available | Available |
| Performance Max | Available (newer) | More mature |
| Ad preview tool | Available | Available |
| Scripts/automation | Microsoft Ads Scripts (JavaScript) | Google Ads Scripts (JavaScript) |
| API | Microsoft Advertising API | Google Ads API |

---

## Budget Allocation Guidance

### Initial Microsoft Ads Budget as % of Google Ads Budget

| Scenario | Recommended Starting Budget | Rationale |
|----------|---------------------------|-----------|
| First-time Microsoft Ads | 10-15% of Google budget | Test waters, build data |
| Proven Google campaigns | 15-20% of Google budget | Scale what works |
| B2B / LinkedIn-targetable | 20-30% of Google budget | LinkedIn targeting justifies premium |
| Desktop-heavy verticals | 20-25% of Google budget | Microsoft over-indexes on desktop |
| eCommerce (general) | 10-15% of Google budget | Lower volume but efficient |

### Scaling Decision Framework

- **CPA is lower than Google by >20%?** Increase Microsoft budget by 25% per month
- **CPA is within 10% of Google?** Maintain and optimize before scaling
- **CPA is higher than Google?** Audit targeting, bids, and landing pages before scaling
- **LinkedIn targeting drives qualified leads?** Allocate additional budget specifically for LinkedIn-targeted campaigns

---

## UET Tag & Conversion Tracking

### Setup Checklist

- [ ] UET tag installed on all pages (via tag manager or direct)
- [ ] UET tag verified in Microsoft Ads Tag Helper extension
- [ ] Conversion goals created for each business objective (purchase, lead, signup)
- [ ] Revenue values passed for eCommerce conversions
- [ ] Enhanced conversions enabled (hashed email for cross-device matching)
- [ ] Offline conversion import configured (CRM integrations for B2B)
- [ ] Auto-tagging enabled or manual UTM parameters configured
- [ ] Audience lists building from UET data (check 1,000 minimum for targeting)
- [ ] Conversion window set appropriately (default 30 days, extend for longer B2B cycles)
- [ ] View-through conversion window configured (1-day recommended)

### Offline Conversion Tracking (B2B)

For businesses where conversions happen offline (calls, sales meetings, signed contracts):

1. **Pass Microsoft Click ID (MSCLKID)** with form submissions to your CRM
2. **Map CRM stages** to Microsoft Ads conversion goals
3. **Upload conversions** via file upload, API, or CRM connector (Salesforce, HubSpot)
4. **Set conversion windows** to match your sales cycle (30, 60, or 90 days)
5. **Use offline conversions** to train automated bidding on actual revenue, not just leads

---

## Reporting & Optimization

### Weekly Optimization Checklist

- [ ] Review search terms report — add negatives for irrelevant queries
- [ ] Check auction insights — monitor competitive landscape
- [ ] Review Quality Score changes — address drops in ad relevance or landing page
- [ ] Analyze device performance — adjust bids for over/under-performing devices
- [ ] Check demographic performance — adjust age and gender bid modifiers
- [ ] Review LinkedIn audience performance — identify high-converting segments
- [ ] Monitor ad extension performance — replace underperforming extensions
- [ ] Check budget pacing — ensure spend is distributed across the period
- [ ] Review RSA asset performance — replace "Low" rated headlines and descriptions

### Key Reports to Monitor

| Report | Frequency | What to Look For |
|--------|-----------|-----------------|
| Search Terms | Weekly | Irrelevant queries, new keyword opportunities |
| Auction Insights | Weekly | Impression share changes, new competitors |
| Device Performance | Bi-weekly | Desktop vs mobile conversion rate gaps |
| Demographics | Monthly | Age/gender bid adjustment opportunities |
| Geographic | Monthly | Location bid adjustments, exclusions |
| Ad Extension | Monthly | Extension performance, replace underperformers |
| LinkedIn Audience | Monthly | Segment-level ROAS for targeting refinement |
| Change History | As needed | Audit recent changes when performance shifts |

---

*Microsoft Ads is not a smaller version of Google Ads. It reaches a distinct audience with different demographics, behaviors, and intent signals. The combination of lower CPCs and LinkedIn profile targeting makes it uniquely valuable for B2B advertisers and any brand targeting affluent, desktop-heavy audiences.*
