# Vietnam PDPL — Jurisdiction Notes

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

| | |
|---|---|
| **Statute** | Luật Bảo vệ dữ liệu cá nhân (Law on Personal Data Protection), Law No. 91/2025/QH15 |
| **Current text reflected** | Law 91/2025/QH15 (39 articles, 5 chapters) read with **Decree 356/2025/NĐ-CP** (42 articles). Obligation files are written against the **Vietnamese text** of both, which is the binding version |
| **Last verified** | 2026-09-17 |
| **Passed** | 26 June 2025, National Assembly XV, 9th session |
| **In force since** | **1 January 2026** (Điều 38(1)) |
| **Replaces** | Decree 13/2023/NĐ-CP (17 April 2023), Vietnam's first personal-data framework. Guiding decree for the Law: **Decree 356/2025/NĐ-CP** (31 December 2025) |
| **Regulator** | `Cơ quan chuyên trách bảo vệ dữ liệu cá nhân` — the specialised personal-data-protection authority **under the Ministry of Public Security** (Điều 33(1)(a)), in practice A05. Vietnam enforces through the MPS, not an independent DPA |
| **Pending guidance** | Decree 356/2025/NĐ-CP supplies the data catalogues (Điều 3, 4), consent methods (Điều 6), dossier procedure (Điều 17–20) and breach form (Điều 28). Điều 38(4) of the Law still delegates the small-enterprise transition detail to further Government regulation |

