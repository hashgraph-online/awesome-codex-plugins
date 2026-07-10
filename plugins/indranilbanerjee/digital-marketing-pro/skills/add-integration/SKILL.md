---
name: add-integration
description: "Add MCP server integrations. Use when: connecting a custom tool, API, or service to the plugin via .mcp.json."
argument-hint: "[service-name]"
---

# /digital-marketing-pro:add-integration

## Purpose

Guide users through adding a custom MCP server integration to the Digital Marketing Pro plugin. Search for existing MCP packages that provide the desired service connection, configure the server entry in `.mcp.json` with proper command, arguments, and environment variables, test connectivity to verify the integration works, and document the available tools. Supports both pre-built MCP servers from npm and custom implementations for proprietary APIs or internal tools.

## Input Required

The user must provide (or will be prompted for):

- **Service to integrate**: The name and purpose of the service to connect — e.g., "Ahrefs for backlink analysis", "Stripe for payment data", "our internal analytics API for custom dashboards". This determines the MCP package search terms and configuration approach
- **Integration type**: Whether to use a pre-built npm MCP package (preferred — faster setup, community-maintained) or build a custom MCP server (necessary for proprietary APIs, internal tools, or services without existing MCP packages). If unsure, the system searches for pre-built options first
- **Credentials available**: API keys, access tokens, OAuth client IDs, or other authentication credentials required by the service. The user should have these ready — the system will specify which environment variable names to use and where to store them, but will never ask the user to paste secrets into the conversation

## Process

1. **Load brand context**: Read `~/.claude-marketing/brands/_active-brand.json` for the active slug, then load `~/.claude-marketing/brands/{slug}/profile.json`. Check for agency credential profiles at `~/.claude-marketing/credentials/` — if agency mode is active, the new integration may need to be mapped to specific client credential sets. Check for agency SOPs at `~/.claude-marketing/sops/`. If no brand exists, ask: "Set up a brand first (/digital-marketing-pro:brand-setup)?" — or proceed with defaults.
2. **Search for existing MCP package**: Query npm registry and known MCP server directories for packages matching the requested service — search by service name, API name, and common variations. Evaluate candidates by download count, last update date, GitHub stars, and compatibility with the plugin's MCP configuration format. Present the best match (or top 3 if multiple viable options) with package name, description, supported tools, and any known limitations.
3. **Generate configuration for pre-built package**: If a suitable package is found, generate the complete `.mcp.json` entry — server name (following the plugin's naming convention: lowercase with hyphens), command (`npx` for npm packages), args array with the package name and any required flags, env object mapping environment variable names to credential references, and a description field summarizing what the integration provides. Show the user the exact JSON block to add.
4. **Provide custom MCP guidance if needed**: If no suitable pre-built package exists, provide a custom MCP server development template based on `skills/context-engine/custom-mcp-guide.md` — project structure, required tool definitions, input/output schemas, authentication handling, and error response patterns. Include a starter implementation skeleton for the specific API the user wants to connect, with placeholder endpoints and authentication flow.
5. **Configure environment variables**: Guide the user on environment variable setup — specify the exact variable names to use (following the `SERVICE_API_KEY` convention), where to add them (`.env` file in the project root or system environment variables for CI/CD), and how to reference them in the `.mcp.json` configuration. For agency setups, explain how to add the credentials to the appropriate credential profile at `~/.claude-marketing/credentials/`.
6. **Test MCP connectivity**: After the user confirms the configuration is in place, verify the integration works — check that the MCP server starts without errors, list the available tools it exposes, execute a basic read-only operation (e.g., fetching account info, listing resources, or a health check endpoint) to confirm authentication and connectivity. Report success or diagnose failure with specific error details and remediation steps.
7. **Map to agency credential profile (if applicable)**: For agency setups with multiple client brands, add the new integration's credential mapping to the appropriate profile — which environment variables are client-specific vs shared, how to switch credentials when switching brands, and how to verify the correct credentials are active.
8. **Document the integration**: Record the new integration in the brand's configuration — service name, MCP server name, tools available, credential requirements, any rate limits or usage constraints discovered during testing, and example usage patterns for team reference.

## Output

A complete integration setup report containing:

- **MCP configuration entry**: The exact JSON block ready to add to `.mcp.json` — server name, command, args, env, and description — formatted and validated against the plugin's configuration schema
- **Environment variable setup instructions**: Step-by-step guide for configuring the required credentials — variable names, where to set them, format requirements, and verification command to confirm they are loaded
- **Connectivity test results**: Server startup status, list of available tools with descriptions, and result of the basic read-only test operation — confirming the integration is working or providing specific error diagnostics
- **Credential profile mapping (if agency mode)**: How the new integration's credentials map to client profiles, switching instructions, and verification steps for multi-brand setups
- **Available tools documentation**: Complete list of tools exposed by the new MCP server — tool names, descriptions, required parameters, and example invocations for the most common operations
- **Next steps**: How to use the new integration — which existing commands can leverage it, example prompts that will trigger its use, and any workflows that should be updated to incorporate the new capability

## Agents Used

- **execution-coordinator** — MCP package discovery and evaluation, configuration generation with schema validation, connectivity testing with diagnostic error handling, credential profile mapping for agency setups, and integration documentation with tool inventory and usage guidance
