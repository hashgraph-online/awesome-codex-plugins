# BAB IV — Data Subject Rights (Pasal 5–15) + Operational Windows (Pasal 30, 32, 40, 41, 43)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

UU PDP grants 9 data subject rights. Each must be supported by the Controller; refusals require recorded reasons.

## Pasal 5 — Right to information about the Controller

**Rule:** the Data Subject has the right to receive Information about:
- The identity of the Controller
- The legal interest basis for processing
- The purpose of the request and use of Personal Data
- Accountability of the party requesting the data

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md) (privacy policy + at-collection notices).

## Pasal 6 — Right to correction

**Rule:** the Data Subject has the right to **complete, update, and/or correct errors and/or inaccuracies** in their Personal Data.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md) (self-service edit), [04 Controls](../../../layers/04-controls-and-processes.md).

**Operational window:** the Controller must act on the request **within 3 × 24 hours (72 hours)** per Pasal 30, AND notify the Subject of the result.

## Pasal 7 — Right to access + obtain copy

**Rule:** the Data Subject has the right to **access and obtain a copy** of their Personal Data.

**Implementation layer:** [04 Controls](../../../layers/04-controls-and-processes.md).

**Operational window:** the Controller must provide access **within 3 × 24 hours (72 hours)** per Pasal 32(2).

The access response must include the **processing trail** (rekam jejak pemrosesan) — i.e. who has accessed / used the data and how, within the retention period.

## Pasal 8 — Right to end processing, erasure, and destruction

**Rule:** the Data Subject has the right to **terminate processing**, **erase**, and/or **destroy** their Personal Data.

**Implementation layers:** [04 Controls](../../../layers/04-controls-and-processes.md), [05 Feature/UX](../../../layers/05-feature-ux.md) (delete-account flow).

**Operational details:**
- Pasal 42: Controller must end processing when retention met, purpose achieved, or Subject requests
- Pasal 43: Controller must erase Personal Data on 4 grounds (no longer needed, consent withdrawn, Subject requests, unlawfully processed)
- Pasal 44: Controller must destroy Personal Data on 4 grounds (similar)

The split between erasure and destruction reflects archival practice: erasure removes from active systems; destruction is permanent (more applicable to physical records or backups).

## Pasal 9 — Right to withdraw consent

**Rule:** the Data Subject has the right to **withdraw consent** previously given.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md) (settings toggles), [03 Data model](../../../layers/03-data-model.md) (consent log).

**Operational window:** Pasal 40(2) — processing must stop **within 3 × 24 hours (72 hours)** of the consent withdrawal request. This propagates to:
- Database state (notification flag flipped, etc.)
- Sub-processors (push provider de-registered, OAuth tokens revoked)
- Future scheduled jobs

## Pasal 10 — Right to object to automated decision-making

**Rule:** the Data Subject has the right to **object to decisions based solely on automated processing, including profiling**, that produce legal effects or significantly affect the Subject.

This is **explicit and standalone** — comparable to GDPR Article 22.

**Implementation layers:** [04 Controls](../../../layers/04-controls-and-processes.md) (object-to-automation mechanism), [05 Feature/UX](../../../layers/05-feature-ux.md) (UI to invoke).

**Operationalisation:** for any feature that takes automated decisions (pricing, content moderation, recommendation that affects access, scoring, etc.) with legal or significant impact, you need:
- A way for the Subject to object
- Either human review on objection, OR a different processing path for objecting users
- Documented limits on what counts as "significant impact" (PP refines this)

## Pasal 11 — Right to suspend or restrict processing

**Rule:** the Data Subject has the right to **suspend or restrict processing** of Personal Data, in accordance with the purpose of processing.

**Implementation layers:** [04 Controls](../../../layers/04-controls-and-processes.md) (restriction state + read-path enforcement), [05 Feature/UX](../../../layers/05-feature-ux.md) (Settings toggle).

**Operational window:** Pasal 41 — Controller must comply **within 3 × 24 hours (72 hours)**.

**Exceptions to compliance** (Pasal 41(2)):
a. Other laws require continued processing
b. Suspension would endanger others' safety
c. A written contract with the Subject prevents suspension

The Controller must **notify the Subject** when the suspension/restriction is in force.

**Compared to other jurisdictions:**
- Singapore PDPA: no equivalent right — would require building net-new code if launching in SG and re-using for ID
- Thailand PDPA s34: equivalent right — same code mechanism works for both

## Pasal 12 — Right to sue for damages

**Rule:** the Data Subject has the right to **sue and receive damages** for violations.

Procedural — relevant during litigation, not a UX feature. But note that this exists; it changes the risk calculus when designing high-impact processing.

## Pasal 13 — Right to data portability

**Rule:** the Data Subject has the right to:

(1) **Obtain or use** their Personal Data from the Controller in a format aligned with the structure / format commonly used or readable by electronic systems
(2) **Have the data sent or transferred** to another Controller, when the systems involved can communicate securely

**Implementation layer:** [04 Controls](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Same as the access endpoint (Pasal 7) but with explicit machine-readable format requirement (JSON / CSV)
- Optional: an interface to push data directly to another Controller (rare in consumer apps)
- The "secure inter-system communication" qualifier limits the practical scope — most apps satisfy by providing a downloadable JSON the user can manually upload elsewhere

## Pasal 14 — How to exercise rights

**Rule:** the Subject exercises rights under Pasal 6–11 via a **recorded request** (written or electronic), submitted to the Controller.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md) (in-app request channels), [04 Controls](../../../layers/04-controls-and-processes.md) (admin-side intake).

In-app self-service satisfies "recorded electronic request." Email also works.

## Pasal 15 — Exceptions to Subject rights

**Rule:** the rights under **Pasal 8 (end processing / erasure), 9 (withdraw consent), 10(1) (object to automated decision-making), 11 (suspend / restrict), and 13 (portability)** are **excluded** for:

a. National defence and security
b. Law enforcement
c. Public administration in the interest of the state
d. Financial-sector supervision (banking, monetary, payment, financial-system stability) for state interests
e. Statistical and scientific research

The exceptions apply only when implementing law (Pasal 15(2)).

**Implementation note:** the rights to **information (Pasal 5), correction (Pasal 6), access (Pasal 7), legal action (Pasal 12), and on-demand information (Pasal 14)** are NOT subject to these exceptions — those are absolute.

## Operational summary — the 72-hour SLAs

| Right | Pasal | Window |
|---|---|---|
| Correction | 30 | 72 hours from request |
| Access (incl. processing trail) | 32 | 72 hours from request |
| Stop processing on consent withdrawal | 40 | 72 hours from withdrawal |
| Suspend / restrict processing | 41 | 72 hours from request |

Four parallel 72-hour SLAs is operationally aggressive. Customer-support / engineering must:
- Triage incoming requests fast (target: same business day)
- Have automation paths for the common cases (self-service edit; settings-toggle effect)
- Have admin-mediated escalation paths for the rest with sub-72-hour latency

## Penalty exposure (this Part)

Failures across the access/correction/restriction/erasure obligations all carry administrative sanctions per Pasal 57 — ceiling 2% of annual revenue. See [07-offences.md](07-offences.md).