> **Translation caveat:** the binding texts of Law 91/2025/QH15 and Decree 356/2025/NĐ-CP are the original **Vietnamese** versions. No official English translation was available at the last verification date. For the **Law**, the commercial database thuvienphapluat publishes an English rendering, but the accessible export is partial — 36 passages across 29 of the 39 articles are replaced by a subscription prompt, including every engineering-critical article. For the **Decree**, no English rendering was available at all. The content here is therefore based on the maintainer's reading of the **original Vietnamese text of both instruments**; English phrasing of Decree provisions, and of the redacted parts of the Law, is the maintainer's own unofficial translation. **In any conflict, the Vietnamese original wins.** Load-bearing Vietnamese terms are given in the original alongside the rendering. Use this as a starting framework; verify specific provisions against the Vietnamese text and consult a qualified Vietnamese privacy lawyer for binding interpretation.
>
> **Source copyright:** Vietnamese legal instruments are published by the State in Công báo and on government portals. The copies consulted here were exports from the **commercial legal databases** thuvienphapluat.vn and luatvietnam.vn, which apply their own subscription terms to their compilations and translations — a different posture from the government-published sources used for Singapore, Thailand and Indonesia. Verbatim quotations in this skill are short operative phrases in the original Vietnamese, reproduced with attribution for educational and engineering reference under fair-dealing principles — they are **not** licensed under this repository's MIT licence, and the English renderings are the maintainer's own. See [DISCLAIMER.md § Copyright in source materials](../../../../DISCLAIMER.md#copyright-in-source-materials).

## Critical thresholds

| Item | Detail |
|---|---|
| **Breach notification** | **72 hours from detection** of the violating act (Điều 23(1)), to the specialised authority. Note the trigger is **harm-based, not scale-based** — see below |
| **Processing impact assessment (DPIA)** | Dossier filed with the authority within **60 days from the first day of processing** (Điều 21(1)). Prepared **once for the entity's operating life**, then kept updated (Điều 21(2)) |
| **Cross-border transfer assessment (CTIA)** | Separate dossier, filed within **60 days from the first day of cross-border transfer** (Điều 20(2)). Also once-for-life, then updated (Điều 20(3)) |
| **Assessment updates** | Both dossiers reviewed **every 6 months**, or immediately on the triggers in Điều 22(2) |
| **Data-protection personnel** | **Every organisation** must designate qualified personnel or engage a service provider (Điều 33(2)) — no headcount or volume threshold |
| **Cross-border inspection** | Authority may inspect **at most once a year**, or without notice on a suspected violation or a data-loss incident (Điều 20(4)), and may order transfers suspended (Điều 20(5)) |
| **Maximum fines** | **5% of revenue** for cross-border transfer violations (Điều 8(4)); **10× the gain** for buying or selling personal data (Điều 8(3)); administrative, criminal, and compensation liability all available (Điều 8(1)) |

## Application — read this first

**Vietnam's reach follows citizenship, not user location** (Điều 1(2)). The Law applies to:

- Vietnamese agencies, organisations and individuals
- Foreign agencies, organisations and individuals **in Vietnam**
- Foreign agencies, organisations and individuals **directly participating in or related to the processing of personal data of Vietnamese citizens**, and of people of Vietnamese origin without determined nationality who live in Vietnam and hold an identity certificate

That third limb matters for this skill's usual advice. Everywhere else in these notes, active jurisdiction is decided by *where your users are*. Vietnam is the exception: a Vietnamese citizen using your product from Berlin is still within scope, with no establishment, targeting, or equipment test to fail. If you have Vietnamese users anywhere, treat VN as active.

## Obligations covered

| File | Articles |
|---|---|
| [01-accountability](obligations/01-accountability.md) | Điều 33 (data-protection personnel), 34, 35, 36, 37 |
| [02-consent](obligations/02-consent.md) | Điều 9, 10, 19 |
| [03-purpose](obligations/03-purpose.md) | Điều 3, 11, 16, 18 |
| [04-access-correction](obligations/04-access-correction.md) | Điều 4, 13, 14, 15, 17 |
| [05-care](obligations/05-care.md) | Điều 12, 20, 21, 22 |
| [06-breach-notification](obligations/06-breach-notification.md) | Điều 23 |
| [07-offences](obligations/07-offences.md) | Điều 7, 8 |
| [08-sector-specific](obligations/08-sector-specific.md) | Điều 24–32 |

The eighth file has no counterpart in the other jurisdictions. Điều 24–32 impose duties by **sector and processing type** — children, employment, health, finance, advertising, social media, big data and AI, location and biometrics, recording — rather than by lifecycle stage. Folding nine statutory articles into the seven lifecycle files would bury them; they are collected instead, and cross-referenced from the files they touch.

## What's intentionally not covered

- **Administrative-penalty procedure.** Điều 8(2) routes this through the general law on handling administrative violations. Engineering surface is the exposure, not the procedure.
- **State-agency processing.** Điều 21(6) exempts competent state agencies from the impact-assessment regime.
- **Administrative-penalty tariffs.** The Law sets the caps (Điều 8); the per-offence schedule sits in the general administrative-penalties regime and is out of scope here.

## Mental model: what makes Vietnam PDPL distinctive (engineering view)

Recalibrations if you know the other four regimes in this skill:

- **Filing, not just documenting.** SG, TH, MY and PH expect you to *hold* records. Vietnam expects you to **send** them: an original DPIA dossier within 60 days of first processing, and an original CTIA within 60 days of first cross-border transfer. The deadline runs from your own first action, so it starts silently — nobody notifies you.
- **Cross-border is defined broadly enough to catch ordinary architecture.** Điều 20(1)(c) counts *using a platform located outside Vietnam to process personal data collected in Vietnam* as a cross-border transfer. A managed database in Singapore, an analytics SaaS, a US-hosted error tracker — each is in scope. Most products touching Vietnamese users are transferring cross-border on day one.
- **Breach notification is harm-triggered, not scale-triggered.** Điều 23(1) turns on potential harm to national defence, national security, social order and safety, or to a data subject's life, health, honour, dignity or property. There is no "500 individuals" style threshold to count against, and the clock runs from **detection of the violation**, not from assessing it.
- **Data-protection personnel are universal.** Điều 33(2) requires every organisation to designate qualified personnel or engage a provider. There is no threshold equivalent to MY's 20,000-subject JPDP guideline or TH's core-activity test.
- **De-identified data leaves scope outright.** Điều 2(1) states that personal data, once de-identified, is no longer personal data — cleaner than the risk-based framing elsewhere. Điều 14 governs deletion, destruction and de-identification; Điều 7 separately **prohibits re-identification**.
- **Encryption has its own article.** Điều 12 addresses encryption and decryption of personal data directly, rather than leaving it as an unnamed security measure.
- **Small entities get a real transition.** Small and startup enterprises may opt out of Điều 21, 22 and 33(2) for **5 years** from entry into force; household and micro businesses are exempt from them outright (Điều 38(2)–(3)). Both carve-outs fall away if the entity provides data-processing services, directly processes **sensitive** personal data, or processes data of a **large number** of subjects.

## Cross-references

- [`../../checklists/`](../../checklists/) — entry points for common engineering tasks.
- [`../_index.md`](../_index.md) — cross-jurisdiction comparison.
- [`statute-map.md`](statute-map.md) — reverse lookup from article number.
