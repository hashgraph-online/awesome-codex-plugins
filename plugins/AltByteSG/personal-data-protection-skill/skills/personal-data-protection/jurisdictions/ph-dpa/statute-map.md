# Philippines DPA — Statute ↔ Layer Cross-Reference

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Reverse lookup. Use when citing a section in a PR description, audit response, or breach notification. For day-to-day work, use the layer files and obligation files instead.

References use the section numbering of RA 10173 (Data Privacy Act of 2012), the 2016 NPC Implementing Rules and Regulations (IRR), and the operative NPC Circulars.

## RA 10173 — Substantive provisions

| Section | Topic | Obligation file | Layer |
|---|---|---|---|
| § 3(b) | Definition of "consent of the data subject" — freely given, specific, informed indication of will | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md), [03](../../layers/03-data-model.md) |
| § 3(g) | Definition of "personal information" (PI) | — | [03](../../layers/03-data-model.md) |
| § 3(h) | Definition of "personal information controller" (PIC) | — | [01](../../layers/01-non-technical.md), [02](../../layers/02-architecture.md) |
| § 3(i) | Definition of "personal information processor" (PIP) | — | [01](../../layers/01-non-technical.md), [02](../../layers/02-architecture.md) |
| § 3(l) | Definition of "sensitive personal information" (SPI) — race, ethnic origin, marital status, age, colour, religious / philosophical / political affiliations; health, education, genetic, sexual life, criminal proceedings; government identifiers (SSS, GSIS, TIN, PhilHealth, etc.); other classified by law | [02-consent](obligations/02-consent.md) | [03](../../layers/03-data-model.md) |
| § 4 | Scope of the Act and statutory exclusions | — | — |
| § 6 | Extraterritorial application — link to the Philippines / personal information about Philippine citizens or residents | — | [02](../../layers/02-architecture.md) |
| § 11 | General data privacy principles — transparency, legitimate purpose, proportionality | [03-purpose](obligations/03-purpose.md) | [05](../../layers/05-feature-ux.md), [06](../../layers/06-disclosure.md) |
| **§ 12** | **Lawful bases for processing personal information** — six bases including consent, contract, legal obligation, vital interests, public order / national emergency, legitimate interests | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md), [03](../../layers/03-data-model.md) |
| **§ 13** | **Lawful bases for processing sensitive personal information** — narrower than § 12; explicit consent default | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md), [03](../../layers/03-data-model.md) |
| § 14 | Subcontracting — PIC remains responsible for personal information subcontracted to a PIP | [01-accountability](obligations/01-accountability.md), [05-care](obligations/05-care.md) | [01](../../layers/01-non-technical.md) |
| § 15 | Extension of privileged communication — applies to attorney–client, doctor–patient, etc. | — | — |
| **§ 16** | **Rights of the data subject** — informed, access, object, rectification, erasure / blocking, damages, complaint (and data portability via NPC Circular 18-01) | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md), [05](../../layers/05-feature-ux.md) |
| § 17 | Transmissibility of rights of the data subject (heirs / assigns) | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md) |
| § 18 | Right to data portability (heading; details by NPC Circular 18-01) | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md), [05](../../layers/05-feature-ux.md) |
| § 19 | Non-applicability of certain rights — research, journalism, court orders | [04-access-correction](obligations/04-access-correction.md) | — |
| **§ 20** | **Security of personal information** — organisational, physical, technical safeguards; appropriate level of protection | [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md), [04](../../layers/04-controls-and-processes.md) |
| § 20(c) | The PIC's third-party service provider safeguards — contractual obligations | [01-accountability](obligations/01-accountability.md), [05-care](obligations/05-care.md) | [01](../../layers/01-non-technical.md) |
| § 20(f) | Notification of personal data breach to the Commission and to the data subjects within 72 hours (operationalised by NPC Circular 16-03) | [06-breach-notification](obligations/06-breach-notification.md) | [07](../../layers/07-operational.md) |
| **§ 21** | **Cross-border / accountability** — PIC remains accountable for personal information transferred to a third party for processing, in or outside the Philippines | [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md), [01](../../layers/01-non-technical.md) |
| § 22 | Accountability for transfer of personal information — designated personnel accountable for compliance | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |

## RA 10173 — Offences (Chapter VIII, §§ 25–37)

