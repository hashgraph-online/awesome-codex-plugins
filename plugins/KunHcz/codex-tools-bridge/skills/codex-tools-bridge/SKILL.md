---
name: codex-tools-bridge
description: Set up or diagnose Codex Tools Bridge when the user asks to connect ChatGPT Web to native local Codex tools through an OpenAI Secure MCP Tunnel. Use for a fresh dedicated installation or read-only connection diagnostics while preserving existing hosts, credentials, and native permissions.
---

# Codex Tools Bridge

This plugin provides setup and diagnostic guidance. The bridge runtime uses a separate source checkout, dedicated native tool host, and official Tunnel configuration. Installing the plugin does not start them. ChatGPT Web retains reasoning and conversation context; native Codex executes tools without a second model loop.

Read the current [setup guide](https://github.com/KunHcz/codex-tools-bridge/blob/main/docs/SETUP.md) and [security policy](https://github.com/KunHcz/codex-tools-bridge/blob/main/SECURITY.md) before acting. This is an experimental, macOS-first independent project.

## Fresh installation

1. Use the user's authorized scope to choose a fresh source checkout, dedicated workspace, private state directory, native Codex binary, and explicitly selected provider registry. Never overwrite an existing installation's runtime state or user-owned configuration.
2. Check Bun, Codex, compatible Desktop support, and the official tunnel-client with read-only version/help commands. Explain missing prerequisites without changing global defaults or installing access credentials.
3. Follow the setup guide in the fresh source checkout: install locked dependencies with lifecycle scripts disabled, run `bun run verify`, and run the read-only `doctor` command with the chosen paths.
4. For authorized setup, use the documented `prepare-desktop` command. It creates a dedicated workspace-write/on-request native task and an owned named provider definition in the selected registry. Keep `configured` tool access by default. `--tool-access all` is a separate explicit broad grant, never a troubleshooting shortcut.
5. Keep Tunnel credentials in the official client's local secret-management flow; never request their values in chat or read browser cookies. Use an explicitly selected unused Tunnel and preserve existing live consumers.
6. Follow the manual first start of the existing dedicated Desktop task and connect the private MCP plugin in ChatGPT. Verify the native tool inventory and `pwd` in the authorized workspace. Report actual results and build limitations; Tunnel readiness and automated tests do not establish fresh Desktop acceptance.

## Connection diagnostics

Run the configured checkout's documented `doctor` command with its existing paths. Report native host state separately from Tunnel readiness, using sanitized errors. Do not open private runtime state, transcripts, or credentials. Never stop/restart services, create another host, switch providers, or broaden permissions as an incidental repair.

A timed-out action may have executed; inspect state before retrying and never automatically replay an unknown outcome. Native permission prompts, OS protections, and physical-input pauses remain in force. Chat/task mappings may share files, credentials, applications, and the desktop. Requested tool results leave the machine for ChatGPT; this is a single-user bridge, not an offline or multi-tenant service.
