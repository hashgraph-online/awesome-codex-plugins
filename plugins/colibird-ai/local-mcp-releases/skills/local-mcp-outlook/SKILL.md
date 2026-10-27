---
name: local-mcp-outlook
description: Use when the user wants to read, search, reply to or send Microsoft Outlook email, or work with Outlook calendar and contacts, on Windows or macOS. Powered by LMCP, reading the Outlook account already set up on the computer.
---

# Outlook via LMCP

LMCP works with the Outlook account already set up on the user's computer: no Azure app
registration, no Graph API token and no tenant admin approval.

## Core tools
- **Outlook app tools**: `outlook_list_emails`, `outlook_search_emails`, `outlook_read_email`,
  `outlook_reply_email`, `outlook_reply_all`, `outlook_forward_email`, `outlook_send_email`, `outlook_move_email`,
  `outlook_flag_email`, `outlook_save_attachment`; calendar `outlook_calendar_list_events`,
  `outlook_calendar_create_event`; contacts `outlook_contacts_search`, `outlook_get_contact`.
- **Mail tools**: `list_emails`, `search_emails`, `read_email` and `reply_email` read the mail accounts configured
  on the computer. `outlook_diagnose` shows which Outlook accounts LMCP can see and what is missing.
- A Microsoft 365 account can also be connected with `connect_m365_account` for the `m365_*` tools.

## Good practice
- Search first (`outlook_search_emails` / `search_emails`), then read the few messages that matter.
- Summarize threads instead of pasting whole emails.
- Sending, replying and forwarding are preview-first: show recipients and text, confirm, then send.
- If an account is missing, run `outlook_diagnose` and relay its fix to the user.

Guides: https://www.local-mcp.com/guides/claude-outlook-windows · https://www.local-mcp.com/guides/claude-outlook-mac
