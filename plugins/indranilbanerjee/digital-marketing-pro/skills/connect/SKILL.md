---
name: connect
description: "Set up an MCP connector. Use when: connecting Google Ads, Salesforce, Mailchimp, or any service to the plugin."
argument-hint: "[connector-name]"
---

# /digital-marketing-pro:connect

## Purpose

Guide users through connecting a specific MCP integration to the Digital Marketing Pro plugin. Provides platform-specific setup instructions, credential requirements, configuration steps, and verification. This is the user-friendly entry point for adding integrations — it handles the common cases (known connectors with established setup paths) while `/digital-marketing-pro:add-integration` handles custom or unknown MCP servers.

## Input Required

The user must provide (or will be prompted for):

- **Connector name**: The service to connect — e.g., "google-ads", "salesforce", "mailchimp", "twilio", "deepl". If the user provides a partial or informal name (e.g., "google analytics", "fb ads", "linkedin"), match it to the closest connector in the registry
- **Environment** (optional): Whether they're using Claude Code (supports HTTP + npx) or Cowork (HTTP only). Defaults to auto-detect based on available context. If the requested connector is npx-only and the user is on Cowork, explain the limitation and suggest HTTP alternatives in the same category

## Process

1. **Look up connector**: Execute `python3 scripts/connector-status.py --action setup-guide --name <connector>` to get the detailed setup guide for the requested connector. If the name doesn't match exactly, search the registry for close matches and suggest the correct name.

2. **Check current status**: Execute `python3 scripts/connector-status.py --action check --name <connector>` to determine if the connector is already configured. If already connected, report that and show which skills it powers — ask if the user wants to verify connectivity or reconfigure.

3. **Present setup instructions based on transport type**:

   **For HTTP connectors** (Slack, Canva, Figma, HubSpot, Notion, Ahrefs, Similarweb, Klaviyo, Google Calendar, Gmail, Stripe, Asana, Webflow):
   - Explain that the connector is already pre-configured in `.mcp.json`
   - No API keys or manual configuration needed
   - The user just needs to use a skill that requires it — Claude will prompt for OAuth authorization
   - Example: "Your Slack connector is already configured. Just run `/digital-marketing-pro:send-notification` and you'll be prompted to authorize Slack access."
   - List the skills this connector enables

   **For npx connectors** (Google Ads, Meta, Salesforce, Twilio, etc.):
   - List the specific environment variables needed with clear descriptions
   - Provide platform-specific instructions for obtaining credentials:
     - Where to go in the platform's dashboard to create API keys
     - What permissions/scopes are needed
     - Any prerequisites (developer accounts, app creation, etc.)
   - Show the exact `.mcp.json` entry to add (from the setup guide)
   - Offer two setup paths:
     1. **Quick**: "Set the environment variables and run `/digital-marketing-pro:add-integration <name>` to configure automatically"
     2. **Manual**: Show the JSON block to add to `.mcp.json` directly
   - Note that npx connectors work in Claude Code only, not Cowork

4. **Handle unknown connectors**: If the connector name isn't in the registry:
   - Search for close matches and suggest them
   - If no match found, explain that it's a custom integration and guide them to `/digital-marketing-pro:add-integration` which handles npm package discovery and custom MCP server setup
   - List the categories of connectors available so they can explore alternatives

5. **Verify after setup** (for npx connectors): After the user confirms they've set up credentials, offer to verify connectivity:
   - Check that all required environment variables are set and non-empty
   - Suggest running a read-only test via the connector to confirm it works
   - Report success or diagnose failure with specific guidance

## Output

A connector setup guide containing:

- **Connector info**: Name, category, description, transport type (HTTP/npx), and current status (connected/not connected)
- **Skills unlocked**: List of all skills this connector enables, with brief descriptions of what each skill does
- **Setup instructions**: Step-by-step guide appropriate to the transport type — OAuth flow for HTTP, credential setup for npx
- **Credential requirements** (npx only): Exact environment variable names, where to obtain them, and required permissions
- **Configuration entry** (npx only): The exact JSON block to add to `.mcp.json`, ready to copy
- **Verification steps**: How to confirm the connector is working after setup
- **Alternative connectors**: Other connectors in the same category that the user might consider (e.g., "If you prefer Salesforce over HubSpot for CRM, run `/digital-marketing-pro:connect salesforce`")
- **Next steps**: "Run `/digital-marketing-pro:integrations` to see your updated integration dashboard" and relevant skills to try

## Agents Used

- No specialized agent needed — this skill uses the `connector-status.py` script directly and provides platform-specific guidance based on the connector registry
