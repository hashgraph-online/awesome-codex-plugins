# SenderKit Email Deliverability Skill

This directory contains a portable, open-source agent skill for diagnosing and fixing email domain authentication (SPF/DKIM/DMARC). The canonical source is `https://github.com/senderkit/senderkit-skills`, and this reusable skill lives in `skills/senderkit-email-deliverability/`.

For any coding assistant or LLM:

1. Read `SKILL.md` first.
2. Follow the workflow in order: identify → diagnose → generate → SenderKit handoff → verify → optional code-side follow-ups.
3. Load reference files only when relevant:
   - `references/spf-dkim-dmarc.md`
   - `references/dns-provider-notes.md`
   - `references/troubleshooting.md`
4. Diagnose published DNS with `dig`/`nslookup` before prescribing records. Never fabricate SenderKit DKIM selectors, SPF includes, or verification tokens — use the values SenderKit issues.

This skill does not edit DNS or application code; it inspects DNS, generates records to apply, and verifies them. For code changes use `senderkit-integration`; for live test sends use `senderkit-mcp-messaging-operations`.
