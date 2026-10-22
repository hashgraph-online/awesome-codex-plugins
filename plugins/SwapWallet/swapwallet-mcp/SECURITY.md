# Security policy

This repository holds the public description and client configs of SwapWallet's MCP server. The server itself runs in SwapWallet's backend at `https://swapwallet.app/mcp`.

## Reporting a vulnerability

Please report vulnerabilities in the MCP server, its OAuth flow or these configs **privately**, not in a public issue:

- Contact: https://t.me/SadeghHayeri (see https://swapwallet.app/.well-known/security.txt)
- Policy, scope and testing rules: https://swapwallet.app/security

We answer in Persian or English and aim to acknowledge reports within a few working days.

## How the server protects funds

- OAuth 2.1 with PKCE; per-scope consent; tokens can be revoked by the user at any time.
- No tool moves money by itself. `request_*` tools only create a request that is priced and sent to the user's Telegram; it runs only after the user approves it there, and expires after 15 minutes.
- No scope lets an agent execute a withdrawal without the user's approval.
- This repository contains no secrets, binaries or executable code: only JSON configs, Markdown and images.
