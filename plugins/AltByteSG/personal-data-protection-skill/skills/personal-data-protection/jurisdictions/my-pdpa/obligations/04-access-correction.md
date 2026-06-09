# Access, Correction, Prevention, Portability — Part II Division 4 (s30–37, s42, s43A)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Data subjects have a closed list of statutory rights against a controller. The big ones engineers ship are: access (s30–33), correction (s34–37), prevention of damaging processing (s42), and the **new (2024) data portability** right (s43A).

## s30 — Right of access

**Rule (verbatim):** *"An individual is entitled... to be informed by a data user whether personal data of which that individual is a data subject is being processed by or on behalf of the data user; and... [to be supplied with] a copy of the personal data..."*

**Practical effect:** the user can demand a copy of their personal data. Engineering implication: build a self-service export, or a manual workflow with an SLA.

**Implementation layer:** [04 Controls and processes](../../../layers/04-controls-and-processes.md), [05 Feature/UX](../../../layers/05-feature-ux.md).

**Operationalisation:**
- Self-service export: Settings > Data > Export. ZIP / JSON / CSV (any structured format the user can open). Reuse this for s43A data portability — see below.
- For data not held in the user's row (e.g., shared chat history, server-side logs containing user identifiers), document the path: what is exported, what is excluded with the basis (e.g., third-party privacy in shared chats).
- Authentication on the export request — re-prompt for password / MFA before generating, since the export is a high-value asset to an account-takeover attacker.

## s31 — Compliance with data access request

**Rule (summary):** the controller must comply with a data access request as soon as practicable and in any case **no later than 21 days** from the date of receipt. The 21-day window can be extended once by another 14 days with a written notice (s31(3)–(4)). The controller may charge a *prescribed* fee (s31(2)).

**Practical effect:** **21-day SLA**. Self-service exports trivially satisfy this. Manual workflows must hit the 21 days.

