# Campaigns

Use `sendsets campaign --help` for the installed version. Build an audience, sequence, and sender assignment based on the selected idea. Show the rendered first email and its recipient before a send.

Use `sendsets campaign validate CAMPAIGN_ID --json` and `sendsets campaign preflight CAMPAIGN_ID --json` where available. Resolve problems instead of bypassing them. `sendsets campaign test-email` sends a real message. `sendsets campaign test CAMPAIGN_ID --prospect EMAIL --wait` runs one prospect through the actual workflow and also sends real mail. Ask for approval for that specific test. A successful test does not authorize `sendsets campaign start CAMPAIGN_ID`.

Never start a live campaign unless the user explicitly requested sending. The credential's agent policy may still return `awaiting_approval`; share that approval URL. Use an idempotency key for retried writes. Keep stop-on-reply and sender limits aligned with the user's intent and mailbox health.

## Building from a run file

`sendsets campaign import campaign.yaml --dry-run --wait --json` creates the campaign as a draft and runs preflight; nothing sends. JSON is valid YAML, so generating the file as JSON is fine.

- Leads come from `csv:` or an inline `leads:` list. In a CSV, `email`, `first_name`, `last_name`, `company` and `phone` map to contact fields and any other named column becomes a custom field under its header. Inline leads carry `custom_fields`.
- Re-adding a contact that already exists merges its custom fields; it never blanks a field.
- `senders: {mode: explicit, mailbox_ids: [...]}` pins the mailboxes. Get ids from `sendsets mailbox list --json`.
- Variants on one step split contacts at send time, so you cannot know in advance who gets which. If one variant needs per-lead data, give every lead that data or split the variants into two campaigns.

## Merge fields

- Contact fields are `{{.FirstName}}`, `{{.LastName}}`, `{{.Company}}`, `{{.Email}}`, `{{.Phone}}`; custom fields are `{{.key}}` with the exact key. Give a fallback with `{{.FirstName | default "there"}}`.
- Spintax uses single braces, `{Hi|Hey}`. Double braces are template syntax, so `{{Hi|Hey}}` breaks the email.
- The sending mailbox's signature and the opt-out footer are appended to every email. Do not write a sign-off or an opt-out line into the body, or they appear twice.
- `validate` reports `campaign_variable_missing` when no contact has a field and `campaign_variable_incomplete` when some leads leave it blank, with the count and a sample. Fix both before starting; a blank field sends as a gap in the email.
- Render a template for a real lead through the send engine: `sendsets api -X POST /campaign-template-preview --input @preview.json` with `subject`, `body_plain`, `contact_id`, `campaign_id` and `account_id` (the mailbox, for its signature). AI variable blocks are not resolved in a preview.

## Volume

`daily_limit` is per mailbox, not per campaign: a mailbox stops taking the campaign's sends once it has sent that many campaign emails today, counting every campaign. The day's ceiling is roughly `min(daily_limit, mailbox campaign_limit) × senders`. Two campaigns sharing mailboxes should each use the mailbox's cap; setting each to half makes the second one find its mailboxes already full.

## Starting

`sendsets campaign start CAMPAIGN_ID --yes`. A 403 with code `plan_required` is the workspace's plan, not the API key: tell the user to choose a plan under Settings > Billing rather than signing in again. Start is a real send; in a coding agent it may need the user's own approval, in which case give them the exact command to run.
