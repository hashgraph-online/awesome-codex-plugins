# Part 6A — Data Breach Notification (s26A–E)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

This Part is the strictest of the Act and was added by the 2020 Amendments (commenced 1 February 2021). The 3-day notification clock makes preparation in advance non-negotiable.

## s26A — Definition of "data breach"

**Rule (verbatim):** *"data breach"* means *"(a) the unauthorised access, collection, use, disclosure, copying, modification or disposal of personal data; or (b) the loss of any storage medium or device on which personal data is stored in circumstances where the unauthorised access, collection, use, disclosure, copying, modification or disposal of the personal data is likely to occur."*

**Practical effect:** the definition is **broad**. A lost laptop with prod credentials, a leaked API key, a misdirected email, an RLS bypass — all qualify as breaches even before any actual misuse is confirmed.

**Implementation layer:** [07 Operational](../../../layers/07-operational.md) (incident-response runbook).

**Operationalisation:** the runbook (see `templates/INCIDENT_RESPONSE.md.template`) must define "incident" broadly enough to capture all of the above. When in doubt, treat as an incident — the cost of opening a triage case is low; the cost of missing the clock is high.

## s26B(1)–(3) — Notifiable data breach thresholds

**Rule (verbatim):** a breach is notifiable if it *"(a) results in, or is likely to result in, significant harm to an affected individual; or (b) is, or is likely to be, of a significant scale."*

**"Significant harm"** is **deemed** when prescribed personal-data classes are involved. Per the PDP Notification of Data Breaches Regulations 2021, this includes:
- Full name + NRIC / FIN / passport / driving licence / work permit / dependant's pass / similar
- Financial info (account numbers, credit card, transaction details)
- Health / medical information
- Account credentials (passwords, security questions, etc.)
- Login credentials with sufficient context to take over the account

A single-record breach involving these categories is mandatorily notifiable.

**"Significant scale"** is **deemed** at *"not fewer than the prescribed number of affected individuals"* — currently **500**.

**Implementation layer:** [07 Operational](../../../layers/07-operational.md).

**Operationalisation:**
- Breach assessment matrix in the runbook: data category × affected count → notifiable yes/no
- High-risk PaoPao-style categories: phone, email, location, photos, private chat content (chat content is borderline — disclosure to a third party is significant; internal-only access is not a notifiable breach per s26B(4))

## s26B(4) — Internal-only breach not notifiable

**Rule (verbatim):** a breach *"that relates to the unauthorised access, collection, use, disclosure, copying or modification of personal data only within an organisation is deemed not to be a notifiable data breach."*

**Practical effect:** a curious employee accessing data they shouldn't, **without** disclosing externally, is not a notifiable data breach under Part 6A.

**But:** this same conduct **is** likely a personal offence under s48D / s48E (see [07-offences.md](07-offences.md)) — and may also be a s24 protection-obligation breach for the org. Investigate, document, and discipline.

## s26C(2) — Duty to assess reasonably and expeditiously

**Rule (verbatim):** *"Where an organisation has reason to believe that a data breach affecting personal data in its possession or under its control has occurred, the organisation must conduct, in a reasonable and expeditious manner, an assessment of whether the data breach is a notifiable data breach."*

**Practical effect:** the assessment clock starts on awareness of the suspected breach, not on confirmation. Open the case immediately; assess; conclude.

**Implementation layer:** [07 Operational](../../../layers/07-operational.md).

**Operationalisation:**
- Runbook step: triage owner = DPO; assessment template; target ≤ 30 days from awareness (PDPC guidance for the assessment phase)
- Capture the timeline: awareness → assessment-in-progress → assessment-complete → notifiable Y/N

## s26C(3) — Data intermediary's duty to notify the controller

**Rule (verbatim):** *"Where a data intermediary... has reason to believe that a data breach has occurred in relation to personal data that the data intermediary is processing on behalf of and for the purposes of another organisation... the data intermediary must, without undue delay, notify that other organisation."*

**Practical effect:** when **you** are processing on behalf of someone else, you must notify them. When **someone is processing on behalf of you**, they must notify you — and your DPA with them must require it.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md) (vendor contracts).

