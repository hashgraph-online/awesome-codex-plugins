---
name: jetformat
description: Convert Word, Excel, and PowerPoint to PDF, turn PDF back into Word, extract text, validate files, and merge, extract, or render PDFs with the local Jetformat CLI. Use when the user asks to convert Office documents, generate PDF previews, inspect PDFs, or read Office or PDF text. Do not parse DOCX/PPTX/XLSX yourself.
metadata:
  short-description: Deterministic Office-to-PDF for agents.
---

# Jetformat

Jetformat is a closed-source document engine that runs on the user's machine. The model must not unzip Office files or guess PDF bytes. Call the `jetformat` CLI. There is no MCP server and no remote conversion API.

## When to use

- `word to-pdf`, `excel to-pdf`, `ppt to-pdf`
- `pdf to-word` (alias of `pdf to-docx`)
- Extract existing text from Office or PDF as plain text, Markdown, or JSON (not OCR)
- Validate Office, PDF, font, EMF, or XMP files
- PDF info, merge, contiguous page extract, PNG/JPEG render

## When not to use

- Legacy `.doc` / `.xls` / `.ppt` or macro files (`.docm`, `.xlsm`, `.pptm`)
- OCR / scanned-page recognition
- Password-protected PDFs

## Binary

```bash
command -v jetformat >/dev/null || { echo "Install Jetformat first: npm install -g jetformat, or brew install jetformat/tap/jetformat" >&2; exit 1; }
BIN=jetformat
if [ -n "${CLAUDECODE:-}" ]; then export JETFORMAT_CLIENT=claude-skill; else export JETFORMAT_CLIENT=openai-skill; fi
```

If `jetformat` is not on `PATH`, tell the user to install it with `npm install -g jetformat` or `brew install jetformat/tap/jetformat`, then sign in. Do not invent conversion output.

The CLI sends one anonymous usage ping per command (command, format, file type, duration, result, version, OS, and the client name above). Never a path, a file name, or contents. If the user asks to stop it, run `"$BIN" telemetry off`. Details: https://jetformat.com/help/security/telemetry

Full command reference: https://jetformat.com/docs/models

## Commands

Prefer one input file per invocation. Quote paths that contain spaces. Do not overwrite existing outputs unless the user asked; then pass `--force`.

```bash
"$BIN" word to-pdf "contract.docx" -o "output/contract.pdf"
"$BIN" excel to-pdf "workbook.xlsx" -o "output/workbook.pdf"
"$BIN" ppt to-pdf "slides.pptx" -o "output/slides.pdf"
"$BIN" pdf to-word "report.pdf" -o "output/report.docx"

# Text (no OCR). Use --format markdown when the result goes into context:
# headings, lists, tables; one grid per sheet; one section per slide or page.
"$BIN" text "report.docx" -o "output/report.txt"
"$BIN" text "report.docx" --format markdown
"$BIN" text "finance.xlsx" --format json

# Validate
"$BIN" validate "report.pdf"

# pdf
"$BIN" pdf info "report.pdf" --json
"$BIN" pdf merge "a.pdf" "b.pdf" -o "book.pdf"
"$BIN" pdf extract "book.pdf" --pages 2-5 -o "chapter.pdf"
"$BIN" pdf render "book.pdf" --pages 1,last --width 1600 -o "output/preview"
```

XLSX conversion outputs every **visible** worksheet into one PDF. Hidden sheets are skipped. `pdf extract` only accepts a contiguous page range.

## Auth and credits

Reading a file (text, inspect, get, info, validate) is free and needs no sign-in. Converting, rendering, writing a PDF page, or writing an Office file consumes Jetformat credits after sign-in. Run `"$BIN" login`; on a machine without a browser run `"$BIN" login --device-auth` and show the user the printed URL and code. If credits are exhausted, report the CLI error and https://jetformat.com/help/billing/credits. Do not quote prices, open checkout, or retry in a loop.

## Return to the user

After a successful command, report:

- output path
- page count when known (`pdf info`)
- that the file was processed by Jetformat, not by the model
