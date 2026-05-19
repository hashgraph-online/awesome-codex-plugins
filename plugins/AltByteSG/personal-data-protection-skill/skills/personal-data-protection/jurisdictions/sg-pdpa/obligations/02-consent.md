# Part 4 Division 1 — Consent (s13–17)

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

## s13 — Consent required before collection / use / disclosure

**Rule (verbatim):** *"An organisation must not collect, use or disclose personal data about an individual unless the individual gives, or is deemed to have given, his or her consent under this Act to the collection, use or disclosure, or the collection, use or disclosure is required or authorised under this Act or any other written law."*

**Implementation layers:** [05 Feature/UX](../../../layers/05-feature-ux.md) (signup, settings toggles, JIT prompts), [03 Data model](../../../layers/03-data-model.md) (consent record).

**Operationalisation:**
- Active opt-in at signup (T&C / privacy policy checkbox)
- Just-in-time OS-level permission prompts (camera, photos, location, notifications) — see [layer 05](../../../layers/05-feature-ux.md)
- No silent collection — every endpoint maps either to a consented purpose or to a s17 exception

## s14(2)(a) — No bundled consent beyond what is reasonable

**Rule (verbatim):** *"An organisation must not, as a condition of providing a product or service, require an individual to consent to the collection, use or disclosure of personal data about the individual beyond what is reasonable to provide the product or service."*

**Practical effect:** marketing / promotional consent must be **separable** from operational / transactional consent. A single "I agree" checkbox covering both is non-compliant if the application sends marketing.

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md).

**Operationalisation:**
- Mandatory signup data: keep minimal (full name, contact for verification, anything required for service delivery)
- Optional data and marketing: separate toggles, default off
- If everything in the app is transactional (no marketing pushes / emails): a single bundled consent is acceptable. The line shifts the moment marketing is added.

## s14(2)(b) — No deceptive consent practices

**Rule (verbatim):** *"An organisation must not obtain or attempt to obtain consent for collecting, using or disclosing personal data... by providing false or misleading information... or using deceptive or misleading practices."*

**Practical effect:** plain-language disclosures, no pre-checked boxes for non-essential purposes, no dark patterns ("agree" button visually dominant, "decline" hidden).

**Implementation layers:** [05 Feature/UX](../../../layers/05-feature-ux.md), [06 Disclosure](../../../layers/06-disclosure.md).

## s15 — Deemed consent (voluntary provision + contract necessity)

**Rule:** an individual is deemed to consent if they voluntarily provide the personal data and it is reasonable that they would do so. Sub-flows in s15(3) and s15(6) cover sharing data with sub-processors during contract performance.

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md) (lawful-basis register).

**Operationalisation:**
- Document which fields rely on deemed vs explicit consent
- For data shared with sub-processors during contract performance, the s15(3)/(6) chain applies — and respects contractual purpose limits (don't expand the sub-processor's permitted use)

## s15A — Deemed consent by notification (opt-out)

**Rule:** an individual may be deemed to consent to a new use of existing data if (a) the organisation conducts an assessment that the use is **not likely to have an adverse effect** on the individual; (b) takes reasonable steps to inform of intent, purpose, and a reasonable opt-out window; (c) the individual does not opt out within that window. Excludes prescribed purposes.

**When relevant:** introducing a new use of data already collected, without going back for fresh consent.

**Operationalisation:**
- Run and document an adverse-effect assessment **before** relying on this basis
- In-app notice + email with clear opt-out and stated window (≥ 14 days is a defensible default)
- Implement an opt-out endpoint and honour opt-outs **before** the new use begins

## s16 — Withdrawal of consent

**Rule (verbatim, key language):** an individual *"may at any time withdraw any consent"*; the organisation *"must inform the individual of the likely consequences of withdrawing"*; *"must not prohibit"* withdrawal; on withdrawal *"must cease (and cause its data intermediaries and agents to cease) collecting, using or disclosing the personal data."*

**Implementation layers:** [05 Feature/UX](../../../layers/05-feature-ux.md) (settings toggles), [04 Controls](../../../layers/04-controls-and-processes.md) (cessation propagation to sub-processors).

**Operationalisation:**
- Settings toggles for each consent the user gave, with equal effort to revoke as to grant
- Confirmation dialog stating the consequences of withdrawal where they're non-obvious
- On withdrawal, cessation must propagate to:
  - Database state (notification flag flipped, push token nulled)
  - Sub-processors (push provider de-registered, OAuth token revoked, etc.)
  - Future operations (retention sweeps, scheduled jobs)
- Target cessation latency: ASAP; PDPC guidance is ≤ 30 days

## s17 + First/Second Schedules — Collection / use / disclosure without consent

**Rule:** specific enumerated cases where consent is not required. Not a general balancing test (unlike GDPR's legitimate interests).

**Common cases for consumer apps:**

| Schedule item | When it applies |
|---|---|
| 1st Sch Pt 1 — Vital interests | Lost-pet emergency, safety / medical situations |
| 1st Sch Pt 3 §1 — Legitimate Interests | Fraud prevention, abuse moderation, safety. Requires written assessment + reasonable user access to information about the use |
| 1st Sch Pt 3 §3 — Investigations | Police / abuse reports |
| 1st Sch Pt 4 — Business asset transactions | Acquisition / sale of the business; users notified post-deal; data destroyed if deal fails |
| 1st Sch Pt 5 / 2nd Sch Pt 2 Div 2 — Business improvement | Single-org product analytics. Identifiable form must be necessary AND a reasonable person would consider use appropriate. **Cannot be used for marketing.** |
| 2nd Sch Pt 2 Div 3 — Research | Strict purpose limitation |

**Operationalisation:**
- Maintain a per-data-flow lawful-basis register
- For Legitimate Interest reliance: document the assessment (LIA) before launch
- For Vital Interest reliance: notify the individual *"as soon as is practicable"* after the use
- For Business Improvement reliance: never extend to marketing use

## Cross-references

- [05-care.md](05-care.md) for the related Protection (s24) and Retention (s25) obligations
- [03-purpose.md](03-purpose.md) for the related Purpose Limitation and Notification of Purpose obligations
- [06-breach-notification.md](06-breach-notification.md) for cessation duties triggered by a breach
