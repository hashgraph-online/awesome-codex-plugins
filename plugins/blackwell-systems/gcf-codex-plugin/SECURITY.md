# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in this plugin, please report it responsibly.

**Email:** dayna@blackwell-systems.com

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact

We will acknowledge receipt within 48 hours and provide a fix timeline within 7 days.

## Scope

This plugin wraps MCP servers with gcf-proxy for token optimization. It:
- Does NOT store or transmit credentials
- Does NOT modify MCP server behavior beyond re-encoding responses
- Writes session stats to `/tmp/gcf-proxy-stats.json` (local, ephemeral)
- Runs gcf-proxy as a subprocess with the same permissions as the parent process
