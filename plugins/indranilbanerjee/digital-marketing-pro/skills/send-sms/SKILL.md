---
name: send-sms
description: "Send SMS or WhatsApp messages. Use when: deploying marketing messages via Twilio or Brevo with compliance checks."
disable-model-invocation: true
argument-hint: "[message-type]"
---

# /digital-marketing-pro:send-sms

## Purpose

Send an SMS or WhatsApp marketing message via Twilio or Brevo with mandatory compliance checks, consent verification, quiet hours enforcement, and delivery tracking. SMS and WhatsApp are high-impact, high-risk channels — messages reach personal devices instantly with near-100% open rates, which means compliance failures carry significant legal and reputational consequences. This command enforces every required safeguard before any message leaves the system: TCPA consent for US recipients, GDPR consent for EU, CASL for Canada, opt-out mechanism presence, quiet hours respect, and message length compliance. No message is sent without passing all gates and receiving explicit user approval.

## Input Required

The user must provide (or will be prompted for):

- **Message content**: The SMS or WhatsApp message body — must include a clear opt-out mechanism (e.g., "Reply STOP to unsubscribe") for regulatory compliance. WhatsApp messages may include rich media (image, document, video, or location) and must use pre-approved message templates for business-initiated conversations per Meta's policy
- **Recipient(s)**: Phone number(s) in E.164 format (+1XXXXXXXXXX), a named contact list from the brand's audience data, or a segment reference. For bulk sends, provide a CSV file path or list identifier. Each recipient must have documented consent on file
- **Channel**: `sms` or `whatsapp` — determines message length limits (160 chars SMS, 1,024 chars WhatsApp), media support (text-only SMS vs. rich media WhatsApp), template requirements, and platform-specific compliance rules
- **Sender ID (optional)**: The sender phone number, short code, or alphanumeric sender ID to use — must be registered and verified on the platform. If omitted, uses the brand's default sender configured in the messaging MCP. Alphanumeric sender IDs are not supported in all countries
- **Send time**: `immediate` for instant delivery or a scheduled date and time with timezone (ISO 8601 format). Scheduling must respect quiet hours — no sends between 9pm and 8am in the recipient's local time zone
- **Campaign name (optional)**: For tracking and attribution — links this send to a campaign in the brand's analytics and performance reporting. If omitted, auto-generated from message content and date
- **Personalization fields (optional)**: Dynamic fields to merge into the message — first name, order number, appointment time, loyalty points, or custom variables. Each field requires a fallback default for recipients with missing data (e.g., "Valued Customer" for missing first name)
- **WhatsApp template ID (optional)**: For WhatsApp business-initiated messages, the pre-approved template identifier with variable mappings. Required by Meta for messages sent outside the 24-hour customer service window
- **Priority (optional)**: `normal` (standard delivery queue) or `urgent` (priority delivery for time-sensitive messages like appointment reminders or security alerts). Urgent sends skip scheduling optimization but still enforce all compliance checks

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Verify consent compliance**: Check that all recipients have documented opt-in consent for the selected channel. Apply jurisdiction-specific rules — TCPA express written consent for US recipients, GDPR explicit consent with recorded lawful basis for EU, CASL express or implied consent with expiration tracking for Canada. Flag any recipients missing required consent and exclude them from the send with a per-recipient compliance report.
3. **Enforce quiet hours**: Determine each recipient's timezone from phone number country code and area code where deterministic, or from stored audience profile data. Block any immediate sends where the recipient's local time falls between 9pm and 8am. For scheduled sends, verify the scheduled time respects quiet hours in all recipient timezones. Flag conflicts and suggest the nearest compliant send window.
4. **Validate opt-out mechanism**: Scan the message body for a compliant opt-out instruction — "Reply STOP to unsubscribe" or jurisdiction-appropriate equivalent. For WhatsApp, verify the opt-out flow is configured in the business account settings. If missing or non-compliant, reject the send and require the user to add opt-out language before proceeding.
5. **Check message length**: Validate message length against channel limits — 160 characters per SMS segment (concatenated messages up to 1,600 characters with segment count and cost warning), 1,024 characters for WhatsApp text. For personalized messages, calculate length with the longest possible variable substitution to ensure no recipient receives a truncated message. Report character count, segment count, and per-message cost.
6. **Verify messaging MCP connection**: Check which messaging platform MCP is connected — Twilio or Brevo — and confirm it supports the selected channel (SMS, WhatsApp, or both). Verify sender ID is registered, authorized, and compliant with the destination country's sender ID regulations. If not connected, guide the user through integration setup.
7. **Score brand voice**: Run `brand-voice-scorer.py` on the message content to verify alignment with brand tone guidelines. SMS requires concise, direct messaging — flag content that is off-brand, overly formal for the channel, or could be misinterpreted in short-form context without visual cues.
8. **Create approval record**: Run `approval-manager.py` with risk level set to HIGH — SMS and WhatsApp marketing carries regulatory exposure (TCPA fines up to $1,500 per unsolicited message) and per-message cost. Generate a comprehensive send summary for review.
9. **Present send summary**: Display the complete summary — message preview with personalization tokens resolved for a sample recipient, recipient count (total, eligible after compliance filtering, excluded with reasons), channel, sender ID, send time with quiet hours verification, compliance checklist (consent, quiet hours, opt-out, sender verification), estimated cost per message and total send cost, SMS segment count if applicable, and brand voice score. Wait for explicit "send" confirmation.
10. **Execute send via MCP**: On approval, trigger the message send through the connected Twilio or Brevo MCP. Handle personalization token replacement per recipient, batch processing for bulk sends with rate limiting, WhatsApp template variable injection, and platform-specific API formatting. Monitor for immediate delivery failures and API errors.
11. **Track delivery**: Poll the messaging platform API for delivery status updates — delivered, failed, undelivered, queued, or read (WhatsApp only). Track per-recipient status for bulk sends. Alert the user if delivery failure rate exceeds 5% with categorized failure reasons (invalid numbers, carrier blocks, opt-outs processed, network timeouts).
12. **Log execution**: Run `execution-tracker.py` to log the send event with timestamp, platform, channel, campaign name, recipient count (total and per-status), message content hash, compliance verification results, delivery metrics, cost incurred, and any failures. Save a performance insight for future SMS strategy optimization and send-time analysis.

