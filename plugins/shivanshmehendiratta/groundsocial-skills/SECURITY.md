# Security

This repository holds skill texts, plugin manifests and a smoke-test script for Groundsocial. The skills run no code of their own on your machine: they tell the agent which Groundsocial API calls to make, and every call goes to `https://api.groundsocial.dev` (REST) or the hosted MCP server at `https://api.groundsocial.dev/mcp`.

## Reporting a problem

If you find a security problem in these skills, in the API, in the MCP server or in any other part of Groundsocial, write to **support@groundsocial.dev** with "security" in the subject. Include what you found, how to reproduce it and which account or key it affects, and give us time to fix it before you publish anything. We reply within three business days and tell you when the fix is out.

Please test only against your own account. A free account (100 credits, no card) is enough to reproduce most issues.

## What the skills can and cannot do

- Read-only. They fetch public, logged-out data and never post, message or log in to any social platform.
- Access comes from your own Groundsocial API key (`GROUNDSOCIAL_API_KEY`) or an OAuth sign-in in your MCP client. Keys never appear in skill files.
- The only side effect is spending your account's credits. You can set daily and monthly spend caps per key in the dashboard, and revoke a key at any time.

More on what the data is and how removal requests work: https://groundsocial.dev/docs/compliance
