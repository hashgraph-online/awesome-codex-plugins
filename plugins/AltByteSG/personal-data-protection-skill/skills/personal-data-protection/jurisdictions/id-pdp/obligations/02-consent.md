# Pasal 4, 20–26 — Lawful Bases, Consent, Sensitive Data, Special Subjects

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

## Pasal 4 — Specific (sensitive) vs general Personal Data

**Rule:** Personal Data is split into two categories:

a. **"Specific" Personal Data** (Data Pribadi yang bersifat spesifik) — sensitive categories warranting heightened protection
b. **"General" Personal Data** (Data Pribadi yang bersifat umum)

The Act itself is brief on what falls into "specific" — the implementing Government Regulation (PP) provides the detailed list. Based on Indonesian privacy practice and the structure of Pasal 4, "specific" Personal Data typically includes:
- Health and biometric data
- Genetic data
- Criminal records
- Children's data
- Personal financial data
- Other categories defined by PP

**Verify the current PP text at [peraturan.go.id](https://peraturan.go.id) for the binding scope.**

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md) (sensitive-data flagging), [05 Feature/UX](../../../layers/05-feature-ux.md) (separate explicit-consent UX).

**Operationalisation:** audit your data inventory for "specific" categories. Specific data triggers stricter handling at multiple points: Pasal 34 mandatory DPIA; Pasal 53 DPO designation if it's the core activity; heightened administrative scrutiny.

## Pasal 20 — Lawful bases (6 GDPR-style)

**Rule:** the Controller must have a lawful basis for each processing activity. Six bases (Pasal 20(2)):

| # | Basis | Notes |
|---|---|---|
| (a) | **Explicit consent** | For one or more specific notified purposes |
| (b) | **Contractual necessity** | Performance of a contract to which the Subject is party, or pre-contractual steps at Subject's request |
| (c) | **Legal obligation** | Compliance with law applicable to the Controller |
| (d) | **Vital interests** | Protection of vital interests of the Data Subject |
| (e) | **Public-interest task / official authority** | Performance of public-interest task or exercise of authority |
| (f) | **Legitimate interests** | Considering purposes, needs, and balance between Controller's interests and Subject's rights |

**Compared to Thailand and Singapore:**
- Indonesia and Thailand both use 6 GDPR-style bases — closely parallel
- Singapore PDPA is structurally different (consent + enumerated 1st/2nd Schedule cases)
- The "(f) legitimate interests" balancing test should be documented (LIA-style assessment) before reliance

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md) (privacy policy purposes table), [05 Feature/UX](../../../layers/05-feature-ux.md) (consent UX where consent is the basis).

## Pasal 21 — Information at consent (7 categories)

**Rule:** when processing is based on consent (Pasal 20(2)(a)), the Controller must inform the Subject of:

a. Legality of the processing (lawful basis)
b. Purpose of the processing
c. Type and relevance of Personal Data to be processed
d. Retention period of documents containing Personal Data
e. Details of the information collected
f. Processing duration
g. Rights of the Data Subject

If any of this information changes, the Controller must notify **before** the change takes effect (Pasal 21(2)).

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md), [05 Feature/UX](../../../layers/05-feature-ux.md) (consent screen content).

**Operationalisation:** the consent screen needs to surface all 7 items — typically as a combination of in-line disclosures + a linked privacy policy section. Pre-checked checkboxes are not consent (Pasal 22(5) effectively requires affirmative action).

## Pasal 22 — Consent form requirements

**Rule:** consent must be **written or recorded** (electronic or non-electronic, both have equal force). When the request includes other purposes, the consent request must:

a. Be **clearly distinguishable** from other matters
b. Be in **understandable and easily accessible format**
c. Use **simple and clear language**

**Critical:** consent failing any of these requirements is **null and void by law** (Pasal 22(5)) — no fallback, no cure.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md).

**Operationalisation:**
- Active opt-in only (no pre-checked boxes)
- Plain-language consent text
- Consent UX physically separate from T&C scrolling — typically a discrete checkbox + link to detailed disclosure
- Consent record stored with the format / language used (audit-ready)

## Pasal 23 — Null contractual clauses

**Rule:** any contractual clause that includes a request for Personal Data processing **without explicit valid consent** from the Data Subject is **null and void**.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md) (T&C drafting).

**Operationalisation:** T&C cannot smuggle in processing consent. Each processing purpose needs a real, distinguishable consent moment — not a "by using our service you agree" boilerplate.

## Pasal 24 — Demonstrate consent

**Rule:** the Controller must be able to **show evidence** of consent given by the Subject.

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md) (append-only consent record), [04 Controls](../../../layers/04-controls-and-processes.md) (consent log RPCs).

## Pasal 25 — Children's data consent

**Rule:** processing of children's Personal Data is conducted **specially** (secara khusus) — and requires **consent of the parent and/or guardian** as required by other laws.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md) (age gate + parental-consent flow).

The Act doesn't specify the age threshold — defers to other Indonesian law. Practical: most consumer apps gate at 16 or 17 to avoid the parental-consent flow entirely.

## Pasal 26 — Disability accommodations

**Rule:** processing of Personal Data of persons with disabilities is conducted **specially**, through **certain forms of communication** appropriate to the disability. Consent must be obtained from the disabled person and/or their guardian.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md) (accessibility, alternative consent channels).

This is unique to Indonesia among the populated jurisdictions. Operationalisation depends on the application context (screen reader compatibility, alternative formats, etc.).

## Penalty exposure (this Part)

| Failure | Source |
|---|---|
| Pasal 20(1) (no lawful basis), Pasal 21 (notification at consent), Pasal 24 (prove consent), Pasal 25(2) (parental consent for children) | Administrative sanctions per Pasal 57 — ceiling 2% revenue |
| Sensitive ("specific") data violations | No separate criminal tier in UU PDP (unlike Thailand) — but heightened administrative scrutiny + corporate criminal liability under Pasal 70 |
| Unlawful obtaining or disclosure for self/another's benefit | Criminal — Pasal 67 — see [07-offences.md](07-offences.md) |

See [07-offences.md](07-offences.md) for the full penalty matrix.
