# Security

This repository holds manifests, skill texts and documentation for the Termalin plugin. It runs no code on your machine: every tool call goes to Termalin's hosted MCP server at `https://termal.in/mcp`, and the open-source stdio bridge lives in [termalinapp/termalin-mcp](https://github.com/termalinapp/termalin-mcp).

## Reporting a problem

If you find a security problem in this plugin, in the hosted MCP server or in any other part of Termalin, write to **support@termal.in** with "security" in the subject. Please include what you found, how to reproduce it and which account or server it affects, and give us time to fix it before you publish anything. We answer within three business days and tell you when the fix is out.

Please do not test against servers or accounts that are not yours. A Free Termalin account with one Connector on your own machine is enough to reproduce most issues.

## What the plugin can and cannot do

- The agent never receives an SSH key or a password. Access comes from the user's Termalin account over OAuth or an API key, and each command is signed with a short-lived certificate issued by Termalin.
- Every connection has a command policy set by the account owner (full, allowlist or read-only) and an audit log in the web cabinet.
- Access can be revoked at any time from the account page (AI apps and API keys).

More on how Termalin handles data: https://termal.in/security/ and https://termal.in/privacy/
