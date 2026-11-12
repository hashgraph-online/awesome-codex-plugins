# Security

This repository contains only manifests, Markdown skills and a script that
writes the manifests. It holds no Rush service code, dependencies or
credentials. The plugin connects to one hosted MCP server,
https://api.phoenix.so/mcp, which signs people in with OAuth 2.1 (dynamic
client registration and PKCE). It never asks for an API key in chat.

Report a vulnerability in the plugin or the service privately to
contact@phoenix.so. Do not open a public issue for it.
