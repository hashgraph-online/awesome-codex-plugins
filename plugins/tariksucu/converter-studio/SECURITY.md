# Security

## Reporting a vulnerability

Email **support@converter.studio** with "Security" in the subject. Please include what you found, how to reproduce it and what it affects. Do not open a public issue for a vulnerability.

We aim to reply within a few working days and will tell you when it is fixed. Please give us a reasonable time to fix it before you publish anything.

## Scope

- This repository: the plugin and extension manifests, the MCP settings and the Agent Skills.
- The hosted service it connects to: the MCP server at `https://converter.studio/api/mcp`, the REST API and the website `https://converter.studio`.

## What this repository does

It contains no executable code. The manifests point the assistant at one network endpoint, `https://converter.studio/api/mcp`, authenticated with your Converter Studio API key in the `Authorization` header (read from the `CONVERTER_STUDIO_API_KEY` environment variable or your client's settings). The skills suggest local commands (ffmpeg, ImageMagick, cwebp, LibreOffice) that the assistant shows and runs only with your client's usual permission prompts.

Keep your API key out of shared files and repositories. You can revoke a key at any time on your [account page](https://converter.studio/account#api-keys).
