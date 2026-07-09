---
name: local-seo
description: "Build local SEO strategy. Use when: optimizing Google Business Profile, fixing NAP consistency, improving local pack rankings."
---

# Local SEO

## When to Use This Skill

## Context efficiency

Heavy skill. **Grep before Read** any referenced file, then `Read` only matched ranges with `offset` + `limit`. List `${CLAUDE_PLUGIN_DATA}/<brand>/` before opening files. On re-invocation mid-session, skip files already in context.

## 2026 priority — Google Agentic Booking expansion

At I/O 2026 Google expanded its **agentic booking flow** beyond restaurants to:

- **Local services** (cleaners, electricians, plumbers, handymen)
- **Home repair** (general contractors, HVAC, appliance repair)
- **Beauty** (hair salons, spas, nail studios)
- **Pet care** (groomers, walkers, vets)

If your brand is in any of these 4 verticals, agentic booking is now a high-leverage local-SEO investment. Three things matter for opt-in:

1. **Google Business Profile must accept bookings.** Either via Google's direct integration with supported scheduling vendors (Booksy, Vagaro, Square Appointments, Resy, Tock, etc.) or via Reserve with Google.
2. **`AvailabilityFeed` structured data must be served** so the AI agent can reason about open slots without making the call. See `skills/context-engine/schema-templates.json` for the `LocalBusiness` + `Reservation` + `AvailabilityFeed` pairing.
3. **Pricing transparency in Service catalog** — agents prefer businesses that list price ranges; opaque pricing pushes the agent to the next option.

