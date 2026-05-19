# Malaysia PDPA — Statute ↔ Layer Cross-Reference

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Reverse lookup. Use when citing a section in a PR description, audit response, or breach notification. For day-to-day work, use the layer files and obligation files instead.

References use the section numbering of Act 709 as amended by Act A1727 (in force 1 June 2025). "(new 2024)" marks provisions inserted by A1727; "(amended 2024)" marks substantive A1727 changes.

## Part I — Preliminary

| Section | Topic | Obligation file | Layer |
|---|---|---|---|
| s2(1)–(2) | Application: commercial transactions; government carve-out | — | — |
| s3 | Territorial reach (established in MY, or equipment in MY) | — | [02](../../layers/02-architecture.md) |
| s4 | Definitions, including "sensitive personal data" (incl. biometric, amended 2024), "personal data breach" (new 2024), "data subject" excludes deceased (amended 2024) | [02-consent](obligations/02-consent.md), [06-breach-notification](obligations/06-breach-notification.md) | [03](../../layers/03-data-model.md) |

## Part II Division 1 — Personal Data Protection Principles

| Section | Topic | Obligation file | Layer |
|---|---|---|---|
| s5(1) | Seven Principles enumerated | All obligation files | All |
| s5(1A) (new 2024) | Data processor directly subject to Security Principle (s9) | [05-care](obligations/05-care.md) | [01](../../layers/01-non-technical.md), [02](../../layers/02-architecture.md) |
| s5(2) (amended 2024) | Penalty for principle breach: RM 1M / 3 years | [07-offences](obligations/07-offences.md) | — |
| s6 | General Principle: consent + lawful-purpose tests | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md), [03](../../layers/03-data-model.md) |
| s6(2) | Non-consent bases (contract, legal obligation, vital interests, justice administration, statutory functions) | [02-consent](obligations/02-consent.md) | [06](../../layers/06-disclosure.md) |
| s6(3) | Lawful purpose, necessity, adequacy / non-excessiveness | [02-consent](obligations/02-consent.md), [03-purpose](obligations/03-purpose.md) | [03](../../layers/03-data-model.md), [05](../../layers/05-feature-ux.md) |
| s7 | Notice and Choice Principle: written notice content | [03-purpose](obligations/03-purpose.md) | [06](../../layers/06-disclosure.md), [05](../../layers/05-feature-ux.md) |
| s7(3) | Notice in **both** Bahasa Malaysia and English | [03-purpose](obligations/03-purpose.md) | [06](../../layers/06-disclosure.md) |
| s8 | Disclosure Principle: no disclosure outside notified purpose / class | [03-purpose](obligations/03-purpose.md) | [04](../../layers/04-controls-and-processes.md), [06](../../layers/06-disclosure.md) |
| s9 (amended 2024) | Security Principle: practical steps; now binds **both** controller and processor directly | [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md), [04](../../layers/04-controls-and-processes.md), [01](../../layers/01-non-technical.md) |
| s10 | Retention Principle: not longer than necessary; destroy or permanently delete | [05-care](obligations/05-care.md) | [03](../../layers/03-data-model.md), [04](../../layers/04-controls-and-processes.md) |
| s11 | Data Integrity Principle: accurate, complete, not misleading, kept up-to-date | [05-care](obligations/05-care.md) | [05](../../layers/05-feature-ux.md), [04](../../layers/04-controls-and-processes.md) |
| s12 | Access Principle: data subject has right of access + correction | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md), [05](../../layers/05-feature-ux.md) |

## Part II Division 1A — Accountability of personal data (new 2024)

| Section | Topic | Obligation file | Layer |
|---|---|---|---|
| s12A (new 2024) | Appointment of Data Protection Officer; notify Commissioner | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |
| **s12B(1)** (new 2024) | **Notify Commissioner of personal data breach** ("as soon as practicable"; **72h** per Guideline) | [06-breach-notification](obligations/06-breach-notification.md) | [07](../../layers/07-operational.md) |
| s12B(2) (new 2024) | Notify data subject if breach causes / likely causes significant harm ("without unnecessary delay"; **7 days** post-Commissioner per Guideline) | [06-breach-notification](obligations/06-breach-notification.md) | [07](../../layers/07-operational.md) |
| s12B(3) (new 2024) | Penalty for failure: RM 250,000 / 2 years | [06-breach-notification](obligations/06-breach-notification.md), [07-offences](obligations/07-offences.md) | — |

## Part II Division 3 — Data controller forum and code of practice