## Output

A structured send confirmation containing:

- **Send confirmation**: Message ID or batch ID, platform (Twilio or Brevo), channel (SMS or WhatsApp), send status (sent, scheduled, partially sent, or held for approval), and timestamp with timezone
- **Recipient details**: Total recipients submitted, recipients eligible after compliance filtering, recipients excluded with per-recipient reason (consent missing with jurisdiction cited, quiet hours violation with timezone, invalid number format), and recipients in the final send list
- **Compliance report**: Pass/fail for each check — TCPA consent (US), GDPR consent (EU), CASL consent (Canada), opt-out mechanism present and compliant, quiet hours respected across all recipient timezones, sender ID verified and country-compliant, and WhatsApp template approved (if applicable)
- **Message details**: Final message content with character count, SMS segment count and concatenation status, personalization preview for 2-3 sample recipients showing variable resolution and fallback defaults, and opt-out mechanism placement confirmation
- **Cost report**: Per-message cost by destination country, per-segment cost for concatenated SMS, total send cost, and comparison to the campaign's messaging budget if a campaign name was linked
- **Delivery report**: Real-time delivery status — delivered count and percentage, pending/queued count, failed count with categorized failure reasons (invalid number, carrier rejection, opt-out processed, network error, rate limit), and read receipts for WhatsApp
- **Brand voice score**: Message alignment with brand tone guidelines and SMS best practices, with notes on conciseness, clarity, and any adjustments recommended for future mobile messaging
- **Execution log entry**: Timestamped record with all send metadata for compliance audit trail, campaign performance tracking, and cost accounting

## Agents Used

- **execution-coordinator** — Multi-jurisdiction consent verification (TCPA, GDPR, CASL) with per-recipient compliance filtering, quiet hours enforcement with timezone resolution from phone number and audience profiles, opt-out mechanism validation per channel requirements, approval workflow with HIGH risk classification and cost-aware summary, send execution via Twilio or Brevo MCP with batch processing and rate limiting, real-time delivery status tracking with failure categorization and threshold alerting, cost calculation per message and segment, and execution logging with full compliance audit trail for regulatory documentation
