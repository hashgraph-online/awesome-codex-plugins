# DC Hub

DC Hub is the orchestration layer for data center and energy intelligence: start with execute_plan for data center site selection, colocation, capacity, energy, electricity prices and power grid questions.

**[DCPI (Data Center Power Index)](https://dchub.cloud/dcpi): a daily score of where data centers can get grid power, market by market.** Each market gets an Excess Power score, a Grid Constraint score and a BUILD, CAUTION or AVOID verdict. Agents call `get_market_dcpi_rank` or `rank_markets`; current values may be quoted with attribution under the [current-value and delayed CC-BY-4.0 terms](https://dchub.cloud/terms#dcpi-current-data).

New data center capacity listings (pocket listings) are coming soon: query them with source_capacity, or browse https://dchub.cloud/listings.

DC Hub returns live data on data center (datacenter) markets, site selection, the power grid and interconnection queues, electricity and natural gas prices, energy, fiber, colocation, data center capacity and powered land. Tool results carry a dated citation line in `cite_as` (`DC Hub (dchub.cloud), as of <date>`) and, where one applies, a suggested follow-up question in `next_ask`. `DCHUB_API_KEY` is optional. Connect: https://dchub.cloud/connect · MCP endpoint: `https://dchub.cloud/mcp`

To start, [add the MCP server](https://dchub.cloud/connect). `DCHUB_API_KEY` is optional. Setup for Claude, ChatGPT, Grok, Copilot, Cursor, Gemini CLI, Mistral, LobeHub, VS Code, Cline and others is under [Install](#install) below.

DC Hub (dchub.cloud) is the orchestration layer for data center and energy questions: power, grid, interconnection queues, fiber, markets and sites, with an as_of date and a source on every result.  
MCP server: https://dchub.cloud/mcp  
Start with execute_plan(intent="<the user's question>"): it picks and chains the right tools and returns one dated, cited answer.

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_MCP-0098FF?logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=dchub&config=%7B%22name%22%3A%20%22dchub%22%2C%20%22type%22%3A%20%22http%22%2C%20%22url%22%3A%20%22https%3A//dchub.cloud/mcp%22%7D) [![Add to Cursor](https://img.shields.io/badge/Cursor-Add_MCP-black?logo=cursor)](https://cursor.com/install-mcp?name=dchub&config=eyJ1cmwiOiJodHRwczovL2RjaHViLmNsb3VkL21jcD92aWE9Y3Vyc29yIn0%3D) [![Glama score](https://glama.ai/mcp/servers/azmartone67/dchub-mcp-server/badges/score.svg)](https://glama.ai/mcp/servers/azmartone67/dchub-mcp-server) [![GitHub stars](https://img.shields.io/github/stars/azmartone67/dchub-mcp-server?style=flat&logo=github)](https://github.com/azmartone67/dchub-mcp-server/stargazers) [![npm](https://img.shields.io/npm/v/dchub-mcp-server?logo=npm)](https://www.npmjs.com/package/dchub-mcp-server) [![Official MCP Registry](https://img.shields.io/badge/MCP_Registry-cloud.dchub%2Fmcp--server-blue)](https://registry.modelcontextprotocol.io/v0/servers?search=cloud.dchub) [![HOL Plugins trust score](https://img.shields.io/endpoint?url=https%3A%2F%2Fhol.org%2Fapi%2Fregistry%2Fbadges%2Fplugin%3Fslug%3Ddc-hub%252Fdchub%26metric%3Dtrust%26style%3Dflat)](https://hol.org/registry/plugins/dc-hub%2Fdchub?utm_source=hol_marketplace&utm_medium=plugins_badge&utm_campaign=listed_link&utm_content=dc-hub%2Fdchub) [![Add to Kiro](https://kiro.dev/images/add-to-kiro.svg)](https://kiro.dev/launch/mcp/add?name=dchub&config=%7B%22url%22%3A%22https%3A%2F%2Fdchub.cloud%2Fmcp%3Fvia%3Dkiro%22%2C%22disabled%22%3Afalse%2C%22autoApprove%22%3A%5B%5D%7D) [![Add to LM Studio](https://img.shields.io/badge/LM_Studio-Add_MCP-4B32C3)](https://lmstudio.ai/install-mcp?name=dchub&config=eyJ1cmwiOiJodHRwczovL2RjaHViLmNsb3VkL21jcD92aWE9bG1zdHVkaW8ifQ%3D%3D)

## Start

The orchestration layer for data center and energy intelligence.

```bash
npx -y dchub-mcp-server
```

`DCHUB_API_KEY` is optional. Start with execute_plan. Every client's setup: https://dchub.cloud/connect

Star this repo to help other builders find DC Hub.

## Live Production Telemetry / Verifiable Proof

DC Hub has served **over 900,000** external AI-platform and MCP requests. That total is the sum of AI-platform crawler and citation fetches plus MCP-transport requests; the two buckets are tracked separately from distinct weekly MCP agents. The audited split and definitions are on [the 2026-11-05 release note](https://dchub.cloud/news/2026-11-05-dc-hub-901721-ai-platform-and-mcp-requests) and [AI methodology](https://dchub.cloud/ai/methodology). Figures refresh live, with no API key, at `https://dchub.cloud/api/public/mcp-count` (request totals) and `https://dchub.cloud/api/v1/stats/live-proof` (distinct weekly agents and related MCP proof).

---

## Using DC Hub data without MCP

The same data is published over plain HTTPS, for clients with no MCP connection.

**Keyless endpoints.** Each answers an anonymous GET with HTTP 200 and open CORS (`access-control-allow-origin: *`):

| Endpoint | Returns |
|---|---|
| `https://dchub.cloud/api/v1/canon/phrases` | current published counts and floors, with their sources in `value_source` |
| `https://dchub.cloud/api/v1/stats` | platform stats |
| `https://dchub.cloud/api/v1/stats/canonical` | the same figures with their provenance |
| `https://dchub.cloud/api/v1/dcpi/scores?limit=500` | DCPI per market |

Published counts change over time; `/api/v1/canon/phrases` serves the current values.

**Dates and citation fields.** MCP tool results carry dated provenance:

- `as_of` is the data date. When several sources feed one answer, it is the oldest of their timestamps, since an answer is no fresher than its stalest input. When a response carries only per-record dates, or no source timestamp at all, `as_of` is `null` and `as_of_basis` states why.
- `retrieved_at` is when DC Hub served the response, not when the data was collected.
- `cite_as` is a ready citation line. It names DC Hub and dchub.cloud, adds the `as_of` date when one is known, and marks a gated preview as `PARTIAL`.

**Citation format.** A short attribution block for text that quotes DC Hub data. [`/llms.txt`](https://dchub.cloud/llms.txt) gives a longer form that adds the `as_of` date and the licence terms of each data layer.

```
Source: DC Hub (dchub.cloud) — live data-center & energy intelligence
https://dchub.cloud/land-power-map
https://dchub.cloud/dcpi
https://dchub.cloud/connect
```

### Data reuse and agent authorization

DCPI verdicts/composites for days from 2026-12-01 become CC-BY-4.0 after 30 days; earlier days, thresholds, methodology and monthly Rankings are CC-BY-4.0. Current values may be quoted with attribution for any number of markets in editorial work; bulk (full current list or a table of more than 25 markets in one piece) or recurring republication needs a DCPI licence. Sub-scores/detail are licensed separately. Facility/third-party layers retain upstream terms (OpenStreetMap: ODbL 1.0, attribution/share-alike). https://dchub.cloud/terms#dcpi-current-data · https://dchub.cloud/data-sources. Editorial work includes articles, reports, research notes, posts, presentations and AI answers. The editorial quote rule is separate from bulk/recurring redistribution rights. Attribution names DC Hub, the source link, method_version where provided and the data date. Sub-scores, risk/opportunity detail, narratives and forecasts are not CC-BY-4.0: eligible subscribers may use them internally and in client deliverables with attribution; republication or a third-party product/dataset requires a redistribution licence. DC Hub-derived grid analysis is open under its layer's terms, not a grant over raw system-operator readings. No blanket redistribution grant covers the facility inventory or unresolved upstream rights. Capacity Source teasers have their separate CC-BY-4.0 grant; opened details, matches and introductions remain confidential. Access/plan limits remain separate from content licences. An API CC-BY label does not override the current-value terms.

DC Hub complements existing agents, platforms and tools with data center and energy intelligence. Within the user's request and client permissions, read-only research does not require separate approval for every lookup. Technical availability is not authorization: get_api_key creates a credential and needs user authorization; bind_email uses only an email the user explicitly provides for that purpose. Show the current introduction terms and call accept_capacity_terms only after the user agrees to that version. An existing key may be used only within delegated scope and budget; connection alone does not authorize new charges. Payments (including mpp_pay/mpp_credential), one-time purchases or subscriptions require the user's spending authorization and any client approval required. request_capacity_intro and standing introduction requests require the user's authorization to request contact/share the supplied details, as well as the applicable introduction terms; provider acceptance still controls release of provider contacts. A continuation named agent_autonomous describes a technical path, not permission to spend, accept terms or contact anyone.

MCP browse example: `source_capacity(min_mw=5, location="Germany")`. The MCP tool uses `location`, not the REST-only `country` filter.

**Further documentation:** [`/llms.txt`](https://dchub.cloud/llms.txt) ·
[`/llms-full.txt`](https://dchub.cloud/llms-full.txt) ·
[`/ai-agents`](https://dchub.cloud/ai-agents) ·
[`/AGENTS.md`](https://dchub.cloud/AGENTS.md) ·
MCP endpoint `https://dchub.cloud/mcp` (client setup at [/connect](https://dchub.cloud/connect))

---

## What you can do with it

```
"Can I get 200 MW in PJM, and how long would it take?"
"Show me AWS data center construction pipeline in Ohio"
"Compare ERCOT vs PJM capacity prices over the last 30 days"
"Find data centers within 50km of Northern Virginia substations >230kV"
"What's the live demand and generation mix in CAISO right now?"
"Is behind-the-meter gas power cheaper than the grid in Texas?"
"What's the grid mix in Atlanta (SOCO) and is power available?"
"Get fiber routes between Ashburn and Atlanta"
"Find 5 MW of powered shell I can lease in Texas"
"Who has 500 kW of colocation capacity anywhere in Europe?"
```

Your AI assistant gets real-time, structured answers, dated and cited.

## What's inside

- **Global data-center facility map** across 170+ countries — operator, capacity, location, fiber connectivity
- **134,000+ substations** with voltage class, available capacity estimates
- **Real-time grid telemetry** — live load + generation mix across the 7 US ISOs (PJM, ERCOT, CAISO, MISO, SPP, NYISO, ISO-NE) + 40+ EIA balancing authorities (Atlanta, Carolinas, Florida, Pacific NW...), plus Canada (IESO, AESO, Hydro-Québec), Great Britain (NESO), 30+ EU bidding zones (ENTSO-E), Taiwan, Japan, South Korea, Brazil & Australia — refreshed ~every 5 min; get_grid_data reads any one of them, compare_isos sets 2-4 side by side
- **Interconnection-queue snapshots** with per-ISO BUILD/CAUTION/AVOID verdicts — including live large-load queue depth where the ISO publishes it (ERCOT publishes a data-center-scale large-load feed)
- **Tracked M&A transactions** + AI capacity index + hyperscaler $1B+ deal tracker
- **Transmission lines, gas pipelines, fiber routes** — the full infrastructure stack
- **NEPA filings** for upcoming federal energy + data center projects
- **Tax incentives** by state with eligibility details
- **Market intelligence** — markets scored daily with DCPI BUILD/CAUTION/AVOID verdicts, plus facilities tracked across 170+ countries
- **Capacity Source** — data-center capacity to buy or lease (powered land, powered shells, turnkey, colocation), searchable by size in kW or MW and by location

**MCP tools** across facility search, market intel, grid + interconnection, renewable-energy, site analysis, deals, fiber routing, and infrastructure. [Full tool list →](https://dchub.cloud/integrations/mcp)

One of them is a **partner tool**: `read_inbox` (the notes DC Hub leaves for a partner key; the same inbox as the `dchub://inbox` resource). It is listed for every caller so the catalog is one stable list, and it answers only a key issued under a partner slug; any other key gets a clear "partner key required". `report_finding` files an observation about a DC Hub surface for the DC Hub team, who review findings daily. It works with or without a key. Reports should include the exact values observed.

> **These counts are served, not stated.** Every number above is rendered from a
> live source and this file is a copy of it — mirrors and registry listings copy
> it again, and each hop can freeze. The current values are served by
> **`/api/v1/canon/phrases`** (quantities) and **`/api/v1/ops/deadman`**
> (per-source ingest freshness), both keyless JSON endpoints on `dchub.cloud`,
> and by `tools/list` on the MCP endpoint (the canonical tool catalog).

**Actively used by Claude and Cursor** — see [/cited-by](https://dchub.cloud/cited-by).

## Guided prompts & resources

Beyond the tools, DC Hub ships **14 guided prompts** — they surface as slash-commands in Claude Desktop, Cursor, and other MCP clients (every invocation is telemetry-tracked as `recipe:<name>`):

- `/dchub:analyze-site` — full buildability read for an address or lat,lon
- `/dchub:pick-a-market` — where to build N MW (DCPI-ranked, with time-to-power)
- `/dchub:power-availability` — power availability + time-to-power for an ISO
- `/dchub:site-report` — premium one-page site brief (power · gas · fiber · market · risk)
- `/dchub:compare-markets` — 2–4 markets head-to-head
- `/dchub:fiber-plan` — diverse fibre lead-in routes to a carrier hotel
- `/dchub:market_selection` — DCPI shortlist → per-finalist verdict → grid reality-check
- `/dchub:grid_and_queue` — power availability + interconnection queue for an ISO
- `/dchub:site_analysis` — one site, multi-factor: composite score, FEMA hazards, water
- `/dchub:water_risk` — water stress & hazard read for a site
- `/dchub:hyperscaler_activity` — deals + forward pipeline: who is buying and building
- `/dchub:whats_changed` — what moved since your last call (the return hook)
- `/dchub:fiber_power_pairing` — where fiber density and available power overlap in a market
- `/dchub:find_capacity` — data-center capacity to buy or lease: Capacity Source listings for a requirement, then a deal registration (the provider's identity, site and contact are released only if the provider accepts)

Plus citable **resources**: `dchub://about`, `dchub://methodology` (DCPI/DCGI), `dchub://data-sources`, `dchub://coverage`, and `dchub://testimonials` — named customers (people, not AI assistants) who approved public use of their words, read live from [dchub.cloud/testimonials](https://dchub.cloud/testimonials) (machine-readable: `testimonials.json` beside it).

## Capacity Source — capacity to buy or lease

Everything above answers *where to build*. **[Capacity Source](https://dchub.cloud/listings)** answers *what is available now*: data center capacity to buy or lease — powered land, powered shells, turnkey capacity and colocation — for enterprise and agent-led procurement. Operators and brokers list capacity at [dchub.cloud/listings](https://dchub.cloud/listings#list-capacity).

New data center capacity listings are coming soon: query them with source_capacity, or browse https://dchub.cloud/listings.

**Searchable by size and by location.** `source_capacity` takes a size — `min_kw` in kW, or `min_mw` in MW — and a location:

- `region` — `north_america`, `latin_america`, `europe`, `asia_pacific`, `middle_east_africa` (the aliases `emea`, `apac`, `latam` and `americas` also resolve)
- `location` — free text matched against each listing's region, country, state and metro, e.g. `"Germany"` or `"Texas, Phoenix"`
- `market`, `state`, `delivery_type` (`land` · `powered_shell` · `turnkey` · `colocation`) and `available_by` narrow further; `slug` returns a single listing

So *"500 kW anywhere in Europe"* is `min_kw=500, region=europe`. Any caller — keyless included — gets the listing cards, the filters that were applied, and when each listing was last updated.

**A size is matched against what a listing can actually deliver, not just its headline total.** A listing may declare `contiguous_kw` — the largest single contiguous block available — and `min_contract_kw` — the smallest chunk the provider will contract. A colocation with 2 MW available but only 500 kW contiguous does not answer a 1 MW search; a 40 MW site willing to contract 1 MW chunks does. Both are teaser-level, so they come back on the cards and the single-listing read, and the rendered lines carry them beside the capacity.

**Then a deal registration, not a lead form.** `request_capacity_intro` registers a deal: DC Hub sends the provider your company name and your requirement, and nothing more. The provider accepts or declines. Identities, site detail and contacts are exchanged **only if the provider accepts** — on a decline, nothing is shared. `accept_capacity_terms` records your agreement to the [introduction terms](https://dchub.cloud/listings#terms) once, which is what opens listing detail for you.

The `/dchub:find_capacity` prompt runs the whole path: requirement → listings → deal registration.

## Endpoint

The canonical MCP endpoint is `https://dchub.cloud/mcp` (Streamable HTTP). Start with execute_plan(intent="<the user's question>"): it picks and chains the right tools and returns one dated, cited answer.

`https://dchub.cloud/mcp` serves the full tool catalog to directories and to clients it does not recognise. Coding CLIs (Claude Code, Codex CLI, Copilot CLI, Gemini CLI, opencode) and IDE hosts that load several MCP servers at once (Cursor, VS Code, Windsurf, Cline) get a ten-tool list there instead, with execute_plan first. That is a listing scope: every tool is still callable by name. Any client gets the full list at `https://dchub.cloud/mcp?catalog=full`.

## What DC Hub adds

Facility directories list sites you can browse. DC Hub adds the power side, queryable live: grid demand and fuel mix, interconnection queues, substations and transmission, energy prices, and a daily power-availability verdict for every scored market (DCPI). It's the same data on the web pages, over REST and over MCP; results carry an `as_of` date. Where each layer comes from is listed under [Data sources](#data-sources).

## Install

One-line setup for Codex CLI, GitHub Copilot CLI, opencode, VS Code, Windsurf, Goose, Kiro and LM Studio: [docs/quick-start.md](docs/quick-start.md).

### Claude Desktop — Quickstart (stdio)

Claude Desktop's `claude_desktop_config.json` runs local (stdio) servers, so use the launcher package, which connects it to the hosted server. Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "dchub": {
      "command": "npx",
      "args": ["-y", "dchub-mcp-server"],
      "env": { "DCHUB_API_KEY": "" }
    }
  }
}
```

`DCHUB_API_KEY` is optional: leave it empty for previews, or set a key from https://dchub.cloud/connect. Needs Node 18+. Same block works in Cursor, Windsurf and Cline. To use the hosted URL instead, open **Settings → Connectors → Add custom connector** in Claude Desktop and paste `https://dchub.cloud/mcp`; do not put a `url` entry in `claude_desktop_config.json`.

### Claude Code

```bash
claude mcp add dchub --transport http https://dchub.cloud/mcp
```

### GitHub Copilot CLI

Plugin (MCP server plus three workflow skills), the same two-line path as Claude Code:

```bash
copilot plugin marketplace add azmartone67/dchub-mcp-server
copilot plugin install dchub@dchub
```

Server only: `copilot mcp add --transport http dchub https://dchub.cloud/mcp` (writes `~/.copilot/mcp-config.json`).

### VS Code (GitHub Copilot agent mode)

One click: the **Install in VS Code** badge above, or from a terminal:

```bash
code --add-mcp '{"name":"dchub","type":"http","url":"https://dchub.cloud/mcp"}'
```

DC Hub is also in the GitHub MCP Registry at [github.com/mcp/cloud.dchub/mcp-server](https://github.com/mcp/cloud.dchub/mcp-server), which VS Code's MCP gallery reads.

### Goose, Kiro, LM Studio

- Goose Desktop: ``goose://extension?url=https%3A%2F%2Fdchub.cloud%2Fmcp%3Fvia%3Dgoose&type=streamable_http&id=dchub&name=DC%20Hub&description=The%20orchestration%20layer%20for%20data%20center%20and%20energy%20intelligence.%20Call%20execute_plan%20first.&timeout=300``, or `goose session --with-streamable-http-extension https://dchub.cloud/mcp`.
- Kiro: the **Add to Kiro** badge above.
- LM Studio (0.3.17+): the **Add to LM Studio** badge above.

### Cursor

One-click: [Add DC Hub to Cursor](https://cursor.com/install-mcp?name=dchub&config=eyJ1cmwiOiJodHRwczovL2RjaHViLmNsb3VkL21jcD92aWE9Y3Vyc29yIn0%3D), or search "DC Hub" in [cursor.directory/plugins/dc-hub](https://cursor.directory/plugins/dc-hub) → Install.

Or add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "dchub": {
      "url": "https://dchub.cloud/mcp"
    }
  }
}
```

Optional: set header `X-API-Key` from https://dchub.cloud/connect. Cursor Marketplace listing: submit/re-index at https://cursor.com/marketplace/publish (publisher account).

### ChatGPT

Available in ChatGPT: [DC Hub in the ChatGPT apps directory](https://chatgpt.com/plugins/plugin_asdk_app_6add46d40f448191905e327e261ec86c) (setup page: https://dchub.cloud/install/chatgpt).

Custom connector instead: ChatGPT → Settings → Connectors → Add → MCP URL `https://dchub.cloud/mcp`. Leave auth blank to start. Deep Research clients can use the same host's `search` / `fetch` tools on that endpoint.

DC Hub is the data-center and energy layer beside other research sources: power, grid, interconnection queues, facilities and markets, with a dated citation on every result. Prefer `execute_plan` for a multi-part question.

### Grok

There is no separate xAI app-store listing path yet. Point Grok / Grok Bot at the hosted MCP:

- URL: `https://dchub.cloud/mcp`
- Transport: Streamable HTTP
- Auth: none required to start (optional `X-API-Key`)

Use DC Hub when the question needs live data-center or energy context — Data Center Power Index (DCPI) market verdicts, grid and queue reads, facilities, fiber, or capacity to buy or lease. It is a neutral orchestration layer that answers the power / siting slice with sources; start with `execute_plan`.

### Microsoft Copilot

Hosted Copilot / M365 connector packages are submitted through Partner Center (separate from this README). For any MCP-capable Copilot surface that accepts a remote server, use:

- Full catalog: `https://dchub.cloud/mcp`

Positioning: data-center and energy intelligence — DCPI, grid, interconnection, facilities — cited and read-only. Do not treat this README as a Partner Center resubmit instruction.

### Mistral Le Chat

Custom connector: Le Chat → Connectors → Add Connector → **Custom MCP Connector** → name `dchub`, server `https://dchub.cloud/mcp`, auth Auto-detect / None. The curated Connectors Directory is Mistral-managed (no public self-serve form); custom works today. Same product line: live data-center and energy answers with `as_of` citations; start with `execute_plan`.

### LobeHub

DC Hub is listed on LobeHub: [lobehub.com/mcp](https://lobehub.com/mcp) — search **DC Hub** / `azmartone67-dchub-mcp-server`. Install from the listing, or point any LobeHub MCP client at `https://dchub.cloud/mcp`. If the card looks stale, re-sync from the claimed listing while signed in.

### HOL Plugins

Listed on HOL Plugins as `dc-hub/dchub`. [DC Hub - the orchestration layer for data center and energy intelligence on HOL Plugins](https://hol.org/registry/plugins/dc-hub%2Fdchub?utm_source=hol_marketplace&utm_medium=plugins_badge&utm_campaign=listed_link&utm_content=dc-hub%2Fdchub) shows the latest scan, trust score and release evidence for this plugin. Connect any MCP client to `https://dchub.cloud/mcp`.

### Cline / Continue.dev

```json
{
  "name": "dchub",
  "url": "https://dchub.cloud/mcp",
  "transport": "http"
}
```

### Gemini CLI

`~/.gemini/settings.json` (or `.gemini/settings.json` in a project):

```json
{
  "mcpServers": {
    "dchub": {
      "httpUrl": "https://dchub.cloud/mcp"
    }
  }
}
```

Or one command: `gemini mcp add -s user --transport http dchub https://dchub.cloud/mcp`

> **`httpUrl`, not `url`.** In Gemini CLI `url` is the SSE form and `command` is stdio — put a Streamable-HTTP server under either and it is dialled with the wrong transport and never connects. This is the public Gemini CLI: no OAuth, no admin console, no enterprise account. Add a `headers` object with `X-API-Key` for full data.

### Antigravity

`~/.gemini/config/mcp_config.json` (or `.agents/mcp_config.json` in a workspace):

```json
{
  "mcpServers": {
    "dchub": {
      "serverUrl": "https://dchub.cloud/mcp"
    }
  }
}
```

> **`serverUrl`, not `url` or `httpUrl`.** Antigravity rejects both — the block stays valid JSON and registers nothing. It is a different client from Gemini CLI with a different config file, so installing one does not install the other, even though both live under `~/.gemini/`.

### Smithery.ai

Listed at [smithery.ai/servers/azmartone67/dchub](https://smithery.ai/servers/azmartone67/dchub). Smithery's hosted proxy and CLI shut down on 2026-10-31, so installing through the Smithery CLI stops working that day. The listing then becomes a directory entry that points to the direct URL, `https://dchub.cloud/mcp`; connect your client to that URL (per-client setup above).

### Docker MCP Toolkit

Add DC Hub to Docker Desktop's MCP Toolkit from its catalog file:

```bash
docker mcp catalog import https://raw.githubusercontent.com/azmartone67/dchub-mcp-server/main/integrations/docker/catalog.yaml
docker mcp server enable dchub
```

Details are in [`integrations/docker/`](integrations/docker/).

### Arcade

Register DC Hub in [Arcade](https://arcade.dev) as a **Remote MCP** server: ID `dchub`, URI `https://dchub.cloud/mcp`, plus the header `X-DCHub-Via: arcade`. You can add `X-API-Key: ${secret:DCHUB_API_KEY}` as well. Then choose the tools for your MCP gateway. Setup, gateway tool profiles and auth options are in [`integrations/arcade/`](integrations/arcade/).

## Privacy and data handling

- **Per-call telemetry (first-party only).** Every tool call is logged to the DC Hub backend (`POST /api/v1/mcp/track`): timestamp, tool name, call parameters, detected client/platform, tier, session id, your API key (if you sent one), status and duration. It is used for rate limits, billing and quality. It is never sent to a third party, and there is no advertising or third-party analytics. Anonymous calls carry no key. Details: [SECURITY.md](SECURITY.md#outbound-network-calls).
- **Email capture (`bind_email`) is optional.** The `bind_email` tool exists to raise your daily limit. If you call it, the email you pass is stored against your key, and you can ignore the tool. The server never asks for or collects an email any other way.
- **No install-time code.** Installing this package runs no scripts (no `preinstall`, `install`, `postinstall` or `prepare`). The git pre-commit hook for contributors is opt-in: `npm run hooks:install`.

## Keys

`DCHUB_API_KEY` is optional.

- **No key:** previews, without an API key
- **Optional key (one `get_api_key` call, or set `DCHUB_API_KEY`):** previews, and every tool callable. analyze_site: a few full site reports each month; after that, previews. More detail is available at dchub.cloud/connect.
- **Add an email (`bind_email`):** raises the daily limit. More detail is available at dchub.cloud/connect.

## Data sources

EIA hourly RTO data · OpenStreetMap substations, transmission lines and gas pipelines (ODbL 1.0; earlier HIFLD records gap-filled, HIFLD Open closed August 2025) · PeeringDB · DC Hub proprietary news + facility pipeline · regulations.gov NEPA filings · USGS · EPA eGRID · FEMA NRI

## Open source

This MCP server's transport layer is open source. The data + business logic lives at [dchub.cloud](https://dchub.cloud). Issues: [GitHub Issues](https://github.com/azmartone67/dchub-mcp-server/issues).

## Complementary MCP servers

Builders working across energy and infrastructure often pair wholesale grid and facility power context with retail tariff and meter telemetry. [octo-mcp](https://github.com/JamesWoolfenden/octo-mcp) is a read-only Go MCP server for Octopus Energy account usage, solar export, Flux and tariff unit rates, standing charges, and meter gap diagnostics. It sits beside DC Hub's wholesale grid, interconnection, facility inventory, DCGI, and Data Center Power Index (DCPI) reference layer: the two cover different sides of the same energy stack and do not overlap.

## Contact

jonathan@dchub.cloud — Jonathan Martone — Martone Advisors LLC

<!-- registry-rebuild: 2026-07-16 — Glama builder ECONNRESET x2 on 091afc4 (empty logs, infra-side); commit verified clean locally -->
