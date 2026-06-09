# Troubleshooting deliverability

Map the reported symptom to a cause, confirm with `dig`, then fix. Always diagnose before changing records.

## "Emails go to the spam folder"

Likely causes, in order:
1. No DMARC, or DMARC fails because nothing aligns. Check `dig +short TXT _dmarc.<domain>` and alignment (see spf-dkim-dmarc.md). Fix: publish aligned DKIM and a DMARC record.
2. DKIM not published / wrong selector. Check `dig +short TXT <selector>._domainkey.<domain>`. Fix: add the exact SenderKit DKIM record.
3. SPF missing, duplicated, or `permerror` (>10 lookups). Check `dig +short TXT <domain>`. Fix: one merged SPF record within the lookup limit.
4. Content/reputation: new domain with no history, spammy content, no `List-Unsubscribe`. Fix: warm up gradually, add unsubscribe headers, clean content.

## "Emails are not arriving at all"

1. Hard bounce / rejected at SMTP: read the bounce message. Common: `550 SPF/DKIM/DMARC` → authentication; `550 user unknown` → bad recipient.
2. Domain not verified with the sender (SenderKit verification token missing). Fix: add the verification TXT from the dashboard.
3. Recipient on a suppression list from a prior bounce/complaint. Fix: remove/relist per provider rules; do not resend blindly.

## "High bounce rate"

1. Invalid addresses → validate at capture; remove hard-bounced addresses.
2. Authentication failures counted as bounces → fix SPF/DKIM/DMARC first.

## "DMARC reports show failures"

- Aggregate (`rua`) reports list sources failing alignment. Identify legitimate senders not yet authenticated and add their includes/DKIM before escalating `p=none` → `quarantine` → `reject`.

## Quick diagnostic block

```bash
dig +short TXT <domain>                         # SPF
dig +short TXT <selector>._domainkey.<domain>   # DKIM
dig +short TXT _dmarc.<domain>                   # DMARC
dig +short MX <domain>                           # MX
```
