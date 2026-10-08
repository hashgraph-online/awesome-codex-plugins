---
name: local-mcp-email
description: Use when the user wants to read, search, summarize, draft or triage their Apple Mail / Gmail / Outlook / iCloud email in Apple Mail on macOS. Powered by LMCP's Mail tools, which are macOS-only.
---

# Working with email via LMCP

LMCP reads Apple Mail on the user's Mac (Gmail, Outlook, iCloud — any account in Mail.app). The tools execute on the device; the content you read is sent to the user's AI provider as part of the conversation. For a Microsoft 365 mailbox not added to Mail.app, use `m365_list_emails` / `m365_search_emails` / `m365_read_email` (macOS and Windows, require `connect_m365_account`).

## Core tools
- `list_email_accounts` — see the user's accounts first if there are several.
- `list_emails` — recent headers. **On a multi-account Mac, always pass `account="<name>"`** to avoid scanning every account (slow). Use `offset` to page (limit caps at 50).
- `search_emails` — search by text; pass `account=` to scope and stay fast.
- `read_email` — full body of one message (pass `account=` and `mailbox=` from the list result to make the lookup fast).
- `create_draft` — compose a draft in Mail's Drafts for the user to review and send. **Never auto-send.**

## Good practice
- Lead with `list_email_accounts` when unsure which account.
- Summarize threads; don't dump raw bodies.
- For "reply to X", use `create_draft` with `reply_to_message_id` — the user sends it themselves.
- If a tool returns a permission or install message, relay the one-click setup step to the user; it means the LMCP app isn't installed or a permission isn't granted yet.
