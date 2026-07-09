---
name: pipeline-update
description: "Update CRM pipeline. Use when: changing deal stages, values, notes, tracking velocity, or managing deal progression."
disable-model-invocation: true
argument-hint: "[deal-name or stage]"
---

# /digital-marketing-pro:pipeline-update

## Purpose

Update deal and opportunity records in the CRM pipeline — move deals between stages, update values, add notes, and track pipeline velocity. Provides a clear before-and-after view of every change and calculates the downstream impact on pipeline metrics, giving both marketing and sales teams visibility into deal progression, forecast accuracy, and revenue pacing against targets. Designed for both individual deal updates and batch stage transitions, with built-in validation to prevent invalid stage skips and mandatory field gaps.

Use this command for pipeline changes that affect deal stage, value, or forecast. For creating new deals from leads, use `/digital-marketing-pro:lead-import` to bring leads into the CRM first, then use this command to manage their pipeline progression.
For bulk pipeline reporting without individual updates, use `/digital-marketing-pro:executive-dashboard` instead.

## Input Required

The user must provide (or will be prompted for):

- **Deal identifier**: How to locate the deal — deal name, associated contact email, company name, or CRM record ID. If ambiguous, the system will present matching candidates for selection.
- **Updates to apply**: One or more changes — stage change (e.g., "Proposal Sent" to "Negotiation"), deal value update (increase, decrease, or split), close date adjustment, probability override, loss reason (if moving to closed-lost), or custom field modification
- **Notes or context**: Reason for the update, meeting summary, objection details, competitor intelligence, next steps, or any qualitative context to attach to the deal record as a timestamped note
- **Pipeline name (if multiple)**: Which pipeline the deal belongs to — relevant for businesses with separate pipelines for new business, renewals, upsells, partnerships, or different product lines
- **CRM platform**: Salesforce, HubSpot, Zoho, or Pipedrive — and the specific pipeline/opportunity object if the platform supports multiple pipeline types
- **Activity association (optional)**: Whether to log the update as a specific activity type — call, meeting, email, task, demo, or custom activity — with timestamp, duration, and participants
- **Follow-up actions (optional)**: Tasks to create as a result of this update — schedule next call, send proposal, loop in technical resource, create SOW, or set reminder for follow-up date with assignee and due date
- **Notification preferences (optional)**: Whether to notify the deal owner, account executive, or manager about this pipeline change — and via which channel (CRM notification, email, Slack)
- **Batch update scope (optional)**: If updating multiple deals at once — a list of deal identifiers with the same update to apply, or a filter criteria to select deals (e.g., "all deals in Discovery stage with close date before March 1")
- **Win/loss analysis fields (optional)**: If closing a deal — won/lost reason, competitor involved, deciding factor, lessons learned, and whether the contact should enter a win-back or referral sequence
- **Revenue recognition details (optional)**: For closed-won deals — contract terms (monthly/annual), start date, renewal date, one-time vs. recurring revenue split, and any discount or promotional pricing applied
- **Related deals (optional)**: Whether this update affects related deals — upsell opportunities, cross-sell deals, or renewal pipeline that should be created or updated based on this deal's stage change

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Apply brand voice, compliance rules for target markets (`skills/context-engine/compliance-rules.md`), and industry context. **Also check for guidelines** at `~/.claude-marketing/brands/{slug}/guidelines/_manifest.json` — if present, load restrictions and relevant category files. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Check connected CRM and pipeline configuration**: Verify CRM connection status, retrieve available pipelines and their stage definitions (including required fields per stage, stage ordering, and probability defaults), and confirm the user has write access to the target pipeline. If multiple pipelines exist, present options for selection.
3. **Look up existing deal record**: Search the CRM for the deal using the provided identifier — by name, email, company, or ID. If multiple matches are found, present the candidates with key details (deal name, stage, value, owner, last activity date, days in current stage) for the user to select the correct record.
4. **Present current deal state**: Display the full current record — deal name, pipeline, current stage, value, probability, close date, owner, associated contacts and company, recent activity timeline (last 5 activities), custom field values, and days in current stage. This serves as the "before" snapshot for the change audit.
5. **Validate proposed updates against pipeline rules**: Check that the stage transition is valid (no skipping required stages unless the pipeline allows it), the deal value is within acceptable range for the target stage, the close date is realistic given stage position, and any mandatory fields for the target stage are populated. Flag violations with specific corrections needed.
6. **Calculate pipeline impact preview**: Before executing, compute how this change will affect pipeline metrics — weighted pipeline value change, forecast impact for the current period, stage conversion rate adjustment, and whether this deal's movement creates any pipeline coverage gaps or concentrations.
7. **Prepare update payload**: Build the CRM-ready update payload with all changes — stage, value, close date, probability, custom fields, notes, activity log entry, follow-up tasks, and any associated record updates (e.g., updating the parent account's pipeline value rollup).
8. **Create approval gate**: Assess risk as medium for all pipeline updates (deals directly affect revenue forecasting). Present the update summary as a before-and-after comparison — current state vs. proposed state — with pipeline velocity impact, forecast changes, and any validation warnings.
9. **On approval, update via CRM MCP**: Push the update payload to the CRM through the platform MCP. Create the activity log entry, attach notes, generate follow-up tasks with correct assignees and due dates, and send notifications if configured. Confirm the update succeeded by reading back the updated record from the CRM.
10. **Calculate pipeline velocity impact**: Compute how this update affects pipeline velocity metrics — stage conversion rate, average deal cycle time for this stage, weighted pipeline value, forecast accuracy vs. target, and comparison to historical averages for similar deal sizes and stages.
11. **Process win/loss data (if closing)**: If the deal is being closed won or lost, record the win/loss reason, competitor data, and deciding factors. For closed-lost deals, determine if the contact should enter a win-back nurture sequence. For closed-won deals, trigger any post-sale workflows (customer onboarding, case study candidate flagging, referral request scheduling).
12. **Generate pipeline health assessment**: After the update, assess overall pipeline health — pipeline coverage ratio vs. quota, average deal age by stage, deals at risk of slipping (past expected close date or stalled beyond historical average), and stage-by-stage bottleneck identification.
13. **Log the update**: Record the complete update — timestamp, deal ID, before state, after state, user who initiated, velocity impact, follow-up tasks created, win/loss data, and notifications sent — to `~/.claude-marketing/brands/{slug}/logs/pipeline-update-log.json`.

## Output

A structured pipeline update report containing:

- **Updated deal record**: The complete deal record after all changes have been applied — stage, value, probability, close date, owner, custom fields, associated contacts, and next scheduled activity
- **Before-and-after comparison**: Side-by-side view of every changed field showing previous value, new value, change delta (for numeric fields), and the reason or context provided for the change
- **Pipeline velocity metrics**: Updated stage conversion rate, average days in current stage vs. historical average, weighted pipeline value change, and projected close date confidence based on historical stage duration data for deals of similar size
- **Activity log entry**: The recorded activity — type (call, meeting, email, note), timestamp, duration, participants, summary, and next steps — as it appears in the CRM's activity timeline
- **Follow-up tasks created**: Any tasks generated from this update — description, due date, assignee, priority, associated deal reference, and reminder settings
- **Pipeline snapshot**: Current state of the full pipeline after this update — total deals by stage, total weighted value, stage-by-stage breakdown with conversion rates, deals at risk (overdue close dates or stalled in stage beyond average), and pipeline coverage ratio vs. quota
- **Forecast impact**: How this single deal update affects the overall pipeline forecast — change in weighted pipeline value, movement in pipeline coverage ratio, confidence level adjustment, and impact on current-period revenue projection
- **Win/loss analysis (if closing)**: Recorded win/loss reason, competitor involved, deciding factors, and triggered post-close actions (customer onboarding, win-back sequence, case study candidacy, or referral request)
- **Pipeline health assessment**: Overall pipeline health after this update — coverage ratio vs. quota, average deal age by stage, bottleneck stages, deals at risk of slipping, and comparison to the previous pipeline snapshot
- **Stalled deal alerts**: Deals identified as stalled during the pipeline health check — deal name, stage, days in stage, expected stage duration, and recommended action (re-engage, escalate, or close-lost)
- **Historical stage duration comparison**: How long this deal spent in its previous stage compared to average deals of similar size — faster or slower than expected, with implications for close probability
- **Marketing attribution on deal**: Marketing touchpoints that contributed to this deal — source campaign, content interactions, email engagements, and ad clicks associated with the deal's contacts, providing marketing-to-revenue visibility
- **Notification delivery confirmation**: Notifications sent to deal owner, manager, or team — channel used, delivery status, and content summary of the notification
- **Execution log**: Timestamped record of the update — API calls made, response status, notifications delivered, tasks created, processing duration, and CRM confirmation

## Agents Used

- **crm-manager** — Deal lookup, pipeline stage validation, update preparation, CRM schema resolution, velocity calculation, activity logging, forecast impact analysis, and pipeline analytics
- **marketing-strategist** — Marketing attribution on deal, campaign-to-revenue connection analysis, win/loss pattern identification for strategic marketing optimization, and pipeline health assessment interpretation
