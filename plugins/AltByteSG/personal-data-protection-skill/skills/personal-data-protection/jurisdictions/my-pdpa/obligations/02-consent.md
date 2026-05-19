# Consent — General Principle (s6), Withdrawal (s38), Sensitive PD (s40), Direct Marketing (s43)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

Consent is the default lawful basis under the General Principle. The carve-outs in s6(2) cover most transactional processing; sensitive personal data needs **explicit consent** under s40; direct marketing has a per-channel opt-out right under s43.

## s6 — General Principle

**Rule (verbatim):** *"A data user shall not — (a) in the case of personal data other than sensitive personal data, process personal data about a data subject unless the data subject has given his consent to the processing of the personal data; or (b) in the case of sensitive personal data, process sensitive personal data about a data subject except in accordance with the provisions of section 40."* (s6(1))

**Practical effect:** consent is the default. The Act does not prescribe a form for consent for non-sensitive data — a clear opt-in checkbox bound to the privacy notice is sufficient in most consumer contexts, provided it is informed (s7 notice) and recorded.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md) (signup flow), [03 Data model](../../../layers/03-data-model.md) (consent records).

**Operationalisation:**
- Signup screen: bundled "I agree to the Privacy Notice and Terms" checkbox is acceptable for transactional processing — the notice itself does the heavy lifting under s7.
- Persist a consent record per data subject: timestamp, notice version (hash of the rendered notice), client metadata (IP, UA), the specific processing purposes consented to. This is your evidence under any inspection.
- "Pre-ticked" boxes are not consent. Make the user act.
- For analytics / personalisation / non-transactional purposes, separate the toggle from the bundled checkbox — see s43 below.

## s6(2) — Non-consent bases

**Rule (verbatim):** consent is not required where processing is necessary *"(a) for the performance of a contract to which the data subject is a party; (b) for the taking of steps at the request of the data subject with a view to entering into a contract; (c) for compliance with any legal obligation to which the data user is the subject, other than an obligation imposed by a contract; (d) in order to protect the vital interests of the data subject; (e) for the administration of justice; or (f) for the exercise of any functions conferred on any person by or under any law."*

**Practical effect:** the (a)–(c) carve-outs cover the common case — collecting account details to provide the service, processing payment, retaining records for tax / AML obligations. (d) is for emergencies. (e) and (f) are statutory carve-outs that rarely apply to commercial apps.

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md) — your privacy notice must explain which purposes ride on consent and which ride on contract necessity / legal obligation.

**Operationalisation:**
- In the privacy notice, label each processing purpose with its lawful basis (consent vs s6(2)(a) contract vs s6(2)(c) legal obligation). This makes withdrawal logic clean — withdrawal can stop consent-based processing but cannot stop legal-obligation processing.
- Tax / AML / accounting-record retention overrides the Retention Principle (s10) — keep the carve-out documented.

## s6(3) — Lawful purpose, necessity, adequacy

**Rule (verbatim):** *"Personal data shall not be processed unless — (a) the personal data is processed for a lawful purpose directly related to an activity of the data user; (b) the processing of the personal data is necessary for or directly related to that purpose; and (c) the personal data is adequate but not excessive in relation to that purpose."*

**Practical effect:** a "data minimisation" rule baked into the General Principle. Even with valid consent, you can only collect what you need.

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md), [05 Feature/UX](../../../layers/05-feature-ux.md).

**Operationalisation:**
- Every new column / field in a user-data table should map to a documented purpose. If a field doesn't map, drop it.
- Avoid "we might use it later" fields. Add the field when the use case is real.
- Forms: optional vs required is a UX decision but also a statutory one — required-but-not-necessary fails s6(3)(b)–(c).

## s38 — Withdrawal of consent

**Rule (verbatim):** *"A data subject may by notice in writing withdraw his consent to the processing of personal data in respect of which he is entitled to withdraw consent."* (s38(1)). The controller, *"on receiving the notice... shall... cease the processing of the personal data."* (s38(2))

