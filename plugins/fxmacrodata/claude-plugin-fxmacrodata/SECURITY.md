# Security policy

## Reporting a vulnerability

Email info@fxmacrodata.com with the details and steps to reproduce. Please do not open a public issue for a security problem. We aim to acknowledge reports within three working days.

## Scope

This repository contains plugin manifests, a skill and command prompts. It runs no local code: the MCP server is the hosted endpoint `https://mcp.fxmacrodata.com/mcp`, and the plugin only points your client at it.

## Credentials

The plugin ships no credentials. USD data works without a key. If you use an FXMacroData API key, keep it in your client's secret storage or an environment variable, never in a committed file.
