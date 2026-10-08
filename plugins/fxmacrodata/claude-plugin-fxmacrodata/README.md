# FXMacroData plugin for Claude

[FXMacroData](https://fxmacrodata.com/?utm_source=github&utm_medium=referral&utm_campaign=claude-plugin-fxmacrodata&utm_content=readme) provides official-source FX, macroeconomic and central-bank data inside Claude Code: release calendars,
indicator histories, policy rates, FX spot rates, COT positioning and commodities across 22
currencies.

## Install

```
/plugin marketplace add fxmacrodata/claude-plugin-fxmacrodata
/plugin install fxmacrodata@fxmacrodata
```

## Codex

The same repository is a Codex plugin (`.codex-plugin/plugin.json`): it registers the hosted MCP server and the FXMacroData skill. Add it to a Codex marketplace that points at this repository, or copy the `mcp_servers` entry from `.mcp.json` into your Codex config.

## What's included

- **MCP server**: the hosted FXMacroData server at `https://mcp.fxmacrodata.com/mcp`.
- **Skill**: guides Claude to pick the right FXMacroData tool for macro and FX questions.
- **Commands**:
  - `/fxmacrodata:macro-brief USD` - policy rate, inflation, jobs, growth and the next releases.
  - `/fxmacrodata:pair-brief EURUSD` - rate differential, inflation gap, spot and event risk.

## Access

USD data works without an account. Other currencies, FX rates, COT, commodities and research
tools need an FXMacroData subscription. Run `/mcp` in Claude Code and choose **fxmacrodata** to
sign in.

Pricing: https://fxmacrodata.com/subscribe?utm_source=github&utm_medium=referral&utm_campaign=claude-plugin-fxmacrodata&utm_content=readme

## Network and credentials

The plugin ships no scripts or hooks. Its only network endpoint is the hosted MCP server at
`https://mcp.fxmacrodata.com/mcp`, declared in `.mcp.json`; every tool on it is read-only.
No credential is needed for USD data. For a subscription, sign in through the client's MCP OAuth
flow, or send an API key as an `Authorization: Bearer` header. The plugin never reads files,
environment variables or local tokens.

## Example prompts

- "What US data is due this week?"
- "Show me the last 12 months of US core CPI."
- "How has the Fed funds rate moved this year?"

## Support

- Documentation: https://fxmacrodata.com/documentation/mcp-server?utm_source=github&utm_medium=referral&utm_campaign=claude-plugin-fxmacrodata&utm_content=readme
- Email: info@fxmacrodata.com
- Privacy policy: https://fxmacrodata.com/privacy?utm_source=github&utm_medium=referral&utm_campaign=claude-plugin-fxmacrodata&utm_content=readme
- Terms: https://fxmacrodata.com/terms?utm_source=github&utm_medium=referral&utm_campaign=claude-plugin-fxmacrodata&utm_content=readme

## License

MIT
