# PriceWin plugin for coding agents

Live hotel and flight prices compared across Booking.com, Agoda, Trip.com and
Traveloka, in USD, from inside your coding agent. One package bundles:

- **`.mcp.json`**: the PriceWin MCP server, `https://mcp.price.win/mcp`
  (Streamable HTTP, no account, no API key);
- **`skills/pricewin-travel-search`**: how to run a search (results arrive in
  two steps), what to ask when the trip details are incomplete, and how to read
  prices and links.

The same files load in Claude Code, Codex CLI and ZCode: all three read
`.claude-plugin/plugin.json`, the plugin-root `.mcp.json` and `skills/`.
Antigravity reads the root `plugin.json`, `mcp_config.json` and the same
`skills/`; GitHub Copilot CLI reads `.plugin/plugin.json` with `.mcp.json`
and `skills/`; Gemini CLI reads `gemini-extension.json` and `skills/`. OpenCode
takes the server from `opencode.json` and the skill from `~/.agents/skills`.

## Install

### Claude Code

```
/plugin marketplace add PriceDotWin/pricewin-agent-plugin
/plugin install pricewin@pricewin
```

### Codex CLI

```bash
codex plugin marketplace add PriceDotWin/pricewin-agent-plugin
codex plugin add pricewin@pricewin
```

Codex asks for approval before PriceWin calls: the search and booking tools
reach outside services, and their annotations say so (`openWorldHint: true`).

### GitHub Copilot CLI

```bash
copilot plugin install PriceDotWin/pricewin-agent-plugin
```

`copilot mcp list` should show `pricewin (http)` under plugin servers.

### Antigravity

```bash
agy plugin install https://github.com/PriceDotWin/pricewin-agent-plugin
```

### Gemini CLI

```bash
gemini extensions install https://github.com/PriceDotWin/pricewin-agent-plugin
```

### OpenCode

OpenCode needs no plugin: add the server to `opencode.json` (in the project, or
`~/.config/opencode/opencode.json` for every project):

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "pricewin": {
      "type": "remote",
      "url": "https://mcp.price.win/mcp"
    }
  }
}
```

and, optionally, the skill, which OpenCode loads from `~/.agents/skills`:

```bash
git clone --depth 1 https://github.com/PriceDotWin/pricewin-agent-plugin /tmp/pricewin
mkdir -p ~/.agents/skills && cp -r /tmp/pricewin/skills/pricewin-travel-search ~/.agents/skills/
```

`opencode mcp list` should show `pricewin` as connected.

### Cline

Add the server to Cline's MCP settings (`cline_mcp_settings.json`; in the CLI,
`~/.cline/data/settings/cline_mcp_settings.json`). Set `type` explicitly,
because Cline otherwise assumes the legacy SSE transport:

```json
{
  "mcpServers": {
    "pricewin": {
      "type": "streamableHttp",
      "url": "https://mcp.price.win/mcp",
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

No API key or login is needed. Optionally copy
`skills/pricewin-travel-search` into `~/.cline/skills/`, which Cline loads as a
skill. Tested with the Cline CLI 3.0.68.

### Pi and DeepSeek Harness

Both need their own package format, so they have their own repositories with
the same server and skill:
[pricewin-pi](https://github.com/PriceDotWin/pricewin-pi) and
[pricewin-dsh](https://github.com/PriceDotWin/pricewin-dsh).

### ZCode

ZCode reads this package format. A listing in the ZCode plugin marketplace is
pending; this README will give the install step once it is live.

Then ask, for example:

> Compare hotel prices in Da Nang for 2 adults from November 10 to 12.

## Tools

| Tool | What it does |
|---|---|
| `search_hotels_live`, `poll_search_results` | Search a city's hotels across the OTAs and OpenTravel partner hotels; results arrive in two steps |
| `search_flights_live`, `poll_flight_results` | Search one-way or per-leg round-trip fares |
| `get_ota_hotel_detail` | Rooms, live prices, facilities and reviews for one named hotel (Booking.com) |
| `get_hotel_detail`, `get_hotel_info` | Rooms and prices, or facilities and policies, of an OpenTravel partner hotel |
| `get_cancellation_policy` | Refund terms for one rate |
| `request_booking`, `check_booking_status` | Send a booking request to a partner hotel and read its status |
| `request_cancel_token`, `cancel_booking` | Cancel such a booking, in two steps |

**Booking takes no money.** `request_booking` sends the guest's name, phone and
email to the hotel, which confirms the request; no room is held and the guest
pays at the property. Cancelling needs a single-use token that is emailed to the
address on the booking, so nothing is cancelled without the guest's own inbox.

## What the plugin sends, and where

The plugin contains no code. It points the agent at one remote MCP server,
`https://mcp.price.win/mcp`, and a skill that tells the agent how to use it.

- **To `mcp.price.win`**: the arguments of each tool call, which are trip details
  (city, dates, party size, hotel name, price range, airports, cabin), a short
  excerpt of the request used only to pick the reply language, and, for a
  booking request, the guest's name, phone number and email.
- **Onward from PriceWin's server**: only to PriceWin's own backend and to
  OpenTravel's API (`api.travelopen.ai`), which the PriceWin developer also owns.
  A booking request's name, phone and email go to the partner hotel through
  OpenTravel, so the hotel can confirm it.
- **Usage analytics**: PriceWin records trip parameters only (city, dates,
  party size, hotel name, currency), never a guest's name, email, phone,
  confirmation code or cancel token.
- **Where prices come from**: PriceWin's backend reads Booking.com, Agoda,
  Traveloka, Trip.com and Google Flights from their public pages at search time.
  PriceWin has no partnership with those sites. Each result is labelled with its
  source and links to it for booking. Prices are time-sensitive.

No account is needed, nothing runs on your machine, and no payment data is
ever requested. See the [privacy policy](https://www.price.win/en/privacy-policy)
and [terms of service](https://www.price.win/en/terms-of-service).

## Support

[mcp.price.win/support](https://mcp.price.win/support) · support@price.win ·
[tool reference](https://mcp.price.win/docs)

## License

MIT
