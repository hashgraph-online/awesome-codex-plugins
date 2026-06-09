# Indonesia UU PDP — Statute ↔ Layer Cross-Reference

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Reverse lookup. Use when citing a Pasal in a PR description, audit response, or breach notification. For day-to-day work, use the layer files and obligation files instead.

## BAB I — General Provisions (Pasal 1–2)

Definitions and scope. Engineers reference indirectly via the defined terms (Data Pribadi, Pengendali Data Pribadi, Prosesor Data Pribadi, Subjek Data Pribadi, Pemrosesan).

## BAB II — Principles (Pasal 3)

Foundational principles statement. Operationalised through specific obligations in BAB V and BAB VI.

## BAB III — Types of Personal Data (Pasal 4)

| Pasal | Topic | Obligation file | Layer |
|---|---|---|---|
| 4 | Specific (sensitive) vs general Personal Data | [02-consent](obligations/02-consent.md) | [03](../../layers/03-data-model.md) |

## BAB IV — Data Subject Rights (Pasal 5–15)

| Pasal | Topic | Obligation file | Layer |
|---|---|---|---|
| 5 | Right to information about Controller | [04-access-correction](obligations/04-access-correction.md) | [06](../../layers/06-disclosure.md) |
| 6 | Right to correction | [04-access-correction](obligations/04-access-correction.md) | [05](../../layers/05-feature-ux.md) |
| 7 | Right to access + obtain copy | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md) |
| 8 | Right to end processing, erase, destroy | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md), [05](../../layers/05-feature-ux.md) |
| 9 | Right to withdraw consent | [04-access-correction](obligations/04-access-correction.md) | [05](../../layers/05-feature-ux.md), [03](../../layers/03-data-model.md) |
| 10 | Right to object to automated decision-making | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md), [05](../../layers/05-feature-ux.md) |
| 11 | Right to suspend / restrict processing | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md), [05](../../layers/05-feature-ux.md) |
| 12 | Right to sue for damages | (procedural) | — |
| 13 | Right to data portability | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md) |
| 14 | How to exercise rights | [04-access-correction](obligations/04-access-correction.md) | [05](../../layers/05-feature-ux.md), [04](../../layers/04-controls-and-processes.md) |
| 15 | Exceptions to rights | [04-access-correction](obligations/04-access-correction.md) | — |

## BAB V — Personal Data Processing (Pasal 16–18)

| Pasal | Topic | Obligation file | Layer |
|---|---|---|---|
| 16 | Personal Data protection principles (8) | [03-purpose](obligations/03-purpose.md) | [02](../../layers/02-architecture.md), [03](../../layers/03-data-model.md), [06](../../layers/06-disclosure.md) |
| 17 | Public-area visual data processing (CCTV-style) | [03-purpose](obligations/03-purpose.md) | [05](../../layers/05-feature-ux.md), [06](../../layers/06-disclosure.md) |
| 18 | Joint Controllers | [03-purpose](obligations/03-purpose.md) | [01](../../layers/01-non-technical.md) |

## BAB VI Bagian Kedua — Controller Obligations (Pasal 19–50)

