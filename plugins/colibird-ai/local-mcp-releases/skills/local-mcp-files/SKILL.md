---
name: local-mcp-files
description: Use when the user wants to find, read or create files and Office documents (Word/Excel/PowerPoint/PDF) on macOS or Windows, or browse OneDrive / Google Drive. Powered by LMCP; the tools execute on the device.
---

# Files & Office via LMCP

LMCP reads and writes the user's files, Office documents and cloud-drive contents on their computer. Everything below
exists on macOS and Windows unless marked otherwise.

## Core tools
- Local files: `file_list` (`path`, defaults to home), `file_read` (`path`), `file_search` (`query`, by name), `file_write`.
- Finder (macOS): `finder_list`, `finder_search`.
- Office (read + create): `word_read`/`word_create`/`word_append`, `excel_read`/`excel_create`/`excel_write_cell`, `ppt_read`/`ppt_create`, `pdf_read`.
- OneDrive: `onedrive_root` first, then `onedrive_list_files`, `onedrive_search_files`, `onedrive_read_file`, `onedrive_write_file`, `onedrive_move_file`.
- Google Drive (locally synced folder): `gdrive_root` first, then `gdrive_list_files`, `gdrive_search_files`, `gdrive_read_file`, `gdrive_write_file`.

## Good practice
- For "find my invoice from March", use `file_search` (or `finder_search` on macOS) then `pdf_read`/`excel_read`.
- Office create tools take structured input (rows, slides, headings) — build the content, then create.
- Some locations are off-limits (credential stores; on Windows, paths outside the allowed folders); if a read is denied, tell the user which path/permission is needed rather than retrying.
