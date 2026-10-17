# Channel Families — Part 9 Operational Grouping

Part 9 of the engagement methodology produces up to 17 channel documents. These channels group naturally into seven families based on how they are produced, managed, and measured.

This grouping is operational, not strategic. The strategic taxonomy lives in [five-digital-markets.md](five-digital-markets.md). The Channel Families groupings tell teams *how to organise the work* of Part 9.

## The 7 Families and 17 Channels

### Family 1: Search & Campaign (2 channels)

The upstream layer that informs other channels.

| 9.1 | SEO + AEO | Organic search optimisation across Google, Bing, plus AEO (visibility in ChatGPT, Perplexity, Gemini, Claude, Copilot) |
| 9.2 | Campaign Strategy | The cross-channel campaign architecture — themes, calendar, naming conventions, the master campaign list |

These two feed everything else. Keyword work from 9.1 informs ad copy and content; the campaign architecture from 9.2 sets the campaign IDs that all paid and social channels reference.

### Family 2: Paid Platforms (5 channels)

Direct media buying with measurable spend and outcomes.

| 9.3 | Google Ads | Full stack: Search, Display, Contextual, YouTube, Performance Max |
| 9.4 | Meta Ads | Facebook + Instagram, including Reels, Stories, Advantage+ |
| 9.5 | LinkedIn Ads | Sponsored Content, Message Ads (InMail), Lead Gen Forms, Dynamic Ads, Thought Leader Ads |
| 9.6 | Other Paid | Programmatic display (DV360, The Trade Desk), TikTok Ads, Twitter Ads, Quora Ads, Reddit Ads, podcast/CTV |
| 9.7 | Custom Audience Acquisition | The strategy for building first-party audiences (lookalikes, retargeting pools, CDP audiences) that feed all paid platforms |

### Family 3: Organic & Influencer (2 channels)

Earned and content-driven distribution.

| 9.8 | Organic Social Media | Posting strategy, content pillars, community management, native format strategy per platform |
| 9.9 | Influencer Strategy | Tier strategy (nano/micro/macro/mega), discovery, briefs, contracts, FTC compliance, performance measurement |

### Family 4: Marketplace & CRM (2 channels)

Owned commerce and direct-to-customer channels.

| 9.10 | Marketplace Strategy | E-commerce (Amazon, Flipkart), quick-commerce (Blinkit, Zepto), B2B marketplaces (IndiaMART) |
| 9.11 | Email + WhatsApp Lifecycle | Email programme (welcome, nurture, abandoned cart, post-purchase, win-back), WhatsApp programme (transactional, broadcast, lifecycle), SMS strategy if applicable |

### Family 5: Content, ATL, BTL, PR (4 channels)

Brand-building and earned-media disciplines.

| 9.12 | Utility Content & Whitepapers | Long-form content strategy: thought leadership articles, whitepapers, ebooks, research reports, case studies, calculators, templates |
| 9.13 | ATL Strategy | Above-the-line advertising — TV, radio, OOH (out-of-home), print. Not always digital, but planned alongside digital |
| 9.14 | BTL Strategy | Below-the-line — events, activations, sampling, dealer engagement, channel partner marketing |
| 9.15 | PR Strategy | Earned media, press releases, journalist relations, byline articles, awards strategy, crisis communications playbook |

### Family 6: Web + Measurement (2 channels)

The infrastructure that makes everything else measurable.

| 9.16 | Website + Landing Page | Website strategy, landing page architecture, CRO methodology, A/B testing programme, page-speed strategy |
| 9.17 | GA4 Setup | Measurement architecture: events, conversions, audiences, attribution model, custom dimensions, BigQuery export, dashboards |

GA4 setup sits in Part 9 (not Part 7 Preparation) because measurement architecture is more strategy-execution mix than pure preparation. It needs the channel strategies to be defined first so the events, conversions, and audiences mirror what the channels are actually doing.

## Standard Channel Document Structure

Every Part 9 channel document follows the same four-component structure:

