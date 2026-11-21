---
name: local-mcp-teamchat
description: Use when the user wants to read or search Microsoft Teams or Slack on macOS or Windows, including channels and DMs. Powered by LMCP, which shows the messages already synced in the desktop apps.
---

# Teams & Slack via LMCP

LMCP shows the Teams and Slack messages already synced in the desktop apps the user is signed in to,
on macOS and Windows. Claude only receives the messages LMCP returns. Sending to Teams is different: `teams_send_channel_message`
(and `teams_send_message` on Windows) goes through Microsoft Graph and needs `connect_m365_account`.

## Core tools
- Teams: `teams_list_teams`, `teams_list_channels`, `teams_list_chats`, `teams_read_channel_messages`, `teams_read_chat_messages`; send via `teams_send_message` / `teams_send_channel_message` (preview-before-send).
- Slack: `slack_list_workspaces`, `slack_list_channels`, `slack_read_channel_messages`, `slack_search_messages`.

## Good practice
- Messages come from what the desktop app has already synced; summarize threads rather than dumping every message.
- For "what did the team decide about X", use `teams_read_channel_messages` / `slack_search_messages`.
- These show what the desktop app has synced — if a tool reports not-synced/not-set-up, the user needs the Teams/Slack desktop app installed and signed in; relay that instead of retrying.
- Any send is preview-first: show the channel + text, confirm, then send.
