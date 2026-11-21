# Benchmarks, Deliverability, and Common Mistakes

Use these numbers to calibrate a plan, never to promise a result. They are
directional ranges from published outbound studies, and they move year to year.
The user's own last 90 days of sends beat any table here.

## Directional performance ranges (B2B, 2024 to 2026)

| Metric | Weak | Typical | Strong | Notes |
|---|---|---|---|---|
| Reply rate | under 2% | 3 to 6% | 8%+ | Reply rate is the metric to manage; opens are unreliable |
| Positive share of replies | under 30% | 40 to 50% | 60%+ | A high reply rate with low positive share means the targeting is off |
| Meeting rate per contact | under 0.5% | 0.5 to 1.5% | 2%+ | Depends on offer and ACV more than copy |
| Hard bounce rate | over 3% | 1 to 2% | under 1% | Above 2% is a list-hygiene problem, not a copy problem |

Open rates stopped being trustworthy after Apple Mail Privacy Protection began
preloading images in 2021, and many cold senders now turn open tracking off to
protect deliverability. Do not report open rate as proof that a subject line
worked. Use replies.

A rough funnel for planning: 1,000 delivered emails, 30 to 60 replies, 12 to 30
positive replies, 5 to 15 meetings. Replace every number with the user's own
data the moment it exists.

## What moves reply rate, in rough order

1. **Targeting.** A tight list of people who have the problem now beats any copy
   change. Small, segment-specific campaigns outperform one large blast.
2. **Relevance of the opening line.** An observation tied to the problem you
   solve. A compliment that leads nowhere does not count.
3. **Brevity.** Under 75 words for a first touch. Short sentences, plain words,
   roughly a 5th to 7th grade reading level.
4. **A low-friction ask.** An interest question ("worth a look?") beats a
   30-minute meeting request on first touch.
5. **Follow-up.** The first email draws most replies (about 58% in Instantly's
   2026 benchmark); the other ~42% arrive on follow-ups. Each follow-up must
   carry something new.
6. **Contacts per account.** One or two people per company. Ten people at one
   company get the domain flagged and annoy the buyer.

Send day and hour are weak levers. Test them only after the five above are
solid, and in the prospect's local time.

## Deliverability rules that apply to cold email (verified October 2026)

Cold email is commercial email. The mailbox providers do not exempt it, and a
burned domain costs more than any copy improvement earns.

**Gmail (personal accounts).** A sender that sends close to 5,000 or more
messages to personal Gmail accounts in 24 hours is a bulk sender, and that
status does not expire. Bulk senders need SPF and DKIM, a DMARC record (p=none
is the minimum) with the From domain aligned to SPF or DKIM, one-click
unsubscribe via RFC 8058 List-Unsubscribe headers on marketing and promotional
mail, and unsubscribe requests honored within 48 hours. Keep the user-reported
spam rate below 0.1% and never let it reach 0.3%. Starting November 2025 Gmail
ramped up enforcement, so non-compliant mail now sees temporary and permanent
rejections. Source: Google Email sender guidelines FAQ,
https://support.google.com/mail/answer/14229414

**Yahoo.** Mirrors the Gmail bulk requirements (authentication, DMARC,
one-click unsubscribe, low complaint rate). Source:
https://senders.yahooinc.com/best-practices/

**Microsoft (Outlook.com, Hotmail, Live).** Since May 5, 2025, domains sending
more than 5,000 messages a day must pass SPF, DKIM, and DMARC (p=none minimum,
aligned with SPF or DKIM). Non-compliant mail is junked and then rejected with
`550; 5.7.515 Access denied`. Source: Microsoft Outlook blog, "Strengthening
Email Ecosystem: Outlook's New Requirements for High-Volume Senders",
https://techcommunity.microsoft.com/blog/outlook/strengthening-email-ecosystem-outlook%E2%80%99s-new-requirements-for-high%E2%80%90volume-senders/4399730

**US law (CAN-SPAM).** Honest headers and subject, identification as an ad
where applicable, a valid physical postal address, a working opt-out, and
opt-outs honored within 10 business days. Source: FTC, CAN-SPAM Act compliance
guide, https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business

**EU, UK, Canada.** Cold B2B email is restricted under GDPR plus ePrivacy rules
(UK PECR) and Canada's CASL. Route any program that mails these regions to
qualified legal review before sending. This skill does not decide lawful basis.

Operating rules that follow from the above:

- Send cold outreach from a separate subdomain or secondary domain, never the
  primary domain that carries invoices and password resets.
- Warm new mailboxes gradually and keep per-mailbox daily volume low.
- Verify every address before sending; a hard bounce rate above 2% is a stop.
- Plain text, one link at most, no images or attachments on first touch.
- Watch Google Postmaster Tools and Microsoft SNDS weekly.

## Mistakes ranked by damage

1. **Too long.** Three paragraphs about your company. Cut to the problem, the
   proof, and the ask.
2. **Self-focused.** Count the "we" sentences. If they outnumber "you," rewrite.
3. **No reason for this person, now.** If the email could go to anyone in the
   segment unchanged, it is a template.
4. **Fake personalization.** "Loved your post!" with no specifics reads as
   automation.
5. **Big ask on first touch.** A 30-minute call before the reader agrees there
   is a problem.
6. **Unsupported claims.** "300% more leads" without a named, checkable source.
7. **Too many contacts at one company.**
8. **Fake urgency or fake reply chains.** "Re:" on a first email destroys trust.
9. **"Just checking in" follow-ups.** No new value, no reason to reply.
10. **Ignoring deliverability.** No authentication, no warmup, no bounce
    control. Great copy in the spam folder earns nothing.

## Regional calibration

| Region | Tone | Length | Proof that lands |
|---|---|---|---|
| US | Direct, casual | Shortest | Outcome numbers |
| UK | Polite, professional | Slightly longer, insight-led | Research-backed credibility |
| DACH | Precise | Detail-oriented | Technical specifics |
| Nordics | Fact-based, egalitarian | Concise but substantive | Shared values, plain facts |
