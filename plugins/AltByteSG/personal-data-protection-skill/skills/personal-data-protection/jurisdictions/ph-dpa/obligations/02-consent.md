# Consent and Lawful Bases — §§ 3(b), 12, 13 RA 10173 + §§ 19, 21–22 IRR

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

PH has a GDPR-shaped lawful-basis framework: **six bases for personal information** under § 12 (consent, contract, legal obligation, vital interests, public order / national emergency, legitimate interests) and a **narrower set of bases for sensitive personal information** under § 13. Consent is one option among several — engineering should pick the basis that fits the processing, not default to consent reflexively.

## § 3(b) — Definition of consent

**Rule (verbatim):** *"'Consent of the data subject' refers to any freely given, specific, informed indication of will, whereby the data subject agrees to the collection and processing of personal information about and/or relating to him or her. Consent shall be evidenced by written, electronic or recorded means. It may also be given on behalf of the data subject by an agent specifically authorized by the data subject to do so."*

**Practical effect:** consent is **freely given, specific, informed, and evidenced**. Pre-ticked checkboxes, bundled "I agree to everything" without granularity, and silence-as-consent all fail the definition. The consent must be **recorded** — your evidence trail is what supports the basis.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md) (signup flow), [03 Data model](../../../layers/03-data-model.md) (consent records).

**Operationalisation:**
- Consent UI: an explicit user act (checkbox, button) bound to a specific, named purpose. "I agree to receive marketing emails" is specific; "I agree to the privacy policy" is the catch-all under § 12(a) that should be reserved for the bundled-purpose case.
- Persist a consent record per data subject per purpose: `user_id`, `purpose_code`, `granted_at`, `notice_version_hash`, `client_ip`, `user_agent`. This is the evidence under any NPC inspection.
- "Specifically authorized agent": parents consenting on behalf of minors, attorneys-in-fact under a recorded SPA, etc. Build the agent-attribution into the consent record schema if your product touches minors or assisted users.
- Withdrawal must be as easy as the original grant — see § 16(b) right to object in [04-access-correction.md](04-access-correction.md).

## § 12 — Lawful bases for processing personal information (non-SPI)

**Rule (verbatim):** *"The processing of personal information shall be permitted only if not otherwise prohibited by law, and when at least one of the following conditions exists:"*

| Basis | Citation | Engineering case |
|---|---|---|
| Consent | § 12(a) | The data subject has granted a specific, informed, evidenced consent. Default for marketing, optional analytics, profile-enrichment features. |
| Contract performance | § 12(b) | Necessary to fulfil a contract with the data subject, or to take steps before entering one. Covers account creation, payment processing, service delivery. |
| Legal obligation | § 12(c) | Required by law — tax record retention, AML / KYC, sectoral regulator demands. |
| Vital interests | § 12(d) | Necessary to protect the data subject's life and health — narrow, mostly emergency cases. |
| Public order / national emergency | § 12(e) | Response to a national emergency, public order and safety, or to fulfil functions of public authority. Rarely applies to private commercial apps. |
| **Legitimate interests** | § 12(f) | Necessary for the legitimate interests of the PIC or a third party — **subject to a balancing test** against the data subject's fundamental rights and freedoms. Genuinely usable for fraud detection, security monitoring, internal analytics where consent isn't workable. |

**Practical effect:** unlike SG/MY which restrict alternatives to a narrower enumerated list, **§ 12(f) legitimate interests is a real engineering option**. It requires a documented balancing test and cannot be used where the processing would harm the data subject's rights. Common engineering uses: fraud detection, abuse / spam prevention, security log analysis, internal product analytics on aggregated / pseudonymised data.

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md) (label each processing purpose with its lawful basis), [06 Disclosure](../../../layers/06-disclosure.md) (privacy notice).

**Operationalisation:**
- Privacy notice should label each processing purpose with its lawful basis. This makes withdrawal logic clean — withdrawing consent doesn't stop contract-necessity processing or legitimate-interests processing.
- For a § 12(f) legitimate-interests basis, keep a written balancing test on file. NPC inspections may ask to see it. Template: (1) what is the legitimate interest, (2) is the processing necessary to achieve it, (3) does it override the data subject's rights.
- Tax / AML retention overrides any "purpose ended, delete" pressure under § 11 — keep the legal-obligation basis documented per retention rule.

## § 13 — Lawful bases for sensitive personal information

**Rule (summary):** processing of SPI is **prohibited except** in one of these cases:

| Basis | Citation | Engineering case |
|---|---|---|
| Consent specific to the purpose | § 13(a) | Data subject has given consent specific to the SPI processing — the realistic basis for most consumer apps that touch SPI categories. |
| Existing law / regulation | § 13(b) | Permitted by existing laws and regulations, with conditions. |
| To protect life and health | § 13(c) | Necessary to protect the life and health of the data subject or another person, where the data subject is not legally / physically able to consent. |
| Lawful and noncommercial objectives of public organisations | § 13(d) | Foundations, associations, or non-stock non-profit organisations operating for public-interest purposes — narrow. |
| Medical treatment | § 13(e) | Necessary for medical treatment, carried out by a medical practitioner / institution under appropriate confidentiality. |
| Legal claims | § 13(f) | Necessary for the protection of lawful rights and interests of natural or legal persons in court proceedings, or the establishment, exercise, or defense of legal claims. |

