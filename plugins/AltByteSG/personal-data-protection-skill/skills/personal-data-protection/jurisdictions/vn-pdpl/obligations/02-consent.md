# Consent and Lawful Processing — Điều 9, 10, 19

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.
>
> **Unofficial translation.** Law 91/2025/QH15 and Decree 356/2025/NĐ-CP have no official
> English version. English wording below is the maintainer's rendering of the Vietnamese;
> load-bearing terms carry the original. **In any conflict the Vietnamese wins.** See the
> translation caveat in [README.md](../README.md).

Vietnam does not offer a GDPR-style menu of lawful bases. **Consent is the rule** (Điều 9), and Điều 19 lists the closed set of cases where processing may proceed without it. Điều 10 governs withdrawal and restriction.

## Điều 9 — Consent of the data subject

**Rule:** consent is the data subject permitting the processing of their own personal data, unless the law provides otherwise (Điều 9(1)).

Consent is valid **only** where it is voluntary and the subject knows (Điều 9(2)):

- a) the **types** of personal data processed and the **purpose** of processing
- b) the **controller**, or controller-and-processor
- c) the **rights and obligations** of the data subject

**Form (Điều 9(3)):** consent must be expressed by a clear, specific method that can be **printed or copied in writing**, including electronic or **verifiable** formats. Detail is delegated to the Government (Điều 9(5)).

**Principles (Điều 9(4)) — these are the engineering constraints:**

- a) **Consent is per purpose.** One record per purpose, not one flag per user.
- b) **No bundling.** Consent must not be conditioned on also agreeing to purposes outside the agreed content.
- c) **Consent persists** until the subject changes it or the law provides otherwise.
- d) **Silence or non-response is not consent.** No pre-ticked boxes, no implied opt-in.

**Operationalisation:**

- One row per (subject, purpose) with timestamp, method, and the notice version shown — Điều 9(3)'s "printable or copyable" and "verifiable" requirements mean a boolean column is not enough; you must be able to reproduce what was agreed to.
- Store the notice text or a content hash alongside the record. "Verifiable" implies you can demonstrate *what* was consented to, not just that a click happened.
- Separate toggles per purpose, all defaulting to **off** (Điều 9(4)(d)).

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md), [03 Data model](../../../layers/03-data-model.md).

## Điều 10 — Withdrawal of consent and restriction of processing

**Rule:** the subject may withdraw consent, and may **request restriction** of processing where they doubt the scope or purpose of processing, or the accuracy of the data (Điều 10(1)) — except in the Điều 19 cases or where the law provides otherwise.

- **Form (Điều 10(2)):** the request must be **in writing**, including electronic or verifiable formats, and sent to the controller or controller-and-processor.
- **Effect (Điều 10(3)):** the controller receives and performs the request, and must require its **processors** to perform it too, within the period prescribed by law.
- **Not retroactive (Điều 10(4)):** withdrawal and restriction do not apply to processing carried out **before** the request.

**Operationalisation:**

- Withdrawal must fan out to sub-processors, not just flip a local flag — Điều 10(3) puts that propagation duty on you. Your DPA needs a matching flow-down clause.
- Restriction is a **state**, not a deletion: the record stays but further processing stops. Mutation paths must check it. This mirrors TH s34 and ID Pasal 41.
- Because withdrawal is not retroactive, do not retro-delete derived artefacts on withdrawal unless a separate deletion right applies — but do stop further use.

**Implementation layer:** [04 Controls](../../../layers/04-controls-and-processes.md), [03 Data model](../../../layers/03-data-model.md).

## Điều 19 — Processing without consent

Điều 19 sets the closed list of situations where personal data may be processed **without** the subject's consent. It is also the carve-out referenced by Điều 10(1), so a withdrawal or restriction request does not defeat processing that rests on an Điều 19 ground.

**Engineering consequence:** if a processing activity relies on Điều 19 rather than consent, record *which* ground, in the same place you record consent. When a withdrawal request arrives you need to answer, per purpose, whether that purpose was consent-based (stop) or Điều 19-based (continue, and tell the subject why).

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md), [06 Disclosure](../../../layers/06-disclosure.md).

## Cross-jurisdiction note

Vietnam's per-purpose, no-bundling, no-silence rules land close to **ID Pasal 22** in strictness. If you already satisfy Indonesia's form-of-consent requirements, the VN gap is usually the **verifiable format** obligation in Điều 9(3) and the **processor fan-out** duty in Điều 10(3).
