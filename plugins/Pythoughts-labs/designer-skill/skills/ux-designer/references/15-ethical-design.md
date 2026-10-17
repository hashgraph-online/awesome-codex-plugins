# Ethical Design & Dark Patterns

Deceptive design patterns face increasing regulatory enforcement with real financial penalties. This reference provides a taxonomy of dark patterns, the regulatory landscape, and practical guidance for ethical design.

---

## Dark Pattern Taxonomy

### 1. Roach Motel
Easy to get into, hard to get out of.

```
❌ Sign up: 1 click → Cancel: call a phone number during business hours
✅ Sign up: 1 click → Cancel: 1 click in the same place
```

- Subscription cancellation buried in settings or requiring phone calls
- Account deletion requiring email to support team
- Free trial that auto-converts with no easy cancellation

### 2. Confirmshaming
Using guilt-laden language to manipulate decisions.

```
❌ "No thanks, I don't want to save money"
❌ "I'll pass on protecting my family"
✅ "No thanks" / "Not now" / "Skip"
```

- Opt-out buttons using shame language
- Modal dismissals that imply user is making a bad choice
- Emotional manipulation in decline copy

### 3. Misdirection
Drawing attention away from important information.

```
❌ Large "Accept All" button, tiny "Manage preferences" link
✅ Equal-sized "Accept" and "Reject" buttons side by side
```

- Visual emphasis on the choice that benefits the company
- Using color, size, and position to guide toward preferred option
- Burying important notices in walls of text

### 4. Forced Continuity
Silently charging after a free trial without adequate notice.

```
❌ Free trial ends → auto-charge with no warning
✅ Free trial ends → email 7 days before → email 1 day before → charge
```

- No reminder before trial-to-paid conversion
- Making it hard to find the charge after conversion
- Requiring payment info for "free" trials without clear disclosure

### 5. Hidden Costs
Revealing unexpected charges late in the checkout process.

```
❌ $29.99 product → checkout reveals $8.99 shipping + $4.99 "service fee"
✅ Show total cost including all fees from the product page
```

- Drip pricing (adding fees throughout checkout)
- Service fees, processing fees, convenience fees added at the end
- Mandatory add-ons pre-selected in checkout

### 6. Trick Questions
Confusing wording that causes users to make unintended choices.

```
❌ "Uncheck this box if you prefer not to not receive emails"
✅ "Check this box to receive marketing emails" (unchecked by default)
```

- Double negatives in opt-out language
- Confusing toggle labels (is "on" opting in or out?)
- Swapping the expected position of yes/no buttons

### 7. Bait & Switch
Promising one thing and delivering another.

```
❌ "Free download" → requires paid subscription to access
✅ Clear pricing and feature comparison before any action
```

- Advertising features only available in premium tiers
- Changing terms after user commitment
- "Free" products that require payment for core functionality

### 8. Disguised Ads
Ads designed to look like content or navigation elements.

```
❌ "Download" buttons that are actually ads
✅ Clearly labeled "Advertisement" or "Sponsored" with visual distinction
```

- Native ads without clear sponsorship labels
- Fake download buttons or system alerts
- Content recommendation widgets that mix ads with real content

### 9. Friend Spam
Using access to contacts for unauthorized messaging.

```
❌ "Find friends" → sends invites to entire address book without review
✅ "Find friends" → shows contact list for user to select individually
```

- Auto-importing and messaging contacts
- "Invite friends" defaulting to select-all
- Social sharing without clear preview of what will be posted

### 10. Privacy Zuckering
Making privacy settings confusing to encourage maximum data sharing.

```
❌ 47 pages of privacy settings across 8 different menus
✅ Single privacy dashboard with clear toggles and plain-language explanations
```

- Default to maximum data sharing
- Privacy controls scattered across multiple screens
- Confusing privacy policy language

### 11. Sneak into Basket
Adding extra items to the shopping cart without user consent.

```
❌ Pre-selected insurance, warranties, or add-ons in checkout
✅ All add-ons presented as opt-in with clear pricing
```

- Pre-checked donation or insurance boxes
- Default-selected premium shipping
- Mandatory bundles disguised as individual products

---

## Regulatory Landscape

