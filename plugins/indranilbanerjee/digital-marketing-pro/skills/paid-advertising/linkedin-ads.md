# LinkedIn Ads — B2B Advertising Reference

## Campaign Types Overview

| Campaign Type | Objective Fit | Format | Avg CPC | Best For |
|---|---|---|---|---|
| Sponsored Content (Single Image) | Awareness, Leads, Web Visits | In-feed image + copy | $5–$12 | Thought leadership, content promotion |
| Sponsored Content (Video) | Awareness, Engagement | In-feed video | $0.06–$0.15 (CPV) | Brand storytelling, product demos |
| Sponsored Content (Carousel) | Engagement, Consideration | Multi-card swipeable | $4–$10 | Multi-feature showcase, case studies |
| Document Ads | Lead Gen, Engagement | In-feed downloadable doc | $4–$10 | Whitepapers, reports, guides |
| Message Ads (InMail) | Lead Gen, Event Promotion | Direct message | $0.30–$1.00 (per send) | High-value offers, event invites |
| Conversation Ads | Lead Gen | Interactive message tree | $0.30–$1.00 (per send) | Multi-path CTAs, qualification flows |
| Lead Gen Forms | Lead Capture | Native form overlay | $5–$15 | Gated content, demo requests |
| Dynamic Ads (Follower) | Page Growth | Right rail, personalized | $3–$7 | Company page follower acquisition |
| Dynamic Ads (Spotlight) | Traffic, Conversion | Right rail, personalized | $3–$7 | Personalized CTAs, job postings |
| Text Ads | Traffic | Right rail, small format | $2–$5 | Low-budget awareness, remarketing supplement |

## Targeting Deep-Dive

### Professional Targeting Dimensions

| Dimension | Targeting Options | Quality Rating | Notes |
|---|---|---|---|
| Job Title | Exact or standardized titles | Highest | Most precise; use for narrow ABM |
| Job Function | 26 categories (e.g., Marketing, IT, Finance) | High | Broader reach, good for awareness |
| Seniority Level | Entry, Senior, Manager, Director, VP, CXO, Owner | High | Combine with function for precision |
| Company Name | Specific organizations | Highest | ABM lists; min 300 company matches |
| Company Industry | 148 industries | Medium-High | Good top-of-funnel layer |
| Company Size | 1–10 up to 10,001+ (9 brackets) | High | Critical for SMB vs Enterprise targeting |
| Skills | Member-listed skills (2,000+) | Medium | Self-reported; broader but less reliable |
| Groups | LinkedIn group membership | Medium | Niche audiences; limited scale |
| Education | School, degree, field of study | Medium | Recruiting, higher education verticals |
| Years of Experience | 1–12+ years | Medium | Useful seniority proxy |
| Interests | Inferred from content engagement | Low-Medium | Supplement, don't rely on alone |

### Targeting Combination Best Practices
- [ ] Layer Job Function + Seniority for decision-maker targeting
- [ ] Use Company Name for ABM; Company Industry + Size for broader B2B
- [ ] Avoid overly narrow audiences — minimum 50,000 for Sponsored Content
- [ ] Exclude competitors, agencies, and job seekers when appropriate
- [ ] Use "OR" within a dimension, "AND" across dimensions
- [ ] Enable Audience Expansion only for awareness campaigns — disable for precision

### Audience Size Guidelines

| Campaign Type | Minimum Audience | Sweet Spot |
|---|---|---|
| Sponsored Content | 50,000 | 100,000–500,000 |
| Message Ads | 15,000 | 30,000–100,000 |
| Text/Dynamic Ads | 30,000 | 60,000–300,000 |
| ABM (Company List) | 300 companies | 1,000–10,000 companies |

## ABM (Account-Based Marketing) Strategies

### LinkedIn ABM Framework

