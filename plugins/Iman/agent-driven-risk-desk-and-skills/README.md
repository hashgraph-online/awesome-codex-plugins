# risk-desk plugin

The local Risk Desk plugin: 30 MCP tools, 14 skills, commands and agents for
portfolio risk that an agent can drive from data the caller supplies. It
covers historical and model VaR and Expected Shortfall with backtests,
exposure and leverage, and Greeks and full revaluation of European
options. It also covers risk attribution, limits and pre-trade what-if,
liquidity-adjusted VaR, and explicit, historical and reverse stress. Last,
it covers SA-CCR and exposure profiles, portfolio credit VaR, FRTB capital
pieces, and XVA through a local Open Source Risk Engine project.

The MCP server entry starts `riskdesk-mcp` through PATH. `install.sh` at
the repository root installs it in `.venv/bin` and puts nothing on PATH.
So activate `.venv` in the environment that launches the agent, or point
the client at `.venv/bin/riskdesk-mcp` by absolute path. Without the
runtime the skills remain instructions and cannot compute numbers. Every
computation runs on your machine; nothing is sent anywhere. For a remote
server with no install, use the `risk-desk-hosted` plugin, which serves
every tool except `risk_xva`.

The skills, commands and agents in this folder are the sources: edit them
here. Results are research output, not investment advice, and they are not
a regulatory submission. See DISCLAIMER.md at the repository root, and
LICENSE in this folder (PolyForm Noncommercial 1.0.0).
