---
name: send-email-campaign
description: "Send email campaigns. Use when: deploying via SendGrid, Klaviyo, Customer.io, Brevo, or Mailgun with A/B testing."
disable-model-invocation: false
argument-hint: "[campaign-name]"
---

# /digital-marketing-pro:send-email-campaign

## Purpose

Create and send a targeted email campaign through the brand's connected email platform with personalization, A/B subject lines, compliance checks, and deliverability monitoring. Handles the full lifecycle from content validation through send execution to post-send monitoring, with tiered risk controls based on recipient list size. Ensures every send passes spam, compliance, and brand voice gates before reaching any inbox.

## Execution gate (MANDATORY — cannot be skipped)

1. Present the full preview — recipients / spend / changes / compliance — as an **Execution Summary** before touching any live system.
2. The user must type `yes` (or an equivalent explicit approval). ANY other input — ambiguous, implied, partial, or absent approval — cancels the run.
3. Never proceed on ambiguous input. Never auto-retry a failed execution; a failure needs human review before any re-run.
4. Record the approval with `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action create-approval --data '{"risk_level":"<tier>","summary":"..."}'` **before** executing, then `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action mark-executed --id {approval_id}` after the platform confirms success.

## Input Required

The user must provide (or will be prompted for):

- **Email content**: Subject line, preview text (40-90 chars), body copy with HTML structure, and primary CTA — or a draft to refine
- **Target list or segment**: The recipient list name, segment ID, or audience criteria for the send — with confirmation of list hygiene status (last cleaned date)
- **Email platform**: Which email service to use — SendGrid, Klaviyo, Customer.io, Brevo, or Mailgun — must have the corresponding MCP server connected
- **Personalization fields**: Dynamic fields to personalize — first name, company, product interest, last purchase, location, or custom merge tags with fallback defaults for missing data
- **A/B variants**: Optional — 2-3 subject line or content variants for split testing with desired test percentage (10-50%), test duration, and winning metric (open rate or click rate)
- **Send time**: Immediate send, scheduled date and time with timezone, or "optimal" to use send-time optimization based on historical engagement data per segment
- **Reply-to address**: Reply-to email address if different from the default sender configured in the platform
- **Sender name and from address**: Display name and from address — must match authenticated sending domain (SPF, DKIM, DMARC)
- **Unsubscribe handling**: Confirm unsubscribe link placement, one-click unsubscribe header compliance (required for bulk senders per Gmail/Yahoo 2024 rules), and preference center link
- **UTM tracking**: Google Analytics UTM parameters for all links in the email body (source, medium, campaign), or auto-generate based on brand naming conventions
- **Suppression list**: Any additional email addresses or domains to exclude from this send beyond the platform's global suppression list
- **Email template**: Optional — platform template ID to use, or build from scratch with the provided content and brand styling
- **Preheader text strategy**: Whether the preview text should complement, tease, or extend the subject line — affects how the email appears in inbox list view
- **Fallback content**: Plain-text version of the email for recipients whose clients do not render HTML, or auto-generate from the HTML body

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Verify email platform connection**: Check which email MCP server is connected and confirm it matches the user's target platform. Verify the sending domain is authenticated (SPF, DKIM, DMARC records). If not connected or not authenticated, instruct the user on setup steps.
3. **Score email subject lines**: Run `email-subject-tester.py` on all subject line variants to evaluate length (optimal 30-50 chars), power words, personalization token effectiveness, emoji usage, and predicted open rate. Recommend improvements if any variant scores below threshold.
4. **Check spam score**: Run `spam-score-checker.py` to analyze subject lines and body content for spam trigger words, excessive capitalization, exclamation marks, link-to-text ratio, image-to-text ratio, and authentication alignment. Flag any deliverability risks with specific remediation steps.
5. **Optimize send time**: If the user selected "optimal" timing, run `python "${CLAUDE_PLUGIN_ROOT}/scripts/send-time-optimizer.py" --industry {industry} --audience-type {b2b|b2c|mixed}` to suggest a send window by day of week and hour. NOTE: this returns a **static industry heuristic (2024-era best-times table)** — it does NOT read your historical engagement data. Treat the output as a starting hypothesis and validate it against your own segment's open/click history before relying on it. Factor in the timezone distribution of the recipient list.
6. **Build platform-specific payload**: Structure the email payload per the target platform's API requirements — consult `skills/context-engine/platform-publishing-specs.md` for field mappings, template rendering, merge tag syntax (e.g., `{{first_name}}` vs `{first_name}`), A/B test configuration parameters, and scheduling API format.
7. **Verify list size and consent compliance**: Confirm recipient count and segment definition. Check that the list has proper opt-in consent flags for the applicable jurisdiction. Verify unsubscribe mechanism is functional, one-click unsubscribe header is present, physical mailing address is included, and compliance with CAN-SPAM (US), GDPR (EU), CASL (Canada), and any other regulations for the brand's target markets.
8. **Score brand voice**: Run `brand-voice-scorer.py` on the email body content to verify alignment with brand tone and messaging guidelines. Flag any copy that deviates from brand standards.
9. **Create approval record**: Create the record via `approval-manager.py --action create-approval` with the tiered risk level inside the `--data` JSON — `{"risk_level":"medium",...}` for fewer than 1,000 recipients, `"high"` for 1,000-10,000, `"critical"` for more than 10,000. There is no `--risk-level` flag; see the Execution gate above for the exact command. Generate a send summary with all campaign details, scores, and compliance status.
10. **Present campaign summary**: Display the complete summary for user review — subject lines with scores, preview text, recipient count and segment name, send time, personalization preview with sample recipient data, spam score, brand voice score, and compliance checklist. Wait for explicit confirmation.
11. **Send test email**: On initial approval, send a test email to the user's address (and any additional test addresses) via the MCP server. Ask the user to confirm the test renders correctly across desktop and mobile, personalization tokens resolve, links work, and images load.
12. **Execute full send via MCP**: After test confirmation, trigger the campaign send through the connected email platform MCP. Handle A/B test split configuration, scheduling, and any platform-specific send options (track opens, track clicks, Google Analytics UTM tagging).
13. **Monitor deliverability**: After send, poll the platform API at 15-minute intervals for the first hour to track delivery metrics — bounce rate, delivery rate, soft bounces, hard bounces, and spam complaints. Alert the user if bounce rate exceeds 3% or spam complaint rate exceeds 0.1%.
14. **Capture early engagement signals**: After 1 hour and again at 4 hours, pull open rate and click rate data. Compare against the brand's historical averages for the same segment. If A/B testing, report which variant is leading.
15. **Log execution**: Run `execution-tracker.py` to log the send event with timestamp, platform, campaign ID, list size, subject lines, A/B configuration, send time, initial delivery metrics, and compliance verification status. Save an insight about subject line performance for future email strategy optimization.

