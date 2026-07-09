# Programmatic Advertising — DSP, CTV & DOOH

## Programmatic Ecosystem Overview

### How Programmatic Works
```
Advertiser → DSP → Ad Exchange → SSP → Publisher
     ↑                  ↑
     └── DMP ──────────┘ (Audience Data)
```

### Key Components

| Component | Role | Examples |
|---|---|---|
| **DSP** (Demand-Side Platform) | Buys ad inventory on behalf of advertisers | DV360, The Trade Desk, Amazon DSP, Xandr |
| **SSP** (Supply-Side Platform) | Sells ad inventory on behalf of publishers | Google Ad Manager, Magnite, PubMatic, Index Exchange |
| **Ad Exchange** | Marketplace connecting DSPs and SSPs | Google AdX, OpenX, Xandr Marketplace |
| **DMP** (Data Management Platform) | Aggregates and segments audience data | Oracle BlueKai, Lotame, LiveRamp |
| **CDP** (Customer Data Platform) | Unifies first-party customer data | Segment, mParticle, Tealium |
| **Ad Server** | Serves ads and tracks delivery/performance | Campaign Manager 360 (CM360), Innovid, Flashtalking |
| **Verification** | Brand safety, viewability, fraud detection | IAS, DoubleVerify, MOAT, Pixalate |

### Transaction Flow (RTB)
1. User visits a web page or opens an app
2. Publisher's SSP sends a bid request with user/context data to the exchange
3. Exchange forwards bid request to connected DSPs
4. DSPs evaluate user data, campaign criteria, and bid in real-time (<100ms)
5. Highest bidder wins the impression
6. Winning ad is served to the user
7. Impression, click, and conversion data flows back for optimization

## DSP Selection Criteria

| Criteria | DV360 (Google) | The Trade Desk (TTD) | Amazon DSP | Xandr (Microsoft) |
|---|---|---|---|---|
| **Inventory access** | Google + open exchange | Open exchange (broadest) | Amazon + open exchange | Microsoft + open exchange |
| **Unique advantage** | YouTube integration, Google ecosystem | Independent, transparent, unified ID 2.0 | Amazon shopper data, retail signals | LinkedIn data, Netflix CTV |
| **CTV strength** | Strong (YouTube CTV) | Strongest (broadest CTV supply) | Moderate (Fire TV, Freevee) | Growing (Netflix partnership) |
| **Data/Targeting** | Google audiences, 1P data | 3P data marketplace, UID2 | Purchase intent, in-market | LinkedIn B2B, Microsoft graph |
| **Self-serve** | Yes (via DV360) | Yes | Limited (managed + self-serve) | Yes (via Invest) |
| **Minimum spend** | No minimum (self-serve) | $25K/month (typical) | $35K+ (managed); lower self-serve | Varies by contract |
| **Best for** | Google-centric stacks, YouTube | Independent, transparent buying | E-commerce, CPG, retail | B2B, Microsoft ecosystem |
| **Reporting** | Good (CM360 integration) | Excellent (Koa AI insights) | Good (Amazon Attribution) | Good |

### DSP Selection Decision Tree
```
START: What is your primary goal?
│
├── E-commerce / Retail → Amazon DSP (shopper data advantage)
├── B2B / Enterprise → Xandr (LinkedIn targeting)
├── Video / YouTube focus → DV360 (exclusive YouTube inventory)
├── CTV / Streaming priority → The Trade Desk (broadest CTV)
├── Transparency / Independence → The Trade Desk (no walled garden)
└── Already in Google stack → DV360 (ecosystem integration)
```

## Deal Types

| Deal Type | How It Works | Pricing | Inventory Guarantee | Best For |
|---|---|---|---|---|
| **Open Exchange (RTB)** | Real-time auction; anyone can bid | Market rate (CPM varies) | None | Scale, prospecting, testing |
| **Private Marketplace (PMP)** | Invite-only auction with select buyers | Floor price CPM | None (preferred access) | Premium inventory at competitive rates |
| **Preferred Deal** | Fixed CPM; buyer has first look before PMP/RTB | Negotiated fixed CPM | None (right of first refusal) | Consistent pricing, priority access |
| **Programmatic Guaranteed (PG)** | Fixed CPM, fixed impressions; reserved | Negotiated fixed CPM | Yes (guaranteed volume) | Tentpole events, must-have placements |

### Deal Type Selection Guide

| Scenario | Recommended Deal Type |
|---|---|
| Testing new publishers or inventory | Open Exchange |
| Access premium inventory at scale | PMP |
| Consistent CPMs with priority access | Preferred Deal |
| Guaranteed delivery for a product launch or event | Programmatic Guaranteed |
| Brand-safe environments required | PMP or PG (curated supply) |