Source: [blog.google/search-io-2026](https://blog.google/products-and-platforms/products/search/search-io-2026/). Combine with Google Ads API v24.2's new `AssetGroup.google_local_services_info` field (see `skills/paid-advertising/google-ads.md`) for the paid-side complement.

Activate this module when the user's request involves any of the following:

- **Google Business Profile Optimization**: Setting up, optimizing, or auditing a Google Business Profile (categories, attributes, photos, posts, Q&A, products, services)
- **Local Citations**: Building, auditing, or cleaning up business listings across directories and data aggregators
- **NAP Consistency**: Auditing Name, Address, Phone number consistency across the web
- **Local Pack / Map Pack Rankings**: Strategies to appear in the Google 3-pack and Google Maps results
- **Location Pages**: Creating or optimizing landing pages for individual business locations or service areas
- **Multi-Location SEO**: Managing local SEO at scale for businesses with multiple physical locations or franchise operations
- **"Near Me" Optimization**: Optimizing for proximity-based and implicit local searches
- **Local Link Building**: Earning links from local organizations, chambers of commerce, community partners, sponsorships, and local media
- **Local Schema Markup**: Implementing LocalBusiness, GeoCoordinates, OpeningHours, AggregateRating, and related structured data
- **Review Management for Local**: Generating reviews, improving ratings, responding to reviews, and leveraging reviews for local ranking signals
- **Service Area Businesses**: Optimizing for businesses without a physical storefront that serve customers at their locations
- **Local Content Strategy**: City pages, neighborhood guides, local event content, and geo-targeted blog posts
- **Google Maps Optimization**: Improving visibility and engagement within Google Maps specifically
- **Local Competitive Analysis**: Benchmarking local search performance against nearby competitors

**Trigger phrases**: "local seo," "google business profile," "gbp," "google maps," "local pack," "map pack," "near me," "local citations," "nap consistency," "location pages," "multi-location," "service area," "local link building," "local reviews," "local schema," "local business," "local rankings," "google 3-pack," "local directory," "local search," "store locator," "franchise seo," "city pages," "neighborhood seo"

## Brand Context (Auto-Applied)

Before producing any marketing output from this module:

1. **Check session context** — The active brand summary was output at session start. Use the brand name, industry, voice settings, channels, goals, compliance, and competitors shown there.
2. **If you need the full profile**, read: `~/.claude-marketing/brands/{slug}/profile.json`
3. **Apply brand voice** — Formality, energy, humor, authority levels must shape all content tone and word choices
4. **Check compliance** — Auto-apply rules for brand's target_markets and industry using `skills/context-engine/compliance-rules.md`
5. **Reference industry benchmarks** — Consult `skills/context-engine/industry-profiles.md` for the brand's industry
6. **Use platform specs** — Reference `skills/context-engine/platform-specs.md` for character limits and format requirements
7. **Check campaign history** — Run `python "${CLAUDE_PLUGIN_ROOT}/scripts/campaign-tracker.py" --brand {slug} --action list-campaigns` before planning new work
8. **If no brand exists**, say: "No brand profile found. Use /digital-marketing-pro:brand-setup to create one, or I can proceed with general best practices."
9. **Check brand guidelines** — If `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` exists, load and enforce: `restrictions.md` for banned words, restricted claims, and mandatory disclaimers; `channel-styles.md` for channel-specific tone overrides (may differ from base voice); `messaging.md` for approved key messages, taglines, and positioning language; `voice-and-tone.md` for detailed voice rules beyond the 4 numeric scores. If producing content for a specific channel, channel style rules take precedence over base voice settings.

Do not ask the user for information that already exists in their brand profile.

## Required Context

Before executing local SEO work, gather:

1. **Business Name & Address**: Exact legal business name and full street address (or multiple addresses for multi-location)
2. **Phone Number(s)**: Primary and tracking phone numbers in use
3. **Service Areas**: Geographic areas served (cities, counties, zip codes, radius)
4. **Number of Locations**: Single location, multi-location (how many), or service area business (no storefront)
5. **GBP Access**: Does the business have a claimed and verified Google Business Profile?
6. **Current Review Profile**: Average star rating, total review count, review velocity trend, and response rate
7. **Industry/Category**: Primary business category and any secondary categories currently set
8. **Local Competitors**: Top 3-5 businesses competing for the same local searches
9. **Current Rankings**: Known local pack positions for target keywords (if tracked)
10. **Website Structure**: Does the site have individual location pages? A store locator? Location-specific content?
11. **Existing Citations**: Known directory listings (Yelp, YP, BBB, industry-specific) and their accuracy
12. **Budget & Resources**: Team capacity for review management, content creation, and ongoing citation maintenance

For quick requests (e.g., "optimize my Google Business Profile"), proceed with available information. For comprehensive local SEO strategy, gather the full context.

## Capabilities

### Google Business Profile Optimization
- Profile completeness audit and optimization (every field, every section)
- Primary and secondary category selection strategy
- Business attribute configuration for ranking signals and user engagement
- Photo strategy (exterior, interior, team, product, at-work — quantity and quality benchmarks)
- Google Posts publishing strategy (What's New, Events, Offers — cadence and CTA optimization)
- Q&A section seeding and management
- Products and Services section optimization
- Business description keyword optimization within character limits
- Hours, special hours, and holiday hours management
- Booking and appointment URL integration
- Messaging and chat setup
- GBP suspension prevention and recovery procedures
- GBP Insights analysis and action planning

### Local Citation Building & NAP Management
- Structured citation audit across 50+ directories
- Unstructured citation identification (mentions in articles, press, blogs)
- NAP consistency scoring and discrepancy resolution
- Data aggregator submissions (Data Axle, Neustar Localeze, Foursquare)
- Industry-specific citation source identification and prioritization
- Duplicate listing detection and cleanup
- Citation velocity planning for steady listing growth

### Local Search Strategy
- Local keyword research (geo-modified terms, service+location combinations, implicit local queries)
- Local pack ranking factor analysis (proximity, prominence, relevance)
- Local competitive gap analysis (citations, reviews, content, links)
- Local SERP feature targeting (local pack, knowledge panel, local finder, Google Maps)
- "Near me" and voice search optimization for local intent

### Location Page & Local Content
- Location page template design with unique, substantive content per location
- Service area page strategy for SABs
- City and neighborhood landing pages (when appropriate, avoiding thin content)
- Local blog content planning (community events, local news, neighborhood guides)
- Localized testimonials and case studies
- Local FAQ content by industry

### Local Link Building
- Local partnership and sponsorship link opportunities
- Chamber of commerce and business association memberships
- Local media and press link earning
- Community event sponsorship and participation
- Local scholarship and charity link programs
- Geo-relevant industry directory submissions

### Local Schema Markup
- LocalBusiness schema (and subtypes: Restaurant, Dentist, Attorney, etc.)
- GeoCoordinates, PostalAddress, OpeningHoursSpecification
- AggregateRating and individual Review schema
- Service, hasOfferCatalog, and areaServed markup
- Multi-location Organization-to-LocalBusiness relationship schema
- FAQ and HowTo schema for local content

### Multi-Location Management
- Organizational GBP account structure and location groups
- Scalable location page architecture
- Store locator SEO (indexable, schema-enhanced, user-friendly)
- Centralized vs decentralized management frameworks
- Brand consistency enforcement across locations
- Multi-location reporting and benchmarking

## Process

### Primary Workflow: Local SEO Audit & Strategy

1. **Google Business Profile Audit**
   - Verify claim and verification status
   - Assess profile completeness: name accuracy, address, phone, website, hours, categories, attributes, description, photos, posts, Q&A, products, services
   - Evaluate category selection (primary and secondary) against competitors
   - Review photo quantity, quality, and recency (benchmark: 100+ photos, updated quarterly)
   - Assess Google Posts activity and engagement
   - Check for policy violations or suspension risks

2. **NAP Consistency Audit**
   - Document the canonical NAP (the exact name, address, and phone that should appear everywhere)
   - Scan top 50 citation sources for existing listings
   - Score each listing for NAP accuracy (exact match, minor variation, major discrepancy)
   - Identify the source of discrepancies (old address, former business name, incorrect phone format)

3. **Citation Audit & Strategy**
   - Count total structured citations (directory listings)
   - Compare citation volume against top 3 local competitors
   - Identify missing citations on high-authority directories
   - Check data aggregator accuracy (Data Axle, Neustar Localeze, Foursquare)
   - Prioritize citation building by domain authority and industry relevance

4. **Local Keyword Research**
   - Map geo-modified keywords: [service] + [city], [service] + [neighborhood], [service] near me
   - Identify implicit local keywords (keywords Google treats as local without a geo modifier)
   - Analyze local search volume and competition for priority terms
   - Map keywords to pages (location pages, service pages, blog content)

5. **Location Page Assessment**
   - Audit existing location pages for content depth, uniqueness, and optimization
   - If no location pages exist, design the page template and content plan
   - Ensure each page has unique content (not just city name swapped into a template)
   - Verify local schema markup implementation on each location page

6. **Local Link Profile Analysis**
   - Identify existing links from local sources (directories, media, organizations, partners)
   - Compare local link profile against top competitors
   - Build a local link opportunity list (chambers, associations, sponsors, events, media)
   - Prioritize by authority, relevance, and acquisition difficulty

7. **Review Profile Analysis**
   - Current average rating and total volume by platform (Google, Yelp, industry-specific)
   - Review velocity trend (increasing, stable, or declining)
   - Response rate and response quality assessment
   - Sentiment analysis of recent reviews (common praise, recurring complaints)
   - Competitor review benchmarking (their rating, volume, velocity)

8. **Local Schema Review**
   - Test existing schema with Google's Rich Results Test and Schema Validator
   - Identify missing schema types (LocalBusiness, GeoCoordinates, OpeningHours, AggregateRating)
   - Recommend schema additions with implementation-ready JSON-LD

9. **Competitor Local SEO Benchmarking**
   - Identify the top 3 local pack competitors for primary keywords
   - Compare across all ranking factors: GBP completeness, reviews, citations, content, links, proximity
   - Identify the specific gaps where the business can gain competitive advantage

10. **Prioritized Local SEO Action Plan**
    - Rank all findings by impact and effort (quick wins first)
    - Create a 30/60/90-day local SEO roadmap
    - Assign specific actions with responsible parties and deadlines
    - Define KPIs: local pack position, GBP impressions, GBP actions (calls, directions, website clicks), review volume, citation accuracy score

## Reference Files

- `gbp-optimization.md` — Complete Google Business Profile optimization guide: profile completeness checklist, category strategy, photo optimization, Google Posts, Q&A management, suspension prevention, and GBP analytics
- `citation-management.md` — Citation building framework: top sources by industry, NAP consistency requirements, data aggregator strategy, audit methodology, cleanup procedures, and multi-location citation management
- `local-content.md` — Local content strategy: geo-modified keyword research, location page best practices, city and neighborhood pages, local blog content, "near me" optimization, voice search, and local content scaling
- `multi-location.md` — Multi-location local SEO: GBP management at scale, location page architecture, store locator SEO, franchise challenges, multi-location review management, reporting, and location opening/closing procedures

## Output Formats

| Deliverable | Format | Description |
|---|---|---|
| Local SEO Audit Report | Document | Comprehensive assessment of GBP, citations, NAP, reviews, content, links, and schema with scores and priorities |
| GBP Optimization Checklist | Checklist | Field-by-field GBP optimization guide with current state and recommended actions |
| Citation Report | Spreadsheet | Directory-by-directory listing status, NAP accuracy, and submission priority |
| Location Page Template | Document | Content structure, SEO requirements, schema markup, and unique content guidelines per location |
| Local Content Calendar | Spreadsheet/Calendar | Monthly local content plan with topics, keywords, formats, and publishing schedule |
| Review Response Templates | Document | Industry-appropriate response templates for positive, neutral, negative, and fake reviews |
| Local Link Building Plan | Spreadsheet | Opportunity list with source, authority, contact, and outreach approach |
| Local Schema Package | Code snippets | Implementation-ready JSON-LD for LocalBusiness, GeoCoordinates, OpeningHours, and AggregateRating |
| Local SEO Roadmap | Document | 30/60/90-day action plan with priorities, owners, deadlines, and KPIs |

## Edge Cases

### Service Area Businesses (No Physical Storefront)
SABs (plumbers, electricians, mobile services, home cleaners) cannot display a street address on GBP. Set the service area using city names or zip codes. Hide the address in GBP settings. Do not use a P.O. Box or virtual office — Google will suspend the listing. Location pages become service area pages targeting each city served. Citation building uses the hidden address consistently but relies on phone and website URL as primary identifiers. Focus content strategy on city-specific service pages rather than a single location page.

### Multi-Location Chains (50+ Locations)
At scale, manual management fails. Recommend bulk GBP management via API or third-party platforms (Yext, Rio SEO, Uberall). Implement templatized but locally unique location pages with automated data feeds for hours, staff, and offers. Centralize review response with approved templates while allowing location managers to personalize. Build reporting dashboards that benchmark locations against each other and flag underperformers. Prioritize high-revenue or underperforming locations for dedicated attention rather than spreading effort equally.

### Highly Competitive Local Markets (Restaurants, Dentists, Plumbers)
In saturated local markets, the standard playbook is table stakes — everyone has citations and reviews. Differentiation comes from: (1) review velocity and response quality that outpaces competitors, (2) GBP engagement signals from regular posts, photos, and Q&A activity, (3) local content depth that competitors do not invest in, (4) local link building from community involvement that cannot be easily replicated, and (5) hyper-local targeting at the neighborhood level rather than just the city level.

### Businesses Spanning Multiple Cities or States
When a business serves a wide geographic area, avoid creating thin doorway pages for every city. Instead, build substantial content for primary markets (with unique testimonials, case studies, team members, and service details per location) and use service area targeting in GBP for secondary markets. Prioritize the cities with the highest revenue potential. For multi-state businesses, account for different regulatory requirements by state and adjust compliance messaging accordingly.

### New Business with Zero Local Presence
Starting from scratch requires a phased approach: (1) Claim and fully optimize GBP on day one — this is the single highest-impact action. (2) Submit to the four major data aggregators within the first week. (3) Build 20-30 high-authority citations in month one (general + industry-specific). (4) Launch a review generation program immediately — the first 10-20 reviews are the hardest but most impactful. (5) Publish a fully optimized location page with local schema. (6) Begin local content and link building in month two once the foundation is set. Set expectations: meaningful local pack visibility typically takes 3-6 months for a new business in a moderately competitive market.

## Tips & caveats

- **Google Business Profile is the single highest-leverage asset** in local SEO — practitioners commonly treat it as the majority of local-pack impact (the "60-80%" figure is an illustrative rule of thumb, not a measured statistic). Get it 100% before optimising anything else.
- **NAP (Name/Address/Phone) consistency matters across HUNDREDS of citation sources** — not just the top 10. Use a citation-management tool quarterly to catch drift.
- **Don't fake reviews.** Google's review-spam systems are increasingly aggressive (an April 2026 update reportedly tightened the bar further — verify current enforcement status before advising a client). One detected fake-review pattern can suppress GBP visibility for months.
- **Service-area businesses** (no storefront) need different proximity strategy than brick-and-mortar — location pages per service area, not per store.
- **For multi-location brands,** treat each location as its own GBP entity — don't try to consolidate. Cross-link between location pages for internal-link signal.
- **AI Overviews are increasingly local** — for "near me" queries, AI Mode + AI Overviews now both surface local results. Run `/digital-marketing-pro:aeo-audit` against location-specific queries quarterly.

## Related Skills

- **Content Engine** — For creating locally-optimized blog content, location page copy, and local content calendars
- **Reputation Management** — For comprehensive review strategy, crisis response, and sentiment monitoring beyond local-specific review tactics
- **Paid Advertising** — For Google Ads location extensions, local campaigns, and local service ads that complement organic local SEO
- **Digital PR & Authority** — For earning local media coverage and building local authority through press and community engagement
- **Analytics & Insights** — For tracking local SEO performance metrics, GBP insights analysis, and local ranking monitoring
