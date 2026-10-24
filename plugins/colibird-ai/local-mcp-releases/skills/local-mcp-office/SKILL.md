---
name: local-mcp-office
description: Use when the user wants to read or create Excel spreadsheets, Word documents or PowerPoint presentations, or read PDFs, from files on their Mac or Windows computer. Powered by LMCP; no Microsoft 365 subscription needed.
---

# Excel, Word, PowerPoint and PDF via LMCP

LMCP reads and writes Office files directly on the user's computer (macOS and Windows). It does not
need Microsoft 365 or Office installed to read or create the files.

## Core tools
- Excel: `excel_read`, `excel_create`, `excel_write_cell`.
- Word: `word_read`, `word_create`, `word_append`.
- PowerPoint: `ppt_read`, `ppt_create`.
- PDF: `pdf_read`.
- Find the file first with the file tools (`file_search`, `finder_search` on macOS, `explorer_search` on Windows), or in OneDrive and Google Drive.

## Good practice
- Read before writing: check sheet names and headers with `excel_read` before writing cells.
- Create new files next to the source instead of overwriting the user's original, unless asked.
- For a long PDF or deck, summarize by section instead of returning all the text.

Guides: https://www.local-mcp.com/guides/claude-excel-mac · https://www.local-mcp.com/guides/claude-office-docs-windows