## CTV (Connected TV) Planning Guide

### CTV Landscape

| Platform / Service | Ad-Supported Tier | Inventory Access Via |
|---|---|---|
| Hulu | Yes | Disney DSP, TTD, DV360 |
| Peacock (NBC) | Yes | TTD, DV360, Xandr |
| Max (HBO) | Yes (with ads tier) | TTD, DV360 |
| Paramount+ | Yes | TTD, DV360 |
| Netflix | Yes (with ads tier) | Microsoft/Xandr |
| Disney+ | Yes (with ads tier) | Disney DSP, TTD |
| Amazon Freevee / Prime Video | Yes | Amazon DSP |
| YouTube CTV | Yes | DV360 |
| Roku | Yes | TTD, DV360, Roku OneView |
| Samsung TV+ | Yes | TTD, DV360 |
| Tubi (Fox) | Yes (FAST) | TTD, DV360 |
| Pluto TV (Paramount) | Yes (FAST) | TTD, DV360 |

### CTV Campaign Planning Checklist
- [ ] Define target audience and geographic focus
- [ ] Select DSP(s) based on inventory and data needs
- [ ] Choose deal type: PMP for premium, open exchange for scale
- [ ] Set frequency cap: 3–5 impressions per household per week
- [ ] Prepare video assets: 15-second and 30-second spots (1920x1080 minimum)
- [ ] Implement cross-device tracking (household graph)
- [ ] Set up conversion tracking: website visits, app installs, or offline attribution
- [ ] Apply brand safety filters and content targeting
- [ ] Plan measurement: reach/frequency, brand lift, tune-in, foot traffic

### CTV Creative Specs

| Specification | Requirement |
|---|---|
| Resolution | 1920x1080 (Full HD) minimum; 3840x2160 (4K) preferred |
| Aspect ratio | 16:9 |
| Duration | 15s or 30s (6s bumpers available on some platforms) |
| File format | MP4 (H.264 codec) |
| File size | Under 1 GB (varies by platform) |
| Audio | Required — CTV is a lean-back, sound-on environment |
| Companion banner | 300x250 or 728x90 (optional, increases engagement) |

### CTV Benchmarks

| Metric | Average | Good | Excellent |
|---|---|---|---|
| VCR (Video Completion Rate) | 90–95% | 95%+ | 97%+ |
| CPM | $25–$45 | $20–$30 | < $20 |
| Reach (per $10K) | 50K–150K HH | 150K+ HH | 250K+ HH |
| Brand Lift | 3–8% | 8–15% | 15%+ |

## DOOH (Digital Out-of-Home) Strategy

### DOOH Venue Types

| Venue Category | Examples | Audience Context | Best For |
|---|---|---|---|
| Roadside / Billboard | Digital billboards, highways | Commuters, mass reach | Brand awareness, directional |
| Transit | Bus shelters, subway, airports | Urban commuters, travelers | Local, frequency-driven campaigns |
| Retail / Point-of-Purchase | In-store screens, mall kiosks | Shoppers near purchase moment | Retail, CPG, QSR |
| Place-Based | Gyms, doctors' offices, elevators | Captive, context-rich audience | Health, fitness, professional services |
| Spectaculars | Times Square, iconic locations | Tourists, event audiences | Tentpole moments, PR-worthy brand statements |

### Programmatic DOOH Platforms

| Platform | Strength | Inventory |
|---|---|---|
| Vistar Media | Largest pDOOH marketplace | 500K+ screens globally |
| Hivestack | Programmatic infrastructure | Global SSP partnerships |
| Place Exchange | SSP for OOH | Clear Channel, Lamar, JCDecaux |
| The Trade Desk | DSP with DOOH access | Via SSP integrations |
| DV360 | DSP with DOOH access | Via SSP integrations |

### DOOH Planning Checklist
- [ ] Define geographic targeting (DMA, zip code, POI radius)
- [ ] Select venue types aligned with audience behavior
- [ ] Choose buy type: programmatic guaranteed for premium, open exchange for flexibility
- [ ] Set dayparting aligned with audience presence (commute hours, lunch, evening)
- [ ] Prepare creative: simple, bold, max 5–7 words, high contrast
- [ ] Plan measurement: foot traffic lift, brand lift, QR code scans, promo code redemption
- [ ] Set frequency: 3–5 exposures per audience member over campaign flight
- [ ] Consider weather and event triggers for dynamic creative

## Audience Targeting Methods