**Practical effect:** for almost all consumer apps that touch SPI, **explicit consent specific to the SPI category is the realistic basis**. The other bases are narrow (medical professionals, court proceedings, etc.).

**SPI categories (§ 3(l)) — what triggers § 13:**
- Race, ethnic origin, marital status, age, colour, religious / philosophical / political affiliations
- **Health, education, genetic, sexual life, criminal proceedings**
- **Government-issued identifiers** — SSS, GSIS, TIN, PhilHealth, Philippine passport, driver's licence, Philippine national ID (PhilSys / PSN), and *any* number issued by a government office for personal identification
- Information classified as confidential by an executive order or act of Congress

**Practical effect of the government-identifier rule:** **storing a TIN, SSS, or PhilSys number is SPI processing in PH**. This is broader than SG/MY/TH/ID and is one of the most common compliance traps for cross-jurisdiction apps. KYC flows for fintech, ride-hailing, gig-work platforms — all touch SPI in PH even if the same flow is plain PI elsewhere.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md), [03 Data model](../../../layers/03-data-model.md), [04 Controls and processes](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Discrete consent UI for any SPI collection — a separate dialog, not a bundle into the signup checkbox. The dialog must identify the SPI category and the purpose.
- Schema: tag every column that holds SPI (`is_spi: true` or per-column tags by category). Gate access at the database layer (RLS / row-level policy / column-level GRANT) so the default service role cannot read SPI without an explicit access path.
- **Audit-log every read** of an SPI column, not just writes. A staff member casually browsing PhilSys numbers is the textbook § 31 (malicious disclosure) and § 25(b) (unauthorised SPI processing) scenario — the audit trail is your evidence trail.
- If the application stores government identifiers, treat them like passwords: never log them in clear text, mask them in display ("•••-•••-1234"), and rotate / re-collect rather than allowing edit-in-place where possible.
- § 25(b) penalty — unauthorised SPI processing: 3 to 6 years prison + ₱500,000 to ₱4,000,000 per offence.
- § 26(b) penalty — negligent access to SPI: 3 to 6 years prison + ₱500,000 to ₱4,000,000.

## § 19 IRR — Definition and elements of valid consent (operational)

**Rule (summary):** the IRR confirms consent must be (a) freely given, (b) specific, (c) informed, and (d) evidenced by written, electronic, or recorded means. The PIC bears the burden of proof.

**Practical effect:** the **PIC bears the burden of proof** that consent is valid. The architectural implication is that consent records are not optional — without them, the PIC cannot defend the lawful basis, and the processing falls back to "no basis" → § 25 unauthorised processing.

**Operationalisation:**
- Consent record schema must capture: purpose, version of the notice / consent text, granular choice (per-purpose toggles, not one bundled flag), timestamp, identity binding (user ID), and channel evidence (form submission record / IP / user agent).
- Notice version hash: the consent record references the exact text the user saw, not just "the privacy policy" generally. When the privacy policy changes materially, re-consent.

## Consent withdrawal

PH does not have a single "right to withdraw consent" section equivalent to MY § 38; the right is built into:
- The general right to **object** (§ 16(b) — see [04-access-correction.md](04-access-correction.md)).
- The right to **erasure or blocking** (§ 16(e)) — discontinue further processing of personal information that is no longer necessary.
- The general principle of consent under § 3(b) — consent that can be granted can be withdrawn.

**Operationalisation:**
- Settings screen: a per-purpose toggle for every consent-based purpose. Withdrawal takes effect on the toggle event — log the change in the consent records table.
- Mutation paths: any code path processing consent-based data must check the live consent state. A single `consents` table joined on user ID is the clean implementation.
- Withdrawal of consent does **not** stop processing under contract necessity (§ 12(b)) or legal obligation (§ 12(c)). Make this clear in the UX so the user understands what stops and what continues.
- NPC Circular 2022-04 sets the **15-day default** for acting on a data subject request — the withdrawal must take effect within that window (immediately for digital toggles; up to 15 days where downstream pipelines need to flush).

## What's at stake

- **§ 25(a) — unauthorised processing of PI**: 1 to 3 years + ₱500k–₱2M per offence.
- **§ 25(b) — unauthorised processing of SPI**: 3 to 6 years + ₱500k–₱4M per offence.
- **§ 28 — processing for unauthorised purposes**: 1.5 to 7 years + up to ₱2M per offence.
- **§ 33 — combination or series of the above acts**: 3 to 6 years + ₱1M–₱5M.
- **§ 34 — officer liability**: where the corporate offence engages, the responsible officers face the prison terms personally.
- **§ 35 — large-scale aggravation**: where PI / SPI of at least 100 persons are harmed, the penalty is imposed in its maximum period.

The consent record is the single most valuable artefact in any NPC complaint or inspection. Build the consent records table and the audit trail early; trust them.
