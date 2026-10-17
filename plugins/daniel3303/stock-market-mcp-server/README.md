# Equibles — Stock Market & Financial Data MCP Server

111 MCP tools for AI agents like Claude, ChatGPT and Cursor: SEC filings, fundamentals, 13F institutional holdings, insider and congressional trades, earnings call transcripts, options chains, live quotes, IPO filings, short interest, macro data, and your own portfolio. Free hosted tier, or self-host the open-source stack.

[![Discovery repo: MIT](https://img.shields.io/badge/discovery%20repo-MIT-blue.svg)](LICENSE)
[![Tools](https://img.shields.io/badge/tools-111-brightgreen.svg)](#tools)
[![Free tier](https://img.shields.io/badge/free%20tier-100%20req%2Fday-orange.svg)](#pricing--rate-limits)
[![equibles.com](https://img.shields.io/badge/equibles.com-visit-6366f1.svg)](https://equibles.com)

## What is this?

The Model Context Protocol (MCP) lets AI assistants call external data tools instead of guessing from training data. Equibles exposes US stock market and financial data as an MCP server: use it hosted at `https://mcp.equibles.com/mcp` (free API key, or OAuth with no key at all), or run it yourself from the open-source stack. Everything is parsed from the primary sources (SEC EDGAR, FINRA, FRED, CFTC, CBOE, USAspending, company IR sites), not from third-party estimates.

## Licenses

This discovery repository's documentation and metadata use the [MIT license](LICENSE). The self-hosted server implementation is in [daniel3303/Equibles](https://github.com/daniel3303/Equibles) under [AGPL-3.0](https://github.com/daniel3303/Equibles/blob/main/LICENSE). The hosted service is governed by the [Equibles Terms of Service](https://equibles.com/legal/terms).

## Quickstart (hosted, 30 seconds)

1. Create a free account at [equibles.com](https://equibles.com) — no credit card required.
2. Create an API key at [`https://equibles.com/dashboard/apikeys`](https://equibles.com/dashboard/apikeys). It starts with `eq_` and is shown once, so copy it right away.
3. Connect your client with the URL `https://mcp.equibles.com/mcp` (see below).

ChatGPT and Claude (web and Desktop) can skip the key entirely and sign in over OAuth.

## Connect your AI client

### Plugin packages

This repository includes an [Agent Plugins](https://agent-plugins.org/specification) package for compatible clients such as Cursor (`plugin.json` and `mcp.json`), a Grok Build package (`.grok-plugin/plugin.json` and `.mcp.json`), a Codex plugin and marketplace (`.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json` and `.mcp.json`), a Claude Code plugin and marketplace (`.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`), and a Gemini CLI extension (`gemini-extension.json`). The `skills/` folder holds one research skill that any package loader which discovers skills picks up, including the Codex and Claude Code plugins and Agent Plugins clients. These files configure the hosted MCP endpoint; they do not contain the server implementation. Marketplace availability is separate from these installable packages.

The packages use client-managed OAuth through `https://mcp.equibles.com/mcp?auth=oauth`, except the Claude Code plugin, which uses `https://mcp.equibles.com/mcp` to match the Claude directory connector. For the other packages, the query parameter requests authentication during discovery, so the client prompts for sign-in before attempting a data query. Sign in to your Equibles account when prompted. In Gemini CLI, use `/mcp auth equibles` if needed. If your client does not support OAuth, use the API-key configuration below instead.

Install the Gemini CLI extension from this repository:

```bash
gemini extensions install https://github.com/daniel3303/stock-market-mcp-server
```

For a local checkout of this package, use `gemini extensions link /absolute/path/to/stock-market-mcp-server`. After reviewing the package, Grok Build users can run `grok plugin install /absolute/path/to/stock-market-mcp-server --trust`, then `grok plugin enable equibles` and start a new session.

Install the Codex plugin from this repository's marketplace:

```bash
codex plugin marketplace add daniel3303/stock-market-mcp-server
codex plugin add equibles@equibles
```

The only MCP endpoints configured by these packages are `https://mcp.equibles.com/mcp?auth=oauth` and, in the Claude Code plugin, `https://mcp.equibles.com/mcp`. OAuth discovery and sign-in use `https://equibles.com/`. Queries and explicitly requested portfolio changes are sent to Equibles under the signed-in account. Keep the client's normal tool confirmations enabled: portfolio tools can create, change, or delete your saved holdings, and feedback tools send reports to Equibles. The packages contain no executable scripts, lifecycle hooks, embedded credentials, or telemetry code. Report security problems as described in [SECURITY.md](SECURITY.md). Hosted usage is subject to account entitlements and the [service terms](https://equibles.com/legal/terms).

### Cline

Create an Equibles account and an API key using the Quickstart above. In Cline, open **MCP Servers → Configure MCP Servers** and merge this entry into the `mcpServers` object, replacing `eq_your_api_key` with your own key:

```json
{
  "mcpServers": {
    "equibles": {
      "type": "streamableHttp",
      "url": "https://mcp.equibles.com/mcp",
      "headers": { "Authorization": "Bearer eq_your_api_key" },
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

Keep the key in your local client configuration and never commit it. Save the configuration, confirm Equibles is connected, and ask Cline to call `GetMarketStatus` as a read-only connection check. If authentication fails, check the key or sign in through the client's OAuth flow. See the [Cline MCP documentation](https://docs.cline.bot/mcp/mcp-overview) for client setup.

### Claude Desktop / Claude web (claude.ai)

Settings → Connectors → Add custom connector → URL `https://mcp.equibles.com/mcp` → sign in over OAuth (no key needed).

Key alternative: use the URL `https://mcp.equibles.com/mcp?api_key=eq_your_api_key`.

### Claude Code

```bash
claude mcp add --transport http equibles https://mcp.equibles.com/mcp
```

Then run `/mcp` and choose **Authenticate** to sign in over OAuth.

Or install the plugin, which adds the same server plus the research skill:

```text
/plugin install equibles --marketplace daniel3303/stock-market-mcp-server
```

On Claude Code versions before 2.1.275, run `/plugin marketplace add daniel3303/stock-market-mcp-server` first, then `/plugin install equibles@equibles`.

The plugin uses the same server URL as the Equibles connector in Claude's directory; run `/mcp` and choose **Authenticate** to sign in.

Key alternative:

```bash
claude mcp add-json equibles '{"type":"http","url":"https://mcp.equibles.com/mcp","headers":{"Authorization":"Bearer eq_your_api_key"}}' --scope user
```

### ChatGPT

Add a developer-mode connector with URL `https://mcp.equibles.com/mcp` and complete the OAuth sign-in (or use the `?api_key=eq_your_api_key` URL).

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{ "mcpServers": { "equibles": { "url": "https://mcp.equibles.com/mcp", "headers": { "Authorization": "Bearer eq_your_api_key" } } } }
```

### VS Code (Copilot)

```bash
code --add-mcp '{"name":"equibles","type":"http","url":"https://mcp.equibles.com/mcp"}'
```

Or add a `.vscode/mcp.json` with a `"servers"` object using the same URL and `Authorization` header shape:

```json
{ "servers": { "equibles": { "type": "http", "url": "https://mcp.equibles.com/mcp", "headers": { "Authorization": "Bearer eq_your_api_key" } } } }
```

### Any MCP client

Use the HTTP transport with URL `https://mcp.equibles.com/mcp`, authenticating with an `Authorization: Bearer eq_...` header or a `?api_key=eq_...` query parameter.

After connecting, see the full per-client guides at [https://equibles.com/docs/mcp](https://equibles.com/docs/mcp).

## Example prompts

- "Which hedge funds bought the most NVIDIA last quarter?"
- "Summarize the risk factors in Tesla's latest 10-K."
- "Show recent insider selling at Microsoft, and has any member of Congress traded it this year?"
- "What did NVIDIA guide for next quarter, and what KPIs did it report?"
- "Which stocks have the highest short-squeeze scores today?"
- "Screen for profitable software stocks under a 20 P/E."
- "What's the latest CPI and unemployment rate?"

## Tools

111 tools, grouped by dataset.

### SEC filings search & full-text RAG

| Tool | Description |
|---|---|
| SearchDocuments | Hybrid keyword + semantic search across all companies' SEC filings. |
| SearchCompanyDocuments | Hybrid search of one company's filings by ticker. |
| SearchDocument | Hybrid search within a single filing. |
| ListCompanyDocuments | Browse available SEC filings and transcripts for a company. |
| SearchDocumentKeyword | Keyword search within one filing. |
| ReadDocumentLines | Read a line range from a filing. |

### Financial statements & fundamentals (XBRL)

| Tool | Description |
|---|---|
| GetFinancialStatement | Income statement, balance sheet, or cash-flow statement for a fiscal period (XBRL). |
| GetFinancialFact | One financial concept over time. |
| CompareFinancialFact | Compare a concept across companies. |
| GetRevenueBreakdown | Revenue by segment, geography, and product (dimensional XBRL). |

### 13F institutional holdings & hedge fund portfolios

| Tool | Description |
|---|---|
| GetFundCloneBacktest | Backtest cloning an institutional filer's 13F portfolio vs a market benchmark. |
| GetTopHolders | Top institutional holders of a stock from SEC 13F-HR filings, ranked by shares held. |
| GetOwnershipHistory | Historical trend of institutional ownership across quarters. |
| GetInstitutionPortfolio | A specific institution's portfolio from its 13F-HR. |
| SearchInstitutions | Search institutional investors by name or SEC CIK. |
| GetTopBuyersSellers | Institutions with the biggest share additions/reductions on a stock this quarter. |
| GetMarketWide13FActivity | Market-wide 13F leaderboards (top buys/sells/new/sold-out) for a quarter. |
| GetMostHeldStocks | Stocks ranked by institutional 13F breadth. |
| GetInstitutionSummary | Portfolio summary for a 13F filer (value, concentration, turnover). |
| GetInstitutionSectorAllocation | An institution's 13F allocation by sector. |
| GetInstitutionQuarterlyActivity | Initiated / increased / reduced / exited activity vs the prior quarter. |
| GetFundOverlap | 13F portfolio overlap between two institutions. |
| GetConsensusHoldings | Consensus portfolio of 2–25 institutions. |

### Insider trading (Form 3/4/5 & Form 144)

| Tool | Description |
|---|---|
| GetInsiderTransactions | Recent insider transactions from SEC Form 3/4/5. |
| GetInsiderOwnership | Insider ownership summary, ranked by shares held. |
| GetProposedSales | Proposed insider sales from SEC Form 144. |
| SearchInsiders | Search corporate insiders by name. |
| GetInsiderSentimentScores | Stocks with the highest composite 0–100 insider-sentiment score. |

### Congressional stock trading

| Tool | Description |
|---|---|
| GetCongressionalTrades | Congressional trades for a ticker. |
| GetMemberTrades | A member's disclosed trades. |
| GetMemberNetWorth | A member's net worth history from disclosures. |
| SearchCongressMembers | Search members by name. |
| GetMarketWideCongressionalActivity | Stocks Congress traded most over a trailing window. |

### Earnings calls: transcripts, briefs & AI insights

| Tool | Description |
|---|---|
| GetEarningsCallEvent | The earnings-call event for a fiscal quarter. |
| ListInvestorEvents | Recent investor events. |
| GetInvestorEventSpeakers | Speaker-labelled transcript by event id. |
| GetEarningsCallSpeakers | Speaker-labelled earnings-call transcript by fiscal quarter. |
| GetEarningsBrief | AI earnings brief (TL;DR, bull/bear, pull-quotes). |
| GetCallInsights | AI-scored insights (tone, hedging, themes). |
| GetInvestorEventSlides | Captured investor-event slide deck: title, source, page count, and links to the PDF or slide images. |

### Earnings guidance, KPIs & non-GAAP bridges

| Tool | Description |
|---|---|
| GetGuidance | Earnings guidance from 8-Ks and call transcripts. |
| GetCompanyKpis | Company-specific KPIs (subscribers, ARR, adj. EBITDA…). |
| GetNonGaapBridge | Non-GAAP-to-GAAP reconciliations. |

### Stock prices & technical indicators

| Tool | Description |
|---|---|
| GetStockPrices | Daily OHLCV history (split-adjusted). |
| GetLatestPrices | Latest close, change, and volume. |
| GetStochasticOscillator | Stochastic oscillator series. |
| GetAverageTrueRange | Average true range (ATR) series. |
| GetOnBalanceVolume | On-balance-volume (OBV) series. |
| GetBollingerBands | Bollinger Bands series. |

### Short interest, short volume & dark pools (FINRA)

| Tool | Description |
|---|---|
| GetShortVolume | Daily short-sale volume (FINRA). |
| GetShortInterest | Bi-monthly short interest. |
| GetShortInterestSnapshot | Market-wide latest settlement snapshot. |
| GetLargestShortVolume | Largest daily short volume. |
| GetShortSqueezeScores | Highest composite 0–100 short-squeeze scores. |
| GetOffExchangeVolume | Weekly dark-pool / OTC volume (FINRA ATS). |

### Live quotes & options chains

| Tool | Description |
|---|---|
| GetLiveQuote | Latest intraday price for one or more US listings. |
| GetOptionExpirations | Available option expiration dates for a stock, with the contract count at each. |
| GetOptionChain | Calls and puts for one expiration: strike, bid/ask, volume, open interest, IV, and greeks. |
| GetOptionContract | Full snapshot for one option contract by its OCC symbol. |

### IPO pipeline (S-1 / F-1)

| Tool | Description |
|---|---|
| GetIpoFeed | The US S-1/F-1 registration pipeline, newest filing activity first. |
| GetIpoDetails | One registration in full: status, offer terms, underwriters, risk factors, and pre-IPO financials. |

### Valuation multiples & stock screener

| Tool | Description |
|---|---|
| GetValuationMultiples | EV/Revenue, EV/EBIT, P/E with industry quartiles. |
| GetValuationMultiplesHistory | The same valuation multiples over time. |
| ScreenStocks | Screen the stock universe with range filters across datasets. |
| GetCorrelatedStocks | Most and least correlated stocks by daily returns. |

### Economic data (FRED) & macro calendar

| Tool | Description |
|---|---|
| GetEconomicIndicator | Time series for a FRED indicator (~40 curated series). |
| GetLatestEconomicData | Latest values across categories. |
| SearchEconomicIndicators | Search the curated series. |
| GetEconomicCalendar | Scheduled and recent US macro releases. |

### Futures positioning (CFTC COT)

| Tool | Description |
|---|---|
| GetCftcPositioning | COT positioning for a futures contract. |
| GetLatestCftcData | Latest COT snapshot across ~35 tracked contracts. |
| SearchCftcMarkets | Search tracked CFTC contracts. |

### Volatility & options sentiment (CBOE)

| Tool | Description |
|---|---|
| GetPutCallRatios | CBOE put/call ratios (Total / Equity / Index / Vix / Etp). |
| GetVixHistory | VIX daily OHLC history. |

### Funds, ETFs & investment advisers

| Tool | Description |
|---|---|
| SearchInvestmentAdvisers | Search SEC-registered investment advisers (Form ADV). |
| GetInvestmentAdviser | Full Form ADV profile by CRD number. |
| GetFundOperations | Fund operational data from Form N-CEN. |
| GetFundHoldings | Fund/ETF portfolio holdings from latest NPORT-P. |
| GetFundsHoldingStock | Funds/ETFs holding a given stock. |
| GetExemptOfferings | Private placements from Form D. |
| GetFailsToDeliver | FTD data from the SEC's twice-monthly files. |
| SearchFunds | Search registered funds/ETFs. |
| GetFundProfile | Fund profile and largest holdings from NPORT-P. |

### Index composition & forecasts

| Tool | Description |
|---|---|
| GetIndexComposition | Current constituent list for an index, heaviest first, with each company's weight. |
| GetIndexChanges | Companies that have joined or left an index, newest first, with the dates each change is bounded by. |
| GetIndexForecast | Applies an index's published entry rules to every company we track, rule by rule. |

### Corporate events & governance

| Tool | Description |
|---|---|
| GetExecutiveChanges | Executive/director changes from 8-K Item 5.02. |
| GetExecutiveCompensation | Compensation from DEF 14A. |
| GetBuybackPrograms | Share-repurchase programs and history. |
| GetAtmPrograms | At-the-market equity offering programs. |
| GetGoingConcernStatus | Going-concern doubt status from the latest filing. |
| GetCustomerConcentration | Customer-concentration risk disclosures. |
| GetInvestorRelationsNews | Recent IR press releases. |
| GetInvestorRelationsEvents | Upcoming IR events / webcasts. |
| GetSuperInvestors | Curated superinvestor directory with 13F CIKs. |
| GetGovernmentContracts | Federal contract awards (USAspending.gov) won by a company. |
| GetTopGovernmentContractors | Companies ranked by federal contract dollars. |
| GetFdaCatalysts | Scheduled FDA advisory-committee meetings. |
| GetMarketStatus | US market session status. |
| GetMarketCalendar | Market holidays and half days. |

### Your own portfolio (the only tools that write)

Scoped to the account behind the API key. The caller's own holdings, never anyone else's.

| Tool | Description |
|---|---|
| GetMyPortfolio | The user's saved holdings, priced, with cost basis and realized/unrealized profit. |
| CreateMyPortfolio | Create a new, empty portfolio. |
| DeleteMyPortfolio | Permanently delete a portfolio and every lot in it. |
| AddPortfolioLot | Record one purchase or sale as a lot, for a stock or an option contract. |
| UpdatePortfolioLot | Correct a lot's quantity, price, trade date, or note. |
| ClosePortfolioLot | Record a sale, cover, or expiry of all or part of a lot, keeping its realized profit. |
| RemovePortfolioLot | Permanently delete a lot entered by mistake. |
| WatchInstrument | Put a stock or option contract on a watchlist, with no position recorded. |
| UnwatchInstrument | Remove a stock or option contract from a watchlist. |

### Agent feedback

| Tool | Description |
|---|---|
| ReportProblem | Report wrong, missing, or broken data straight from the tool call. |
| SuggestToolImprovement | Suggest a change to a tool's behaviour, arguments, or output. |

## Pricing & rate limits

| Plan | Daily requests | Price | Card required |
|---|---|---|---|
| Free | 100 requests/day | $0 | No |
| Plus | 10,000 requests/day | See [pricing](https://equibles.com/pricing) | Yes |
| Pro | 100,000 requests/day | See [pricing](https://equibles.com/pricing) | Yes |

- One shared daily counter across both the MCP server and the REST API; it resets at 00:00 UTC.
- Rate-limit headers are exposed on responses: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, and `Retry-After` (on 429).
- When you go over the limit, the MCP server answers in-band with a normal tool result explaining the limit rather than returning an opaque error, so your agent can read and react to it.

Details at [https://equibles.com/pricing](https://equibles.com/pricing).

## Self-host with Docker (open source)

The full stack is open source at [https://github.com/daniel3303/Equibles](https://github.com/daniel3303/Equibles).

```bash
git clone https://github.com/daniel3303/Equibles
cd Equibles
docker compose up
```

The MCP server comes up at `http://localhost:8081/mcp`. No API key is required by default; set the `MCP_API_KEY` environment variable to require an `Authorization: Bearer <key>` header. When self-hosting, the Bearer header is the only auth method (no query parameter, no OAuth).

The self-hosted server exposes the 64-tool open-source subset: 13F holdings, insider trading, SEC filings and fundamentals, funds/ETFs/advisers, FRED, CFTC, CBOE, congressional trades, short data, stock prices, government contracts, and the FDA calendar. The hosted server adds 44 more on top: earnings calls, guidance, KPIs, the screener, valuation multiples, buybacks, executive data, live quotes, options chains, IPO filings, and your own portfolio.

Note: the self-hosted stack runs its own scrapers against the primary sources, so the databases start empty and fill up over time after you start it.

## REST API

Everything is also available as a conventional REST API at `https://api.equibles.com/v1`, sharing the same API key and daily limit as the MCP server. Docs at [https://equibles.com/docs](https://equibles.com/docs).

## Data sources & methodology

Every dataset is parsed from the primary source, never from third-party estimates:

- **SEC EDGAR** — filings, XBRL fundamentals, 13F holdings, Forms 3/4/5/144, NPORT, ADV, N-CEN, Form D
- **FINRA** — short volume, short interest, dark-pool / off-exchange volume
- **FRED** — economic indicators and macro series
- **CFTC** — Commitments of Traders futures positioning
- **CBOE** — put/call ratios and VIX
- **USAspending.gov** — federal government contract awards
- **Company IR sites** — investor-relations news and events
- **Congressional disclosures** — member trades and net worth

Methodology details at [https://equibles.com/docs/methodology](https://equibles.com/docs/methodology).

## Links

- Website: [https://equibles.com](https://equibles.com)
- Docs: [https://equibles.com/docs](https://equibles.com/docs)
- Create an API key: [https://equibles.com/dashboard/apikeys](https://equibles.com/dashboard/apikeys)
- Open-source stack: [https://github.com/daniel3303/Equibles](https://github.com/daniel3303/Equibles)
- Pricing: [https://equibles.com/pricing](https://equibles.com/pricing)