**Practical effect:** the right is symmetric to consent. If you accepted consent via a checkbox, you must accept its withdrawal via an equivalently friction-free path — typically a Settings toggle.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md), [04 Controls and processes](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Settings screen: a toggle for each consent-based purpose that the user can switch off. Withdrawal takes effect on the toggle event — log the change in the consent-records table.
- Mutation paths: any code path that processes consent-based data must check the live consent state. A single "consents" table joined on user ID is the clean implementation.
- Withdrawal from the **consent-based** purposes does not stop processing under s6(2)(a) contract necessity (e.g., billing for an active subscription). Make that clear in the UX so the user understands what stops and what continues.

## s40 — Sensitive personal data

**Rule (summary):** s40(1) prohibits processing sensitive personal data of a data subject except where (a) the data subject has given **explicit consent**, or (b) processing is necessary under one of the enumerated bases (employment-law obligation, vital interests, medical purposes by a healthcare professional or equivalent, legal proceedings / advice / rights, administration of justice, statutory functions, Ministerial order), or (c) the data has been made public by the data subject's deliberate steps.

**Definition (s4 as amended by A1727 item 3(c)):** sensitive personal data means personal data consisting of *"physical or mental health or condition... political opinions... religious beliefs or other beliefs of a similar nature... commission or alleged commission... of any offence... biometric data..."*

**"biometric data" (s4 as inserted by A1727 item 3(b)):** *"any personal data resulting from technical processing relating to the physical, physiological or behavioural characteristics of a person."*

**Practical effect:** **explicit consent** is the realistic basis for almost all consumer apps that touch any of these categories. The (b) carve-outs are narrow. "Explicit" means the consent screen for these fields is **separate from** the bundled signup checkbox — a discrete dialog identifying the sensitive category, the purpose, and a deliberate user act.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md), [03 Data model](../../../layers/03-data-model.md).

**Operationalisation:**
- A second consent screen (modal or in-flow) before any sensitive-data field is collected. Don't bundle into the signup checkbox.
- Schema: tag the sensitive columns and gate access (RLS / row-level policy / column-level GRANT) so a regular service-role can't accidentally read them.
- **Biometric data is now sensitive** post-1 April 2025 — face unlock, fingerprint hashes, voice prints, gait patterns all qualify. If you're shipping a feature with on-device biometrics that never crosses to your server, you may not be processing it; if any embedding crosses, you are.
- Audit-log every read of a sensitive column. Reads, not just writes — a curious staff member browsing health data is a s48-type problem (see [07-offences.md](07-offences.md)) AND a s40 / s9 problem.
- s40(3) penalty: RM 200,000 / 2 years per person convicted.

## s43 — Right to prevent processing for direct marketing

**Rule (verbatim):** *"A data subject may, at any time by notice in writing to a data user, require the data user at the end of such period as is reasonable in the circumstances to cease... processing his personal data for purposes of direct marketing."*

**Practical effect:** the user has a per-channel opt-out right. Marketing email, SMS, push, in-app marketing surfaces — each must honour the opt-out. The Act doesn't prescribe how the user makes the request, so an in-app toggle is acceptable and is the friction-free path.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md), [04 Controls and processes](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Settings split: transactional notifications (always on, mostly contract-necessity under s6(2)(a)) vs marketing notifications (opt-in, withdrawable under s43). Don't conflate.
- Every marketing send pipeline reads the live opt-out state at send time, not at signup time.
- "Reasonable period" — the Act doesn't specify, but operationally treat the opt-out as effective on the next send-batch (≤ 24h is a safe target).
- Unsubscribe link in marketing emails must work. Failed unsubscribes are the textbook s43 + s38 violation pattern.

## What's at stake

- **General Principle breach (s6 → s5(2))**: RM 1,000,000 / 3 years. Same maximum as any principle breach.
- **Sensitive PD breach (s40(3))**: RM 200,000 / 2 years.
- **Failure to comply with a withdrawal-of-consent notice (s38)**: surfaces under s5(2) as a General Principle breach.
- **Direct-marketing breach (s43)**: surfaces under s5(2) (Notice & Choice / General Principle) for failing to honour the user's expressed choice.

The audit trail of consent records (signup, withdrawal, marketing toggle history) is the single most useful evidence in any complaint. Build the consent-records table early and trust it.
