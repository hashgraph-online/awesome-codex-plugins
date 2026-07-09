---
name: send-notification
description: "Send team notifications. Use when: pushing campaign updates, alerts, or approval requests via Slack or Intercom."
disable-model-invocation: false
argument-hint: "[channel or recipient]"
---

# /digital-marketing-pro:send-notification

## Purpose

Send internal team notifications via Slack or Intercom for campaign status updates, performance alerts, approval requests, or general team communication. This command is strictly for internal team messaging — not customer-facing outreach. It provides structured, urgency-aware notifications that keep marketing teams, stakeholders, and collaborators informed about campaign progress, metric thresholds, and pending approvals without requiring them to check dashboards or wait for scheduled reports. Supports tiered urgency with appropriate formatting and mention behavior to balance keeping teams informed without causing alert fatigue.

## Execution gate (MANDATORY — cannot be skipped)

1. Present the full preview — recipients / spend / changes / compliance — as an **Execution Summary** before touching any live system.
2. The user must type `yes` (or an equivalent explicit approval). ANY other input — ambiguous, implied, partial, or absent approval — cancels the run.
3. Never proceed on ambiguous input. Never auto-retry a failed execution; a failure needs human review before any re-run.
4. Record the approval with `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action create-approval --data '{"risk_level":"<tier>","summary":"..."}'` **before** executing, then `python "${CLAUDE_PLUGIN_ROOT}/scripts/approval-manager.py" --brand {slug} --action mark-executed --id {approval_id}` after the platform confirms success.

## Input Required

The user must provide (or will be prompted for):

