---
name: "lemlist-campaign-report"
description: "Read the real stats of the user's lemlist campaigns (leads reached, messages sent, opens, clicks, replies, LinkedIn invitations accepted, bounces), per campaign, per channel and per step, over any period, and turn them into a short diagnosis with the next actions. Use when the user asks 'how are my campaigns doing', 'which campaign works best', 'compare last month', 'which step gets replies', or 'why is my reply rate low'. Requires the lemlist MCP server."
---

# Report on lemlist campaigns

Pull the numbers the lemlist Campaign Reports screen shows, compare them, and say what to change. Numbers come from the tools, never from memory or guesses.

## When to trigger

The user asks about campaign performance, wants campaigns compared, asks for a weekly or monthly report, or wants to know which step or channel works.

## Requires the lemlist MCP

Call `get_team_info` first. If the tool is missing or fails, stop and follow "Connect lemlist" at the end.

## Process

1. **Find the campaigns.** Call `get_campaigns` (`sortOrder: "desc"`, `limit`, `offset`, and `search`, `status` or `labels` to narrow). If the user names a campaign, resolve its `cam_...` id here.
2. **Pick the period.** Default to lifetime. For a period, pass `startDate` and `endDate` as `YYYY-MM-DD` (read in the user's lemlist timezone, or the `timezone` you pass) to `get_campaigns_stats`.
3. **Get the stats.** Call `get_campaigns_stats` with up to 100 `campaignIds`. It returns the lead funnel (`leadMetrics`), message metrics with a per-channel breakdown (`messageMetrics.perChannel`), and one row per step (`steps[]`, one row per A/B variant). Filter with `channels` when the user asks about one channel. For lifetime totals with sender info on many campaigns, `get_campaigns_reports` is the alternative.
4. **Read the steps.** To explain a weak step, read its copy with `get_campaign_sequences`.
5. **Diagnose.** Pick the 2 or 3 facts that matter: the best and worst campaign on reply rate, the step where replies happen, the channel that carries the results, a bounce rate high enough to hurt the domain. Tie each to an action.

## Reading the numbers right

- `messageMetrics.sent` and `delivered` match the UI tiles "Messages sent" and "Delivered"; `leadMetrics.reached` matches "Leads reached".
- For LinkedIn, `delivered` repeats `sent`: never report a LinkedIn delivery rate.
- `notDelivered` counts failed attempts and is separate from `sent`: a failure rate is `notDelivered / (sent + notDelivered)`.
- These figures match the Campaign Reports tiles, not the Reports Dashboard, which counts differently. Say so if the user compares with the dashboard.
- Compare rates, not raw counts, between campaigns of different sizes, and say when a campaign has too few leads to conclude.

## Output format

```
CAMPAIGN REPORT - [period]

AT A GLANCE
[campaign | leads reached | sent | reply rate | main channel]

WHAT WORKS
- [fact with its number]

WHAT DOES NOT
- [fact with its number]

NEXT ACTIONS
1. [action] - because [number]
2. ...
```

## Rules

- Never make up a number. A metric the tools did not return is "not available", not zero.
- This skill only reads. To change a sequence, use the `lemlist-launch-campaign` skill; for spam or bounce problems, use `lemlist-deliverability-check`.

## Connect lemlist

1. Create a lemlist account if needed (a free trial works): https://app.lemlist.com
2. Add the remote MCP server `https://app.lemlist.com/mcp` to your client. In Claude Code: `claude mcp add --transport http lemlist https://app.lemlist.com/mcp`. On first use a lemlist sign-in page opens (OAuth); pick your team and allow access.
3. Per-client steps and API key setup: https://help.lemlist.com/en/articles/13728466-set-up-the-lemlist-mcp-server-in-your-llm-client-oauth-or-api-key
4. Start a new conversation and run the skill again.
