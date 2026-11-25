# Security policy

## Supported versions

Only the latest release of this plugin is supported. The MCP server it connects to is hosted by A1 and is always on the latest version.

| Version | Supported |
| ------- | --------- |
| Latest  | Yes       |
| Older   | No        |

## What this plugin does

This repository holds no server code. The plugin points your client at one hosted remote MCP server:

- URL: `https://www.a1.gallery/api/mcp` (Streamable HTTP, HTTPS only)
- Sign-in: OAuth in the browser with a free A1 account. There is no API key to store.
- Tools: read-only tools for the A1 gallery (websites, sections, pages, fonts, creators and measured design values), plus `save_to_board` and `remove_from_board`, which change only the signed-in user's own A1 boards.

## Reporting a vulnerability

Please email **hello@a1.gallery** with:

- what you found and where (the plugin files or the hosted server),
- steps to reproduce it,
- the impact you think it has.

Please do not open a public issue for a security problem. We aim to reply within 3 working days and will keep you updated until it is fixed.