**Implementation layer:** [04 Controls and processes](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Track every access request with timestamp + status. Bake an SLA reminder at day 14.
- Fee policy: most consumer apps don't charge — make exports free to avoid the friction. The Personal Data Protection (Fees) Regulations 2013 prescribe upper limits.

## s32 — Refusal grounds

**Rule (summary):** the controller may refuse a data access request only where one of the s32 grounds applies — including: not satisfied as to the requestor's identity; the request is repetitious; disclosure would reveal personal data of another individual without their consent; disclosure would be contrary to law; the data is subject to legal professional privilege; the data was processed only for personal/family/household affairs; or the personal data cannot be located after reasonable search.

**Practical effect:** narrow grounds. "We'd rather not" is not a ground.

**Implementation layer:** [04 Controls and processes](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Identity verification step before fulfilment — required by s32(a). Re-authenticate (password + MFA, or stronger if the account has high-value data).
- Third-party data carve-out (s32(d) equivalent): when exporting shared content (chat threads, comments on others' posts), redact / placeholder-replace the other parties' personal data unless they've consented. "Deleted user" or "Anonymous" is a common pattern.

## s33 — Notification of refusal

**Rule (summary):** if the controller refuses to comply with the access request, it must, no later than 21 days from receipt, notify the requestor in writing of the refusal and the reason.

**Implementation layer:** [04 Controls and processes](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Refusal template letter prepared in advance. Reasons should cite the specific s32 paragraph.

## s34 — Right to correct personal data

**Rule (verbatim):** *"...where an individual believes that personal data... is inaccurate, incomplete, misleading or not up-to-date, the data subject may make a data correction request..."*

**Practical effect:** the user can demand correction. Most user-controlled fields (name, email, phone, address) should be self-service editable; for system-controlled fields (account status, subscription tier) the user can request and the controller decides.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md), [04 Controls and processes](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Settings > Profile: every field the user owns is editable. Email change goes through a verification step.
- For non-self-service fields, a "Request a correction" flow that opens a support ticket and routes to the DPO / support team.

## s35 — Compliance with correction request

**Rule (summary):** the controller must comply (or refuse with notice under s37) within **21 days** of receipt. After correction, the controller must take reasonable steps to inform third parties to whom the data was disclosed, where reasonable.

**Practical effect:** the **third-party-notification** part is operationally heavy. If you've shared the user's email with five processors and the user corrects it, you owe a downstream sync.

**Implementation layer:** [04 Controls and processes](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Downstream sync hooks: identity changes (email, phone, name) emit events that fan out to the inventory of processors holding that data.
- For one-shot disclosures (e.g., a marketing email already sent), "reasonable steps" likely doesn't require recall — document the reasoning.

## s36 — Refusal grounds for correction

**Rule (summary):** the controller may refuse where (a) the controller is not satisfied that the data is inaccurate / incomplete / misleading / not up-to-date; (b) the controller is not satisfied as to the requestor's identity; (c) the controller does not hold the data; or (d) the request is otherwise frivolous.

**Operationalisation:** rare in practice for consumer apps; mostly engages where the user's claimed identity disputes the controller's records (e.g., disputed credit-bureau-style data).

## s37 — Notification of correction refusal

**Rule (summary):** notify within 21 days, in writing, with reason.

## s42 — Right to prevent processing causing damage or distress

**Rule (verbatim):** the data subject may, by written notice, *"require the data user at the end of such period as is reasonable in the circumstances to cease, or not to begin, the processing or processing for a specified purpose or in a specified manner of personal data in respect of which he is the data subject, on the ground that, for specified reasons — (a) the processing of that personal data or the processing of personal data for that purpose or in that manner is causing or is likely to cause substantial damage or substantial distress to him or to another person; and (b) the damage or distress is or would be unwarranted."*

**Practical effect:** rarely invoked, but maps to "stop processing my data because it's harming me". If a user invokes it, the controller has 21 days to respond.

**Implementation layer:** [04 Controls and processes](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Receive via DPO email or support ticket. Engineering touch-point: a per-user processing-restriction flag (`processing_restricted_at` timestamp on the user record). Reads still allowed; mutations blocked or queued for review.
- A bare-bones implementation matches what TH-PDPA s34 effectively requires — see the cross-reference in [`jurisdictions/_index.md`](../../_index.md).

## s43 — Right to prevent direct marketing

Covered in [02-consent.md](02-consent.md) — the marketing toggle is the engineering surface.

## s43A (new 2024) — Right to data portability

**Rule (verbatim):** *"Subject to subsection (2), a data subject may request the data controller to transmit his personal data to another data controller of his choice directly by giving a notice in writing by way of electronic means to the data controller."* (s43A(1)). *"The request for data portability... is subject to technical feasibility and compatibility of the data format."* (s43A(2)). *"Upon receiving the request..., the data controller shall complete the transmission of personal data within the period as may be prescribed."* (s43A(3))

**Practical effect:** the user can ask you to send their data to a competitor / replacement service. Two outs: **technical feasibility** and **format compatibility**. The "period as may be prescribed" is to be set by subordinate regulation — until that's published, treat the s31 21-day SLA as a sensible operational default.

**Implementation layer:** [04 Controls and processes](../../../layers/04-controls-and-processes.md), [05 Feature/UX](../../../layers/05-feature-ux.md).

**Operationalisation:**
- Reuse the s30 export. The portability format should be **structured, commonly used, and machine-readable** — JSON is the safe choice. Avoid bespoke binary formats.
- Receive the request in writing by electronic means (per the statute) — DPO email or a dedicated form. Verify the user's identity, and verify (where reasonable) the destination controller's identity / endpoint.
- Direct transmission: the statute says *"transmit... directly"*. A user-mediated download-and-upload is not technically "direct" but is a defensible fallback where direct isn't feasible. Document the choice.
- Technical feasibility carve-out (s43A(2)): if the destination controller cannot accept the format you produce, you've discharged the obligation by offering a feasible format. Don't use this as a gate to refuse — be cooperative, and document.
- Until the prescribed period is gazetted, default SLA = 21 days, the same as s31 access.

## What's at stake

- **Access / correction / portability / prevention breach (s30–37, s42, s43A)** all surface under **s5(2)**: RM 1,000,000 / 3 years for principle breach. The Access Principle (s12) is the catch-all.
- The 21-day SLA is the most-tested operational metric. Self-service exports + a per-user request log are the cleanest evidence.
- Data portability is **new** and unproven in enforcement; expect the regulator to start with structural questions (do you have a process? a published format?) before substantive ones (was your specific transmission timely? compatible?).
