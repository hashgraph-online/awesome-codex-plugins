# Vietnam PDPL — Statute ↔ Layer Cross-Reference

>
> **Unofficial translation.** Law 91/2025/QH15 and Decree 356/2025/NĐ-CP have no official
> English version. English wording below is the maintainer's rendering of the Vietnamese;
> load-bearing terms carry the original. **In any conflict the Vietnamese wins.** See the
> translation caveat in [README.md](README.md).

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Reverse lookup. Use when citing an article in a PR description, audit response, or breach notification. For day-to-day work, use the layer files and obligation files instead.

References use the article numbering of **Law No. 91/2025/QH15** and **Decree 356/2025/NĐ-CP**. Article text was read in **Vietnamese**, which is the binding version; the English topic descriptions below are the maintainer's unofficial renderings. No official English translation was available at the last verification date — see the translation caveat in [README.md](README.md).

## Law 91/2025/QH15

| Article | Topic | Obligation file | Layer |
|---|---|---|---|
| Điều 1 | Scope and applicable entities — reaches processing of Vietnamese citizens' data wherever it occurs | — | [02](../../layers/02-architecture.md) |
| Điều 2 | Definitions; basic vs sensitive split; de-identified data leaves scope | [03-purpose](obligations/03-purpose.md) | [03](../../layers/03-data-model.md) |
| Điều 3 | Protection principles — purpose limitation, accuracy, purpose-bound retention | [03-purpose](obligations/03-purpose.md) | [03](../../layers/03-data-model.md), [06](../../layers/06-disclosure.md) |
| Điều 4 | **Rights and obligations of the data subject** | [04-access-correction](obligations/04-access-correction.md) | [05](../../layers/05-feature-ux.md), [04](../../layers/04-controls-and-processes.md) |
| Điều 7 | **Prohibited acts** — incl. buying/selling data, intentional disclosure or loss | [07-offences](obligations/07-offences.md) | [01](../../layers/01-non-technical.md) |
| Điều 8 | **Penalties** — 10× gain for data sale; 5% revenue for cross-border breach | [07-offences](obligations/07-offences.md) | [01](../../layers/01-non-technical.md) |
| Điều 9 | **Consent** — per purpose, no bundling, silence is not consent, verifiable format | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md), [03](../../layers/03-data-model.md) |
| Điều 10 | Withdrawal of consent; restriction of processing; processor fan-out | [02-consent](obligations/02-consent.md) | [04](../../layers/04-controls-and-processes.md), [03](../../layers/03-data-model.md) |
| Điều 11 | Collection, analysis, aggregation | [03-purpose](obligations/03-purpose.md) | [03](../../layers/03-data-model.md) |
| Điều 12 | **Encryption and decryption of personal data** | [05-care](obligations/05-care.md) | [03](../../layers/03-data-model.md), [02](../../layers/02-architecture.md) |
| Điều 13 | Correction of personal data | [04-access-correction](obligations/04-access-correction.md) | [05](../../layers/05-feature-ux.md) |
| Điều 14 | Deletion, destruction, de-identification | [04-access-correction](obligations/04-access-correction.md) | [03](../../layers/03-data-model.md), [07](../../layers/07-operational.md) |
| Điều 15 | Provision of personal data (access / export) | [04-access-correction](obligations/04-access-correction.md) | [04](../../layers/04-controls-and-processes.md) |
| Điều 16 | Publication of personal data | [03-purpose](obligations/03-purpose.md) | [05](../../layers/05-feature-ux.md), [06](../../layers/06-disclosure.md) |
| Điều 17 | Transfer of personal data (domestic) | [04-access-correction](obligations/04-access-correction.md) | [02](../../layers/02-architecture.md) |
| Điều 18 | Other processing activities | [03-purpose](obligations/03-purpose.md) | [03](../../layers/03-data-model.md) |
| Điều 19 | Processing **without** consent — closed list | [02-consent](obligations/02-consent.md) | [03](../../layers/03-data-model.md), [06](../../layers/06-disclosure.md) |
| Điều 20 | **Cross-border transfer** — incl. use of any platform outside Vietnam; CTIA filed in 60 days | [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md) |
| Điều 21 | **Processing impact assessment** — dossier filed with the authority in 60 days | [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md), [07](../../layers/07-operational.md) |
| Điều 22 | Updating both dossiers — 6-monthly, or immediately on trigger | [05-care](obligations/05-care.md) | [07](../../layers/07-operational.md) |
| Điều 23 | **Breach notification — 72h from detection**; also purpose-creep and rights failures | [06-breach-notification](obligations/06-breach-notification.md) | [07](../../layers/07-operational.md) |
| Điều 24 | Children and persons with limited civil act capacity | [08-sector-specific](obligations/08-sector-specific.md) | [05](../../layers/05-feature-ux.md) |
| Điều 25 | Recruitment, management and use of employees | [08-sector-specific](obligations/08-sector-specific.md) | [04](../../layers/04-controls-and-processes.md) |
| Điều 26 | Health information | [08-sector-specific](obligations/08-sector-specific.md) | [03](../../layers/03-data-model.md) |
| Điều 27 | Finance, banking, credit information | [08-sector-specific](obligations/08-sector-specific.md) | [03](../../layers/03-data-model.md) |
| Điều 28 | Advertising services | [08-sector-specific](obligations/08-sector-specific.md) | [05](../../layers/05-feature-ux.md), [06](../../layers/06-disclosure.md) |
| Điều 29 | Social media platforms and online communication services | [08-sector-specific](obligations/08-sector-specific.md) | [05](../../layers/05-feature-ux.md) |
| Điều 30 | **Big data, AI, blockchain, virtual worlds** | [08-sector-specific](obligations/08-sector-specific.md) | [03](../../layers/03-data-model.md), [02](../../layers/02-architecture.md) |
| Điều 31 | **Personal location data and biometric data** | [08-sector-specific](obligations/08-sector-specific.md) | [03](../../layers/03-data-model.md) |
| Điều 32 | Audio and video recording in public places | [08-sector-specific](obligations/08-sector-specific.md) | [05](../../layers/05-feature-ux.md) |
| Điều 33 | **Data-protection personnel — required of every organisation** | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |
| Điều 34 | Technical standards and regulations | [01-accountability](obligations/01-accountability.md) | — |
| Điều 35 | Inspection of protection activities | [01-accountability](obligations/01-accountability.md) | — |
| Điều 36 | State management responsibility | [01-accountability](obligations/01-accountability.md) | — |
| Điều 37 | **Controller / processor responsibilities** — incl. preventing unauthorised collection | [01-accountability](obligations/01-accountability.md) | [02](../../layers/02-architecture.md), [04](../../layers/04-controls-and-processes.md) |
| Điều 38 | Effective date (1 Jan 2026); small-entity 5-year transition | — | [01](../../layers/01-non-technical.md) |
| Điều 39 | Transitional provisions — Decree 13/2023 consents and filings preserved | — | [01](../../layers/01-non-technical.md) |