```
Tier 1: Named Accounts (1:1)
├── Matched Audience: Upload company list (CSV)
├── Creative: Personalized by account/industry
├── Objective: Engagement, demo requests
└── Budget: Highest per-account spend

Tier 2: Industry Clusters (1:Few)
├── Targeting: Company industry + size + seniority
├── Creative: Industry-specific messaging
├── Objective: Content consumption, lead gen
└── Budget: Medium per-account spend

Tier 3: ICP Characteristics (1:Many)
├── Targeting: Function + seniority + company size
├── Creative: Persona-based, broad value prop
├── Objective: Awareness, nurture
└── Budget: Lowest per-account spend
```

### ABM Execution Checklist
- [ ] Upload target company list (CSV: company name, domain, industry)
- [ ] Match rate target: 70%+ (clean and standardize names)
- [ ] Layer with seniority/function to reach decision-makers within accounts
- [ ] Create account-specific or industry-specific creative
- [ ] Set up Website Demographics reporting for account-level engagement tracking
- [ ] Track engagement metrics: company-level impressions, clicks, leads
- [ ] Coordinate with sales team on account prioritization and follow-up

## Lead Gen Form Optimization

### Form Fields Performance Impact

| Number of Fields | Completion Rate | Use When |
|---|---|---|
| 2–3 fields | 12–15% | Maximizing volume (top of funnel) |
| 4–5 fields | 8–12% | Balanced quality and volume |
| 6–7 fields | 4–8% | Qualifying leads (bottom of funnel) |
| 8+ fields | < 4% | Enterprise qualification only |

### Recommended Field Configuration

| Field | Auto-Filled | Include? | Notes |
|---|---|---|---|
| First Name | Yes | Always | Pre-populated; no friction |
| Last Name | Yes | Always | Pre-populated; no friction |
| Email (work) | Yes | Always | Work email auto-filled; highest value |
| Job Title | Yes | Recommended | Qualification signal |
| Company Name | Yes | Recommended | ABM attribution |
| Phone Number | No | Optional | Adds friction; use for high-intent only |
| Company Size | No | Optional | Manual entry; qualification |
| Custom Question | No | Optional | Free text or multiple choice for intent |

### Lead Gen Form Best Practices
- [ ] Offer a clear, specific value exchange (not just "Learn More")
- [ ] Use custom thank-you message with next-step CTA
- [ ] Set up hidden fields for UTM tracking and campaign attribution
- [ ] Connect to CRM via integration (HubSpot, Salesforce, Zapier)
- [ ] Respond to leads within 5 minutes — conversion rate drops 80% after 30 minutes
- [ ] A/B test: short form (3 fields) vs qualifying form (5+ fields)

## B2B Funnel Structure

### Full-Funnel LinkedIn Campaign Architecture

| Stage | Objective | Campaign Type | Content Type | KPI |
|---|---|---|---|---|
| Awareness (TOF) | Brand recognition | Sponsored Content (Video) | Thought leadership, trends, POV | Video views, reach, engagement rate |
| Consideration (MOF) | Education + interest | Sponsored Content (Image/Carousel), Document Ads | Case studies, whitepapers, webinars | CTR, content downloads, engagement |
| Conversion (BOF) | Lead capture | Lead Gen Forms, Message Ads | Demo offers, free trial, consultation | CPL, lead volume, form completion rate |
| Retention | Upsell + loyalty | Sponsored Content, Conversation Ads | Product updates, customer stories | Engagement, expansion revenue |

### Retargeting Layers

| Audience | Lookback Window | Funnel Stage |
|---|---|---|
| Video viewers (50%+) | 90 days | MOF |
| Lead form openers (not submitted) | 90 days | BOF |
| Website visitors (key pages) | 180 days | MOF–BOF |
| Company page engagers | 365 days | MOF |
| Event attendees | 365 days | MOF–BOF |
| Customer list (CRM upload) | Refreshed monthly | Retention |

## Creative Specs & Best Practices

