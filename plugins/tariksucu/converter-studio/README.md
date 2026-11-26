# Converter Studio for AI assistants

[Converter Studio](https://converter.studio) converts files between **67 formats**: video, audio, images, PDFs, documents, e-books, subtitles, data and archives (HEIC to JPG, MOV to MP4, video to MP3, Word to PDF, PDF to images and hundreds more pairs). This repository connects it to AI assistants and coding agents:

- an **MCP server** at `https://converter.studio/api/mcp` (Streamable HTTP),
- a **plugin** for Claude Code and Codex, an **extension** for Gemini CLI,
- four **Agent Skills** that use the MCP tools when connected, and local ffmpeg, ImageMagick, cwebp or LibreOffice commands otherwise:
  - `convert-files`: one file to another format;
  - `batch-convert`: a whole folder, one target format per file type;
  - `web-ready-media`: images to WebP/AVIF in responsive sizes, videos to streaming-friendly MP4/WebM with a poster;
  - `extract-audio`: the sound of a video as MP3, M4A, WAV or FLAC (cut, evened out, or ready for transcription), and its subtitles as SRT.

Give the assistant a link or a file; it gets back a download link, valid for 6 hours.

## 1. Get an API key

Create a key on your [account page](https://converter.studio/account#api-keys). Conversions use your account's credits, the same as on the website: free accounts get 25 credits a day, and most files cost 1 credit; audio and video are priced by their length (and video by its frame size and the format made, WebM costing several times more than MP4) once Converter Studio has looked at them. Plans: [converter.studio/pricing](https://converter.studio/pricing).

```bash
export CONVERTER_STUDIO_API_KEY=cvs_live_...
```

## 2. Connect

**Claude Code** (plugin with the MCP server and the skills):

```bash
claude plugin marketplace add tariksucu/converter-studio
claude plugin install converter-studio@converter-studio
```

or the MCP server alone:

```bash
claude mcp add --transport http converter-studio https://converter.studio/api/mcp \
  --header "Authorization: Bearer $CONVERTER_STUDIO_API_KEY"
```

**Codex**: `codex plugin marketplace add tariksucu/converter-studio`, or in `~/.codex/config.toml`:

```toml
[mcp_servers.converter-studio]
url = "https://converter.studio/api/mcp"
bearer_token_env_var = "CONVERTER_STUDIO_API_KEY"
```

**Gemini CLI**: `gemini extensions install https://github.com/tariksucu/converter-studio`, then `gemini extensions config converter-studio` to set the key.

**Kiro**: [![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](https://kiro.dev/launch/mcp/add?name=converter-studio&config=%7B%22url%22%3A%22https%3A%2F%2Fconverter.studio%2Fapi%2Fmcp%22%2C%22headers%22%3A%7B%22Authorization%22%3A%22Bearer%20%24%7BCONVERTER_STUDIO_API_KEY%7D%22%7D%2C%22disabled%22%3Afalse%2C%22autoApprove%22%3A%5B%5D%7D) (reads the key from `CONVERTER_STUDIO_API_KEY`).

**Cursor, VS Code, Windsurf and other MCP clients**: the URL `https://converter.studio/api/mcp` with the header `Authorization: Bearer <your key>`. Ready settings for each: [converter.studio/developers](https://converter.studio/developers).

## Tools

| Tool                 | What it does                                                                                                        |
| -------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `list_formats`       | Formats and what each converts to (no key needed)                                                                   |
| `convert`            | Converts from a link (direct, Google Drive, Dropbox, OneDrive), an upload, or a small file sent inline (up to 8 MB) |
| `create_upload`      | An upload URL and `curl` command for local files over 8 MB                                                          |
| `get_conversion`     | Status and download link; waits for the result                                                                      |
| `confirm_conversion` | Starts a conversion that costs more than `maxCredits` (default 20)                                                  |
| `get_account`        | Plan, credits left, largest file                                                                                    |

The same is available as a REST API: [converter.studio/developers](https://converter.studio/developers#rest).

The MCP server is also listed on [Glama](https://glama.ai/mcp/connectors/studio.converter/converter-studio).

## Privacy

Files are used only to convert them. Uploads are deleted after the conversion and results after 6 hours. See the [privacy policy](https://converter.studio/privacy). Questions: support@converter.studio.

## License

The files in this repository (plugin, extension and skills) are MIT-licensed. Converter Studio itself is a hosted service.
