# SMS Compliance Reference

Comprehensive compliance reference for SMS marketing across major jurisdictions, opt-in copy templates, and STOP/HELP response templates.

> This is operational guidance, not legal advice. For high-volume programs (50K+ subscribers) or any program with non-trivial revenue, run your compliance setup past a TCPA-experienced attorney.

---

## United States: TCPA

### What it is

The Telephone Consumer Protection Act (1991, amended) regulates marketing calls and texts. The FCC enforces it; private plaintiffs sue under it. Statutory damages: $500–$1,500 **per message**. Class actions easily reach 7–8 figures.

### Consent tiers

| Type | What it covers | How to capture |
|------|---------------|----------------|
| **Express written consent** | Marketing SMS (sales, promotions, offers) | Checkbox + clear disclosure language, captured electronically with timestamp |
| **Express consent (non-written)** | Informational/transactional (delivery, account alerts) | Phone number provided during transaction with awareness it'll be used to text |
| **Established business relationship** | NOT sufficient for marketing SMS | Doesn't apply |

### Express written consent requirements

The opt-in flow must capture all of:

1. The recipient agreed to receive marketing SMS from your brand
2. The recipient understands consent is not a condition of purchase
3. The disclosure showed frequency expectation, message and data rate notice, STOP/HELP instructions, terms link
4. The agreement was electronically recorded with timestamp

The FCC's 2023 "one-to-one" consent rule, which would have required consent
to name a single seller, never took effect: the Eleventh Circuit vacated it on
January 24, 2025 (Insurance Marketing Coalition v. FCC). Consent captured on a
lead-generation or comparison site still has to be clear and specific to the
seller texting, so name the brand in the disclosure.

### Opt-in disclosure template (compliant)

```
By signing up via text, you agree to receive recurring automated promotional and
personalized marketing text messages (e.g., cart reminders) from [Brand] at the
cell number used when signing up. Consent is not a condition of any purchase.
Reply HELP for help and STOP to cancel. Msg frequency varies. Msg & data rates
may apply. Terms: <TERMS_URL>. Privacy: <PRIVACY_URL>.
```

Place this **directly adjacent** to the phone number field and submit button. Do not bury it in a footer.

### Quiet hours

- **Federal**: 8am–9pm in the recipient's local time zone
- **Stricter states**: Florida (8am–8pm), Oklahoma (8am–8pm), Washington (8am–8pm); Texas brought marketing texts under its telephone solicitation law effective September 1, 2025 (SB 140). Verify every state in scope before launch.
- **Carrier-recommended**: 9am–8pm recipient-local
- **Practical default**: 9am–8pm recipient-local for safety

Time zone is determined by area code, but area codes lie (people move). Major platforms (Klaviyo, Postscript, Attentive) handle this automatically; verify yours does.

### Revocation of consent (FCC rule, effective April 11, 2025)

- Consumers may revoke consent by **any reasonable means**. A reply of stop,
  quit, end, revoke, opt out, cancel, or unsubscribe is a valid revocation as a
  matter of law, and so is a clear free-text request.
- Honor the revocation as soon as practical and **no later than 10 business
  days** after receipt.
- One confirmation text is allowed, sent within 5 minutes, with no marketing
  content. If the person had consented to several message types, it may ask
  which ones to stop; no reply means stop all.
- If the texting system cannot accept replies, every message must say so and
  give another way to opt out.
- The "revoke-all" provision (an opt-out applies to all unrelated robocalls and
  robotexts from that sender) is delayed to **January 31, 2027**.

Sources: FCC Report and Order FCC 24-24 (Revocation of Consent), effective
April 11, 2025, summarized by the National Law Review, "FCC's New Consent
Revocation Rule Set to Take Effect April 2025"; CompliancePoint, "FCC Delays
Revoke-All Again".

### STOP/HELP handling

**STOP variants you must honor**: STOP, QUIT, END, REVOKE, OPT OUT, CANCEL, UNSUBSCRIBE, plus common variants such as STOPALL and OPTOUT, and any clear free-text request

**STOP response** (after STOP received):
```
You're unsubscribed from [Brand] alerts. No more messages will be sent. Reply HELP for help.
```

**HELP variants**: HELP, INFO

**HELP response**:
```
[Brand] alerts: For help, visit [URL] or email [support@example.com]. Msg & data rates may apply. Reply STOP to cancel.
```