**Operationalisation:**
- Add this clause to vendor DPAs where you're the controller: "without undue delay" notification
- Be prepared to notify partners "without undue delay" if you're the intermediary
- Most consumer apps are controllers, not intermediaries — re-evaluate if that changes

## s26D(1) — Notify PDPC within 3 calendar days [CRITICAL]

**Rule (verbatim):** where an organisation assesses a breach as notifiable, it *"must notify the Commission as soon as is practicable, but in any case no later than 3 calendar days after the day the organisation makes that assessment."*

**Practical effect:** **3 calendar days. Not business days.** The clock starts when the assessment concludes the breach is notifiable — which can be days or weeks after initial awareness.

**Implementation layer:** [07 Operational](../../../layers/07-operational.md).

**Operationalisation:**
- Pre-fill the PDPC breach report template before any incident occurs (it's a standard form on the PDPC e-services portal)
- DPO + backup contact must both have access to submit
- Treat the 3-day window as strict — an incident discovered on Friday afternoon must still be notified by Monday morning if the assessment concluded on Friday

**PDPC reporting portal:** [eservice.pdpc.gov.sg/case/db](https://eservice.pdpc.gov.sg/case/db)

## s26D(2) — Notify affected individuals (significant-harm breach)

**Rule (verbatim):** on or after notifying the Commission, the organisation *"must also notify each affected individual affected by a notifiable data breach mentioned in section 26B(1)(a) [significant harm] in any manner that is reasonable in the circumstances."*

**Practical effect:** for significant-harm breaches, individuals must be told. For significant-scale breaches that don't involve significant harm to individuals, individual notification may not be required — depends on the assessment.

**Operationalisation:**
- Channels: email (primary), in-app banner (next launch), push notification (only if email and in-app aren't reaching them)
- Plain-language template: what happened, when, what data, what you've done, what they should do, how to contact the DPO
- Pre-stage templates in `templates/breach-comms/`

## s26D(3)–(4) — Notification content and form

**Rule:** notifications *"must contain... all the information that is prescribed for this purpose"* to PDPC and individuals, in *"the form and submitted in the manner required by the Commission."*

**Operationalisation:** use the PDPC breach reporting form. It asks for:
- Nature of the breach (one paragraph)
- When discovered, when it occurred (or "unknown — under investigation")
- Number of affected individuals (estimate is fine if exact unknown — update later)
- Types of personal data involved
- Cause (root cause if known; "under investigation" otherwise)
- Likely harm to individuals
- Containment + remediation actions taken
- Steps individuals can take to protect themselves
- DPO contact

## s26D(5) — Tech-measure exception

**Rule (verbatim):** individual notification not required if the organisation *"on or after assessing... takes any action... that renders it unlikely that the notifiable data breach will result in significant harm"* OR *"had implemented, prior to the occurrence... any technological measure that renders it unlikely that the notifiable data breach will result in significant harm."*

**Practical effect:** strong encryption with uncompromised keys, fast credential revocation, hashed passwords (where the hash function is strong) can defuse the individual-notification requirement — but **PDPC notification is still required**.

**Operationalisation:**
- Document encryption / hashing / revocation posture so the exception is defensible
- The exception is a defence, not a default — it requires affirmative documentation

## s26D(6) — Suspend individual notice on law-enforcement direction

**Rule:** the organisation *"must not notify any affected individual... if (a) a prescribed law enforcement agency so instructs; or (b) the Commission so directs."*

**Operationalisation:** runbook checkpoint — before mass user comms, check for any law-enforcement hold.

## s26E — Data intermediary of public agency

**Rule:** where the organisation is a data intermediary processing personal data on behalf of a public agency, and has reason to believe a breach has occurred, it *"must, without undue delay, notify the public agency of the occurrence of the data breach."*

**Operationalisation:** N/A for most consumer apps. Re-evaluate if you ever contract with a SG public agency.

## What's at stake

Penalty for breach of Part 6A: same s48J(3) cap — SGD 1M for orgs ≤ SGD 10M SG turnover; **10% of SG turnover above that**. PDPC has demonstrated willingness to use the higher cap for material breaches.

The runbook (see `templates/INCIDENT_RESPONSE.md.template`) is the single most important artefact for this Part. Build it before you need it.
