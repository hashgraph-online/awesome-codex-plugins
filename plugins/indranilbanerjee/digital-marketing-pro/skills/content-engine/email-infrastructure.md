# Email Infrastructure — Authentication & Deliverability

## SPF (Sender Policy Framework)

### What It Does
Specifies which mail servers are authorized to send email on behalf of your domain.

### Setup
1. Identify all services that send email from your domain (ESP, CRM, transactional email, support)
2. Create a TXT record on your domain:
```
v=spf1 include:_spf.google.com include:sendgrid.net include:amazonses.com ~all
```
3. **Important limits**: Maximum 10 DNS lookups. Each `include:` counts as one lookup.
4. Use `~all` (softfail) during testing, switch to `-all` (hardfail) once confirmed.

---

## DKIM (DomainKeys Identified Mail)

### What It Does
Adds a digital signature to outgoing emails proving the message hasn't been altered.

### Setup
1. Generate a DKIM key pair in your ESP (public + private key)
2. Add the public key as a TXT record:
```
selector._domainkey.yourdomain.com TXT "v=DKIM1; k=rsa; p=[public key]"
```
3. ESP signs outgoing emails with the private key
4. Receiving servers verify using the public key in DNS
5. Use 2048-bit keys (1024-bit is minimum, 2048 recommended)

---

## DMARC (Domain-based Message Authentication)

### What It Does
Tells receiving servers what to do when SPF or DKIM fail, and sends reports to you.

### Setup (Progressive)

**Phase 1: Monitoring** (start here)
```
_dmarc.yourdomain.com TXT "v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com; pct=100"
```

**Phase 2: Quarantine** (after reviewing reports for 2-4 weeks)
```
v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com; pct=25
```
Gradually increase `pct` from 25 → 50 → 100.

**Phase 3: Reject** (when confident all legitimate senders are authenticated)
```
v=DMARC1; p=reject; rua=mailto:dmarc@yourdomain.com; ruf=mailto:dmarc@yourdomain.com
```

---

## BIMI (Brand Indicators for Message Identification)

### Requirements
1. DMARC policy must be at `p=quarantine` or `p=reject`
2. SVG logo file meeting BIMI specifications
3. A mark certificate from an issuer such as DigiCert or Entrust: a VMC (Verified Mark Certificate; needs a registered trademark; Gmail shows a verified checkmark) or a CMC (Common Mark Certificate; logo only, no checkmark; Gmail accepts it since 2024-09-24, [Workspace Updates](https://workspaceupdates.googleblog.com/2024/09/gmail-additional-bimi-protections.html)). Both carry an annual fee: check the issuer's current price
4. DNS record:
```
default._bimi.yourdomain.com TXT "v=BIMI1; l=https://yourdomain.com/logo.svg; a=https://yourdomain.com/cert.pem"
```

### Benefits
- Brand logo displays next to emails in supported clients (Gmail, Yahoo)
- Recognition in the inbox (vendor studies claim higher opens, but opens are inflated by Apple Mail Privacy Protection: judge it on clicks)

---

## Domain Warming Plan

For new sending domains or IPs:

| Day | Daily Volume | Notes |
|-----|-------------|-------|
| 1-3 | 50-100 | Send to most engaged subscribers only |
| 4-7 | 200-500 | Expand to recently engaged |
| 8-14 | 500-2,000 | Gradually add segments |
| 15-21 | 2,000-5,000 | Continue expanding |
| 22-30 | 5,000-10,000 | Approaching normal volume |
| 31-45 | 10,000-50,000 | Ramp to full volume |
| 46+ | Full volume | Normal sending |

### Warming Rules
- Send to engaged users first (opened in last 30 days)
- Monitor bounce rate (<2%), spam complaints (<0.1%), and inbox placement
- If bounce rate spikes or deliverability drops, reduce volume and investigate
- Don't skip days — consistency matters
- Avoid promotional content during warming — send value-first content

---

## Deliverability Best Practices

### List Hygiene
- Remove hard bounces immediately (never retry)
- Suppress soft bounces after 3 consecutive failures
- Remove unengaged subscribers after 6-12 months without a click, a purchase or site activity (opens can't prove engagement: Apple Mail Privacy Protection fires them automatically)
- Run email verification on old/imported lists before sending
- Clean list quarterly

### Sending Practices
- Maintain consistent sending schedule (ISPs expect predictable patterns)
- Keep spam complaint rate below 0.1% (Google requires <0.3%)
- Include clear unsubscribe link in every email
- Honor unsubscribes within 2 days (Gmail: within 48 hours; Yahoo: within 2 days) — aim for instant
- Segment and personalize (better engagement = better deliverability)

### Content Practices
- Balanced text-to-image ratio (not image-only emails)
- Avoid spam trigger words in subject lines and body
- Include physical mailing address (CAN-SPAM requirement)
- Use a recognizable "From" name
- Preheader text should be intentional (not "View in browser")

---

## Debugging Deliverability Issues

| Symptom | Likely Cause | Investigation |
|---------|-------------|--------------|
| Emails going to spam | Authentication failure, poor reputation | Check SPF/DKIM/DMARC, review content |
| Low open rates suddenly | Inbox placement dropped | Check Google Postmaster Tools, seed testing |
| High bounce rate | Stale list, bad data | Run verification, check acquisition source |
| Blacklisted | Spam complaints exceeded threshold | Check blacklist databases, submit delisting request |
| Gmail tabs (Promotions) | Content signals | Reduce images, simplify formatting |
| Apple Mail categories (Promotions) | Apple Mail sorts mail into Primary, Transactions, Updates and Promotions; a time-sensitive message in the other three also shows in Primary ([Apple support](https://support.apple.com/guide/icloud/use-categories-mmafbebd3108/icloud), read 2026-10-28) | Send receipts and shipping notices from a transactional stream, keep marketing out of it, and don't fake urgency |
