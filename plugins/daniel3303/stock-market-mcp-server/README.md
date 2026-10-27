# Equibles — Stock Market & Financial Data MCP Server

130 MCP tools for AI agents like Claude, ChatGPT and Cursor: SEC filings, fundamentals, 13F institutional holdings, insider and congressional trades, earnings call transcripts, options chains, live quotes, IPO filings, short interest, macro data, and your own portfolio. Free hosted tier, or self-host the open-source stack.

[![Discovery repo: MIT](https://img.shields.io/badge/discovery%20repo-MIT-blue.svg)](LICENSE)
[![Tools](https://img.shields.io/badge/tools-130-brightgreen.svg)](#tools)
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

130 tools, grouped by dataset. 120 read market data; the 10 marked ✏️ write to your own portfolios, watchlist or feedback.

### Filings & documents

| Tool | Description |
|---|---|
| SearchDocuments | Hybrid keyword and semantic search across the filing corpus. |
| SearchDocument | Runs search inside one document identified by the UUID returned from ListFilings. |
| ListFilings | Lists stored filings and transcripts newest first (by filing date, then EDGAR acceptance time) and paginated. |
| ReadDocumentLines | Reads a specific range of numbered lines from a document. |
| GetFormDOfferings | Lists a company's recent Regulation D private placements from its SEC Form D notices, newest first. |

### Fundamentals & valuation

| Tool | Description |
|---|---|
| GetFinancialFact | A single XBRL financial concept (revenue, net income, diluted EPS, total assets, operating cash flow, and the like) returned as a time series drawn from SEC Company Facts: one row per fiscal period for flows such as revenue, and one row per as-of date for balances and share counts, so a cover-page share count and the balance-sheet count at the period end both appear. |
| CompareFinancialFact | Compares one financial concept across several companies for the same fiscal period, a peer table with one row per ticker, each showing the latest-restated value; tickers with no data for the period are listed separately. |
| GetFinancialStatement | A full income statement, balance sheet, or cash-flow statement for one fiscal year and period, from SEC Company Facts (XBRL). |
| GetRevenueBreakdown | Revenue disaggregated by business segment, geography, and product/service, built from the dimensional XBRL facts the issuer tags in its own filings. |
| GetCompanyKpis | The company's own key performance indicators, extracted from its written Item-2.02 8-K earnings releases and 10-K/10-Q MD&A. |
| GetNonGaapBridge | The GAAP-to-non-GAAP reconciliation "bridge" for each stated non-GAAP measure, such as Adjusted EBITDA, adjusted EPS or adjusted operating income, extracted from a company's earnings releases and 10-K/10-Q periodic reports: the GAAP starting line, each stated adjustment in order, and the non-GAAP result, with the period, unit and verbatim source quote, verifier-approved and newest filing first. |
| GetGuidance | Forward guidance ranges issued by management, extracted from Item-2.02 8-K earnings releases and earnings-call transcripts (some issuers, e.g. |
| GetValuationMultiples | Trailing-twelve-month EV/Revenue, EV/EBIT and P/E, each shown against a subject-excluded peer median, quartiles, and the actual peer sample for that ratio. |
| GetValuationMultiplesHistory | EV/Revenue, EV/EBIT, EV/EBITDA and P/E recomputed at each past quarter's filing date, one row per quarter, up to ~10 years. |
| GetCustomerConcentration | A company's disclosed customer-concentration risk, statements like "one customer accounted for 26% of revenue." The tool serves both authoritative filing shapes directly. |
| GetGoingConcernStatus | Whether the company's latest examined SEC filing states substantial doubt about its ability to continue as a going concern (with the verbatim disclosure, the source filing, and the history of examined filings showing when doubt appeared, was alleviated, or cleared. |

### Debt profiles

| Tool | Description |
|---|---|
| GetDebtProfile | Returns the company's issuer-reported debt-total history and a current-state summary of each identified note, loan, and revolving credit facility. |
| GetDebtInstrument | Returns one durable instrument from the profile, including its current reported balance and as-of date, paged linked filing-observation history, currently operative verified covenant terms, and governing, amending, refinancing, or retirement documents. |

### Earnings calls & investor relations

| Tool | Description |
|---|---|
| GetEarningsBrief | A verifier-approved qualitative read of a company's most recent earnings calls, newest quarter first. |
| GetEarningsCallToneAndThemes | The AI-scored read of a company's recent earnings calls, newest first. |
| GetEarningsCallThemeHistory | How a company's call themes move quarter over quarter. |
| GetTranscriptPhraseTrend | How often a word or phrase comes up on a company's last earnings calls, oldest call first. |
| GetEarningsCallEvent | The single event record that groups one fiscal quarter's earnings-call artefacts (audio, transcript, slide deck, and the 8-K earnings release) under one entry. |
| GetEarningsCallTranscript | The speaker-labelled transcript of a company's earnings call for a given fiscal quarter. |
| GetEarningsCallQuestions | The analyst questions asked in a call's Q&A, one entry per analyst turn at the microphone with any follow-ups, in the order they were asked. |
| GetInvestorEventSlideMetadata | Metadata and access links for a captured investor-event slide deck. |
| ListInvestorEvents | A company's recent investor events (earnings calls plus the other events it webcasts (conferences, investor/analyst days, shareholder meetings)) newest first. |
| GetInvestorEventTranscript | The speaker-labelled transcript of a specific investor event by its event id. |
| GetInvestorRelationsNews | Recent investor-relations press releases for a stock, scraped straight from the company's own IR website, headline, publish date, a one-line summary when the source provides one, and link, in reverse-chronological order. |
| GetUpcomingInvestorEvents | The forward investor-relations calendar for a stock (earnings webcasts, conference appearances, presentations and shareholder meetings scraped from the company's IR website, scheduled from now onward, soonest first (NVIDIA had none as of this capture, so the example below uses Microsoft). |
| GetShareholderVoteResults | A company's shareholder meeting vote results, read from the Item 5.07 section of its SEC 8-K filings, latest meeting first. |

### Analyst estimates

| Tool | Description |
|---|---|
| GetAnalystEstimates | Reads stored analyst consensus forecasts for one company. |

### Institutional holdings (13F)

| Tool | Description |
|---|---|
| GetTopHolders | Ranks the largest tracked institutional holding rows for a stock from the latest 13F filings. |
| GetInstitutionalOwnershipHistory | Shows how aggregate reported 13F exposure to a stock has trended across recent quarters, the number of filers, total reported quantity, aggregate published position value, and the like-for-like quarter-over-quarter change: only filers with an observed 13F in both quarters count, and each quarter lists the filers and shares it excluded (late or confidential filings, first filings, CIK changes whose books do not match), because a missing filing is not a trade. |
| GetHolderMix | Splits a stock's 13F holders by one dimension, quarter by quarter. |
| GetTopInstitutionalBuyersSellers | Surfaces the institutions that moved the needle most on a stock this quarter, two ranked tables, the biggest absolute share additions (Top Buyers) and the biggest absolute reductions (Top Sellers) versus the prior 13F report date. |
| GetInstitutionPortfolio | Lists a specific institution's largest reported 13F positions by published value, with each row's type, share count, value and percent of the tracked portfolio. |
| GetInstitutionSummary | Returns the header-level portfolio summary for a 13F filer, published tracked portfolio value, position count, top-10 and top-25 concentration, quarter-over-quarter turnover, and the latest/prior report dates with the number of quarters on file. |
| GetInstitutionStyleHistory | How a 13F filer's book behaves, quarter by quarter, measured from its filed common-share positions. |
| GetInstitutionSectorAllocation | Breaks an institution's latest 13F portfolio down by industry/sector, sorted by weight, with the position count, published dollar value, and percent of tracked portfolio for each sector. |
| GetInstitutionQuarterlyActivity | Diffs an institution's 13F against the immediately prior quarter and groups the changes into four buckets (Initiated, Increased, Reduced, and Exited) each sorted by absolute change in value. |
| SearchInstitutions | Searches the tracked 13F filer set by filed-name words or CIK prefix and includes verified brand aliases for current flagship filers. |
| GetMarketWide13FActivity | Returns a market-wide 13F leaderboard for one chosen bucket, ranking stocks across all filers by their aggregate move versus the prior quarter. |
| GetHolderTypeFlows | Market-wide money flows by kind of 13F filer for a closed quarter. |
| GetMostHeldStocks | Ranks stocks by institutional 13F breadth for a quarter, by default the number of filers reporting each name, or by quarter-over-quarter change in filer count (a warming/cooling heat map), or by total published position value. |
| GetSuperInvestors | Returns the curated super-investor directory, a hand-picked roster of well-known value investors and fund managers (Warren Buffett, Bill Ackman, Michael Burry, Seth Klarman and more), each with their 13F filer CIK, latest published tracked portfolio value, position count, quarter-over-quarter change, and report date. |

### ETFs

| Tool | Description |
|---|---|
| SearchEtfs | Search active exchange-traded funds and products by ticker, fund name, or sponsor. |
| GetEtfProfile | Return an ETF-specific profile with exact-ticker settled price and total-return performance, 52-week range, average volume, SEC-reported assets, top-ten concentration, allocation, and ten largest holdings. |
| GetEtfHoldings | Return the ETF's stored portfolio from its latest Form NPORT-P report, ranked by value. |

### Funds & advisers

| Tool | Description |
|---|---|
| SearchFunds | Searches the tracked directory of registered management investment companies and UIT ETFs that file SEC Form NPORT-P by fund-name, registrant, identifier, or ticker words in any order. |
| GetFundProfile | Returns a registered fund's profile and largest holdings from its most recent SEC Form NPORT-P. |
| GetFundNcenReports | Returns operational data for a registered investment company from its SEC Form N-CEN annual reports. |
| GetFundsHoldingStock | Returns the registered funds and ETFs holding a given stock or ETF listing, from SEC Form NPORT-P portfolio reports. |
| GetEuropeanFundHoldings | European investment funds reporting a position in one listing outside the US, written MIC:TICKER, matched by that security's ISIN. |
| CompareInstitutionPortfolios | Returns the 13F portfolio overlap between two institutional managers for their latest common report date, union and shared position counts, Jaccard similarity, a dollar-weighted overlap, and a side-by-side table of stocks with each manager's share count and percent of tracked portfolio. |
| GetInstitutionConsensusHoldings | Returns the consensus / combined portfolio of 2–25 institutional managers for their latest common report date. |
| GetInstitutionCloneBacktest | Backtests how cloning an institutional filer's reported 13F portfolio would have performed against a market benchmark over a trailing window. |
| SearchInvestmentAdvisers | Searches SEC-registered and exempt reporting investment advisers (Form ADV) by firm name. |
| GetInvestmentAdviser | Returns the full Form ADV profile for a single SEC-registered or exempt reporting investment adviser by its Organization CRD number. |

### Insider trading

| Tool | Description |
|---|---|
| GetInsiderTransactions | Returns the most recent insider transactions for a stock, straight from SEC Forms 4 and 5. |
| GetInsiderOwnership | Returns a roster of a company's insiders (directors, officers, and 10% owners) each with their role, total shares held, and the type and date of their most recent transaction, ranked from the largest holder down. |
| GetForm144ProposedSales | Returns recent Form 144 notices for a stock, an affiliate's advance declaration of intent to sell restricted or control shares. |
| GetInsiderSentimentScores | Ranks the entire scored universe by a composite 0-100 insider-sentiment score over a trailing 90-day window, a peer-relative blend of three direction-aware factors (net distinct insiders buying, net shares bought as a percent of shares outstanding, and net insider buy value in dollars), built only from open-market Forms 4/5 purchases and sales. |
| SearchInsiders | Looks up tracked corporate insiders (directors, officers, and 10% owners) by whole name words, never arbitrary substrings. |
| GetEuropeanDirectorTransactions | Director and related-person (PDMR) transactions a European regulator published for one listing outside the US, written MIC:TICKER. |

### Congressional trading

| Tool | Description |
|---|---|
| GetCongressionalTrades | Returns the disclosed congressional trades for one ticker, newest first. |
| GetMemberTrades | Returns one member of Congress's disclosed trades, newest first. |
| GetMemberNetWorth | Returns a member's net-worth history reconstructed from their annual financial-disclosure reports. |
| GetMarketWideCongressionalActivity | Aggregates congressional trading across every member and every ticker over a trailing window, "what did Congress buy (or sell) lately" without needing a ticker or a member name. |
| SearchCongressMembers | Searches the tracked congressional roster by punctuation-independent name words in any order. |

### Short selling

| Tool | Description |
|---|---|
| GetShortVolume | FINRA's daily short-sale volume for one stock. |
| GetShortInterest | FINRA's bi-monthly short-interest report for one stock. |
| GetOffExchangeVolume | Weekly off-exchange trading volume for one stock from FINRA's OTC/ATS Transparency data. |
| GetFailsToDeliver | Returns SEC fails-to-deliver (FTD) records for a stock or ETF, listed oldest to newest. |
| GetShortInterestSnapshot | A market-wide leaderboard at the latest FINRA short-interest settlement date, ranked by days-to-cover (descending) so the most squeeze-prone names surface first. |
| GetLargestShortVolume | The listed securities, ETFs included, with the largest short-sale volume on a single trading day (the latest available by default), ranked by short volume descending, with ticker, short volume, short-exempt volume, total volume, and short percentage. |
| GetShortSqueezeScores | A market-wide leaderboard of the highest composite short-squeeze scores (0–100), ranked peer-relative across primary operating-company stocks with short interest at the latest settlement date. |
| GetEuropeanShortPositions | Net short positions disclosed to European regulators for one listing outside the US, written MIC:TICKER, matched by that security's ISIN or, for issuer-level sources such as Sweden's, the issuer's LEI. |

### Capital, executives & screening

| Tool | Description |
|---|---|
| GetBuybackPrograms | A company's share-repurchase picture (tracked programs (authorized total, remaining, expiry), the latest authorization, and the repurchase history (cash spent, shares, average price) by fiscal year) from XBRL facts plus verified extractions of the filings' narrative. |
| GetAtmPrograms | At-the-market (ATM) equity programs: executed sales/distribution agreements under which a company sells new shares directly into the market. |
| GetExecutiveChanges | Executive and director appointments and departures, extracted from Item-5.02 8-K filings (each with the person, role text exactly as filed, a separate normalized role classification, the nature of the change, its effective date, the verbatim disclosure, and a link to the source 8-K. |
| GetExecutiveCompensation | Named-executive pay from the company's DEF 14A Summary Compensation Table, salary, bonus, stock and option awards, non-equity incentive, other, and the company-reported total, per fiscal year. |
| ScreenStocks | Screen US listings, or European, Chinese and Hong Kong listings with market, by combining range filters across datasets. |
| GetGovernmentContracts | Federal contract awards won by a company, from USAspending, each with the award date, the **recipient** as the government named it, awarding agency, award type, total value, period-of-performance end, award ID, and description. |
| GetTopGovernmentContractors | The companies that have won the most federal contract dollars over a window, ranked by total awarded, with the award count. |
| GetFdaAdvisoryCommitteeMeetings | Scheduled FDA advisory-committee meetings, soonest first, with the date, meeting title, FDA center, type, and a link to the per-meeting FDA page (the only place that names the product and sponsor under review). |

### Prices & technicals

| Tool | Description |
|---|---|
| GetStockPrices | Daily OHLCV bars for one stock, one row per trading day with open, high, low, close and positive share volume, listed oldest to newest. |
| GetLatestClosingPrices | The most recent traded closing price, one-session change, share volume, and trailing 52-week range for up to 25 tickers in one call. |
| GetDividendHistory | Stored declared cash dividends for an exact stock or ETF listing, newest ex-dividend date first. |
| GetLiveQuote | GetLiveQuote checks the live service's current in-memory snapshot first. |
| GetBollingerBands | Bollinger Bands for one stock. |
| GetStochasticOscillator | The stochastic oscillator for one stock. |
| GetAverageTrueRange | Wilder's Average True Range (ATR) for one stock (a volatility measure built from the true range (the greatest of high−low, /high−prev close/ and /low−prev close/) and smoothed recursively over period days) shown alongside each day's close, newest first. |
| GetOnBalanceVolume | On-Balance Volume (OBV) for one stock. |
| GetCorrelatedStocks | The stocks whose daily returns move most (or least) with one stock. |

### Options

| Tool | Description |
|---|---|
| GetOptionExpirations | The listed expiration dates for an underlying, ascending, with the number of active contracts at each. |
| GetOptionChain | The calls-and-puts chain for one expiration: strike, type, last daily price, dated open interest, implied volatility and greeks (delta, gamma, theta, vega). |
| GetOptionContract | A single option contract by its OCC symbol: last daily price and range, dated open interest, implied volatility, greeks, and tier-appropriate bid/ask. |

### Economic, futures & sentiment

| Tool | Description |
|---|---|
| GetEconomicIndicator | The observation history for one FRED economic series, one row per period with its value, plus the series title, units, frequency, and seasonal-adjustment flag. |
| GetLatestEconomicIndicators | The latest reading for every tracked FRED series, grouped by category, as a one-glance macro dashboard. |
| SearchEconomicIndicators | Search the tracked FRED series by exact ID, verified common alias, or title/topic words in any order. |
| GetEconomicCalendar | The economic-release calendar: upcoming release dates by default, and recent ones when startDate is in the past. |
| GetMarketStatus | Whether the US equity market is open right now, the current session, and the next open and close, computed from the exchange's curated holiday and early-close calendar, in Eastern Time. |
| GetMarketHolidayCalendar | The US market's holidays and early-close (1:00 p.m. |
| GetCftcPositioning | The weekly Commitments of Traders (COT) positioning for one futures contract. |
| GetLatestCftcPositioning | The latest COT snapshot across every tracked contract, grouped by category (Agriculture, Energy, Metals, Equity Indices, Interest Rates, Currencies), with open interest and net commercial / non-commercial positioning at a glance. |
| SearchCftcMarkets | Search the tracked CFTC futures-contract set by exact market code, verified standard symbol/common alias, or name words in any order. |
| GetPutCallRatios | The CBOE put/call ratio history for one ratio type (equity by default): call and put volume, total, and the P/C ratio per date. |
| GetVixHistory | The CBOE VIX daily OHLC series (the market's "fear gauge"), available back to 1990. |

### IPOs

| Tool | Description |
|---|---|
| GetIpoFeed | Returns the tracked registrations, newest filing activity first. |
| GetIpoDetails | Returns one registration's full picture by SEC CIK. |

### Stock indexes

| Tool | Description |
|---|---|
| GetIndexComposition | Returns one index's current constituent list, heaviest first, with each company's share of the index and the tracking fund's position in it. |
| GetIndexChanges | Returns the companies that have joined or left an index, newest first. |
| GetIndexForecast | Applies an index's own published entry rules to every company we track. |

### Your portfolio

| Tool | Description |
|---|---|
| GetMyPortfolio | Your positions, priced, with cost basis, unrealized profit and the realized profit from lots you have closed. |
| CreateMyPortfolio ✏️ | Creates a new, empty portfolio. |
| AddPortfolioLot ✏️ | Records one purchase or sale. |
| UpdatePortfolioLot ✏️ | Corrects a lot you already recorded: a mistyped quantity, price, date, note or exchange rate. |
| ClosePortfolioLot ✏️ | Records that you sold, covered, or let a lot expire, at a price and on a date. |
| RemovePortfolioLot ✏️ | Permanently deletes a lot, as if it had never been recorded. |
| WatchInstrument ✏️ | Puts a stock or an option contract on a portfolio's watchlist, without recording any position. |
| UnwatchInstrument ✏️ | Removes an instrument from a portfolio's watchlist. |
| DeleteMyPortfolio ✏️ | Permanently deletes a portfolio and every lot in it, open and closed, including the realized-profit history. |

### Trackers

| Tool | Description |
|---|---|
| ListWebDataFeeds | Lists the caller's trackers with their identifiers, active or paused state, visibility, source access, schedule, next collection, and latest run status. |
| GetWebDataFeed | Reads the latest independently verified successful result and its captured source URLs by default. |

### Supply chains

| Tool | Description |
|---|---|
| GetSupplyChain | A company's supply chain. |
| GetSupplyChainOverlap | Which of a company's suppliers and customers also supply or buy from its listed competitors, from the same 10-K readings as GetSupplyChain. |
| GetOrganization | An organization that no market we cover lists: the U.S. |

### Agent feedback

| Tool | Description |
|---|---|
| ReportProblem ✏️ | Report an Equibles tool call you actually made when it failed, timed out, was unexpectedly empty (ToolFailed), or returned verifiably impossible or contradictory data (ImplausibleResult). |
| SuggestToolImprovement ✏️ | Suggest the smallest actionable contract improvement to an existing Equibles tool you actually called when it worked as documented but lacked a useful operation, filter, parameter or output option. |

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
