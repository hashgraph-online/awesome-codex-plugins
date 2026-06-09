# BAB VI — Controller / Processor Obligations + DPO + Records (Pasal 19–54)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

## Pasal 19 — Who is bound

Data Controllers (Pengendali Data Pribadi) and Data Processors (Prosesor Data Pribadi) include:
a. Any Person (Setiap Orang)
b. Public Bodies (Badan Publik)
c. International Organisations (Organisasi Internasional)

UU PDP applies broadly across the public and private sectors.

## Pasal 20 — Lawful basis required

**Rule:** the Data Controller must have a lawful basis for processing.

**The 6 bases (Pasal 20(2)):**
a. Explicit consent of the Data Subject for one or more specific purposes notified by the Controller
b. Performance of a contract to which the Data Subject is a party, or pre-contractual steps at the Data Subject's request
c. Compliance with a legal obligation
d. Protection of vital interests of the Data Subject
e. Performance of a public-interest task or exercise of authority vested in the Controller
f. Legitimate interests, balanced against the Data Subject's rights

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md), [06 Disclosure](../../../layers/06-disclosure.md).

See [02-consent.md](02-consent.md) for depth on each basis.

## Pasal 22 — Consent must be in writing

**Rule:** consent for personal data processing must be **written or recorded** — may be electronic or non-electronic, both have equal legal force. When the consent request includes other purposes, the consent request must:

a. Be clearly distinguishable from other matters
b. Be in an understandable and easily accessible format
c. Use simple and clear language

Consent failing these requirements is **null and void** (Pasal 22(5)).

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md).

## Pasal 24 — Burden of proof on Controller

**Rule:** the Data Controller must be able to **demonstrate** that consent was given by the Data Subject.

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md) (consent record).

## Pasal 27, 28 — Core processing duties

The Controller must process Personal Data:
- **Limited and specific, lawful, and transparent** (Pasal 27)
- **Consistent with the notified purpose** (Pasal 28)

## Pasal 29 — Accuracy

The Controller must ensure accuracy, completeness, and consistency of Personal Data, including verification.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md) (self-service edit), [04 Controls](../../../layers/04-controls-and-processes.md) (verification flows).

## Pasal 30 — Correction within 72 hours

**Rule:** the Controller must update or correct errors / inaccuracies in Personal Data **within 3 × 24 hours** (72 hours) from receiving the Data Subject's request, AND notify the Data Subject of the result.

**Implementation layer:** [04 Controls](../../../layers/04-controls-and-processes.md), [05 Feature/UX](../../../layers/05-feature-ux.md).

**Operationalisation:** customer-support workflow must guarantee a 72-hour cycle. For self-service edits, any latency is on the user. For admin-mediated corrections, dispatch + execution + verification all need to fit inside the window.

## Pasal 31 — Records of Processing Activities

**Rule:** the Controller must keep **records of all Personal Data processing activities**.

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md), [04 Controls](../../../layers/04-controls-and-processes.md).

The Act itself is brief on what the records must contain — the implementing Government Regulation (PP) provides the detailed schema. Verify current PP text at [peraturan.go.id](https://peraturan.go.id). At minimum, expect to record: data categories, purposes, retention, recipients, security measures, source, lawful basis.

## Pasal 32 — Access within 72 hours

**Rule:** the Controller must provide the Data Subject with access to processed Personal Data + the **processing trail** (rekam jejak), within **3 × 24 hours** (72 hours) of the access request.

**Implementation layer:** [04 Controls](../../../layers/04-controls-and-processes.md).

Same operational pressure as Pasal 30 — 72-hour SLA must be designed in.

## Pasal 33 — Permitted refusals

The Controller **must refuse** access or change requests where:
a. It would endanger the safety, physical or mental health of the Data Subject or others
b. It would impact disclosure of Personal Data of others
c. It conflicts with national defence and security interests

## Pasal 34 — Mandatory DPIA for high-risk processing

**Rule:** the Controller must conduct a **Data Protection Impact Assessment** (penilaian dampak Pelindungan Data Pribadi) when the processing has high risk to the Data Subject. **Seven trigger criteria (Pasal 34(2)):**

a. Automated decision-making with legal effect or significant impact
b. Processing of "specific" (sensitive) Personal Data
c. Large-scale Personal Data processing
d. Systematic evaluation, scoring, or monitoring of Data Subjects
e. Data matching or combining
f. Use of new technologies in processing
g. Processing that limits the exercise of Data Subject rights

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md) (DPIA documentation).

**Compared to GDPR Art. 35:** very similar shape — same conceptual list of triggers, same "high risk" framing.

## Pasal 35–39 — Security obligations

| Pasal | Obligation |
|---|---|
| 35 | Implement technical and operational measures to protect Personal Data; level proportionate to data sensitivity and risk |
| 36 | Maintain confidentiality |
| 37 | Supervise all parties processing data under the Controller's control |
| 38 | Protect Personal Data from unlawful processing |
| 39 | Prevent unauthorized access — through reliable security systems for processed data and electronic systems |

