# Source notes

This skill was built from:

- SenderKit open-source skills repository: `https://github.com/senderkit/senderkit-skills`
  - Reusable email-deliverability skill folder: `skills/senderkit-email-deliverability/`
  - License: MIT.
- SenderKit docs: `https://docs.senderkit.com`
  - Sending-domain registration issues the DKIM selector/key and a domain-verification token; obtain exact values from the dashboard/docs.
- Email authentication standards (use the RFCs/specs as source of truth over these notes):
  - SPF: RFC 7208 (including the 10-DNS-lookup limit).
  - DKIM: RFC 6376.
  - DMARC: RFC 7489 (policies, alignment, aggregate reporting).
  - BIMI: requires DMARC enforcement (quarantine/reject).
- Standard local tooling: `dig`/`nslookup` for reading published DNS records; no third-party API required.
- Optional manual validators (no key required): mail-tester.com, Google Postmaster Tools, MXToolbox.

Prefer current SenderKit docs/dashboard and the relevant RFCs over this source note when they differ.
