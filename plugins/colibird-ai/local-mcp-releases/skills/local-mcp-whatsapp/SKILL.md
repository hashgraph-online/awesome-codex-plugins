---
name: local-mcp-whatsapp
description: Use when the user wants to read, search or send WhatsApp messages, files or polls, or manage WhatsApp groups, on macOS or Windows. Powered by LMCP, which links WhatsApp to the computer with a QR code.
---

# WhatsApp via LMCP

LMCP links WhatsApp to the user's computer as a linked device (macOS and Windows). Messages are kept
in a local store on the computer, so search works across all chats.

## Core tools
- Setup: `whatsapp_connect` shows the QR code in the chat; `whatsapp_diagnose` checks the link; `whatsapp_list_accounts` when there is more than one number.
- Read: `whatsapp_list_chats`, `whatsapp_read_messages`, `whatsapp_search_messages`, `whatsapp_search_contacts`, `whatsapp_read_poll`.
- Groups: `whatsapp_list_groups`, `whatsapp_group_info`, `whatsapp_create_group`.
- Send: `whatsapp_send_message`, `whatsapp_send_file`, `whatsapp_send_poll`.
- `whatsapp_sync` pulls the latest messages, groups and contacts into the local store.

## Good practice
- Resolve the person with `whatsapp_search_contacts` before reading or sending.
- Summarize conversations rather than pasting every message.
- Every send is preview-first: show the chat and the text, confirm, then send.
- If a tool says WhatsApp isn't linked, offer `whatsapp_connect` instead of retrying.

Guides: https://www.local-mcp.com/guides/claude-whatsapp-mac · https://www.local-mcp.com/guides/claude-whatsapp-windows
