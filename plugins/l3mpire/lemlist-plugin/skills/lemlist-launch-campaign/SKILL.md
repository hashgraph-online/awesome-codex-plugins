---
name: "lemlist-launch-campaign"
description: "Build and launch a lemlist outreach campaign from a goal: agree on the target and the angle, write a short email and LinkedIn sequence, create it in lemlist, add the leads, check that the campaign can send, and launch it only after the user confirms. Use when the user says 'create a campaign', 'write me a cold email sequence and put it in lemlist', 'launch my campaign', or 'why can't my campaign start'. Requires the lemlist MCP server."
---

# Build and launch a lemlist campaign

Go from "I want to reach these people about this" to a campaign that is ready to send, without the user opening the lemlist editor, and without sending anything they did not approve.

## When to trigger

The user wants a new outreach campaign, a sequence written and saved in lemlist, leads added to a campaign, or a draft campaign launched.

## Requires the lemlist MCP

Call `get_team_info` first. If the tool is missing or fails, stop and follow "Connect lemlist" at the end.

## Process

1. **Load the server playbooks.** Call `load_skill` with `skillName: "campaign-builder"`, then with `skillName: "copywriting"` before writing any message. They carry lemlist's sequence patterns, channel limits and copy rules; follow them over this file.
2. **Agree on the brief in one exchange:** who the campaign targets, the problem the user solves for them, the call to action (meeting, reply, demo), the channels (email only, or email plus LinkedIn), and the language. Ask only for what is missing.
3. **Check who can send.** Call `get_senders` (team members and their connected mailbox, LinkedIn, WhatsApp, phone). If no mailbox is connected, or the LinkedIn steps have no LinkedIn account behind them, say so now: the campaign could not send. Load `load_skill("senders")` to read any diagnostic.
4. **Propose the sequence in plain text first**: each step with its channel, delay in days, subject and body. Keep it short (3 to 5 touches). Use lemlist variables such as `{{firstName}}` and `{{companyName}}`. Wait for the user's approval or edits.
5. **Create it.** Call `create_campaign_with_sequence` with `name`, `subject`, `body` (the first email) and `timezone`. The response returns `campaign.id` and `sequence.id`; if it also names a teammate in `assignedSenderUserId`, tell the user who. Then add each other step with `add_sequence_step` (`campaignId`, `sequenceId`, `type`, `delay`, `message`, and `userConfirmed: true` once the user approved the sequence in step 4). After a `linkedinInvite`, any LinkedIn message must sit in the accepted branch of a `conditional` step with `conditionKey: "linkedinInviteAccepted"`.
6. **Add the leads.** From a list the user gives, or from the `lemlist-find-leads` skill: `add_leads_to_campaign` (max 100 per call). Report the outcome counts.
7. **Check before launch.** Call `validate_campaign_readiness` with the `campaignId`, after the writes above returned. On `has_errors`, list each error in plain words and fix what the tools can fix; for a sender error, read `get_campaign_senders` instead of trusting the generic message.
8. **Launch only on an explicit yes.** Call `launch_campaign` without `userConfirmed`: it returns `awaiting_confirmation`. Ask the user to confirm the launch, and separately whether future leads should send automatically (`autoReview`, off unless they ask). Then call it again with `userConfirmed: true`. Report `reviewedCount`, `scannedCount` and every `blockedReasons` entry.

## Output format

```
CAMPAIGN [name] (cam_...)
Target: [who]
Senders: [who sends, from which accounts]

SEQUENCE
1. Day 0, email: [subject]
2. Day 2, LinkedIn invite
...

LEADS: [added] added, [skipped] skipped ([reasons])
READINESS: [ready / errors and what was done]
STATUS: [draft, waiting for your go / launched: N leads sent, M blocked because ...]
```

## Rules

- Launching sends real messages to real people. Never set `userConfirmed: true` on `launch_campaign` without a yes from the user in this conversation.
- Never invent ids: campaign, sequence, user and list ids come from tool results.
- To resume a paused campaign, use `set_campaign_state` with `action: "start"`, not `launch_campaign`.
- Do not claim a campaign is live until `launch_campaign` returned with leads reviewed.

## Connect lemlist

1. Create a lemlist account if needed (a free trial works): https://app.lemlist.com
2. Add the remote MCP server `https://app.lemlist.com/mcp` to your client. In Claude Code: `claude mcp add --transport http lemlist https://app.lemlist.com/mcp`. On first use a lemlist sign-in page opens (OAuth); pick your team and allow access.
3. Per-client steps and API key setup: https://help.lemlist.com/en/articles/13728466-set-up-the-lemlist-mcp-server-in-your-llm-client-oauth-or-api-key
4. Start a new conversation and run the skill again.