## Output

A structured send confirmation containing:

- **Send confirmation**: Campaign ID, platform, send status (sent, scheduled, or A/B testing), and timestamp with timezone
- **List details**: Recipient count, segment name, consent verification status, and list hygiene notes
- **Subject line scores**: Score breakdown for each variant — length, power words, personalization effectiveness, predicted open rate, and spam risk indicators
- **Spam score report**: Overall deliverability risk rating (low/medium/high) with specific flags for any triggered spam indicators and remediation steps
- **Brand voice score**: Email content alignment score with notes on tone consistency and any copy adjustments recommended
- **Send time**: Actual send time with rationale — user-specified, scheduled with timezone, or optimized with supporting engagement data
- **A/B test configuration**: If applicable — variant descriptions, split percentage, test duration, winning metric, and auto-send winner settings
- **Deliverability report**: Initial delivery rate, bounce rate (hard and soft), spam complaint rate, and comparison against industry benchmarks for the brand's sector
- **Compliance checklist**: Pass/fail for CAN-SPAM, GDPR, CASL, unsubscribe mechanism, one-click unsubscribe header, physical address, authentication headers (SPF, DKIM, DMARC), and sender identity
- **Early engagement signals**: 1-hour and 4-hour open rate and click rate snapshots with comparison to brand historical averages and industry benchmarks
- **Personalization preview**: Sample rendering showing how the email appears for 2-3 representative recipients with different merge tag values and fallback defaults
- **UTM tracking summary**: Complete UTM parameters applied to all email links for attribution tracking in the brand's analytics platform
- **Execution log entry**: Timestamped record of the send action with all campaign metadata for audit trail and performance benchmarking

## Agents Used

- **email-specialist** — Subject line optimization, content personalization strategy, deliverability analysis, spam scoring, send time optimization, compliance verification, brand voice scoring, A/B test design with statistical significance thresholds, and preheader text strategy
- **execution-coordinator** — Approval workflow with tiered risk controls based on list size, test send coordination across desktop and mobile, platform API execution, deliverability monitoring with real-time alerting, early engagement signal capture, and execution logging with insight archival