| Section | Topic | Obligation file | Layer |
|---|---|---|---|
| s23–28 | Codes of practice — applicable, registered, issued by Commissioner | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |
| s29 | Penalty for non-compliance with applicable code | [01-accountability](obligations/01-accountability.md), [07-offences](obligations/07-offences.md) | [01](../../layers/01-non-technical.md) |

## Part II Division 4 — Rights of data subject

| Section | Topic | Obligation file | Layer |
|---|---|---|---|
| s30 | Right of access to personal data | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md), [05](../../layers/05-feature-ux.md) |
| s31 | Compliance with data access request (form, period) | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md) |
| s32 + 5th Sch (where applicable) | Circumstances where the controller may refuse access | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md) |
| s33 | Notification of refusal to comply with access request | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md) |
| s34 | Right to correct personal data | [04-access-correction](obligations/04-access-correction.md) | [05](../../layers/05-feature-ux.md) |
| s35 | Compliance with correction request | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md), [05](../../layers/05-feature-ux.md) |
| s36 | Circumstances where controller may refuse correction | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md) |
| s37 | Notification of refusal to comply with correction request | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md) |
| s38 | Withdrawal of consent | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md), [04](../../layers/04-controls-and-processes.md) |
| s39 | Extent of disclosure of personal data (carve-out from s8) | [03-purpose](obligations/03-purpose.md) | [04](../../layers/04-controls-and-processes.md) |
| s40 | Processing of sensitive personal data — explicit consent default | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md), [03](../../layers/03-data-model.md) |
| s40(3) | Penalty for sensitive-PD breach: RM 200,000 / 2 years | [07-offences](obligations/07-offences.md) | — |
| s41 | Repeated collection of personal data in same circumstances | [03-purpose](obligations/03-purpose.md) | [05](../../layers/05-feature-ux.md) |
| s42 | Right to prevent processing likely to cause damage or distress | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md) |
| s43 | Right to prevent processing for direct marketing | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md), [04](../../layers/04-controls-and-processes.md) |
| **s43A** (new 2024) | **Right to data portability** — transmit to another controller; technical-feasibility / format-compatibility caveat | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md), [05](../../layers/05-feature-ux.md) |
| s44 | Record to be kept by data controller | [05-care](obligations/05-care.md) | [03](../../layers/03-data-model.md), [04](../../layers/04-controls-and-processes.md) |

## Cross-border transfer

| Section | Topic | Obligation file | Layer |
|---|---|---|---|
| **s129** (amended 2024) | Cross-border transfer — **whitelist regime deleted** (1 April 2025); transfer permitted on s129(3) safeguards (consent, contract, due diligence under (f), etc.) | [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md), [06](../../layers/06-disclosure.md) |
| s129(5) | Penalty for breach: RM 300,000 / 2 years | [07-offences](obligations/07-offences.md) | — |

## Offences

| Section | Topic | Obligation file |
|---|---|---|
| s5(2) (amended 2024) | Principle breach — RM 1M / 3 years | [07-offences](obligations/07-offences.md) |
| s12B(3) (new 2024) | Failure to notify breach to Commissioner — RM 250,000 / 2 years | [07-offences](obligations/07-offences.md) |
| s40(3) | Sensitive-PD breach — RM 200,000 / 2 years | [07-offences](obligations/07-offences.md) |
| s129(5) | Cross-border breach — RM 300,000 / 2 years | [07-offences](obligations/07-offences.md) |
| s130 | Unlawful collection / sale of personal data — RM 500,000 / 3 years | [07-offences](obligations/07-offences.md) |
| s131 | Abetment and attempt | [07-offences](obligations/07-offences.md) |
| s132 | Compounding (Commissioner may compound up to 50% of max fine, with Public Prosecutor's consent) | [07-offences](obligations/07-offences.md) |
| **s133** | **Body-corporate liability — directors / managers deemed liable unless they prove no knowledge + due diligence** | [07-offences](obligations/07-offences.md) |

## Subordinate sources (operative)

| Source | Effective | Where referenced |
|---|---|---|
| Personal Data Protection Guideline on Data Breach Notification (JPDP, 25 Feb 2025) | 1 June 2025 | [06-breach-notification](obligations/06-breach-notification.md) |
| Personal Data Protection Guideline on the Appointment of Data Protection Officer (JPDP, 25 Feb 2025) | 1 June 2025 | [01-accountability](obligations/01-accountability.md) |
| P.U.(B) 522/2024 — Commencement notice for Act A1727 | Staged 1 Jan / 1 Apr / 1 Jun 2025 | [README](README.md) |
