---
name: notibuddy-setup
description: Pair an iPhone/iPad with NotiBuddy, bind this host client when multiple destinations exist, verify two-way E2EE delivery, and diagnose pairing or MCP duplicates. Use when setting up or troubleshooting NotiBuddy.
---

# NotiBuddy Setup & Diagnostics

Help the user connect NotiBuddy safely without ever exposing pairing secrets in chat transcripts.

## Strict Privacy Rules

- **Never ask the user to paste an `nbpair1.` pairing bundle or setup snippet into chat.** Pairing secrets must stay strictly between the NotiBuddy iOS app and the user's own terminal.
- **Never read or print files under `~/.notibuddy/`.** Use only `nb status`, `nb doctor`, and `nb bind`.
- **Never choose between multiple paired phones on the user's behalf.** Always ask which alias to bind.

## Step-by-Step Verification

1. **Check local status:** Call `notibuddy_list_destinations` (if MCP tools are loaded) or run `nb status` (or `npx -y notibuddy@0.4.0 status`).
2. **If no destination is paired yet:**
   Tell the user to run these two steps on their own devices:
   - On iPhone/iPad: open **NotiBuddy → Connect → Add → Create setup code → Share Setup** (keep NotiBuddy open and online; code lasts 10 minutes).
   - In their own **Terminal** (not chat):
     ```bash
     pbpaste | npx -y notibuddy@0.4.0 pair --to personal
     ```
     *(Or `brew install yourbit-network/tap/notibuddy` first, then `pbpaste | nb pair --to personal`.)*
3. **If two or more destinations exist:**
   Ask which destination this host should use, then bind it explicitly (replaces ambiguity without editing plugin files):
   ```bash
   nb bind --client <host-id> --to <chosen-alias>
   ```
   *(Common `<host-id>` values: `claude-code`, `antigravity`, `cursor`, `codex`.)*
4. **Connect the local MCP server (if `notibuddy_*` tools are not yet loaded):**
   For Claude Code, register the local stdio server once in Terminal:
   ```bash
   claude mcp add -s user notibuddy -- npx -y notibuddy@0.4.0 mcp --client claude-code
   ```
   *(End-to-end encryption keys stay strictly on this computer and the user's iPhone.)*
5. **Verify health & relay approval:**
   Run `nb doctor --to <alias>` (or `npx -y notibuddy@0.4.0 doctor --to <alias>`). Do not regenerate keys if a diagnostic fails.
6. **Check for duplicate MCP servers:**
   If the user previously added a manual `notibuddy` MCP server entry alongside a marketplace plugin that already declares `.mcp.json`, advise removing the older duplicate so tools appear once.
7. **Confirm two-way delivery:**
   Call `notibuddy_notify` with `{ "title": "NotiBuddy connected", "message": "Tap OK to confirm two-way replies.", "options": ["OK"] }` (or run `nb gate "NotiBuddy connected" --approve "OK" --reject "Cancel"`). Confirm setup only after receiving a verified `status: "resolved"` reply.
