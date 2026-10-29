# Compliance Rules Reference

This file is the canonical compliance ruleset for the Digital Marketing Pro plugin. All marketing modules MUST check outputs against these rules before delivery. Rules are structured for programmatic consumption by the context engine.

## Dated obligations (check before each date)

Every date below was read at the source named, and each Section 1 entry carries a **Verified** row saying when it was last checked. `tests/test_compliance_dates.py` fails when a date in this table passes while its row still says `upcoming`, and when a Verified stamp goes stale; the weekly dated-checks job runs it. When a date arrives, update the section it points to and mark the row `in force`.

| Date | Jurisdiction | What changes | Section | Source | Status |
|---|---|---|---|---|---|
| 2026-02-05 | United Kingdom | PECR: new cookie exceptions (analytics to improve your own service, appearance), charity soft opt-in, PECR fines at the UK GDPR higher maximum | 1.7 | The Data (Use and Access) Act 2025 (Commencement No. 6) Regulations 2026, reg. 2 | in force |
| 2026-08-01 | California | Delete Act: registered data brokers process DROP deletion requests at least every 45 days | 1.3 | cppa.ca.gov/data_brokers (Civ. Code 1798.99.86(c)) | in force |
| 2026-08-02 | European Union | AI Act Article 50 transparency obligations apply | 1.1b | AI Act Service Desk timeline | in force |
| 2026-08-02 | California | AI Transparency Act (SB 942 as amended by AB 853) operative | 1.3 | AB 853, Ch. 674 (leginfo) | in force |
| 2026-11-13 | India | DPDP Rule 4: Consent Manager registration opens (one year after the 13 Nov 2025 notification) | 1.11 | DPDP Rules 2025, rule 1(3), G.S.R. 846(E) | upcoming |
| 2026-11-25 | United States (FCC) | TCPA: a revocation may be treated as covering only the category of informational calls or texts it answered; callers may designate an exclusive means to revoke | 1.2 | 91 FR 67214 (FCC, 26 Oct 2026) | upcoming |
| 2026-12-02 | European Union | Article 50(2) marking deadline for generative AI systems already on the market before 2 Aug 2026; new prohibition on AI that generates non-consensual sexual deepfakes or CSAM | 1.1b | AI Act Service Desk timeline; Commission guidelines C(2026) 5054 | upcoming |
| 2027-01-01 | California | AB 566 browser opt-out preference signal; AI Transparency Act duties for large online platforms; CPPA automated decision-making (ADMT) compliance | 1.3 | AB 566, Ch. 465; AB 853, Ch. 674; CPPA regulations | upcoming |
| 2027-01-01 | Oklahoma | SB 546 consumer data privacy law takes effect | 1.4 | SB 546 enrolled text, section 22 | upcoming |
| 2027-05-01 | Alabama | HB 351 consumer data privacy law takes effect | 1.4 | HB 351 enrolled text, section 12 | upcoming |
| 2027-05-13 | India | DPDP Rules 3, 5-16, 22 and 23 (notice, security, breach notification, children's verifiable consent, rights, retention) apply | 1.11 | DPDP Rules 2025, rule 1(4) | upcoming |
| 2027-12-02 | European Union | AI Act high-risk rules for Annex III systems apply (moved by the Digital Omnibus on AI) | 1.1b | AI Act Service Desk timeline | upcoming |
| 2028-01-01 | California | AI Transparency Act duties for capture-device makers | 1.3 | AB 853, Ch. 674 | upcoming |
| 2028-08-02 | European Union | AI Act high-risk rules for Annex I regulated products apply | 1.1b | AI Act Service Desk timeline | upcoming |

---

## Section 1: Geographic Privacy Laws

### 1.1 EU/EEA — General Data Protection Regulation (GDPR)

| Field | Detail |
|---|---|
| **Region** | European Union / European Economic Area (27 EU member states + Iceland, Liechtenstein, Norway) |
| **Law** | General Data Protection Regulation (GDPR) |
| **Year Enacted** | 2016 (enforced May 25, 2018) |
| **Consent Model** | Consent is one of six lawful bases (GDPR Art 6(1)). Valid consent is "freely given, specific, informed and unambiguous" (Art 4(11)). Silence or pre-ticked boxes are not consent (Recital 32). "Explicit" consent applies only to special-category data (Art 9(2)(a)). Direct marketing "may be regarded as carried out for a legitimate interest" after a balancing test (Recital 47). Consent must be as easy to withdraw as to give (Art 7(3)). |
| **Email Rules** | Set by ePrivacy Directive Art 13 as each country applies it. Prior consent is needed for marketing email to individuals (Art 13(1)). Soft opt-in: own similar products, with an opt-out at collection and in every message (Art 13(2)). Email to businesses as legal persons is left to each member state (Art 13(5)). Never hide the sender, and always give a valid address for opt-out requests (Art 13(4)). After an objection, stop direct marketing (GDPR Art 21(3)). |
| **Cookie/Tracking Rules** | Consent is needed before storing or reading anything on a device, except what is "strictly necessary" for a service the user requested (ePrivacy Art 5(3)). Consent must meet the GDPR standard, with separate consent for each purpose (Recital 32). Pending: the Digital Omnibus (Commission proposal 19 Nov 2025; Council position 21 Oct 2026) would add consent-free purposes such as audience measurement and device security. It is not law yet. |
| **Penalty Range** | Up to EUR 20 million or 4% of global annual turnover, whichever is higher. Supervisory authorities may also issue warnings, bans on processing, and orders to erase data. |
| **Key Marketing Impact** | Have a contract with every processor (Art 28(3)). Privacy notices list "the recipients or categories of recipients" (Art 13(1)(e)). People may object at any time to direct marketing, including profiling linked to it (Art 21(2)), and an objection triggers erasure (Art 17). Transfers outside the EEA need an adequacy decision, SCCs or BCRs (Arts 45–46), or a derogation (Art 49). Double opt-in is good practice, not law. |
| **Verified** | 2026-10-27: every row against the GDPR and ePrivacy texts on EUR-Lex and the Council press release of 21 Oct 2026 (Digital Omnibus still a proposal) |

### 1.1b EU/EEA — AI Act Article 50 (Generative AI Disclosure)

| Field | Detail |
|---|---|
| **Region** | European Union / European Economic Area |
| **Law** | Regulation (EU) 2024/1689 — Artificial Intelligence Act, Article 50 (Transparency obligations for providers and deployers of certain AI systems) |
| **Applicable** | **2 August 2026** (transparency obligations). Generative AI systems placed on the market before 2 Aug 2026 have until **2 December 2026** to add the Article 50(2) machine-readable marking; the disclosure duty for systems that interact with people applied from 2 Aug 2026 either way. General-purpose AI obligations applied 2 Aug 2025. High-risk rules, as moved by the Digital Omnibus on AI: Annex III systems from 2 Dec 2027, Annex I regulated products from 2 Aug 2028. From 2 Dec 2026, AI systems that generate non-consensual sexual deepfakes or child sexual abuse material are prohibited. |
| **Existing and republished content** | Output generated or manipulated before 2 Aug 2026 need not be marked or labelled retroactively. But AI-generated text on a matter of public interest that was generated before 2 Aug 2026 and **published on or after** that date must be labelled (Commission guidelines C(2026) 5054, 20 Jul 2026, para 154). Republishing old AI copy is a new publication. |
| **Scope** | All generative-AI outputs distributed in EU markets — no minimum spend threshold, advertising not exempted. Both providers (AI developers) and deployers (advertisers, brands) bear obligations. |
| **Disclosure Requirements** | (a) AI-generated or AI-manipulated content **must be marked in a machine-readable format** using open, interoperable standards. **C2PA (Coalition for Content Provenance and Authenticity) is the emerging backbone.** Marking must be technically robust and survive routine processing. (b) Deepfakes (synthetic audio/image/video resembling real persons, objects, places, or events) must be **visibly disclosed**. (c) AI-generated text on matters of public interest must be disclosed unless human-reviewed and the brand assumes editorial responsibility. |
| **Carve-outs** | Genuine artistic, satirical, or fictional works are narrowly exempt — applies in limited cases and does not blanket-exempt marketing. |
| **Penalty Range** | Up to **EUR 15 million or 3% of global annual turnover**, whichever is higher (transparency obligations). High-risk system breaches up to EUR 35M or 7%. |
| **Verified** | 2026-10-27: dates and the retroactivity rule above, against the AI Act Service Desk timeline and guidelines C(2026) 5054 |
| **Key Marketing Impact** | Any AI-generated ad creative, social image, AI-narrated video, or AI-written long-form copy distributed in the EU must carry machine-readable provenance metadata. Use `/digital-marketing-pro:c2pa-metadata` to embed a C2PA manifest in any AI-generated image / video / audio / PDF before EU publication. Deepfakes need an additional visible disclosure overlay or audio cue. AI-written editorial pieces need an "AI-assisted" byline unless the human editor assumes full editorial accountability. The pre-publish gate (`/digital-marketing-pro:check`) verifies C2PA presence on AI-flagged assets in EU-targeted campaigns. |

#### 1.1b.i — Article 50 implementing guidelines (FINAL, 2026)

The European Commission published draft implementing guidelines for Article 50 on 8 May 2026 (consultation closed 3 June) and has since **adopted the final Guidelines** (C(2026) 5054, 20 July 2026), alongside the AI Office's **final Code of Practice on Transparency of AI-Generated Content (10 June 2026)** — both ahead of the 2 August 2026 applicability date. The clarifications below carried through from the draft into the final interpretation:

| Topic | Final guidance (2026) | What this means for marketing |
|---|---|---|
| **"Substantial AI manipulation"** | Defined as any AI-driven change that alters meaning, identity, or factual claims of a real person, object, place, or event. Routine colour correction, framing, denoising are NOT in scope. | A subject-replacement image swap = substantial manipulation (disclosure). A Lightroom-style retouch = not. |
| **"Matters of public interest"** | Includes health, elections, finance, government services, public safety, and any topic where a reasonable consumer expects journalistic accuracy. Marketing copy itself is generally not in scope UNLESS it crosses into one of those topics (e.g., health claims, financial product claims). | Generic product copy = no AI disclosure required. AI-generated copy making health, financial, or political claims = disclosure required unless a human editor signs off. |
| **Machine-readable marking** | C2PA Content Credentials are explicitly named as a "presumption of compliance" pathway. Alternative open-standard markings allowed if technically equivalent. | Continue using C2PA via `/digital-marketing-pro:c2pa-metadata`. Brands that ship without C2PA must show equivalent provenance — substantially more work. |
| **Deepfake visible disclosure** | Visible label, watermark, or audio cue must be perceivable at normal viewing/listening distance. Hidden corner overlays in a tiny font are explicitly insufficient. | If you produce a synthetic-talent ad or AI-cloned voice ad for the EU market, the disclosure must be visible from any normal viewing distance. |
| **Editorial-responsibility carve-out** | Human reviewer must (a) be identifiable, (b) have authority to alter or reject the AI output, (c) have a documented review record. A pure rubber-stamp does not satisfy the carve-out. | A documented reviewer scorecard (e.g. the quality-assurance agent's logged eval) satisfies (c), but a named human editor must still sign off and that name must be on the published piece (byline, masthead, or accessible "About this article" link). |
| **Enforcement priority** | National regulators are expected to prioritise (1) deepfakes, (2) AI-generated political/health content, (3) AI-generated content marketed without any provenance metadata at all. Routine commercial creative with C2PA is low priority. | Brands using C2PA across EU-distributed AI assets are in a strong defensive posture under the final guidelines. |

**Action items for brands with EU exposure (Article 50 applies since 2 August 2026):**

1. **Audit your EU AI-asset inventory now.** Catalogue any AI-generated image, video, audio, deepfake-style synthetic content, and AI-written long-form copy distributed to EU users in the last 12 months. Identify which carry C2PA and which don't.
2. **Lock in your C2PA signing-cert procurement immediately — Article 50 applies 2 August 2026.** See `docs/c2pa-production-cert-guide.md` for the four recognised authorities. Allow 2–4 weeks for Adobe Content Credentials approval.
3. **Update your Definition of Done.** Any creative produced for EU distribution should be C2PA-signed at production time, not retrofitted at publish time. The pre-publish gate (`/digital-marketing-pro:check`) blocks unsigned AI assets for EU-targeted campaigns.
4. **Treat the carve-out as conditional, not a free pass.** "Human-reviewed" requires named accountability. Don't claim editorial responsibility unless a named editor is willing to be on the record.

### 1.2 United States Federal — CAN-SPAM Act

| Field | Detail |
|---|---|
| **Region** | United States (federal) |
| **Law** | Controlling the Assault of Non-Solicited Pornography and Marketing Act (CAN-SPAM) |
| **Year Enacted** | 2003 (effective January 1, 2004; amended 2008) |
| **Consent Model** | Opt-out. No prior consent required to send commercial email. Recipients must be given a clear way to opt out, and opt-out requests must be honored within 10 business days. |
| **Email Rules** | No deceptive subject lines. "From" and "Reply-To" must accurately identify the sender. Every commercial email must include: a clear identification as an advertisement (if applicable), the sender's valid physical postal address, and a conspicuous opt-out mechanism. Purchased lists are legal but opt-out obligations still apply. Transactional emails are exempt if their primary purpose is transactional. |
| **Cookie/Tracking Rules** | No federal cookie consent law. Tracking pixels in email are legal. The FTC enforces against deceptive tracking practices under Section 5 of the FTC Act. |
| **Penalty Range** | Civil penalties per violation (per email): $53,088, the 2025 level, which the FTC kept unchanged for 2026 (notice published 15 Sep 2026). ISPs and state attorneys general may also bring actions. |
| **SMS and calls (TCPA)** | Marketing texts and autodialed or prerecorded marketing calls need prior express written consent; informational ones need prior express consent. Consumers may revoke consent by any reasonable means, and revocations must be honoured within 10 business days (FCC 2024 rule). **From 25 Nov 2026** (91 FR 67214): a caller may treat a revocation as applying only to the category of informational calls or texts it answered, and may designate an exclusive means to revoke consent. A STOP to marketing messages still ends marketing messages. The FCC is consulting on shortening the 10-day window (comments due 25 Nov 2026). |
| **Verified** | 2026-10-27: penalty level (FTC notice, 15 Sep 2026) and the TCPA rule (Federal Register, 26 Oct 2026) |
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
| **Penalty Range** | Up to $2,663 per violation; $7,988 per intentional violation or violation involving consumers under 16 (inflation-adjusted from 1 Jan 2025; the CPPA adjusts in odd years). Private right of action for data breaches ($107–$799 per consumer per incident). Business threshold: $26,625,000 annual gross revenue. Enforced by the California Privacy Protection Agency (CPPA). |
| **AI, signals and brokers** | **AI Transparency Act** (SB 942 as amended by AB 853, Ch. 674): operative 2 Aug 2026 for providers of generative AI systems with over 1,000,000 monthly users (an AI-detection tool and provenance disclosures); large online platforms must detect and surface provenance data from 1 Jan 2027; capture-device makers from 1 Jan 2028; $5,000 per violation, each day a separate violation. **AB 566** (Ch. 465): from 1 Jan 2027 every browser must offer an opt-out preference signal, so expect more GPC-style signals to honour. **CPPA automated decision-making (ADMT) rules:** compliance from 1 Jan 2027 for significant decisions made with ADMT. **Delete Act:** from 1 Aug 2026 registered data brokers process deletion requests from the DROP platform at least every 45 days, so broker-sourced lists will shrink. |
| **Verified** | 2026-10-27: penalties (cppa.ca.gov inflation-adjustment page), AB 853 and AB 566 (chaptered text on leginfo), DROP (cppa.ca.gov) |
| **Key Marketing Impact** | Retargeting audiences using third-party data requires opt-out mechanism. Service provider agreements needed with all martech vendors. 12-month lookback on data collection disclosures. "Sensitive personal information" (e.g., geolocation, race, health) triggers additional restrictions — limit use to what is necessary. |

### 1.4 US State Privacy Laws (Multi-State Summary)

| Field | Detail |
|---|---|
| **Region** | United States — 20+ states with enacted comprehensive privacy laws |
| **Laws** | Virginia (VCDPA, 2023), Colorado (CPA, 2023), Connecticut (CTDPA, 2023), Utah (UCPA, 2023), Iowa (ICDPA, 2025), Indiana (ICDPA, 2026), Tennessee (TIPA, 2025), Montana (MCDPA, 2024), Texas (TDPSA, 2024), Oregon (OCPA, 2024), Delaware (DPDPA, 2025), New Hampshire (SB 255, 2025), New Jersey (SB 332, 2025), Nebraska (NDPA, 2025), Maryland (MODPA, 2025), Minnesota (MCDPA, 2025), Rhode Island (RIDPA, 2026), Kentucky (KCDPA, 2026), Oklahoma (SB 546, effective 1 Jan 2027), Alabama (HB 351, effective 1 May 2027), Vermont (S.71, signed 16 Jun 2026; reported as Act 145, effective 1 Jan 2028), and others pending. Connecticut's amended CTDPA applies at 35,000 consumers, or to any processing of sensitive data, or to any sale of data; a controller may not process a minor's data for targeted advertising or sale, and needs consent before profiling a minor (Attorney General's CTDPA page). The amending act (SB 1295, reported as PA 25-113, effective 1 Jul 2026) was not read in its enacted text. |
| **Year Enacted** | Rolling: 2021–2026. Most operative between 2023–2026. |
| **Consent Model** | Generally opt-out for sale of data and targeted advertising. Opt-in for sensitive data processing. Most follow the VCDPA template. Maryland and Minnesota are more restrictive (closer to GDPR's data minimization standard). |
| **Email Rules** | Defer to CAN-SPAM federally. State laws add data rights (access, deletion, correction, portability) that affect CRM and email list management. |
| **Cookie/Tracking Rules** | Most require opt-out rights for targeted advertising (which implicates ad cookies and pixels). Universal opt-out mechanisms (like GPC) are mandated in Colorado, Connecticut, Texas, Montana, Oregon, Delaware, and others. |
| **Penalty Range** | Set state by state, mostly enforced by the state Attorney General. Connecticut: up to $5,000 per violation (Attorney General's CTDPA page). Many other states allow up to $7,500 per violation (not re-read state by state on 2026-10-27; check the statute before quoting a figure). Few have private rights of action. Cure periods (30–60 days) are common in early-enacted laws but are being removed in newer laws. |
| **AI laws** | Colorado SB 26-189 (signed 14 May 2026) repeals and re-enacts the SB 24-205 AI Act as an automated decision-making law. From 1 Jan 2027, deployers using it in consequential decisions (education, employment, housing, lending, insurance, health care, government services) must give advance notice, explain adverse outcomes within 30 days, and offer data correction and human review on request. AG-only enforcement; 60-day cure notice until 1 Jan 2030; no new private right of action (leg.colorado.gov). |
| **Verified** | 2026-10-27: Oklahoma and Alabama effective dates (enrolled texts); Colorado SB 26-189 (the signed act, leg.colorado.gov); Vermont's signing (the Governor's 2026 bill-action page); Connecticut's threshold, minors rule and penalty (the Attorney General's CTDPA page). Vermont's act number and effective date and Connecticut's act number and date are reported: legislature.vermont.gov and cga.ct.gov refused connections from here |
| **Key Marketing Impact** | Treat the US as a patchwork. The safest approach is to build to the most restrictive standard (currently Maryland or CPRA) and apply nationally. Universal opt-out signal support is becoming table stakes. Data mapping is essential to know which state laws apply to which consumers. |

### 1.5 Canada — CASL

| Field | Detail |
|---|---|
| **Region** | Canada |
| **Law** | Canada's Anti-Spam Legislation (CASL) |
| **Year Enacted** | Royal Assent 15 Dec 2010 (S.C. 2010, c. 23). Most provisions in force 1 July 2014; the software-installation rule (s.8) from 15 Jan 2015. |
| **Consent Model** | Express consent is required. Implied consent applies to an existing business relationship (purchase within 2 years, inquiry within 6 months, s.10(10)); a conspicuously published address relevant to the person's role (s.10(9)(b)); or an address the person gave you without saying no (s.10(9)(c)). One message after a named referral is exempt (SOR/2013-221 s.4). |
| **Email Rules** | Identify the sender and give a mailing address plus a phone number, email or web address (SOR/2012-36 s.2), valid for 60 days (s.6(3)). Unsubscribe requests are honoured within 10 business days (s.11(3)). A message asking for consent is itself a commercial message (s.1(3)), so you cannot email to ask. Keep proof of consent (s.13). |
| **Cookie/Tracking Rules** | Installing software needs express consent (s.8). Cookies, HTML and JavaScript count as consented to where the person's conduct shows consent (s.10(8); CRTC FAQ). Under PIPEDA, the privacy regulator (OPC) says opt-out consent may be acceptable for behavioural ads if strict conditions are met. |
| **Penalty Range** | Up to $1M per violation for individuals and $10M for businesses (s.20(4)), enforced by the CRTC. There is no private right of action: sections 47–51 were "Repealed before coming into force". |
| **Key Marketing Impact** | One of the strictest email laws globally. Implied consent windows are short — CRM must track consent expiry. "Conspicuous publication" is narrow and does not cover scraping. B2B cold outreach is heavily restricted. Referral/tell-a-friend programs require careful structuring. |
| **Verified** | 2026-10-27: every row against the Act on laws-lois.justice.gc.ca (current to 2026-09-30), its regulations and the CRTC FAQ |

### 1.6 Brazil — LGPD

| Field | Detail |
|---|---|
| **Region** | Brazil |
| **Law** | Lei Geral de Protecao de Dados (LGPD) |
| **Year Enacted** | 2018 (enforced September 2020; penalties from August 2021) |
| **Consent Model** | Consent must be "livre, informada e inequívoca" (Art 5 XII). Legitimate interest is an alternative (Art 7 IX); ANPD may request an impact report (Art 10 §3). The ANPD guide of 2 Feb 2024 gives a three-stage balancing-test model. |
| **Email Rules** | Consent or legitimate interest required. Unsubscribe must be easy and immediate. Data subjects have rights to access, correction, deletion, and portability. Marketing communications must identify the sender and purpose. |
| **Cookie/Tracking Rules** | The ANPD cookie guide (v1.0, Oct 2022) accepts legitimate interest for strictly necessary cookies and, in some contexts, aggregated audience measurement. It says legitimate interest "dificilmente será" right for advertising cookies, so ad cookies effectively need consent. It recommends a reject-all button on the first-layer banner and consent cookies switched off by default. |
| **Penalty Range** | Up to 2% of Brazilian revenue, capped at R$50M per infraction (Art 52 II), set by the ANPD fine-calculation rules (Resolution 4/2023). Also warnings, publicising the breach, blocking or deleting data, and suspension or prohibition of processing. |
| **Key Marketing Impact** | Appoint a DPO (Art 41). Small businesses are exempt unless their processing is high-risk or their revenue exceeds the legal limit, but they must offer a contact channel (Resolution 2/2022 Arts 3 and 11). Transfers rely on Art 33, ANPD standard contractual clauses (Resolution 19/2024), or adequacy; the EU and EEA have been adequate since 26 Jan 2026 (Resolution 32/2026). ANPD is now the Agência Nacional de Proteção de Dados (Lei 15.352/2026). |
| **Verified** | 2026-10-27: every row against Lei 13.709 on planalto.gov.br and the ANPD resolutions and guides on gov.br/anpd |

### 1.7 United Kingdom — UK GDPR + PECR

| Field | Detail |
|---|---|
| **Region** | United Kingdom |
| **Law** | UK General Data Protection Regulation (UK GDPR) + Privacy and Electronic Communications Regulations (PECR) |
| **Year Enacted** | UK GDPR: 2018 (retained post-Brexit, 2021). PECR: 2003. |
| **Consent Model** | Opt-in for marketing. PECR requires prior consent for unsolicited marketing emails to individuals. Soft opt-in exception (similar to EU): existing customers can be emailed about similar products if opt-out was offered at collection and in each message; since 5 Feb 2026 charities may use the soft opt-in for supporters (Data (Use and Access) Act 2025, s.114). B2B exception: corporate email addresses (e.g., info@company.com) may be contacted without prior consent under PECR, but UK GDPR still requires a lawful basis. |
| **Email Rules** | Same structural requirements as GDPR: sender identity, physical address, unsubscribe. ICO enforces. Unsolicited B2C email without consent is a PECR violation. |
| **Cookie/Tracking Rules** | PECR requires prior consent for non-essential cookies, with two exceptions since 5 Feb 2026 (Data (Use and Access) Act 2025, s.112 and Sch 12): cookies used **solely** to collect statistics about how your own service or website is used in order to improve it (shared only with someone helping make those improvements), and cookies that adapt or enhance the site's appearance or functionality. Both need clear and comprehensive information and a simple, free way to object. Advertising and cross-site tracking cookies still need consent, and legitimate interest is not a basis for them. |
| **Penalty Range** | UK GDPR: up to GBP 17.5 million or 4% of global turnover. PECR: since 5 Feb 2026 the same higher maximum applies to PECR breaches (s.115 and Sch 13, applying Data Protection Act 2018 s.157); before that, up to GBP 500,000. ICO enforcement. |
| **Verified** | 2026-10-27: PECR changes and dates against the Act's Schedules 12 and 13 and SI 2026/82 (legislation.gov.uk) |
| **Key Marketing Impact** | Post-Brexit, UK adequacy decision from the EU allows data flows, but this is subject to review. Data Protection Impact Assessments required for high-risk processing (profiling, large-scale marketing). ICO publishes direct marketing guidance — treat as binding. International transfers require UK-specific transfer mechanisms (UK SCCs, IDTA). |

### 1.8 Australia — Privacy Act + Spam Act

| Field | Detail |
|---|---|
| **Region** | Australia |
| **Law** | Privacy Act 1988 (Australian Privacy Principles) + Spam Act 2003 |
| **Year Enacted** | Privacy Act: 1988 (APPs added 2014). Spam Act: 2003. |
| **Consent Model** | Spam Act: express or inferred consent. ACMA says inferred consent needs a provable ongoing relationship and directly related marketing, and "does not cover sending messages after someone has just bought something". Privacy Act APP 7: direct marketing allowed if reasonably expected with a simple opt-out; otherwise consent is required (APP 7.3). |
| **Email Rules** | Identify the sender with contact details valid for 30 days. Unsubscribe must be free, need no login, work for 30 days, and be honoured within 5 working days (ACMA). Address-harvesting software and harvested lists are banned. Bought lists are legal, but the sender still needs consent (ACMA). |
| **Cookie/Tracking Rules** | No specific cookie consent law. The Privacy and Other Legislation Amendment Act 2024 (assented 10 Dec 2024) brought in: a statutory tort for serious invasions of privacy (from 10 June 2025); automated-decision disclosure in privacy policies (from 10 Dec 2026); and a Children's Online Privacy Code that must be registered by 10 Dec 2026. Tranche 2 has not been introduced (OAIC). |
| **Penalty Range** | Spam Act: ACMA (17 Oct 2024) gave court maximums of $626,000 a day without a prior record and $3,130,000 a day with one; they are set in penalty units, which have risen since, so current maximums are higher. Privacy Act: s.13G up to the greater of $50M, 3× the benefit, or 30% of turnover; s.13H up to 2,000 penalty units; infringement notices up to 200 units (OAIC). |
| **Key Marketing Impact** | Inferred consent is narrow, so get express consent. Keep consent records, since the sender must prove consent. Take reasonable steps before disclosing data overseas (APP 8.1). Individuals can now sue for serious privacy invasions. |
| **Verified** | 2026-10-27: every row against OAIC and ACMA pages; the Spam Act's penalty units were not read in the statute (legislation.gov.au timed out), so the row quotes ACMA's dated figures |

### 1.9 Singapore — PDPA

| Field | Detail |
|---|---|
| **Region** | Singapore |
| **Law** | Personal Data Protection Act (PDPA) |
| **Year Enacted** | 2012 (significant amendments 2021) |
| **Consent Model** | Express opt-in consent expected for direct marketing; deemed consent by notification, legitimate interests and business improvement cannot be used to send it (PDPC Key Concepts guidelines, rev. 29 Apr 2026). |
| **Email Rules** | DNC Registry check (or clear, recorded consent) before marketing calls, texts or faxes to Singapore numbers (PDPA s. 43). Bulk commercial email/SMS: unsubscribe facility honoured within 10 business days, "<ADV>" label, accurate subject and header, sender contact (Spam Control Act, Second Schedule). |
| **Cookie/Tracking Rules** | No specific cookie consent law. PDPA's consent obligation applies if cookies collect personal data. PDPC advisory guidelines recommend transparency and consent for tracking. |
| **Penalty Range** | Up to 10% of Singapore turnover for organisations above S$10m, otherwise S$1m (PDPA s. 48J, from 1 Oct 2022). DNC breaches: S$200k for individuals, S$1m for others. PDPC enforces. |
| **Key Marketing Impact** | Check the DNC Registry before marketing calls, texts or faxes to Singapore numbers. Notify the PDPC within 3 calendar days of assessing a breach as notifiable (s. 26D). Appoint a Data Protection Officer (s. 11(3)). Consent withdrawal must be easy. Cross-border transfers require comparable protection (s. 26). |
| **Verified** | 2026-10-27: every row against the PDPA and Spam Control Act on sso.agc.gov.sg (current version as at 27 Oct 2026) and PDPC guidelines |

### 1.10 China — PIPL

| Field | Detail |
|---|---|
| **Region** | People's Republic of China |
| **Law** | Personal Information Protection Law (PIPL) |
| **Year Enacted** | 2021 (effective November 1, 2021) |
| **Consent Model** | Opt-in. Separate consent required for: sensitive personal information, cross-border transfers, public disclosure, and processing by third parties. Consent must be informed, voluntary, and explicit. |
| **Email Rules** | Commercial email needs prior express consent and "广告" or "AD" at the front of the subject; stop on refusal; opt-out contact valid 30 days (MII Order No. 38, 2006, Arts. 13–14; gov.cn). Electronic ads need consent, the sender's real identity and a refusal method; fine RMB 5,000–30,000 (Advertising Law Arts. 43, 63). Commercial SMS needs proof of consent and an opt-out in every message (MIIT SMS Rules, revised by Order 74, in force 1 May 2026). |
| **Cookie/Tracking Rules** | No cookie statute; consent rules apply. Automated push or marketing must offer a non-personalised option or an easy refusal (PIPL Art. 24). Platforms must provide a personalised-recommendation off switch and tag deletion (Network Data Security Management Regulations Art. 42, from 1 Jan 2025). |
| **Penalty Range** | Up to RMB 50 million or 5% of prior year's revenue; responsible individuals up to RMB 1 million and a ban from serving as directors or officers (PIPL Art. 66). The CAC coordinates; other State Council departments enforce within their remits (Art. 60). |
| **Key Marketing Impact** | Mandatory in-China storage applies only to critical information infrastructure operators and handlers above CAC volume thresholds (PIPL Art. 40). Transfers needed for a contract with the person, or of under 100k people's non-sensitive data a year, are exempt; 100k–1m (or under 10k sensitive): standard contract or certification; above that: security assessment (CAC Order 16, 22 Mar 2024; certification under CAC/SAMR Order 20, from 1 Jan 2026). Impact assessments required (Art. 55). Overseas handlers need a China agency or representative (Art. 53). Handlers of 1m+ people must name a protection officer; 10m+ must audit every 2 years (CAC Order 18, from 1 May 2025). |
| **Verified** | 2026-10-27: every row against the PIPL on cac.gov.cn and the CAC/MIIT orders cited |

### 1.11 India — DPDPA

| Field | Detail |
|---|---|
| **Region** | India |
| **Law** | Digital Personal Data Protection Act (DPDPA) 2023, operationalised by the Digital Personal Data Protection Rules 2025: notification G.S.R. 846(E) dated 13 Nov 2025 (PIB reports notification on 14 Nov). The 3 Jan 2025 text (G.S.R. 02(E)) was the consultation draft. |
| **Year Enacted** | Act 2023. The Rules phase in (rule 1): rules 1, 2 and 17-21 (definitions and the Data Protection Board) from publication in Nov 2025; **rule 4 (Consent Manager registration) one year later, from 13 Nov 2026**; rules 3, 5-16, 22 and 23 (notice, security safeguards, breach notification, children's verifiable consent, rights, retention, cross-border and research rules) eighteen months later, **from 13 May 2027**. Build to the full rules now; most obligations are enforceable only from May 2027. |
| **Consent Model** | Opt-in. Consent must be free, specific, informed, unconditional, and unambiguous, and must be requested in clear, plain language. Notice must accompany or precede the consent request (Rule 3). "Deemed consent" was removed in the 2023 Act and replaced with "Certain Legitimate Uses" (Section 7) — narrower than the 2022 draft. |
| **Email Rules** | Marketing requires verifiable consent. Withdrawal must be as easy as giving consent. Consent Managers (registered entities that let a Data Principal give, manage, review or withdraw consent on one platform) can register from 13 Nov 2026 under rule 4 and must be companies incorporated in India; integrate with one once registered managers exist. Data Principals' access, correction and erasure requests must be answered within 90 days. |
| **Cookie/Tracking Rules** | Cookie / SDK-based tracking that identifies a Data Principal is processing of personal data and requires DPDPA-compliant consent. The Rules do not carve out cookies; rely on the general processing-with-consent obligation. EU-style banner UX is the safest pattern. |
| **Penalty Range** | Up to INR 250 crore for failing to keep reasonable security safeguards; up to INR 200 crore for failing to notify a breach or for violating obligations on children's data; up to INR 50 crore for any other violation of the Act or Rules (PIB, 17 Nov 2025). No percentage-of-revenue calculation. The Data Protection Board of India (four members, fully digital; rules 17-21, in force from Nov 2025) enforces and adjudicates; appeals go to TDSAT. |
| **Key Marketing Impact** | Children's data (under 18) requires verifiable parental consent (rule 10, from 13 May 2027), and the Act prohibits targeted advertising and behavioural tracking directed at children — design age-gating and parental-consent flows before launching India campaigns to under-18 audiences. Cross-border transfers are permitted by default; Government may notify restricted countries by gazette (none broadly restricted as of July 2026 — verify before launch). Significant Data Fiduciaries (designated by the Government based on volume / sensitivity / risk) carry additional obligations: appoint an India-resident Data Protection Officer, conduct annual Data Protection Impact Assessments, and undergo periodic audits. Breach notification to the Board and affected Data Principals is mandatory without delay (rule 7, from 13 May 2027). |
| **Verified** | 2026-10-27: notification, commencement (rule 1) and rules 4 and 10 against the Rules text on meity.gov.in; penalties against PIB (17 Nov 2025) |

### 1.12 Japan — APPI

| Field | Detail |
|---|---|
| **Region** | Japan |
| **Law** | Act on the Protection of Personal Information (APPI) |
| **Year Enacted** | 2003 (Act No. 57); the 2020 amendment fully in force 1 Apr 2022; Act No. 56 of 2026 (promulgated 17 Jul 2026) comes into force within two years, on a date not yet set (PPC). |
| **Consent Model** | Opt-in for provision to third parties and for use beyond the stated purpose. Opt-out third-party provision is available only after a filing with the PPC, and never for sensitive data (APPI Art. 27(2)). Cross-border transfer needs consent unless an exception applies (Art. 28). |
| **Email Rules** | Specified Electronic Mail Act: opt-in (exceptions: business relationship, address given to sender, published business address); keep consent records; honour opt-outs; show sender name and an opt-out address (Arts. 3–4). Corporations up to JPY 30m (Art. 37). |
| **Cookie/Tracking Rules** | Providing cookie-linked "personally referable information" that the recipient will tie to a person: the provider must confirm the recipient got the person's consent (APPI Art. 31). Sites and apps covered by the Telecommunications Business Act must notify or publish (or get consent / offer opt-out) what tags send, to whom and why (MIC, from 16 Jun 2023). The 2026 amendment bans improper use or acquisition of data carrying Cookie IDs and other contact identifiers (Art. 31-2, not yet in force). |
| **Penalty Range** | Criminal: breaching a PPC order, up to 1 year or JPY 1m; corporations up to JPY 100m (APPI Arts. 178, 184). Act No. 56 of 2026 adds a surcharge equal to the gain from serious violations, aimed at large cases (1,000-person benchmark); in force within 2 years (PPC). |
| **Key Marketing Impact** | Japan has an EU adequacy decision (mutual), facilitating EU-Japan data flows. Pseudonymized data has a specific legal regime — can be used for internal analytics without consent but cannot be provided to third parties. Breach notification to PPC and affected individuals is mandatory. "Individually referable information" concept means cookie syncing and DMP practices need consent. |
| **Verified** | 2026-10-27: every row against the APPI (Japanese Law Translation), e-Gov, MIC and PPC pages; re-check when the cabinet order sets the 2026 amendment's in-force date |

### 1.13 South Korea — PIPA

| Field | Detail |
|---|---|
| **Region** | South Korea |
| **Law** | Personal Information Protection Act (PIPA) |
| **Year Enacted** | 2011; major amendments in force 15 Sep 2023 and 11 Sep 2026 (Act No. 21445) (law.go.kr; PIPC) |
| **Consent Model** | Each consent item must be presented and obtained separately, marketing included; service cannot be refused for declining marketing consent (PIPA Art. 22). Cross-border transfer: separate consent, or law/treaty, contract necessity with disclosure, certification, or PIPC adequacy (Art. 28-8). |
| **Email Rules** | ICNA Art. 50: explicit prior opt-in (exception: own customers, same kind of goods, within 6 months of the transaction ending). Separate consent for 21:00–08:00, except email (Decree Art. 61). "(광고)" at the start of the subject line; sender name and contact; opt-out instructions in Korean and English (Decree Annex 6). Stop on refusal; confirm the outcome within 14 days; re-confirm consent every 2 years (Decree Arts. 62-2, 62-3). |
| **Cookie/Tracking Rules** | No cookie statute. PIPC policy (31 Jan 2024): behavioural data processed so no one can be identified needs no consent; identifying processing needs notice, consent and a later opt-out; ad media must list third-party collection in their privacy policy. |
| **Penalty Range** | Up to 3% of total revenue (KRW 2bn if revenue can't be calculated); up to 10% (KRW 5bn) for repeat intentional or grossly negligent violations within 3 years, intentional or grossly negligent harm to 10m+ people, or a leak after ignoring a corrective order. Revenue unrelated to the violation is excluded (PIPA Art. 64-2, in force 11 Sep 2026). Criminal: up to 10 years / KRW 100m (Art. 70). PIPC enforces. |
| **Key Marketing Impact** | Very granular consent: a separate item for each purpose and recipient (Art. 22). Night-time advertising messages need separate consent, except email, so code send-time rules per channel. Resident Registration Numbers are highly restricted. Cross-border transfer grounds were widened (Art. 28-8), and PIPC can order a transfer stopped (Art. 28-9). |
| **Verified** | 2026-10-27: every row against PIPA and the ICNA on law.go.kr (in force 2026-09-11) and PIPC pages |

### 1.14 Saudi Arabia — PDPL

| Field | Detail |
|---|---|
| **Region** | Kingdom of Saudi Arabia |
| **Law** | Personal Data Protection Law (PDPL) |
| **Year Enacted** | 2021 (Royal Decree M/19, 16 Sep 2021; amended by M/148, 2023). SDAIA's Implementing Regulation and Transfer Regulation (v2.0, Aug 2024). Grace period reported to have ended 14 Sep 2024 (law firms). Draft amendments to the Implementing Regulation consulted 6 Oct–5 Nov 2026 (Clyde & Co; not adopted). |
| **Consent Model** | Consent is the default basis (PDPL Art 5), with exceptions including the controller's legitimate interests, never for sensitive data (Art 6(4)). Consent must be free, documented and given separately for each purpose; withdrawing it must be as easy as giving it (Implementing Regulation Arts 11–12). Explicit consent is needed for sensitive data, credit data and fully automated decisions (Art 11(2)). Sensitive data = ethnic origin, religious or political belief, criminal or security data, biometric, genetic and health data, unknown parentage (PDPL Art 1). |
| **Email Rules** | Advertising sent to postal or email addresses needs the recipient's consent and an opt-out (PDPL Art 25). Under Implementing Regulation Art 28, consent is required where there is no prior dealing with the recipient; the sender must be named, and opt-out must be free, as easy as opting in, and acted on at once. Direct marketing needs consent plus opt-out (Art 29). Marketing may use only data collected directly from the person, never sensitive data (PDPL Art 26). |
| **Cookie/Tracking Rules** | The general consent rule applies to personal data collected through cookies. Neither the PDPL nor its regulations has a cookie-specific rule. |
| **Penalty Range** | Warning or fine up to SAR 5M per violation, doubled for repeat violations (PDPL Art 36), imposed by SDAIA committees and appealable to court. Unlawfully disclosing sensitive data with intent to harm or for gain: up to 2 years and/or SAR 3M (Art 35, prosecuted by the Public Prosecution). SDAIA is the competent authority; SAMA keeps its own powers (Art 30). |
| **Key Marketing Impact** | There is no localisation rule in force. Transfers abroad are allowed to countries on SDAIA's adequacy list, or under standard contractual clauses, binding common rules or an accreditation certificate, with a transfer risk assessment in set cases (Transfer Regulation Arts 3, 4, 7). Watch: the Oct 2026 draft would require storage in the Kingdom and notices in the language used to serve customers. DPO needed for public bodies processing at large scale, systematic monitoring, or sensitive data as a core activity (Art 32). Notify SDAIA of a breach within 72 hours where harm is likely (Art 24). |
| **Verified** | 2026-10-27: every row against the PDPL, its Implementing Regulation and the Transfer Regulation (v2.0, Aug 2024) on SDAIA's platform; the end of the grace period and the Oct 2026 draft come from law firms (Clyde & Co, 8 Oct 2026) |

### 1.15 UAE — Federal Decree-Law No. 45

| Field | Detail |
|---|---|
| **Region** | United Arab Emirates, federal. Outside the law (Art 2): free zones with their own data protection law (e.g. DIFC, ADGM), government data, and health and banking data covered by their own laws. |
| **Law** | Federal Decree-Law No. 45 of 2021 on the Protection of Personal Data |
| **Year Enacted** | 2021 (issued 20 Sep 2021; in force 2 Jan 2022). No Executive Regulation is listed on uaelegislation.gov.ae as of 26 Oct 2026. Firms get six months from its issue to comply (Art 29). |
| **Consent Model** | Consent is required unless an Article 4 exception applies: public interest, data the subject made public, legal claims, health care, public health, research, the subject's interests, employment duties, contract, legal obligation. There is no legitimate-interest basis. Consent must be provable, clear, unambiguous and withdrawable (Art 6). |
| **Email Rules** | Marketing needs consent or another Article 4 ground; there is no legitimate-interest route. People may object to and stop direct marketing, including related profiling (Art 17). Free-zone entities with their own data law (e.g. DIFC, ADGM) are outside the federal law (Art 2). |
| **Cookie/Tracking Rules** | The general consent rule (Arts 4 and 6) covers personal data collected through cookies and tracking. There is no cookie-specific rule, and the Executive Regulation that could add detail has not been issued. |
| **Penalty Range** | The Decree-Law sets no fine amounts; a Cabinet decision is to set violations and penalties (Art 26), and none is listed on the official portal. Regulator: UAE Data Office (Decree-Law 44/2021). DIFC and ADGM have separate penalty regimes. |
| **Key Marketing Impact** | Three regimes: the federal Decree-Law, DIFC's own data protection law and ADGM's own regulations; which applies depends on where the entity is registered. Transfers abroad go to countries with adequate protection or under the other routes in Arts 22–23; the consent route needs explicit consent. Until the Executive Regulation and the Cabinet penalty decision are issued, build to the Decree-Law itself and check the official portal before quoting a penalty. |
| **Verified** | 2026-10-27: every row against Decree-Law 45/2021 on uaelegislation.gov.ae (portal updated 26 Oct 2026) and the u.ae data protection page (updated 4 Dec 2025); the DIFC and ADGM regimes were not re-read |

### 1.16 Thailand — PDPA

| Field | Detail |
|---|---|
| **Region** | Thailand |
| **Law** | Personal Data Protection Act (PDPA) |
| **Year Enacted** | 2019 (Government Gazette, 27 May 2019). Full enforcement from 1 June 2022 after two postponements (UNVERIFIED: the postponement decrees were not on the PDPC decree page, and the Royal Gazette site refused the request on 2026-10-27). |
| **Consent Model** | Opt-in. Consent must be freely given, specific, informed, and unambiguous. Legitimate interest available as an alternative basis. Explicit consent required for sensitive data. Consent must be as easy to withdraw as to give. |
| **Email Rules** | The PDPA has no rule specific to marketing channels. Marketing needs a lawful basis (consent, or legitimate interest under s.24(5)), and people may object to direct marketing at any time (s.32(2)). |
| **Cookie/Tracking Rules** | The PDPA has no cookie-specific rule: cookies that collect personal data need a lawful basis like any other processing (s.24), and consent for advertising cookies is common practice. UNVERIFIED: the PDPC's guideline list (checked 2026-10-27) has no cookie guideline, so do not cite one. |
| **Penalty Range** | Administrative fines up to THB 1M, 3M or 5M (ss.82–90). Up to 1 year and/or THB 1M for misusing sensitive data for unlawful gain (s.79). Punitive damages up to twice actual compensation (s.78). Expert committees had issued 9 fine orders in 6 cases, totalling over THB 21.5M, by 1 Aug 2025; the largest was THB 7M against a retailer with no adequate security, no breach report and no DPO (PDPC). |
| **Key Marketing Impact** | Structure is close to the GDPR. A DPO is required for certain controllers (s.41). Notify the PDPC of a breach within 72 hours where feasible (s.37(4)). Transfers abroad need adequate protection in the destination or an exception (s.28). Keep a record of processing (s.39). |
| **Verified** | 2026-10-27: every row against the official English translation of the PDPA and PDPC pages on pdpc.or.th (press release of 1 Aug 2025); the 2022 enforcement date and the cookie practice are marked UNVERIFIED |

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
| **Regulation** | COPPA (Children's Online Privacy Protection Act, 1998; updated rule 2013; amended rule finalized January 2025); FTC Act; State laws (e.g., California Age-Appropriate Design Code) |
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
| **Penalty** | Civil penalties per violation, inflation-adjusted annually (~$53K+ as of 2026). Applies to businesses, review brokers, and platforms that knowingly facilitate fake reviews. |

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
| **Section 5 (Unfair or Deceptive Acts)** | Consent orders, cease and desist, corrective advertising. No direct fines for first-time Section 5 violations, but violation of a consent order: civil penalties per violation, inflation-adjusted annually (~$53K+ as of 2026). |
| **Penalty Offense Authority** | FTC can seek civil penalties from companies that had prior notice that conduct is unlawful (via prior FTC cases). Per-violation civil penalty, inflation-adjusted annually (~$53K+ as of 2026). |
| **Fake Reviews Rule (2024)** | Civil penalties per violation, inflation-adjusted annually (~$53K+ as of 2026). |
| **COPPA Violations** | Per-violation civil penalty, inflation-adjusted annually (~$53K+ as of 2026). |
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
| **Special Ad Categories** | Credit, Employment, Housing, Social Issues/Elections/Politics. These categories have restricted targeting: no age, gender, zip code, or interest-based exclusions. Must declare category before ad creation. Lookalike audiences unavailable; Special Ad Audiences were discontinued (2023) — use broad targeting within the allowed constraints. |
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

### 5.1 WCAG 2.2 AA — Marketing Content Requirements

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
| **Legal Basis** | Title III of the Americans with Disabilities Act. DOJ has confirmed that websites of public accommodations must be accessible. No specific technical standard is codified, but courts consistently reference WCAG 2.2 AA as the benchmark. |
| **Who Is Covered** | Any business that is a "place of public accommodation" (virtually all commercial websites, including e-commerce, SaaS, services, media). |
| **Enforcement** | Private lawsuits (ADA Title III does not provide damages in federal court but does in some states, notably California's Unruh Act: $4,000 minimum per violation per visit). DOJ enforcement actions. Demand letters are common. |
| **Marketing Implications** | All landing pages, microsites, campaign pages, and promotional web content must be WCAG 2.2 AA compliant. Pop-ups and modals must be keyboard-accessible and screen-reader-compatible. Video content needs captions. PDFs (whitepapers, ebooks) must be tagged for accessibility. Forms must have labels, error handling, and keyboard access. |
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
5. **Accessibility** — Apply WCAG 2.2 AA and email accessibility standards to all outputs

When rules conflict, apply the **most restrictive** standard. When jurisdiction is unknown, default to **GDPR + CPRA + FTC** as the baseline.

### Severity Levels

| Level | Definition | Action |
|---|---|---|
| **BLOCK** | Violation would be illegal or result in platform ban (false health claims, missing disclosures on regulated products, COPPA violations, discriminatory targeting). | Do not output. Flag to user with specific rule citation. |
| **WARN** | Likely violation requiring human review (ambiguous claims, missing disclaimers, potential trademark issues, accessibility gaps). | Output with prominent warning and recommended fix. |
| **SUGGEST** | Best practice not strictly required by law but reduces risk (double opt-in where only opt-out required, adding disclaimers proactively, exceeding minimum contrast ratios). | Output with suggestion as a footnote. |