### FTC (United States)
- **Click-to-Cancel Rule (2024)**: Must be as easy to cancel as to subscribe
- **Amazon settlement ($25M, 2023)**: Deceptive Prime enrollment/cancellation
- **Fortnite/Epic ($245M, 2022)**: Dark patterns in children's purchases
- Enforcement focus: subscriptions, negative option marketing, COPPA violations

### EU Digital Services Act (DSA)
- Prohibits dark patterns on online platforms
- Bans: deceptive UI, manipulated choices, repeated nagging, obstruction of cancellation
- Applies to: all online intermediaries, with stricter rules for very large platforms
- Effective: February 2024

### EU Digital Fairness Act (Upcoming)
- Extends dark pattern protections to all digital services
- Covers addictive design, virtual currencies, influencer marketing
- Expected proposal: 2025-2026

### GDPR (EU)
- Consent must be freely given, specific, informed, and unambiguous
- Pre-checked consent boxes are invalid
- Withdrawing consent must be as easy as giving it
- Maximum penalty: 4% of annual global turnover or €20M

### California CPRA
- Extends CCPA with additional consent requirements
- "Do Not Sell or Share My Personal Information" link required
- Equal prominence for opt-out as opt-in
- Dark pattern consent is not valid consent

### COPPA (US Children's Privacy)
- Verifiable parental consent for under-13 data collection
- No behavioral advertising to children
- FTC actively enforcing against manipulative design targeting minors

---

## Consent Design

### Button Parity

```css
/* ❌ Dark pattern: asymmetric buttons */
.accept-btn {
  background: #0066cc;
  color: white;
  font-size: 16px;
  padding: 12px 24px;
}
.reject-link {
  color: #999;
  font-size: 12px;
  text-decoration: underline;
}

/* ✅ Ethical: equal prominence */
.consent-btn {
  font-size: 16px;
  padding: 12px 24px;
  border-radius: 6px;
}
.consent-btn.accept {
  background: #0066cc;
  color: white;
}
.consent-btn.reject {
  background: white;
  color: #0066cc;
  border: 2px solid #0066cc;
}
```

### Consent Best Practices

- Accept and reject buttons must have **equal visual weight**
- No pre-checked boxes for optional data processing
- Clear, plain-language explanation of what users are consenting to
- Granular control: let users accept some and reject others
- Withdrawing consent must be as easy as giving it (same number of clicks)
- No "consent walls" that block access unless all is accepted (unless strictly necessary)
- Record consent with timestamp and version for compliance

---

## Cookie / Privacy UX

### Banner Design

```
┌─────────────────────────────────────────────────────┐
│  We use cookies to improve your experience.         │
│  [Learn more]                                       │
│                                                     │
│  [Accept All]  [Reject All]  [Manage Preferences]   │
└─────────────────────────────────────────────────────┘
```

**Requirements:**
- Show on first visit only (persist choice)
- No page interaction tracking before consent
- "Reject All" must be as prominent as "Accept All"
- Brief, clear description of cookie purposes
- Link to full privacy policy

### Preference Center

```
┌─ Cookie Preferences ────────────────────┐
│                                          │
│  Necessary         [Always on]           │
│  Authentication, security, basic         │
│  functionality                           │
│                                          │
│  Analytics         [○ Off]               │
│  Anonymous usage statistics              │
│                                          │
│  Marketing         [○ Off]               │
│  Personalized ads and content            │
│                                          │
│  Social Media      [○ Off]               │
│  Social sharing and embeds               │
│                                          │
│  [Save Preferences]  [Reject All]        │
└──────────────────────────────────────────┘
```

- Default all optional categories to OFF
- Clear descriptions for each category
- Easy toggle interface
- "Reject All" shortcut available
- Accessible from footer link at all times (not just the banner)

---

## Subscription & Cancellation

### FTC Click-to-Cancel Rule

The cancellation process must be as simple as the sign-up process.

```
Sign-up:     Product page → Click "Subscribe" → Enter payment → Done (3 steps)
Cancellation: Settings → Click "Cancel" → Confirm → Done (3 steps max)

❌ Cancel: Settings → Account → Billing → "Contact support" → Phone wait →
   Agent pitch → Second pitch → "Are you sure?" → "Last chance offer" → Cancel
```

### Ethical Subscription Patterns

