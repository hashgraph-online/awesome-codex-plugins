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

The same repository is a Codex plugin (`.codex-plugin/plugin.json`): it registers the hosted MCP server and the FXMacroData skill. Add it to a Codex marketplace that points at this repository, or configure the same hosted URL through Codex's native MCP settings.

## What's included

- **MCP server**: the hosted FXMacroData server at `https://mcp.fxmacrodata.com/mcp`.
- **Skill**: guides Claude to pick the right FXMacroData tool for macro and FX questions.
- **Commands**:
  - `/fxmacrodata:macro-brief USD` - policy rate, inflation, jobs, growth and the next releases.
  - `/fxmacrodata:pair-brief EURUSD` - rate differential, inflation gap, spot and event risk.

## Access

The public USD catalogue, recent macro history and calendar work without an account, within the service's current anonymous window and release delay. Other currencies, FX rates, COT, commodities and research
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
- "Show me US core CPI within the available public history window, with its units and source."
- "Show the latest available USD policy-rate observations and the next officially scheduled release."

## Support

- Documentation: https://fxmacrodata.com/documentation/mcp-server?utm_source=github&utm_medium=referral&utm_campaign=claude-plugin-fxmacrodata&utm_content=readme
- Email: info@fxmacrodata.com
- Privacy policy: https://fxmacrodata.com/privacy?utm_source=github&utm_medium=referral&utm_campaign=claude-plugin-fxmacrodata&utm_content=readme
- Terms: https://fxmacrodata.com/terms?utm_source=github&utm_medium=referral&utm_campaign=claude-plugin-fxmacrodata&utm_content=readme

## License

MIT


## Research workflows

The plugin includes six native commands and three research skills. The existing
`/fxmacrodata:pair-brief` and `fxmacrodata` skill remain available.

| Command | Result |
|---|---|
| `/fxmacrodata:connection-check` | Check the remote connection and public USD catalogue. |
| `/fxmacrodata:macro-brief USD policy rate` | Sourced recent observations, units and release context. |
| `/fxmacrodata:release-context USD policy_rate` | Officially scheduled events, publication qualifications and revisions. |
| `/fxmacrodata:pair-brief AUD/USD` | Existing pair brief, subject to dataset access. |
| `/fxmacrodata:currency-context AUD USD` | FX reference, policy, curves and positioning evidence where accessible. |
| `/fxmacrodata:macro-research <question>` | Route a research question through available MCP tools. |

For a local session, extract the plugin archive into `fxmacrodata` and run
`claude --plugin-dir ./fxmacrodata`. In Claude chat or Cowork, open
**Customize → Plugins**, upload the plugin ZIP using the custom-plugin flow,
then open the plugin's **Connectors** tab and connect FXMacroData.
Organization policy can limit custom-plugin availability.

The connector is fixed HTTPS and keyless. Public USD catalogue, recent macro
history and release calendar need no account, key or credit card. Anonymous
history and request limits follow the service's current public scope. Protected
datasets and older history may require access; installation does not grant it.
This keyless package does not prompt for or store a subscriber key. The complete
reviewed tool reference and transport limits are in [CONNECTORS.md](CONNECTORS.md).

The additional `macro-evidence` and `research-provenance` skills preserve source
links, original units, observation periods and publication qualifications.
Scheduled times and capture clocks are not observed publication timestamps.
Current history may contain later revisions; it is not automatically a
point-in-time backtest dataset. Unavailable data stays unavailable.

## Data handling

This plugin contains Markdown instructions, static configuration and brand
images. It installs no executable, hook, background watcher or local database.
Research calls send selected currency, indicator, dates and other tool arguments
to the declared FXMacroData MCP connector. The workflows need no personal
documents, customer records or local files. Do not include private material in
research requests. The hosted service's request handling is covered by the
[privacy policy](https://fxmacrodata.com/privacy); Claude's processing is covered
by your Claude terms. Contact [info@fxmacrodata.com](mailto:info@fxmacrodata.com)
for support. [Terms](https://fxmacrodata.com/terms).

The existing MIT license is retained. The FXMacroData name and logo identify
the provider; no trademark rights are granted by the software license.
