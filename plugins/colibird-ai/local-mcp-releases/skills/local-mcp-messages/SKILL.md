---
name: local-mcp-messages
description: Use when the user wants to read or search iMessage, WhatsApp or Signal (macOS) or Microsoft Teams and Slack (macOS and Windows) from the apps on their computer. Powered by LMCP.
---

# Messages & team chat via LMCP

LMCP reads message stores on the user's computer. iMessage (Messages.app), WhatsApp and Signal are available
**only on macOS**; Microsoft Teams and Slack work on **macOS and Windows**.

## Core tools
- iMessage (macOS): `list_message_chats`, `read_messages`, `search_messages`.
- Teams (macOS and Windows): `teams_list_chats` / `teams_list_channels` / `teams_read_chat_messages` / `teams_read_channel_messages`.
- Slack (macOS and Windows): `slack_list_workspaces` / `slack_list_channels` / `slack_read_channel_messages` / `slack_search_messages`.
- WhatsApp (macOS): `whatsapp_list_chats` / `whatsapp_read_messages` / `whatsapp_search_messages`.
- Signal (macOS): `signal_list_chats` / `signal_read_messages` / `signal_search_messages`.
- Sending: `send_message` (iMessage, macOS) and `teams_send_message` (macOS and Windows; on Windows it goes through Microsoft Graph and needs `connect_m365_account`) return a preview first and send only with `confirm=true` — never send silently.

## Good practice
- Reading is fast; summarize conversations rather than dumping every line.
- For "did X text me about Y", use `search_messages`.
- Teams/Slack/WhatsApp/Signal require the respective app or account to be set up on the computer; if a tool says it's not connected/synced, relay that setup step to the user.
- Any send is preview-first — show the recipient + text, confirm, then send.
