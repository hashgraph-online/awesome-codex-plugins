# Purpose — Notice & Choice (s7), Disclosure (s8), s39, s41

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

The Notice and Choice Principle (s7) and the Disclosure Principle (s8) together do the work that a "purpose limitation" obligation does in other regimes. The notice has to be in **both** Bahasa Malaysia and English (s7(3)) — this is a hard MY-specific requirement most teams forget on first pass.

## s7(1) — Notice and Choice: required content

**Rule (verbatim):** *"A data user shall by written notice inform a data subject — (a) that personal data of the data subject is being processed by or on behalf of the data user, and shall provide a description of the personal data... (b) the purposes for which the personal data is being or is to be collected and further processed; (c) of any information available to the data user as to the source of that personal data; (d) of the data subject's right to request access to and to request correction of the personal data and how to contact the data user with any inquiries or complaints in respect of the personal data; (e) of the class of third parties to whom the data user discloses or may disclose the personal data; (f) of the choices and means the data user offers the data subject for limiting the processing of personal data, including personal data relating to other persons who may be identified from that personal data; (g) whether it is obligatory or voluntary for the data subject to supply the personal data; and (h) where it is obligatory for the data subject to supply the personal data, the consequences for the data subject if he fails to supply the personal data."*

**Practical effect:** the notice content is **prescribed** — eight specific points, no negotiation. Most off-the-shelf privacy notice templates are missing (c) source, (f) choices and means, (g)/(h) obligatory-vs-voluntary disclosure.

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md).

**Operationalisation:**
- Privacy notice structure (sectioned to map onto s7(1)):
  1. **What we collect** — description of personal data (a)
  2. **Why we collect it** — purposes (b), with each purpose tagged consent vs non-consent basis under s6(2) (cross-reference [02-consent.md](02-consent.md))
  3. **Where we got it** — direct from you, or class of third-party sources (c)
  4. **Your rights** — access (s30), correction (s34), withdrawal (s38), data portability (s43A), prevent direct marketing (s43); how to contact the DPO (d)
  5. **Who we share with** — categories of recipients (e), including service providers / processors / cross-border destinations (cross-reference [05-care.md](05-care.md))
  6. **Your choices** — settings toggles, opt-outs, marketing preferences (f)
  7. **Required vs optional** — for each form field, indicate which fields are obligatory and the consequence of not providing them (g, h)
- The DPO contact in (d) must be a real working channel — see [01-accountability.md](01-accountability.md).

## s7(2) — When the notice is given

**Rule (summary):** the notice must be given as soon as practicable when the controller first asks for or first collects the personal data, **OR** before using the data for a purpose other than the one for which it was originally collected, **OR** before disclosing it to a third party.

**Practical effect:** "just-in-time" notice for new purposes. If you add a new processing purpose (e.g., "we'll now send marketing emails using the email you gave us at signup"), you owe a fresh s7 notice **before** the new processing starts — not after.

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md), [05 Feature/UX](../../../layers/05-feature-ux.md).

**Operationalisation:**
- Privacy-notice version history. When you change purposes, bump the version, persist the new version's hash, and re-prompt active users for consent (or notify them, depending on the basis).
- For brand-new third-party disclosures (e.g., adding an analytics SDK), surface a contextual disclosure at the next user touchpoint and update the privacy notice in the same release.

## s7(3) — Bilingual notice [MY-specific]

**Rule (verbatim):** *"A notice under subsection (1) shall be in the national and English languages, and the individual shall be provided with a clear and readily accessible means to exercise his choice, where necessary, in the national and English languages."*

**Practical effect:** the privacy notice **must** be available in **Bahasa Malaysia** and **English**. Both. Not "select your preferred language and we'll show one"— **both** must be accessible. Same applies to consent / choice mechanisms.

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md), [05 Feature/UX](../../../layers/05-feature-ux.md).

**Operationalisation:**
- App: privacy notice screen renders the active locale by default but exposes a language toggle that produces the other version. Settings > Language > Privacy Notice (BM | EN).
- Web: language switcher on the privacy page, with the alternate URL canonical-linked.
- Pre-launch checklist: BM translation reviewed by a fluent reviewer (machine translation alone is the textbook compliance failure here; the regulator can read it).

## s8 — Disclosure Principle

**Rule (verbatim):** *"Subject to section 39, no personal data shall, without the consent of the data subject, be disclosed — (a) for any purpose other than — (i) the purpose for which the personal data was to be disclosed at the time of collection of the personal data; or (ii) a purpose directly related to the purpose referred to in subparagraph (i); or (b) to any party other than a third party of the class of third parties as specified in paragraph 7(1)(e)."*

**Practical effect:** disclosure is constrained both by **purpose** and by **class of recipient**. Adding a new third-party recipient class (a new analytics SDK, a new CRM, a new payment processor) requires updated notice **before** the data flows.

**Implementation layer:** [04 Controls and processes](../../../layers/04-controls-and-processes.md), [06 Disclosure](../../../layers/06-disclosure.md).

**Operationalisation:**
- Maintain an inventory of every external recipient of personal data (what data, what purpose, what class). When the inventory grows, the privacy notice grows.
- Code-level: any new outbound integration touching personal data should trigger a privacy review step — easy to wire as a CI check on PRs that add new HTTP clients to known recipients.
- Sub-processors of your processors are still your concern under s8 if their existence widens the recipient class. Vendor DPAs should require disclosure of sub-processors — see [01-accountability.md](01-accountability.md).

## s39 — Extent of disclosure (carve-out from s8)

**Rule (summary):** s8 does not preclude disclosure where one of the s39 grounds applies — most commonly: subject's consent; necessary for prevention / detection of crime; required or authorised by law or by court order; necessary in the public interest; or necessary in the legitimate interests of the controller, except where prejudicial to the data subject's rights.

**Practical effect:** rarely engaged in normal product operation. Engages on law-enforcement requests, fraud investigations, and audit-driven disclosures. Document each invocation.

**Implementation layer:** [04 Controls and processes](../../../layers/04-controls-and-processes.md).

**Operationalisation:**
- Law-enforcement request handling SOP: who reviews, what the standard of evidence is, what is logged. Don't disclose on the basis of a casual request — require written authority.
- Each s39-basis disclosure is logged with the basis cited.

## s41 — Repeated collection

**Rule (summary):** the controller must take *"reasonable steps"* to ensure that personal data is **not collected from the same data subject more than once** for the same purpose, unless circumstances change.

**Practical effect:** anti-friction provision. Don't re-ask the user for the same details on every visit if you already have them. Leverages a sensible UX pattern as a statutory rule.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md), [03 Data model](../../../layers/03-data-model.md).

**Operationalisation:**
- Pre-fill known fields. If the user has already provided their phone number for one workflow, don't make them retype it for another.
- Onboarding wizards that re-ask known data (because state was lost, or because the wizard wasn't engineered to read existing fields) are the usual offender.

## What's at stake

- **Notice & Choice breach (s7 → s5(2))**: RM 1,000,000 / 3 years.
- **Disclosure breach (s8 → s5(2))**: RM 1,000,000 / 3 years.
- **Both surface together** in any privacy-policy-related complaint — a missing s7(1) item is also typically an s8 disclosure-without-prior-notice problem.

The bilingual-notice obligation is the easiest box to forget and the easiest one for a regulator to test — keep BM and EN versions in sync as part of release engineering.
