# Accountability — s12A (new 2024) and Codes of Practice (s23–29)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Accountability obligations under MY PDPA are largely **non-engineering** (DPO designation, code-of-practice registration, vendor contracts) — but the engineering touch-points are real: a registered DPO contact has to be reachable, the audit trail underpins any "due diligence" defence under s133, and applicable codes of practice can prescribe specific technical controls.

## s12A (new 2024) — Appointment of Data Protection Officer

**Rule (verbatim):** *"A data controller shall appoint one or more data protection officers who shall be accountable to the data controller for the compliance with this Act."* (s12A(1)). Where a processor processes on behalf of a controller, *"the data processor shall appoint one or more data protection officers"* (s12A(2)). The controller *"shall notify the Commissioner on the appointment of data protection officer in the manner and form as determined by the Commissioner"* (s12A(3)).

**Practical effect:** DPO appointment is **mandatory** post-1 June 2025. The JPDP DPO Appointment Guideline (25 February 2025, effective 1 June 2025) sets the practical threshold for which organisations must appoint: processing personal data of more than **20,000 individuals**, or sensitive personal data of more than **10,000 individuals**. Below those thresholds the requirement still applies in principle, but enforcement focus is on the threshold tier. Registration of the DPO via the Personal Data Protection System within **21 days** of appointment.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md) — DPO appointment is a governance task, not an engineering one. The engineering touch-point is **the DPO contact channel**:

**Operationalisation (engineering surface):**
- Privacy policy and any disclosure under s7 (Notice and Choice) must list a working DPO contact email (typically `dpo@<org>` or equivalent).
- The DPO email mailbox must route to a real human and not silently bounce.
- Staff AUP / induction materials must reference the DPO so internal escalations know where to go.
- The DPO appointment fact (and the registration confirmation) is the artefact a regulator looks for first in an inspection — keep a copy with the org's compliance evidence.
- s12A(4): appointing a DPO does **not** discharge the controller / processor from any duty under the Act. The DPO is a coordination role, not a liability shield.

## Codes of practice — s23–29

**Rule (summary):** A data controller forum may submit a code of practice to the Commissioner for registration (s23–s27). The Commissioner may register, vary, or revoke a code (s24, s26, s28). A controller must comply with **the applicable code** for its class (s25). **Non-compliance with an applicable code is itself an offence** under s29: fine up to RM 100,000 and/or 1 year imprisonment.

**Practical effect:** if your organisation operates in a class with a registered code of practice (e.g., banking, insurance, telecommunications, healthcare, utilities, aviation, transport — check the JPDP register for the current list), the code's specific technical requirements bind on top of the seven Principles. Codes typically prescribe more granular controls — minimum encryption strengths, retention periods, third-party assessment cadences — that go beyond what s5–12 require by themselves.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md), with knock-on effects to [02 Architecture](../../../layers/02-architecture.md), [04 Controls and processes](../../../layers/04-controls-and-processes.md), and [06 Disclosure](../../../layers/06-disclosure.md).

**Operationalisation:**
- Determine your class. If a code is applicable, treat it as a hard floor — code-prescribed controls override any "reasonable steps" judgement under s9.
- A code typically references: encryption at rest and in transit; access logging and retention; user-access-request handling SLA; vendor onboarding controls; staff training cadence. Map each into the universal layer files.
- Codes are revised periodically. Track the JPDP register and re-baseline annually.

## Vendor / processor obligations — flow-down

**Rule (summary):** since 1 April 2025, A1727 has put **direct duties on data processors** — s5(1A) requires a processor to comply with the Security Principle (s9) when processing on behalf of a controller, and s12A(2) requires a processor to appoint its own DPO. The controller's pre-existing duty (originally s9(2)) to *"ensure that the data processor"* provides sufficient guarantees and takes reasonable steps was tightened by A1727 item 5: the controller still selects + contracts; the processor is now also independently liable under s9.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md) (vendor DPAs), with [04 Controls and processes](../../../layers/04-controls-and-processes.md) (vendor review cadence) and [02 Architecture](../../../layers/02-architecture.md) (vendor scoping).

**Operationalisation:**
- Vendor DPA must require the vendor to (a) comply with the Security Principle, (b) appoint a DPO, (c) notify breaches without undue delay (so the controller can hit its 72-hour s12B(1) clock), (d) restrict sub-processors.
- Any vendor handling sensitive personal data (incl. **biometric data** under the amended s4 definition) is automatically in the higher-stakes tier — explicit-consent UX, narrower retention, stricter access logs.
- Cross-border vendor processing additionally engages s129 — see [05-care.md](05-care.md).

## What's at stake

- **Failure to comply with an applicable code of practice** (s29): RM 100,000 / 1 year — relatively modest compared to the principle penalty, but cumulative.
- **Failure to appoint a DPO**: the Act does not specify a discrete penalty for s12A non-appointment, but the JPDP Guideline frames it as a compliance expectation; non-appointment will surface in any inspection and undercut the s133 due-diligence defence for directors.
- **Director liability under s133**: a director facing personal liability for a body-corporate offence will rely on the audit trail (DPO appointment, training records, code-of-practice adherence) to establish the "reasonable precautions and due diligence" defence. The accountability layer is what makes that defence credible.
