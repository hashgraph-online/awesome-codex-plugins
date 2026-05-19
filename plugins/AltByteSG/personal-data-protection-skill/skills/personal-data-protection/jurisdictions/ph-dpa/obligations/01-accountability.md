# Accountability — §§ 21, 22 RA 10173 + § 14, §§ 44–45, § 50 IRR

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

PH accountability obligations sit mostly in **non-engineering** governance — DPO appointment under § 14 IRR, NPC registration of data processing systems under NPC Circular 17-01, and outsourcing / data-sharing agreements under §§ 44–45 IRR. This file covers the **engineering touch-points only**: the DPO contact channel exposed by your application, and the vendor flow-down clauses that affect what your stack can do with the data.

For the paperwork — DPO appointment, NPC registration, code-of-practice adherence — see the [README "What's intentionally not covered"](../README.md#whats-intentionally-not-covered) and refer to the NPC directly.

## § 21 RA 10173 — Principle of accountability

**Rule (verbatim):** *"Each personal information controller is responsible for personal information under its control or custody, including information that have been transferred to a third party for processing, whether domestically or internationally, subject to cross-border arrangement and cooperation."* (§ 21(a))

**Practical effect:** the PIC remains the controller-of-record for personal information **even after it has been transferred to a processor or sub-processor**. There is no statutory cross-border whitelist, no SCC mechanism, no adequacy decisions — accountability follows the data.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md) (vendor DPAs), with knock-on to [02 Architecture](../../../layers/02-architecture.md) (vendor scoping, data-residency choices) and [04 Controls and processes](../../../layers/04-controls-and-processes.md) (vendor review cadence).

**Operationalisation (engineering surface):**
- Maintain a vendor inventory keyed to the personal information they touch — what categories of PI / SPI, what processing operations, in what region.
- Vendor onboarding gate: no production data flows to a vendor without (a) a signed Outsourcing Agreement / Data Sharing Agreement, (b) documented review of the vendor's controls (typically ISO 27001 / SOC 2 / NPC seal), (c) the engineering scope-of-data (which fields / which volumes) recorded.
- Annual re-baseline of every active vendor — controls drift, contracts go stale, sub-processors change.
- For processors operating outside the Philippines: the PIC remains accountable under § 21(b) and must use *"contractual or other reasonable means to provide a comparable level of protection"*. There is no exemption for popular cloud regions; the PIC owns the assessment.

## § 22 RA 10173 — Designated personnel accountable for compliance

**Rule (summary):** the PIC must designate an individual or individuals accountable for its compliance with the Act. The IRR (§ 14) operationalises this as the **Data Protection Officer (DPO)** appointment requirement, mandatory for every PIC and PIP regardless of size.

**Engineering touch-point:** the DPO is exposed to data subjects through:
- The privacy notice / privacy policy (must list a working DPO contact).
- The Data Subject Rights flow (data subject requests under § 16 must reach the DPO).
- Breach communication (the DPO is the named contact in NPC and subject notifications under § 38 IRR).

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md) (DSR flow), [06 Disclosure](../../../layers/06-disclosure.md) (privacy notice copy).

**Operationalisation (engineering surface):**
- The DPO email address (typically `dpo@<org>` or equivalent) must route to a real human inbox and not silently bounce. Pin a routing test in your release checklist.
- The DSR endpoint (web form, in-app flow, or email channel) must capture the request, attach a request ID, and create the audit-trail entry that NPC Circular 2022-04 expects to see if a complaint is filed.
- For B2B SaaS where the customer is the PIC: the customer's DPO appears on **their** users' privacy notice. Your role is to provide the platform and DSR plumbing the customer's DPO can use.

## §§ 44–45 IRR — Outsourcing and subcontract agreements

**Rule (summary):** when a PIC outsources personal information processing to a PIP, the engagement must be governed by a written contract that:
- Specifies the data processed, the purpose, and the duration.
- Requires the PIP to process only on the documented instructions of the PIC.
- Requires the PIP to implement the security measures under § 20 RA 10173 + IRR §§ 25–29.
- Requires the PIP to ensure confidentiality of staff with access.
- Requires the PIP to use sub-processors only with the PIC's prior written authorisation.
- Requires the PIP to notify the PIC of any personal data breach **without unreasonable delay** so the PIC can satisfy its own § 38 IRR notification clock.
- Requires the PIP to assist the PIC in handling data subject rights requests under § 16 RA 10173.
- Requires the PIP to delete or return personal information at the end of the engagement.
- Allows the PIC to audit the PIP's compliance.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md) (DPA template), with knock-on to [04 Controls and processes](../../../layers/04-controls-and-processes.md) (vendor review SOP).

**Operationalisation (engineering surface):**
- Vendor DPA breach-notification clause: require notification **within 24 hours** of the vendor's knowledge of, or reasonable belief in, a breach. The PIC's 72-hour clock to NPC starts on the PIC's knowledge — if the vendor sits on a breach for 60 hours, the PIC has 12 hours left.
- Vendor DPA must require operational support for DSR fulfilment — the vendor cannot be a black hole for data the customer's user has the right to access, rectify, or have erased.
- Sub-processor change notice: at least 30 days, with a customer veto right. Engineering implication: maintain a public sub-processor list and update on every change.

## § 50 IRR — Accountability for transfers

**Rule (summary):** § 50 IRR reinforces § 21 RA 10173 — the PIC is accountable for personal information transferred to a third party, **regardless of the location** of the third party. The IRR specifically requires the PIC to use *"contractual or other reasonable means to provide a comparable level of protection while the information is being processed by a third party"*.

**Practical effect:** for cross-border processing (cloud regions outside PH, SaaS vendors abroad, group-company transfers), the realistic mechanism is:
- A written Data Sharing Agreement / Outsourcing Agreement with the recipient that contractually replicates the IRR's security and rights-handling obligations.
- Documented due diligence on the recipient's controls.
- A retention / return / deletion clause that survives the engagement.

**Implementation layer:** [02 Architecture](../../../layers/02-architecture.md) (where the data lands), [01 Non-technical](../../../layers/01-non-technical.md) (the contractual machinery).

**Operationalisation (engineering surface):**
- Region-pinning is not a legal requirement under PH law (unlike some sector-specific regulations like BSP rules for banks), but it simplifies the accountability story: data that never leaves PH is straightforward; data that crosses borders triggers § 21 / § 50 documentation.
- Where the SaaS stack uses a foreign-region cloud (typical for AWS Singapore, GCP us-central1, Azure SEA, etc.): document the transfer in the vendor inventory, attach the DPA, and confirm the sub-processor list is current.

## What's at stake

- Most accountability obligations don't have a discrete penalty; the failure surfaces under another offence (e.g., a breach exposes inadequate vendor due diligence under § 21, which compounds into the § 25 / § 26 / § 30 penalties).
- **Officer liability under § 34**: where the corporate offence engages, the responsible officers (which can include the engineering manager who approved a non-compliant vendor onboarding) face the prison terms in their personal capacity. Vendor onboarding is one of the textbook scenarios where § 34 attaches.
- The audit trail (vendor inventory, DPAs, due-diligence records, sub-processor change log) is the single most useful evidence in any NPC investigation. Build it as you go, not under deadline.