| Section | Offence | Penalty | Obligation file |
|---|---|---|---|
| § 25(a) | Unauthorised processing of personal information | 1–3 years + ₱500k–₱2M | [07-offences](obligations/07-offences.md) |
| § 25(b) | Unauthorised processing of sensitive personal information | 3–6 years + ₱500k–₱4M | [07-offences](obligations/07-offences.md) |
| § 26(a) | Accessing personal information due to negligence | 1–3 years + ₱500k–₱2M | [07-offences](obligations/07-offences.md) |
| § 26(b) | Accessing sensitive personal information due to negligence | 3–6 years + ₱500k–₱4M | [07-offences](obligations/07-offences.md) |
| § 27 | Improper disposal of personal information / SPI | 6m–3y + ₱100k–₱1M | [07-offences](obligations/07-offences.md) |
| § 28 | Processing of personal information for unauthorised purposes | 1y6m–7y + up to ₱2M | [07-offences](obligations/07-offences.md) |
| § 29 | Unauthorised access or intentional breach | 1–3 years + ₱500k–₱2M | [07-offences](obligations/07-offences.md) |
| **§ 30** | **Concealment of security breaches involving sensitive personal information** | 1y6m–5y + ₱500k–₱1M | [06-breach-notification](obligations/06-breach-notification.md), [07-offences](obligations/07-offences.md) |
| § 31 | Malicious disclosure | 1y6m–5y + ₱500k–₱1M | [07-offences](obligations/07-offences.md) |
| § 32 | Unauthorised disclosure | 1–5 years + ₱500k–₱2M | [07-offences](obligations/07-offences.md) |
| § 33 | Combination or series of acts | 3–6 years + ₱1M–₱5M | [07-offences](obligations/07-offences.md) |
| **§ 34** | **Extent of liability — responsible officers of juridical persons** | Personal liability for officers / employees who participated or by gross negligence allowed the act | [07-offences](obligations/07-offences.md) |
| § 35 | Large-scale processing — penalty in maximum period when PI / SPI of at least 100 persons is harmed | Aggravation of §§ 25–32 | [07-offences](obligations/07-offences.md) |
| § 36 | Offences committed by public officer | Prohibition from public office | [07-offences](obligations/07-offences.md) |
| § 37 | Restitution | Civil indemnity to victims | [07-offences](obligations/07-offences.md) |

## NPC Implementing Rules and Regulations (IRR), 2016

| Section | Topic | Obligation file | Layer |
|---|---|---|---|
| § 14 IRR | Designation of a Data Protection Officer (paperwork — see README "What's intentionally not covered") | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |
| § 18 IRR | General data privacy principles operationalised | [03-purpose](obligations/03-purpose.md) | [05](../../layers/05-feature-ux.md), [06](../../layers/06-disclosure.md) |
| § 19 IRR | Definition and elements of valid consent | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md) |
| § 21 IRR | Lawful bases for processing PI (mirrors § 12 RA 10173) | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md) |
| § 22 IRR | Lawful bases for processing SPI (mirrors § 13 RA 10173) | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md) |
| §§ 25–29 IRR | Data subject rights — operational detail | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md), [05](../../layers/05-feature-ux.md) |
| §§ 25–29 IRR (security part) | Security measures — organisational, physical, technical | [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md), [04](../../layers/04-controls-and-processes.md) |
| § 34 IRR | Rights of the data subject — operational mechanics | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md) |
| **§ 38 IRR** | **Personal data breach notification** — 72-hour clock + content + recipients | [06-breach-notification](obligations/06-breach-notification.md) | [07](../../layers/07-operational.md) |
| §§ 44–45 IRR | Outsourcing and subcontract agreements with PIPs — required clauses | [01-accountability](obligations/01-accountability.md), [05-care](obligations/05-care.md) | [01](../../layers/01-non-technical.md) |
| § 50 IRR | Accountability of PIC for transfers — domestic and cross-border | [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md) |

## NPC Circulars (operative)

| Source | Effective | Where referenced |
|---|---|---|
| **NPC Circular 16-03** — Personal Data Breach Management | 15 Dec 2016 | [06-breach-notification](obligations/06-breach-notification.md) |
| NPC Circular 16-01 — Security of Personal Data in Government Agencies (reference baseline for private-sector practice) | 10 Oct 2016 | [05-care](obligations/05-care.md) |
| NPC Circular 16-02 — Data Sharing Agreements involving Government Agencies | 10 Oct 2016 | [05-care](obligations/05-care.md) |
| NPC Circular 17-01 — Registration of Data Processing Systems and Notification regarding Automated Decision-making | 31 Jul 2017 (as amended) | (registration paperwork — out of scope) |
| **NPC Circular 18-01** — Right to Data Portability | 26 Sep 2018 | [04-access-correction](obligations/04-access-correction.md) |
| NPC Circular 2020-03 — Data Sharing Agreements in the Private Sector | 02 Dec 2020 | [05-care](obligations/05-care.md) |
| **NPC Circular 2022-04** — Rules on the Exercise of Data Subject Rights | 17 Oct 2022 | [04-access-correction](obligations/04-access-correction.md) |
| NPC Advisory 2017-03 — Privacy Impact Assessments | 31 Jul 2017 | (PIA encouraged — see README) |
| NPC Advisory 2017-01 — Designation of a DPO | 14 Mar 2017 | (DPO paperwork — out of scope) |
