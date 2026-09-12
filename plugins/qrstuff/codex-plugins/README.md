# QRStuff MCP Server Plugin for OpenAI Codex

Official OpenAI Codex plugin for [QRStuff](https://www.qrstuff.com/). Connects OpenAI Codex CLI agents directly to the hosted QRStuff MCP server to generate, customize, and manage QR codes and track scan analytics seamlessly.

```bash
codex marketplace add qrstuff/codex-plugins
codex plugin install qrstuff-mcp-server@qrstuff-codex-plugins
```

## What It Does

This plugin exposes QRStuff's QR code generation, project management, and analytics platform to Codex agents:

- **25+ QR Code Types**: URLs, Plain Text, WiFi networks, vCard contacts, Email, SMS, Phone, Locations, and more.
- **Dynamic & Static QR Codes**: Generate static codes or editable dynamic QR codes with short URLs.
- **Visual Customization**: Configure custom foreground, background, and finder pattern colors, error correction levels (L, M, Q, H), and output formats (`png`, `svg`, `pdf`, `eps`).
- **Scan Analytics & Tracking**: Retrieve scan counts, date-wise breakdowns, geographic locations, and device statistics for dynamic QR codes.
- **Project Management**: Organize, list, update, restore, or transfer QR codes and projects.

## Installation

### From Codex CLI

```text
/marketplace add qrstuff/codex-plugins
/plugin install qrstuff-mcp-server@qrstuff-codex-plugins
```

### From the Terminal

```bash
codex marketplace add qrstuff/codex-plugins
codex plugin install qrstuff-mcp-server@qrstuff-codex-plugins
```

## Configuration & Authentication

The plugin connects automatically to the hosted QRStuff MCP endpoint:

```text
https://mcp.qrstuff.ai/mcp
```

- **Zero-Config Public Generation**: Standard QR code generation tools work out of the box with no API keys or configuration needed.
- **Account & Project Features**: To access your private QR codes, projects, and scan analytics, the MCP server handles authentication seamlessly via QRStuff OAuth 2.1.

## Example Agent Prompts

Once installed, ask Codex agents in natural language:

- *"Generate a QR code for https://qrstuff.com with high error correction and SVG format."*
- *"Create a WiFi QR code for network 'OfficeGuest' with password 'Welcome2026'."*
- *"Show my QRStuff account overview and scan statistics for the last 30 days."*
- *"List all my QR codes in the Marketing project."*

## Support & Links

- Website: [qrstuff.com](https://www.qrstuff.com/)
- Documentation: [qrstuff.com/docs](https://www.qrstuff.com/)
- Plugin Repository: [github.com/qrstuff/codex-plugins](https://github.com/qrstuff/codex-plugins)

