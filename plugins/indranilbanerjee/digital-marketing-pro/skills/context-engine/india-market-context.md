# India Market Context

The plugin supports brands operating globally, but India is a large enough market with distinct enough dynamics that a dedicated context reference is warranted. Skills serving brands operating in India should consult this document.

This is a regional context module. Equivalent modules can be added for other markets (US, EU, SEA, LATAM, MENA) as engagements demand. India is documented first because the methodology was developed primarily in the Indian market context.

## Regulatory Environment

### Digital Personal Data Protection Act (DPDP Act)

India's primary data protection law, enacted 2023, with implementation rules rolling out through 2025–2026.

Key implications for marketing:

- **Consent must be specific, informed, and free.** Pre-ticked boxes, bundled consents, and ambiguous purpose statements are not compliant.
- **Withdrawal of consent must be as easy as giving it.** Unsubscribe must be one-click; consent withdrawal flows must be visible.
- **Data Principal rights:** access, correction, erasure, grievance redressal. Brands must provide mechanisms.
- **Data fiduciary obligations:** notify Data Principals within 72 hours of breach.
- **Cross-border transfer:** restrictions on transfers to certain jurisdictions; check current MeitY notifications.
- **Children's data:** verifiable parental consent required for under-18 users; behavioural monitoring of children prohibited.

The plugin's `compliance-rules.md` includes DPDP Act details. Compliance gates in PreToolUse hooks check DPDP applicability when the engagement targets India.

### Industry-specific Indian regulations

- **Pharma:** DCGI rules, Schedule H drug advertising restrictions, Magic Remedies Act (1954) for therapeutic claims
- **Financial services:** SEBI investment advisor regulations, RBI rules on NBFC lending advertising, IRDAI for insurance
- **Real estate:** RERA registration requirements for project advertising, RERA-mandated disclosures
- **Education:** UGC + AICTE rules for higher education advertising, NEP 2020 implications
- **Food:** FSSAI rules for nutritional claims, prohibition on misleading health claims
- **Alcohol:** state-by-state surrogate advertising rules (most direct alcohol advertising prohibited)
- **Tobacco:** complete advertising ban (Cigarettes and Other Tobacco Products Act, 2003)
- **Online gaming:** state-specific regulations, IT Rules 2021 amendments for online gaming intermediaries

### Consumer Protection Act (2019) and CCPA Rules

- Misleading advertisements attract penalties (manufacturer + endorser liability)
- Influencer disclosures required (ASCI Influencer Guidelines, 2021, updated periodically)
- Dark patterns prohibited per CCPA Dark Patterns Guidelines 2023

## Market Behaviour Patterns

### Mobile-first reality

- **75–80% of web traffic in India is mobile.** Desktop optimisation matters less than for Western markets.
- Mid-range Android dominates. Test on a typical Xiaomi or Samsung A-series phone on a 4G connection — that is the user reality for most users.
- 5G adoption is uneven; do not assume 5G performance.
- Data costs have dropped dramatically (cheapest data in the world by some measures), but users still notice heavy pages — 3G-equivalent connections remain common in tier-2 and tier-3 cities.

### Tier-1 / Tier-2 / Tier-3 city differences

- **Tier-1 (8 metros):** higher purchasing power, greater English fluency, behave most similarly to Western markets, higher digital sophistication
- **Tier-2 (mid-size cities):** rapid digital adoption, growing purchasing power, vernacular content increasingly preferred, mobile-first, social commerce growth
- **Tier-3 / rural:** lower purchasing power, vernacular-first (often vernacular-only), strong WhatsApp/YouTube penetration, video and audio over text, high family/community influence on purchase decisions

Channel and creative strategy must differentiate by tier. A campaign that works in Mumbai may flop in Lucknow if not adapted.

### Language considerations

- **English is a marketing language but not a primary language for most.** Hindi, Tamil, Telugu, Marathi, Kannada, Malayalam, Bengali, Gujarati, Punjabi, Odia, Assamese — each has substantial speaker bases.
- **Hinglish** (Hindi + English code-mix) is widely used, especially in urban tier-1 / tier-2.
- **Vernacular video and audio convert significantly better in tier-2 / tier-3** than English equivalents.
- **Indic script support** in ad platforms varies — test rendering before scaling.
- Translation services for India: **Sarvam AI** (best for Indic languages), **Google Cloud Translation**, **Lara Translate**, **DeepL** (limited Indic support).
- The plugin includes a multilingual layer; see [multilingual-execution-guide.md](multilingual-execution-guide.md).

