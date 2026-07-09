---
name: integrations
description: "Show MCP integration status. Use when: checking active connectors, available integrations, or skill unlocks."
---

# /digital-marketing-pro:integrations

## Purpose

Show a complete integration status dashboard — which MCP connectors are currently connected, which are available but not yet configured, and which skills each connector unlocks. This is the first thing users should check after installing the plugin to understand what capabilities are active and what additional connections they can set up.

## Input Required

The user may optionally provide:

- **Filter** (optional): A specific category to focus on — e.g., "crm", "seo", "advertising", "email-marketing", "social-media". If omitted, shows all categories
- **Show** (optional): `connected` (only active connectors), `available` (only not-yet-connected), or `all` (default)

## Process

1. **Run connector status check**: Execute `python3 scripts/connector-status.py --action status` to get the full status dashboard. This reads the active `.mcp.json` configuration and checks environment variables for npx connectors to determine which are connected.

2. **Format the dashboard**: Present the results organized by category, with clear visual distinction between connected and available connectors:

   For each category (Chat, Design, CRM, SEO, Email Marketing, Advertising, Analytics, Social Media, etc.):
   - Show connected connectors with a checkmark indicator and the skills they power
   - Show available-but-not-connected connectors with what they would unlock
   - For available connectors, indicate whether they are HTTP (works everywhere, easy OAuth setup) or npx (Claude Code only, requires API keys)

3. **Highlight quick wins**: Identify the top 3 connectors the user should consider connecting based on which would unlock the most additional skill capabilities. Prioritize HTTP connectors (easier to set up) over npx connectors.

4. **Show coverage summary**: Display the overall integration coverage — X of Y connectors active, with a breakdown by category showing which areas have full coverage vs gaps.

5. **Provide next steps**: For each available connector, briefly explain how to connect it:
   - HTTP connectors: "Just use any skill that needs it — you'll be prompted to authorize via OAuth"
   - npx connectors: "Run `/digital-marketing-pro:connect <name>` for setup instructions, or `/digital-marketing-pro:add-integration <name>` for guided configuration"

## Output

A structured integration dashboard containing:

- **Coverage summary**: Total connected vs total available, percentage coverage, and per-category breakdown
- **Connected integrations**: List of all active connectors grouped by category, with the skills each one powers and its transport type (HTTP/npx)
- **Available integrations**: List of all not-yet-connected connectors grouped by category, with what skills they would unlock, transport type, and setup complexity (HTTP = easy/OAuth, npx = requires API keys)
- **Quick wins**: Top 3 recommended connectors to add next, based on skill coverage impact and setup ease
- **Category gaps**: Categories with zero connected connectors highlighted, with the most impactful connector to add in each gap category
- **Next steps**: Clear guidance — "Run `/digital-marketing-pro:connect <name>` to set up any connector" and "Run `/digital-marketing-pro:add-integration` for custom MCP servers not in the registry"

## Agents Used

- No specialized agent needed — this skill uses the `connector-status.py` script directly and formats the output
