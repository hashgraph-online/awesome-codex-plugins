# Security Policy

## Reporting a vulnerability

Please report security vulnerabilities in lemlist, including the hosted lemlist MCP server (`https://app.lemlist.com/mcp`) and this plugin, through our HackerOne program:

https://hackerone.com/lemlist

Do not open a public GitHub issue for a security report.

Our disclosure policy and contact details are also published in our security.txt file: https://www.lemlist.com/.well-known/security.txt

## Scope of this repository

This repository only contains plugin manifests, configuration and agent skills. It holds no secrets and runs no code: the plugin points your AI client to the hosted lemlist MCP server, and you sign in with OAuth 2.1 (or an API key you provide in your own client configuration).