### Seasonality patterns

| Period | Pattern | Marketing implication |
|---|---|---|
| **Dussehra → Diwali (Sept–Nov)** | Festive spending peak | Ad costs +30–50%; categories like jewelry, electronics, apparel, automobile, home goods peak; budget-front-load if relevant |
| **Wedding season (Nov–Feb, regional variations)** | Wedding-related spending peak | Critical for jewelry, fashion, catering, venues, photographers |
| **End of financial year (Jan–Mar)** | B2B budget spend-down | Strong B2B outreach window; enterprise procurement closes deals |
| **Back-to-school (Apr–Jun)** | EdTech, stationery, uniforms | Critical for education-related categories |
| **Monsoon (Jun–Sep, regional)** | Outdoor activities decline; indoor / online behaviour increases | Streaming, gaming, online learning peaks; outdoor categories dip |
| **Cricket season (especially IPL Mar–May)** | Massive attention concentration on cricket | Sports-adjacent categories peak; non-cricket entertainment dips during major matches |

### Payment and commerce infrastructure

- **UPI** (Unified Payments Interface) is the dominant digital payment rail. Conversion-friendly checkout requires UPI as a primary option.
- **Cash on Delivery (COD)** still substantial in tier-2 / tier-3 e-commerce. Refusing COD often costs 30%+ of orders.
- **Buy Now Pay Later** (Simpl, Lazypay, ZestMoney) influences AOV decisions for D2C.
- **EMI as a marketing message** is potent for high-AOV categories.

### Communication and channel preferences

- **WhatsApp = primary communication channel.** 500M+ users. Brands must support WhatsApp for customer service, transactional messages, and (with explicit opt-in) marketing.
- **YouTube** dominates long-form video; very high penetration including tier-2 / tier-3 / rural.
- **Instagram** is the dominant lifestyle / D2C / influencer platform.
- **LinkedIn** is the dominant B2B platform with strong India growth.
- **ShareChat, Moj** are the dominant vernacular short-video apps (post the TikTok ban in 2020).
- **Facebook** retains reach especially in tier-2 / tier-3 and older demographics.
- **X (Twitter)** is influential among media, journalists, professionals — small audience but high-influence.
- **Telegram** is meaningful for communities, especially tech / crypto / education.
- **Quora** has substantial India usage, especially for considered B2B and education research.

### Local platforms to consider

- **Marketplaces:** Amazon India, Flipkart, Myntra (fashion), Nykaa (beauty), Meesho (social commerce), JioMart, BigBasket / Zepto / Blinkit / Instamart (quick commerce), IndiaMART (B2B)
- **Job platforms (relevant for B2B / employer brand):** Naukri, LinkedIn India
- **Real estate platforms:** Magicbricks, 99acres, Housing.com, NoBroker
- **Travel:** MakeMyTrip, Goibibo, Yatra, Booking.com (international)
- **Food delivery:** Zomato, Swiggy
- **WhatsApp Business platforms:** Wati, Interakt, Yellow.ai, Gupshup, AiSensy

### Content and media consumption

- **OTT:** JioCinema, Netflix, Prime Video, Disney+ Hotstar, Sony LIV, Zee5. JioCinema's free IPL streaming changed the OTT competitive landscape in 2023+.
- **News:** vernacular news apps (Dainik Bhaskar, Dailyhunt) have larger audiences than English news for most regions.
- **Podcasts:** Spotify, JioSaavn, Gaana, Audible. Podcast adoption growing but smaller than US.
- **Search:** Google dominates (>95%); Bing has minimal share.

### Commerce and retail dynamics

- **D2C boom (2020–2024)** has consolidated. Channel mix has shifted from pure-DTC-website to omnichannel (DTC + Amazon + quick-commerce + retail).
- **Quick-commerce** has rewritten convenience expectations — 10-minute delivery is normal in tier-1.
- **Tier-2 / Tier-3 e-commerce growth** is the primary engine of category expansion. Brands without tier-2/3 presence are leaving large addressable market on the table.

## Pricing benchmark hints (rough, vary widely)

These are directional. Always validate with current data.

