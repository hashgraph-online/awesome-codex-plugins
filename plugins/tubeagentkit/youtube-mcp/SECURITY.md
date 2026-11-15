# Security Policy

## Supported versions

Only the latest release of this plugin and the hosted MCP server at `https://getyoutubetranscript.com/mcp` are supported. Older plugin versions keep working against the hosted server, but fixes land only in the latest version.

## Reporting a vulnerability

Please report security issues privately by email to **issac@getyoutubetranscript.com** with "Security" in the subject line. Do not open a public GitHub issue for a vulnerability.

Include:

- what you found and where (plugin file, MCP tool, or API endpoint)
- steps to reproduce
- the impact you expect

We aim to reply within 3 business days and to ship a fix or mitigation for confirmed issues as fast as their severity calls for. We will credit you in the release notes unless you ask us not to.

## Scope

- This repository: plugin manifests, skills, the local stdio server in `server/`
- The hosted MCP server and REST API at getyoutubetranscript.com

Out of scope: YouTube itself, third-party MCP clients, and denial-of-service or volume testing against production.

## How the plugin handles credentials

The plugin holds no secrets. It connects to the hosted MCP server with OAuth or with an API key that you supply through your client's environment or settings. Keys are never written to this repository.
