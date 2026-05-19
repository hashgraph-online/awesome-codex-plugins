# General Privacy Principles and Notice — § 11 RA 10173 + § 18 IRR

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

§ 11 sets the substantive ground rules for processing — **transparency, legitimate purpose, proportionality** — and the data-quality requirements (accurate, kept up to date, not retained longer than necessary). The IRR § 18 operationalises each.

## § 11 — General data privacy principles

**Rule (verbatim):** *"The processing of personal information shall be allowed, subject to compliance with the requirements of this Act and other laws allowing disclosure of information to the public and adherence to the principles of transparency, legitimate purpose and proportionality."*

The section then lists the operational requirements:

| § 11 sub | Requirement | Engineering surface |
|---|---|---|
| (a) | Personal information shall be collected for **specified and legitimate purposes** determined and declared **before**, or **as soon as reasonably practicable after**, collection | Privacy notice + consent surface |
| (b) | Processed **fairly and lawfully** | Lawful basis labelling per processing purpose |
| (c) | **Accurate, relevant and, where necessary, kept up to date**; inaccurate or incomplete data must, having regard to the purposes for which they were collected or further processed, be **rectified, supplemented, destroyed or their further processing restricted** | Data integrity controls; rectification UX |
| (d) | **Adequate and not excessive** in relation to the purposes for which they are collected and processed | Data minimisation in schema design |
| (e) | **Retained only for as long as necessary** for the fulfilment of the purposes for which the data was obtained or for the establishment, exercise or defence of legal claims, or for legitimate business purposes, or as provided by law | Retention sweeps; deletion conventions |
| (f) | **Kept in a form which permits identification of data subjects for no longer than is necessary** for the purposes for which the data were collected and processed; further processing for historical, statistical or scientific purposes shall not be considered as incompatible with the original purposes | Anonymisation / pseudonymisation pipeline |
| (g) | Personal information processed for **historical, statistical or scientific purposes**, and not otherwise made available to the public, shall be retained for the prescribed period and irreversibly anonymised / aggregated as soon as the personal information identification is no longer necessary | Research / analytics handling |

**Practical effect:** these are the **principles every engineering decision should be testable against**. A new column proposed in design review: does it have a specified purpose declared in the notice? Is the lawful basis labelled? Is it adequate but not excessive? Is the retention rule defined? Will it be rectifiable?

**Implementation layer:** the principles map across [03 Data model](../../../layers/03-data-model.md), [05 Feature/UX](../../../layers/05-feature-ux.md), and [06 Disclosure](../../../layers/06-disclosure.md).

**Operationalisation:**
- **Specified and legitimate purpose** (a): every persistent personal-data field is mapped to a declared purpose. If a field has no purpose, it doesn't ship.
- **Fair and lawful** (b): the privacy notice labels each purpose with its lawful basis (consent under § 12(a), contract under § 12(b), etc.).
- **Accurate and kept up to date** (c): users have a Settings / Profile surface to rectify their own data; downstream systems propagate corrections.
- **Adequate but not excessive** (d): "we might need it later" fields are dropped at design review. Optional vs required field distinction in forms reflects this — required-but-not-necessary fails.
- **Retention** (e): every persistent field has a documented retention rule (purpose lifetime + grace period). Sweep jobs enforce the rule. Soft-delete plus a hard-delete sweep is the typical pattern.
- **Identifiability minimisation** (f): for analytics / research, anonymise or aggregate as early in the pipeline as possible. Joining on `user_id` and stripping at egress is fine; storing the personally-identified version when not needed is not.

## § 18 IRR — Operational principles (notice content and timing)

**Rule (summary):** the IRR § 18 expands § 11 with operational detail on the notice — content, timing, format. Combined with § 16(a) (right to be informed) it specifies what the data subject must be told.

**Notice content (§ 16(a) + § 34(a) IRR):** the data subject must be informed of:
1. The **identity** of the PIC and (if different) the PIC's representative.
2. The **DPO contact** information.
3. The **purpose(s)** for which the personal information is being collected and processed.
4. The **lawful basis** for the processing.
5. The **intended recipients or categories of recipients** of the personal information, including domestic and international transfers.
6. Whether the personal information is being collected by the PIC directly from the data subject or from a third party.
7. The **methods of collection** (forms, cookies, sensors, etc.).
8. The **rights of the data subject** under § 16 and how to exercise them.
9. The **period for which the personal information will be stored**, or the criteria used to determine it.
10. The **existence of automated decision-making**, including profiling, where relevant.
11. The **complaint mechanism** (with the PIC's DPO and with the NPC).

**Practical effect:** the privacy notice is not a checkbox — it has prescribed content. Missing items make the notice non-compliant and the consent invalid, and consent invalidity collapses the lawful basis.

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md) (privacy notice copy), [05 Feature/UX](../../../layers/05-feature-ux.md) (notice surface placement).

**Operationalisation:**
- Privacy notice is a versioned document. Each material change increments the version; each consent record references the version hash the user saw.
- Notice is presented **before or at the point of collection**, in plain language, in a place the user actually sees (signup screen, in-flow before the data is collected, not buried 15 clicks deep).
- Layered notice is acceptable: a short summary at the collection point, with a link to the full notice. The summary must be substantive — "we collect data" doesn't qualify.
- Notice is in a language the data subject is reasonably likely to understand. PH consumer apps typically ship English + Filipino notices; sectoral rules may require the local language.
- For data **collected from a third party** (e.g., your app receives data from a partner platform via OAuth), the data subject must still be informed, *"within a reasonable period"* after collection — usually on first interaction with the user under the new context.
- Automated decision-making disclosure: if the app uses ML for credit scoring, content moderation, eligibility scoring, or any decision with significant effect on the user, the notice must disclose its existence and offer the right to object (see [04-access-correction.md](04-access-correction.md)).

## Repeated collection in the same circumstances

The IRR does not have a section equivalent to MY § 41 / SG s20 ("repeated collection in the same circumstances does not require fresh notice"). PH practice: when the collection is materially the same as previously notified and the user has not asked for a fresh notice, the original notice continues to govern. Material changes — new purpose, new recipient, new processing — require a fresh notice and (where the basis is consent) a fresh consent.

## What's at stake

- **§ 25(a) / (b) — unauthorised processing**: where the lawful basis fails because the notice was non-compliant, the processing is unauthorised. PI: 1–3 years + ₱500k–₱2M. SPI: 3–6 years + ₱500k–₱4M.
- **§ 28 — processing for unauthorised purposes**: where the actual processing diverges from the notified purpose. 1.5 to 7 years + up to ₱2M.
- **§ 32 — unauthorised disclosure**: where personal information is disclosed to a recipient not covered by the notice. 1 to 5 years + ₱500k–₱2M.
- **§ 11(c) and (d)** breaches (inaccurate, excessive data) typically don't carry a discrete penalty but compound the case in any complaint and undermine the PIC's "good faith / due diligence" posture.
- **§ 34 — officer liability**: where the corporate offence engages, the responsible officers serve the prison terms personally.

The privacy notice is the artefact NPC inspects first. Get it right at version 1, version it like code, and re-consent on material changes.
