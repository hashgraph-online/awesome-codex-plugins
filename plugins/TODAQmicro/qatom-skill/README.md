# Qatom — Agentic Payments & Verification

An agentic MCP based marketplace: a payment and verification layer built on the TODA file technology and ADOT application protocol.

## What it does

* Become a provider — register your own discoverable Qatom MCP server, register any API, content, or service as a marketplace tool, and earn per call, automatically, every time a purchase is made.
* Sell with your own merchant agent — Your own Qatom powered agent can sell your published services through AI app, your website, as well as whatsapp and text messaging.
* Discover and buy — allow customers and consumers to discover and pay for services through agentic conversational checkout using their credit card.
* Call paywalled tools — other Qatom powered agents can access your marketplace APIs.
* Control your market — Publishing, funding, payments, payouts, secure bank integration, auditable records, are all under your control.

## Connect Codex / ChatGPT

This repo is also packaged as a Codex plugin. Add it as a marketplace source:

    codex plugin marketplace add TODAQmicro/qatom-skill --ref main
    codex plugin install qatom --source qatom-skill

Or in the ChatGPT desktop app: Settings, then Plugins, then +Add More..., and paste the repo URL. The plugin bundles the Qatom skill plus the hosted MCP server connection (mcp.m.todaq.net, OAuth 2.0). After installing, start a new session and ask: "Help me register as a Qatom provider" or "Check my Qatom wallet balance."

## Connect Claude

### Claude Code

Add this repo as a plugin marketplace, then install the plugin:

    /plugin marketplace add TODAQmicro/qatom-skill
    /plugin install qatom@qatom-skill

Or from your shell, without opening a session:

    claude plugin marketplace add TODAQmicro/qatom-skill
    claude plugin install qatom@qatom-skill

If the install summary says Run /reload-plugins to activate, run /reload-plugins. Confirm with /plugin list.

### Claude desktop app (Code tab)

Add the marketplace once with the command above, then click the + button next to the prompt box, then Plugins, then Add plugin, and choose qatom from the browser. Use Manage plugins in the same menu to enable, disable, or uninstall it later.

### Claude app — chat and Cowork

If you aren't using Claude Code, connect the hosted Qatom MCP server directly:

1. Go to Settings, then Connectors, then Add custom connector.
2. Name it Qatom and enter the server URL: https://mcp.m.todaq.net/mcp
3. Click Connect. Claude opens the Qatom sign-in (OAuth 2.0 via https://pay.m.todaq.net) — sign in with your email and 2FA code from the Qatom app or web UI.
4. Approve the requested scopes: openid, profile, email, twin.

## Connect Gemini

Add the Qatom MCP server to your Gemini CLI settings (~/.gemini/settings.json):

    "mcpServers": {
      "qatom": {
        "url": "https://mcp.m.todaq.net/mcp"
      }
    }

Restart Gemini CLI — the OAuth login flow opens in your browser on first use. Then ask: "Help me register as a Qatom provider" or "Check my Qatom wallet balance."

## Connect Hermes

Tell your Hermes agent: "Install the Qatom skill from github.com/TODAQmicro/qatom-skill and help me register as a provider."

## Connect OpenClaw

    clawhub install qatom

If installing manually for OpenClaw, copy skills/qatom/SKILL.md into your OpenClaw skills directory.

## Onboarding

On first successful connection, Qatom provisions two twins for you automatically: your primary twin (your main wallet, MFA-gated) and an agent twin (your agent's spending wallet, Bearer-token only, no MFA prompt on each payment). Twins are micro-applications that secure and manage any funds and auditable records.

Start a new session and ask:

* "Help me register as a Qatom provider"
* "Check my Qatom wallet balance"
* "What Qatom tools are available for [your use case]?"

## Requirements

* Popular platforms: Codex, Claude, Gemini (macOS), Hermes, OpenClaw
* mcporter (npm i -g mcporter)
* A Qatom account — your agent can walk you through setup, just ask: "Help me register as a Qatom provider."

## Usage

Once installed, your Qatom powered agent will automatically use this skill when you:

* Ask to call a tool from the Qatom marketplace
* Ask to check your wallet balance
* Ask to register and publish your own tool

## MCP Server

This skill connects to the TODAQ MCP server at mcp.m.todaq.net — a hosted, multi-tenant MCP server that exposes the Qatom marketplace to any MCP-compatible agent.

## License

MIT
