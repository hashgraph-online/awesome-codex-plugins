# Data Subject Rights — Điều 4, 13, 14, 15, 17

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.
>
> **Unofficial translation.** Law 91/2025/QH15 and Decree 356/2025/NĐ-CP have no official
> English version. English wording below is the maintainer's rendering of the Vietnamese;
> load-bearing terms carry the original. **In any conflict the Vietnamese wins.** See the
> translation caveat in [README.md](../README.md).

Điều 4 enumerates the rights; Điều 13–17 give the operative mechanics for correction, deletion, provision and transfer.

## Điều 4(1) — Rights of the data subject

- a) To **know** about the processing of their personal data
- b) To **consent or refuse**, and to request **withdrawal** of consent
- c) To **view, correct, or request correction** of their personal data
- d) To request **provision**, **deletion**, or **restriction** of processing; and to submit an **objection** to processing
- đ) To **complain, denounce, sue**, and claim **compensation** under the law
- e) To require the competent authority, or parties involved in processing, to apply protection measures

**Note the shape:** viewing and correction sit together in (c), and provision, deletion, restriction and objection sit together in (d). The right to **object** is explicit — unlike SG and MY, where it is only implicit via consent withdrawal.

Điều 4(2) also imposes **duties on the subject** (protect their own data, respect others', provide accurate data, comply with the law) — unusual among the regimes in this skill, and Điều 4(3)(b) bars the subject from obstructing the controller's lawful performance. This does not reduce your obligations; it is context for disputes.

Điều 4(4) requires organisations to **facilitate** the exercise of rights and not obstruct it.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md), [04 Controls](../../../layers/04-controls-and-processes.md).

## Điều 13 — Correction of personal data

Build a self-service edit surface where the field allows it, and a documented channel where it does not.

**Two traps:**

- **Corrections must reach derived copies.** A corrected name that stays wrong in the search index, the analytics warehouse or a vendor's records is still wrong. Decide per field whether correction propagates or the derived copy is regenerated.
- **Correction and restriction interact.** Điều 10(1) lets a subject request restriction precisely because they doubt the data's **accuracy** — so a disputed field may need to be frozen rather than silently overwritten while the dispute is open.

## Điều 14 — Deletion, destruction, de-identification

Điều 14 is the longest of this group and covers all three disposal routes. Read with **Điều 2(1)**: once de-identified, the data is **no longer personal data**, which makes de-identification a genuine exit from scope rather than a risk-reduction measure.

**Operationalisation:** account deletion should decide, per table, between hard deletion, destruction, and de-identification — and de-identification must be irreversible, because **Điều 7 prohibits re-identification**.

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md), [07 Operational](../../../layers/07-operational.md).

## Điều 15 — Provision of personal data

The export must cover **all** personal data held about the subject, which in Vietnam is a wider set than engineers usually assume: Decree Điều 3(11) makes any identifying field basic personal data by default, so anything keyed to the user is in scope unless it has been de-identified.

**Practical consequence:** the export path is the single thing most likely to silently fall out of date. Every new column, event stream or vendor-held record is in scope from the day it exists. Treat "is it in the export?" as a required review item on any migration adding a user-keyed field — [`new-data-field.md`](../../../checklists/new-data-field.md) step 4 covers this.

Behaviour-tracking events are **sensitive** under Decree Điều 4(1)(l), so analytics data is both exportable and subject to the Điều 4(2) access controls — the export path itself needs to be an access-controlled surface.

## Điều 17 — Transfer of personal data

Transfer between parties **within Vietnam**. Distinct from Điều 20, which governs transfer across the border — only Điều 20 carries the 60-day filing duty.

**Check which one you are doing before designing the flow.** The test is not who the counterparty is but where the processing happens: handing data to a Vietnamese company that processes it on infrastructure outside Vietnam is a **cross-border** transfer under Điều 20(1)(c), not a domestic one under Điều 17.

**Implementation layer:** [02 Architecture](../../../layers/02-architecture.md).
