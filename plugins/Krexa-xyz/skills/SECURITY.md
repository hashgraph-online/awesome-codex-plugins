# Security Policy

## Reporting a vulnerability

Email **tejas@krexa.xyz** with a description of the issue, the steps to reproduce it, and its impact. Please do not open a public GitHub issue for security problems.

This covers the skill files in this repository and the hosted Krexa MCP server they connect to (`https://www.krexa.xyz/mcp`).

## Scope notes

- The Krexa agent key (`kxm_…`) can research, backtest, paper-trade, pause agents and request deploys. It cannot withdraw, transfer or fund money, resume an agent or raise a limit. A way around any of those limits is in scope.
- If you find a leaked key, report it here; the owner can revoke it at https://krexa.xyz/mcp/link.
