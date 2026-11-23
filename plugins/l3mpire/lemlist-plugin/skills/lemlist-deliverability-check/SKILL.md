---
name: "lemlist-deliverability-check"
description: "Audit the email deliverability of the user's lemlist team (DNS of sending domains, warm-up reputation, sending volume, bounces, campaign settings, content) with lemlist's own audit engine, then explain the verdict and the fixes in order. Use when the user says 'my emails go to spam', 'my open or reply rate dropped', 'is my domain burned', 'check my DNS', or 'is my sending setup healthy'. Read-only. Requires the lemlist MCP server."
---

# Check lemlist deliverability

Run the same deliverability audit lemlist's support team uses, and turn it into a clear answer: is the setup healthy, what is wrong, what to fix first.

## When to trigger

Spam complaints, a drop in open or reply rate, rising bounces, a domain the user thinks is burned, a new setup to check before a launch, or a direct question about DNS, warm-up or sending limits.

## Requires the lemlist MCP

Call `get_team_info` first. If the tool is missing or fails, stop and follow "Connect lemlist" at the end.

## Process

1. **Load the guide.** Call `load_skill` with `skillName: "deliverability-audit"` and follow it; it defines how to present the report.
2. **Ask what triggered the check** (drop in replies, bounces, spam, burned domain, routine check). The answer decides which part of the report you lead with, never what runs.
3. **Run the audit.** Call `run_deliverability_audit` (no arguments, current team, read-only). It returns a header, a summary with a severity (healthy, minor, critical), sections (technical, cold sending, campaign settings, content, warm-up) with findings per sending domain, and a verdict with causes, ordered actions and an optional recovery plan.
4. **Present it as the engine computed it.** Do not recompute thresholds, do not rank the causes, and show each "unknown" as unknown with its reason.
5. **Answer follow-ups with the narrow tools.** DNS records of one domain: `check_domain_health` with `domain` (score, per-check status and the DNS records to fix). Warm-up of given mailboxes: `get_statistics` with `type: "lemwarm"` and the `usm_...` ids. Owned domains: `list_domains`.
6. **Inbox placement test only on request.** `run_inbox_placement_test` sends a real email: explain that, and run it only after the user says yes.

## Output format

```
DELIVERABILITY - [team], [date]
Severity: [healthy / minor / critical] because [criteria]

PER DOMAIN
[domain | DNS | warm-up spam (14 days) | cold bounce rate]

WHAT IS WRONG
- [cause] - evidence: [number or finding]

FIX IN THIS ORDER
1. [action]
2. ...

NOT MEASURED
- [unknown] - why
```

## Rules

- This skill changes nothing: no DNS edit, no mailbox or campaign change. Fixing DNS (`configure_domain_dns`) or buying domains are separate actions the user must ask for.
- Never call a domain healthy or burned without the audit or `check_domain_health` saying so.

## Connect lemlist

1. Create a lemlist account if needed (a free trial works): https://app.lemlist.com
2. Add the remote MCP server `https://app.lemlist.com/mcp` to your client. In Claude Code: `claude mcp add --transport http lemlist https://app.lemlist.com/mcp`. On first use a lemlist sign-in page opens (OAuth); pick your team and allow access.
3. Per-client steps and API key setup: https://help.lemlist.com/en/articles/13728466-set-up-the-lemlist-mcp-server-in-your-llm-client-oauth-or-api-key
4. Start a new conversation and run the skill again.
