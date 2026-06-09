---
name: senderkit-email-deliverability
description: Diagnose and fix email deliverability and domain authentication so transactional email lands in the inbox instead of spam. Use whenever emails go to spam or are not arriving, or a user wants to set up, fix, or verify SPF, DKIM, DMARC, MX, or DMARC alignment, authenticate a sending domain, improve sender reputation, reduce bounces, or check why mail is rejected or filtered. Works whether mail is sent directly via SenderKit or routed through a provider (Resend, SendGrid, Postmark, Mailgun, SES, SMTP). Diagnoses current DNS with standard tools (dig/nslookup), generates the exact records to add, then verifies them. For wiring sends into code use senderkit-integration; for live test sends use senderkit-mcp-messaging-operations.
---

# SenderKit email deliverability

Use this open-source skill to get authenticated, inbox-landing transactional email. It **diagnoses** a sending domain's authentication, **generates** the exact DNS records to fix it, and **verifies** the result — using standard tools (`dig`/`nslookup`) that need no install, signup, or API key. The reusable source lives at `https://github.com/senderkit/senderkit-skills` in the `skills/senderkit-email-deliverability/` directory; the skill name remains `senderkit-email-deliverability`.

Email authentication is required whether the app sends directly via SenderKit or routes through a provider (Resend, SendGrid, Postmark, Mailgun, SES, SMTP). This skill is provider-agnostic: it reads and fixes the DNS that controls inbox placement.

This skill **does not change application code** and **does not edit DNS** — it inspects DNS, produces records for the user to apply at their DNS host, and re-checks them. To wire sends into the codebase (From domain, headers) use `senderkit-integration`. To send a live test message and confirm placement use `senderkit-mcp-messaging-operations`.

## Workflow

1. Identify the sending domain.
   - Establish the exact `From` domain mail is (or will be) sent from, e.g. `mail.example.com` or `example.com`.
   - If known, note the SenderKit DKIM **selector** and SPF **include** for the account; otherwise the user obtains these from the SenderKit dashboard (see step 4). Do not guess these values.

2. Diagnose current DNS. Read `references/spf-dkim-dmarc.md` for syntax and limits, then query:
   - SPF: `dig +short TXT <domain>` — flag a missing record, more than one `v=spf1` record, syntax errors, and the **10-DNS-lookup limit**.
   - DKIM: `dig +short TXT <selector>._domainkey.<domain>` — confirm the selector is published with a `p=` public key.
   - DMARC: `dig +short TXT _dmarc.<domain>` — confirm presence and policy strength (`p=none` vs `quarantine`/`reject`) and reporting (`rua`).
   - MX: `dig +short MX <domain>` — sanity check.
   - Alignment: confirm SPF (`MAIL FROM`/Return-Path) and DKIM (`d=`) align with the visible `From` domain.

3. Generate the records to add.
   - Produce the exact TXT records for the diagnosed faults (one consolidated SPF record; DKIM as published by SenderKit; a DMARC record starting at `p=none` for monitoring, then escalating).
   - Never produce a second `v=spf1` record; merge includes into the existing one.

4. SenderKit handoff for issued values.
   - DKIM key/selector and the domain-verification token are issued when a sending domain is registered with SenderKit. There is no MCP tool for this yet — direct the user to the SenderKit dashboard/docs to copy the exact DKIM record and verification token, then add them alongside the records from step 3.
   - If a future SenderKit domain-management tool/endpoint is available at runtime, use it here to fetch the records instead of asking the user to copy them.

5. Verify.
   - Re-run the `dig` queries from step 2 to confirm publication. Set expectations: DNS propagation is eventually-consistent (minutes to hours); offer a re-check rather than asserting instant success.
   - Optionally suggest a manual validator (mail-tester.com, Google Postmaster Tools, MXToolbox) — these are optional and require no key.
   - Optionally use `senderkit-mcp-messaging-operations` to send a live test and confirm inbox placement and that headers pass SPF/DKIM/DMARC.

6. Code-side follow-ups (optional, defer depth to `senderkit-integration`).
   - Ensure the app `From` domain matches the authenticated domain.
   - Ensure `List-Unsubscribe` and `List-Unsubscribe-Post` headers are present on bulk-ish transactional mail.
   - For deeper code changes, hand off to `senderkit-integration`.

When a symptom is reported ("going to spam", "not arriving", "bouncing"), read `references/troubleshooting.md` and map symptom → cause → fix before changing records.

## Reference files

- `references/spf-dkim-dmarc.md` - SPF/DKIM/DMARC concepts, record syntax, the 10-lookup limit, alignment, and a BIMI note.
- `references/dns-provider-notes.md` - Where and how to add TXT records on common DNS hosts.
- `references/troubleshooting.md` - Symptom → likely cause → fix for spam folder, bounces, and non-delivery.
- `references/sources.md` - Source notes used to build this skill.

## Standards

- Diagnose before prescribing: never tell a user to add a record without first reading what is published.
- Keep exactly one SPF record per domain; stay within 10 DNS lookups.
- Recommend DMARC starting at `p=none` with `rua` reporting, then escalating to `quarantine`/`reject` after monitoring.
- Do not fabricate SenderKit DKIM selectors, SPF includes, or verification tokens; use the values SenderKit issues.
- Treat current SenderKit docs/dashboard as source of truth over this skill's static notes.