### Sponsored Content (Single Image)
- **Image size:** 1200x627 (1.91:1) or 1080x1080 (1:1)
- **Headline:** Max 70 characters (recommended) / 200 (limit)
- **Introductory text:** Max 150 characters above fold / 600 (limit)
- **File type:** JPG, PNG
- **Max file size:** 5 MB

### Sponsored Content (Video)
- **Aspect ratio:** 16:9 (landscape), 1:1 (square), 9:16 (vertical/mobile)
- **Length:** 15–90 seconds (sweet spot: 30 seconds)
- **File size:** 75 KB–200 MB
- **Captions:** Required (add SRT or burn in)

### Creative Best Practices for B2B
- [ ] Lead with insight, not product pitch — "What we learned from analyzing 10,000 B2B deals"
- [ ] Use data and specificity — "37% reduction in onboarding time" beats "faster onboarding"
- [ ] Include faces — posts with people get 2–3x engagement
- [ ] Use native, editorial-style creative — avoid stock photo aesthetics
- [ ] Test long-form vs short-form copy (LinkedIn audience reads)
- [ ] Always include a clear, single CTA in both copy and image

## Budget Recommendations

### Minimum Viable Budgets

| Campaign Goal | Monthly Minimum | Recommended Monthly | Notes |
|---|---|---|---|
| Awareness / Thought Leadership | $3,000 | $5,000–$10,000 | Need reach; LinkedIn CPMs are high ($30–$60) |
| Lead Generation | $5,000 | $10,000–$25,000 | Expect $30–$150 CPL depending on offer |
| ABM (Tier 1) | $5,000 | $10,000–$20,000 | Small audiences require sustained impressions |
| Full-Funnel B2B | $10,000 | $25,000–$50,000+ | Supports awareness + retargeting + lead gen |

### Budget Allocation by Funnel Stage (B2B)

| Stage | % of Budget | Rationale |
|---|---|---|
| Awareness (TOF) | 30–40% | Build audience, earn trust |
| Consideration (MOF) | 30–40% | Drive engagement with valuable content |
| Conversion (BOF) | 20–30% | Capture demand generated above |

## LinkedIn-Specific Benchmarks

| Metric | Sponsored Content | Message Ads | Lead Gen Forms | Text Ads |
|---|---|---|---|---|
| CTR | 0.4–0.7% | 3–5% (open rate: 30–50%) | 10–15% (form fill rate) | 0.02–0.05% |
| CPC | $5–$12 | N/A (cost per send) | $10–$50 (CPL) | $2–$5 |
| CPM | $30–$60 | N/A | $30–$60 | $8–$15 |
| Engagement Rate | 0.5–1.5% | N/A | N/A | N/A |
| Avg CPL | $50–$150 | $30–$100 | $30–$120 | $80–$200 |

### Key Metric Notes
- LinkedIn CPC is 3–5x higher than Meta or Google Display — that is normal and expected for B2B
- Value is in audience quality: decision-makers in verified professional profiles
- Measure downstream metrics (SQL rate, pipeline, revenue) not just CPL
- B2B sales cycles are 3–12 months — attribution must account for long consideration windows
- Use LinkedIn Insight Tag for website demographics reporting (see which companies visit)

## Troubleshooting Common Issues

| Issue | Likely Cause | Fix |
|---|---|---|
| Low delivery / impressions | Audience too narrow, bid too low | Expand audience to 100K+; increase bid above suggested range |
| High CPC, low CTR | Weak creative or poor targeting alignment | Test new creative angles; refine targeting to remove low-relevance segments |
| High CPL from Lead Gen Forms | Too many fields, weak offer | Reduce to 3–4 fields; strengthen value exchange |
| Low open rate on Message Ads | Weak subject line, wrong sender | Test subject lines under 40 chars; send from a person, not a brand |
| Low engagement rate | Content too promotional | Shift to thought leadership, data-driven, educational content |
| Poor match rate on company list | Inconsistent company names | Standardize against LinkedIn naming conventions; include domains |