**Implementation layers:** [02 Architecture](../../../layers/02-architecture.md), [04 Controls](../../../layers/04-controls-and-processes.md).

## Pasal 40 — Stop processing on consent withdrawal (72h)

**Rule:** the Controller must stop processing **within 3 × 24 hours** (72 hours) when the Data Subject withdraws consent.

## Pasal 41 — Suspend / restrict processing (72h)

**Rule:** the Controller must suspend or restrict processing (in whole or in part) **within 3 × 24 hours** (72 hours) of the Data Subject's request, unless:
- Other laws require continued processing
- Suspension would endanger others' safety
- A written contract benefiting the Data Subject prevents suspension

The Controller must notify the Data Subject when suspension/restriction is in force.

**Implementation layer:** [04 Controls](../../../layers/04-controls-and-processes.md) (restriction state + read-path enforcement), [05 Feature/UX](../../../layers/05-feature-ux.md) (Settings toggle).

## Pasal 42 — End processing on retention met / purpose achieved / subject request

**Rule:** the Controller must end processing when:
a. Retention period reached
b. Purpose achieved
c. Subject requests it

## Pasal 43 — Erasure obligation (4 grounds)

The Controller must erase Personal Data when:
a. No longer needed for the original purpose
b. Subject has withdrawn consent
c. Subject requests it
d. Data was unlawfully obtained or processed

## Pasal 44 — Destruction obligation

Destruction (more permanent than erasure — physical destruction of records) required when:
a. Retention period reached AND archive schedule indicates destruction
b. Subject requests it
c. Not related to ongoing legal proceedings
d. Data was unlawfully obtained / processed

## Pasal 45 — Notify subject of erasure / destruction

After erasure or destruction, the Controller must notify the Data Subject.

## Pasal 46 — Breach notification (72 hours)

See [06-breach-notification.md](06-breach-notification.md).

## Pasal 47 — Accountability

**Rule:** the Controller must be **responsible for processing** AND **demonstrate accountability** in implementing the Personal Data protection principles.

This is the broad accountability obligation — equivalent to GDPR Article 5(2). Operationalised through documentation, governance records, training records.

## Pasal 48 — M&A / dissolution notice

When the Controller (as a legal person) undergoes merger, demerger, takeover, consolidation, or dissolution, the Controller must **notify the Data Subject of the data transfer**, both **before and after** the transaction.

## Pasal 49 — Comply with regulator orders

Both Controller and Processor must comply with orders from the regulator (lembaga) issued under UU PDP.

## Pasal 50 — Exceptions (national security, law enforcement, public administration)

Specific Controller obligations (correction, access, confidentiality, retention end, erasure, destruction, breach notification) are **exempted** for:
a. National defence and security
b. Law enforcement processes
c. Public administration in the interest of the state
d. Financial-sector supervision (banking, monetary, payment systems, financial stability) carried out for the state

These exceptions apply only when implementing law.

## Pasal 51–52 — Data Processor obligations

**Pasal 51:** Processor must process **based on Controller's instructions**.

**Critical (Pasal 51(6)):** if the Processor processes data **outside the Controller's instructions**, **the Processor is treated as the Controller** for that processing — taking on full liability.

**Pasal 52:** specific Controller obligations (Pasal 29, 31, 35, 36, 37, 38, 39 — accuracy, records, security, confidentiality, supervision, unlawful-processing protection, unauthorized-access prevention) **also apply directly to the Processor**.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md) (DPA terms), [04 Controls](../../../layers/04-controls-and-processes.md) (sub-processor dispatch).

## Pasal 53 / 54 — DPO (engineering touch-points)

DPO designation is required where processing is for public-interest purposes, where core activities require large-scale regular and systematic monitoring, or where core activities consist of large-scale processing of "specific" (sensitive) Personal Data or criminal-records data — same structure as GDPR Article 37(1)(b)/(c). DPO qualifications, internal-vs-external sourcing, and the full Pasal 54 duties (inform/advise, monitor, advise on DPIA, act as contact) are governance — see [01 Non-technical](../../../layers/01-non-technical.md).

**Engineering surface:**

- Published DPO contact in the privacy notice — the email address must route to a real human and not silently bounce.
- DPO needs read access to the Pasal 31 records-of-processing inventory and to audit logs to perform Pasal 54(b) monitoring duties — wire those reads on day one.
- For Pasal 34 DPIA workflows, the DPO is the sign-off owner; the DPIA artefact (purpose, categories, risk, mitigation) lives next to the feature in a documented location the DPO can reach.

## Penalty exposure (this Part)

| Failure | Triggers | Source |
|---|---|---|
| Most controller and processor duty failures | Administrative sanctions per Pasal 57 | Pasal 57 |
| Administrative fine ceiling | **2% of annual revenue** | Pasal 57(3) |

See [07-offences.md](07-offences.md) for the full administrative + criminal penalty matrix.
