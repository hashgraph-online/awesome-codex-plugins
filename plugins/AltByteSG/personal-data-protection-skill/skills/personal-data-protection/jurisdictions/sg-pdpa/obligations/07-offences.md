# Part 9B — Personal Offences (s48D–F) + Penalties (s48J)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

This Part imposes **personal criminal liability** on individuals — not just civil penalties on the organisation. It was added by the 2020 Amendments (commenced 1 February 2021).

The organisation cannot indemnify a criminal sanction. Reflect this prominently in the staff AUP (see [layer 01](../../../layers/01-non-technical.md)).

## s48D — Unauthorised disclosure (individual offence)

**Rule (verbatim):** an individual commits an offence if they *"(a) disclose, or cause disclosure of, personal data in the possession or under the control of an organisation to another person; (b) the disclosure is not authorised by the organisation; and (c) they do so knowing that the disclosure is not authorised by the organisation, or reckless as to whether the disclosure is or is not authorised."*

**Practical scenarios:**
- An admin exports `users.csv` to their personal device
- An engineer pastes user PII into a public Slack channel, screenshot, or AI chat
- A staff member sells or leaks data
- A contractor takes a client list when leaving

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md) (staff AUP), [04 Controls](../../../layers/04-controls-and-processes.md) (admin audit log).

**Operationalisation:**
- Staff AUP must explicitly prohibit disclosure outside the system, with examples
- Limit raw-data exports from admin console (no bulk CSV by default)
- Admin audit log captures all admin reads of personal data — provides evidence in any subsequent investigation

**Penalty:** fine ≤ **SGD 5,000** OR imprisonment ≤ **2 years** OR both. Personal liability — the org cannot pay or indemnify.

## s48E — Improper use (individual offence)

**Rule:** an individual commits an offence by using personal data in possession of an organisation, where the use is unauthorised, they know or are reckless as to authorisation, AND the use results in *"a gain for the individual or another person", "harm to another individual",* or *"a loss to another person."*

**Practical scenarios:**
- Admin uses user contact details for personal benefit (looking up an ex-partner's address)
- Engineer uses user data for a side project
- Staff member uses customer lists to start a competing business

**Operationalisation:**
- Same staff AUP as s48D
- Train admins explicitly that read-only access for personal benefit is potentially criminal — not just policy violation

**Penalty:** same as s48D — fine ≤ SGD 5,000 / imprisonment ≤ 2 years / both.

## s48F — Unauthorised re-identification (individual offence)

**Rule:** an individual commits an offence by taking action to re-identify, or causing re-identification of, the person to whom anonymised information relates, without authorisation, knowing or reckless as to lack of authorisation.

**Practical scenarios:**
- Joining anonymised analytics dump with another dataset to identify users
- Reverse-engineering pseudonymous identifiers to reach real identities
- Linking aggregated metrics back to individuals via inference

**Operationalisation:**
- For any aggregate metrics, research datasets, or shared analytics: document the anonymisation methodology
- Prohibit re-identification in the data-use licence / agreement
- If using k-anonymity, differential privacy, or other formal techniques, document the parameters

**Penalty:** same as s48D / s48E.

## s48C(2) — Public-sector exclusion (informational)

Part 9B does not apply to relevant public officials in Singapore public-sector agencies — they are governed by the Public Sector (Governance) Act 2018. Not relevant to private-sector consumer apps.

## Penalty cap on the organisation — s48J(3)

**Rule (verbatim):** on intentional or negligent contravention of Part 3, 4, 5, 6, 6A or 6B, the Commission may impose a financial penalty *"in no case more than (a) in the case of a contravention on or after [1 October 2022] by an organisation whose annual turnover in Singapore exceeds $10 million — 10% of the annual turnover in Singapore of the organisation; or (b) in any other case — $1 million."*

**Practical effect:**
- Small org (SG turnover ≤ SGD 10M): cap is **SGD 1 million** per contravention
- Larger org (SG turnover > SGD 10M): cap is **10% of SG turnover** per contravention

**Operationalisation:**
- Maintain audited SG turnover figures
- Track which cap applies to your organisation
- The cap is **per contravention** — multiple findings can stack

## Penalty cap calculation factors — s48J(6)

PDPC must have regard to:
- Nature, gravity, duration of the contravention
- Type and sensitivity of the data involved
- Financial benefit gained or loss avoided
- Mitigation actions and timeliness
- **Pre-existing compliance measures**
- Prior non-compliance
- Cooperation with directions
- Proportionality
- Impact on operations
- Any other relevant factor

**Practical effect:** demonstrable proactive compliance is the single biggest mitigant. PDPC penalties for organisations that had documented controls + responded quickly + cooperated are routinely a fraction of the cap. Penalties for organisations with no documentation, slow response, and adversarial posture skew toward the cap.

**Operationalisation:**
- Keep a dated **compliance evidence bundle** per major release (snapshots of policies, vendor list, audit log, training records)
- Document risk-based decisions when you accept residual risk
- During an enforcement action, cooperate fully — adversarial posture aggravates the penalty

## Mental model

Three concepts to internalise:

1. **Civil + criminal layers.** s48J(3) hits the org civilly. s48D/E/F hit individuals criminally. Both can apply to the same incident.

2. **Personal liability is real.** Engineers and admins should know that misusing user data is not just a sackable offence — it's potentially a criminal one. The AUP makes this explicit.

3. **Documentation is mitigation.** The penalty calculation under s48J(6) explicitly weighs pre-existing compliance measures. Investing in this skill, the runbook, the audit log, and the documentation discipline is not bureaucracy — it's actuarially material.
