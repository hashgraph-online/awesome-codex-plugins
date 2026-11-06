<img src="assets/icon.png" width="88" height="88" alt="FXMacroData" />

# FXMacroData

Official economic data, release calendars and actual release times, with source-linked charts, release replays and FX backtests.

Research macroeconomic releases in Claude using data from central banks,
statistical agencies and other official publishers. Keep the observation period,
unit, source and revision context beside each result.

## What you can do

- **Prepare a macro brief.** Review inflation, interest rates, employment and growth with source references.
- **Plan around releases.** Find confirmed economic release schedules in your timezone.
- **Compare currency drivers.** Bring policy rates, FX reference data, positioning and commodities into a research question where your access permits.
- **See when data really came out.** Actual publication times are kept separate from the schedule and from later revisions.
- **Test an idea.** Replay how a pair moved after past releases, or run a spot FX backtest on rate-differential or momentum signals with costs included.
- **Follow events.** Review a sourced history of maritime, sanctions and conflict-zone events.
- **Keep your research.** Signed-in subscribers can save research studies and simulated paper accounts.
- **Explore the evidence.** Use interactive charts in compatible Claude surfaces, with structured tables when a chart cannot render.

The connection discovers the server's full tool set. It covers catalogue and
coverage metadata; macro histories and revisions; current and historical release
calendars; release predictions; official news; FX rates, curves and
differentials; market sessions; COT positioning; commodities; official
datasets; organisation profiles; geopolitical event history; seasonality;
release replays, backtests and trade setups; and saved research.
Protected tools follow your account's entitlements. See the complete
[tool and workflow reference](CONNECTORS.md) for supported operations and
transport limitations.

## Add to Claude

Open **Customize → Plugins**, search for **FXMacroData**, and select **Add**.
Connect the FXMacroData connector when prompted.

Start with:

- "What US economic releases are scheduled this week? Show them in Australia/Sydney time."
- "What was the latest US CPI reading, and when was it actually published?"
- "Build a US macro briefing: rates, inflation, jobs and the releases due next."

The public USD baseline works without an FXMacroData account or API key, within
the current public history window and release delay. Other currencies, older
history and protected datasets require appropriate access. Connect your own
FXMacroData account through the host's OAuth flow when needed.

## Claude Code

```text
/plugin marketplace add fxmacrodata/claude-plugin-fxmacrodata
/plugin install fxmacrodata@fxmacrodata
```

| Command | Use |
| --- | --- |
| `/fxmacrodata:connection-check` | Check the connection and public catalogue. |
| `/fxmacrodata:macro-brief USD` | Build a sourced macro brief. |
| `/fxmacrodata:release-context USD policy_rate` | Review schedules, publication evidence and revisions. |
| `/fxmacrodata:pair-brief AUD/USD` | Research a currency pair where access permits. |
| `/fxmacrodata:currency-context AUD USD` | Compare currency drivers and reference data. |
| `/fxmacrodata:macro-research <question>` | Route a research question to the available tools. |

## Data and access

The plugin connects to the hosted MCP server at
`https://mcp.fxmacrodata.com/mcp`. Data tools are read-only. Research tools save only your own research studies and simulated paper accounts. No tool places live orders, moves money or changes account settings.
Account credentials belong in the host's connection flow, never in a prompt.

Returned observations retain their units, periods and source references.
Current histories can contain later revisions. Scheduled release times are
distinct from observed publication times. Missing data is reported as unavailable.
FX reference rates are reference data rather than executable trading quotes.

## Documentation and support

- [Product overview](https://fxmacrodata.com/features?utm_source=github&utm_medium=referral&utm_campaign=claude_plugin&utm_content=readme_overview)
- [MCP documentation](https://fxmacrodata.com/documentation/mcp-server?utm_source=github&utm_medium=referral&utm_campaign=claude_plugin&utm_content=readme_documentation)
- [Support](https://fxmacrodata.com/support?utm_source=github&utm_medium=referral&utm_campaign=claude_plugin&utm_content=readme_support)
- [Plans and access](https://fxmacrodata.com/subscribe?utm_source=github&utm_medium=referral&utm_campaign=claude_plugin&utm_content=readme_plans)
- [Privacy policy](https://fxmacrodata.com/privacy?utm_source=github&utm_medium=referral&utm_campaign=claude_plugin&utm_content=readme_privacy)
- [Terms of service](https://fxmacrodata.com/terms?utm_source=github&utm_medium=referral&utm_campaign=claude_plugin&utm_content=readme_terms)

This repository also includes the existing Codex-compatible plugin manifest.

## License

MIT. See [LICENSE](LICENSE).
