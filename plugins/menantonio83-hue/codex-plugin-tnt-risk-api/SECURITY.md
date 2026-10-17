# Security

The `tnt-house-risk-data-api` MCP server is **read-only**. Its tools
(`check_token_risk`, `check_token_risk_batch`, `get_token_risk_history`)
query on-chain and market data about a Solana token and return a JSON risk
report. The server:

- Never requests, stores, or has access to a wallet's private key or seed
  phrase.
- Never signs or submits a transaction.
- Never requires wallet connection to use `check_token_risk`.

The only credential involved is an optional `Authorization: Bearer <key>`
API key, used solely to raise the daily rate limit and unlock the batch and
history tools. It carries no funds and grants no on-chain permissions.

## Reporting a vulnerability

Open an issue at https://github.com/menantonio83-hue/tnt-house/issues or
reach out via X: [@RiskDataApiSol](https://x.com/RiskDataApiSol).