- Cancel button in the same location as the subscribe button
- No retention dark patterns (forced phone calls, multi-step cancellation)
- Show clear summary of what will happen on cancellation (access end date, data retention)
- Offer pause/downgrade as alternatives, not barriers
- Send cancellation confirmation immediately
- Allow easy resubscription if the user changes their mind

---

## Pricing Transparency

### Drip Pricing Avoidance

```
❌ Drip pricing:
   Product: $99 → Cart: $99 + $15 shipping → Checkout: $99 + $15 + $5.99 service fee

✅ Transparent pricing:
   Product: $119.99 (includes shipping & all fees)
   — or —
   Product: $99 + Shipping: $15 + Fees: $5.99 = Total: $119.99 (shown from start)
```

- Show total price including all mandatory fees as early as possible
- Break down fees clearly if itemized
- No surprise charges at checkout
- Currency and tax handling clear for international users
- Comparison pricing (strikethrough) must reference genuine previous prices

---

## Children & Vulnerable Users

### Age-Appropriate Design (AADC / ICO Code)

- Age verification at entry points (not just a "I am over 13" checkbox)
- Default to maximum privacy for minors
- No nudge techniques to encourage more data sharing
- No reward loops or variable reward schedules (addictive patterns)
- Parental controls accessible but not bypassable by children
- No profiling of children for personalization or advertising

### Addictive Pattern Avoidance

```
❌ Addictive patterns:
  - Infinite scroll with no natural stopping point
  - Pull-to-refresh with variable rewards
  - Streak counters that penalize breaks
  - Autoplay with no natural stopping point
  - Social approval metrics (like counts) as primary feedback

✅ Ethical alternatives:
  - "You're all caught up" markers
  - Daily digest summaries
  - "Time spent" dashboards
  - Intentional session boundaries
  - Content-focused rather than metric-focused design
```

---

## Ethical Design Checklist

### Pre-Launch Review

- [ ] **Symmetry**: Is it equally easy to opt out as to opt in?
- [ ] **Clarity**: Would a non-technical person understand what they're agreeing to?
- [ ] **Button parity**: Are accept/reject options equally prominent?
- [ ] **No pre-selection**: Are optional choices defaulted to off/unchecked?
- [ ] **No confirmshaming**: Is decline language neutral and respectful?
- [ ] **Pricing transparency**: Are all fees visible before the final step?
- [ ] **Cancellation ease**: Can users cancel in the same number of steps as subscribing?
- [ ] **Privacy defaults**: Are privacy settings defaulted to the most protective option?
- [ ] **Consent validity**: Is consent freely given, specific, informed, and unambiguous?
- [ ] **Children's safety**: Are there protections for underage users?
- [ ] **No misdirection**: Is the visual hierarchy honest about what options do?
- [ ] **Audit trail**: Are consent records stored with timestamps and versions?

### Ongoing Monitoring

- Track unsubscribe/cancellation completion rates (should be near 100%)
- Monitor complaint rates related to billing or consent
- Review A/B tests for dark pattern creep (optimization that exploits users)
- Regular accessibility audit of consent interfaces
- Legal review of consent flows against current regulations

---

## Key Metrics

| Metric | Target | Context |
|--------|--------|---------|
| Consent rejection rate | Monitor (not minimize) | High rejection is honest UX |
| Cancel completion rate | > 95% | Easy cancellation |
| Complaint rate | < 0.1% | Billing/consent complaints |
| Cookie preference usage | Track | Users exercising choice |
| Time to cancel | ≤ sign-up time | Click-to-cancel compliance |

---

## Sources

- [FTC Dark Patterns Report (2022)](https://www.ftc.gov/reports/bringing-dark-patterns-light) — Regulatory guidance
- [Deceptive Design](https://www.deceptive.design/) — Harry Brignull's dark pattern catalog
- [EU Digital Services Act](https://digital-strategy.ec.europa.eu/en/policies/digital-services-act-package) — Platform regulation
- [GDPR consent guidelines](https://edpb.europa.eu/our-work-tools/documents/public-consultations/2020/guidelines-052020-consent-under-regulation_en) — EDPB guidance
- [ICO Age Appropriate Design Code](https://ico.org.uk/for-organisations/childrens-code-hub/) — Children's privacy
- [Nielsen Norman Group: Dark Patterns](https://www.nngroup.com/articles/dark-patterns/) — UX research
- [CPRA regulations](https://cppa.ca.gov/) — California privacy enforcement