### Component 1: Media

The platform-specific strategy:

- Account / property setup (account IDs, properties, ownership)
- Campaign architecture (campaign types, ad group / ad set structure, naming conventions)
- Targeting strategy (audiences, exclusions, layering)
- Bidding strategy (manual / auto / portfolio)
- Budget plan (per campaign, per ad group, daily / lifetime)
- Schedule / pacing (always-on, burst, day-parting)
- Format strategy (image, video, carousel, native, etc.)

### Component 2: KPIs

The measurement plan for this channel:

- Primary KPI (the one number that matters most)
- Secondary KPIs (3–5)
- Targets per KPI (with realistic conservative / moderate / aggressive scenarios)
- Reporting cadence (daily / weekly / monthly)
- Attribution model used for this channel
- Known measurement gaps (what cannot be measured + workarounds)

### Component 3: Infrastructure

The supporting assets and systems the channel needs:

- Landing pages required (URLs, ownership, CRO test schedule)
- Forms (fields, validation, where leads land in CRM)
- Tracking tags (pixels, server-side tracking, conversion events)
- Creative formats required (specs, dimensions, variations)
- Asset library reference (where creative assets live)
- Tooling required (e.g., a comparison tool, a calculator)
- Compliance assets (disclosures, consent flows, opt-outs)

### Component 4: Communication

This component is **deferred to Part 10 (Execution Artefacts)**.

Part 9 channel documents reference what communication will be required (e.g., "this channel needs 12 ad headlines, 8 descriptions, 4 video scripts"), but the actual ad copy / post copy / headlines / CTAs are produced in Part 10.

This separation keeps Part 9 focused on strategy (what) and Part 10 focused on execution (the actual words).

## Channel selection logic

Not every engagement uses all 17 channels. Channel selection happens in Core Doc 3.4 (DMFlow) during Part 3, and is validated in Part 5.

Channels not selected are **deferred** — never placeholder-filled. A Part 9 directory for a B2B SaaS engagement might contain only:

```
part-09-channel-strategy/
├── 9.1-seo-aeo.md
├── 9.2-campaign-strategy.md
├── 9.3-google-ads.md
├── 9.5-linkedin-ads.md
├── 9.8-organic-social.md
├── 9.11-email-whatsapp.md
├── 9.12-utility-content.md
├── 9.16-website-landing-page.md
└── 9.17-ga4-setup.md
```

That is 9 channels in scope (out of 17 possible). The remaining 8 are not produced because they are not relevant to this engagement.

If the engagement later expands to add a channel (e.g., adding 9.4 Meta Ads after Q1 results show LinkedIn alone is not scaling), a new channel doc is added at that time.

## Production order within Part 9

Channels in Family 1 (Search & Campaign) and Family 6 (Web + Measurement) should be produced first because they inform the others.

Recommended order:

1. 9.16 Website + Landing Page (defines the destination)
2. 9.17 GA4 Setup (defines what gets measured)
3. 9.2 Campaign Strategy (defines campaign IDs all channels reference)
4. 9.1 SEO + AEO (informs keyword and content strategy)
5. 9.7 Custom Audience Acquisition (informs paid channels' audience strategy)
6. Then the rest of Family 2 (Paid platforms) — can run in parallel
7. Then Family 3 (Organic & Influencer)
8. Then Family 4 (Marketplace & CRM)
9. Then Family 5 (Content, ATL, BTL, PR) — can run in parallel with the above

When using parallel agents (Anthropic Agent Teams or similar orchestration), Family 2, Family 3, Family 4, Family 5 can all spawn parallel teammates after the foundational docs (9.16, 9.17, 9.2, 9.1, 9.7) are complete.

## Related references

- [five-digital-markets.md](five-digital-markets.md) — strategic taxonomy
- [engagement-flow-methodology.md](engagement-flow-methodology.md) — Part 9 in context
- [four-core-documents-spec.md](four-core-documents-spec.md) — Core Doc 3.4 DMFlow that selects channels
