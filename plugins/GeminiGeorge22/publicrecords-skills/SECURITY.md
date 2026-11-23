# Security policy

## Reporting a vulnerability

Please report security problems privately through GitHub's **Report a vulnerability** button on this repository's Security tab (private vulnerability reporting). Do not open a public issue for a security problem. We aim to reply within 7 days.

## Scope

This repository holds Agent Skills (`SKILL.md`) and plugin/MCP manifests only. It contains no executable code, no scripts and no credentials. The only network endpoint it configures is Apify's hosted MCP server, `https://mcp.apify.com` (HTTPS, OAuth or the user's own Bearer token). Problems in the Apify MCP server itself belong to Apify: https://github.com/apify/apify-mcp-server/security.

## Secrets

Never put an Apify API token in this repository, in an issue, or in a chat. If you find one here, report it as above.