- **Notification content**: The message to send — can be a brief status update ("Q1 campaign launched successfully"), a detailed performance alert with metrics ("Bounce rate spiked to 8.2%, up from 2.1% baseline — investigate immediately"), an approval request with action items ("Budget increase needs sign-off by EOD"), or a campaign milestone announcement. Plain text, markdown-formatted sections, or structured data that will be auto-formatted
- **Channel**: `slack` or `intercom` — must have the corresponding MCP server connected. For Slack, specify the target channel name (e.g., #marketing-updates, #campaign-alerts, #leadership-reports) or a direct message recipient username. For Intercom, specify the conversation ID or team inbox name
- **Urgency level**: `info` (standard notification — clean formatting, no special indicators or mentions), `warning` (highlighted with caution indicator — metrics approaching thresholds, deadlines within 24 hours, or issues requiring attention soon), or `critical` (urgent with @here or @channel mention in Slack, priority flag in Intercom — immediate action required for budget overspend, campaign failure, compliance issue, or service outage)
- **Related context (optional)**: Campaign ID, approval ID, report reference, dashboard link, or metric snapshot to attach to the notification — recipients see the relevant context inline without needing to search for it or open another tool
- **Mentions (optional)**: Specific team members to @mention — by Slack username or Intercom team member name. For critical urgency, @here is auto-included unless explicitly overridden by the user. Multiple mentions supported for cross-functional notifications
- **Follow-up action (optional)**: A specific action the recipient should take — "Approve the Q1 budget by 5pm EST", "Review the campaign report and flag issues", "Investigate the bounce rate spike in the newsletter segment" — rendered as a clear call-to-action block in the notification
- **Thread or conversation (optional)**: For Slack, a thread timestamp to reply within an existing thread rather than posting a new top-level message. For Intercom, a conversation ID to continue an existing conversation. Keeps related updates grouped and reduces channel noise
- **Schedule (optional)**: Send at a specific time instead of immediately — e.g., "9am EST Monday" for start-of-week status updates or "after business hours" for non-urgent recaps. If omitted, sends immediately
- **Attachments (optional)**: File paths or URLs to attach — performance charts, campaign screenshots, report PDFs, or dashboard snapshots. Uploaded via the platform MCP as message attachments

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. Also check for guidelines at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Format notification by urgency**: Structure the notification content based on urgency level. For `info`: clean standard message with brand name header and timestamp. For `warning`: highlighted block with caution indicator, metric context with threshold comparison, and deadline if applicable. For `critical`: urgent header with action-required flag, @here/@channel mention (Slack) or highest priority flag (Intercom), red indicator, and response deadline. All levels include the brand name, notification type label, and formatted timestamp.
3. **Attach related context**: If a campaign ID, approval ID, metric snapshot, or dashboard link was provided, resolve it to a human-readable summary — campaign name with current status and key metrics, approval details with pending actions and deadline, or metric values with trend indicators and threshold comparisons. Embed this context directly in the notification body so recipients have full situational awareness without leaving the messaging platform.
4. **Format follow-up action**: If a follow-up action was specified, render it as a distinct call-to-action block — visually separated from the notification body with clear action text, owner (mentioned team member or channel), and deadline if specified. In Slack, use a section block with button-style formatting. In Intercom, use a note with action assignment.
5. **Verify messaging MCP connection**: Check which messaging platform MCP is connected — Slack or Intercom — and confirm it matches the user's target channel. Verify the bot has permission to post to the specified channel or conversation, can use @here/@channel mentions if critical urgency is selected, and can upload attachments if provided. If not connected or permissions are insufficient, guide the user to configure the integration with specific permission scopes needed.
6. **Check alert fatigue**: Query recent notification history for the target channel — count notifications sent in the past 24 hours, with breakdown by urgency level. If more than 5 critical notifications or 15 total notifications have been sent to the same channel in that window, warn the user about potential alert fatigue and suggest consolidating updates or adjusting urgency levels downward.
7. **Create approval gate**: Assess notification risk — `low` for info and warning urgency (standard team communication with no channel-wide disruption), `medium` for critical urgency with @here or @channel mentions (interrupts everyone in the channel). Present the notification preview showing formatted content as it will appear in the target platform, mentions, attachments, and urgency formatting for user confirmation.
8. **Send via MCP**: On approval, deliver the notification through the connected Slack or Intercom MCP. For Slack: post to the specified channel with Block Kit formatting (header blocks, section blocks with fields, context blocks for metadata, and action blocks for CTAs), thread reply if thread timestamp specified, and file uploads for attachments. For Intercom: create or reply to a conversation with priority setting matching urgency, internal note for team-only visibility, and attachment uploads.
9. **Log delivery**: Record the notification event with timestamp, platform, channel or conversation target, urgency level, content summary, mentions included, related context references, attachments sent, and delivery confirmation. Update the channel's notification frequency counter for alert fatigue tracking on subsequent sends.

## Output

A structured delivery confirmation containing:

- **Send confirmation**: Notification ID or message timestamp, platform (Slack or Intercom), target channel or conversation, delivery status (sent, scheduled, failed, or queued), and permalink to the posted message where available
- **Formatted preview**: The notification as it appeared to recipients — showing urgency formatting, header and body sections, mentions highlighted, attached context rendered, call-to-action block, and any attachments listed
- **Urgency classification**: The urgency level applied with platform-specific formatting details — info (standard), warning (highlighted with caution indicator), or critical (urgent with @here/@channel or priority flag) — and channel-wide impact assessment
- **Context attached**: Summary of any campaign, approval, metric, or dashboard context embedded in the notification, with source reference IDs for traceability
- **Mentions delivered**: Confirmation of all @mentions and @here/@channel notifications triggered, with recipient count for channel-wide mentions
- **Delivery timestamp**: Exact time the notification was delivered (or scheduled delivery time) with timezone, for coordination tracking and response time measurement
- **Alert fatigue report**: Notification frequency for the target channel in the past 24 hours — total notifications sent, critical count, warning count, info count, and recommendation to consolidate or reduce urgency if volume is elevated
- **Execution log entry**: Timestamped record for audit trail with full notification metadata, delivery confirmation, alert fatigue metrics, and channel activity trend

## Agents Used

- **execution-coordinator** — Urgency-tiered notification formatting with platform-specific rendering (Slack Block Kit with header, section, context, and action blocks; Intercom priority flags and internal notes), related context resolution and inline embedding from campaign and approval data, follow-up action formatting as call-to-action blocks, approval workflow with risk assessment scaled to urgency level and channel-wide mention impact, alert fatigue monitoring with 24-hour rolling window tracking, MCP delivery execution for Slack and Intercom with thread support and attachment uploads, and execution logging with delivery confirmation and channel activity metrics