| Method | Description | Data Source | Privacy Compliance |
|---|---|---|---|
| **First-Party Data** | Your own CRM, website, app data | CDP, CRM | Highest (consent-based) |
| **Contextual Targeting** | Target based on page content, not user | Real-time content analysis | Cookie-free, fully compliant |
| **Behavioral / Interest** | User browsing and purchase signals | DMP, DSP data marketplace | Requires consent; declining with cookie deprecation |
| **Lookalike / Modeled** | Expand from seed audience using ML | DSP modeling, LiveRamp | Moderate; depends on seed data |
| **Geofencing / Location** | Target users in/near physical locations | Mobile location data (Foursquare, etc.) | Requires opt-in location services |
| **Seller-Defined Audiences** | Publisher-created audience segments | Publisher first-party data | High (publisher consent flow) |
| **Universal ID** | Cross-site identity without cookies | UID2, RampID, ID5, SharedID | Consent-based, industry-supported |

### Post-Cookie Strategy Checklist
- [ ] Prioritize first-party data collection (email, login, loyalty programs)
- [ ] Implement contextual targeting as primary scale driver
- [ ] Test Universal ID solutions (UID2 via TTD, RampID via LiveRamp)
- [ ] Evaluate seller-defined audiences from premium publishers
- [ ] Invest in Google Privacy Sandbox APIs (Topics, Attribution Reporting)
- [ ] Shift measurement from last-click to incrementality and media mix modeling

## Brand Safety & Fraud Prevention

### Brand Safety Framework

| Layer | Solution | What It Does |
|---|---|---|
| Pre-bid | IAS, DoubleVerify, Oracle Contextual | Blocks unsafe inventory before bidding |
| Inclusion lists | Curated publisher lists | Only buy from approved sources |
| Exclusion lists | Block lists by domain, app, category | Prevent ads on specific content |
| Content categories | GARM framework alignment | Block by risk category (misinformation, hate speech, etc.) |
| Keyword blocking | Custom keyword lists | Avoid pages with specific terms |
| Post-bid monitoring | IAS, DV, MOAT | Verify where ads actually ran |

### Ad Fraud Prevention

| Fraud Type | Description | Prevention |
|---|---|---|
| Bot traffic | Non-human impressions and clicks | Pre-bid fraud filtering (IAS, DV) |
| Domain spoofing | Fake sites mimicking premium publishers | Ads.txt / app-ads.txt verification |
| Ad stacking | Multiple ads layered in one slot | Viewability verification |
| Pixel stuffing | Ad served in 1x1 pixel | Viewability standards (MRC) |
| Click injection | Mobile apps generating fake clicks | App-ads.txt, SDK-level validation |

### Fraud Prevention Checklist
- [ ] Enable pre-bid fraud filtering on all campaigns
- [ ] Verify ads.txt / app-ads.txt for all publishers
- [ ] Set viewability targets: 70%+ (display), 70%+ VCR (video)
- [ ] Monitor invalid traffic (IVT) rates — flag if > 5%
- [ ] Review placement reports weekly for suspicious domains/apps
- [ ] Use PMPs or PG deals for highest-value campaigns

## Viewability Standards

| Standard | Display | Video |
|---|---|---|
| **MRC Standard** | 50% of pixels in view for 1 continuous second | 50% of pixels in view for 2 continuous seconds |
| **GroupM Standard** | 100% of pixels in view for 1 second | 100% of pixels in view, 50% duration |
| **Industry Target** | 70%+ viewability | 70%+ VCR |

### Viewability Optimization Tips
- [ ] Prioritize above-the-fold placements
- [ ] Use high-impact formats (interstitial, adhesion, in-read video)
- [ ] Avoid infinite scroll pages and below-fold standard display
- [ ] Set viewability targets in DSP (minimum 60%, target 70%+)
- [ ] Use verified viewability vendors for third-party measurement
- [ ] Consider attention metrics beyond viewability (eye-tracking, dwell time)

## Key Programmatic Benchmarks

| Metric | Display (Open Exchange) | Display (PMP) | Video (Pre-roll) | CTV | DOOH |
|---|---|---|---|---|---|
| CPM | $1–$5 | $5–$15 | $10–$25 | $25–$45 | $5–$15 |
| CTR | 0.05–0.15% | 0.10–0.30% | 0.3–0.8% | N/A | N/A |
| Viewability | 50–65% | 65–80% | 70–85% | 95%+ | 90%+ (by design) |
| VCR | N/A | N/A | 65–80% | 90–97% | N/A |
| Fraud Rate | 5–15% | 2–5% | 3–8% | 1–3% | < 1% |

> **Note:** Programmatic benchmarks vary enormously by inventory source, deal type, targeting precision, and vertical. Open exchange carries the most variability. PMP and PG deals provide more predictable performance. Always layer verification vendors to ensure accuracy.
