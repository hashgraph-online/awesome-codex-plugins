# Security policy

## Reporting a vulnerability

Email **hello@greatwork.company** with "Security" in the subject line. Include the affected component (this plugin's files, the MCP server at `https://bankbridge.money/api/mcp`, or the bankbridge.money website), steps to reproduce, and any proof of concept. Please don't open a public GitHub issue for security problems.

We will confirm receipt and keep you posted until the issue is fixed. Please give us a reasonable window to fix the problem before disclosing it publicly.

## Scope

- This repository: plugin manifests, the skill, slash commands and MCP configuration.
- The hosted BankBridge service at bankbridge.money, including OAuth sign-in and the MCP endpoint.

## How BankBridge handles data

- Access to bank data is read-only. No tool can move money, pay bills or place trades.
- Financial data is fetched live from the bank on each request and is not stored by BankBridge.
- MCP clients sign in with OAuth 2.1. This repository contains no keys or secrets.

More detail: https://bankbridge.money/security and https://bankbridge.money/privacy
