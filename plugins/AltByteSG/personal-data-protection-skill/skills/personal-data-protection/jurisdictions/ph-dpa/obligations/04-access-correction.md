# Data Subject Rights — § 16 RA 10173 + § 34 IRR + NPC Circular 18-01 + NPC Circular 2022-04

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

PH grants the data subject **eight rights**: informed, access, object, rectification, erasure / blocking, damages, complaint (RA 10173 § 16), and **data portability** (NPC Circular 18-01). NPC Circular 2022-04 sets the operational rules — including the **15-day default response window**.

## § 16(a) — Right to be informed

**Rule (verbatim):** the data subject has the right *"to be informed whether personal information pertaining to him or her shall be, are being or have been processed."*

**Practical effect:** the active limb is the privacy notice (covered in [03-purpose.md](03-purpose.md)). The passive limb is the data subject's right to ask whether the PIC holds personal information about them.

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md) (notice), [04 Controls and processes](../../../layers/04-controls-and-processes.md) (DSR endpoint).

**Operationalisation:**
- The DSR endpoint must accept "do you hold data about me?" as a request type. Most engineering implementations bundle this with the access right — a single "request my data" flow returns both the confirmation and the data export.

## § 16(b) — Right to object

**Rule (verbatim):** the data subject has the right *"to object to the processing of his or her personal information, including processing for direct marketing, automated processing or profiling."*

**Practical effect:** the right to object can be exercised at any time. The PIC must stop processing for the objected-to purpose unless it can demonstrate compelling legitimate grounds that override the data subject's interests, OR the processing is for the establishment, exercise, or defense of legal claims.

**For direct marketing**, the right to object is **absolute** — the PIC must stop, no balancing.

**For automated decision-making and profiling**, the right to object is the operational counterpart to the disclosure obligation under § 16 + § 34(a) IRR.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md) (Settings toggles), [04 Controls and processes](../../../layers/04-controls-and-processes.md) (mutation paths check live state).

**Operationalisation:**
- Settings screen split: transactional notifications (always on, contract necessity under § 12(b)) vs marketing notifications (opt-in, withdrawable absolutely under § 16(b)).
- Marketing send pipeline reads the live opt-out state at send time, not at signup time. Failed unsubscribes are the textbook § 16(b) + § 32 (unauthorised disclosure to a recipient who has objected) violation pattern.
- Automated decision-making opt-out: provide a fall-through path to a human-reviewed decision where the user objects to automated processing with significant effect.
- The opt-out must take effect within the **15-day NPC Circular 2022-04 window** — operationally, treat digital toggles as immediate; downstream pipeline flushes (analytics warehouses, ML feature stores, partner integrations) within 15 days.

## § 16(c) — Right of access

**Rule (verbatim):** the data subject has the right *"to reasonable access to, upon demand"* — the contents, sources, names of recipients, manner by which the data was processed, reasons for disclosure to recipients (if any), retention period, manner the data subject can exercise their rights, and whether automated decision-making is in use.

**Practical effect:** an access request returns more than just the data. It returns a **report**: data + provenance + recipients + retention + rights mechanics.

**Implementation layer:** [04 Controls and processes](../../../layers/04-controls-and-processes.md), [05 Feature/UX](../../../layers/05-feature-ux.md).

**Operationalisation:**
- Access endpoint returns: the data itself (in a readable / portable format), source of the data (signup, third-party login, partner integration), recipients (vendors, sub-processors, sharing partners), processing manner (purpose + lawful basis labels), retention rule, and links to the rectification / erasure / object surfaces.
- Identity verification before fulfilment: balance the user's right against the risk of unauthorised disclosure (which is itself a § 32 offence). Strong authentication tier — re-auth, MFA, or out-of-band verification — for sensitive datasets.
- Default response window: **15 calendar days** (NPC Circular 2022-04 § 11), extendable once by 15 days for complex requests.
- Free of charge for the first request in a reasonable period; reasonable fee for repetitive or excessive requests.

## § 16(d) — Right to rectification

**Rule (summary):** the data subject has the right *"to dispute the inaccuracy or error in the personal information and have the personal information controller correct it immediately and accordingly, unless the request is vexatious or otherwise unreasonable."*

**Practical effect:** users can correct their own data. The PIC must propagate the correction to recipients, where reasonably practical.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md), [04 Controls and processes](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Profile / Settings surface for self-rectification of name, contact, address, etc.
- For data the user cannot self-edit (audit trails, transaction records), provide a request channel that creates a rectification audit record alongside the original.
- Propagate corrections to vendors and sub-processors per the DPA flow-down. Most propagation can be batched (daily delta sync) rather than immediate, unless the data drives a real-time decision (e.g., delivery address for an in-flight order).
- 15-day NPC Circular 2022-04 window applies.

## § 16(e) — Right to erasure or blocking

**Rule (summary):** the data subject has the right *"to suspend, withdraw or order the blocking, removal or destruction of his or her personal information"* upon discovery and substantial proof that:
- The personal information is incomplete, outdated, false, or unlawfully obtained.
- It is being used for purposes not authorised by the data subject.
- The data is no longer necessary for the purposes for which it was collected.
- The data subject withdraws consent or objects to the processing.
- The personal information concerns private information that is prejudicial to the data subject (unless justified by freedom of speech or constitutional rights).
- The processing is unlawful.
- The PIC or PIP violated the rights of the data subject.

**Practical effect:** PH framing distinguishes **erasure** (destruction) from **blocking** (suspending further processing while retaining the record). The user can request either; the PIC chooses the appropriate response based on the trigger.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md), [04 Controls and processes](../../../layers/04-controls-and-processes.md), [03 Data model](../../../layers/03-data-model.md).