| Pasal | Topic | Obligation file | Layer |
|---|---|---|---|
| 19 | Who is bound (definitions of Controllers / Processors) | [01-accountability](obligations/01-accountability.md) | — |
| 20 | Lawful basis required (6 GDPR-style bases) | [02-consent](obligations/02-consent.md) | [06](../../layers/06-disclosure.md) |
| 21 | Information at consent (7 categories) | [02-consent](obligations/02-consent.md), [03-purpose](obligations/03-purpose.md) | [06](../../layers/06-disclosure.md) |
| 22 | Consent form requirements (written / recorded; null if non-compliant) | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md) |
| 23 | Null contractual clauses requesting processing without explicit consent | [02-consent](obligations/02-consent.md) | [01](../../layers/01-non-technical.md) |
| 24 | Demonstrate consent (burden on Controller) | [01-accountability](obligations/01-accountability.md), [02-consent](obligations/02-consent.md) | [03](../../layers/03-data-model.md) |
| 25 | Children's data — parental consent | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md) |
| 26 | Disability accommodations | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md) |
| 27 | Limited, specific, lawful, transparent | [01-accountability](obligations/01-accountability.md), [03-purpose](obligations/03-purpose.md) | [06](../../layers/06-disclosure.md) |
| 28 | Purpose limitation | [03-purpose](obligations/03-purpose.md) | [06](../../layers/06-disclosure.md) |
| 29 | Accuracy | [05-care](obligations/05-care.md), [01-accountability](obligations/01-accountability.md) | [05](../../layers/05-feature-ux.md), [04](../../layers/04-controls-and-processes.md) |
| 30 | Correction within 72 hours | [01-accountability](obligations/01-accountability.md), [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md), [05](../../layers/05-feature-ux.md) |
| 31 | Records of processing activities | [01-accountability](obligations/01-accountability.md) | [03](../../layers/03-data-model.md), [04](../../layers/04-controls-and-processes.md) |
| 32 | Access within 72 hours | [01-accountability](obligations/01-accountability.md), [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md) |
| 33 | Permitted refusals (safety, others' data, national security) | [01-accountability](obligations/01-accountability.md), [04-access-correction](obligations/04-access-correction.md) | — |
| **34** | **Mandatory DPIA for high-risk processing (7 triggers)** | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |
| 35 | Security obligations | [01-accountability](obligations/01-accountability.md), [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md), [04](../../layers/04-controls-and-processes.md) |
| 36 | Confidentiality | [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md), [04](../../layers/04-controls-and-processes.md) |
| 37 | Supervise all parties | [01-accountability](obligations/01-accountability.md), [05-care](obligations/05-care.md) | [01](../../layers/01-non-technical.md), [04](../../layers/04-controls-and-processes.md) |
| 38 | Protect from unlawful processing | [01-accountability](obligations/01-accountability.md), [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md), [04](../../layers/04-controls-and-processes.md) |
| 39 | Prevent unauthorized access | [01-accountability](obligations/01-accountability.md), [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md) |
| 40 | Stop processing on consent withdrawal (72h) | [01-accountability](obligations/01-accountability.md), [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md) |
| 41 | Suspend / restrict processing (72h) | [01-accountability](obligations/01-accountability.md), [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md), [05](../../layers/05-feature-ux.md) |
| 42 | End processing when triggered | [01-accountability](obligations/01-accountability.md), [05-care](obligations/05-care.md) | [04](../../layers/04-controls-and-processes.md) |
| 43 | Erasure obligation (4 grounds) | [01-accountability](obligations/01-accountability.md) | [04](../../layers/04-controls-and-processes.md) |
| 44 | Destruction obligation | [01-accountability](obligations/01-accountability.md) | [04](../../layers/04-controls-and-processes.md) |
| 45 | Notify Subject of erasure / destruction | [01-accountability](obligations/01-accountability.md) | [04](../../layers/04-controls-and-processes.md) |
| **46** | **Breach notification — 72h, dual-recipient** | [06-breach-notification](obligations/06-breach-notification.md) | [07](../../layers/07-operational.md) |
| 47 | Accountability | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |
| 48 | M&A / dissolution notification | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |
| 49 | Comply with regulator orders | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |
| 50 | Exceptions to controller obligations | [01-accountability](obligations/01-accountability.md) | — |

## BAB VI Bagian Ketiga — Processor Obligations (Pasal 51–52)

| Pasal | Topic | Obligation file | Layer |
|---|---|---|---|
| 51 | Processor must process on Controller's instructions; reclassification if exceeded | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md), [04](../../layers/04-controls-and-processes.md) |
| 52 | Processor inherits specific Controller obligations (Pasal 29, 31, 35–39) | [01-accountability](obligations/01-accountability.md) | [02](../../layers/02-architecture.md), [04](../../layers/04-controls-and-processes.md) |

## BAB VI Bagian Keempat — DPO (Pasal 53–54)

| Pasal | Topic | Obligation file | Layer |
|---|---|---|---|
| 53 | DPO designation triggers (3 conditions) | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |
| 54 | DPO duties (4 minimum) + protections | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |

## BAB VII — Personal Data Transfer (Pasal 55–56)

| Pasal | Topic | Obligation file | Layer |
|---|---|---|---|
| 55 | Domestic transfer | [05-care](obligations/05-care.md) | [01](../../layers/01-non-technical.md) |
| **56** | **Cross-border transfer (3-tier hierarchy)** | [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md), [06](../../layers/06-disclosure.md) |

## BAB VIII — Administrative Sanctions (Pasal 57)

| Pasal | Topic | Obligation file |
|---|---|---|
| **57** | **Administrative sanctions — written warning, suspension, deletion, fine up to 2% revenue** | [07-offences](obligations/07-offences.md) |

## BAB IX–XII — Authority, International Cooperation, Public Participation, Dispute Resolution

Mostly governance / procedural. Engineers indirectly affected via the regulator's authority to issue notifications and binding interpretations.

## BAB XIII — Prohibitions (Pasal 65–66)

| Pasal | Topic | Obligation file |
|---|---|---|
| 65 | Prohibitions on use of others' data (basis for criminal Pasal 67) | [07-offences](obligations/07-offences.md) |
| 66 | Prohibition on falsification (basis for criminal Pasal 68) | [07-offences](obligations/07-offences.md) |

## BAB XIV — Criminal Penalties (Pasal 67–73)

| Pasal | Topic | Obligation file |
|---|---|---|
| 67 | Three-tier criminal offences (4–5 years + IDR 4–5B) | [07-offences](obligations/07-offences.md) |
| 68 | Falsification (6 years + IDR 6B) | [07-offences](obligations/07-offences.md) |
| 69 | Additional penalties (asset confiscation, compensation) | [07-offences](obligations/07-offences.md) |
| **70** | **Corporate criminal liability — fine up to 10× + suspension / ban / dissolution** | [07-offences](obligations/07-offences.md) |
| 71–73 | Enforcement procedures | (procedural) |

## BAB XV–XVI — Transitional and Closing Provisions (Pasal 74–76)

Initial setup transition (2-year window from October 2022 to October 2024) and procedural closing provisions. Mostly historical for compliance-implementation purposes.
