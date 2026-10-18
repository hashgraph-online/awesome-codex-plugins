# Security policy

## Reporting a vulnerability

Send the details and steps to reproduce through the [contact form](https://equibles.com/legal/contact) or to support [at] equibles [dot] com. Please do not open a public issue for a security problem.

## Scope

This repository holds plugin manifests and one skill. It runs no local code: the MCP server is the hosted endpoint `https://mcp.equibles.com/mcp`, and the plugin only points your client at it.

## Credentials

The plugin ships no credentials. Clients sign in over OAuth. If you use an API key from Equibles instead, keep it in your client's secret storage or an environment variable, never in a committed file.

## Tools that write

Most tools only read market data. Portfolio, watchlist and feedback tools write to the signed-in user's own Equibles account. No tool places trades or moves money.