## Decree 356/2025/NĐ-CP

| Article | Topic | Obligation file | Layer |
|---|---|---|---|
| Điều 3 | **Catalogue of basic personal data** — 11 items, residual | [03-purpose](obligations/03-purpose.md) | [03](../../layers/03-data-model.md) |
| Điều 4 | **Catalogue of sensitive personal data** — 13 items incl. location, credentials, financial, behaviour tracking | [03-purpose](obligations/03-purpose.md) | [03](../../layers/03-data-model.md), [04](../../layers/04-controls-and-processes.md) |
| Điều 5 | Exercise of data subject rights | [04-access-correction](obligations/04-access-correction.md) | [05](../../layers/05-feature-ux.md) |
| Điều 6 | **Methods of expressing consent** | [02-consent](obligations/02-consent.md) | [05](../../layers/05-feature-ux.md) |
| Điều 7 | Transfer of personal data | [04-access-correction](obligations/04-access-correction.md) | [02](../../layers/02-architecture.md) |
| Điều 8–12 | Sector and technology detail — finance, big data, AI and virtual worlds, blockchain, **cloud computing** | [08-sector-specific](obligations/08-sector-specific.md) | [02](../../layers/02-architecture.md), [03](../../layers/03-data-model.md) |
| Điều 13–16 | Data-protection personnel conditions and duties; service providers | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |
| Điều 17–20 | Cross-border transfer; dossier conditions and procedures; dossier updates | [05-care](obligations/05-care.md) | [02](../../layers/02-architecture.md), [07](../../layers/07-operational.md) |
| Điều 21–27 | Data-processing service business — conditions, certificate, revocation | [01-accountability](obligations/01-accountability.md) | [01](../../layers/01-non-technical.md) |
| Điều 28 | **Breach notification content and Form No. 08** | [06-breach-notification](obligations/06-breach-notification.md) | [07](../../layers/07-operational.md) |
| Điều 29 | Breach notification for sensitive personal data | [06-breach-notification](obligations/06-breach-notification.md) | [07](../../layers/07-operational.md) |
| Điều 31 | Inspection of protection activities | [01-accountability](obligations/01-accountability.md) | — |
