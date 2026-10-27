---
name: local-mcp-notion
description: Use when the user wants to search or read Notion pages and databases from the Notion desktop app on macOS, without a Notion integration token. Powered by LMCP. Read-only.
---

# Notion via LMCP

LMCP reads the Notion desktop app's local cache on macOS: no integration token and no workspace
admin approval. It is read-only; creating or editing pages needs Notion's own API.

## Core tools
- `notion_list_workspaces`, `notion_list_pages`, `notion_list_databases`.
- `notion_search` finds pages by title or text.
- `notion_read_page` returns a page as markdown; `notion_read_database` returns rows with their properties.
- `notion_open_page` opens a page in the Notion app.

## Good practice
- Search first, then read the pages that match.
- Only content the desktop app has cached is available. If a page is missing, ask the user to open it in Notion or mark it «Available offline».
- For edits, give the user the text to paste, or open the page with `notion_open_page`.

Guide: https://www.local-mcp.com/guides/claude-notion-mac
