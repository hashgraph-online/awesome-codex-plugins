# Thailand PDPA — Statute ↔ Layer Cross-Reference

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Reverse lookup. Use when citing a section in a PR description, audit response, or breach notification. For day-to-day work, use the layer files and obligation files instead.

## Chapter I — Personal Data Protection Committee (s8–18)

Governance / regulator structure. Engineers reference these only via subordinate notifications issued by the Committee.

## Chapter II Part I — Consent (s19–21)

| Section | Topic | Obligation file | Layer |
|---|---|---|---|
| s19 | Consent required + form requirements + withdrawal | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md), [03](../../layers/03-data-model.md) |
| s20 | Minor consent (parental for under-10; complex for under-sui-juris) | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md) |
| s21 | Purpose limitation tied to consent | [03-purpose](obligations/03-purpose.md) | [06](../../layers/06-disclosure.md) |

## Chapter II Part II — Personal Data Collection (s22–26)

| Section | Topic | Obligation file | Layer |
|---|---|---|---|
| s22 | Data minimization | [03-purpose](obligations/03-purpose.md) | [03](../../layers/03-data-model.md), [05](../../layers/05-feature-ux.md) |
| s23 | Notification of purpose at collection | [03-purpose](obligations/03-purpose.md) | [06](../../layers/06-disclosure.md) |
| s24 | Lawful bases (6 enumerated) | [02-consent](obligations/02-consent.md) | [06](../../layers/06-disclosure.md) |
| s25 | Collection from sources other than the data subject | [02-consent](obligations/02-consent.md) | [04](../../layers/04-controls-and-processes.md) |
| s26 | Sensitive Personal Data | [02-consent](obligations/02-consent.md) | [03](../../layers/03-data-model.md), [05](../../layers/05-feature-ux.md) |

## Chapter II Part III — Use and Disclosure (s27–29)

| Section | Topic | Obligation file | Layer |
|---|---|---|---|
| s27 | Use / disclosure requires consent (or s24/s26 exceptions) | [02-consent](obligations/02-consent.md) | [04](../../layers/04-controls-and-processes.md) |
| s28 | Cross-border transfer — adequacy or 6 exceptions | [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md), [06](../../layers/06-disclosure.md) |
| s29 | Within-affiliate Personal Data Protection Policy (BCR-equivalent) | [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md) |

## Chapter III — Rights of the Data Subject (s30–36)

| Section | Topic | Obligation file | Layer |
|---|---|---|---|
| s30 | Access right + 30-day response | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md) |
| s31 | Data portability | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md) |
| s32 | Right to object (incl. direct marketing) | [04-access-correction](obligations/04-access-correction.md) | [05](../../layers/05-feature-ux.md), [04](../../layers/04-controls-and-processes.md) |
| s33 | Right to erasure / anonymisation | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md), [03](../../layers/03-data-model.md) |
| s34 | Right to restrict processing | [04-access-correction](obligations/04-access-correction.md) | [03](../../layers/03-data-model.md), [04](../../layers/04-controls-and-processes.md) |
| s35 | Accuracy obligation | [04-access-correction](obligations/04-access-correction.md), [05-care](obligations/05-care.md) | [05](../../layers/05-feature-ux.md), [04](../../layers/04-controls-and-processes.md) |
| s36 | Correction request handling | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md), [05](../../layers/05-feature-ux.md) |

## Data Controller / Processor / DPO Duties (s37–42)

| Section | Topic | Obligation file | Layer |
|---|---|---|---|
| s37(1) | Security measures | [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md), [04](../../layers/04-controls-and-processes.md), [01](../../layers/01-non-technical.md) |
| s37(2) | Onward-disclosure protection | [01-accountability](obligations/01-accountability.md), [05-care](obligations/05-care.md) | [01](../../layers/01-non-technical.md), [04](../../layers/04-controls-and-processes.md) |
| s37(3) | Erasure / destruction system | [01-accountability](obligations/01-accountability.md) | [04](../../layers/04-controls-and-processes.md) |
| **s37(4)** | **72-hour breach notification** | [06-breach-notification](obligations/06-breach-notification.md) | [07](../../layers/07-operational.md) |
| s37(5) | Designate Thai representative (non-Thai controllers) | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |
| s38 | Exceptions to representative requirement | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |
| s39 | Records of processing activities | [01-accountability](obligations/01-accountability.md) | [03](../../layers/03-data-model.md), [04](../../layers/04-controls-and-processes.md) |
| s40 | Data Processor duties | [01-accountability](obligations/01-accountability.md), [05-care](obligations/05-care.md) | [01](../../layers/01-non-technical.md), [04](../../layers/04-controls-and-processes.md) |
| s41 | DPO designation triggers | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |
| s42 | DPO duties + protections | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |

## Chapter IV — Office of the PDPC (s43–70)

Governance structure. Not directly relevant to engineering compliance.

## Chapter V — Complaints (s71–76)

Procedural — relevant during an active complaint. Engineers should know:
- s73 — data subjects have a right to file complaints with the expert committee
- s75–76 — Competent Official inspection powers; cooperation duties

## Chapter VI — Civil Liability (s77–78)

Civil damages framework. Relevant during litigation, not for ongoing compliance.

## Chapter VII — Penalties

### Part I — Criminal (s79–81)

| Section | Topic | Obligation file |
|---|---|---|
| s79 | Use/disclosure or cross-border of sensitive data without consent — criminal | [07-offences](obligations/07-offences.md) |
| s80 | Unauthorised disclosure by duty-holders — criminal | [07-offences](obligations/07-offences.md) |
| **s81** | **Personal liability for directors / managers (acts or omissions)** | [07-offences](obligations/07-offences.md) |

### Part II — Administrative (s82–90)

| Section | Topic | Cap |
|---|---|---|
| s82 | Procedural failures (records, DPO, consent form, etc.) | THB 1M |
| s83 | Substantive failures (consent, purpose, security, transfer) | THB 3M |
| **s84** | **Sensitive-data violations** | **THB 5M** |
| s85 | Data Processor procedural failures | THB 1M |
| s86 | Data Processor substantive failures | THB 3M |
| s87 | Data Processor sensitive-data failures | THB 5M |
| s88 | Representative failures | THB 1M |
| s89 | Failure to cooperate with the expert committee / Officials | THB 500K |
| s90 | Penalty calculation factors (severity + business size) | — |

## Transitional Provisions (s91–96)

Initial setup of the regulator and transitional arrangements for pre-existing data. Mostly historical — verify any relevant subordinate Decree at [pdpc.or.th](https://www.pdpc.or.th).