**Critical rules**:
- Process keyword opt-outs instantly in the platform; the legal outer limit is 10 business days
- Do not require the recipient to log in or visit a website to opt out
- One STOP confirmation is allowed; do not send additional messages after
- HELP responses do not count as marketing messages and are not subject to quiet hours

### Sample TCPA-compliant footer language by sequence type

- **Opt-in confirmation**: "Reply HELP for help, STOP to cancel. Msg & data rates may apply.": required
- **Recurring promotional**: "Reply STOP to opt out": required quarterly minimum; carrier-recommended every send
- **Transactional**: Not required by TCPA but carriers expect it; include for safety

---

## United States: A2P 10DLC

### What it is

Application-to-Person 10-Digit Long Code registration, run by The Campaign Registry (TCR). Required for businesses sending SMS through 10DLC numbers (regular long codes). Since February 1, 2025, US carriers block unregistered 10DLC traffic entirely (Twilio error 30034, https://www.twilio.com/docs/api/errors/30034).

### Registration components

1. **Brand registration**
   - Legal entity name, EIN, business type
   - Trust score assigned (Standard or Verified)
   - Higher trust = better throughput, lower fees

2. **Campaign registration** (one per use case)
   - Use case: Marketing, Account Notification, Customer Care, Public Service, Higher Education, Polling and Voting, 2FA, Delivery Notification, etc.
   - Sample message text (must match what you actually send)
   - Opt-in flow description and screenshot
   - Opt-out language
   - Help message language
   - Volume estimate

3. **Phone number assignment** to campaigns

### Throughput tiers (varies by carrier and trust score)

| Trust score + use case | Throughput |
|------------------------|-----------|
| Verified brand, marketing | 75–100+ msg/sec |
| Standard brand, marketing | 4–10 msg/sec |
| Unregistered | Blocked |

### Common rejections

- Sample message text doesn't match actual sends
- Opt-in flow screenshot doesn't show required disclosure language
- "SHAFT" content (Sex, Hate, Alcohol, Firearms, Tobacco) without explicit use case
- Generic or vague campaign descriptions

**Process time**: 1–7 business days. Plan for this in launch timelines.

---

## EU / UK: GDPR + ePrivacy Directive

### Consent requirements

- **Explicit opt-in**: clear affirmative action (no pre-checked boxes)
- **Specific**: opt-in must be for marketing SMS specifically, separate from generic ToS
- **Informed**: data subject must know who's processing and why
- **Freely given**: can't be bundled with service access

### Mandatory provisions

- Sender identity in every message
- Easy opt-out in every message
- Right to access data (DSARs)
- Right to deletion
- Records of consent kept for the duration of processing + statute of limitations

### Penalty exposure

GDPR fines up to €20M or 4% of global revenue, whichever is higher.

---

## Canada: CASL

### Consent

- **Express consent**: explicit opt-in (same standard as US TCPA express written consent)
- **Implied consent**: existing business relationship within 24 months: limited use, expires

### Every message must include

- Sender identification (legal name + any operating names)
- Mailing address
- Phone, email, or website contact
- Unsubscribe mechanism that works within 10 business days

### Penalty exposure

Up to CAD $10M per violation. Enforced by the CRTC.

---

## Australia: Spam Act 2003

- Express or inferred consent (inferred has narrow application)
- Sender ID required
- Functional unsubscribe required
- Enforced by ACMA

---

## Multi-jurisdictional programs

If you send across US + EU + Canada simultaneously:

- Default to the **strictest** standard across all jurisdictions (US TCPA express written consent + GDPR explicit opt-in)
- Track consent jurisdiction per subscriber
- Default quiet hours to recipient-local 9am–8pm
- Include all required identifiers in every message

---

## Audit-ready compliance checklist

- [ ] A2P 10DLC registration complete (US, if applicable)
- [ ] Opt-in flow includes all required disclosures, adjacent to phone field
- [ ] Disclosure text matches A2P registered sample messages
- [ ] Opt-in event captures: timestamp, IP, page URL, exact disclosure shown
- [ ] STOP/HELP keywords honored across all variants
- [ ] Quiet hours enforced at platform level (recipient-local time)
- [ ] Privacy policy includes SMS section
- [ ] Terms of service include SMS terms
- [ ] Consent records retained per applicable law (typically 4+ years US, longer EU)
- [ ] Process for handling DSARs (EU) and consent revocation
- [ ] Sender identity in every message
- [ ] Compliance footer on every promotional message (recommended) or quarterly minimum (required)
- [ ] Test STOP/HELP from a real phone number quarterly to verify it still works
