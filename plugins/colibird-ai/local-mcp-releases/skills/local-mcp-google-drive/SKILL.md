---
name: local-mcp-google-drive
description: Use when the user wants to find, read or write files in Google Drive (My Drive or Shared drives) on macOS or Windows. Powered by LMCP, working with the folder Google Drive for desktop syncs on the computer.
---

# Google Drive via LMCP

LMCP works with the folder that Google Drive for desktop syncs on the user's computer, so it needs
no Google Cloud project, OAuth consent screen or API token. Files LMCP writes upload through Google
Drive for desktop.

## Core tools
- `gdrive_root` lists the synced Drive folders (My Drive, Shared drives, one per account).
- `gdrive_list_files`, `gdrive_search_files`, `gdrive_file_info`, `gdrive_read_file`.
- `gdrive_write_file` creates or overwrites a text file; `gdrive_delete_file` (macOS).
- `gdrive_set_scope` (Windows) picks the active Drive when several accounts are synced; `gdrive_disconnect` turns a Drive folder off.
- For .docx, .xlsx, .pptx and .pdf files in Drive, use `word_read`, `excel_read`, `ppt_read` and `pdf_read` on the path.

## Good practice
- Google Docs, Sheets and Slides are links in the synced folder, not documents with text: export them or ask the user for an Office/PDF copy.
- Confirm before overwriting or deleting.
- If no Drive folder appears, the user needs Google Drive for desktop installed and signed in.

Guide: https://www.local-mcp.com/guides/claude-google-drive-mac
