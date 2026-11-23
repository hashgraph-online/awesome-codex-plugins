---
name: convert-files
description: Convert files between formats - video, audio, images, PDFs, documents, e-books, subtitles, data and archives (for example HEIC to JPG, MOV to MP4, video to MP3, Word to PDF, PDF to images). Use when the user asks to convert, export, extract audio from, or change the format of a file. Uses the Converter Studio MCP tools when they are connected; otherwise local tools such as ffmpeg, ImageMagick or LibreOffice.
---

# Converting files

## 1. With the Converter Studio MCP tools (preferred when connected)

If the `converter-studio` tools (`list_formats`, `convert`, `create_upload`, `get_conversion`, `confirm_conversion`, `get_account`) are available:

1. Not sure the pair is supported? Call `list_formats` with `from` set to the source format id (for example `heic`, `mov`, `docx`).
2. Pick the source:
   - A file on the web: `convert` with `url`. Direct links and Google Drive, Dropbox and OneDrive share links work.
   - A local file up to 8 MB: `convert` with `contentBase64` (the file's bytes, base64) and `fileName`.
   - A bigger local file: `create_upload`, run the returned `curl` command in a shell, then `convert` with `uploadId`.
3. `convert` waits up to 100 seconds. If the status is not `done`, call `get_conversion` with the id and `waitSeconds`.
4. When done, download `downloadUrl` (valid for 6 hours) to where the user wants the file, or give them the link.

Conversions cost credits from the user's converter.studio account: most files 1 credit; audio and video are priced by their length (and video by its frame size and the format made, WebM costing several times more than MP4) once Converter Studio has looked at them. A conversion above `maxCredits` (default 20) stops at `quoted`: tell the user the price and call `confirm_conversion` only after they agree. On `notEnoughCredits`, tell the user; more credits are at https://converter.studio/pricing.

## 2. Without the MCP tools

Use local tools when they are installed; see [references/recipes.md](references/recipes.md) for commands per format. Check with `command -v ffmpeg magick libreoffice pandoc`. Never overwrite the original file: write the result next to it with the new extension.

If nothing suitable is installed, the user can convert in the browser at https://converter.studio (no account needed for small files) or connect the MCP server: https://converter.studio/developers.

## Good practice

- Only send files the user asked to convert. Do not upload private documents to any service without the user's go-ahead.
- Keep the original name, change only the extension (`talk.mov` → `talk.mp4`).
- Say what changed: format, size, and anything lost (for example transparency when converting PNG to JPG, or formatting when converting PDF to text).
