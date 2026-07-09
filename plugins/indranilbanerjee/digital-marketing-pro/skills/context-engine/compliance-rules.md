# Compliance Rules Reference

This file is the canonical compliance ruleset for the Digital Marketing Pro plugin. All marketing modules MUST check outputs against these rules before delivery. Rules are structured for programmatic consumption by the context engine.

---

## Section 1: Geographic Privacy Laws

### 1.1 EU/EEA — General Data Protection Regulation (GDPR)

| Field | Detail |
|---|---|
| **Region** | European Union / European Economic Area (27 EU member states + Iceland, Liechtenstein, Norway) |
| **Law** | General Data Protection Regulation (GDPR) |
| **Year Enacted** | 2016 (enforced May 25, 2018) |
| **Consent Model** | Opt-in. Explicit, informed, freely given, specific, and unambiguous consent required before processing personal data. Consent must be as easy to withdraw as to give. Legitimate interest may apply in narrow B2B contexts but requires a documented balancing test. |
| **Email Rules** | Prior opt-in required for all marketing emails. Soft opt-in exception: existing customers may be emailed about similar products/services if given an easy opt-out at collection and in every message. Every email must include sender identity, physical address, and a functional unsubscribe mechanism honored within 30 days. |
| **Cookie/Tracking Rules** | Prior consent required for all non-essential cookies and trackers (ePrivacy Directive). Cookie banners must allow granular choice (accept/reject by category). Pre-ticked boxes are invalid. Analytics cookies require consent unless strictly necessary. Server-side tracking of personal data still requires a lawful basis. |
| **Penalty Range** | Up to EUR 20 million or 4% of global annual turnover, whichever is higher. Supervisory authorities may also issue warnings, bans on processing, and orders to erase data. |
| **Key Marketing Impact** | Double opt-in is industry standard. All lead forms need clear consent checkboxes (not bundled). Data Processing Agreements required with every martech vendor. Privacy policy must disclose all data recipients. Cross-border data transfers require adequacy decisions, SCCs, or BCRs. Right to erasure means suppression lists must be maintained. Profiling for ad targeting requires explicit consent or legitimate interest with opt-out. |

### 1.1b EU/EEA — AI Act Article 50 (Generative AI Disclosure)

| Field | Detail |
|---|---|
| **Region** | European Union / European Economic Area |
| **Law** | Regulation (EU) 2024/1689 — Artificial Intelligence Act, Article 50 (Transparency obligations for providers and deployers of certain AI systems) |
| **Applicable** | **2 August 2026** (transparency obligations); general-purpose AI obligations applied 2 Aug 2025; high-risk system obligations 2 Aug 2027 |
| **Scope** | All generative-AI outputs distributed in EU markets — no minimum spend threshold, advertising not exempted. Both providers (AI developers) and deployers (advertisers, brands) bear obligations. |
| **Disclosure Requirements** | (a) AI-generated or AI-manipulated content **must be marked in a machine-readable format** using open, interoperable standards. **C2PA (Coalition for Content Provenance and Authenticity) is the emerging backbone.** Marking must be technically robust and survive routine processing. (b) Deepfakes (synthetic audio/image/video resembling real persons, objects, places, or events) must be **visibly disclosed**. (c) AI-generated text on matters of public interest must be disclosed unless human-reviewed and the brand assumes editorial responsibility. |
| **Carve-outs** | Genuine artistic, satirical, or fictional works are narrowly exempt — applies in limited cases and does not blanket-exempt marketing. |
| **Penalty Range** | Up to **EUR 15 million or 3% of global annual turnover**, whichever is higher (transparency obligations). High-risk system breaches up to EUR 35M or 7%. |
| **Key Marketing Impact** | Any AI-generated ad creative, social image, AI-narrated video, or AI-written long-form copy distributed in the EU must carry machine-readable provenance metadata. Use `/digital-marketing-pro:c2pa-metadata` to embed a C2PA manifest in any AI-generated image / video / audio / PDF before EU publication. Deepfakes need an additional visible disclosure overlay or audio cue. AI-written editorial pieces need an "AI-assisted" byline unless the human editor assumes full editorial accountability. The pre-publish gate (`/digital-marketing-pro:check`) verifies C2PA presence on AI-flagged assets in EU-targeted campaigns. |

#### 1.1b.i — Article 50 draft implementing guidelines (May 2026)

The European Commission published **draft implementing guidelines for Article 50 on 8 May 2026**. The draft is open for public consultation until **3 June 2026**; final guidelines are expected July 2026, ahead of the 2 August 2026 enforcement date. The draft clarifies the following points that brands should treat as the working interpretation today:

| Topic | Draft guidance (May 2026) | What this means for marketing |
|---|---|---|
| **"Substantial AI manipulation"** | Defined as any AI-driven change that alters meaning, identity, or factual claims of a real person, object, place, or event. Routine colour correction, framing, denoising are NOT in scope. | A subject-replacement image swap = substantial manipulation (disclosure). A Lightroom-style retouch = not. |
| **"Matters of public interest"** | Includes health, elections, finance, government services, public safety, and any topic where a reasonable consumer expects journalistic accuracy. Marketing copy itself is generally not in scope UNLESS it crosses into one of those topics (e.g., health claims, financial product claims). | Generic product copy = no AI disclosure required. AI-generated copy making health, financial, or political claims = disclosure required unless a human editor signs off. |
| **Machine-readable marking** | C2PA Content Credentials are explicitly named as a "presumption of compliance" pathway. Alternative open-standard markings allowed if technically equivalent. | Continue using C2PA via `/digital-marketing-pro:c2pa-metadata`. Brands that ship without C2PA must show equivalent provenance — substantially more work. |
| **Deepfake visible disclosure** | Visible label, watermark, or audio cue must be perceivable at normal viewing/listening distance. Hidden corner overlays in a tiny font are explicitly insufficient. | If you produce a synthetic-talent ad or AI-cloned voice ad for the EU market, the disclosure must be visible from any normal viewing distance. |
| **Editorial-responsibility carve-out** | Human reviewer must (a) be identifiable, (b) have authority to alter or reject the AI output, (c) have a documented review record. A pure rubber-stamp does not satisfy the carve-out. | ContentForge's Phase 7 reviewer scorecard satisfies (c) but a named human editor must still sign off and that name must be on the published piece (byline, masthead, or accessible "About this article" link). |
| **Enforcement priority** | National regulators are expected to prioritise (1) deepfakes, (2) AI-generated political/health content, (3) AI-generated content marketed without any provenance metadata at all. Routine commercial creative with C2PA is low priority. | Brands using C2PA across EU-distributed AI assets are in a strong defensive posture even before final guidelines land. |

**Action items for brands with EU exposure before 2 August 2026:**

1. **Audit your EU AI-asset inventory now.** Catalogue any AI-generated image, video, audio, deepfake-style synthetic content, and AI-written long-form copy distributed to EU users in the last 12 months. Identify which carry C2PA and which don't.
2. **File a consultation comment by 3 June 2026 if Article 50 will materially affect your operations.** The Commission has explicitly asked for industry input on the "substantial manipulation" boundary and the carve-out scope. Brands in regulated sectors (health, finance, automotive, political adjacencies) should weigh in.
3. **Lock in your C2PA signing-cert procurement.** See `docs/c2pa-production-cert-guide.md` for the four recognised authorities. Allow 2–4 weeks for Adobe Content Credentials approval — start no later than 1 July 2026.
4. **Update your Definition of Done.** Any creative produced after 1 July 2026 for EU distribution should be C2PA-signed at production time, not retrofitted at publish time. The pre-publish gate (`/digital-marketing-pro:check`) blocks unsigned AI assets for EU-targeted campaigns.
5. **Treat the carve-out as conditional, not a free pass.** "Human-reviewed" requires named accountability. Don't claim editorial responsibility unless a named editor is willing to be on the record.

### 1.2 United States Federal — CAN-SPAM Act

