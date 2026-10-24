---
name: local-mcp-onedrive
description: Use when the user wants to find, read, write, move or organize files in OneDrive (personal or work) on macOS or Windows. Powered by LMCP, working with the OneDrive folder already synced on the computer.
---

# OneDrive via LMCP

LMCP works with the OneDrive folder that the OneDrive app already syncs on the user's computer
(macOS and Windows), so it needs no Graph API, OAuth token or Azure AD app. Changes sync to the
user's other devices through OneDrive itself.

## Core tools
- `onedrive_root` lists the synced OneDrive folders (personal and work accounts).
- `onedrive_list_files`, `onedrive_search_files`, `onedrive_file_info`, `onedrive_read_file`.
- `onedrive_write_file`, `onedrive_move_file`, `onedrive_delete_file`.
- `onedrive_set_scope` limits access to a single folder; `onedrive_disconnect` turns a OneDrive folder off.
- For Office files inside OneDrive, use `excel_read`, `word_read`, `ppt_read` and `pdf_read` on the file path.

## Good practice
- Start with `onedrive_root` when there is more than one account.
- Files that are online-only download when read; a very large folder search can take a moment.
- Confirm before deleting, and prefer moving over deleting when the user is reorganizing.

Guides: https://www.local-mcp.com/guides/claude-onedrive-windows · https://www.local-mcp.com/guides/claude-onedrive-mac
