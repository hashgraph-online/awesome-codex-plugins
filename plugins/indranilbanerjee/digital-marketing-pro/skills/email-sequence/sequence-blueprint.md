# Email sequence — cadence, per-email blueprint, branching, output layout, and follow-ups

Read this when you are sizing a sequence, writing each email, defining branching and suppression, laying out the deliverable, or offering next steps. It supplements `SKILL.md`; the brand-loading step and the bulk-sender checklist there are authoritative.

## Sequence types (ask if not given)

Welcome series (new subscriber/user) · nurture sequence (move leads down the funnel) · onboarding (activate new users/customers) · re-engagement (win back inactive subscribers) · cart abandonment (recover lost purchases) · post-purchase (retention, upsell, review request) · event-based (webinar, product launch, seasonal) · promotional (sale, offer, limited-time).

Also gather: the goal (activate, convert, retain, upsell, educate, re-engage), the audience segment and what triggers entry (signup, purchase, inactivity period, cart event), the desired email count (or recommend one), key messages or offers, and the ESP in use for format and feature guidance. Apply email-specific tone overrides from the brand guidelines if present, and the compliance rules (CAN-SPAM, GDPR, CASL) for the brand's target markets.

## Sequence architecture

- Map the sequence to the customer journey stage.
- Define the narrative arc: introduction → value → proof → conversion.
- Size by type (a starting point; adjust to the audience and offer):

| Type | Emails | Window |
|---|---|---|
| Welcome | 3-5 | 7-14 days |
| Nurture | 5-8 | 3-6 weeks |
| Onboarding | 4-7 | 14-30 days |
| Re-engagement | 3-4 | 7-14 days |
| Cart abandonment | 3 | 3 days |
| Post-purchase | 3-5 | 30-60 days |

- Define send cadence and timing logic.

## Per-email blueprint

**Subject lines**
- 2-3 options per email
- Character counts (aim for 30-50 characters for mobile)
- Preview text that complements, not repeats, the subject
- A/B testing recommendations

**Body copy**
- Opening hook tied to the sequence narrative
- Body content with clear hierarchy and scannable formatting
- Single primary CTA (button text + destination)
- Secondary CTA (optional, text link)
- Personalization tokens (first name, company, product, behavior-based)
- Dynamic content blocks (based on segment attributes)

**Timing**
- Send delay from trigger or previous email
- Best send time recommendation (day of week, time of day)
- Timezone handling notes

## Segmentation and branching logic

- Entry trigger conditions
- Branching rules based on engagement (opened, clicked, converted)
- Exit conditions (converted, unsubscribed, completed sequence)
- Suppression rules (already purchased, already in another sequence)

## Per-email deliverability checklist

For each email, verify:
- No spam trigger words in subject or body
- Link density appropriate (not too many links)
- Image-to-text ratio balanced
- Unsubscribe link present and functional
- Physical address included (CAN-SPAM)
- Authentication reminders (SPF, DKIM, DMARC)
- List hygiene recommendations

## Deliverable layout

### Sequence overview
- Sequence name, type, and goal
- Target audience and entry trigger
- Email count and total duration
- Expected performance benchmarks for the sequence type

### Email-by-email breakdown

| Email # | Subject Line | Send Timing | Goal | Primary CTA |
|---------|-------------|-------------|------|-------------|

Followed by the full copy for each email.

### Flow diagram
A visual representation of the flow with branching logic: Entry → Email 1 → Wait → Email 2 → Branch (opened / not opened) → …

### Performance benchmarks

| Metric | Industry Average | Target |
|--------|-----------------|--------|

Include open rate, click rate, conversion rate, and unsubscribe rate per email. Label any industry average that is not sourced as an estimate.

## After the sequence

Ask: "Would you like me to:
- Set up this sequence in your ESP? (`/digital-marketing-pro:send-email-campaign`)
- Create A/B test variants for the subject lines? (`/digital-marketing-pro:prompt-test`)
- Design a complementary re-engagement flow for non-openers?
- Build landing pages for the CTA destinations? (`/digital-marketing-pro:content-engine`)
- Add SMS touchpoints alongside the emails? (`/digital-marketing-pro:send-sms`)
- Review deliverability setup for your domain? (`/digital-marketing-pro:email-sequence` with deliverability focus)"
