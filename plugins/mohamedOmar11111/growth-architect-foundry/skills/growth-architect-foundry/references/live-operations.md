# Live Operations — Lazy Reference

Load this file ONLY when a `live` command is being executed or explained.

## Safety Model (non-negotiable)

### Read-only verbs (pull, optimize)
- Same as every other command — fail loud if creds missing, never modify anything.
- Pull data from Google Ads and/or Meta via the tenant's .env credentials.
- If no creds configured, output says "no campaigns found" — not a crash.

### Write verbs (pause, budget)
- **Require `--confirm` AND a human at a terminal.** Without `--confirm` the exact change is printed and nothing happens. With it, the user must type the campaign key at an interactive terminal; non-interactive runs (an AI agent's shell) exit 3 "refused". Agents preview and hand the user the command; they never run the write.
- The exact change is shown BEFORE execution — campaign name, current status/budget, proposed change.
- Budget changes capped at **20% per action** (rule 3: respect learning). Attempting a larger change is blocked, not clamped.
- Every write appends to `log.md` with the exact change made.

## Commands

| Verb | Read/Write | What it does |
|---|---|---|
| `live pull` | Read | Pull live campaign data from all configured platforms |
| `live optimize` | Read | Scale/hold/reduce/kill recommendations with numbers |
| `live pause` | Write | Pause a specific campaign (--confirm required) |
| `live budget` | Write | Adjust campaign budget (--confirm required, max 20% change) |

## Campaign ID Format

Campaigns are keyed as `platform:id` — e.g., `google:12345678` or `meta:23456789`. The `live pull` command outputs these keys; use them in `--campaign-id` for pause/budget.

## Platform Support

| Platform | Read | Write | Creds needed |
|---|---|---|---|
| Google Ads | ✓ | ✓ | GOOGLE_ADS_CLIENT_ID, _SECRET, _REFRESH_TOKEN, _DEVELOPER_TOKEN, _CUSTOMER_ID |
| Meta Ads | ✓ | ✓ | META_ACCESS_TOKEN, META_AD_ACCOUNT_ID |

## Budget Change Rules

1. Show the exact change before executing
2. Cap at 20% per action (raise or lower)
3. State assumptions (why this change, what metric it targets)
4. One change at a time — don't batch budget edits across campaigns
5. After the change, re-run `optimize` in 7 days to see if it moved the metric

## When NOT to Use Live Commands

- When you just need to see what's in the account → use `campaigns list/status/compare` (reads from captured reports, no API needed)
- When you're diagnosing → use `account diagnose` (reads from kernel state)
- When the tracking isn't set up → use `tracking check` first (fix tracking before touching bids)

## Error Handling

- **Missing creds:** "no campaigns found" — not a crash, not a traceback
- **API error:** printed as WARNING, returns empty data
- **Campaign not found:** lists available campaigns
- **Budget change too large:** blocked with exact max allowed shown