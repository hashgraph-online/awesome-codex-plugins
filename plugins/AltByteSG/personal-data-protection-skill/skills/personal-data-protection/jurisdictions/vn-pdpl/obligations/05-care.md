# Security, Impact Assessment and Cross-Border Transfer — Điều 12, 20, 21, 22

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.
>
> **Unofficial translation.** Law 91/2025/QH15 and Decree 356/2025/NĐ-CP have no official
> English version. English wording below is the maintainer's rendering of the Vietnamese;
> load-bearing terms carry the original. **In any conflict the Vietnamese wins.** See the
> translation caveat in [README.md](../README.md).

This is where Vietnam departs most sharply from the other jurisdictions in this skill. Two impact-assessment dossiers must be **filed with the regulator**, each within **60 days**, and the cross-border definition is broad enough to catch ordinary architecture.

## Điều 12 — Encryption and decryption of personal data

Vietnam gives encryption its own article rather than leaving it inside a general security principle. Treat column-level or field-level encryption of sensitive categories as an express expectation, and keep key custody documented.

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md), [02 Architecture](../../../layers/02-architecture.md).

## Điều 21 — Processing impact assessment (DPIA)

**Rule (Điều 21(1)):** the controller, and the controller-and-processor, must prepare and store a processing impact assessment dossier and **send one original to the specialised authority within 60 days from the first day of processing personal data**.

- **(2)** The assessment is performed **once for the entire operating life** of the entity, and updated under Điều 22.
- **(3)** The **processor** prepares and stores its own dossier as agreed with the controller.
- **(4)** The authority may require the dossier to be completed if it is inadequate.
- **(5)** Parties must update the dossier when the submitted content changes.
- **(6)** Competent **state agencies** are exempt.
- **(7)** The Government specifies the dossier contents.

**Engineering consequence:** the 60-day clock starts from **your own first processing**, silently. Nobody sends a reminder. For a new product with Vietnamese users, filing is a launch-window task, not an annual-compliance task.

## Điều 20 — Cross-border transfer

**Điều 20(1) — what counts as a cross-border transfer:**

- a) transferring personal data **stored in Vietnam** to a storage system located outside Vietnam;
- b) an entity **in Vietnam** transferring personal data to an organisation or individual **abroad**;
- c) an entity in Vietnam **or abroad** using a **platform located outside Vietnam** to process personal data **collected in Vietnam**.

**Limb (c) is the one that catches people.** A managed database in another region, an analytics or error-tracking SaaS, a foreign-hosted LLM API — each is a cross-border transfer of data collected in Vietnam. Most products with Vietnamese users are transferring on day one.

**Điều 20(2):** anyone doing any of the above must prepare a **cross-border transfer impact assessment** dossier and send **one original** to the specialised authority **within 60 days from the first day of cross-border transfer**.

**Điều 20(3):** performed **once for the entity's operating life**, updated under Điều 22.

**Điều 20(4):** the authority decides on inspection — **periodic, at most once per year**, or **unannounced** where a violation is found or a data-loss incident occurs.

**Điều 20(5):** the authority may require transfers to be **suspended**.

**Engineering consequence:** treat the sub-processor inventory as the input to this dossier. Every new foreign vendor that touches Vietnamese personal data is a change to the CTIA, which triggers the Điều 22 update duty — so vendor onboarding must have a VN compliance step, not just a DPA review.

## Điều 22 — Updating the assessment dossiers

Both the processing-impact and cross-border-transfer dossiers are updated **every 6 months**, or **immediately** on the triggers in Điều 22(2).

**Operationalisation:** put a recurring 6-month review on the same calendar as your retention sweeps, and wire an immediate-update trigger into the vendor-onboarding and architecture-change paths. A once-for-life dossier that is never updated is worse than none — it is a filed document that has become inaccurate.

**Implementation layer:** [02 Architecture](../../../layers/02-architecture.md), [07 Operational](../../../layers/07-operational.md).

## Small-entity transition

Small and startup enterprises may **opt out of Điều 21 and 22 for 5 years** from 1 January 2026; household and micro businesses are exempt outright (Điều 38(2)–(3)). Both carve-outs **fall away** where the entity provides data-processing services, directly processes **sensitive** personal data, or processes data of a **large number** of subjects. Check the carve-out before relying on it — most consumer products processing sensitive categories will not qualify.