**Operationalisation:**
- Account deletion flow: hard-delete + "Deleted User" attribution for shared content (chat history, comments) where retention is required for the integrity of the shared resource.
- Where erasure is constrained by legal-obligation retention (tax records, AML), apply **blocking** — mark the record as restricted, suspend further processing, retain only what the law requires. The IRR contemplates this distinction.
- Schema: a `deletion_state` column with values `active | blocked | deleted_pending_purge | purged`. The sweep job moves records through the states as the legal-retention window expires.
- Vendor flow-down: propagate erasure / blocking instructions to processors. The vendor DPA should require the vendor to honour the instruction within an agreed window.

## § 16(f) — Right to data portability (operative via NPC Circular 18-01)

**Rule (NPC Circular 18-01):** the data subject has the right to obtain from the PIC a copy of the personal information undergoing processing in an *"electronic or structured format that is commonly used and allows for further use by the data subject."* The right applies where the processing is based on consent or contract and is carried out by automated means.

**Practical effect:** an export endpoint returning the user's data in a machine-readable format. Unlike MY § 43A, PH does not include direct controller-to-controller transmission as a default — the user receives the export, not a direct transfer.

**Implementation layer:** [04 Controls and processes](../../../layers/04-controls-and-processes.md), [05 Feature/UX](../../../layers/05-feature-ux.md).

**Operationalisation:**
- Export format: JSON or CSV, ZIP-bundled where the dataset is multi-table. Proprietary blobs don't satisfy "commonly used and structured".
- Scope of the export: data the data subject **provided to** the PIC + data **observed about** the data subject — not derived data (analytics scores, ML features) where derivation is the PIC's intellectual contribution.
- 15-day NPC Circular 2022-04 window applies.
- Identity verification before delivery (export is a high-risk surface for impersonation attacks).

## § 16(g) — Right to damages

**Rule (verbatim):** the data subject has the right *"to be indemnified for any damages sustained due to such inaccurate, incomplete, outdated, false, unlawfully obtained or unauthorized use of personal information."*

**Practical effect:** **PH grants a direct civil cause of action**. The data subject can claim civil indemnity directly from the PIC for damages caused by non-compliant processing — separate from, and in addition to, the criminal penalties under §§ 25–37.

**Implementation layer:** primarily legal / dispute-resolution; the engineering touch-point is the audit trail (consent records, processing logs, change history) that supports the PIC's defence.

**Operationalisation:** every consent grant, every withdrawal, every rectification, every erasure / blocking action should produce an audit-trail entry that survives. This is the evidence in any civil claim or NPC complaint.

## § 16(h) — Right to file a complaint

**Rule (summary):** the data subject can file a complaint with the NPC (under the NPC Rules of Procedure). The PIC must **disclose the complaint mechanism** in the privacy notice and the DSR flow.

**Operationalisation:** privacy notice + DSR surface lists both the PIC's internal complaint channel (DPO contact) AND the NPC complaint channel ([privacy.gov.ph/complaints](https://privacy.gov.ph/complaints-assisted/)). Both are required disclosures.

## NPC Circular 2022-04 — Operational rules for exercising rights

The Circular sets the binding operational rules:

| Item | Rule |
|---|---|
| Default response window | **15 calendar days** from receipt of a verifiable request |
| Extension | Once by 15 days, with notice to the data subject explaining why |
| Form of request | Any written / electronic form; the PIC cannot impose unreasonable formal requirements |
| Identity verification | Must be reasonable and proportionate; cannot be used to obstruct |
| Free of charge | First request in a reasonable period is free; reasonable fee for repetitive / manifestly excessive requests |
| Refusal grounds | Limited and must be justified in writing to the data subject |
| Audit trail | The PIC must keep a record of every request, action taken, and response delivered |

**Implementation layer:** [04 Controls and processes](../../../layers/04-controls-and-processes.md), [05 Feature/UX](../../../layers/05-feature-ux.md).

**Operationalisation:**
- DSR ticketing system (or equivalent) keyed by request ID. Each ticket records: data subject identity, request type, receipt timestamp, identity-verification step + result, action taken, response delivered, supporting evidence.
- 15-day SLA encoded as a hard deadline in the ticket workflow. Auto-escalate on day 10.
- Refusal template: must state the legal ground (e.g., the request is part of journalism / research / criminal investigation per § 19 RA 10173) and the data subject's right to complain to the NPC.

## What's at stake

- **§ 16(g) civil claim**: the direct civil-damages route is unique to PH among the four SEA jurisdictions covered here. Quantum is determined by the court; high-profile PH NPC cases have carried six-figure peso awards.
- **§ 32 — unauthorised disclosure**: where a DSR is fulfilled to the wrong person (impersonation through weak identity verification), the disclosure itself becomes the offence. 1 to 5 years prison + ₱500k–₱2M.
- **§ 25 — unauthorised processing**: where the PIC continues processing after a valid object / withdrawal, the post-objection processing is unauthorised. 1 to 3 years + ₱500k–₱2M (PI); 3 to 6 years + ₱500k–₱4M (SPI).
- **§ 34 — officer liability**: where the corporate offence engages, the responsible officers face the prison terms personally.

The DSR audit trail is the single most useful evidence in any NPC complaint. Build the request-ticketing surface early.