- **Google Search CPC (B2B):** INR 50–500 depending on category competitiveness
- **Google Search CPC (B2C):** INR 5–50 for high-volume categories; INR 50+ for premium/competitive
- **LinkedIn Ads CPC:** INR 80–500
- **LinkedIn CPL (B2B):** INR 1,500–5,000
- **Meta Ads CPM:** INR 80–250 for general; INR 200–500 for narrow targeting
- **Meta CPL (B2C):** INR 50–500 depending on offer and category
- **WhatsApp Business Platform (per-message pricing since 1 July 2025):** India marketing template ≈ USD 0.0118 per message (~INR 1.0 at current FX); utility templates lower; authentication templates lower still. Conversation-based pricing is deprecated. Click-to-WhatsApp ads and Facebook Page CTAs open a 72-hour free service window. Service messages inside the 24-hour customer-care window are free.
- **WhatsApp Business voice calling (May 2026 launch):** WhatsApp Business now supports brand-to-customer voice calls in/out of WhatsApp. Use cases: high-AOV consult (real estate, automotive, financial services), post-purchase support, B2B account management. Pricing model still settling in May 2026 — check Meta's WhatsApp Business pricing page for the current tier. Practical guidance: pilot with a single use case (e.g. "post-purchase escalation" or "qualified-lead callback") rather than treating it as a broadcast channel; voice calls preserve the WhatsApp customer-care window for the next 24 hours after the call ends.
- **Influencer rates (per post):** Nano (INR 2K–10K), Micro (INR 10K–80K), Macro (INR 1L–10L), Mega (INR 10L+)
- **Email service costs:** Mailchimp / Brevo / Klaviyo / Customer.io scale with list size; INR 1,500–50,000+/month for typical SMB

These are 2025–2026 benchmarks. Refresh annually.

## Cultural context for messaging

- **Family / community decision-making:** for many high-AOV categories (real estate, education, jewelry, automotive), the buyer is also influenced by family and community. Messaging that targets "the head of the household" alone misses the broader influence set.
- **Festival framing** is broadly resonant but must be tonally calibrated (Hindu festivals, Eid, Christmas, regional festivals — each requires authentic engagement, not generic "festive" framing).
- **Respect for elders / authority** affects tone — overly casual brand voices can backfire in some segments.
- **Aspirational tone** works powerfully — India remains an aspirationally upward-mobile market. "Achievement" narratives resonate strongly.
- **Value sensitivity is high** even in premium segments — Indian consumers research extensively for value, even when willing to pay premium. Discounts and EMI options matter.
- **Skepticism of advertising claims** is high. Proof points (testimonials, certifications, specific quantified outcomes) outperform vague benefit claims.

## Common pitfalls when extending Western strategy to India

1. **Translating English copy without transcreating** — direct translation rarely converts. Transcreation (cultural adaptation, idiom substitution, register adjustment) is essential.
2. **Assuming desktop user research applies** — mobile is the user reality.
3. **Underestimating WhatsApp** — it is not "another messaging app." For many segments it is the primary digital channel.
4. **Over-targeting tier-1** — the volume opportunity is often tier-2 / tier-3 if the brand can speak vernacular.
5. **Treating India as homogeneous** — Mumbai, Bangalore, Delhi, Lucknow, Coimbatore are all "India" but behave very differently.
6. **Ignoring local platforms** — Meesho, ShareChat, Moj, JioCinema have audiences not reachable through Meta / Google alone.
7. **Mispricing for India without testing** — Western pricing applied to India often underperforms; pricing localisation is a strategic decision, not a translation task.

## Where India context applies in the engagement

- **Core Doc 3.1 (Business & SBU):** geography section flags India operations; unit economics use INR
- **Core Doc 3.2 (Segmentation):** persona geography includes city tier; multilingual personas if relevant
- **Core Doc 3.3 (Brand Positioning):** tone-of-voice and sensitive-topic handling reference Indian cultural context
- **Core Doc 3.4 (DMFlow):** channel selection includes Indian platforms (WhatsApp, Meesho, JioCinema where relevant)
- **Part 9 channels:** Indian platform-specific docs (e.g., 9.10 Marketplace covers Amazon India + Flipkart + Meesho)
- **Compliance gates:** DPDP Act + industry-specific Indian regulations apply

## Related references

- [compliance-rules.md](compliance-rules.md) — DPDP Act details and other Indian regulations
- [multilingual-execution-guide.md](multilingual-execution-guide.md) — Indic language support
- [transcreation-framework.md](transcreation-framework.md) — cultural recreation for emotional content
- [platform-specs.md](platform-specs.md) — Indian platform specifications
