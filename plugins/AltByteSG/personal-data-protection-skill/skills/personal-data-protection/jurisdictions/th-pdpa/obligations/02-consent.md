# Chapter II Part I + Sections 24, 26 — Consent, Lawful Bases, Sensitive Data

> ⚠ **Reference material only — not legal advice.** See [DISCLAIMER.md](../../../../../DISCLAIMER.md). Verify against the official statute and consult a qualified DPO / lawyer.

## Section 19 — Consent required (general rule)

**Rule (verbatim):** *"The Data Controller shall not collect, use, or disclose Personal Data, unless the data subject has given consent prior to or at the time of such collection, use, or disclosure, except the case where it is permitted to do so by the provisions of this Act or any other laws."*

**Form requirements:**
- Consent must be **explicit**, in writing or via electronic means (unless impossible by nature)
- The request must be **clearly distinguishable** from other matters
- In **easily accessible and intelligible** form
- In **clear and plain language**
- **Not deceptive or misleading** about the purpose
- The Committee may prescribe specific forms

**Freely given:** the request must take into account that consent is freely given. **Bundled consent prohibited:** entering a contract or service must not be conditioned on consenting to processing not necessary or not related to the contract / service.

**Withdrawal (s19 paragraph 5–6):**
- The data subject **may withdraw consent at any time**, with the **same ease as giving it**, unless restricted by law or by a contract benefiting the data subject
- Withdrawal does not affect prior lawful processing
- The Data Controller **must inform** the data subject of the consequences of withdrawal where withdrawal will affect them

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md) (signup, settings, withdrawal symmetry), [03 Data model](../../../layers/03-data-model.md) (consent record).

## Section 20 — Minor consent

**Rule:** when the data subject is a minor:
- Below age 10: consent must be obtained from the **holder of parental responsibility**
- 10 and above (still a minor not sui juris): consent is generally required from the parent in addition to the minor, except where the act is one a minor may legally do alone (specific Civil and Commercial Code provisions)

Same rules apply for incompetent / quasi-incompetent data subjects (custodian / curator gives consent).

**Implementation layer:** [05 Feature/UX](../../../layers/05-feature-ux.md) (age gating + parental-consent flow if minors are permitted users).

## Section 21 — Purpose limitation tied to consent

**Rule:** Personal Data must be collected, used, or disclosed **according to the purpose notified to the data subject** prior to or at the time of collection. New purposes require either:
1. Notifying the data subject of the new purpose AND obtaining new consent, OR
2. Permission under the Act or other law.

See [03-purpose.md](03-purpose.md) for purpose-limitation depth.

## Section 24 — Lawful bases (collection without consent)

**Rule:** the Data Controller may NOT collect Personal Data without consent, **except** under one of six bases:

1. **Research / archival in public interest** — with safeguards per Committee notification
2. **Vital interests** — preventing or suppressing a danger to a person's life, body, or health
3. **Contractual necessity** — performance of a contract to which the data subject is a party, or pre-contractual steps at the data subject's request
4. **Public-interest task / official authority** — necessary for a task in public interest, or exercising official authority vested in the Data Controller
5. **Legitimate interests** — necessary for the legitimate interests of the Data Controller or third parties, **except where overridden** by the data subject's fundamental rights
6. **Legal obligation** — necessary for compliance with a law to which the Data Controller is subject

**This is a closed list** — but materially close to the GDPR Article 6 lawful bases. Singapore PDPA's enumerated 1st/2nd Schedule cases differ in structure.

**Implementation layer:** [06 Disclosure](../../../layers/06-disclosure.md) (lawful-basis register / privacy policy purposes table).

**Operationalisation:**
- Maintain a per-data-flow lawful-basis register
- For Legitimate Interests reliance: document an LIA-style assessment proving necessity AND that data subject's rights are not overridden
- For Vital Interests reliance: notify the data subject after the use where practicable (general accountability principle)

## Section 25 — Collection from sources other than the data subject

**Rule:** the Data Controller may not collect Personal Data from sources other than the data subject directly, **except**:

1. The Data Controller **informs the data subject** of the collection from another source within **30 days** and obtains consent, OR
2. The collection falls within the s24 (lawful basis) or s26 (sensitive-data) exceptions

**Notification timing:** within 30 days from the date of collection. Special cases (where the Personal Data is used for direct communication with the data subject; or where disclosure to a third party is envisaged) may shift the timing.

**Implementation layer:** [01 Non-technical](../../../layers/01-non-technical.md) (partner integration MOUs), [04 Controls](../../../layers/04-controls-and-processes.md) (notification flow).

## Section 26 — Sensitive Personal Data

**Rule (verbatim, key categories):** *"Any collection of Personal Data pertaining to racial, ethnic origin, political opinions, cult, religious or philosophical beliefs, sexual behavior, criminal records, health data, disability, trade union information, genetic data, biometric data, or of any data which may affect the data subject in the same manner, as prescribed by the Committee, is prohibited, without the explicit consent from the data subject."*

**Compared to Singapore:** much broader than Singapore PDPA's "deemed significant harm" categories. Many data points your application might collect routinely (health for medical apps, location-derived political affiliation, etc.) are sensitive under Thai law.

**Sensitive-data exceptions (without explicit consent):**

1. Vital interests (data subject incapable of consent)
2. Legitimate activities by foundations / associations / not-for-profits — with appropriate safeguards, no external disclosure
3. Information already disclosed publicly with explicit data subject consent
4. Establishment, compliance, exercise, or defence of legal claims
5. Compliance with a law for specific purposes:
   - (a) Preventive / occupational medicine, medical diagnosis, health/social care, or services management — subject to confidentiality
   - (b) Public-health purposes (cross-border contagious disease, medicinal product safety, etc.)
   - (c) Employment / social security / health welfare / road accident victim protection — with safeguards
   - (d) Scientific, historical, or statistical research with safeguards

**Implementation layer:** [03 Data model](../../../layers/03-data-model.md) (sensitive-data flagging), [05 Feature/UX](../../../layers/05-feature-ux.md) (explicit consent UX).

**Operationalisation:**
- **Audit your data inventory** for sensitive categories. Many apps inadvertently collect sensitive data — e.g. health-related (fitness apps), religious (community apps), political (advocacy apps).
- **Explicit consent** for sensitive data must be captured separately from general consent (no bundling).
- The s84 administrative fine for sensitive-data violations is **THB 5M** — the highest tier. Don't assume sensitive-data handling is the same risk as general data.

## Penalty exposure (this Part)

| Failure | Maximum administrative fine | Source |
|---|---|---|
| Fails consent form requirements (s19 para 3) or impact-of-withdrawal notice (s19 para 6) | THB 1M | s82 |
| Violates s24 (collection without lawful basis) | THB 3M | s83 |
| Violates s26 paragraph 1 or 3 (sensitive data without explicit consent or per exceptions) | **THB 5M** | s84 |
| Obtains consent by deception about purpose | THB 3M | s83 |
| Violates s27 (use/disclosure without consent) involving sensitive data | **THB 5M** + criminal liability under s79 | s84, s79 |

Plus s81 personal liability for directors / managers responsible for the offence.