| Field | Detail |
|---|---|
| **Region** | United States (federal) |
| **Law** | Controlling the Assault of Non-Solicited Pornography and Marketing Act (CAN-SPAM) |
| **Year Enacted** | 2003 (effective January 1, 2004; amended 2008) |
| **Consent Model** | Opt-out. No prior consent required to send commercial email. Recipients must be given a clear way to opt out, and opt-out requests must be honored within 10 business days. |
| **Email Rules** | No deceptive subject lines. "From" and "Reply-To" must accurately identify the sender. Every commercial email must include: a clear identification as an advertisement (if applicable), the sender's valid physical postal address, and a conspicuous opt-out mechanism. Purchased lists are legal but opt-out obligations still apply. Transactional emails are exempt if their primary purpose is transactional. |
| **Cookie/Tracking Rules** | No federal cookie consent law. Tracking pixels in email are legal. The FTC enforces against deceptive tracking practices under Section 5 of the FTC Act. |
| **Penalty Range** | Up to $51,744 per violation (per email). ISPs and state attorneys general may also bring actions. |
| **Key Marketing Impact** | Lower bar than GDPR but strict on opt-out honoring. Affiliate and partner emails count — the brand whose product is promoted is liable. "Sender" definition includes the entity whose product is advertised. Suppression list management is critical. Header manipulation is a criminal offense. |

### 1.3 California — CCPA / CPRA

| Field | Detail |
|---|---|
| **Region** | California, United States |
| **Law** | California Consumer Privacy Act (CCPA, 2018) as amended by the California Privacy Rights Act (CPRA, 2020; fully operative January 1, 2023) |
| **Year Enacted** | CCPA: 2018. CPRA amendment: 2020 (enforced 2023). |
| **Consent Model** | Opt-out for sale/sharing of personal information. Opt-in required for consumers under 16 (under 13 requires parental consent). "Sharing" includes cross-context behavioral advertising. |
| **Email Rules** | CAN-SPAM governs email. CCPA/CPRA layer on top: consumers can opt out of the "sale" or "sharing" of personal information used for email targeting and personalization. Honoring Global Privacy Control (GPC) signals is required. |
| **Cookie/Tracking Rules** | Third-party cookies and ad pixels that share data with ad platforms constitute "sharing" under CPRA. A "Do Not Sell or Share My Personal Information" link must be on the website. GPC browser signals must be honored as a valid opt-out. |
| **Penalty Range** | $2,500 per unintentional violation; $7,500 per intentional violation. Private right of action for data breaches ($100–$750 per consumer per incident). Enforced by the California Privacy Protection Agency (CPPA). |
| **Key Marketing Impact** | Retargeting audiences using third-party data requires opt-out mechanism. Service provider agreements needed with all martech vendors. 12-month lookback on data collection disclosures. "Sensitive personal information" (e.g., geolocation, race, health) triggers additional restrictions — limit use to what is necessary. |

### 1.4 US State Privacy Laws (Multi-State Summary)

