# MAQAMI Travel MCP Server

[![Official MCP Registry](https://img.shields.io/badge/MCP_Registry-io.github.negm17111995%2Fmaqami--travel-blue)](https://registry.modelcontextprotocol.io/v0/servers/io.github.negm17111995%2Fmaqami-travel/versions/latest)
[![npm version](https://img.shields.io/npm/v/maqami-travel)](https://www.npmjs.com/package/maqami-travel)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Transport: Streamable HTTP](https://img.shields.io/badge/transport-Streamable_HTTP-informational)](#other-streamable-http-clients)
[![MAQAMI Travel MCP server on Glama](https://glama.ai/mcp/servers/negm17111995/mcp-server/badge)](https://glama.ai/mcp/servers/negm17111995/mcp-server)

Official MCP server for MAQAMI, a hotel and flight booking platform with 3M+ hotels. Search live hotel rates and flights, look up cities, airports and hotel details, then send the customer a secure checkout link on book.maqami.co for the exact room or fare they chose. Remote Streamable HTTP endpoint, no API key required.

```
https://mcp.maqami.co/
```

## Quick start

Pick your client. Each line is enough to connect; the full steps are under [Connect](#connect).

| Client | Fastest way to connect |
| --- | --- |
| Claude Code | `claude mcp add --transport http maqami-travel https://mcp.maqami.co/` |
| Claude Desktop (one click) | Download [`maqami-travel.mcpb`](https://github.com/negm17111995/mcp-server/releases/latest/download/maqami-travel.mcpb) and open it ([steps](#claude-desktop-extension)) |
| Any stdio client (npm) | `npx -y maqami-travel` as the server command ([config](#local-stdio-npm)); Node.js 18+ |
| claude.ai, Claude Desktop and Claude mobile | **Customize → Connectors → Add custom connector**, URL `https://mcp.maqami.co/`, **No sign in**. Works on the Free plan ([steps](#claude-claudeai-and-claude-desktop)) |
| Cursor | [Add to Cursor](https://cursor.com/en/install-mcp?name=maqami-travel&config=eyJ1cmwiOiJodHRwczovL21jcC5tYXFhbWkuY28vIn0%3D) (one click), or add `"maqami-travel": { "url": "https://mcp.maqami.co/" }` to `mcp.json` |
| VS Code | [Install in VS Code](https://insiders.vscode.dev/redirect/mcp/install?name=maqami-travel&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fmcp.maqami.co%2F%22%7D) (one click), or `code --add-mcp '{"name":"maqami-travel","type":"http","url":"https://mcp.maqami.co/"}'` |
| Windsurf | Add `"maqami-travel": { "serverUrl": "https://mcp.maqami.co/" }` to `mcp_config.json` |
| Gemini CLI | `gemini extensions install https://github.com/negm17111995/mcp-server` |
| OpenAI Codex | `codex mcp add maqami-travel --url https://mcp.maqami.co/` |
| ChatGPT | Developer mode → create an app with URL `https://mcp.maqami.co/` and **No Authentication** ([steps and plans](#chatgpt)) |
| OpenAI Agents SDK | `MCPServerStreamableHttp(name="MAQAMI Travel", params={"url": "https://mcp.maqami.co/"})` |
| LangChain | `MCPAdapter("https://mcp.maqami.co/")` from `langchain.mcp` ([example](#langchain-python)) |
| n8n | **MCP Client Tool** node, endpoint `https://mcp.maqami.co/`, HTTP Streamable, no authentication ([steps](#n8n)) |
| Cline | **MCP Servers → Remote Servers**, URL `https://mcp.maqami.co/`, Streamable HTTP |
| LM Studio | Add `"maqami-travel": { "url": "https://mcp.maqami.co/" }` to `mcp.json`, or use the [install link](#lm-studio) |
| Booking skill only (Claude Code, Codex, Cursor and other skill-aware agents) | `npx skills add negm17111995/mcp-server` |
| Any other client | Streamable HTTP at `https://mcp.maqami.co/` with no auth, or `npx -y maqami-travel` for stdio-only clients |

Then try: *"Find 4-star hotels in Lisbon for 2 adults, 12 to 15 May."*

## Contents

- [Connect](#connect)
- [How agents use the server](#how-agents-use-the-server)
- [What you can do](#what-you-can-do)
- [Example prompts](#example-prompts)
- [FAQ](#faq)
- [Examples](#examples)
- [Privacy and security](#privacy-and-security)
- [Development](#development)

## Connect

The server is hosted at `https://mcp.maqami.co/` and uses the Streamable HTTP transport. There is nothing to install and no API key to configure.

### Claude (claude.ai and Claude Desktop)

Add MAQAMI as a custom connector:

1. Go to **Customize → Connectors**.
2. Click **+ Add**, then **Add custom connector**.
3. Enter the name `MAQAMI Travel` and the URL `https://mcp.maqami.co/`, then click **Continue**.
4. Under **Authentication**, choose **No sign in**, then click **Add**.

This works on every Claude plan, including Free. Free accounts can have one custom connector at a time.

On Team and Enterprise plans, an Owner adds the connector under **Organization settings → Connectors** first.

### Claude Desktop extension

A one-click install for Claude Desktop on macOS, Windows and Linux. It doesn't use a custom connector slot, so it also suits Free accounts that already have one.

1. Download [`maqami-travel.mcpb`](https://github.com/negm17111995/mcp-server/releases/latest/download/maqami-travel.mcpb).
2. Open the file, or drag it into Claude Desktop under **Settings → Extensions**.
3. Click **Install**.

The extension runs the same stdio bridge as the npm package and connects to `https://mcp.maqami.co/`. Claude Desktop provides Node.js, so there is nothing else to install.

### Claude Code

```bash
claude mcp add --transport http maqami-travel https://mcp.maqami.co/
```

Or install the plugin, which adds the server and a booking skill that walks Claude through search, confirmation and the checkout link:

```text
/plugin marketplace add negm17111995/mcp-server
/plugin install maqami-travel@maqami
```

### Cursor

Add to `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (project):

```json
{
  "mcpServers": {
    "maqami-travel": {
      "url": "https://mcp.maqami.co/"
    }
  }
}
```

Or install with one click: [Add to Cursor](https://cursor.com/en/install-mcp?name=maqami-travel&config=eyJ1cmwiOiJodHRwczovL21jcC5tYXFhbWkuY28vIn0%3D). The same install as a deeplink, to open in your browser:

```text
cursor://anysphere.cursor-deeplink/mcp/install?name=maqami-travel&config=eyJ1cmwiOiJodHRwczovL21jcC5tYXFhbWkuY28vIn0=
```

### VS Code

Add to `.vscode/mcp.json` in your workspace:

```json
{
  "servers": {
    "maqami-travel": {
      "type": "http",
      "url": "https://mcp.maqami.co/"
    }
  }
}
```

Or [install in VS Code](https://insiders.vscode.dev/redirect/mcp/install?name=maqami-travel&config=%7B%22type%22%3A%22http%22%2C%22url%22%3A%22https%3A%2F%2Fmcp.maqami.co%2F%22%7D) with one click, or add it to your user profile from the command line:

```bash
code --add-mcp '{"name":"maqami-travel","type":"http","url":"https://mcp.maqami.co/"}'
```

### Cline

In the Cline panel, open **MCP Servers → Remote Servers**, enter the URL `https://mcp.maqami.co/` and choose **Streamable HTTP**. Or add it to the MCP settings JSON:

```json
{
  "mcpServers": {
    "maqami-travel": {
      "type": "streamableHttp",
      "url": "https://mcp.maqami.co/"
    }
  }
}
```

### LM Studio

LM Studio 0.3.17 and later can use MCP servers. Open the **Program** tab in the right-hand sidebar, choose **Install → Edit mcp.json**, and add:

```json
{
  "mcpServers": {
    "maqami-travel": {
      "url": "https://mcp.maqami.co/"
    }
  }
}
```

Or install it by opening this link in your browser:

```text
lmstudio://add_mcp?name=maqami-travel&config=eyJ1cmwiOiJodHRwczovL21jcC5tYXFhbWkuY28vIn0%3D
```

Local models have smaller context windows, so consider turning off the tools you don't need (see the [FAQ](#faq)).

### Windsurf

Open `mcp_config.json` from the **…** menu in the Cascade panel (**Open MCP config file**) and add:

```json
{
  "mcpServers": {
    "maqami-travel": {
      "serverUrl": "https://mcp.maqami.co/"
    }
  }
}
```

On current releases the file is at `~/.config/devin/mcp_config.json` (macOS and Linux) or `%APPDATA%\devin\mcp_config.json` (Windows). Older releases use `~/.codeium/windsurf/mcp_config.json`.

### ChatGPT

Developer mode apps are available on the web for Plus, Pro, Business, Enterprise and Education accounts. On the Free plan, ChatGPT shows only apps published in its app directory.

1. Open **Settings → Security and login** and turn on **Developer mode**.
2. Open **Plugins**, select the **+** button and create a developer-mode app.
3. Enter the name `MAQAMI Travel` and the URL `https://mcp.maqami.co/`, and choose **No Authentication**.
4. In a conversation, choose **Developer mode** from the **+** menu and select MAQAMI Travel.

### OpenAI Codex

```bash
codex mcp add maqami-travel --url https://mcp.maqami.co/
```

Or add to `~/.codex/config.toml`:

```toml
[mcp_servers.maqami-travel]
url = "https://mcp.maqami.co/"
```

### Gemini CLI

Install the extension, which adds the server and its context file:

```bash
gemini extensions install https://github.com/negm17111995/mcp-server
```

Or add only the server:

```bash
gemini mcp add --transport http maqami-travel https://mcp.maqami.co/
```

Or add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "maqami-travel": {
      "httpUrl": "https://mcp.maqami.co/"
    }
  }
}
```

### OpenAI Agents SDK (Python)

```python
import asyncio

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp


async def main() -> None:
    async with MCPServerStreamableHttp(
        name="MAQAMI Travel",
        params={"url": "https://mcp.maqami.co/"},
    ) as maqami:
        agent = Agent(name="Travel assistant", mcp_servers=[maqami])
        result = await Runner.run(agent, "Find 4-star hotels in Lisbon for 2 adults, 12 to 15 May.")
        print(result.final_output)


asyncio.run(main())
```

### LangChain (Python)

LangChain 1.x includes MCP support in `langchain.mcp` (beta). Install with `pip install langchain langchain-openai`:

```python
import asyncio

from langchain.agents import create_agent
from langchain.mcp import MCPAdapter


async def main() -> None:
    async with MCPAdapter("https://mcp.maqami.co/") as maqami:
        tools = await maqami.list_tools()
        agent = create_agent("openai:gpt-5.4-mini", tools)
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": "Which airports serve Tokyo?"}]}
        )
        print(result["messages"][-1].content)


asyncio.run(main())
```

For a version that asks for your approval before any prebook, see [travel-agent-examples/langchain-python](https://github.com/negm17111995/travel-agent-examples/tree/main/langchain-python).

### n8n

1. Add an **AI Agent** node to your workflow.
2. Under **Tools**, add an **MCP Client Tool** node.
3. Set the endpoint to `https://mcp.maqami.co/`, choose **HTTP Streamable** as the server transport (if your n8n version shows the option) and **None** for authentication.
4. Under **Tools to Include**, pick the tools your workflow needs, or keep **All**.

### Other Streamable HTTP clients

| Setting   | Value                    |
| --------- | ------------------------ |
| URL       | `https://mcp.maqami.co/` |
| Transport | Streamable HTTP          |
| Auth      | None                     |

### Local stdio (npm)

For clients that only support stdio servers, the `maqami-travel` npm package is a thin bridge to the remote endpoint. It runs no booking logic locally and needs no credentials. Node.js 18 or later is required.

```json
{
  "mcpServers": {
    "maqami-travel": {
      "command": "npx",
      "args": ["-y", "maqami-travel"]
    }
  }
}
```

This works in `claude_desktop_config.json` and any other client that launches stdio servers.

## How agents use the server

The server is a standard MCP server. Every tool has a JSON Schema for its inputs and MCP annotations, so clients can tell read-only tools (`readOnlyHint: true`) from tools that change something.

Customers always book and pay on MAQAMI's website, book.maqami.co. The server finds the hotel or flight, holds the price and returns a `checkoutUrl` for that exact choice; the customer enters guest or passenger details, pays and gets their confirmation there. No tool takes payment or asks for payment details.

### Hotel booking flow

| Step | What happens | Tool (example) |
| --- | --- | --- |
| 1. Search rates | Live rates for the dates and guests. Needs `checkin`, `checkout`, `occupancies`, `currency`, `guestNationality` and one location field (`cityName` with `countryCode`, `latitude` and `longitude`, `iataCode`, `hotelIds` or `aiSearch`). To find a hotel by name, call `get_data_hotels` with `hotelName` and `countryCode`, then search by `hotelIds`. Each rate has an `offerId`. | `post_hotels_rates` |
| 2. Show details | Description, amenities, photos and reviews for the hotels the user is interested in | `get_data_hotel`, `get_data_reviews` |
| 3. Confirm | Show the user the hotel, room, dates, guests, price and cancellation terms, and wait for a clear yes | (your agent) |
| 4. Prebook | Holds one `offerId`, passed exactly as the search returned it, and returns a `prebookId` with the final price, the cancellation terms and a `checkoutUrl` | `post_rates_prebook` |
| 5. Checkout | Give the customer the `checkoutUrl` (`https://book.maqami.co/booking?prebookId=...`) to enter guest details and pay | (your agent) |

### Flight booking flow

| Step | What happens | Tool (example) |
| --- | --- | --- |
| 1. Find airports | Resolve cities to IATA airport codes | `get_data_flights_airports` |
| 2. Search flights | Live offers. Needs `legs` (each with `origin`, `destination` and `date`), `adults` and `currency`. One leg for one-way, two for a round trip. Also returns `searchUrl`, the same search on book.maqami.co. | `post_flights_rates` |
| 3. Verify | Confirms an `offerId` is still available and returns the latest price, baggage, fare rules and a `checkoutUrl` for that offer. Offers expire (see `expiration`); if one is gone, search again. | `post_flights_verify` |
| 4. Confirm | Show the user the flights, passengers, final price and fare rules, and wait for a clear yes | (your agent) |
| 5. Checkout | Give the customer the `checkoutUrl` (`https://book.maqami.co/flights/booking?offerId=...`) promptly; the fare is held for a limited time | (your agent) |

### Existing bookings

Lookup, amend and cancel tools need the booking ID and the email used to book; the server only returns or changes a booking when both match. Pass both `bookingId` and `email` to every booking tool. To find a customer's hotel bookings, call `listBookings` with the email and last name used to book; it returns only bookings where both match the booking holder. Hotel bookings are cancelled with `cancel_hotel_booking`, flights with `post_flights_bookings_bookingid_cancellations` (check `get_flights_bookings_bookingid_cancellations` for the refund estimate first). `put_bookings_bookingid_amend` corrects the holder's name, email or phone on a hotel booking: it takes the `email` currently on the booking and the corrected `holder` (`firstName`, `lastName`, `email`, optional `phone`).

Tool names and required fields above are as published by the server in October 2026. The tool list your client receives from the server is always the source of truth: only the tools it lists exist, and other tool names are rejected. Hotel `offerId`s are signed by the server: pass them exactly as returned, and run the search again if one is rejected.

### Good practice for agents

- **Ask for missing inputs** instead of guessing: dates, number of guests, the guest's nationality and the currency for hotels; dates, passengers and currency for flights.
- **Quote only what the tools return.** Show the price with its currency and the cancellation or fare rules when they are available.
- **Confirm before anything that is not read-only.** Prebook holds a real rate, and the amend and cancel tools change or cancel real bookings. Ask the user first and show exactly what will happen.
- **Send only links the tools return.** Give the customer the `checkoutUrl` from prebook or verify, and never ask for card or passport details in the chat.
- **If a price or availability changes** at prebook or verify, show the new result and ask again.
- **Keep guest details to what the booking needs**, and only send them once the user has chosen an option.
- **Keep responses small.** Set `limit` and `maxRatesPerHotel` on hotel searches and `filters` on flight searches. `get_data_facilities`, `get_data_chains`, `get_data_iatacodes` and `get_data_cities` return whole reference lists, so call them only when you need an ID from them; find airports with `get_data_flights_airports` instead.

The [examples](#examples) show one way to do this: read-only tools run automatically and every other tool waits for the user's approval.

## FAQ

**Do I need an API key or an account to connect?**
No. The endpoint accepts connections without authentication.

**How does the customer pay?**
Only on MAQAMI's website. Prebook (hotels) or verify (flights) returns a `checkoutUrl` on book.maqami.co for that exact room or fare. The customer opens it, enters guest or passenger details, pays securely and receives the confirmation there. The MCP server never takes payment.

**Does the checkout link create a real reservation?**
Yes, once the customer completes checkout on book.maqami.co. Review the details and final price before paying.

**Which transport does the server use?**
Streamable HTTP at `https://mcp.maqami.co/`. If your client only supports stdio, use the [`maqami-travel` npm bridge](#local-stdio-npm).

**My client warns that there are too many tools. What should I do?**
Turn on only the tools you need. Most clients let you do this: the tool picker in VS Code, per-tool toggles in Cursor and Claude, and **Tools to Include** in n8n. For a travel assistant, the search, details, prebook and verify tools in the tables above are a good start.

**What does the server see?**
An MCP server receives only the tool calls and arguments your client sends. It does not see the rest of your conversation.

**Where is the server listed?**
In the official MCP Registry as `io.github.negm17111995/maqami-travel`, and on npm as `maqami-travel`. It is also a Claude Desktop extension ([`maqami-travel.mcpb`](https://github.com/negm17111995/mcp-server/releases/latest/download/maqami-travel.mcpb)). This repository is also a Gemini CLI extension (`gemini-extension.json`), a Claude Code plugin and marketplace (`.claude-plugin/`), a Codex plugin (`.codex-plugin/plugin.json`) and an Agent Plugins package (`plugin.json` and `mcp.json`). The plugins bundle the `maqami-travel-booking` skill. Directories: [Smithery](https://smithery.ai/servers/ahmednegm-1711/maqami-travel), [Glama](https://glama.ai/mcp/servers/negm17111995/mcp-server), Raycast's MCP registry, the ToolSDK MCP registry and the Hermes Agent plugin catalog.

**Can I use it in my own agent or product?**
Yes, it's a public endpoint. Please follow the confirmation guidance above. For partnerships, contact [info@maqami.co](mailto:info@maqami.co).

**How do I report a bug or a security issue?**
Open an [issue](https://github.com/negm17111995/mcp-server/issues) for bugs and client setup problems. For security issues, follow [SECURITY.md](SECURITY.md) and don't open a public issue.

## Examples

[negm17111995/travel-agent-examples](https://github.com/negm17111995/travel-agent-examples) has small, runnable travel assistants that connect to this server from the OpenAI Agents SDK (Python), LangChain with LangGraph (Python) and the Vercel AI SDK (TypeScript). Each one asks for your approval before any call that is not read-only.

## What you can do

- **Search hotels** with live rates and availability.
- **Search flights** and compare fares.
- **Look up cities, airports and hotel details**, including amenities and photos.
- **Hold a price** for a hotel room (prebook) or check a flight fare (verify).
- **Send a checkout link** on book.maqami.co where the customer enters their details, pays and gets confirmed.
- **Find, look up and cancel** existing bookings: find them with the email and last name, then act on one with its booking ID and email.

## Example prompts

- "Find 5-star hotels in Istanbul for 15 to 17 August, 2 adults."
- "Show me the amenities and photos for the second hotel."
- "Search flights from Dubai to London on 10 December for one adult."
- "Which airports serve Tokyo?"
- "Hold that room and send me the checkout link."

## Privacy and security

- No API key or account is required to connect.
- All traffic to `https://mcp.maqami.co/` is encrypted over HTTPS.
- Searches and bookings are processed by MAQAMI. Payment happens only on book.maqami.co; the MCP server never receives card details.
- Completing checkout creates a real reservation. Review the details and final price before paying.
- Privacy policy: [maqami.co/privacy-policy](https://maqami.co/privacy-policy/)

## Development

The repository contains the npm stdio bridge (`index.js`). The hosted server is deployed separately.

```bash
npm install
npm test
```

The bridge tests start a local mock Streamable HTTP server and point the bridge at it with the `MAQAMI_MCP_URL` environment variable. That variable exists for testing only; by default the bridge connects to `https://mcp.maqami.co/`. The manifest tests check that every manifest parses, points at the same endpoint and carries the version from `package.json`.

### Repository layout

| File | Purpose |
| --- | --- |
| `index.js` | npm stdio bridge to the hosted endpoint |
| `server.json` | Official MCP Registry entry |
| `gemini-extension.json`, `GEMINI.md` | Gemini CLI extension and its context file |
| `.claude-plugin/plugin.json`, `.mcp.json` | Claude Code plugin |
| `.claude-plugin/marketplace.json` | Claude Code plugin marketplace (`maqami`) |
| `.codex-plugin/plugin.json`, `assets/logo-512.png` | Codex plugin and its icon |
| `plugin.json`, `mcp.json` | Agent Plugins manifest |
| `mcpb/manifest.json`, `scripts/build-mcpb.sh` | Claude Desktop extension (`npm run build:mcpb` writes `dist/maqami-travel.mcpb`) |
| `skills/maqami-travel-booking/SKILL.md` | Booking skill bundled with the plugins |
| `glama.json` | Glama directory metadata |
| `AGENTS.md`, `llms.txt` | Short guides for coding agents and LLM tools |
| `test/` | Bridge tests against a local mock server, and manifest consistency checks (`npm test`) |
| `.github/workflows/` | CI (`npm test` on every pull request) and the release workflow that publishes to npm and the Official MCP Registry |

## Contributing

Documentation fixes, client setup guides and bug reports are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) and the [Code of Conduct](CODE_OF_CONDUCT.md). Questions and ideas go to [Discussions](https://github.com/negm17111995/mcp-server/discussions).

## License

[MIT](LICENSE)

## Support

Questions or issues: [info@maqami.co](mailto:info@maqami.co) or [open an issue](https://github.com/negm17111995/mcp-server/issues).
