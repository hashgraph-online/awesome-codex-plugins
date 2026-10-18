# LMCP — Context and Actions for Your AI

[![npm](https://img.shields.io/npm/v/local-mcp)](https://www.npmjs.com/package/local-mcp)
[![macOS](https://img.shields.io/badge/macOS-13%2B-blue)](https://www.local-mcp.com/download?ref=github-releases)
[![Windows](https://img.shields.io/badge/Windows-10%2B-blue)](https://www.local-mcp.com/download?ref=github-releases)

**Give your AI the context to get things done.** LMCP connects compatible assistants to your apps and accounts through the Model Context Protocol (MCP). Bring together relevant information from email, messages, calendars and files, then use tools to turn that context into useful action — with less searching and copying between apps.

Use it with **Claude, ChatGPT, Codex, Cursor** and other compatible MCP clients. Available integrations and connection methods vary by assistant, platform and permissions.

**[Download for Mac or Windows →](https://www.local-mcp.com/download?ref=github-releases)** · **[Explore the product](https://www.local-mcp.com/mcp-context)** · **[Setup guides](https://www.local-mcp.com/guides)**

This repository contains release information, documentation and the npm wrapper. The core binary is proprietary; documentation and scripts have their own license — see [LICENSE](LICENSE).

## More than one app's view of your information

An email, a message and a document may each contain only part of the answer. With compatible tools and access you authorize, your assistant can find those pieces across apps and accounts and use them together.

| What you ask | How connected context helps |
|---|---|
| “Tell me everything I still owe the architect — I can't remember her name.” | Search relevant messages, email and files to identify the person and assemble outstanding requests with their sources. |
| “Help organize my day so I can meet my commitments.” | Combine calendar events, tasks and relevant messages to propose a realistic plan and make supported updates when authorized. |
| “Prepare replies to customer orders using the inventory and plan dispatch.” | Read accessible order and inventory information, draft replies and use supported scheduling tools. Review proposed actions before authorizing execution. |

These illustrate workflows an assistant can build from available tools, not guaranteed autonomous outcomes. Sources must be accessible; assistant capabilities and each tool's permissions still apply.

## Apps and tools

Explore email, calendars, contacts, messages, tasks, files, documents, browser automation and other integrations. Examples include Apple Mail, Outlook, Microsoft Teams, Slack, WhatsApp, Signal, Google Drive, OneDrive, Microsoft 365, Notes, Reminders, Microsoft To Do, OmniFocus, Notion and ServiceNow.

**Not every integration is available on both operating systems.** Apple-native tools require macOS; connected services may need their own sign-in or permissions. Some tools use locally cached or synced data rather than a complete cloud account.

For current tools, requirements and platform coverage, use the **[tool reference](https://www.local-mcp.com/tools)** and **[guides](https://www.local-mcp.com/guides)** rather than a fixed count in this README.

## See it work

<p align="center">
  <img src="assets/claude-web-demo.gif" alt="Claude.ai using LMCP tools on a Mac to create a note and a reminder, including a consent dialog" width="700">
</p>

The recording shows a Mac workflow through Cloud Data Forwarding, not every platform or integration.

**Watch the 1-minute overview** — what MCP is, how LMCP works, and a real run from email to Excel, Word and a reminder:

<p align="center">
  <a href="https://youtu.be/_Ssrmlm0VyA"><img src="https://img.youtube.com/vi/_Ssrmlm0VyA/maxresdefault.jpg" alt="LMCP overview video: the MCP server that connects Claude, ChatGPT and Cursor to your Mac and Windows apps" width="700"></a>
</p>

[Ver en español](https://youtu.be/x3tc6sbF8gI)

## Install and connect

1. **[Download LMCP for your operating system](https://www.local-mcp.com/download?ref=github-releases).** Follow the installer and onboarding steps.
2. Select your assistant and enable the compatible integrations you want to use.
3. Grant required permissions or sign in where needed, then follow the assistant-specific setup guide.

### Cursor plugin

This repository is also a Cursor plugin. It adds the `local-mcp` MCP server, a rule that tells Cursor's agent when to use LMCP, and skills for email, calendar, messages, files and Office.

LMCP must be installed first (step 1 above): the plugin starts the LMCP server on your computer and does not work without it.

Supports **macOS 13+** and **Windows 10+ (64-bit)**. Linux, iOS and Android are not supported yet; join the waitlist on the **[download page](https://www.local-mcp.com/download?ref=github-releases)**.

Choose one installation path:

- **Signed installer** for Mac (`.pkg`) or Windows: **[download page](https://www.local-mcp.com/download?ref=github-releases)**.
- **macOS terminal:** `curl -fsSL 'https://www.local-mcp.com/install?ref=github-releases' | bash`
- **Windows PowerShell:** `irm https://www.local-mcp.com/install-windows?ref=github-releases | iex` (per-user, no administrator rights or Node.js needed).
- **Claude Desktop extension:** one-click `.mcpb` at **[www.local-mcp.com/install/mcpb](https://www.local-mcp.com/install/mcpb)**.
- **npm (requires Node.js):** `npx -y local-mcp@latest setup` configures the compatible clients it detects.

Details for agents and each path: **[llms-install.md](llms-install.md)**. After installing, fully restart your AI client; MCP tools load at startup.

Local desktop/CLI clients and web assistants connect differently. The installer configures the compatible local clients it detects. Web assistants (ChatGPT, Claude.ai, Grok, Perplexity) connect through **`https://www.local-mcp.com/mcp`** as a custom connector with OAuth. They need the local app installed and Cloud Data Forwarding enabled in LMCP (off by default); with forwarding off, the connector exposes only `setup_install`. Follow the **[web AI guide](https://www.local-mcp.com/guides/web-ai)** and the **[current guides](https://www.local-mcp.com/guides)**.

An endpoint alone is not a verified connection: complete authorization and check that tools are available in your client.

## Install LMCP in your AI tool

Install the LMCP app first (see above); it runs the tools on your computer. Then add LMCP to your assistant. After any of these, fully restart the tool: MCP tools load at startup.

| Tool | Copy-paste |
|---|---|
| **Claude Code** | `claude plugin marketplace add colibird-ai/local-mcp-claude-plugin && claude plugin install local-mcp@local-mcp` (inside Claude Code: `/plugin marketplace add colibird-ai/local-mcp-claude-plugin` then `/plugin install local-mcp@local-mcp`) |
| **Codex CLI** | `codex plugin marketplace add colibird-ai/local-mcp-releases && codex plugin add local-mcp@local-mcp` (or, MCP server only: `codex mcp add local-mcp -- npx -y local-mcp@latest`) |
| **GitHub Copilot CLI** | `copilot plugin marketplace add colibird-ai/local-mcp-claude-plugin && copilot plugin install local-mcp@local-mcp` |
| **VS Code (Copilot Chat)** | `code --add-mcp '{"name":"local-mcp","command":"npx","args":["-y","local-mcp@latest"]}'` |
| **Gemini CLI** | `gemini extensions install https://github.com/colibird-ai/local-mcp-releases` |
| **Cursor** | `npx -y local-mcp@latest setup` (or install the Cursor plugin from this repository) |
| **Windsurf, Zed, Claude Desktop** | `npx -y local-mcp@latest setup` configures the clients it detects |
| **LM Studio** (0.3.17 and later) | [![Add to LM Studio](https://files.lmstudio.ai/deeplink/mcp-install-light.svg)](lmstudio://add_mcp?name=local-mcp&config=eyJjb21tYW5kIjoibnB4IiwiYXJncyI6WyIteSIsImxvY2FsLW1jcEBsYXRlc3QiXX0%3D) |
| **Cline, Continue, Goose, OpenCode and other MCP clients** | Add this server to the client's MCP settings: `npx -y local-mcp@latest` (command `npx`, arguments `-y local-mcp@latest`) |

Examples for clients that use their own config format:

```bash
# Goose
goose session --with-extension "npx -y local-mcp@latest"
```

```jsonc
// OpenCode: opencode.json
{ "mcp": { "local-mcp": { "type": "local", "command": ["npx", "-y", "local-mcp@latest"] } } }
```

```jsonc
// Zed: settings.json
{ "context_servers": { "local-mcp": { "command": "npx", "args": ["-y", "local-mcp@latest"] } } }
```

```jsonc
// Cline (cline_mcp_settings.json), LM Studio (mcp.json), Claude Desktop, Windsurf
{ "mcpServers": { "local-mcp": { "command": "npx", "args": ["-y", "local-mcp@latest"] } } }
```

These paths need Node.js. Web assistants (ChatGPT, Claude.ai, Grok, Perplexity) connect differently; see above.

## How it works

**Your assistant → MCP → available tools → relevant apps and accounts → context and actions.**

Compatible tools execute on your computer. Some read native data, local caches or synced files; others connect to services requiring authentication and a network connection. Your assistant chooses tools for your request within the access you grant — it does not automatically gain access to every account.

## Local tools, clear data boundaries

- Local execution does not mean a cloud AI receives no data. Your chosen assistant or connected service may receive content needed for your request, including when a desktop client uses a cloud model.
- Cloud Data Forwarding is optional, off by default, and lets supported web assistants reach tools on your computer. Review its data flow and provider policies before enabling it.
- Permissions, preview and confirmation support vary by tool. Review behavior and authorize actions before execution; do not assume a universal confirmation dialog.
- Locally available read operations may work offline. Cloud models, connected services, sending and remote updates can require a network connection.

See **[Privacy](https://www.local-mcp.com/en/privacy)** and **[Security](SECURITY.md)**. Compliance depends on your complete workflow and provider agreements, not only on where a tool runs.

## Learn more

- **[Apple Mail with Claude](https://www.local-mcp.com/guides/claude-email-mac)**
- **[ChatGPT, Claude.ai, Grok and Perplexity on the web](https://www.local-mcp.com/guides/web-ai)**
- **[Microsoft Teams without Graph API](https://www.local-mcp.com/guides/claude-teams-no-api)**
- **[WhatsApp on Mac](https://www.local-mcp.com/guides/claude-whatsapp-mac)**
- **[Recipes and workflows](https://www.local-mcp.com/recipes)**

## Releases and support

See **[GitHub Releases](https://github.com/colibird-ai/local-mcp-releases/releases)** for this repository's history and the **[download page](https://www.local-mcp.com/download?ref=github-releases)** for current installers. Mac and Windows can have different release versions; a GitHub tag alone is not a fleet-wide deployment signal.

- Report a problem through LMCP's available feedback tools or **[open an issue](https://github.com/colibird-ai/local-mcp-releases/issues)**. Include OS and app version, and remove sensitive content from logs.
- Request a feature through the available feedback tools or GitHub Issues.
- Contact **[ctpo@colibird.co](mailto:ctpo@colibird.co)** for support; see [SECURITY.md](SECURITY.md) for vulnerabilities.
- For current availability and commercial terms, see **[the website](https://www.local-mcp.com)** and [LICENSE](LICENSE). This README does not promise permanent pricing or future features.

If LMCP helps you, **[star the repository](https://github.com/colibird-ai/local-mcp-releases)** to help others discover it.