| Field | Detail |
|---|---|
| **Region** | United States — 20+ states with enacted comprehensive privacy laws |
| **Laws** | Virginia (VCDPA, 2023), Colorado (CPA, 2023), Connecticut (CTDPA, 2023), Utah (UCPA, 2023), Iowa (ICDPA, 2025), Indiana (ICDPA, 2026), Tennessee (TIPA, 2025), Montana (MCDPA, 2024), Texas (TDPSA, 2024), Oregon (OCPA, 2024), Delaware (DPDPA, 2025), New Hampshire (SB 255, 2025), New Jersey (SB 332, 2025), Nebraska (NDPA, 2025), Maryland (MODPA, 2025), Minnesota (MCDPA, 2025), Rhode Island (RIDPA, 2026), Kentucky (KCDPA, 2026), Vermont (VDPA, 2025), and others pending. |
| **Year Enacted** | Rolling: 2021–2026. Most operative between 2023–2026. |
| **Consent Model** | Generally opt-out for sale of data and targeted advertising. Opt-in for sensitive data processing. Most follow the VCDPA template. Maryland and Minnesota are more restrictive (closer to GDPR's data minimization standard). |
| **Email Rules** | Defer to CAN-SPAM federally. State laws add data rights (access, deletion, correction, portability) that affect CRM and email list management. |
| **Cookie/Tracking Rules** | Most require opt-out rights for targeted advertising (which implicates ad cookies and pixels). Universal opt-out mechanisms (like GPC) are mandated in Colorado, Connecticut, Texas, Montana, Oregon, Delaware, and others. |
| **Penalty Range** | Typically $7,500–$10,000 per violation. Most enforced by the state Attorney General. Few have private rights of action. Cure periods (30–60 days) are common in early-enacted laws but are being removed in newer laws. |
| **Key Marketing Impact** | Treat the US as a patchwork. The safest approach is to build to the most restrictive standard (currently Maryland or CPRA) and apply nationally. Universal opt-out signal support is becoming table stakes. Data mapping is essential to know which state laws apply to which consumers. |

### 1.5 Canada — CASL

| Field | Detail |
|---|---|
| **Region** | Canada |
| **Law** | Canada's Anti-Spam Legislation (CASL) |
| **Year Enacted** | 2014 |
| **Consent Model** | Opt-in. Express consent required for commercial electronic messages (CEMs). Implied consent exists in limited cases: existing business relationship (within 2 years of purchase, 6 months of inquiry), conspicuous publication of address (if relevant to role), or disclosure via referral. |
| **Email Rules** | Every CEM must include: sender identification, contact information (physical and digital), and a functional unsubscribe mechanism processed within 10 business days. Consent records must be retained with proof of how and when consent was obtained. Consent requests themselves cannot contain marketing. |
| **Cookie/Tracking Rules** | CASL requires consent for installation of programs on devices. Cookie consent is governed by PIPEDA (federal privacy law) — implied consent may suffice for functional/analytics cookies, but tracking for ad targeting should use express consent. |
| **Penalty Range** | Up to CAD $10 million per violation (individuals: $1 million). CRTC enforces. Private right of action was enacted but enforcement is through administrative monetary penalties. |
| **Key Marketing Impact** | One of the strictest email laws globally. Implied consent windows are short — CRM must track consent expiry. "Conspicuous publication" is narrow and does not cover scraping. B2B cold outreach is heavily restricted. Referral/tell-a-friend programs require careful structuring. |

### 1.6 Brazil — LGPD

| Field | Detail |
|---|---|
| **Region** | Brazil |
| **Law** | Lei Geral de Protecao de Dados (LGPD) |
| **Year Enacted** | 2018 (enforced September 2020; penalties from August 2021) |
| **Consent Model** | Opt-in. Consent must be free, informed, and unambiguous for a specific purpose. Legitimate interest is available as an alternative basis but requires a Legitimate Interest Assessment (LIA). |
| **Email Rules** | Consent or legitimate interest required. Unsubscribe must be easy and immediate. Data subjects have rights to access, correction, deletion, and portability. Marketing communications must identify the sender and purpose. |
| **Cookie/Tracking Rules** | ANPD (National Data Protection Authority) guidance requires consent for non-essential cookies. Cookie banners with accept/reject options are standard practice. |
| **Penalty Range** | Up to 2% of revenue in Brazil, capped at BRL 50 million (~USD 10 million) per violation. ANPD may also issue warnings, publicize violations, and block or delete data. |
| **Key Marketing Impact** | Similar structure to GDPR but with a revenue cap specific to Brazilian operations. Data Protection Officer (DPO) appointment is mandatory. Cross-border transfers require adequacy, contractual safeguards, or consent. Portuguese-language privacy notices required. |

### 1.7 United Kingdom — UK GDPR + PECR

| Field | Detail |
|---|---|
| **Region** | United Kingdom |
| **Law** | UK General Data Protection Regulation (UK GDPR) + Privacy and Electronic Communications Regulations (PECR) |
| **Year Enacted** | UK GDPR: 2018 (retained post-Brexit, 2021). PECR: 2003. |
| **Consent Model** | Opt-in for marketing. PECR requires prior consent for unsolicited marketing emails to individuals. Soft opt-in exception (similar to EU): existing customers can be emailed about similar products if opt-out was offered at collection and in each message. B2B exception: corporate email addresses (e.g., info@company.com) may be contacted without prior consent under PECR, but UK GDPR still requires a lawful basis. |
| **Email Rules** | Same structural requirements as GDPR: sender identity, physical address, unsubscribe. ICO enforces. Unsolicited B2C email without consent is a PECR violation. |
| **Cookie/Tracking Rules** | PECR requires prior consent for non-essential cookies. ICO has signaled stricter enforcement. Legitimate interest is not a valid basis for ad cookies under PECR. |
| **Penalty Range** | UK GDPR: up to GBP 17.5 million or 4% of global turnover. PECR: up to GBP 500,000. ICO enforcement. |
| **Key Marketing Impact** | Post-Brexit, UK adequacy decision from the EU allows data flows, but this is subject to review. Data Protection Impact Assessments required for high-risk processing (profiling, large-scale marketing). ICO publishes direct marketing guidance — treat as binding. International transfers require UK-specific transfer mechanisms (UK SCCs, IDTA). |

### 1.8 Australia — Privacy Act + Spam Act

| Field | Detail |
|---|---|
| **Region** | Australia |
| **Law** | Privacy Act 1988 (Australian Privacy Principles) + Spam Act 2003 |
| **Year Enacted** | Privacy Act: 1988 (APPs added 2014). Spam Act: 2003. |
| **Consent Model** | Opt-in under the Spam Act for commercial electronic messages. Consent can be express or inferred (from an existing business relationship or conspicuous publication). The Privacy Act uses a "reasonable expectation" standard for use of personal information. |
| **Email Rules** | Spam Act requires: consent (express or inferred), accurate sender identification, functional unsubscribe honored within 5 business days. Address harvesting and list selling are prohibited. |
| **Cookie/Tracking Rules** | No specific cookie consent law currently. The Privacy Act requires transparency about data collection. The government's Privacy Act Review (2023–2025) is expected to introduce stronger consent requirements for tracking — monitor for changes. |
| **Penalty Range** | Spam Act: up to AUD 2.22 million per day for body corporates. Privacy Act: up to AUD 50 million, 3x the benefit obtained, or 30% of adjusted turnover (whichever is greater) following 2022 amendments. ACMA and OAIC enforce. |
| **Key Marketing Impact** | Spam Act prohibits address harvesting software and purchased scraped lists. Inferred consent from business relationships is relatively broad but must be documented. The Privacy Act's 2022 penalty increase makes Australia a high-consequence jurisdiction. Cross-border disclosure to overseas recipients requires reasonable steps to ensure compliance. |

### 1.9 Singapore — PDPA

| Field | Detail |
|---|---|
| **Region** | Singapore |
| **Law** | Personal Data Protection Act (PDPA) |
| **Year Enacted** | 2012 (significant amendments 2021) |
| **Consent Model** | Opt-in for marketing. Deemed consent applies in limited situations (e.g., voluntarily providing data for a clear purpose). 2021 amendments added "legitimate interest" and "business improvement" exceptions. |
| **Email Rules** | Do Not Call (DNC) Registry: mandatory to check before sending marketing messages to Singapore numbers/addresses. Opt-out must be free and processed within 10 business days. Sender must be identified. |
| **Cookie/Tracking Rules** | No specific cookie consent law. PDPA's consent obligation applies if cookies collect personal data. PDPC advisory guidelines recommend transparency and consent for tracking. |
| **Penalty Range** | Up to SGD 1 million or 10% of annual turnover in Singapore (whichever is higher, following 2021 amendments). PDPC enforces. |
| **Key Marketing Impact** | DNC Registry check is mandatory and unique to Singapore — scrub all contact lists. Data breach notification mandatory within 3 days. Data Protection Officers must be appointed. Consent withdrawal must be easy. Cross-border transfers require comparable protection. |

### 1.10 China — PIPL

| Field | Detail |
|---|---|
| **Region** | People's Republic of China |
| **Law** | Personal Information Protection Law (PIPL) |
| **Year Enacted** | 2021 (effective November 1, 2021) |
| **Consent Model** | Opt-in. Separate consent required for: sensitive personal information, cross-border transfers, public disclosure, and processing by third parties. Consent must be informed, voluntary, and explicit. |
| **Email Rules** | Marketing requires consent. Individuals have the right to refuse and withdraw. All processing purposes must be disclosed. No specific email-format statute like CAN-SPAM, but general consent and transparency obligations apply. |
| **Cookie/Tracking Rules** | Consent required for collection of personal information via cookies and trackers. Automated decision-making (algorithmic recommendations, targeted ads) must offer an opt-out and a non-personalized alternative. |
| **Penalty Range** | Up to RMB 50 million (~USD 7 million) or 5% of prior year's revenue. Responsible individuals can be fined up to RMB 1 million and banned from serving as directors/officers. CAC (Cyberspace Administration of China) enforces. |
| **Key Marketing Impact** | Data localization: personal information of Chinese residents must be stored in China unless a security assessment, standard contract, or certification is completed for cross-border transfer. Separate consent for each purpose. Personal Information Protection Impact Assessments required for sensitive data, automated decision-making, and cross-border transfers. Local DPO or representative required if processing from outside China. |

### 1.11 India — DPDPA

| Field | Detail |
|---|---|
| **Region** | India |
| **Law** | Digital Personal Data Protection Act (DPDPA) 2023, operationalised by the Digital Personal Data Protection Rules 2025 (notified by MeitY 3 Jan 2025; phased commencement through 2025-2026). |
| **Year Enacted** | 2023 (Rules 2025 finalised; consult MeitY notification for the phase-by-phase commencement schedule before designing for India). |
| **Consent Model** | Opt-in. Consent must be free, specific, informed, unconditional, and unambiguous, and must be requested in clear, plain language. Notice must accompany or precede the consent request (Rule 3). "Deemed consent" was removed in the 2023 Act and replaced with "Certain Legitimate Uses" (Section 7) — narrower than the 2022 draft. |
| **Email Rules** | Marketing requires verifiable consent. Withdrawal must be as easy as giving consent. The Consent Manager framework (registered entities that intermediate consent on behalf of Data Principals) is now live under Rule 4 — Data Fiduciaries handling material volumes should integrate with at least one registered Consent Manager. |
| **Cookie/Tracking Rules** | Cookie / SDK-based tracking that identifies a Data Principal is processing of personal data and requires DPDPA-compliant consent. The Rules do not carve out cookies; rely on the general processing-with-consent obligation. EU-style banner UX is the safest pattern. |
| **Penalty Range** | Up to INR 250 crore (~USD 30 million) per instance of non-compliance. No percentage-of-revenue calculation. The Data Protection Board of India (constituted under Rule 16 et seq) enforces and adjudicates. |
| **Key Marketing Impact** | Children's data (under 18) requires verifiable parental consent, and the Act prohibits targeted advertising and behavioural tracking directed at children — design age-gating and parental-consent flows before launching India campaigns to under-18 audiences. Cross-border transfers are permitted by default; Government may notify restricted countries by gazette (none broadly restricted as of May 2026 — verify before launch). Significant Data Fiduciaries (designated by the Government based on volume / sensitivity / risk) carry additional obligations: appoint an India-resident Data Protection Officer, conduct annual Data Protection Impact Assessments, and undergo periodic audits. Breach notification to the Board and affected Data Principals is mandatory without delay (Rule 7). |

### 1.12 Japan — APPI

| Field | Detail |
|---|---|
| **Region** | Japan |
| **Law** | Act on the Protection of Personal Information (APPI) |
| **Year Enacted** | 2003 (major amendments 2017, 2022) |
| **Consent Model** | Opt-in for provision to third parties and for use beyond the stated purpose. Opt-out mechanism available for third-party provision if registered with the PPC (Personal Information Protection Commission). 2022 amendments tightened opt-out rules and expanded individual rights. |
| **Email Rules** | Specified Electronic Mail Act: opt-in required for commercial email. Sender ID and unsubscribe required. APPI requires specifying the purpose of use at collection. |
| **Cookie/Tracking Rules** | 2022 amendments: "individually referable information" (e.g., cookie IDs that can be linked to personal info by a recipient) requires consent when provided to third parties. Cookie walls are discouraged. |
| **Penalty Range** | Criminal penalties for certain violations (up to JPY 100 million for corporations). PPC can issue orders and recommendations. Reputational enforcement is significant in Japan. 2022 amendments increased penalties. |
| **Key Marketing Impact** | Japan has an EU adequacy decision (mutual), facilitating EU-Japan data flows. Pseudonymized data has a specific legal regime — can be used for internal analytics without consent but cannot be provided to third parties. Breach notification to PPC and affected individuals is mandatory. "Individually referable information" concept means cookie syncing and DMP practices need consent. |

### 1.13 South Korea — PIPA

| Field | Detail |
|---|---|
| **Region** | South Korea |
| **Law** | Personal Information Protection Act (PIPA) |
| **Year Enacted** | 2011 (major amendments 2023, effective 2024) |
| **Consent Model** | Opt-in. Among the strictest globally. Consent must be separate from other terms, clearly distinguishable, and specific. Separate consent required for: collection, use, third-party provision, and cross-border transfer. |
| **Email Rules** | Opt-in required. The Act on Promotion of Information and Communications Network Utilization governs electronic marketing — consent must be verifiable, and opt-out must be honored immediately. Nighttime marketing (9 PM–8 AM) is restricted. |
| **Cookie/Tracking Rules** | 2023 amendments introduced a framework for pseudonymized data and behavioral advertising. Consent required for tracking that constitutes personal information processing. Online behavioral advertising requires notice and opt-out. |
| **Penalty Range** | Up to 3% of relevant revenue or KRW 600 million. Criminal penalties possible (up to 5 years imprisonment). PIPC (Personal Information Protection Commission) enforces. |
| **Key Marketing Impact** | Very granular consent requirements — separate checkboxes for each purpose and each third-party recipient. Nighttime contact restrictions are unique and must be coded into send-time logic. Resident Registration Numbers are highly restricted. 2023 amendments expanded extraterritorial reach and data subject rights. Cross-border transfer rules tightened. |

### 1.14 Saudi Arabia — PDPL

| Field | Detail |
|---|---|
| **Region** | Kingdom of Saudi Arabia |
| **Law** | Personal Data Protection Law (PDPL) |
| **Year Enacted** | 2021 (implementing regulations 2023; grace period until September 2024) |
| **Consent Model** | Opt-in. Consent must be explicit, informed, and freely given. Legitimate interest basis available but narrow. Sensitive data (health, financial, location, biometric, religious/ethnic data) requires explicit consent. |
| **Email Rules** | Marketing requires consent. Data subjects must be informed of the purpose before collection. Right to object to direct marketing. |
| **Cookie/Tracking Rules** | General consent obligation applies to collection of personal data via cookies. Specific cookie regulations expected as implementing rules evolve. |
| **Penalty Range** | Up to SAR 5 million (~USD 1.3 million). Criminal penalties for unauthorized disclosure of sensitive data (up to 2 years imprisonment). SDAIA (Saudi Data and Artificial Intelligence Authority) and NCC enforce. |
| **Key Marketing Impact** | Data localization: personal data of Saudi residents must be stored and processed in Saudi Arabia unless transfer conditions are met (adequacy, appropriate safeguards, or consent with risk disclosure). Arabic-language privacy notices likely required. DPO appointment required for certain controllers. Data breach notification within 72 hours. |

### 1.15 UAE — Federal Decree-Law No. 45

| Field | Detail |
|---|---|
| **Region** | United Arab Emirates (federal, outside free zones) |
| **Law** | Federal Decree-Law No. 45 of 2021 on the Protection of Personal Data |
| **Year Enacted** | 2021 (implementing regulations issued 2023–2024) |
| **Consent Model** | Opt-in. Consent must be clear, specific, informed, and unambiguous. Legitimate interest basis available. Sensitive data requires explicit consent. |
| **Email Rules** | Marketing requires consent or a legitimate interest basis. Right to object to direct marketing at any time. Free zone regulations (DIFC, ADGM) have their own data protection laws that may apply instead. |
| **Cookie/Tracking Rules** | General consent obligation for personal data processing extends to cookies and tracking. Await implementing regulations for specifics. |
| **Penalty Range** | Up to AED 20 million (~USD 5.4 million). UAE Data Office enforces. DIFC Commissioner and ADGM have separate penalty regimes for free zone entities. |
| **Key Marketing Impact** | Three overlapping regimes: federal law, DIFC (own law modeled on GDPR), and ADGM (own regulations). Determine which applies based on entity registration and data subject location. Cross-border transfer requires adequacy, contractual safeguards, or consent. Arabic-language notices advisable. Free zone entities should follow zone-specific rules which may be stricter. |

### 1.16 Thailand — PDPA

| Field | Detail |
|---|---|
| **Region** | Thailand |
| **Law** | Personal Data Protection Act (PDPA) |
| **Year Enacted** | 2019 (fully enforced June 1, 2022) |
| **Consent Model** | Opt-in. Consent must be freely given, specific, informed, and unambiguous. Legitimate interest available as an alternative basis. Explicit consent required for sensitive data. Consent must be as easy to withdraw as to give. |
| **Email Rules** | Direct marketing requires consent or legitimate interest with opt-out. Right to object to marketing at any time. Sender identification required. |
| **Cookie/Tracking Rules** | Consent required for non-essential cookies. Thailand PDPA Committee guidance recommends cookie banners with granular choice. Functional and strictly necessary cookies may rely on legitimate interest. |
| **Penalty Range** | Administrative fines up to THB 5 million (~USD 140,000). Criminal penalties up to THB 1 million and/or 1 year imprisonment for certain violations. Punitive damages up to 2x actual damages in civil cases. PDPA Committee and Expert Committee enforce. |
| **Key Marketing Impact** | Structure is very similar to GDPR. DPO required for certain controllers. Data breach notification within 72 hours. Cross-border transfers require adequacy, appropriate safeguards, or consent. Thai-language privacy notices for Thai data subjects. Record of processing activities required. |

---

## Section 2: Industry-Specific Regulations

### 2.1 Healthcare — HIPAA / FDA

| Field | Detail |
|---|---|
| **Industry** | Healthcare, Health Services, Pharmaceuticals, Medical Devices |
| **Regulation** | HIPAA (Health Insurance Portability and Accountability Act, 1996); FDA regulations on drug/device advertising (21 CFR Parts 202, 801, 812) |
| **Regulatory Body** | HHS (Office for Civil Rights) for HIPAA; FDA for drug/device advertising; FTC for general health claims |
| **Prohibited Claims** | No claims of cure, treatment, prevention, or diagnosis unless FDA-approved for that indication. No off-label promotion. No misleading efficacy statistics. No patient testimonials implying guaranteed outcomes. |
| **Required Disclaimers** | Rx drug ads: fair balance of risk/benefit information, major side effects, contraindications. DTC ads: "Ask your doctor" language, brief summary or adequate provision. Medical device ads: intended use, material risks. |
| **Marketing Restrictions** | PHI (Protected Health Information) cannot be used for marketing without HIPAA-compliant authorization. Treatment communications and healthcare operations are exceptions. Business Associate Agreements required with all martech vendors touching PHI. Patient testimonials require written authorization and cannot guarantee outcomes. |
| **Auto-Applied Rules** | Flag any health outcome claims. Require "consult your healthcare provider" disclaimer. Block PHI in ad copy, landing pages, and email personalization. Require fair balance when mentioning Rx products. Flag superlatives ("best," "safest," "most effective") in health contexts. |

### 2.2 Finance — SEC / FINRA

| Field | Detail |
|---|---|
| **Industry** | Financial Services, Banking, Investment, Insurance, Cryptocurrency |
| **Regulation** | SEC Rule 206(4)-1 (Marketing Rule, 2022); FINRA Rules 2210, 2241; TILA (Truth in Lending); UDAP/UDAAP |
| **Regulatory Body** | SEC, FINRA, CFPB, OCC, State regulators |
| **Prohibited Claims** | No guarantees of investment returns. No promissory statements ("you will earn"). No cherry-picked performance without full context. No testimonials/endorsements without required disclosures (SEC Marketing Rule). No misleading use of "guaranteed" or "risk-free" for investments. |
| **Required Disclaimers** | "Past performance is not indicative of future results." APR disclosure for credit products (TILA). FDIC/SIPC membership disclosures where applicable. Material risks of investment. Fees and expenses disclosure. "Not FDIC insured, may lose value" for non-deposit products. |
| **Marketing Restrictions** | Performance advertising must show net-of-fee returns, 1/5/10-year or since-inception periods, and benchmark comparison. Hypothetical performance requires extensive disclaimers and cannot be shown in mass-market ads (SEC Marketing Rule). Crypto marketing: no implication of government backing, must disclose volatility risks. Pre-approval/review required by compliance department for all communications. |
| **Auto-Applied Rules** | Flag return claims, guarantee language, and "risk-free" terminology. Require performance disclaimer on any content mentioning returns. Flag testimonials and require SEC-compliant disclosure. Block hyperbolic claims ("best returns," "guaranteed income"). Require APR disclosure near any credit/loan rate mention. |

### 2.3 Legal — Bar Association Rules

| Field | Detail |
|---|---|
| **Industry** | Legal Services, Law Firms, Legal Tech |
| **Regulation** | ABA Model Rules of Professional Conduct (Rules 7.1–7.3); State bar advertising rules (vary by state) |
| **Regulatory Body** | State bar associations, State supreme courts |
| **Prohibited Claims** | No guarantees of case outcomes. No misleading comparisons with other lawyers. No claims of specialization unless certified by an approved organization. No implication of results in future cases based on past results. |
| **Required Disclaimers** | Many states require: "Advertising Material" label on solicitation. Past results disclaimer ("Past results do not guarantee future outcomes"). Fee basis disclosure. Office location disclosure. State-specific required language varies significantly. |
| **Marketing Restrictions** | Direct solicitation restrictions (no in-person solicitation for profit in most states). Some states require pre-filing of ads with the bar. Testimonials and endorsements must be truthful and not misleading. Dramatizations must be labeled. Use of "specialist" or "expert" restricted in most states. |
| **Auto-Applied Rules** | Flag outcome guarantees and success rate claims. Require "results may vary" / "past results do not guarantee future outcomes." Flag "specialist" / "expert" claims and require certification disclosure. Flag direct solicitation language. Require jurisdiction identification. |

### 2.4 Alcohol — TTB

| Field | Detail |
|---|---|
| **Industry** | Alcoholic Beverages (beer, wine, spirits) |
| **Regulation** | Federal Alcohol Administration Act; TTB regulations (27 CFR Parts 4, 5, 7); State ABC laws |
| **Regulatory Body** | TTB (Alcohol and Tobacco Tax and Trade Bureau); State Alcohol Beverage Control boards |
| **Prohibited Claims** | No health claims ("good for you," "heart-healthy"). No claims of intoxicating effect as a selling point. No targeting or appeal to minors. No false origin claims. No disparagement of competitors. No government endorsement implication. |
| **Required Disclaimers** | Mandatory health warning on labels (Surgeon General's warning). Responsible drinking messaging encouraged/required by industry codes. ABV and origin disclosures on labels and in many ad formats. |
| **Marketing Restrictions** | Age-gating required on digital platforms (70% adult audience threshold for ad placement per industry codes). No use of cartoon characters, Santa Claus, or imagery appealing to minors. Platform-specific age restrictions apply. State-by-state rules on promotions, contests, and tied-house restrictions. |
| **Auto-Applied Rules** | Require age-gate on landing pages and social content. Flag health benefit claims. Require responsible drinking language ("Drink Responsibly," "21+ only"). Block content that appeals to minors (cartoons, child-associated imagery, school settings). Flag claims about intoxication level or speed. |

### 2.5 Cannabis — State Laws

| Field | Detail |
|---|---|
| **Industry** | Cannabis, CBD, Hemp Products |
| **Regulation** | No federal legalization (Schedule I under CSA); state-by-state licensing and advertising laws; 2018 Farm Bill (hemp/CBD) |
| **Regulatory Body** | State cannabis regulatory agencies; FDA (for CBD ingestibles); FTC (for advertising claims) |
| **Prohibited Claims** | No medical/health claims for cannabis or CBD unless FDA-approved (only Epidiolex as of 2025). No claims targeting minors. No false potency or composition claims. No "FDA approved" language. |
| **Required Disclaimers** | State-specific warnings (e.g., California Prop 65, Colorado THC warnings). "For use only by adults 21+" (or state-specific age). "Keep out of reach of children." Many states require license number in advertising. |
| **Marketing Restrictions** | Most states prohibit: billboards near schools, advertising on platforms with less than 71.6% adult audience, cartoon characters, lifestyle imagery suggesting safety. Some states require pre-approval of ads. Digital advertising severely restricted — most major platforms (Google, Meta, Amazon) prohibit paid cannabis ads. Email marketing is primary channel but must comply with state opt-in rules. |
| **Auto-Applied Rules** | Block all health/medical claims. Require 21+ age disclaimer. Require state-specific warning language. Flag any content that could appeal to minors. Block from major paid ad platforms. Flag cross-state marketing (different rules per state). Require license number disclosure. |

### 2.6 Real Estate — Fair Housing Act

| Field | Detail |
|---|---|
| **Industry** | Real Estate, Property Management, Mortgage, Rental |
| **Regulation** | Fair Housing Act (FHA); HUD advertising guidelines; State fair housing laws; Equal Credit Opportunity Act (ECOA) for lending |
| **Regulatory Body** | HUD (Department of Housing and Urban Development); State fair housing agencies; CFPB (for lending) |
| **Prohibited Claims** | No statements indicating preference, limitation, or discrimination based on race, color, national origin, religion, sex (including gender identity and sexual orientation per HUD 2021), familial status, or disability. |
| **Required Disclaimers** | Equal Housing Opportunity logo or statement in all advertising. ECOA disclosures for mortgage marketing. State-specific fair housing language. |
| **Marketing Restrictions** | Ad targeting cannot exclude protected classes (see Meta's Special Ad Category, Google's Housing category restrictions). Words/phrases to avoid: "exclusive neighborhood," "family-friendly" (implies no children preference), "walking distance to church" (religious preference), "master bedroom" (being phased out). Images must reflect diversity. HUD advertising guidelines provide detailed word lists. Digital ad targeting restrictions apply on all major platforms. |
| **Auto-Applied Rules** | Flag protected-class language (race, religion, familial status, disability references as preference). Require Equal Housing Opportunity statement. Flag exclusionary targeting criteria. Flag phrases from HUD's discriminatory language list. Require Special Ad Category selection on Meta/Google. Block demographic exclusion in audience targeting. |

### 2.7 Education — FERPA

| Field | Detail |
|---|---|
| **Industry** | Education, EdTech, Student Services |
| **Regulation** | FERPA (Family Educational Rights and Privacy Act); FTC Act (for marketing claims); State education privacy laws; COPPA (if under 13) |
| **Regulatory Body** | Department of Education (SPPO); FTC; State AGs |
| **Prohibited Claims** | No guaranteed employment outcomes unless substantiated. No misleading graduation rate claims. No false accreditation claims. Gainful Employment Rule requires outcome disclosures for certain programs. |
| **Required Disclaimers** | Accreditation status and type. Outcome disclosures (graduation rates, median debt, employment rates) for vocational programs. Financial aid disclosures. Net price calculator requirement for Title IV institutions. |
| **Marketing Restrictions** | Student education records (grades, enrollment, financial aid) cannot be used for marketing without consent. Directory information can be disclosed but students can opt out. EdTech vendors must limit data use to educational purposes. Incentive compensation ban: cannot pay recruiters based on enrollment numbers. |
| **Auto-Applied Rules** | Flag employment/salary guarantee claims. Require accreditation disclosure. Block use of student records for marketing personalization without consent. Flag "guaranteed job placement" language. Require outcome statistic sourcing. Flag incentive-based recruitment language. |

### 2.8 Children's Products — COPPA

| Field | Detail |
|---|---|
| **Industry** | Products/Services Directed at Children Under 13 (and under 16/18 in some jurisdictions) |
| **Regulation** | COPPA (Children's Online Privacy Protection Act, 1998; updated rule 2013; proposed amendments 2024); FTC Act; State laws (e.g., California Age-Appropriate Design Code) |
| **Regulatory Body** | FTC; State AGs; International equivalents (UK ICO Age Appropriate Design Code) |
| **Prohibited Claims** | No deceptive advertising to children. No pressure tactics or urgency manipulation ("buy now before it's gone") directed at children. No blurring of content and advertising (e.g., advergames without clear disclosure). |
| **Required Disclaimers** | Clear "Ad" or "Sponsored" labeling in content directed at children. Parental consent disclosures for data collection. |
| **Marketing Restrictions** | Verifiable parental consent (VPC) required before collecting personal info from children under 13. No behavioral advertising targeting children. No push notifications to children encouraging purchases. No collection of geolocation data from children without parental consent. Platforms directed at children must have robust age verification. CARU (Children's Advertising Review Unit) self-regulatory guidelines apply. |
| **Auto-Applied Rules** | Flag any content targeting users under 13 and require COPPA compliance review. Block behavioral ad targeting for children's audiences. Require parental consent mechanisms for data collection. Flag manipulative design patterns (dark patterns) in children's contexts. Block geolocation collection for child-directed services. Flag influencer content targeting children without clear ad disclosure. |

### 2.9 Supplements — FDA / FTC

| Field | Detail |
|---|---|
| **Industry** | Dietary Supplements, Nutraceuticals, Functional Foods |
| **Regulation** | DSHEA (Dietary Supplement Health and Education Act, 1994); FTC Act Section 5; FDA 21 CFR Part 101 (labeling); FTC Health Products Compliance Guidance |
| **Regulatory Body** | FDA (labeling, safety, manufacturing); FTC (advertising claims) |
| **Prohibited Claims** | No disease claims ("cures cancer," "treats diabetes") — these make the product an unapproved drug. No claims without competent and reliable scientific evidence. No misrepresentation of clinical studies. No before/after photos implying guaranteed results without typicality disclosure. |
| **Required Disclaimers** | Structure/function claims require: "This statement has not been evaluated by the Food and Drug Administration. This product is not intended to diagnose, treat, cure, or prevent any disease." Testimonials must disclose typical results if atypical results are presented. |
| **Marketing Restrictions** | Claims must be truthful, non-misleading, and substantiated. FTC requires "competent and reliable scientific evidence" (generally, at least one well-designed human clinical trial). Structure/function claims are permitted (e.g., "supports immune health") but disease claims are not. Celebrity/influencer endorsements must reflect honest experience and disclose material connections. |
| **Auto-Applied Rules** | Flag any disease claim (diagnose, treat, cure, prevent). Auto-insert FDA disclaimer on structure/function claims. Flag unsubstantiated efficacy claims. Require "results not typical" disclosure for testimonials with specific outcomes. Flag "clinically proven" unless backed by published peer-reviewed study. Block "FDA approved" language (supplements are not FDA-approved). |

### 2.10 Tech / SaaS — SOC 2 / GDPR Processor Rules

| Field | Detail |
|---|---|
| **Industry** | Software, SaaS, Cloud Services, Technology |
| **Regulation** | SOC 2 (AICPA Trust Services Criteria); GDPR Article 28 (processor obligations); ISO 27001; Industry-specific (HIPAA for health tech, PCI DSS for payment tech) |
| **Regulatory Body** | No single regulator. AICPA (SOC 2 framework); EU/UK DPAs (GDPR processor rules); Contractual obligations from enterprise customers |
| **Prohibited Claims** | No false security claims ("unhackable," "100% secure"). No misleading uptime guarantees without SLA terms. No "GDPR compliant" or "SOC 2 certified" claims unless accurate and current. No misrepresentation of data handling practices. |
| **Required Disclaimers** | SLA terms and limitations. Data processing location disclosure. Sub-processor disclosure. Incident notification commitments. Certification scope limitations (SOC 2 Type I vs Type II, ISO 27001 scope). |
| **Marketing Restrictions** | Security certifications must be accurately represented (SOC 2 Type II report covers a period, not a point in time). GDPR processor status requires a Data Processing Agreement with every customer. Marketing customer logos may require permission. Case study publication typically requires written customer approval. Competitive claims must be substantiated. |
| **Auto-Applied Rules** | Flag "100% secure," "unhackable," "guaranteed uptime" claims. Require SLA reference when mentioning uptime percentages. Flag certification claims and verify accuracy (SOC 2 Type I vs II, ISO 27001 scope). Require DPA availability mention in B2B marketing to EU audiences. Flag customer logos/names and verify permission. Flag competitive comparison claims and require substantiation. |

---

## Section 3: FTC Advertising Rules

### 3.1 FTC Endorsement Guides (Revised 2023)

| Rule | Requirement |
|---|---|
| **Material Connection Disclosure** | Any material connection between an endorser and the brand must be clearly and conspicuously disclosed. Material connections include: payment, free products, employment, family relationships, business partnerships, equity stakes, and affiliate commissions. |
| **Placement** | Disclosures must be in the same medium as the endorsement, unavoidable by the audience, and in clear language. For social media: within the post text (not hidden in hashtag strings), visible without clicking "more," and in the first lines of a caption. For video: spoken and in text overlay, not just in the description. |
| **Required Language** | Use clear terms: "#ad," "#sponsored," "Paid partnership with [Brand]." Ambiguous terms are insufficient: "#ambassador," "#collab," "#partner" alone do not meet FTC standards. Platform-specific disclosure tools (e.g., "Paid Partnership" tags) are helpful but may not be sufficient alone — a text disclosure is still recommended. |
| **Endorser Liability** | Both the brand AND the endorser can be held liable for non-disclosure. Brands must have reasonable monitoring programs for endorser compliance. Written agreements should include disclosure requirements. |
| **Honest Opinion** | Endorsements must reflect the honest opinion or experience of the endorser. Endorsers must have actually used the product/service. Scripts that misrepresent the endorser's experience violate FTC rules. |
| **Celebrity/Expert Endorsements** | Expert endorsers must have genuine expertise in the field. Celebrity endorsers must actually use the product. Expertise claims must be truthful. AI-generated or deepfake "endorsements" of real people without consent are deceptive. |

### 3.2 FTC Consumer Review Fairness and Rule on Fake Reviews (2024)

| Rule | Requirement |
|---|---|
| **Fake Reviews Ban** | Businesses may not create, buy, sell, or disseminate fake consumer reviews, testimonials, or celebrity endorsements. This includes reviews by employees or insiders not disclosing their connection. |
| **AI-Generated Reviews** | AI-generated reviews presented as human experiences are prohibited. AI-assisted review solicitation is permitted if the review reflects the genuine customer's experience. |
| **Review Suppression** | Businesses may not use unfounded legal threats, contract terms, or other means to suppress negative reviews. Filtering out only negative reviews while publishing positive ones is deceptive. |
| **Review Manipulation** | Buying positive reviews, incentivizing only positive reviews, or manipulating review platforms to boost ratings is prohibited. Soliciting reviews generally is permitted as long as the solicitation is not conditional on a positive review. |
| **Penalty** | Civil penalties up to $51,744 per violation. Applies to businesses, review brokers, and platforms that knowingly facilitate fake reviews. |

### 3.3 Influencer Disclosure Requirements

| Requirement | Detail |
|---|---|
| **When to Disclose** | Any time there is a material connection between the influencer and the brand — even for gifted products, affiliate links, or business relationships. |
| **How to Disclose** | Clear, unambiguous language at the beginning of the content. "#ad" at the start of social posts, spoken disclosure at the beginning of videos, and visible text in image posts. Must be understandable in the language of the audience. |
| **Platform-Specific** | Instagram/TikTok: "#ad" in first line + platform partnership label. YouTube: spoken + text in video + description box. Podcasts: spoken disclosure in the episode (not just show notes). Blog/newsletter: clear disclosure at the top of the post. |
| **Brand Responsibility** | Brands must: (1) clearly inform influencers of disclosure requirements in contracts, (2) monitor compliance, (3) take action when violations are found. A contractual clause alone is insufficient — active monitoring is required. |

### 3.4 AI-Generated Content Disclosure

| Requirement | Detail |
|---|---|
| **FTC Position** | AI-generated content that could be mistaken for human-created content must be disclosed. This includes AI-generated images, text, voices, and video used in marketing. |
| **Deepfakes** | Using AI to create realistic depictions of real people without their consent is deceptive. AI-generated endorsements by fabricated "people" must be disclosed as AI-generated. |
| **AI in Reviews** | AI-generated reviews are fake reviews under FTC rules. AI tools may assist humans in writing reviews, but the review must reflect genuine experience. |
| **Best Practice** | Disclose AI involvement in content creation when a reasonable consumer would consider it material. Label AI-generated imagery clearly. Do not use AI voices mimicking real individuals without consent and disclosure. |

### 3.5 Testimonial Rules

| Rule | Detail |
|---|---|
| **Typicality** | If a testimonial describes results that are not typical, the ad must clearly disclose what results consumers can generally expect. "Results not typical" alone is insufficient — must state typical results. |
| **Truthfulness** | Testimonials must reflect honest, genuine experiences. Cannot be fabricated, materially altered, or taken out of context. |
| **Substantiation** | Claims made through testimonials are treated as claims by the advertiser and must be substantiated. |
| **Expert Endorsements** | Must be supported by an actual examination, testing, or evaluation by the expert. The expert must have qualifications in the relevant field. |

### 3.6 FTC Penalty Structure

| Violation Type | Penalty Range |
|---|---|
| **Section 5 (Unfair or Deceptive Acts)** | Consent orders, cease and desist, corrective advertising. No direct fines for first-time Section 5 violations, but violation of a consent order: up to $51,744 per violation. |
| **Penalty Offense Authority** | FTC can seek civil penalties from companies that had prior notice that conduct is unlawful (via prior FTC cases). Up to $51,744 per violation. |
| **Fake Reviews Rule (2024)** | Civil penalties up to $51,744 per violation. |
| **COPPA Violations** | Up to $51,744 per violation. |
| **Restitution/Disgorgement** | FTC can seek consumer redress through federal courts. AMG Capital Management v. FTC (2021) limited FTC's Section 13(b) authority, but Congress is working to restore it. |

---

## Section 4: Platform-Specific Ad Policies

### 4.1 Google Ads

| Category | Policy Summary |
|---|---|
| **Prohibited Content** | Counterfeit goods, dangerous products, enabling dishonest behavior, inappropriate content, malware, weapons, tobacco, recreational drugs (including CBD in most regions). |
| **Prohibited Practices** | Abusing the ad network, data collection without disclosure, misrepresentation, cloaking (showing different content to reviewers vs. users), manipulating ad auction. |
| **Restricted Categories** | Alcohol (age/country restrictions), gambling (license required), healthcare/medicine (varies by country, FDA approval needed in US), financial services (must comply with local law, no deceptive claims), political advertising (verification required), adult content (limited placements). |
| **Healthcare Specifics** | Rx drug ads: US only (with caveats), must comply with FDA. Online pharmacy ads: VIPPS/CIPA certification required. Unapproved substances and supplements with drug claims are prohibited. Clinical trial recruitment has specific rules. |
| **AI/Automated Ads** | Performance Max and AI-generated creative must still comply with all policies. Advertisers are responsible for AI-generated ad content. |
| **Housing/Employment/Credit** | Special restrictions on targeting (no age, gender, zip code, or parental status targeting). Similar to Meta Special Ad Categories. |

### 4.2 Meta Ads (Facebook / Instagram)

| Category | Policy Summary |
|---|---|
| **Prohibited Content** | Illegal products, tobacco, drugs, unsafe supplements, weapons, surveillance equipment, payday loans (in many regions), multi-level marketing (restricted), before/after images for health/cosmetic products. |
| **Special Ad Categories** | Credit, Employment, Housing, Social Issues/Elections/Politics. These categories have restricted targeting: no age, gender, zip code, or interest-based exclusions. Must declare category before ad creation. Lookalike audiences replaced with Special Ad Audiences. |
| **Health & Wellness** | No before/after images. No claims implying personal attributes ("Are you overweight?"). No idealized body imagery. Weight loss claims require disclaimers. Supplements cannot make drug claims. |
| **Financial Products** | Crypto ads require written approval. Financial services must comply with local licensing. No misleading income claims. "Get rich quick" content is prohibited. |
| **Data & Targeting** | Custom Audiences must be based on consented data. No targeting sensitive categories (health conditions, ethnicity, religion, sexual orientation) — even via proxy targeting. Lead form data must comply with Platform Terms and advertiser's privacy policy. |
| **Content Quality** | No clickbait, sensationalism, or engagement bait. No misleading buttons or UI elements. Landing page must match ad content. No excessive text in images (guideline, not hard rule). |

### 4.3 LinkedIn Ads

| Category | Policy Summary |
|---|---|
| **Prohibited Content** | Illegal products, weapons, tobacco, recreational drugs, adult content, counterfeit goods, spyware/malware, deceptive offers. |
| **Professional Standards** | Content must be appropriate for a professional audience. No vulgar or offensive content. No political or religious advertising (with limited country exceptions for political ads). |
| **B2B Specifics** | Job ads must comply with employment law (no discriminatory targeting or language). Financial claims must be substantiated. No misleading job opportunity claims. Salary claims must be verifiable. |
| **Targeting Restrictions** | No targeting by age, gender, or ethnicity for employment, housing, education, or credit ads. Sensitive category targeting (health, political, religious) is restricted. |
| **Lead Generation** | Lead Gen Forms must link to a privacy policy. Data collected must be used consistent with advertiser's stated purpose. Auto-fill data is shared with advertiser — users must consent. |

### 4.4 TikTok Ads

| Category | Policy Summary |
|---|---|
| **Prohibited Content** | Illegal products, weapons, tobacco, drugs, dangerous challenges, animal products from endangered species, adult content, counterfeit goods, political advertising (banned globally). |
| **Age Sensitivity** | Platform skews young — extra scrutiny on age-gating for alcohol, gambling, and finance. No ads directed at users under 13. Ads for age-restricted products must use age-gate targeting. |
| **Health & Beauty** | No extreme weight loss claims. No before/after images implying guaranteed results. No misleading beauty claims. Supplement ads must comply with local regulations. |
| **Financial Services** | Crypto advertising highly restricted or banned (varies by country). Financial products require licensing disclosure. No "get rich quick" or income guarantee content. |
| **Content Standards** | Ads must not impersonate news content or government announcements. No deepfakes or manipulated media of real people. Branded content must use the Branded Content toggle. Spark Ads (boosting organic content) must comply with all ad policies. |

### 4.5 Amazon Ads

| Category | Policy Summary |
|---|---|
| **Prohibited Content** | Illegal products, tobacco, weapons, offensive content, false claims, competitive disparagement, political advertising. |
| **Product Specifics** | Claims must match product listing. No inconsistency between ad and product detail page. Star ratings must be accurate and current. No "best seller" claims unless backed by Amazon data. |
| **Health & Supplements** | Supplement ads cannot make disease claims. Must include required FDA disclaimer. No unapproved health claims. OTC drug ads must comply with FDA requirements. |
| **Restricted Categories** | Alcohol (limited, marketplace-specific). CBD (prohibited in most regions). Gambling (prohibited). Financial services (restricted). Academic paper writing services (prohibited). |
| **Creative Standards** | No custom "add to cart" buttons or fake interactive elements. No pressure tactics ("only 2 left" in ad creative). Mobile-friendly creative required. No blurry or pixelated images. Logos must not mimic Amazon branding. |

---

## Section 5: Accessibility Requirements

### 5.1 WCAG 2.1 AA — Marketing Content Requirements

| Criterion | Requirement | Marketing Application |
|---|---|---|
| **1.1.1 Non-text Content** | All non-text content has a text alternative serving the equivalent purpose. | All marketing images, infographics, charts, and icons require meaningful alt text. Decorative images use empty alt (`alt=""`). CTA buttons in images must have alt text describing the action. |
| **1.2.1 Audio/Video (Prerecorded)** | Provide alternatives for time-based media. | Marketing videos require captions. Podcasts require transcripts. Webinar recordings need both captions and descriptive audio where visual-only info is presented. |
| **1.2.2 Captions (Prerecorded)** | Captions for all prerecorded audio in synchronized media. | All video ads, social media videos, and embedded video content must have accurate captions — not auto-generated without review. |
| **1.2.5 Audio Description (Prerecorded)** | Audio description for prerecorded video content (AA). | Marketing videos where visual-only content conveys key information need audio description tracks (e.g., product demos, tutorials). |
| **1.3.1 Info and Relationships** | Structure and relationships conveyed through presentation are programmatically determinable. | Email templates must use semantic HTML (headings, lists, tables with headers). Landing pages must use proper heading hierarchy. Forms must have associated labels. |
| **1.3.2 Meaningful Sequence** | Content reading order is correct when linearized. | Email layouts must make sense when CSS is disabled or images don't load. Single-column fallback for responsive emails. |
| **1.4.1 Use of Color** | Color is not the only visual means of conveying information. | CTA buttons must not rely solely on color to indicate interactivity. Error states in forms need text labels, not just red highlighting. Charts need patterns or labels in addition to color coding. |
| **1.4.3 Contrast (Minimum)** | Text: 4.5:1 contrast ratio. Large text (18pt+ or 14pt+ bold): 3:1. | All marketing copy, CTAs, and navigation text must meet contrast minimums. Brand colors must be tested. White text on light backgrounds and light gray text are common failures. |
| **1.4.4 Resize Text** | Text can be resized up to 200% without loss of content or functionality. | Landing pages and web content must remain functional at 200% zoom. No fixed-width containers that cause horizontal scrolling. |
| **1.4.5 Images of Text** | Use actual text rather than images of text (with exceptions for logos). | Avoid embedding key marketing copy in images. Headline text in banner ads should be HTML where possible. Social images with text should have alt text containing the text. |
| **1.4.11 Non-text Contrast** | UI components and graphical objects: 3:1 contrast against adjacent colors. | Form field borders, CTA button borders, icons, and chart elements must meet 3:1 contrast. Focus indicators must be visible. |
| **2.1.1 Keyboard** | All functionality operable through keyboard interface. | Navigation menus, forms, modals, carousels, accordions, and interactive elements on landing pages must be fully keyboard-accessible. No keyboard traps. |
| **2.4.4 Link Purpose (In Context)** | Purpose of each link can be determined from link text or context. | Avoid "Click here" and "Read more" as standalone link text. Use descriptive text: "Download the 2025 Marketing Report" instead of "Download." |
| **2.4.6 Headings and Labels** | Headings and labels describe topic or purpose. | Landing page sections need descriptive headings. Form labels must clearly describe the expected input. |
| **2.4.7 Focus Visible** | Keyboard focus indicator is visible. | Do not remove outline styles from interactive elements on landing pages. Custom focus indicators must meet 3:1 contrast. |
| **3.1.1 Language of Page** | Default human language of each page is programmatically determinable. | Set `lang` attribute on HTML element. Multilingual marketing pages need `lang` attributes on sections in different languages. |
| **3.2.1 On Focus** | No context change on focus. | No auto-redirect, modal popup, or form submission triggered solely by focusing an element. |
| **3.2.2 On Input** | No context change on input unless user is informed beforehand. | Form field changes should not trigger page navigation. Auto-submit on dropdown selection is non-compliant without warning. |
| **4.1.2 Name, Role, Value** | All UI components have accessible name, role, and state information. | Custom components (dropdowns, toggles, tabs, sliders) on landing pages must use ARIA roles, states, and properties correctly. |

### 5.2 ADA Website Compliance

| Requirement | Detail |
|---|---|
| **Legal Basis** | Title III of the Americans with Disabilities Act. DOJ has confirmed that websites of public accommodations must be accessible. No specific technical standard is codified, but courts consistently reference WCAG 2.1 AA as the benchmark. |
| **Who Is Covered** | Any business that is a "place of public accommodation" (virtually all commercial websites, including e-commerce, SaaS, services, media). |
| **Enforcement** | Private lawsuits (ADA Title III does not provide damages in federal court but does in some states, notably California's Unruh Act: $4,000 minimum per violation per visit). DOJ enforcement actions. Demand letters are common. |
| **Marketing Implications** | All landing pages, microsites, campaign pages, and promotional web content must be WCAG 2.1 AA compliant. Pop-ups and modals must be keyboard-accessible and screen-reader-compatible. Video content needs captions. PDFs (whitepapers, ebooks) must be tagged for accessibility. Forms must have labels, error handling, and keyboard access. |
| **Auto-Applied Rules** | Flag landing pages without accessibility review. Require alt text on all images. Require caption files for video content. Flag color contrast issues in design assets. Require keyboard-accessible interactive elements. Flag PDF deliverables without accessibility tagging. |

### 5.3 Email Accessibility Standards

| Requirement | Detail |
|---|---|
| **Semantic HTML** | Use proper HTML elements: `<h1>`–`<h6>` for headings, `<p>` for paragraphs, `<table>` with `role="presentation"` for layout tables, `<th>` for data table headers. |
| **Alt Text** | Every `<img>` must have an `alt` attribute. Meaningful images get descriptive alt text. Decorative images use `alt=""`. CTA images (buttons, banners) get action-oriented alt text. |
| **Color Contrast** | Body text: 4.5:1 minimum. Large text: 3:1 minimum. CTA buttons: text must contrast with button background AND button must contrast with email background. |
| **Font Size** | Minimum 14px for body text, 22px+ for headings. Avoid font sizes below 12px for any content. Use relative units where supported. |
| **Link Styling** | Links must be distinguishable from surrounding text by more than just color (underline is standard). Link text must be descriptive. Avoid multiple links with identical text pointing to different URLs. |
| **Structure** | Single-column layouts are most accessible. If multi-column, ensure proper reading order in code. Use `dir` and `lang` attributes. Avoid relying on CSS-only layout that breaks in stripped-down email clients. |
| **Dark Mode** | Test in dark mode. Use transparent PNGs or match background colors. Ensure text remains readable when background colors are overridden. Provide both light and dark mode color declarations where supported. |
| **Screen Reader** | Include a `role="article"` on the main content wrapper. Use `aria-label` for navigation links if applicable. Avoid "View in browser" as the only way to access content. Preheader text should be meaningful (it's read aloud by screen readers). |
| **Auto-Applied Rules** | Flag images without alt text. Flag text below 4.5:1 contrast ratio. Flag body text below 14px. Flag link text that says "Click here" or "Read more." Flag layout tables without `role="presentation"`. Require single-column fallback for mobile/accessibility. |

---

## Rule Application Reference

When the context engine evaluates marketing content, apply rules in this priority order:

1. **Geographic law** — Identify target audience jurisdiction(s) and apply ALL applicable privacy/consent rules
2. **Industry regulation** — Identify the advertiser's industry and apply sector-specific restrictions
3. **FTC advertising rules** — Apply to all US-targeted content regardless of industry
4. **Platform policies** — Apply the specific platform's rules for the distribution channel
5. **Accessibility** — Apply WCAG 2.1 AA and email accessibility standards to all outputs

When rules conflict, apply the **most restrictive** standard. When jurisdiction is unknown, default to **GDPR + CPRA + FTC** as the baseline.

### Severity Levels

| Level | Definition | Action |
|---|---|---|
| **BLOCK** | Violation would be illegal or result in platform ban (false health claims, missing disclosures on regulated products, COPPA violations, discriminatory targeting). | Do not output. Flag to user with specific rule citation. |
| **WARN** | Likely violation requiring human review (ambiguous claims, missing disclaimers, potential trademark issues, accessibility gaps). | Output with prominent warning and recommended fix. |
| **SUGGEST** | Best practice not strictly required by law but reduces risk (double opt-in where only opt-out required, adding disclaimers proactively, exceeding minimum contrast ratios). | Output with suggestion as a footnote. |
